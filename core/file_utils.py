# core/file_utils.py

import tkinter as tk
from tkinter import filedialog
import os
import sys

class FileUtils:
    @staticmethod
    def select_log_directory() -> str:
        """
        Select the Conan Exiles log directory using a GUI dialog
        
        Returns:
            str: Selected directory path
            
        Raises:
            SystemExit: If no directory is selected or directory doesn't exist
        """
        print("\nPlease select your Conan Exiles logs folder.")
        print("It's usually located in: <Your Server Path>/ConanSandbox/Saved/Logs/")
        
        root = tk.Tk()
        root.withdraw()
        
        dir_path = filedialog.askdirectory(
            title="Select Conan Exiles Logs Directory"
        )
        
        if not dir_path:
            print("No directory selected. Exiting...")
            sys.exit(1)
            
        if not os.path.exists(dir_path):
            print("Selected directory does not exist. Exiting...")
            sys.exit(1)
            
        return dir_path