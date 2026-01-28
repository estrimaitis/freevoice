"""Model download dialog - shows progress when downloading Whisper model."""

import threading
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import os


def is_model_downloaded(model_name: str) -> bool:
    """Check if a model is already downloaded."""
    try:
        from huggingface_hub import scan_cache_dir
        cache_info = scan_cache_dir()
        
        model_id = f"Systran/faster-whisper-{model_name}"
        for repo in cache_info.repos:
            if repo.repo_id == model_id:
                # Check if there are actual files
                for revision in repo.revisions:
                    if revision.files:
                        return True
        return False
    except Exception:
        # Can't check cache, assume not downloaded
        return False


def download_model_with_progress(model_name: str, on_complete: callable = None):
    """Download model with a progress dialog."""
    
    # Check if already downloaded
    if is_model_downloaded(model_name):
        print(f"Model '{model_name}' already downloaded")
        if on_complete:
            on_complete()
        return
    
    # Create progress window
    root = tk.Tk()
    root.title("freevoice")
    root.geometry("400x150")
    root.resizable(False, False)
    
    # Center on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() - 400) // 2
    y = (root.winfo_screenheight() - 150) // 2
    root.geometry(f"400x150+{x}+{y}")
    
    # Keep on top
    root.attributes('-topmost', True)
    
    # Title
    title = tk.Label(root, text="Downloading Whisper Model", font=("Arial", 12, "bold"))
    title.pack(pady=(20, 5))
    
    # Model info
    info = tk.Label(root, text=f"Model: {model_name} (first time setup)", font=("Arial", 10))
    info.pack(pady=(0, 10))
    
    # Progress bar
    progress = ttk.Progressbar(root, mode='indeterminate', length=300)
    progress.pack(pady=10)
    progress.start(10)
    
    # Status
    status = tk.Label(root, text="Downloading... This may take a few minutes.", font=("Arial", 9))
    status.pack(pady=(5, 0))
    
    download_complete = threading.Event()
    download_error = [None]
    
    def do_download():
        try:
            # Actually load the model which triggers download
            from faster_whisper import WhisperModel
            model = WhisperModel(model_name, device="cpu", compute_type="int8")
            del model  # Free memory
            download_complete.set()
        except Exception as e:
            download_error[0] = str(e)
            download_complete.set()
    
    def check_complete():
        if download_complete.is_set():
            progress.stop()
            if download_error[0]:
                status.config(text=f"Error: {download_error[0][:50]}")
                root.after(3000, root.destroy)
            else:
                status.config(text="Download complete!")
                root.after(1000, root.destroy)
        else:
            root.after(100, check_complete)
    
    # Start download in background
    thread = threading.Thread(target=do_download, daemon=True)
    thread.start()
    
    # Check for completion
    root.after(100, check_complete)
    
    # Handle window close
    def on_close():
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_close)
    
    try:
        root.mainloop()
    except:
        pass
    
    if on_complete and not download_error[0]:
        on_complete()


if __name__ == "__main__":
    # Test
    download_model_with_progress("base")
