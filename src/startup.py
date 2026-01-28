"""Startup manager - handle launch at Windows startup."""

import os
import sys
import winreg


APP_NAME = "freevoice"


def get_startup_command() -> str:
    """Get the command to run the app."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        return f'"{sys.executable}"'
    else:
        # Running as script - use pythonw.exe for no console
        python_dir = os.path.dirname(sys.executable)
        pythonw = os.path.join(python_dir, "pythonw.exe")
        
        # Fall back to python.exe if pythonw doesn't exist
        if not os.path.exists(pythonw):
            pythonw = sys.executable
        
        main_py = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "main.py"
        )
        return f'"{pythonw}" "{main_py}"'


def is_startup_enabled() -> bool:
    """Check if the app is set to launch at startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False


def enable_startup():
    """Enable launch at startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, get_startup_command())
        winreg.CloseKey(key)
        print(f"Enabled startup for {APP_NAME}")
        return True
    except Exception as e:
        print(f"Failed to enable startup: {e}")
        return False


def disable_startup():
    """Disable launch at startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass  # Already not set
        winreg.CloseKey(key)
        print(f"Disabled startup for {APP_NAME}")
        return True
    except Exception as e:
        print(f"Failed to disable startup: {e}")
        return False


def set_startup(enabled: bool):
    """Set startup enabled/disabled."""
    if enabled:
        return enable_startup()
    else:
        return disable_startup()
