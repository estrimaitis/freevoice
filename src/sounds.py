"""Sound effects module - plays notification sounds."""

import os
import threading
from .paths import get_asset_path


class SoundPlayer:
    """Plays sound effects for recording feedback."""
    
    def __init__(self):
        """Initialize the sound player."""
        # Sound file paths
        self.start_sound = get_asset_path("on.wav")
        self.stop_sound = get_asset_path("off.wav")
        
        # Check if sounds exist
        self._has_start_sound = os.path.exists(self.start_sound)
        self._has_stop_sound = os.path.exists(self.stop_sound)
        
        if self._has_start_sound:
            print(f"Loaded start sound: {self.start_sound}")
        else:
            print(f"No start sound found at {self.start_sound}")
    
    def _play_wav(self, filepath: str):
        """Play a WAV file (non-blocking)."""
        if not os.path.exists(filepath):
            return
        
        def play():
            try:
                # Use winsound on Windows (built-in, no dependencies)
                import winsound
                winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as e:
                print(f"Could not play sound: {e}")
        
        # Play in background thread to not block
        thread = threading.Thread(target=play, daemon=True)
        thread.start()
    
    def play_start(self):
        """Play the recording start sound."""
        if self._has_start_sound:
            self._play_wav(self.start_sound)
    
    def play_stop(self):
        """Play the recording stop sound."""
        if self._has_stop_sound:
            self._play_wav(self.stop_sound)
