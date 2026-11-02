"""Win32 software discovery via Windows Registry hives."""

import ctypes
import os
import re
import winreg
from typing import Dict, List, Optional
from winget_updater.models import PackageType, ProgramItem
from winget_updater.utils.logger import get_logger

logger = get_logger()

# Standard Windows Uninstall registry subkey
UNINSTALL_SUBKEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"


def extract_pe_file_version(filepath: str) -> Optional[str]:
    """Extracts FileVersion from a Win32 PE binary (.exe/.dll) via ctypes."""
    if not filepath or not os.path.isfile(filepath):
        return None
    try:
        size = ctypes.windll.version.GetFileVersionInfoSizeW(filepath, None)
        if not size:
            return None
        res = ctypes.create_string_buffer(size)
        if not ctypes.windll.version.GetFileVersionInfoW(filepath, None, size, res):
            return None
        r = ctypes.c_void_p()
        u_len = ctypes.c_uint()
        if ctypes.windll.version.VerQueryValueW(res, "\\", ctypes.byref(r), ctypes.byref(u_len)):
            fixed_info = (ctypes.c_uint32 * 13).from_address(r.value)
            ms = fixed_info[2]
            ls = fixed_info[3]
            v_major = ms >> 16
            v_minor = ms & 0xFFFF
            v_build = ls >> 16
            v_rev = ls & 0xFFFF
            if v_rev != 0:
                return f"{v_major}.{v_minor}.{v_build}.{v_rev}"
            elif v_build != 0:
                return f"{v_major}.{v_minor}.{v_build}"
            return f"{v_major}.{v_minor}"
    except Exception:
        pass
    return None


def clean_exe_path(raw_path: Optional[str]) -> Optional[str]:
    """Cleans a raw registry path string (stripping quotes and icon index suffixes)."""
    if not raw_path:
        return None
    p = raw_path.strip().strip('"').strip("'")
    # Strip trailing icon index (e.g. ,0 or ,-1)
    p = re.sub(r",-?\d+$", "", p).strip()
    if os.path.isfile(p):
        return p
    return None


class RegistryScanner:
    """Scans HKLM and HKCU registry hives (64-bit and 32-bit WOW6432Node) for installed programs."""

    def __init__(self):
        # (root_hive, subkey, access_flags, hive_description)
        self.targets = [
            (winreg.HKEY_LOCAL_MACHINE, UNINSTALL_SUBKEY, winreg.KEY_WOW64_64KEY, "HKLM-64"),
            (winreg.HKEY_LOCAL_MACHINE, UNINSTALL_SUBKEY, winreg.KEY_WOW64_32KEY, "HKLM-32"),
            (winreg.HKEY_CURRENT_USER, UNINSTALL_SUBKEY, 0, "HKCU"),
        ]

    def scan(self) -> List[ProgramItem]:
        """Scans the registry hives and returns discovered Win32 applications."""
        discovered: Dict[str, ProgramItem] = {}

        for root_key, subkey, flags, desc in self.targets:
            try:
                self._scan_key(root_key, subkey, flags, desc, discovered)
            except OSError as e:
                logger.debug(f"Failed to open registry key {desc}\\{subkey}: {e}")

        logger.info(f"Registry scanner found {len(discovered)} installed Win32 programs.")
        return list(discovered.values())

    def _scan_key(
        self,
        root_key: int,
        subkey: str,
        flags: int,
        hive_desc: str,
        discovered: Dict[str, ProgramItem],
    ) -> None:
        access_mask = winreg.KEY_READ | flags
        try:
            with winreg.OpenKey(root_key, subkey, 0, access_mask) as key:
                num_subkeys, _, _ = winreg.QueryInfoKey(key)
                for i in range(num_subkeys):
                    try:
                        child_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, child_name, 0, access_mask) as child_key:
                            item = self._parse_uninstall_entry(child_name, child_key, hive_desc)
                            if item:
                                # Deduplicate by name and version
                                dedup_key = f"{item.name.lower()}|{item.installed_version}"
                                if dedup_key not in discovered:
                                    discovered[dedup_key] = item
                    except OSError:
                        continue
        except OSError as e:
            logger.debug(f"Error accessing registry path {hive_desc}: {e}")

    def _parse_uninstall_entry(
        self,
        subkey_name: str,
        key_handle: winreg.HKEYType,
        hive_desc: str,
    ) -> Optional[ProgramItem]:
        """Extracts values from an individual uninstall registry key."""
        def get_val(name: str) -> Optional[str]:
            try:
                val, _ = winreg.QueryValueEx(key_handle, name)
                return str(val).strip() if val is not None else None
            except OSError:
                return None

        # Exclude system components or updates marked hidden
        system_component = get_val("SystemComponent")
        if system_component in ("1", 1):
            return None

        parent_key_name = get_val("ParentKeyName")
        if parent_key_name:
            # Sub-component or patch
            return None

        display_name = get_val("DisplayName")
        if not display_name:
            return None

        display_version = get_val("DisplayVersion")
        publisher = get_val("Publisher")
        install_location = get_val("InstallLocation")
        display_icon = get_val("DisplayIcon")
        uninstall_string = get_val("UninstallString") or ""
        windows_installer = get_val("WindowsInstaller")

        # Fallback: if DisplayVersion is missing or empty, extract directly from PE executable
        if not display_version or display_version.lower() in ("unknown", ""):
            # Try DisplayIcon first
            target_exe = clean_exe_path(display_icon)
            if target_exe:
                extracted_v = extract_pe_file_version(target_exe)
                if extracted_v:
                    display_version = extracted_v

            # Try InstallLocation if not found yet
            if (not display_version or display_version.lower() == "unknown") and install_location and os.path.isdir(install_location):
                try:
                    for f in os.listdir(install_location):
                        if f.lower().endswith(".exe"):
                            cand = os.path.join(install_location, f)
                            extracted_v = extract_pe_file_version(cand)
                            if extracted_v:
                                display_version = extracted_v
                                break
                except Exception:
                    pass

        display_version = display_version or "Unknown"

        # Determine if MSI or standard EXE
        is_msi = False
        if windows_installer in ("1", 1) or "msiexec" in uninstall_string.lower():
            is_msi = True

        pkg_type = PackageType.WIN32_MSI if is_msi else PackageType.WIN32_EXE

        # If subkey_name is a GUID or product code, preserve it
        arp_id = subkey_name

        return ProgramItem(
            name=display_name,
            installed_version=display_version,
            id=arp_id,
            publisher=publisher,
            install_location=install_location,
            package_type=pkg_type,
            notes=f"Found via {hive_desc}",
        )


