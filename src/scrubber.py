"""Text scrubber module - removes filler words and cleans up text."""

import json
import os
import re
from typing import List, Optional
from .paths import get_config_path


class Scrubber:
    """Removes filler words and phrases from transcribed text."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the scrubber.
        
        Args:
            config_path: Path to config.json file
        """
        if config_path is None:
            self.config_path = get_config_path("config.json")
        else:
            self.config_path = config_path
        
        self.enabled = True
        self.fillers: List[str] = []
        self.load()
    
    def load(self):
        """Load settings from config file."""
        if not os.path.exists(self.config_path):
            print(f"No config file found at {self.config_path}, using defaults")
            self._use_defaults()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            scrubber_config = data.get("scrubber", {})
            self.enabled = scrubber_config.get("enabled", True)
            self.fillers = scrubber_config.get("fillers", [])
            
            print(f"Scrubber: {'enabled' if self.enabled else 'disabled'} ({len(self.fillers)} fillers)")
            
        except Exception as e:
            print(f"Error loading config: {e}")
            self._use_defaults()
    
    def _use_defaults(self):
        """Set default fillers."""
        self.enabled = True
        self.fillers = ["um", "uh", "uhm", "uhh", "ah", "ahh", "er", "err", "hmm", "hm", "mm", "mhm"]
    
    def save_enabled_state(self):
        """Save the enabled state to config."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {}
            
            if "scrubber" not in data:
                data["scrubber"] = {}
            
            data["scrubber"]["enabled"] = self.enabled
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def toggle(self) -> bool:
        """Toggle scrubber on/off and save state."""
        self.enabled = not self.enabled
        self.save_enabled_state()
        print(f"Scrubber: {'enabled' if self.enabled else 'disabled'}")
        return self.enabled
    
    def scrub(self, text: str) -> str:
        """
        Remove filler sounds from text.
        
        Args:
            text: The transcribed text
            
        Returns:
            Cleaned text with fillers removed
        """
        if not self.enabled or not text:
            return text
        
        result = text
        
        # Remove fillers (longer matches first to handle multi-word fillers)
        sorted_fillers = sorted(self.fillers, key=len, reverse=True)
        for filler in sorted_fillers:
            # Match filler with word boundaries, case-insensitive
            # Also match with surrounding punctuation/commas
            pattern = r'(?i)\b' + re.escape(filler) + r'\b[,.]?\s*'
            result = re.sub(pattern, ' ', result)
        
        # Clean up the text
        result = self._cleanup(result)
        
        if result != text:
            print(f"Scrubbed: '{text[:50]}...' -> '{result[:50]}...'")
        
        return result
    
    def _cleanup(self, text: str) -> str:
        """Clean up spacing and punctuation."""
        # Multiple spaces to single space
        text = re.sub(r'\s+', ' ', text)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        text = re.sub(r'([.,!?])\s*([.,!?])', r'\1', text)
        
        # Fix sentence starts (capitalize after period)
        text = re.sub(r'([.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
        
        # Capitalize first letter
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def reload(self):
        """Reload settings from config file."""
        print("Reloading scrubber config...")
        self.load()
