"""
ZCleaner Settings Manager
Handles user preferences, configuration, and persistent settings.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import logging


@dataclass
class ScanSettings:
    """Settings for scan operations."""
    min_file_size_mb: float = 0.1
    max_file_size_mb: float = 2000.0
    include_images: bool = True
    include_videos: bool = True
    include_documents: bool = True
    custom_extensions: list = None
    
    def __post_init__(self):
        if self.custom_extensions is None:
            self.custom_extensions = []


@dataclass
class CleanupSettings:
    """Settings for cleanup operations."""
    action: str = "move"  # "move" or "delete"
    destination_folder: str = ""
    create_backup: bool = True
    backup_folder: str = ""
    confirm_before_action: bool = True


@dataclass
class UISettings:
    """Settings for the user interface."""
    theme: str = "DarkGrey13"
    window_width: int = 800
    window_height: int = 600
    show_progress_details: bool = True
    auto_save_logs: bool = True
    log_level: str = "INFO"


class SettingsManager:
    """Manages application settings and configuration."""
    
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.expanduser("~"), ".zcleaner")
        
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "settings.json"
        self.log_file = self.config_dir / "zcleaner.log"
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default settings
        self.scan_settings = ScanSettings()
        self.cleanup_settings = CleanupSettings()
        self.ui_settings = UISettings()
        
        # Load settings
        self.load_settings()
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration."""
        log_level = getattr(logging, self.ui_settings.log_level.upper(), logging.INFO)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
    
    def load_settings(self):
        """Load settings from configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Load scan settings
                if 'scan_settings' in data:
                    scan_data = data['scan_settings']
                    self.scan_settings = ScanSettings(**scan_data)
                
                # Load cleanup settings
                if 'cleanup_settings' in data:
                    cleanup_data = data['cleanup_settings']
                    self.cleanup_settings = CleanupSettings(**cleanup_data)
                
                # Load UI settings
                if 'ui_settings' in data:
                    ui_data = data['ui_settings']
                    self.ui_settings = UISettings(**ui_data)
                    
        except Exception as e:
            logging.warning(f"Failed to load settings: {e}")
            # Keep default settings
    
    def save_settings(self):
        """Save current settings to configuration file."""
        try:
            data = {
                'scan_settings': asdict(self.scan_settings),
                'cleanup_settings': asdict(self.cleanup_settings),
                'ui_settings': asdict(self.ui_settings)
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")
    
    def get_scan_settings(self) -> ScanSettings:
        """Get current scan settings."""
        return self.scan_settings
    
    def get_cleanup_settings(self) -> CleanupSettings:
        """Get current cleanup settings."""
        return self.cleanup_settings
    
    def get_ui_settings(self) -> UISettings:
        """Get current UI settings."""
        return self.ui_settings
    
    def update_scan_settings(self, **kwargs):
        """Update scan settings."""
        for key, value in kwargs.items():
            if hasattr(self.scan_settings, key):
                setattr(self.scan_settings, key, value)
        self.save_settings()
    
    def update_cleanup_settings(self, **kwargs):
        """Update cleanup settings."""
        for key, value in kwargs.items():
            if hasattr(self.cleanup_settings, key):
                setattr(self.cleanup_settings, key, value)
        self.save_settings()
    
    def update_ui_settings(self, **kwargs):
        """Update UI settings."""
        for key, value in kwargs.items():
            if hasattr(self.ui_settings, key):
                setattr(self.ui_settings, key, value)
        
        # Re-setup logging if log level changed
        if 'log_level' in kwargs:
            self._setup_logging()
        
        self.save_settings()
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        self.scan_settings = ScanSettings()
        self.cleanup_settings = CleanupSettings()
        self.ui_settings = UISettings()
        self.save_settings()
        self._setup_logging()
    
    def get_allowed_extensions(self) -> set:
        """Get the set of allowed file extensions based on current settings."""
        extensions = set()
        
        if self.scan_settings.include_images:
            extensions.update({'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff', '.gif'})
        
        if self.scan_settings.include_videos:
            extensions.update({'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm'})
        
        if self.scan_settings.include_documents:
            extensions.update({'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'})
        
        # Add custom extensions
        extensions.update(self.scan_settings.custom_extensions)
        
        return extensions
    
    def get_destination_folder(self) -> str:
        """Get the destination folder for moved duplicates."""
        if self.cleanup_settings.destination_folder:
            return self.cleanup_settings.destination_folder
        
        # Default to Desktop/Duplicates
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        return os.path.join(desktop, "Duplicates")
    
    def get_backup_folder(self) -> str:
        """Get the backup folder path."""
        if self.cleanup_settings.backup_folder:
            return self.cleanup_settings.backup_folder
        
        # Default to Desktop/ZCleaner_Backup
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        return os.path.join(desktop, "ZCleaner_Backup") 