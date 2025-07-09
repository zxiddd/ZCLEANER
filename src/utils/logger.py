"""
ZCleaner Logger
Handles logging for the application with file and GUI output.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
import threading


class ZCleanerLogger:
    """Custom logger for ZCleaner application."""
    
    def __init__(self, log_file: Optional[str] = None):
        """Initialize the logger."""
        self.logger = logging.getLogger("ZCleaner")
        self.logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler
        if log_file is None:
            log_dir = Path.home() / "AppData" / "Local" / "ZCleaner"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "zcleaner.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(console_formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # GUI callback
        self.gui_callback: Optional[Callable[[str], None]] = None
        
        # Thread safety
        self._lock = threading.Lock()
    
    def set_gui_callback(self, callback: Callable[[str], None]):
        """Set callback for GUI log updates."""
        self.gui_callback = callback
    
    def _log_with_gui(self, level: str, message: str):
        """Log message and update GUI if callback is set."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        gui_message = f"{timestamp} - {level.upper()} - {message}"
        
        if self.gui_callback:
            try:
                self.gui_callback(gui_message)
            except Exception:
                pass  # Don't let GUI errors break logging
    
    def debug(self, message: str):
        """Log debug message."""
        with self._lock:
            self.logger.debug(message)
            self._log_with_gui("DEBUG", message)
    
    def info(self, message: str):
        """Log info message."""
        with self._lock:
            self.logger.info(message)
            self._log_with_gui("INFO", message)
    
    def warning(self, message: str):
        """Log warning message."""
        with self._lock:
            self.logger.warning(message)
            self._log_with_gui("WARNING", message)
    
    def error(self, message: str):
        """Log error message."""
        with self._lock:
            self.logger.error(message)
            self._log_with_gui("ERROR", message)
    
    def critical(self, message: str):
        """Log critical message."""
        with self._lock:
            self.logger.critical(message)
            self._log_with_gui("CRITICAL", message)
    
    def log_scan_start(self, folder: str):
        """Log scan start."""
        self.info(f"Starting scan of folder: {folder}")
    
    def log_scan_complete(self, scan_result):
        """Log scan completion."""
        if scan_result:
            total_files = scan_result.total_files
            duplicate_groups = len(scan_result.duplicate_groups)
            total_duplicates = sum(len(group) - 1 for group in scan_result.duplicate_groups)
            
            self.info(f"Scan completed: {total_files} files, {duplicate_groups} groups, {total_duplicates} duplicates")
        else:
            self.info("Scan completed: No duplicates found")
    
    def log_cleanup_start(self, action: str, count: int):
        """Log cleanup start."""
        self.info(f"Starting {action} operation for {count} files")
    
    def log_cleanup_complete(self, action: str, count: int, size: int):
        """Log cleanup completion."""
        size_str = self._format_size(size)
        self.info(f"Files {action}d: {count}")
        self.info(f"Space saved: {size_str}")
    
    def log_error(self, error: Exception, context: str):
        """Log error with context."""
        self.error(f"Error during {context}: {str(error)}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    def get_recent_logs(self, lines: int = 50) -> list[str]:
        """Get recent log lines from file."""
        try:
            log_file = Path.home() / "AppData" / "Local" / "ZCleaner" / "zcleaner.log"
            if not log_file.exists():
                return []
            
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                return all_lines[-lines:] if len(all_lines) > lines else all_lines
                
        except Exception as e:
            self.error(f"Could not read log file: {str(e)}")
            return [] 