"""freevoice Settings GUI - Clean, tabbed design."""

import customtkinter as ctk
import json
import os
import sys
import threading
import time
from typing import Callable, Optional
from pathlib import Path

# Add parent to path for imports when run as module
if __name__ == "__main__" or "src.gui" in sys.modules:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.startup import is_startup_enabled, set_startup
from src.paths import get_config_path, get_asset_path


# Model information
MODELS = {
    "tiny": {
        "name": "Tiny",
        "desc": "Fastest, basic accuracy",
        "size": "~75 MB",
        "quality": "★☆☆☆☆"
    },
    "base": {
        "name": "Base", 
        "desc": "Fast, good for most uses",
        "size": "~150 MB",
        "quality": "★★☆☆☆"
    },
    "small": {
        "name": "Small",
        "desc": "Balanced speed & accuracy",
        "size": "~500 MB",
        "quality": "★★★☆☆"
    },
    "medium": {
        "name": "Medium",
        "desc": "High accuracy, slower",
        "size": "~1.5 GB",
        "quality": "★★★★☆"
    },
    "large-v3": {
        "name": "Large",
        "desc": "Best accuracy, slowest",
        "size": "~3 GB",
        "quality": "★★★★★"
    }
}


class SettingsWindow:
    """Modern tabbed settings window."""
    
    def __init__(self, on_save: Optional[Callable] = None):
        self.on_save = on_save
        self.root = None
        self.current_tab = "model"
        
        # Paths
        self.config_path = get_config_path("config.json")
        self.dictionary_path = get_config_path("dictionary.json")
        self.stats_path = get_config_path("stats.json")
        
        # Load settings
        self.config = self._load_json(self.config_path) or {}
        self.dictionary = self._load_json(self.dictionary_path) or {}
        self.stats = self._load_json(self.stats_path) or {}
        
        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Tab buttons reference
        self.tab_buttons = {}
        self.content_frames = {}
    
    def _load_json(self, path: str) -> dict:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def _save_json(self, path: str, data: dict):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving {path}: {e}")
    
    def _get_model_cache_path(self) -> Path:
        cache_dir = os.environ.get("HF_HOME") or os.environ.get("HUGGINGFACE_HUB_CACHE")
        if not cache_dir:
            cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")
        return Path(cache_dir)
    
    def _is_model_downloaded(self, model_id: str) -> bool:
        cache_path = self._get_model_cache_path()
        model_variants = [
            f"models--Systran--faster-whisper-{model_id}",
            f"models--guillaumekln--faster-whisper-{model_id}",
        ]
        for variant in model_variants:
            model_path = cache_path / variant
            if model_path.exists():
                snapshots = model_path / "snapshots"
                if snapshots.exists() and any(snapshots.iterdir()):
                    return True
        return False
    
    def show(self):
        """Show the settings window."""
        self.root = ctk.CTk()
        self.root.title("freevoice")
        self.root.geometry("700x580")
        self.root.resizable(False, False)
        
        # Set window icon
        logo_path = get_asset_path("logo.png")
        if os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((32, 32), Image.Resampling.LANCZOS)
                self._window_icon = ImageTk.PhotoImage(logo_img)
                self.root.iconphoto(True, self._window_icon)
            except Exception:
                pass
        
        # Main layout: sidebar + content
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.pack(fill="both", expand=True)
        
        # === LEFT SIDEBAR ===
        sidebar = ctk.CTkFrame(main_frame, width=180, corner_radius=0, fg_color="#1a1a1a")
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        
        # Logo/Title with image
        title_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        title_frame.pack(fill="x", padx=20, pady=(25, 30))
        
        # Try to load logo for sidebar
        if os.path.exists(logo_path):
            try:
                from PIL import Image
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)
                self._sidebar_logo = ctk.CTkImage(logo_img, size=(40, 40))
                
                logo_row = ctk.CTkFrame(title_frame, fg_color="transparent")
                logo_row.pack(anchor="w", pady=(0, 8))
                
                ctk.CTkLabel(
                    logo_row,
                    image=self._sidebar_logo,
                    text=""
                ).pack(side="left", padx=(0, 10))
                
                ctk.CTkLabel(
                    logo_row,
                    text="freevoice",
                    font=ctk.CTkFont(size=20, weight="bold")
                ).pack(side="left")
            except Exception:
                ctk.CTkLabel(
                    title_frame,
                    text="freevoice",
                    font=ctk.CTkFont(size=22, weight="bold")
                ).pack(anchor="w")
        else:
            ctk.CTkLabel(
                title_frame,
                text="freevoice",
                font=ctk.CTkFont(size=22, weight="bold")
            ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_frame,
            text="Settings",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(anchor="w")
        
        # Navigation buttons
        nav_items = [
            ("model", "Model"),
            ("language", "Language"),
            ("shortcuts", "Shortcuts"),
            ("general", "General"),
            ("cleanup", "Text Cleanup"),
            ("dictionary", "Dictionary"),
            ("stats", "Statistics"),
            ("about", "About"),
        ]
        
        for tab_id, label in nav_items:
            btn = ctk.CTkButton(
                sidebar,
                text=f"  {label}",
                font=ctk.CTkFont(size=14),
                anchor="w",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                text_color="white",
                hover_color="#333333",
                command=lambda t=tab_id: self._switch_tab(t)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.tab_buttons[tab_id] = btn
        
        # Spacer
        ctk.CTkFrame(sidebar, fg_color="transparent", height=1).pack(fill="both", expand=True)
        
        # Save button at bottom of sidebar
        self.save_btn = ctk.CTkButton(
            sidebar,
            text="Save",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            corner_radius=8,
            command=self._save_settings
        )
        self.save_btn.pack(fill="x", padx=15, pady=(10, 20))
        
        # === RIGHT CONTENT AREA ===
        self.content_area = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True, padx=30, pady=30)
        
        # Create all tab content frames
        self._create_model_tab()
        self._create_language_tab()
        self._create_shortcuts_tab()
        self._create_general_tab()
        self._create_cleanup_tab()
        self._create_dictionary_tab()
        self._create_stats_tab()
        self._create_about_tab()
        
        # Show initial tab
        self._switch_tab("model")
        
        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 700) // 2
        y = (self.root.winfo_screenheight() - 580) // 2
        self.root.geometry(f"700x580+{x}+{y}")
        
        self.root.mainloop()
    
    def _switch_tab(self, tab_id: str):
        """Switch to a different tab."""
        self.current_tab = tab_id
        
        # Update button styles
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.configure(fg_color="#333333")
            else:
                btn.configure(fg_color="transparent")
        
        # Show/hide content frames
        for tid, frame in self.content_frames.items():
            if tid == tab_id:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
    
    def _create_tab_header(self, parent, title: str, subtitle: str):
        """Create a tab header."""
        ctk.CTkLabel(
            parent,
            text=title,
            font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            parent,
            text=subtitle,
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 25))
    
    def _create_model_tab(self):
        """Create the model selection tab."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.content_frames["model"] = frame
        
        self._create_tab_header(frame, "Transcription Model", "Choose quality vs speed")
        
        # Model selection
        current_model = self.config.get("model", "base")
        self.model_var = ctk.StringVar(value=current_model)
        
        # Container for model cards (so we can refresh)
        self.models_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self.models_frame.pack(fill="both", expand=True)
        
        self._populate_model_cards()
    
    def _populate_model_cards(self):
        """Populate the model cards (can be called to refresh)."""
        # Clear existing cards
        for widget in self.models_frame.winfo_children():
            widget.destroy()
        
        # Create model cards
        for model_id, info in MODELS.items():
            self._create_model_card(self.models_frame, model_id, info)
    
    def _refresh_model_tab(self):
        """Refresh the model tab to show updated download status."""
        self._populate_model_cards()
    
    def _create_model_card(self, parent, model_id: str, info: dict):
        """Create a model selection card."""
        is_downloaded = self._is_model_downloaded(model_id)
        is_selected = self.model_var.get() == model_id
        
        card = ctk.CTkFrame(parent, corner_radius=10, height=60)
        card.pack(fill="x", pady=4)
        card.pack_propagate(False)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Left side: radio + info
        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="y")
        
        radio = ctk.CTkRadioButton(
            left,
            text="",
            variable=self.model_var,
            value=model_id,
            width=20
        )
        radio.pack(side="left", padx=(0, 10))
        
        info_frame = ctk.CTkFrame(left, fg_color="transparent")
        info_frame.pack(side="left")
        
        ctk.CTkLabel(
            info_frame,
            text=info["name"],
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            info_frame,
            text=info["desc"],
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w")
        
        # Right side: status + quality
        right = ctk.CTkFrame(inner, fg_color="transparent")
        right.pack(side="right", fill="y")
        
        # Quality stars
        ctk.CTkLabel(
            right,
            text=info["quality"],
            font=ctk.CTkFont(size=13)
        ).pack(anchor="e")
        
        # Download status
        if is_downloaded:
            status_text = "✓ Ready"
            status_color = "#4CAF50"
        else:
            status_text = f"↓ {info['size']}"
            status_color = "#FF9800"
        
        ctk.CTkLabel(
            right,
            text=status_text,
            font=ctk.CTkFont(size=12),
            text_color=status_color
        ).pack(anchor="e")
    
    def _create_language_tab(self):
        """Create the language selection tab."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.content_frames["language"] = frame
        
        self._create_tab_header(frame, "Language", "What language will you speak?")
        
        languages = [
            ("Auto-detect", None),
            ("English", "en"),
            ("Spanish", "es"),
            ("French", "fr"),
            ("German", "de"),
            ("Italian", "it"),
            ("Portuguese", "pt"),
            ("Dutch", "nl"),
            ("Polish", "pl"),
            ("Russian", "ru"),
            ("Chinese", "zh"),
            ("Japanese", "ja"),
            ("Korean", "ko"),
        ]
        self._languages = languages
        
        current_lang = self.config.get("language")
        display_lang = "Auto-detect"
        for name, code in languages:
            if code == current_lang:
                display_lang = name
                break
        
        self.language_var = ctk.StringVar(value=display_lang)
        
        # Language cards
        lang_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        lang_frame.pack(fill="both", expand=True)
        
        for name, code in languages:
            self._create_language_option(lang_frame, name, code)
    
    def _create_language_option(self, parent, name: str, code: Optional[str]):
        """Create a language option."""
        card = ctk.CTkFrame(parent, corner_radius=8, height=45)
        card.pack(fill="x", pady=3)
        card.pack_propagate(False)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=15, pady=8)
        
        radio = ctk.CTkRadioButton(
            inner,
            text=name,
            variable=self.language_var,
            value=name,
            font=ctk.CTkFont(size=14)
        )
        radio.pack(side="left")
        
        if code:
            ctk.CTkLabel(
                inner,
                text=code.upper(),
                font=ctk.CTkFont(size=12),
                text_color="gray"
            ).pack(side="right")
    
    def _create_shortcuts_tab(self):
        """Create the shortcuts settings tab."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.content_frames["shortcuts"] = frame
        
        self._create_tab_header(frame, "Shortcuts", "Customize your hotkeys")
        
        # Get current shortcuts from config
        shortcuts = self.config.get("shortcuts", {})
        default_ptt = shortcuts.get("push_to_talk", "Ctrl+Alt")
        default_lock = shortcuts.get("lock_key", "Space")
        default_cancel = shortcuts.get("cancel", "Escape")
        
        # Push to Talk
        self.ptt_var = ctk.StringVar(value=default_ptt)
        self._create_shortcut_input(frame, "Push to Talk", "Hold to record", self.ptt_var)
        
        # Lock Key
        self.lock_var = ctk.StringVar(value=default_lock)
        self._create_shortcut_input(frame, "Lock Recording", "Press while recording for hands-free", self.lock_var)
        
        # Cancel Key
        self.cancel_var = ctk.StringVar(value=default_cancel)
        self._create_shortcut_input(frame, "Cancel", "Press to cancel recording", self.cancel_var)
        
        # Note
        ctk.CTkLabel(
            frame,
            text="Restart app after changing shortcuts",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w", pady=(15, 0))
    
    def _create_shortcut_input(self, parent, title: str, subtitle: str, variable: ctk.StringVar):
        """Create a shortcut input with click-to-record functionality."""
        card = ctk.CTkFrame(parent, corner_radius=12)
        card.pack(fill="x", pady=(0, 8))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=12)
        
        # Title row
        ctk.CTkLabel(
            inner,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            inner,
            text=subtitle,
            font=ctk.CTkFont(size=11),
            text_color="gray"
        ).pack(anchor="w", pady=(1, 8))
        
        # Input row
        input_row = ctk.CTkFrame(inner, fg_color="transparent")
        input_row.pack(fill="x")
        
        # Shortcut display button (click to record)
        shortcut_btn = ctk.CTkButton(
            input_row,
            text=variable.get() or "Click to set",
            width=180,
            height=32,
            font=ctk.CTkFont(size=13),
            fg_color="#333333",
            hover_color="#444444",
            border_width=1,
            border_color="#555555"
        )
        shortcut_btn.pack(side="left")
        
        # Store reference for updating
        shortcut_btn._variable = variable
        shortcut_btn._is_recording = False
        
        def start_recording():
            if shortcut_btn._is_recording:
                return
            shortcut_btn._is_recording = True
            shortcut_btn.configure(text="Press keys...", fg_color="#1a3a5c", border_color="#3a7abf")
            shortcut_btn._pressed_keys = set()
            shortcut_btn._key_names = []
            
            # Bind keyboard events to the root window
            self.root.bind('<KeyPress>', lambda e: on_key_press(e, shortcut_btn))
            self.root.bind('<KeyRelease>', lambda e: on_key_release(e, shortcut_btn))
            self.root.focus_set()
        
        def on_key_press(event, btn):
            if not btn._is_recording:
                return "break"
            
            key_name = self._get_key_name(event)
            if key_name and key_name not in btn._pressed_keys:
                btn._pressed_keys.add(key_name)
                btn._key_names.append(key_name)
                # Update display
                display = "+".join(btn._key_names)
                btn.configure(text=display)
            return "break"
        
        def on_key_release(event, btn):
            if not btn._is_recording:
                return "break"
            
            key_name = self._get_key_name(event)
            if key_name:
                btn._released_count = getattr(btn, '_released_count', 0) + 1
                # Wait for all keys to be released
                self.root.after(200, lambda: check_finish(btn))
            return "break"
        
        def check_finish(btn):
            if not btn._is_recording:
                return
            # Finish if we have keys recorded
            if btn._key_names:
                finish_recording(btn)
        
        def finish_recording(btn):
            if not btn._is_recording:
                return
            btn._is_recording = False
            
            # Unbind events
            try:
                self.root.unbind('<KeyPress>')
                self.root.unbind('<KeyRelease>')
            except:
                pass
            
            # Set the value
            if btn._key_names:
                # Sort to put modifiers first
                modifiers = ['Ctrl', 'Alt', 'Shift']
                sorted_keys = []
                for mod in modifiers:
                    if mod in btn._key_names:
                        sorted_keys.append(mod)
                for key in btn._key_names:
                    if key not in modifiers:
                        sorted_keys.append(key)
                
                value = "+".join(sorted_keys)
                btn._variable.set(value)
                btn.configure(text=value, fg_color="#333333", border_color="#555555")
            else:
                current = btn._variable.get()
                btn.configure(text=current or "Click to set", fg_color="#333333", border_color="#555555")
        
        shortcut_btn.configure(command=start_recording)
        
        # Clear button
        clear_btn = ctk.CTkButton(
            input_row,
            text="Clear",
            width=60,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color="#444444",
            hover_color="#555555",
            command=lambda: (variable.set(""), shortcut_btn.configure(text="Click to set"))
        )
        clear_btn.pack(side="left", padx=(10, 0))
    
    def _get_key_name(self, event) -> str:
        """Get a readable key name from a tkinter event."""
        # Map special keys
        special_keys = {
            'Control_L': 'Ctrl', 'Control_R': 'Ctrl',
            'Alt_L': 'Alt', 'Alt_R': 'Alt',
            'Shift_L': 'Shift', 'Shift_R': 'Shift',
            'space': 'Space',
            'Return': 'Enter',
            'Escape': 'Escape',
            'BackSpace': 'Backspace',
            'Tab': 'Tab',
            'Delete': 'Delete',
            'Insert': 'Insert',
            'Home': 'Home',
            'End': 'End',
            'Prior': 'PageUp',
            'Next': 'PageDown',
            'Up': 'Up', 'Down': 'Down', 'Left': 'Left', 'Right': 'Right',
        }
        
        keysym = event.keysym
        
        if keysym in special_keys:
            return special_keys[keysym]
        
        # Single character
        if len(keysym) == 1 and keysym.isalnum():
            return keysym.upper()
        
        # F keys
        if keysym.startswith('F') and keysym[1:].isdigit():
            return keysym
        
        return None
    
    def _create_general_tab(self):
        """Create the general settings tab."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.content_frames["general"] = frame
        
        self._create_tab_header(frame, "General", "App settings")
        
        # Startup option
        card1 = ctk.CTkFrame(frame, corner_radius=12)
        card1.pack(fill="x", pady=(0, 10))
        
        inner1 = ctk.CTkFrame(card1, fg_color="transparent")
        inner1.pack(fill="x", padx=20, pady=15)
        
        self.startup_var = ctk.BooleanVar(value=is_startup_enabled())
        
        row1 = ctk.CTkFrame(inner1, fg_color="transparent")
        row1.pack(fill="x")
        
        text_frame1 = ctk.CTkFrame(row1, fg_color="transparent")
        text_frame1.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            text_frame1,
            text="Launch at Startup",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_frame1,
            text="Start freevoice when Windows starts",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w")
        
        switch1 = ctk.CTkSwitch(row1, text="", variable=self.startup_var, width=50)
        switch1.pack(side="right")
        
        # Sounds option
        card2 = ctk.CTkFrame(frame, corner_radius=12)
        card2.pack(fill="x")
        
        inner2 = ctk.CTkFrame(card2, fg_color="transparent")
        inner2.pack(fill="x", padx=20, pady=15)
        
        self.sounds_var = ctk.BooleanVar(value=self.config.get("sounds_enabled", True))
        
        row2 = ctk.CTkFrame(inner2, fg_color="transparent")
        row2.pack(fill="x")
        
        text_frame2 = ctk.CTkFrame(row2, fg_color="transparent")
        text_frame2.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            text_frame2,
            text="Notification Sounds",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_frame2,
            text="Play a sound when recording starts",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w")
        
        switch2 = ctk.CTkSwitch(row2, text="", variable=self.sounds_var, width=50)
        switch2.pack(side="right")
    
    def _create_cleanup_tab(self):
        """Create the text cleanup settings tab."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.content_frames["cleanup"] = frame
        
        self._create_tab_header(frame, "Text Cleanup", "Remove filler words automatically")
        
        scrubber_config = self.config.get("scrubber", {})
        
        # Toggle card
        card1 = ctk.CTkFrame(frame, corner_radius=12)
        card1.pack(fill="x", pady=(0, 15))
        
        inner1 = ctk.CTkFrame(card1, fg_color="transparent")
        inner1.pack(fill="x", padx=20, pady=20)
        
        self.scrubber_var = ctk.BooleanVar(value=scrubber_config.get("enabled", False))
        
        row = ctk.CTkFrame(inner1, fg_color="transparent")
        row.pack(fill="x")
        
        text_frame = ctk.CTkFrame(row, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        
        ctk.CTkLabel(
            text_frame,
            text="Remove Filler Words",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            text_frame,
            text="Automatically remove 'um', 'uh', etc.",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(anchor="w")
        
        switch = ctk.CTkSwitch(row, text="", variable=self.scrubber_var, width=50)
        switch.pack(side="right")
        
        # Filler words card
        card2 = ctk.CTkFrame(frame, corner_radius=12)
        card2.pack(fill="both", expand=True)
        
        inner2 = ctk.CTkFrame(card2, fg_color="transparent")
        inner2.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            inner2,
            text="Words to remove (comma separated)",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 10))
        
        fillers = scrubber_config.get("fillers", [])
        self.fillers_text = ctk.CTkTextbox(
            inner2, 
            font=ctk.CTkFont(size=13),
            wrap="word"
        )
        self.fillers_text.pack(fill="both", expand=True)
        self.fillers_text.insert("1.0", ", ".join(fillers))
        # Disable horizontal scrollbar
        self.fillers_text._textbox.configure(xscrollcommand=None)
        self.fillers_text.configure(wrap="word")
    
    def _create_dictionary_tab(self):
        """Create the dictionary settings tab."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.content_frames["dictionary"] = frame
        
        self._create_tab_header(frame, "Custom Dictionary", "Brand names and special terms")
        
        ctk.CTkLabel(
            frame,
            text="Words that should be recognized exactly as spelled (one per line)",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 15))
        
        terms = self.dictionary.get("terms", [])
        self.terms_text = ctk.CTkTextbox(
            frame, 
            font=ctk.CTkFont(size=14),
            wrap="word"
        )
        self.terms_text.pack(fill="both", expand=True)
        self.terms_text.insert("1.0", "\n".join(terms))
        # Disable horizontal scrollbar
        self.terms_text._textbox.configure(xscrollcommand=None)
        self.terms_text.configure(wrap="word")
    
    def _create_stats_tab(self):
        """Create the statistics tab."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.content_frames["stats"] = frame
        
        self._create_tab_header(frame, "Statistics", "Your voice-to-text journey")
        
        # Get stats values
        total_recordings = self.stats.get("total_recordings", 0)
        total_words = self.stats.get("total_words", 0)
        total_chars = self.stats.get("total_characters", 0)
        total_seconds = self.stats.get("total_audio_seconds", 0)
        
        # Calculate time saved (typing at 40 WPM vs speaking)
        typing_time = (total_words / 40) * 60 if total_words > 0 else 0
        time_saved = max(0, typing_time - total_seconds)
        
        # Format time spoken
        if total_seconds < 60:
            time_spoken = f"{int(total_seconds)}s"
        elif total_seconds < 3600:
            time_spoken = f"{int(total_seconds // 60)}m {int(total_seconds % 60)}s"
        else:
            hours = int(total_seconds // 3600)
            mins = int((total_seconds % 3600) // 60)
            time_spoken = f"{hours}h {mins}m"
        
        # Format time saved
        if time_saved < 60:
            time_saved_str = f"{int(time_saved)} seconds"
        elif time_saved < 3600:
            time_saved_str = f"{int(time_saved // 60)} minutes"
        else:
            hours = int(time_saved // 3600)
            mins = int((time_saved % 3600) // 60)
            time_saved_str = f"{hours}h {mins}m"
        
        # Stats grid
        stats_data = [
            ("Recordings", f"{total_recordings:,}"),
            ("Words Transcribed", f"{total_words:,}"),
            ("Characters", f"{total_chars:,}"),
            ("Time Spoken", time_spoken),
        ]
        
        for label, value in stats_data:
            self._create_stat_card(frame, label, value)
        
        # Time saved highlight
        if total_words > 0:
            highlight_card = ctk.CTkFrame(frame, corner_radius=12)
            highlight_card.pack(fill="x", pady=(15, 0))
            
            highlight_inner = ctk.CTkFrame(highlight_card, fg_color="transparent")
            highlight_inner.pack(fill="x", padx=20, pady=15)
            
            ctk.CTkLabel(
                highlight_inner,
                text="Time Saved vs Typing",
                font=ctk.CTkFont(size=13),
                text_color="gray"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                highlight_inner,
                text=time_saved_str,
                font=ctk.CTkFont(size=24, weight="bold"),
                text_color="#4CAF50"
            ).pack(anchor="w", pady=(5, 0))
            
            ctk.CTkLabel(
                highlight_inner,
                text="Based on average typing speed of 40 WPM",
                font=ctk.CTkFont(size=11),
                text_color="#555555"
            ).pack(anchor="w", pady=(3, 0))
    
    def _create_stat_card(self, parent, label: str, value: str):
        """Create a stat display card."""
        card = ctk.CTkFrame(parent, corner_radius=10, height=70)
        card.pack(fill="x", pady=4)
        card.pack_propagate(False)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=20, pady=12)
        
        ctk.CTkLabel(
            inner,
            text=label,
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            inner,
            text=value,
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(anchor="w")
    
    def _create_about_tab(self):
        """Create the about tab."""
        frame = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.content_frames["about"] = frame
        
        self._create_tab_header(frame, "About", "freevoice")
        
        # Description
        ctk.CTkLabel(
            frame,
            text="Free, open-source voice-to-text for Windows.",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack(anchor="w", pady=(0, 20))
        
        # How it works
        ctk.CTkLabel(
            frame,
            text="How it works",
            font=ctk.CTkFont(size=15, weight="bold")
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            frame,
            text="Hold Ctrl+Alt to record, release to transcribe.\nText is typed wherever your cursor is.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            justify="left"
        ).pack(anchor="w", pady=(0, 20))
        
        # Credits card
        credits_card = ctk.CTkFrame(frame, corner_radius=12)
        credits_card.pack(fill="x", pady=(0, 15))
        
        credits_inner = ctk.CTkFrame(credits_card, fg_color="transparent")
        credits_inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            credits_inner,
            text="Powered by",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            credits_inner,
            text="OpenAI Whisper",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(2, 5))
        
        ctk.CTkLabel(
            credits_inner,
            text="Open-source speech recognition model by OpenAI",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(anchor="w")
        
        link_btn = ctk.CTkButton(
            credits_inner,
            text="github.com/openai/whisper",
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            text_color="#4A9EFF",
            hover_color="#333333",
            anchor="w",
            height=25,
            command=lambda: self._open_url("https://github.com/openai/whisper")
        )
        link_btn.pack(anchor="w", pady=(5, 0))
        
        # Author card
        author_card = ctk.CTkFrame(frame, corner_radius=12)
        author_card.pack(fill="x", pady=(0, 15))
        
        author_inner = ctk.CTkFrame(author_card, fg_color="transparent")
        author_inner.pack(fill="x", padx=20, pady=15)
        
        ctk.CTkLabel(
            author_inner,
            text="Created by",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            author_inner,
            text="@estrimaitis",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", pady=(2, 5))
        
        author_link = ctk.CTkButton(
            author_inner,
            text="github.com/estrimaitis/freevoice",
            font=ctk.CTkFont(size=13),
            fg_color="transparent",
            text_color="#4A9EFF",
            hover_color="#333333",
            anchor="w",
            height=25,
            command=lambda: self._open_url("https://github.com/estrimaitis/freevoice")
        )
        author_link.pack(anchor="w", pady=(5, 0))
        
        # Open source note
        ctk.CTkLabel(
            frame,
            text="freevoice is open source",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", pady=(10, 5))
        
        ctk.CTkLabel(
            frame,
            text="MIT License - use it however you want!",
            font=ctk.CTkFont(size=13),
            text_color="gray"
        ).pack(anchor="w")
    
    def _open_url(self, url: str):
        """Open a URL in the default browser."""
        import webbrowser
        webbrowser.open(url)
    
    def _save_settings(self):
        """Save all settings."""
        # Handle startup setting immediately
        set_startup(self.startup_var.get())
        
        # Check if model needs download
        new_model = self.model_var.get()
        
        if not self._is_model_downloaded(new_model):
            # Show download confirmation dialog
            self._show_download_dialog(new_model)
        else:
            self._do_save()
    
    def _show_download_dialog(self, model_id: str):
        """Show a dialog asking to download the model."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Download Model")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center on parent
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        dialog.geometry(f"400x200+{x}+{y}")
        
        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=30, pady=25)
        
        # Message
        ctk.CTkLabel(
            frame,
            text="Download Required",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            frame,
            text=f"The {MODELS[model_id]['name']} model ({MODELS[model_id]['size']}) needs to be downloaded.",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            wraplength=340
        ).pack(anchor="w", pady=(10, 0))
        
        # Progress area (hidden initially)
        self.dialog_progress_frame = ctk.CTkFrame(frame, fg_color="transparent")
        
        self.dialog_status = ctk.CTkLabel(
            self.dialog_progress_frame,
            text="Downloading...",
            font=ctk.CTkFont(size=12)
        )
        self.dialog_status.pack(anchor="w")
        
        self.dialog_progress = ctk.CTkProgressBar(self.dialog_progress_frame, height=8)
        self.dialog_progress.pack(fill="x", pady=(5, 0))
        self.dialog_progress.configure(mode="indeterminate")
        
        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(20, 0))
        
        self.dialog_cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            width=100,
            fg_color="#444444",
            hover_color="#555555",
            command=dialog.destroy
        )
        self.dialog_cancel_btn.pack(side="left")
        
        self.dialog_download_btn = ctk.CTkButton(
            btn_frame,
            text="Download",
            width=100,
            command=lambda: self._start_download(dialog, model_id)
        )
        self.dialog_download_btn.pack(side="right")
        
        self.download_dialog = dialog
    
    def _start_download(self, dialog, model_id: str):
        """Start downloading the model."""
        # Hide buttons, show progress
        self.dialog_download_btn.configure(state="disabled")
        self.dialog_cancel_btn.configure(state="disabled")
        self.dialog_progress_frame.pack(fill="x", pady=(15, 0))
        self.dialog_progress.start()
        
        def download():
            try:
                self.dialog_status.configure(text=f"Downloading {MODELS[model_id]['name']}...")
                
                from faster_whisper import WhisperModel
                model = WhisperModel(model_id, device="cpu", compute_type="int8")
                del model
                
                # Success
                self.dialog_progress.stop()
                self.dialog_status.configure(text="Download complete!", text_color="#4CAF50")
                time.sleep(0.5)
                
                # Refresh the model tab to show updated download status
                self._refresh_model_tab()
                
                # Close dialog and save
                dialog.destroy()
                self._do_save()
                
            except Exception as e:
                self.dialog_progress.stop()
                self.dialog_status.configure(text=f"Error: {str(e)[:40]}", text_color="#F44336")
                self.dialog_cancel_btn.configure(state="normal")
        
        thread = threading.Thread(target=download, daemon=True)
        thread.start()
    
    def _do_save(self):
        """Actually save the settings."""
        lang_map = {name: code for name, code in self._languages}
        
        self.config["model"] = self.model_var.get()
        self.config["language"] = lang_map.get(self.language_var.get())
        self.config["sounds_enabled"] = self.sounds_var.get()
        
        # Save shortcuts
        self.config["shortcuts"] = {
            "push_to_talk": self.ptt_var.get(),
            "lock_key": self.lock_var.get(),
            "cancel": self.cancel_var.get()
        }
        
        if "scrubber" not in self.config:
            self.config["scrubber"] = {}
        self.config["scrubber"]["enabled"] = self.scrubber_var.get()
        
        fillers_text = self.fillers_text.get("1.0", "end-1c").strip()
        fillers = [f.strip() for f in fillers_text.split(",") if f.strip()]
        self.config["scrubber"]["fillers"] = fillers
        
        terms_text = self.terms_text.get("1.0", "end-1c").strip()
        terms = [t.strip() for t in terms_text.split("\n") if t.strip()]
        self.dictionary["terms"] = terms
        
        self._save_json(self.config_path, self.config)
        self._save_json(self.dictionary_path, self.dictionary)
        
        print("Settings saved!")
        
        if self.on_save:
            self.on_save()
        
        self._on_close()
    
    def _on_close(self):
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
            self.root = None


def show_settings(on_save: Optional[Callable] = None):
    settings = SettingsWindow(on_save=on_save)
    settings.show()


if __name__ == "__main__":
    show_settings()
