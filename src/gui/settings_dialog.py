"""
ZCleaner Settings Dialog
Advanced settings configuration dialog.
"""

import PySimpleGUI as sg
from typing import Optional, Dict, Any
from ..core.settings_manager import SettingsManager


class SettingsDialog:
    """Settings configuration dialog."""
    
    def __init__(self, settings_manager: SettingsManager):
        self.settings_manager = settings_manager
        self.window: Optional[sg.Window] = None
    
    def show(self) -> bool:
        """Show the settings dialog and return True if settings were changed."""
        # Create layout
        layout = [
            [sg.Text("⚙️ ZCleaner Settings", font=("Arial", 14, "bold"))],
            [sg.HorizontalSeparator()],
            
            # Scan Settings Tab
            [sg.TabGroup([[
                sg.Tab("Scan Settings", self._create_scan_tab()),
                sg.Tab("Cleanup Settings", self._create_cleanup_tab()),
                sg.Tab("UI Settings", self._create_ui_tab())
            ]])],
            
            # Buttons
            [sg.Button("Save", key="-SAVE-", button_color=("#FFFFFF", "#4CAF50")),
             sg.Button("Cancel", key="-CANCEL-"),
             sg.Button("Reset to Defaults", key="-RESET-", button_color=("#FFFFFF", "#FF9800"))]
        ]
        
        # Create window
        self.window = sg.Window(
            "ZCleaner Settings",
            layout,
            size=(500, 400),
            modal=True,
            finalize=True
        )
        
        # Load current settings
        self._load_settings_to_gui()
        
        # Event loop
        while True:
            event, values = self.window.read()
            
            if event in (sg.WIN_CLOSED, "-CANCEL-"):
                self.window.close()
                return False
            
            elif event == "-SAVE-":
                if self._save_settings_from_gui():
                    self.window.close()
                    return True
            
            elif event == "-RESET-":
                if sg.popup_yes_no("Reset all settings to defaults?", title="Confirm Reset") == "Yes":
                    self.settings_manager.reset_to_defaults()
                    self._load_settings_to_gui()
    
    def _create_scan_tab(self):
        """Create scan settings tab layout."""
        return [
            [sg.Frame("File Types", [
                [sg.Checkbox("Images (JPG, PNG, WebP, etc.)", key="-SCAN_IMAGES-", default=True)],
                [sg.Checkbox("Videos (MP4, AVI, MKV, etc.)", key="-SCAN_VIDEOS-", default=True)],
                [sg.Checkbox("Documents (PDF, DOC, TXT, etc.)", key="-SCAN_DOCS-", default=True)],
                [sg.Text("Custom extensions (comma-separated):")],
                [sg.Input(key="-CUSTOM_EXTS-", size=(40, 1))]
            ], font=("Arial", 10))],
            
            [sg.Frame("File Size Limits", [
                [sg.Text("Minimum file size:"), 
                 sg.Input("0.1", key="-MIN_SIZE-", size=(10, 1)), 
                 sg.Text("MB")],
                [sg.Text("Maximum file size:"), 
                 sg.Input("2000", key="-MAX_SIZE-", size=(10, 1)), 
                 sg.Text("MB")]
            ], font=("Arial", 10))],
            
            [sg.Frame("Performance", [
                [sg.Text("Max concurrent threads:"), 
                 sg.Slider(range=(1, 16), default_value=8, orientation='h', key="-MAX_THREADS-")],
                [sg.Checkbox("Skip system folders", key="-SKIP_SYSTEM-", default=True)]
            ], font=("Arial", 10))]
        ]
    
    def _create_cleanup_tab(self):
        """Create cleanup settings tab layout."""
        return [
            [sg.Frame("Default Action", [
                [sg.Radio("Move duplicates", "ACTION", key="-ACTION_MOVE-", default=True)],
                [sg.Radio("Delete duplicates", "ACTION", key="-ACTION_DELETE-")],
                [sg.Text("Default destination folder:")],
                [sg.Input(key="-DEST_FOLDER-", size=(40, 1)),
                 sg.Button("Browse", key="-BROWSE_DEST-")]
            ], font=("Arial", 10))],
            
            [sg.Frame("Safety", [
                [sg.Checkbox("Confirm before cleanup", key="-CONFIRM_CLEANUP-", default=True)],
                [sg.Checkbox("Create backup before delete", key="-CREATE_BACKUP-", default=True)],
                [sg.Text("Backup folder:")],
                [sg.Input(key="-BACKUP_FOLDER-", size=(40, 1)),
                 sg.Button("Browse", key="-BROWSE_BACKUP-")]
            ], font=("Arial", 10))]
        ]
    
    def _create_ui_tab(self):
        """Create UI settings tab layout."""
        themes = ["DarkGrey13", "LightGrey1", "BlueMono", "GreenMono", "BrownBlue", "Purple"]
        
        return [
            [sg.Frame("Appearance", [
                [sg.Text("Theme:"), sg.Combo(themes, default_value="DarkGrey13", key="-THEME-")],
                [sg.Text("Window width:"), sg.Input("800", key="-WINDOW_WIDTH-", size=(10, 1))],
                [sg.Text("Window height:"), sg.Input("600", key="-WINDOW_HEIGHT-", size=(10, 1))]
            ], font=("Arial", 10))],
            
            [sg.Frame("Logging", [
                [sg.Text("Log level:"), 
                 sg.Combo(["DEBUG", "INFO", "WARNING", "ERROR"], default_value="INFO", key="-LOG_LEVEL-")],
                [sg.Checkbox("Show progress details", key="-SHOW_PROGRESS-", default=True)],
                [sg.Checkbox("Auto-save logs", key="-AUTO_SAVE_LOGS-", default=True)],
                [sg.Text("Keep logs for (days):"), sg.Input("7", key="-LOG_RETENTION-", size=(10, 1))]
            ], font=("Arial", 10))]
        ]
    
    def _load_settings_to_gui(self):
        """Load current settings into GUI elements."""
        scan_settings = self.settings_manager.get_scan_settings()
        cleanup_settings = self.settings_manager.get_cleanup_settings()
        ui_settings = self.settings_manager.get_ui_settings()
        
        # Scan settings
        self.window["-SCAN_IMAGES-"].update(scan_settings.include_images)
        self.window["-SCAN_VIDEOS-"].update(scan_settings.include_videos)
        self.window["-SCAN_DOCS-"].update(scan_settings.include_documents)
        self.window["-CUSTOM_EXTS-"].update(",".join(scan_settings.custom_extensions))
        self.window["-MIN_SIZE-"].update(str(scan_settings.min_file_size_mb))
        self.window["-MAX_SIZE-"].update(str(scan_settings.max_file_size_mb))
        
        # Cleanup settings
        if cleanup_settings.action == "move":
            self.window["-ACTION_MOVE-"].update(True)
        else:
            self.window["-ACTION_DELETE-"].update(True)
        
        self.window["-DEST_FOLDER-"].update(cleanup_settings.destination_folder)
        self.window["-CONFIRM_CLEANUP-"].update(cleanup_settings.confirm_before_action)
        self.window["-CREATE_BACKUP-"].update(cleanup_settings.create_backup)
        self.window["-BACKUP_FOLDER-"].update(cleanup_settings.backup_folder)
        
        # UI settings
        self.window["-THEME-"].update(ui_settings.theme)
        self.window["-WINDOW_WIDTH-"].update(str(ui_settings.window_width))
        self.window["-WINDOW_HEIGHT-"].update(str(ui_settings.window_height))
        self.window["-LOG_LEVEL-"].update(ui_settings.log_level)
        self.window["-SHOW_PROGRESS-"].update(ui_settings.show_progress_details)
        self.window["-AUTO_SAVE_LOGS-"].update(ui_settings.auto_save_logs)
    
    def _save_settings_from_gui(self) -> bool:
        """Save GUI settings to settings manager."""
        try:
            # Parse custom extensions
            custom_exts = [ext.strip() for ext in self.window["-CUSTOM_EXTS-"].get().split(",") if ext.strip()]
            
            # Update scan settings
            self.settings_manager.update_scan_settings(
                include_images=self.window["-SCAN_IMAGES-"].get(),
                include_videos=self.window["-SCAN_VIDEOS-"].get(),
                include_documents=self.window["-SCAN_DOCS-"].get(),
                custom_extensions=custom_exts,
                min_file_size_mb=float(self.window["-MIN_SIZE-"].get()),
                max_file_size_mb=float(self.window["-MAX_SIZE-"].get())
            )
            
            # Update cleanup settings
            action = "move" if self.window["-ACTION_MOVE-"].get() else "delete"
            self.settings_manager.update_cleanup_settings(
                action=action,
                destination_folder=self.window["-DEST_FOLDER-"].get(),
                confirm_before_action=self.window["-CONFIRM_CLEANUP-"].get(),
                create_backup=self.window["-CREATE_BACKUP-"].get(),
                backup_folder=self.window["-BACKUP_FOLDER-"].get()
            )
            
            # Update UI settings
            self.settings_manager.update_ui_settings(
                theme=self.window["-THEME-"].get(),
                window_width=int(self.window["-WINDOW_WIDTH-"].get()),
                window_height=int(self.window["-WINDOW_HEIGHT-"].get()),
                log_level=self.window["-LOG_LEVEL-"].get(),
                show_progress_details=self.window["-SHOW_PROGRESS-"].get(),
                auto_save_logs=self.window["-AUTO_SAVE_LOGS-"].get()
            )
            
            return True
            
        except ValueError as e:
            sg.popup_error(f"Invalid setting value: {e}", title="Settings Error")
            return False 