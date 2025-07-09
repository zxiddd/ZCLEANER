"""
ZCleaner Main Window
Main GUI application with modern interface using tkinter.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import webbrowser
from typing import Optional, Callable
from pathlib import Path
import time

from ..core.scan_engine import ScanEngine, ScanResult
from ..core.settings_manager import SettingsManager
from ..utils.logger import ZCleanerLogger


class ModernButton(tk.Button):
    """Custom modern button with hover effects."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
    def _on_enter(self, e):
        self.config(relief="raised", bd=2)
        
    def _on_leave(self, e):
        self.config(relief="flat", bd=1)


class MainWindow:
    """Main application window for ZCleaner."""
    
    def __init__(self):
        # Initialize components
        self.settings_manager = SettingsManager()
        self.logger = ZCleanerLogger()
        self.scan_engine = ScanEngine()
        
        # GUI state
        self.root: Optional[tk.Tk] = None
        self.scan_result: Optional[ScanResult] = None
        self.scanning = False
        self.cleanup_running = False
        
        # Setup GUI
        self._setup_gui()
        self._setup_callbacks()
    
    def _setup_gui(self):
        """Setup the main GUI layout."""
        # Create main window
        self.root = tk.Tk()
        self.root.title("ZCleaner - Smart Duplicate File Finder")
        self.root.geometry("900x750")
        self.root.configure(bg="#f5f5f5")
        
        # Set icon if available
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'icon.ico')
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except:
                pass
        
        # Configure grid weights
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Header frame
        header_frame = tk.Frame(self.root, bg="#4CAF50", height=80)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="ZCleaner", 
            font=("Segoe UI", 24, "bold"), 
            fg="white", 
            bg="#4CAF50"
        )
        title_label.grid(row=0, column=0, pady=10)
        
        subtitle_label = tk.Label(
            header_frame, 
            text="Smart Duplicate File Finder & Cleaner", 
            font=("Segoe UI", 12), 
            fg="white", 
            bg="#4CAF50"
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 10))
        
        # Main content frame
        main_frame = tk.Frame(self.root, bg="#f5f5f5")
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Folder selection frame
        folder_frame = tk.LabelFrame(main_frame, text="Folder Selection", font=("Segoe UI", 10, "bold"), bg="#f5f5f5")
        folder_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        folder_frame.grid_columnconfigure(1, weight=1)
        
        tk.Label(folder_frame, text="Select folder to scan:", font=("Segoe UI", 9), bg="#f5f5f5").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        self.folder_var = tk.StringVar()
        self.folder_entry = tk.Entry(folder_frame, textvariable=self.folder_var, font=("Segoe UI", 9))
        self.folder_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
        self.browse_btn = ModernButton(
            folder_frame, 
            text="Browse", 
            command=self._browse_folder,
            bg="#2196F3", 
            fg="white", 
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=20
        )
        self.browse_btn.grid(row=1, column=2, padx=(10, 10), pady=5)
        
        # Scan options frame
        options_frame = tk.LabelFrame(main_frame, text="Scan Options", font=("Segoe UI", 10, "bold"), bg="#f5f5f5")
        options_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        options_frame.grid_columnconfigure(1, weight=1)
        
        # File type checkboxes
        self.include_images = tk.BooleanVar(value=True)
        self.include_videos = tk.BooleanVar(value=True)
        self.include_docs = tk.BooleanVar(value=True)
        
        tk.Checkbutton(
            options_frame, 
            text="Images", 
            variable=self.include_images, 
            font=("Segoe UI", 9), 
            bg="#f5f5f5"
        ).grid(row=0, column=0, sticky="w", padx=10, pady=2)
        
        tk.Checkbutton(
            options_frame, 
            text="Videos", 
            variable=self.include_videos, 
            font=("Segoe UI", 9), 
            bg="#f5f5f5"
        ).grid(row=0, column=1, sticky="w", padx=10, pady=2)
        
        tk.Checkbutton(
            options_frame, 
            text="Documents", 
            variable=self.include_docs, 
            font=("Segoe UI", 9), 
            bg="#f5f5f5"
        ).grid(row=0, column=2, sticky="w", padx=10, pady=2)
        
        # File size options
        tk.Label(options_frame, text="Min file size (MB):", font=("Segoe UI", 9), bg="#f5f5f5").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.min_size_var = tk.StringVar(value="0.1")
        tk.Entry(options_frame, textvariable=self.min_size_var, width=10, font=("Segoe UI", 9)).grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        tk.Label(options_frame, text="Max file size (MB):", font=("Segoe UI", 9), bg="#f5f5f5").grid(row=1, column=2, sticky="w", padx=10, pady=5)
        self.max_size_var = tk.StringVar(value="2000")
        tk.Entry(options_frame, textvariable=self.max_size_var, width=10, font=("Segoe UI", 9)).grid(row=1, column=3, sticky="w", padx=5, pady=5)
        
        # Progress frame
        progress_frame = tk.LabelFrame(main_frame, text="Progress", font=("Segoe UI", 10, "bold"), bg="#f5f5f5")
        progress_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        self.progress_text = tk.Label(progress_frame, text="Ready to scan", font=("Segoe UI", 9), bg="#f5f5f5")
        self.progress_text.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 5))
        
        # Action buttons frame
        buttons_frame = tk.Frame(main_frame, bg="#f5f5f5")
        buttons_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        
        self.scan_btn = ModernButton(
            buttons_frame, 
            text="Start Scan", 
            command=self._start_scan,
            bg="#4CAF50", 
            fg="white", 
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=30,
            pady=5
        )
        self.scan_btn.grid(row=0, column=0, padx=5)
        
        self.cancel_btn = ModernButton(
            buttons_frame, 
            text="Cancel", 
            command=self._cancel_scan,
            bg="#F44336", 
            fg="white", 
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=30,
            pady=5,
            state="disabled"
        )
        self.cancel_btn.grid(row=0, column=1, padx=5)
        
        self.settings_btn = ModernButton(
            buttons_frame, 
            text="Settings", 
            command=self._show_settings,
            bg="#FF9800", 
            fg="white", 
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=30,
            pady=5
        )
        self.settings_btn.grid(row=0, column=2, padx=5)
        
        # Results frame
        results_frame = tk.LabelFrame(main_frame, text="Scan Results", font=("Segoe UI", 10, "bold"), bg="#f5f5f5")
        results_frame.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        results_frame.grid_columnconfigure(0, weight=1)
        
        self.results_text = tk.Label(
            results_frame, 
            text="No scan results yet", 
            font=("Segoe UI", 9), 
            bg="#f5f5f5",
            wraplength=800
        )
        self.results_text.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        results_buttons_frame = tk.Frame(results_frame, bg="#f5f5f5")
        results_buttons_frame.grid(row=1, column=0, pady=5)
        
        self.move_btn = ModernButton(
            results_buttons_frame, 
            text="Move Duplicates", 
            command=self._move_duplicates,
            bg="#2196F3", 
            fg="white", 
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=20,
            state="disabled"
        )
        self.move_btn.grid(row=0, column=0, padx=5)
        
        self.delete_btn = ModernButton(
            results_buttons_frame, 
            text="Delete Duplicates", 
            command=self._delete_duplicates,
            bg="#F44336", 
            fg="white", 
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=20,
            state="disabled"
        )
        self.delete_btn.grid(row=0, column=1, padx=5)
        
        self.summary_btn = ModernButton(
            results_buttons_frame, 
            text="Summary", 
            command=self._show_summary,
            bg="#9C27B0", 
            fg="white", 
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=20,
            state="disabled"
        )
        self.summary_btn.grid(row=0, column=2, padx=5)
        
        # Log frame
        log_frame = tk.LabelFrame(main_frame, text="Activity Log", font=("Segoe UI", 10, "bold"), bg="#f5f5f5")
        log_frame.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        # Create text widget with scrollbar
        log_text_frame = tk.Frame(log_frame, bg="#f5f5f5")
        log_text_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        log_text_frame.grid_columnconfigure(0, weight=1)
        log_text_frame.grid_rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_text_frame, height=8, font=("Consolas", 8), bg="white", fg="black")
        log_scrollbar = tk.Scrollbar(log_text_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = tk.Label(
            self.root, 
            textvariable=self.status_var, 
            font=("Segoe UI", 8), 
            fg="#666666", 
            bg="#f5f5f5",
            anchor="w"
        )
        status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))
        
        # Footer with branding
        footer_frame = tk.Frame(self.root, bg="#f5f5f5")
        footer_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        footer_frame.grid_columnconfigure(0, weight=1)
        
        # Made with love note
        footer_text = tk.Label(
            footer_frame, 
            text="Made with love by Zaid", 
            font=("Segoe UI", 9), 
            fg="#888888", 
            bg="#f5f5f5"
        )
        footer_text.grid(row=0, column=0, pady=5)
        
        # Social links
        links_frame = tk.Frame(footer_frame, bg="#f5f5f5")
        links_frame.grid(row=1, column=0, pady=2)
        
        github_btn = tk.Label(
            links_frame, 
            text="GitHub: zxiddd", 
            font=("Segoe UI", 9, "underline"), 
            fg="#1976D2", 
            bg="#f5f5f5",
            cursor="hand2"
        )
        github_btn.grid(row=0, column=0, padx=5)
        github_btn.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/zxiddd"))
        
        insta_btn = tk.Label(
            links_frame, 
            text="Instagram: zxiddd.14", 
            font=("Segoe UI", 9, "underline"), 
            fg="#C13584", 
            bg="#f5f5f5",
            cursor="hand2"
        )
        insta_btn.grid(row=0, column=1, padx=5)
        insta_btn.bind("<Button-1>", lambda e: webbrowser.open("https://instagram.com/zxiddd.14"))
        
        linkedin_btn = tk.Label(
            links_frame, 
            text="LinkedIn: zxid", 
            font=("Segoe UI", 9, "underline"), 
            fg="#0077B5", 
            bg="#f5f5f5",
            cursor="hand2"
        )
        linkedin_btn.grid(row=0, column=2, padx=5)
        linkedin_btn.bind("<Button-1>", lambda e: webbrowser.open("https://linkedin.com/in/zxid"))
        
        # Setup logger callback
        self.logger.set_gui_callback(self._update_log)
        
        # Setup scan engine callback
        self.scan_engine.set_progress_callback(self._update_progress)
    
    def _setup_callbacks(self):
        """Setup callback functions for GUI events."""
        pass  # Will be handled in individual methods
    
    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(title="Select folder to scan")
        if folder:
            self.folder_var.set(folder)
    
    def _start_scan(self):
        """Start the scanning process in a separate thread."""
        folder = self.folder_var.get().strip()
        
        if not folder:
            messagebox.showerror("No Folder Selected", "Please select a folder to scan!")
            return
        
        if not os.path.exists(folder):
            messagebox.showerror("Invalid Folder", "The selected folder does not exist!")
            return
        
        # Save settings
        self._save_gui_to_settings()
        
        # Start scan in thread
        self.scanning = True
        self.scan_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.progress_bar["value"] = 0
        self.progress_text.config(text="Starting scan...")
        self.status_var.set("Scanning...")
        
        scan_thread = threading.Thread(target=self._scan_worker, args=(folder,))
        scan_thread.daemon = True
        scan_thread.start()
    
    def _scan_worker(self, folder: str):
        """Worker thread for scanning."""
        try:
            # Update scan engine settings based on GUI values
            self.scan_engine.max_file_size_mb = float(self.max_size_var.get())
            
            # Update allowed extensions based on GUI settings
            allowed_exts = set()
            if self.include_images.get():
                allowed_exts.update(self.scan_engine.image_exts)
            if self.include_videos.get():
                allowed_exts.update(self.scan_engine.video_exts)
            if self.include_docs.get():
                allowed_exts.update(self.scan_engine.document_exts)
            
            self.scan_engine.allowed_exts = allowed_exts
            
            # Run scan
            self.scan_result = self.scan_engine.scan_folder(folder)
            
            # Update GUI on main thread
            self.root.after(0, self._scan_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self._scan_error(str(e)))
    
    def _scan_complete(self):
        """Handle scan completion."""
        self.scanning = False
        self.scan_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        self.progress_bar["value"] = 100
        self.progress_text.config(text="Scan completed!")
        self.status_var.set("Scan completed")
        
        if self.scan_result:
            total_files = self.scan_result.total_files
            duplicate_groups = len(self.scan_result.duplicates)
            total_duplicates = sum(len(group) - 1 for group in self.scan_result.duplicates)
            space_wasted = sum(
                sum(os.path.getsize(f) for f in group[1:]) 
                for group in self.scan_result.duplicates
            )
            
            results_text = f"Found {total_files} files\n{duplicate_groups} duplicate groups with {total_duplicates} duplicate files\nPotential space savings: {self._format_size(space_wasted)}"
            
            self.results_text.config(text=results_text)
            self.move_btn.config(state="normal")
            self.delete_btn.config(state="normal")
            self.summary_btn.config(state="normal")
            
            self.logger.info(f"Scan completed: {total_files} files, {duplicate_groups} groups, {total_duplicates} duplicates")
        else:
            self.results_text.config(text="No duplicates found")
            self.logger.info("Scan completed: No duplicates found")
    
    def _scan_error(self, error_msg: str):
        """Handle scan error."""
        self.scanning = False
        self.scan_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        self.progress_text.config(text="Scan failed!")
        self.status_var.set("Scan failed")
        
        messagebox.showerror("Scan Error", f"Scan failed: {error_msg}")
        self.logger.error(f"Scan error: {error_msg}")
    
    def _cancel_scan(self):
        """Cancel the current scan."""
        if self.scanning:
            self.scan_engine.cancel_scan()
            self.scanning = False
            self.scan_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")
            self.progress_text.config(text="Scan cancelled")
            self.status_var.set("Scan cancelled")
            self.logger.info("Scan cancelled by user")
    
    def _move_duplicates(self):
        """Move duplicates to a folder."""
        if not self.scan_result or not self.scan_result.duplicates:
            messagebox.showwarning("No Duplicates", "No duplicates to move!")
            return
        
        destination = filedialog.askdirectory(title="Select destination folder for duplicates")
        if not destination:
            return
        
        self._start_cleanup("move", destination)
    
    def _delete_duplicates(self):
        """Delete duplicates."""
        if not self.scan_result or not self.scan_result.duplicates:
            messagebox.showwarning("No Duplicates", "No duplicates to delete!")
            return
        
        result = messagebox.askyesno(
            "Confirm Deletion", 
            "Are you sure you want to permanently delete all duplicate files?\n\nThis action cannot be undone!"
        )
        
        if result:
            self._start_cleanup("delete", None)
    
    def _start_cleanup(self, action: str, destination: Optional[str]):
        """Start cleanup process."""
        self.cleanup_running = True
        self.move_btn.config(state="disabled")
        self.delete_btn.config(state="disabled")
        self.progress_bar["value"] = 0
        self.progress_text.config(text=f"Starting {action}...")
        self.status_var.set(f"{action.title()}ing duplicates...")
        
        cleanup_thread = threading.Thread(target=self._cleanup_worker, args=(action, destination))
        cleanup_thread.daemon = True
        cleanup_thread.start()
    
    def _cleanup_worker(self, action: str, destination: Optional[str]):
        """Worker thread for cleanup."""
        try:
            if action == "move":
                count, size = self.scan_engine.move_duplicates(self.scan_result.duplicates, destination)
                self.root.after(0, lambda: self._cleanup_complete("move", count, size))
            elif action == "delete":
                count, size = self.scan_engine.delete_duplicates(self.scan_result.duplicates)
                self.root.after(0, lambda: self._cleanup_complete("delete", count, size))
                
        except Exception as e:
            self.root.after(0, lambda: self._cleanup_error(str(e)))
    
    def _cleanup_complete(self, action: str, count: int, size: int):
        """Handle cleanup completion."""
        self.cleanup_running = False
        self.move_btn.config(state="normal")
        self.delete_btn.config(state="normal")
        self.progress_bar["value"] = 100
        self.progress_text.config(text=f"{action.title()} completed!")
        self.status_var.set(f"{action.title()} completed")
        
        # Log without emojis to avoid Unicode issues
        self.logger.log_cleanup_complete(action, count, size)
        
        messagebox.showinfo(
            "Cleanup Complete", 
            f"{action.title()} completed successfully!\n\n"
            f"Files {action}d: {count}\n"
            f"Space saved: {self._format_size(size)}"
        )
    
    def _cleanup_error(self, error_msg: str):
        """Handle cleanup error."""
        self.cleanup_running = False
        self.move_btn.config(state="normal")
        self.delete_btn.config(state="normal")
        self.progress_text.config(text="Cleanup failed!")
        self.status_var.set("Cleanup failed")
        
        messagebox.showerror("Cleanup Error", f"Cleanup failed: {error_msg}")
        self.logger.error(f"Cleanup error: {error_msg}")
    
    def _show_summary(self):
        """Show cleanup summary."""
        if not self.scan_result or not self.scan_result.duplicates:
            messagebox.showinfo("Summary", "No duplicates to summarize!")
            return
        
        try:
            summary_text = self._generate_summary()
            messagebox.showinfo("Cleanup Summary", summary_text)
        except Exception as e:
            messagebox.showerror("Summary Error", f"Could not generate summary: {str(e)}")
            self.logger.error(f"Summary error: {str(e)}")
    
    def _generate_summary(self) -> str:
        """Generate summary text."""
        if not self.scan_result or not self.scan_result.duplicates:
            return "No duplicates found."
        
        total_groups = len(self.scan_result.duplicates)
        total_duplicates = sum(len(group) - 1 for group in self.scan_result.duplicates)
        
        # Calculate total size safely
        total_size = 0
        for group in self.scan_result.duplicates:
            for file_path in group[1:]:  # Skip first file (original)
                try:
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
                except (OSError, FileNotFoundError):
                    continue  # Skip files that can't be accessed
        
        summary = f"Duplicate File Summary:\n\n"
        summary += f"Total duplicate groups: {total_groups}\n"
        summary += f"Total duplicate files: {total_duplicates}\n"
        summary += f"Potential space savings: {self._format_size(total_size)}\n\n"
        
        # Add file type breakdown
        file_types = {}
        for group in self.scan_result.duplicates:
            for file_path in group:
                try:
                    ext = os.path.splitext(file_path)[1].lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
                except:
                    continue
        
        if file_types:
            summary += "File types found:\n"
            for ext, count in sorted(file_types.items()):
                summary += f"  {ext or 'No extension'}: {count} files\n"
        
        return summary
    
    def _show_settings(self):
        """Show settings dialog."""
        # Create settings window
        settings_window = tk.Toplevel(self.root)
        settings_window.title("ZCleaner Settings")
        settings_window.geometry("400x300")
        settings_window.configure(bg="#f5f5f5")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Settings content
        tk.Label(settings_window, text="Settings", font=("Segoe UI", 16, "bold"), bg="#f5f5f5").pack(pady=10)
        
        # Theme selection
        theme_frame = tk.LabelFrame(settings_window, text="Theme", font=("Segoe UI", 10, "bold"), bg="#f5f5f5")
        theme_frame.pack(fill="x", padx=10, pady=5)
        
        theme_var = tk.StringVar(value="Light")
        tk.Radiobutton(theme_frame, text="Light", variable=theme_var, value="Light", bg="#f5f5f5").pack(anchor="w", padx=10)
        tk.Radiobutton(theme_frame, text="Dark", variable=theme_var, value="Dark", bg="#f5f5f5").pack(anchor="w", padx=10)
        
        # Close button
        tk.Button(
            settings_window, 
            text="Close", 
            command=settings_window.destroy,
            bg="#4CAF50", 
            fg="white", 
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padx=30
        ).pack(pady=20)
    
    def _save_gui_to_settings(self):
        """Save GUI settings to settings manager."""
        try:
            self.settings_manager.update_scan_settings(
                include_images=self.include_images.get(),
                include_videos=self.include_videos.get(),
                include_documents=self.include_docs.get(),
                min_file_size_mb=float(self.min_size_var.get()),
                max_file_size_mb=float(self.max_size_var.get())
            )
        except ValueError:
            self.logger.warning("Invalid file size values, using defaults")
    
    def _update_progress(self, percentage: int, message: str = ""):
        """Update progress bar and text."""
        if self.root:
            self.progress_bar["value"] = percentage
            if message:
                self.progress_text.config(text=message)
            self.status_var.set(message)
    
    def _update_log(self, message: str):
        """Update log display."""
        if self.root:
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
    
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
    
    def run(self):
        """Run the main application loop."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.critical(f"Fatal error: {str(e)}")
            messagebox.showerror("Fatal Error", f"ZCleaner encountered a fatal error:\n\n{str(e)}") 