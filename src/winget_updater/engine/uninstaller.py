"""Uninstaller Engine — Complete removal of application files, directories, shortcuts, registry keys, and app data."""

import ctypes
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()

# Constants
APP_TITLE = "Software & Package Updater"
APP_NAME = "WingetUpdater"
SCHEDULED_TASK_NAME = "WingetUpdaterDaily"
REGISTRY_UNINSTALL_SUBKEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\WingetUpdater"
REGISTRY_LEGACY_UNINSTALL_SUBKEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\Software & Package Updater"
REGISTRY_SOFTWARE_SUBKEY = r"Software\WingetUpdater"
REGISTRY_LEGACY_SOFTWARE_SUBKEY = r"Software\Software & Package Updater"
REGISTRY_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

RUN_VALUE_NAMES = ["WingetUpdater", "Software & Package Updater"]

SHORTCUT_NAMES = [
    "Software & Package Updater.lnk",
    "Winget Updater.lnk",
    "WingetUpdater.lnk",
    "Software and Package Updater.lnk",
]

SUBFOLDER_SHORTCUT_DIRS = [
    "Software & Package Updater",
    "WingetUpdater",
    "Winget Updater",
]

APP_DATA_DIR_NAMES = [
    "WingetUpdater",
    "Software & Package Updater",
    "winget_updater",
]

APP_RUNTIME_FILES = [
    "exclusions.json",
    "sources.json",
    "config.json",
    "update_tracker.json",
    "run_state.json",
    "custom_mappings.json",
    "pinned_packages.json",
    "skipped_versions.json",
    "winget_updater.log",
]


@dataclass
class UninstallSummary:
    """Summary of items found and removed during uninstallation."""
    processes_killed: List[str] = field(default_factory=list)
    shortcuts_removed: List[str] = field(default_factory=list)
    registry_keys_removed: List[str] = field(default_factory=list)
    registry_values_removed: List[str] = field(default_factory=list)
    tasks_removed: List[str] = field(default_factory=list)
    appdata_dirs_removed: List[str] = field(default_factory=list)
    files_removed: List[str] = field(default_factory=list)
    dirs_removed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def total_items_removed(self) -> int:
        return (
            len(self.processes_killed)
            + len(self.shortcuts_removed)
            + len(self.registry_keys_removed)
            + len(self.registry_values_removed)
            + len(self.tasks_removed)
            + len(self.appdata_dirs_removed)
            + len(self.files_removed)
            + len(self.dirs_removed)
        )


