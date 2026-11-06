"""Top-level executable entry point for Windows 11 Software & Package Updater."""

import ctypes
import os
import sys
from pathlib import Path

# If frozen without a console (windowed), attach to parent console if invoked from CLI or terminal
if hasattr(sys, "frozen"):
    ATTACH_PARENT_PROCESS = -1
    attached = False
    try:
        if ctypes.windll.kernel32.AttachConsole(ATTACH_PARENT_PROCESS):
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            attached = True
    except Exception:
        pass

    if not attached:
        if sys.__stdout__ is not None:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        elif sys.stdout is None:
            class DummyStream:
                def write(self, *args, **kwargs): pass
                def flush(self): pass
            sys.stdout = DummyStream()
            sys.stderr = DummyStream()

# Add src directory to Python path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Enable Windows 11 High-DPI Per-Monitor V2 awareness
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

from winget_updater.cli import main


def _extract_bundled_uninstaller() -> None:
    """Extract the bundled Uninstall.exe from the PyInstaller bundle to the app directory
    and register the application in Windows Add/Remove Programs (registry).
    Runs asynchronously in the background so main application startup is never blocked."""
    if not getattr(sys, "frozen", False):
        return  # Only runs when packaged as .exe

    try:
        bundle_dir = Path(sys._MEIPASS)
        bundled_uninstaller = bundle_dir / "Uninstall.exe"
        if not bundled_uninstaller.exists():
            return  # No bundled uninstaller found (dev build or stripped)

        # Extract to the directory containing the main WingetUpdater.exe
        app_dir = Path(sys.executable).parent
        target_uninstaller = app_dir / "Uninstall.exe"

        # Check if uninstaller already exists with matching size to skip redundant disk write
        if target_uninstaller.exists():
            try:
                if target_uninstaller.stat().st_size == bundled_uninstaller.stat().st_size:
                    _register_add_remove_programs(app_dir, target_uninstaller)
                    return
            except Exception:
                pass

        import shutil
        shutil.copy2(str(bundled_uninstaller), str(target_uninstaller))

        # Register in Windows Add/Remove Programs (HKLM/HKCU...\Uninstall\WingetUpdater)
        _register_add_remove_programs(app_dir, target_uninstaller)
    except Exception:
        pass  # Non-critical — app works fine without registry entry


def _register_add_remove_programs(app_dir: Path, uninstaller_path: Path) -> None:
    """Creates or updates the Windows registry entry so the app appears in Add/Remove Programs."""
    try:
        import winreg

        reg_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WingetUpdater"

        version = "2.4.0"
        try:
            from winget_updater import __version__
            version = __version__
        except Exception:
            pass

        values = {
            "DisplayName": "Winget Updater — Windows 11 Edition",
            "DisplayVersion": version,
            "Publisher": "rupom787",
            "UninstallString": f'"{uninstaller_path}"',
            "QuietUninstallString": f'"{uninstaller_path}" --silent',
            "InstallLocation": str(app_dir),
            "DisplayIcon": f'"{app_dir / "WingetUpdater.exe"}"',
            "NoModify": 1,
            "NoRepair": 1,
        }

        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                key = winreg.CreateKeyEx(hive, reg_key_path, 0, winreg.KEY_WRITE)
                for name, value in values.items():
                    if isinstance(value, int):
                        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)
                    else:
                        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
                winreg.CloseKey(key)
                break
            except (PermissionError, OSError):
                continue
    except Exception:
        pass


if __name__ == "__main__":
    import threading
    # Launch uninstaller extraction in a background thread for zero-millisecond startup delay
    threading.Thread(target=_extract_bundled_uninstaller, daemon=True).start()
    sys.exit(main())
