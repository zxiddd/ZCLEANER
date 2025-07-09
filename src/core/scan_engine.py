"""
ZCleaner Scan Engine
Handles file discovery, hashing, and duplicate detection with progress tracking.
"""

import os
import zlib
import hashlib
import shutil
import concurrent.futures
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import threading
import time


@dataclass
class FileInfo:
    """Represents a file with its metadata and hash."""
    path: str
    size: int
    hash_value: Optional[str] = None
    hash_type: str = ""


@dataclass
class ScanResult:
    """Results from a scan operation."""
    total_files: int
    total_size: int
    duplicates: List[List[str]]
    scan_time: float
    space_saved: int = 0


class ScanEngine:
    """Main engine for scanning files and detecting duplicates."""
    
    def __init__(self):
        # Configuration
        self.skip_folders = {'Windows', 'Program Files', 'ProgramData', 'AppData', 
                            '$Recycle.Bin', 'System Volume Information'}
        self.image_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif'}
        self.video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'}
        self.document_exts = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
        self.allowed_exts = self.image_exts.union(self.video_exts).union(self.document_exts)
        self.max_file_size_mb = 2000  # 2GB
        
        # Progress tracking
        self.progress_callback: Optional[Callable[[int, str], None]] = None
        self.cancelled = False
        
        # Threading
        self._lock = threading.Lock()
    
    def set_progress_callback(self, callback: Callable[[int, str], None]):
        """Set callback for progress updates."""
        self.progress_callback = callback
    
    def cancel_scan(self):
        """Cancel the current scan operation."""
        self.cancelled = True
    
    def _update_progress(self, percentage: int, message: str = ""):
        """Update progress if callback is set."""
        if self.progress_callback:
            self.progress_callback(percentage, message)
    
    def _should_skip_folder(self, folder_path: str) -> bool:
        """Check if folder should be skipped."""
        folder_name = os.path.basename(folder_path)
        return folder_name in self.skip_folders
    
    def _is_valid_file(self, file_path: str) -> bool:
        """Check if file should be included in scan."""
        try:
            # Check file extension
            ext = Path(file_path).suffix.lower()
            if ext not in self.allowed_exts:
                return False
            
            # Check file size
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > self.max_file_size_mb:
                return False
            
            return True
        except (OSError, PermissionError):
            return False
    
    def discover_files(self, root_folder: str) -> List[str]:
        """Discover all valid files in the given folder."""
        files = []
        total_items = 0
        processed_items = 0
        
        # First pass: count total items for progress
        for root, dirs, filenames in os.walk(root_folder):
            if self._should_skip_folder(root):
                dirs.clear()  # Don't traverse into skipped folders
                continue
            total_items += len(filenames)
        
        # Second pass: collect valid files
        for root, dirs, filenames in os.walk(root_folder):
            if self.cancelled:
                break
                
            if self._should_skip_folder(root):
                dirs.clear()
                continue
            
            for filename in filenames:
                if self.cancelled:
                    break
                    
                processed_items += 1
                file_path = os.path.join(root, filename)
                
                if self._is_valid_file(file_path):
                    files.append(file_path)
                
                # Update progress every 10 files
                if processed_items % 10 == 0:
                    progress = int((processed_items / total_items) * 30)  # First 30% for discovery
                    self._update_progress(progress, f"Discovering files... ({len(files)} found)")
        
        return files
    
    def _crc32_hash(self, file_path: str) -> Optional[int]:
        """Calculate CRC32 hash of a file."""
        try:
            with open(file_path, 'rb') as f:
                return zlib.crc32(f.read()) & 0xFFFFFFFF
        except (OSError, PermissionError):
            return None
    
    def _md5_hash(self, file_path: str) -> Optional[str]:
        """Calculate MD5 hash of a file."""
        try:
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(65536), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except (OSError, PermissionError):
            return None
    
    def _group_by_size(self, files: List[str]) -> Dict[int, List[str]]:
        """Group files by size for efficient duplicate detection."""
        size_groups = defaultdict(list)
        
        for file_path in files:
            if self.cancelled:
                break
            try:
                size = os.path.getsize(file_path)
                size_groups[size].append(file_path)
            except (OSError, PermissionError):
                continue
        
        return size_groups
    
    def _hash_files(self, files: List[str], progress_start: int = 30) -> Dict[str, List[str]]:
        """Hash files using CRC32 first, then MD5 for potential duplicates."""
        crc_groups = defaultdict(list)
        md5_groups = defaultdict(list)
        
        # Group by size first
        size_groups = self._group_by_size(files)
        total_groups = len([g for g in size_groups.values() if len(g) > 1])
        processed_groups = 0
        
        # Pass 1: CRC32 hash
        self._update_progress(progress_start, "Calculating CRC32 hashes...")
        for size, file_list in size_groups.items():
            if self.cancelled:
                break
            if len(file_list) < 2:
                continue
                
            for file_path in file_list:
                hash_value = self._crc32_hash(file_path)
                if hash_value is not None:
                    crc_groups[(size, hash_value)].append(file_path)
        
        # Pass 2: MD5 hash for potential duplicates
        self._update_progress(progress_start + 30, "Calculating MD5 hashes...")
        potential_duplicates = [group for group in crc_groups.values() if len(group) > 1]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = {}
            
            for group in potential_duplicates:
                if self.cancelled:
                    break
                for file_path in group:
                    futures[executor.submit(self._md5_hash, file_path)] = file_path
            
            for i, (future, file_path) in enumerate(futures.items()):
                if self.cancelled:
                    break
                    
                hash_value = future.result()
                if hash_value:
                    md5_groups[hash_value].append(file_path)
                
                # Update progress
                if i % 10 == 0:
                    progress = progress_start + 30 + int((i / len(futures)) * 40)
                    self._update_progress(progress, f"Processing hashes... ({i}/{len(futures)})")
        
        return md5_groups
    
    def scan_folder(self, folder_path: str) -> ScanResult:
        """Main scan method that discovers and identifies duplicates."""
        start_time = time.time()
        self.cancelled = False
        
        try:
            # Step 1: Discover files
            self._update_progress(0, "Starting scan...")
            files = self.discover_files(folder_path)
            
            if self.cancelled:
                return ScanResult(0, 0, [], 0)
            
            # Step 2: Hash files
            hash_groups = self._hash_files(files)
            
            if self.cancelled:
                return ScanResult(0, 0, [], 0)
            
            # Step 3: Identify duplicates
            self._update_progress(90, "Identifying duplicates...")
            duplicates = [group for group in hash_groups.values() if len(group) > 1]
            
            # Calculate statistics
            total_size = sum(os.path.getsize(f) for f in files)
            space_saved = sum(
                sum(os.path.getsize(dup) for dup in group[1:]) 
                for group in duplicates
            )
            
            scan_time = time.time() - start_time
            self._update_progress(100, "Scan complete!")
            
            return ScanResult(
                total_files=len(files),
                total_size=total_size,
                duplicates=duplicates,
                scan_time=scan_time,
                space_saved=space_saved
            )
            
        except Exception as e:
            self._update_progress(0, f"Error during scan: {str(e)}")
            raise
    
    def move_duplicates(self, duplicates: List[List[str]], destination: str) -> Tuple[int, int]:
        """Move duplicate files to destination folder."""
        moved_count = 0
        moved_size = 0
        
        os.makedirs(destination, exist_ok=True)
        
        for group in duplicates:
            if self.cancelled:
                break
                
            # Keep the first file, move the rest
            original = group[0]
            for duplicate in group[1:]:
                try:
                    # Generate unique filename
                    base_name = os.path.basename(duplicate)
                    name, ext = os.path.splitext(base_name)
                    counter = 1
                    dest_path = os.path.join(destination, base_name)
                    
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(destination, f"{name}_{counter}{ext}")
                        counter += 1
                    
                    # Move file
                    shutil.move(duplicate, dest_path)
                    moved_count += 1
                    moved_size += os.path.getsize(dest_path)
                    
                except (OSError, PermissionError) as e:
                    print(f"Failed to move {duplicate}: {e}")
                    continue
        
        return moved_count, moved_size
    
    def delete_duplicates(self, duplicates: List[List[str]]) -> Tuple[int, int]:
        """Delete duplicate files (keep the first one in each group)."""
        deleted_count = 0
        deleted_size = 0
        
        for group in duplicates:
            if self.cancelled:
                break
                
            # Keep the first file, delete the rest
            for duplicate in group[1:]:
                try:
                    size = os.path.getsize(duplicate)
                    os.remove(duplicate)
                    deleted_count += 1
                    deleted_size += size
                    
                except (OSError, PermissionError) as e:
                    print(f"Failed to delete {duplicate}: {e}")
                    continue
        
        return deleted_count, deleted_size 