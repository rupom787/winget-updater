"""Windows Startup & Autorun Optimizer engine."""

import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from winget_updater.utils.logger import get_logger

if sys.platform == "win32":
    import winreg
else:
    winreg = None  # type: ignore

logger = get_logger()

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APPROVED_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\StartupApproved\Run"


@dataclass
class StartupItem:
    """Represents a program configured to run at Windows logon."""
    name: str
    command: str
    clean_path: str
    source: str
    hive: str
    enabled: bool
    exists: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "command": self.command,
            "clean_path": self.clean_path,
            "source": self.source,
            "hive": self.hive,
            "enabled": self.enabled,
            "exists": self.exists,
        }


class StartupManager:
    """Detects, inspects, and manages Windows startup applications."""

    @staticmethod
    def _extract_clean_path(command: str) -> str:
        """Extracts the base executable file path from a command string."""
        if not command:
            return ""
        cmd = os.path.expandvars(command.strip())
        # If quoted, extract first token inside quotes
        if cmd.startswith('"'):
            end_quote = cmd.find('"', 1)
            if end_quote != -1:
                return cmd[1:end_quote].strip()
        # Fallback: check token before first space
        parts = cmd.split(" ")
        for i in range(len(parts), 0, -1):
            candidate = " ".join(parts[:i]).strip('"')
            if os.path.isfile(candidate) or candidate.lower().endswith(".exe"):
                return candidate
        return parts[0].strip('"')

    @classmethod
    def get_startup_items(cls) -> List[StartupItem]:
        """Enumerates startup items across registry hives and startup folders."""
        if winreg is None:
            return []

        items: List[StartupItem] = []
        seen_names = set()

        # Read StartupApproved states (HKCU)
        approved_states: Dict[str, bool] = {}
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, APPROVED_KEY, 0, winreg.KEY_READ) as app_key:
                val_count = winreg.QueryInfoKey(app_key)[1]
                for i in range(val_count):
                    try:
                        vname, val_bytes, _ = winreg.EnumValue(app_key, i)
                        if isinstance(val_bytes, bytes) and len(val_bytes) > 0:
                            # 0x02 = Enabled, 0x01 / 0x03 = Disabled
                            approved_states[vname.lower()] = (val_bytes[0] == 2)
                    except Exception:
                        pass
        except Exception:
            pass

        # 1. HKCU Run
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
                val_count = winreg.QueryInfoKey(key)[1]
                for i in range(val_count):
                    try:
                        name, cmd, _ = winreg.EnumValue(key, i)
                        clean = cls._extract_clean_path(str(cmd))
                        exists = os.path.isfile(clean) if clean else False
                        enabled = approved_states.get(name.lower(), True)
                        items.append(StartupItem(
                            name=name,
                            command=str(cmd),
                            clean_path=clean,
                            source="Registry (Current User)",
                            hive="HKCU",
                            enabled=enabled,
                            exists=exists,
                        ))
                        seen_names.add(name.lower())
                    except Exception as ex:
                        logger.debug(f"Error reading HKCU entry {i}: {ex}")
        except Exception as e:
            logger.debug(f"Cannot read HKCU Run: {e}")

        # 2. HKLM Run
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, RUN_KEY, 0, winreg.KEY_READ) as key:
                val_count = winreg.QueryInfoKey(key)[1]
                for i in range(val_count):
                    try:
                        name, cmd, _ = winreg.EnumValue(key, i)
                        if name.lower() in seen_names:
                            continue
                        clean = cls._extract_clean_path(str(cmd))
                        exists = os.path.isfile(clean) if clean else False
                        enabled = approved_states.get(name.lower(), True)
                        items.append(StartupItem(
                            name=name,
                            command=str(cmd),
                            clean_path=clean,
                            source="Registry (All Users)",
                            hive="HKLM",
                            enabled=enabled,
                            exists=exists,
                        ))
                        seen_names.add(name.lower())
                    except Exception as ex:
                        logger.debug(f"Error reading HKLM entry {i}: {ex}")
        except Exception as e:
            logger.debug(f"Cannot read HKLM Run: {e}")

        # 3. User Startup Folder
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            startup_dir = Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            if startup_dir.exists():
                for f in startup_dir.iterdir():
                    if f.name.lower() == "desktop.ini":
                        continue
                    clean = str(f)
                    exists = f.exists()
                    items.append(StartupItem(
                        name=f.stem,
                        command=str(f),
                        clean_path=clean,
                        source="Startup Folder (User)",
                        hive="FOLDER",
                        enabled=True,
                        exists=exists,
                    ))

        return sorted(items, key=lambda x: (not x.enabled, x.name.lower()))

    @classmethod
    def set_enabled(cls, item: StartupItem, enabled: bool) -> bool:
        """Sets the startup status of an item using Windows 10/11 StartupApproved registry entries."""
        if winreg is None:
            return False

        if item.hive in ("HKCU", "HKLM"):
            try:
                # Open or create StartupApproved\Run key in HKCU
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, APPROVED_KEY) as key:
                    # Windows uses 12-byte binary: 0x02 for enabled, 0x03 for disabled
                    val_bytes = bytes([2 if enabled else 3] + [0] * 11)
                    winreg.SetValueEx(key, item.name, 0, winreg.REG_BINARY, val_bytes)
                logger.info(f"Updated startup status for '{item.name}' to enabled={enabled}")
                return True
            except Exception as e:
                logger.error(f"Failed to toggle startup status for '{item.name}': {e}")
                return False
        elif item.hive == "FOLDER":
            # For startup folder items, disabling can append .disabled or toggle
            try:
                p = Path(item.clean_path)
                if not enabled and p.exists() and not p.suffix == ".disabled":
                    new_p = p.with_suffix(p.suffix + ".disabled")
                    p.rename(new_p)
                    return True
                elif enabled and p.suffix == ".disabled" and p.exists():
                    new_p = p.with_suffix("")
                    p.rename(new_p)
                    return True
            except Exception as e:
                logger.error(f"Failed to toggle startup shortcut: {e}")
        return False

    @classmethod
    def delete_item(cls, item: StartupItem) -> bool:
        """Removes a startup item from the registry or startup folder."""
        if winreg is None:
            return False

        if item.hive == "HKCU":
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, item.name)
                # Also clean up StartupApproved entry if present
                try:
                    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, APPROVED_KEY, 0, winreg.KEY_SET_VALUE) as app_key:
                        winreg.DeleteValue(app_key, item.name)
                except Exception:
                    pass
                return True
            except Exception as e:
                logger.error(f"Failed to delete HKCU startup entry '{item.name}': {e}")
                return False
        elif item.hive == "HKLM":
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
                    winreg.DeleteValue(key, item.name)
                return True
            except Exception as e:
                logger.error(f"Failed to delete HKLM startup entry '{item.name}': {e}")
                return False
        elif item.hive == "FOLDER":
            try:
                p = Path(item.clean_path)
                if p.exists():
                    p.unlink(missing_ok=True)
                    return True
            except Exception as e:
                logger.error(f"Failed to delete startup shortcut: {e}")
        return False

    @staticmethod
    def reveal_in_explorer(file_path: str) -> bool:
        """Opens Windows File Explorer with the target file highlighted."""
        if not file_path:
            return False
        clean = os.path.expandvars(file_path.strip('"'))
        if not os.path.exists(clean):
            # Check directory
            parent = os.path.dirname(clean)
            if os.path.exists(parent):
                subprocess.Popen(["explorer.exe", parent])
                return True
            return False
        try:
            subprocess.Popen(["explorer.exe", f"/select,{clean}"])
            return True
        except Exception as e:
            logger.error(f"Failed to launch explorer: {e}")
            return False

