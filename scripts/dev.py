#!/usr/bin/env python3
"""
Development mode - auto-restarts when you change files.
Press Ctrl+C to stop.
"""

import subprocess
import sys
import time
from pathlib import Path

# Project root is one level up from scripts/
PROJECT_ROOT = Path(__file__).parent.parent

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError:
    print("Installing watchdog for auto-reload...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "watchdog"])
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler


class ReloadHandler(FileSystemEventHandler):
    """Watches for file changes and triggers reload."""
    
    def __init__(self, callback):
        self.callback = callback
        self.last_reload = 0
        self.debounce = 1.0  # Minimum seconds between reloads
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Only watch Python files
        if not event.src_path.endswith('.py'):
            return
        
        # Debounce rapid changes
        now = time.time()
        if now - self.last_reload < self.debounce:
            return
        
        self.last_reload = now
        print(f"\n>>> File changed: {event.src_path}")
        self.callback()


class DevServer:
    """Runs the app with auto-reload."""
    
    def __init__(self):
        self.process = None
        self.observer = None
    
    def start_app(self):
        """Start or restart the application."""
        self.stop_app()
        
        print("\n" + "=" * 50)
        print("Starting freevoice (dev mode)...")
        print("=" * 50 + "\n")
        
        # Start the app as a subprocess
        self.process = subprocess.Popen(
            [sys.executable, "main.py"] + sys.argv[1:],
            cwd=PROJECT_ROOT
        )
    
    def stop_app(self):
        """Stop the running application."""
        if self.process:
            print("\nStopping app...")
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
    
    def run(self):
        """Run the dev server with file watching."""
        print("\n" + "=" * 50)
        print("freevoice Development Mode")
        print("=" * 50)
        print("Watching for file changes...")
        print("Press Ctrl+C to stop")
        print("=" * 50 + "\n")
        
        # Set up file watcher
        handler = ReloadHandler(self.start_app)
        self.observer = Observer()
        
        # Watch src directory
        self.observer.schedule(handler, str(PROJECT_ROOT / "src"), recursive=True)
        
        # Also watch main.py
        self.observer.schedule(handler, str(PROJECT_ROOT), recursive=False)
        
        self.observer.start()
        
        # Start the app
        self.start_app()
        
        try:
            while True:
                time.sleep(1)
                # Check if process died
                if self.process and self.process.poll() is not None:
                    print("\nApp crashed! Waiting for file changes to restart...")
                    self.process = None
        except KeyboardInterrupt:
            print("\n\nShutting down dev server...")
        finally:
            self.stop_app()
            self.observer.stop()
            self.observer.join()


if __name__ == "__main__":
    dev = DevServer()
    dev.run()