class Uninstaller:
    """Discovers and permanently removes all application components."""

    def __init__(self, target_install_dir: Optional[Path] = None):
        self.target_install_dir = target_install_dir or self.detect_install_dir()

    @staticmethod
    def detect_install_dir() -> Optional[Path]:
        """Detects the application installation directory from registry or executable path."""
        # Check registry first
        try:
            import winreg
            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                try:
                    with winreg.OpenKey(hive, REGISTRY_UNINSTALL_SUBKEY) as k:
                        val, _ = winreg.QueryValueEx(k, "InstallLocation")
                        if val and os.path.exists(val):
                            return Path(val).resolve()
                except (FileNotFoundError, OSError):
                    pass
        except Exception:
            pass

        # Check executable location
        if hasattr(sys, "frozen"):
            return Path(sys.executable).resolve().parent

        # Running via python script
        main_file = Path(__file__).resolve().parent.parent.parent.parent
        if (main_file / "run.py").exists():
            return main_file.resolve()

        return Path.cwd().resolve()

    @staticmethod
    def is_dev_source_directory(path: Path) -> bool:
        """Determines if a directory is the source code git repo to avoid accidental code deletion."""
        if not path or not path.exists():
            return False
        return (path / ".git").exists() or (path / "src" / "winget_updater" / "__init__.py").exists()

    def kill_running_processes(self, process_names: Optional[List[str]] = None) -> List[str]:
        """Terminates any active application processes before uninstalling."""
        targets = process_names or ["WingetUpdater.exe", "Software & Package Updater.exe"]
        killed = []
        if sys.platform != "win32":
            return killed

        for name in targets:
            try:
                # Use taskkill /F /IM <name> /T to forcefully kill the process tree
                res = silent_run(["taskkill.exe", "/F", "/IM", name, "/T"], timeout=10)
                if res.returncode == 0:
                    killed.append(name)
                    logger.info(f"Terminated running process '{name}'")
            except Exception as e:
                logger.debug(f"Process termination attempt for {name}: {e}")

        # Short pause to ensure file handles are released
        if killed:
            time.sleep(0.5)
        return killed

    def find_shortcuts(self) -> List[Path]:
        """Locates all application shortcuts across User and System Desktop, Start Menu, Startup, and Quick Launch."""
        found: Set[Path] = set()

        candidate_roots: List[Path] = []

        # User and public environment folders
        user_profile = os.environ.get("USERPROFILE")
        app_data = os.environ.get("APPDATA")
        local_app_data = os.environ.get("LOCALAPPDATA")
        program_data = os.environ.get("PROGRAMDATA") or r"C:\ProgramData"
        public_dir = os.environ.get("PUBLIC") or r"C:\Users\Public"
        onedrive = os.environ.get("OneDrive")

        # Desktop locations
        if user_profile:
            candidate_roots.append(Path(user_profile) / "Desktop")
        if onedrive:
            candidate_roots.append(Path(onedrive) / "Desktop")
        candidate_roots.append(Path(public_dir) / "Desktop")

        # Start Menu Programs
        if app_data:
            candidate_roots.append(Path(app_data) / r"Microsoft\Windows\Start Menu\Programs")
            candidate_roots.append(Path(app_data) / r"Microsoft\Windows\Start Menu\Programs\Startup")
        if program_data:
            candidate_roots.append(Path(program_data) / r"Microsoft\Windows\Start Menu\Programs")
            candidate_roots.append(Path(program_data) / r"Microsoft\Windows\Start Menu\Programs\Startup")

        # Quick Launch / TaskBar
        if app_data:
            candidate_roots.append(Path(app_data) / r"Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar")

        # Also query Windows Explorer Shell Folders in registry if on Windows
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as k:
                for shell_val in ("Desktop", "Programs", "Startup"):
                    try:
                        raw_path, _ = winreg.QueryValueEx(k, shell_val)
                        expanded = os.path.expandvars(raw_path)
                        if os.path.exists(expanded):
                            candidate_roots.append(Path(expanded))
                    except (FileNotFoundError, OSError):
                        pass
        except Exception:
            pass

        # Scan each candidate root
        for root in candidate_roots:
            if not root.exists():
                continue

            # Direct shortcut files
            for sc_name in SHORTCUT_NAMES:
                sc_file = root / sc_name
                if sc_file.exists():
                    found.add(sc_file)

            # Subfolders in Start Menu
            for sub_name in SUBFOLDER_SHORTCUT_DIRS:
                sub_dir = root / sub_name
                if sub_dir.is_dir():
                    for sc_file in sub_dir.glob("*.lnk"):
                        found.add(sc_file)

        return sorted(list(found))

    def remove_shortcuts(self, shortcuts: Optional[List[Path]] = None) -> List[str]:
        """Removes found shortcuts and cleans up any empty subfolders."""
        targets = shortcuts if shortcuts is not None else self.find_shortcuts()
        removed = []
        folders_to_check: Set[Path] = set()

        for sc in targets:
            try:
                if sc.exists():
                    parent = sc.parent
                    sc.unlink()
                    removed.append(str(sc))
                    logger.info(f"Removed shortcut: {sc}")
                    folders_to_check.add(parent)
            except Exception as e:
                logger.error(f"Error removing shortcut {sc}: {e}")

        # Check and remove empty parent shortcut subfolders
        for folder in folders_to_check:
            try:
                if folder.exists() and any(name.lower() in folder.name.lower() for name in SUBFOLDER_SHORTCUT_DIRS):
                    # Check if empty
                    if not any(folder.iterdir()):
                        folder.rmdir()
                        removed.append(str(folder))
                        logger.info(f"Removed empty shortcut directory: {folder}")
            except Exception as e:
                logger.debug(f"Could not remove folder {folder}: {e}")

        return removed

    @staticmethod
    def _delete_reg_key_tree(hive: Any, subkey_path: str) -> bool:
        """Recursively deletes a Windows registry key and all of its subkeys and values."""
        import winreg
        try:
            with winreg.OpenKey(hive, subkey_path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
                # First delete all subkeys recursively
                while True:
                    try:
                        child_name = winreg.EnumKey(key, 0)
                        child_subkey = f"{subkey_path}\\{child_name}"
                        Uninstaller._delete_reg_key_tree(hive, child_subkey)
                    except OSError:
                        # No more subkeys
                        break

            # Now delete the empty key
            winreg.DeleteKey(hive, subkey_path)
            return True
        except FileNotFoundError:
            return True
        except Exception as e:
            logger.debug(f"Error deleting registry key {subkey_path}: {e}")
            return False

    def remove_registry_entries(self) -> Tuple[List[str], List[str]]:
        """Removes all application registry keys (Uninstall, Software, Startup Run) from HKCU and HKLM."""
        keys_removed = []
        vals_removed = []

        if sys.platform != "win32":
            return keys_removed, vals_removed

        import winreg

        # 1. Uninstall and Software Keys
        target_subkeys = [
            REGISTRY_UNINSTALL_SUBKEY,
            REGISTRY_LEGACY_UNINSTALL_SUBKEY,
            REGISTRY_SOFTWARE_SUBKEY,
            REGISTRY_LEGACY_SOFTWARE_SUBKEY,
        ]

        for hive, hive_name in ((winreg.HKEY_CURRENT_USER, "HKCU"), (winreg.HKEY_LOCAL_MACHINE, "HKLM")):
            for subkey in target_subkeys:
                try:
                    # Check if key exists first
                    with winreg.OpenKey(hive, subkey):
                        pass
                    if self._delete_reg_key_tree(hive, subkey):
                        keys_removed.append(f"{hive_name}\\{subkey}")
                        logger.info(f"Deleted registry key: {hive_name}\\{subkey}")
                except (FileNotFoundError, OSError):
                    pass

        # 2. Windows Startup Run Key values
        for hive, hive_name in ((winreg.HKEY_CURRENT_USER, "HKCU"), (winreg.HKEY_LOCAL_MACHINE, "HKLM")):
            try:
                with winreg.OpenKey(hive, REGISTRY_RUN_KEY, 0, winreg.KEY_SET_VALUE | winreg.KEY_READ) as k:
                    for val_name in RUN_VALUE_NAMES:
                        try:
                            winreg.QueryValueEx(k, val_name)
                            winreg.DeleteValue(k, val_name)
                            vals_removed.append(f"{hive_name}\\{REGISTRY_RUN_KEY}\\{val_name}")
                            logger.info(f"Deleted startup run value: {hive_name}\\{REGISTRY_RUN_KEY}\\{val_name}")
                        except (FileNotFoundError, OSError):
                            pass
            except Exception:
                pass

        return keys_removed, vals_removed

    def remove_scheduled_tasks(self) -> List[str]:
        """Deletes scheduled tasks configured in Windows Task Scheduler."""
        removed = []
        if sys.platform != "win32":
            return removed

        tasks = [SCHEDULED_TASK_NAME]
        for t in tasks:
            cmd = ["schtasks.exe", "/Delete", "/TN", t, "/F"]
            try:
                res = silent_run(cmd, timeout=15)
                if res.returncode == 0:
                    removed.append(t)
                    logger.info(f"Deleted scheduled task: {t}")
            except Exception as e:
                logger.debug(f"Error checking/deleting scheduled task {t}: {e}")

        return removed

    def find_appdata_paths(self) -> List[Path]:
        """Locates all leftover application data, cache, and log folders."""
        found: List[Path] = []

        local_app_data = os.environ.get("LOCALAPPDATA")
        app_data = os.environ.get("APPDATA")
        program_data = os.environ.get("PROGRAMDATA")

        bases = []
        if local_app_data:
            bases.append(Path(local_app_data))
        if app_data:
            bases.append(Path(app_data))
        if program_data:
            bases.append(Path(program_data))

        for base in bases:
            for dirname in APP_DATA_DIR_NAMES:
                d = base / dirname
                if d.exists() and d.is_dir():
                    found.append(d)

        # Temp directory files
        temp_dir = os.environ.get("TEMP") or os.environ.get("TMP")
        if temp_dir:
            temp_path = Path(temp_dir)
            if temp_path.exists():
                for pat in ("WingetUpdater*", "Software_Updater*"):
                    for match in temp_path.glob(pat):
                        if match.is_dir():
                            found.append(match)

        return found

    def remove_appdata(self, paths: Optional[List[Path]] = None) -> List[str]:
        """Removes application data, cache, and log folders."""
        targets = paths if paths is not None else self.find_appdata_paths()
        removed = []

        for p in targets:
            try:
                if p.exists() and p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                    if not p.exists():
                        removed.append(str(p))
                        logger.info(f"Removed app data directory: {p}")
            except Exception as e:
                logger.error(f"Error removing app data directory {p}: {e}")

        return removed

    def remove_install_directory(
        self,
        target_dir: Optional[Path] = None,
        force_delete_all: bool = False,
    ) -> Tuple[List[str], List[str]]:
        """Removes the application install directory or runtime artifacts.
        
        If target_dir is the git repository / dev source and force_delete_all is False,
        only removes runtime artifacts and temporary files (never deletes source code).
        If target_dir is a compiled / installed folder, removes all files and the folder.
        """
        directory = target_dir or self.target_install_dir
        if not directory or not directory.exists():
            return [], []

        files_removed = []
        dirs_removed = []

        is_dev = self.is_dev_source_directory(directory)

        if is_dev and not force_delete_all:
            logger.info(f"Preserving development source files in {directory}. Cleaning runtime files...")
            # Clean runtime and generated artifacts only
            for fn in APP_RUNTIME_FILES:
                fp = directory / fn
                if fp.exists():
                    try:
                        fp.unlink()
                        files_removed.append(str(fp))
                    except Exception as e:
                        logger.debug(f"Could not remove {fp}: {e}")

            # Also check for export and backup files
            for pat in ("winget-software-backup*.json", "winget_software_export*.*", "*.log"):
                for fp in directory.glob(pat):
                    if fp.is_file():
                        try:
                            fp.unlink()
                            files_removed.append(str(fp))
                        except Exception:
                            pass
            return files_removed, dirs_removed

        # Full installation directory wipe
        logger.info(f"Removing full application directory: {directory}")
        try:
            for item in list(directory.iterdir()):
                try:
                    if item.is_file() or item.is_symlink():
                        item.unlink(missing_ok=True)
                        files_removed.append(str(item))
                    elif item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                        dirs_removed.append(str(item))
                except Exception as e:
                    logger.debug(f"Could not remove {item}: {e}")

            # Finally remove the parent directory if empty
            try:
                directory.rmdir()
                dirs_removed.append(str(directory))
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Error wiping directory {directory}: {e}")

        return files_removed, dirs_removed

    def execute_full_uninstall(
        self,
        target_dir: Optional[Path] = None,
        force_delete_all: bool = False,
        progress_callback: Optional[Callable[[str, float], None]] = None,
    ) -> UninstallSummary:
        """Performs end-to-end uninstallation of all components.
        
        Order:
        1. Terminate running application processes.
        2. Delete scheduled Windows tasks.
        3. Remove desktop, start menu, and startup shortcuts.
        4. Remove Windows Registry keys and values.
        5. Clean up AppData, LocalAppData, and Temp cache.
        6. Clean up or delete install directory.
        """
        summary = UninstallSummary()

        def update(msg: str, progress: float):
            logger.info(f"[Uninstaller] {msg}")
            if progress_callback:
                progress_callback(msg, progress)

        # 1. Terminate running processes
        update("Terminating active application processes...", 0.10)
        summary.processes_killed = self.kill_running_processes()

        # 2. Delete scheduled tasks
        update("Removing scheduled daily background tasks...", 0.25)
        summary.tasks_removed = self.remove_scheduled_tasks()

        # 3. Remove shortcuts
        update("Removing desktop and Start menu shortcuts...", 0.45)
        summary.shortcuts_removed = self.remove_shortcuts()

        # 4. Remove registry keys
        update("Cleaning Windows Registry entries and uninstall keys...", 0.65)
        keys, vals = self.remove_registry_entries()
        summary.registry_keys_removed = keys
        summary.registry_values_removed = vals

        # 5. Remove leftover AppData
        update("Purging application data, logs, and cache...", 0.85)
        summary.appdata_dirs_removed = self.remove_appdata()

        # 6. Remove installation directory
        update("Removing application files...", 0.95)
        files, dirs = self.remove_install_directory(target_dir=target_dir, force_delete_all=force_delete_all)
        summary.files_removed = files
        summary.dirs_removed = dirs

        update("Uninstallation complete.", 1.0)
        return summary

    @staticmethod
    def register_in_windows_registry(
        install_dir: Path,
        version: str = "2.0.0",
        uninstall_exe_path: Optional[Path] = None,
    ) -> bool:
        """Registers the application in Windows Add/Remove Programs (Settings > Installed Apps)."""
        if sys.platform != "win32":
            return False

        import winreg

        uninst_path = uninstall_exe_path or (install_dir / "Uninstall.exe")
        app_exe = install_dir / "WingetUpdater.exe"

        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_UNINSTALL_SUBKEY) as k:
                winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, APP_TITLE)
                winreg.SetValueEx(k, "DisplayVersion", 0, winreg.REG_SZ, version)
                winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, "Rupom & Deepmind Engineering")
                winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, str(install_dir))
                winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ, str(app_exe) if app_exe.exists() else str(uninst_path))
                winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ, f'"{uninst_path}"')
                winreg.SetValueEx(k, "QuietUninstallString", 0, winreg.REG_SZ, f'"{uninst_path}" --silent')
                winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(k, "EstimatedSize", 0, winreg.REG_DWORD, 65000)  # ~65MB
            logger.info(f"Registered {APP_TITLE} in Windows Registry.")
            return True
        except Exception as e:
            logger.error(f"Failed to register in Windows Registry: {e}")
            return False

