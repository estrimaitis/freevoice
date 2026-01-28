"""Keyboard typing module - simulates typing text into the active window."""

from pynput.keyboard import Controller, Key
import time


class TextTyper:
    """Types text into the currently focused input field."""
    
    def __init__(self, typing_delay: float = 0.0):
        """
        Initialize the typer.
        
        Args:
            typing_delay: Delay between keystrokes (0 for instant)
        """
        self.keyboard = Controller()
        self.typing_delay = typing_delay
    
    def type_text(self, text: str, use_clipboard: bool = True):
        """
        Type text into the currently focused field.
        
        Args:
            text: Text to type
            use_clipboard: If True, use clipboard paste for speed (recommended)
        """
        if not text:
            return
        
        if use_clipboard:
            self._paste_text(text)
        else:
            self._type_characters(text)
    
    def _paste_text(self, text: str):
        """Paste text using clipboard (faster for long text), preserving original clipboard."""
        import subprocess
        
        try:
            # Save the current clipboard contents
            saved_clipboard = self._get_clipboard()
            
            # Set our text to clipboard
            escaped_text = text.replace("'", "''")
            subprocess.run(
                ['powershell', '-command', f"Set-Clipboard -Value '{escaped_text}'"],
                check=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # Small delay to ensure clipboard is set
            time.sleep(0.05)
            
            # Paste with Ctrl+V
            self.keyboard.press(Key.ctrl)
            self.keyboard.press('v')
            self.keyboard.release('v')
            self.keyboard.release(Key.ctrl)
            
            # Small delay to ensure paste completes
            time.sleep(0.05)
            
            # Restore the original clipboard
            self._set_clipboard(saved_clipboard)
            
            print(f"Pasted text: {text[:50]}{'...' if len(text) > 50 else ''}")
            
        except Exception as e:
            print(f"Clipboard paste failed: {e}, falling back to typing")
            self._type_characters(text)
    
    def _get_clipboard(self) -> str:
        """Get current clipboard contents."""
        import subprocess
        try:
            result = subprocess.run(
                ['powershell', '-command', 'Get-Clipboard'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.stdout.rstrip('\r\n') if result.returncode == 0 else ""
        except Exception:
            return ""
    
    def _set_clipboard(self, text: str):
        """Set clipboard contents."""
        import subprocess
        if text:
            escaped_text = text.replace("'", "''")
            try:
                subprocess.run(
                    ['powershell', '-command', f"Set-Clipboard -Value '{escaped_text}'"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            except Exception:
                pass  # Silently fail - not critical
    
    def _type_characters(self, text: str):
        """Type text character by character (slower but more compatible)."""
        for char in text:
            self.keyboard.type(char)
            if self.typing_delay > 0:
                time.sleep(self.typing_delay)
        
        print(f"Typed text: {text[:50]}{'...' if len(text) > 50 else ''}")
