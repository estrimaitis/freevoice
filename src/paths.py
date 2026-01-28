"""Path utilities for freevoice - handles both dev and bundled exe modes."""

import os
import sys


def get_base_path() -> str:
    """Get the base path for the application.
    
    When running as a bundled exe, PyInstaller sets sys._MEIPASS.
    Otherwise, use the project root directory.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as bundled exe
        return sys._MEIPASS
    else:
        # Running as script - project root is parent of src/
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_user_data_path() -> str:
    """Get the path for user data (config, dictionary, stats).
    
    When bundled, these should be in the same folder as the exe
    so users can easily edit them.
    """
    if getattr(sys, 'frozen', False):
        # Running as bundled exe - use exe's directory
        return os.path.dirname(sys.executable)
    else:
        # Running as script - use project root
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_asset_path(filename: str) -> str:
    """Get the full path to an asset file."""
    return os.path.join(get_base_path(), "assets", filename)


def get_config_path(filename: str) -> str:
    """Get the full path to a config/data file."""
    return os.path.join(get_user_data_path(), filename)
