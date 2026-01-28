"""Statistics tracking for freevoice."""

import json
import os
from datetime import datetime
from typing import Optional
from .paths import get_config_path


class Stats:
    """Tracks usage statistics."""
    
    # Average typing speed: ~40 words per minute
    # Average speaking speed: ~150 words per minute
    TYPING_WPM = 40
    SPEAKING_WPM = 150
    
    def __init__(self, stats_path: Optional[str] = None):
        if stats_path is None:
            self.stats_path = get_config_path("stats.json")
        else:
            self.stats_path = stats_path
        
        self.data = self._load()
    
    def _load(self) -> dict:
        """Load stats from file."""
        defaults = {
            "total_recordings": 0,
            "total_words": 0,
            "total_characters": 0,
            "total_audio_seconds": 0.0,
            "first_use": None,
            "last_use": None
        }
        
        try:
            if os.path.exists(self.stats_path):
                with open(self.stats_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Merge with defaults for any missing keys
                    for key, value in defaults.items():
                        if key not in data:
                            data[key] = value
                    return data
        except Exception as e:
            print(f"Error loading stats: {e}")
        
        return defaults
    
    def _save(self):
        """Save stats to file."""
        try:
            with open(self.stats_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            print(f"Error saving stats: {e}")
    
    def record_transcription(self, text: str, audio_duration_seconds: float):
        """Record a completed transcription."""
        now = datetime.now().isoformat()
        
        # Update stats
        self.data["total_recordings"] += 1
        self.data["total_words"] += len(text.split())
        self.data["total_characters"] += len(text)
        self.data["total_audio_seconds"] += audio_duration_seconds
        
        if self.data["first_use"] is None:
            self.data["first_use"] = now
        self.data["last_use"] = now
        
        self._save()
    
    @property
    def total_recordings(self) -> int:
        return self.data["total_recordings"]
    
    @property
    def total_words(self) -> int:
        return self.data["total_words"]
    
    @property
    def total_characters(self) -> int:
        return self.data["total_characters"]
    
    @property
    def total_audio_seconds(self) -> float:
        return self.data["total_audio_seconds"]
    
    @property
    def time_spoken_formatted(self) -> str:
        """Format total audio time as human readable string."""
        seconds = int(self.total_audio_seconds)
        
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    @property
    def time_saved_seconds(self) -> float:
        """Calculate time saved vs typing."""
        if self.total_words == 0:
            return 0
        
        # Time it would take to type at TYPING_WPM
        typing_time = (self.total_words / self.TYPING_WPM) * 60
        
        # Time it took to speak
        speaking_time = self.total_audio_seconds
        
        return max(0, typing_time - speaking_time)
    
    @property
    def time_saved_formatted(self) -> str:
        """Format time saved as human readable string."""
        seconds = int(self.time_saved_seconds)
        
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minutes"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours}h {minutes}m"
            return f"{hours} hours"
    
    @property
    def days_using(self) -> int:
        """Calculate days since first use."""
        if self.data["first_use"] is None:
            return 0
        
        try:
            first = datetime.fromisoformat(self.data["first_use"])
            now = datetime.now()
            return (now - first).days + 1
        except:
            return 0
