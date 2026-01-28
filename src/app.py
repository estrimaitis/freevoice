"""Main freevoice application - system tray app with global hotkey."""

import threading
import time
import json
from typing import Optional
from pynput import keyboard
import pystray
from PIL import Image, ImageDraw
import sys
import os

from .recorder import AudioRecorder
from .transcriber import Transcriber
from .typer import TextTyper
from .dictionary import Dictionary
from .sounds import SoundPlayer
from .scrubber import Scrubber
from .stats import Stats
from .paths import get_config_path, get_asset_path


class FreeVoice:
    """
    freevoice - Voice-to-text with flexible recording modes.
    
    Controls:
    - Hold Ctrl+Alt: Push-to-talk (release to transcribe)
    - Ctrl+Alt + Space: Lock recording (hands-free mode)
    - Ctrl+Alt again: Stop locked recording and transcribe
    - Esc: Cancel recording (no transcription)
    """
    
    def __init__(self):
        """Initialize freevoice."""
        # Load config first
        self._load_config()
        
        # Initialize components
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber(model_size=self.model_size)
        self.typer = TextTyper()
        self.dictionary = Dictionary()
        self.sounds = SoundPlayer()
        self.scrubber = Scrubber()
        self.stats = Stats()
    
    def _load_config(self):
        """Load settings from config file."""
        config_path = get_config_path("config.json")
        
        # Defaults
        self.model_size = "base"
        self.language = None
        self.sounds_enabled = True
        self.shortcut_ptt = "Ctrl+Alt"
        self.shortcut_lock = "Space"
        self.shortcut_cancel = "Escape"
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.model_size = config.get("model", "base")
                self.language = config.get("language")
                self.sounds_enabled = config.get("sounds_enabled", True)
                
                # Load shortcuts
                shortcuts = config.get("shortcuts", {})
                self.shortcut_ptt = shortcuts.get("push_to_talk", "Ctrl+Alt")
                self.shortcut_lock = shortcuts.get("lock_key", "Space")
                self.shortcut_cancel = shortcuts.get("cancel", "Escape")
        except Exception as e:
            print(f"Error loading config: {e}")
        
        # State
        self.is_recording = False
        self.is_locked = False  # Locked mode (hands-free)
        self.is_processing = False
        self.running = True
        self._settings_open = False  # Track if settings window is open
        self._last_transcript = ""  # Store last transcript for copying
        
        # Hotkey tracking
        self._pressed_keys = set()
        self._ptt_was_pressed = False  # Track if PTT combo was just pressed
        
        # System tray
        self.tray_icon = None
    
    def _normalize_key(self, key):
        """Normalize key to handle left/right variants and case."""
        # Map right-side modifiers to left-side
        if key == keyboard.Key.ctrl_r:
            return keyboard.Key.ctrl_l
        if key == keyboard.Key.shift_r:
            return keyboard.Key.shift_l
        if key == keyboard.Key.alt_r:
            return keyboard.Key.alt_l
        
        # Handle character keys
        if hasattr(key, 'char') and key.char is not None:
            char = key.char
            # Convert control characters back to letters (Ctrl+A = '\x01' -> 'a')
            if len(char) == 1 and ord(char) < 32:
                # Control characters: '\x01' is Ctrl+A, '\x02' is Ctrl+B, etc.
                char = chr(ord(char) + ord('a') - 1)
            return keyboard.KeyCode.from_char(char.lower())
        
        # Handle keys without char but with vk (virtual key code)
        if hasattr(key, 'vk') and key.vk is not None:
            # Try to get char from vk for letter keys (A-Z are 65-90)
            if 65 <= key.vk <= 90:
                return keyboard.KeyCode.from_char(chr(key.vk).lower())
        return key
    
    def _parse_key(self, key_str: str):
        """Parse a key string into a pynput key."""
        key_str = key_str.strip().lower()
        key_map = {
            "ctrl": keyboard.Key.ctrl_l,
            "control": keyboard.Key.ctrl_l,
            "alt": keyboard.Key.alt_l,
            "shift": keyboard.Key.shift_l,
            "space": keyboard.Key.space,
            "enter": keyboard.Key.enter,
            "return": keyboard.Key.enter,
            "tab": keyboard.Key.tab,
            "escape": keyboard.Key.esc,
            "esc": keyboard.Key.esc,
            "backspace": keyboard.Key.backspace,
            "delete": keyboard.Key.delete,
            "del": keyboard.Key.delete,
            "insert": keyboard.Key.insert,
            "home": keyboard.Key.home,
            "end": keyboard.Key.end,
            "pageup": keyboard.Key.page_up,
            "pagedown": keyboard.Key.page_down,
            "up": keyboard.Key.up,
            "down": keyboard.Key.down,
            "left": keyboard.Key.left,
            "right": keyboard.Key.right,
            "f1": keyboard.Key.f1,
            "f2": keyboard.Key.f2,
            "f3": keyboard.Key.f3,
            "f4": keyboard.Key.f4,
            "f5": keyboard.Key.f5,
            "f6": keyboard.Key.f6,
            "f7": keyboard.Key.f7,
            "f8": keyboard.Key.f8,
            "f9": keyboard.Key.f9,
            "f10": keyboard.Key.f10,
            "f11": keyboard.Key.f11,
            "f12": keyboard.Key.f12,
        }
        if key_str in key_map:
            return key_map[key_str]
        # Single character (handle both upper and lower)
        if len(key_str) == 1 and key_str.isalnum():
            return keyboard.KeyCode.from_char(key_str.lower())
        return None
    
    def _get_ptt_keys(self) -> set:
        """Get the push-to-talk modifier keys based on config."""
        keys = set()
        for part in self.shortcut_ptt.split("+"):
            key = self._parse_key(part)
            if key:
                keys.add(key)
        return keys if keys else {keyboard.Key.ctrl_l, keyboard.Key.alt_l}
    
    def _get_lock_key(self):
        """Get the lock key based on config."""
        key = self._parse_key(self.shortcut_lock)
        return key if key else keyboard.Key.space
    
    def _get_cancel_key(self):
        """Get the cancel key based on config."""
        key = self._parse_key(self.shortcut_cancel)
        return key if key else keyboard.Key.esc
    
    def _is_ptt_pressed(self) -> bool:
        """Check if push-to-talk keys are pressed."""
        ptt_keys = self._get_ptt_keys()
        return ptt_keys.issubset(self._pressed_keys)
    
    def _on_key_press(self, key):
        """Handle key press events."""
        key = self._normalize_key(key)
        self._pressed_keys.add(key)
        
        # Cancel key cancels recording
        if key == self._get_cancel_key() and self.is_recording:
            self._cancel_recording()
            return
        
        # Check PTT state
        ptt_pressed = self._is_ptt_pressed()
        
        if ptt_pressed:
            # Lock key while PTT held = toggle lock mode
            if key == self._get_lock_key() and self.is_recording and not self.is_locked:
                self._lock_recording()
                return
            
            # PTT pressed while in locked mode = stop recording
            if self.is_locked and not self._ptt_was_pressed:
                self._stop_recording()
                return
            
            # Start recording if not already
            if not self.is_recording and not self.is_processing:
                self._start_recording()
        
        self._ptt_was_pressed = ptt_pressed
    
    def _on_key_release(self, key):
        """Handle key release events."""
        key = self._normalize_key(key)
        
        # Check if PTT key released while recording in push-to-talk mode
        ptt_keys = self._get_ptt_keys()
        if self.is_recording and not self.is_locked:
            if key in ptt_keys:
                self._stop_recording()
        
        # Remove from pressed keys
        self._pressed_keys.discard(key)
        
        # Update PTT state
        self._ptt_was_pressed = self._is_ptt_pressed()
    
    def _lock_recording(self):
        """Lock recording into hands-free mode."""
        self.is_locked = True
        self._update_tray_icon("locked")
        print(f"Recording LOCKED - press {self.shortcut_ptt} to stop, {self.shortcut_cancel} to cancel")
    
    def _start_recording(self):
        """Start recording audio."""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.is_locked = False
        if self.sounds_enabled:
            self.sounds.play_start()
        self.recorder.start()
        self._update_tray_icon("recording")
        print(f"Recording... (release {self.shortcut_ptt} to stop, +{self.shortcut_lock} to lock, {self.shortcut_cancel} to cancel)")
    
    def _stop_recording(self):
        """Stop recording and process the audio."""
        if not self.is_recording:
            return
        
        self.is_recording = False
        self.is_locked = False
        self.is_processing = True
        if self.sounds_enabled:
            self.sounds.play_stop()
        self._update_tray_icon("processing")
        
        # Process in background thread
        thread = threading.Thread(target=self._process_recording)
        thread.daemon = True
        thread.start()
    
    def _cancel_recording(self):
        """Cancel recording without transcribing."""
        if not self.is_recording:
            return
        
        print("Recording CANCELLED")
        self.is_recording = False
        self.is_locked = False
        
        # Stop and discard the audio
        audio_path = self.recorder.stop()
        if audio_path:
            import os
            os.remove(audio_path)
        
        self._update_tray_icon("idle")
    
    def _process_recording(self):
        """Process the recording: transcribe and type."""
        try:
            # Stop recording and get the audio file
            audio_path = self.recorder.stop()
            
            if audio_path:
                # Transcribe
                text = self.transcriber.transcribe_and_cleanup(
                    audio_path,
                    language=self.language
                )
                
                if text:
                    # Apply dictionary replacements (brand names, custom terms, etc.)
                    text = self.dictionary.apply(text)
                    
                    # Remove filler words (um, uh, you know, etc.)
                    text = self.scrubber.scrub(text)
                    
                    # Store for "Copy Last" feature
                    self._last_transcript = text
                    
                    # Record stats
                    self.stats.record_transcription(text, self.recorder.last_duration)
                    
                    # Small delay to let the user refocus if needed
                    time.sleep(0.1)
                    
                    # Type the text
                    self.typer.type_text(text)
                else:
                    print("No speech detected")
            else:
                print("No audio recorded")
                
        except Exception as e:
            print(f"Error processing recording: {e}")
            
        finally:
            self.is_processing = False
            self._update_tray_icon("idle")
    
    def _create_icon(self, state: str = "idle") -> Image.Image:
        """Create a system tray icon using logo.png with state indicator."""
        size = 64
        
        # Try to load custom logo
        logo_path = get_asset_path("logo.png")
        
        if os.path.exists(logo_path):
            # Load and resize the logo
            try:
                image = Image.open(logo_path).convert('RGBA')
                image = image.resize((size, size), Image.Resampling.LANCZOS)
                
                # Add state indicator dot (bottom-right corner) for non-idle states
                if state != "idle":
                    draw = ImageDraw.Draw(image)
                    colors = {
                        "recording": "#FF4A4A",  # Red
                        "locked": "#9B59B6",     # Purple
                        "processing": "#FFB84A"  # Orange
                    }
                    color = colors.get(state, "#4A9EFF")
                    
                    # Draw indicator dot in bottom-right
                    dot_size = 22
                    dot_margin = 0
                    draw.ellipse(
                        [size - dot_size - dot_margin, size - dot_size - dot_margin, 
                         size - dot_margin, size - dot_margin],
                        fill=color,
                        outline="#FFFFFF",
                        width=2
                    )
                
                return image
            except Exception as e:
                print(f"Error loading logo: {e}")
        
        # Fallback: generate simple icon
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        colors = {
            "idle": "#4A9EFF",      # Blue
            "recording": "#FF4A4A", # Red  
            "locked": "#9B59B6",    # Purple
            "processing": "#FFB84A" # Orange
        }
        color = colors.get(state, colors["idle"])
        
        # Simple circle icon
        margin = 8
        draw.ellipse(
            [margin, margin, size - margin, size - margin],
            fill=color
        )
        
        return image
    
    def _update_tray_icon(self, state: str):
        """Update the system tray icon."""
        if self.tray_icon:
            self.tray_icon.icon = self._create_icon(state)
    
    def _on_quit(self, icon, item):
        """Handle quit from system tray."""
        self.running = False
        icon.stop()
    
    def _copy_last_transcript(self, icon, item):
        """Copy the last transcript to clipboard."""
        import subprocess
        if self._last_transcript:
            escaped = self._last_transcript.replace("'", "''")
            try:
                subprocess.run(
                    ['powershell', '-command', f"Set-Clipboard -Value '{escaped}'"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                preview = self._last_transcript[:50] + ('...' if len(self._last_transcript) > 50 else '')
                print(f"Copied: {preview}")
            except Exception as e:
                print(f"Failed to copy: {e}")
        else:
            print("No transcript to copy")
    
    def _open_settings(self, icon=None, item=None):
        """Open the settings GUI."""
        import subprocess
        
        # Prevent opening multiple settings windows
        if self._settings_open:
            return
        
        self._settings_open = True
        
        # Run GUI as a separate process to avoid tkinter threading issues
        # Wait for it to close, then reload settings
        def run_and_reload():
            try:
                process = subprocess.Popen(
                    [sys.executable, "-m", "src.gui"],
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                process.wait()  # Wait for settings window to close
                self._reload_all()
            except Exception as e:
                print(f"Error opening settings: {e}")
            finally:
                self._settings_open = False
        
        thread = threading.Thread(target=run_and_reload, daemon=True)
        thread.start()
    
    def _reload_all(self):
        """Reload all settings after GUI save."""
        print("Reloading settings...")
        
        # Reload config
        old_model = self.model_size
        self._load_config()
        
        # Reload components
        self.dictionary.reload()
        self.scrubber.reload()
        
        # Note: Model change requires restart (too heavy to reload live)
        if self.model_size != old_model:
            print(f"Note: Model changed to '{self.model_size}'. Restart app to apply.")
        
        print("Settings reloaded!")
        self._print_status()
    
    def _print_status(self):
        """Print current status/controls."""
        print(f"\nShortcuts: {self.shortcut_ptt} (talk), +{self.shortcut_lock} (lock), {self.shortcut_cancel} (cancel)")
        print(f"Model: {self.model_size} | Language: {self.language or 'auto'}")
    
    def run(self):
        """Run the application."""
        print("\n" + "=" * 45)
        print("  freevoice - Voice-to-Text for Windows")
        print("=" * 45)
        self._print_status()
        print("\nLoading model...")
        
        # Pre-load the model in background
        def preload():
            self.transcriber.load_model()
            print("\nReady! Hold the hotkey to start recording.\n")
        
        preload_thread = threading.Thread(target=preload)
        preload_thread.daemon = True
        preload_thread.start()
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
        
        # Create system tray menu
        menu = pystray.Menu(
            pystray.MenuItem("Settings", self._open_settings, default=True),
            pystray.MenuItem("Copy Last", self._copy_last_transcript),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit)
        )
        
        # Create and run system tray icon
        self.tray_icon = pystray.Icon(
            "freevoice",
            self._create_icon("idle"),
            "freevoice",
            menu
        )
        
        print("\nRunning in system tray. Double-click icon for settings.")
        self.tray_icon.run()
        
        # Cleanup
        self.keyboard_listener.stop()
        print("freevoice stopped.")


def main():
    """Main entry point."""
    app = FreeVoice()
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nStopping...")


if __name__ == "__main__":
    main()
