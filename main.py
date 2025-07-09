#!/usr/bin/env python3
"""
ZCleaner - Smart Duplicate File Finder and Cleaner
Main application entry point.
"""

import sys
import os
import traceback
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.gui.main_window import MainWindow
    from src.utils.logger import ZCleanerLogger
    
    def main():
        """Main application entry point."""
        # Setup logger
        logger = ZCleanerLogger()
        
        try:
            logger.info("Starting ZCleaner application...")
            
            # Create and run main window
            app = MainWindow()
            app.run()
            
            logger.info("ZCleaner application closed.")
            
        except KeyboardInterrupt:
            logger.info("Application interrupted by user.")
        except Exception as e:
            logger.critical(f"Fatal error: {str(e)}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            
            # Show error dialog using tkinter
            try:
                import tkinter as tk
                from tkinter import messagebox
                
                # Create a temporary root window for the error dialog
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                
                messagebox.showerror(
                    "Fatal Error",
                    f"ZCleaner encountered a fatal error:\n\n{str(e)}\n\n"
                    f"Please check the logs for more details."
                )
                
                root.destroy()
            except:
                # Fallback to console output if tkinter fails
                print(f"Fatal error: {str(e)}")
                print("Please check the logs for more details.")
    
    if __name__ == "__main__":
        main()

except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure all required packages are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"Failed to start ZCleaner: {e}")
    traceback.print_exc()
    sys.exit(1) 