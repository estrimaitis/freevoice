#!/usr/bin/env python3
"""freevoice - Free Voice-to-Text for Windows using Whisper."""

import sys
import os
import traceback

def show_error(title: str, message: str):
    """Show error dialog."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except:
        print(f"ERROR: {title}\n{message}")

def main():
    try:
        # Check if model needs downloading (first run)
        from src.paths import get_config_path
        import json
        
        config_path = get_config_path("config.json")
        model_name = "base"
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                model_name = config.get("model", "base")
            except:
                pass
        
        # Check if model is downloaded, show dialog if not
        from src.model_download import is_model_downloaded, download_model_with_progress
        
        if not is_model_downloaded(model_name):
            print(f"Model '{model_name}' not found. Starting download...")
            download_model_with_progress(model_name)
        
        # Start the main app
        from src.app import main as app_main
        app_main()
        
    except Exception as e:
        error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
        show_error("freevoice Error", error_msg)
        
        # Also log to file for debugging
        try:
            log_path = os.path.join(os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else '.', 'freevoice_error.log')
            with open(log_path, 'w') as f:
                f.write(error_msg)
            print(f"Error log written to: {log_path}")
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()
