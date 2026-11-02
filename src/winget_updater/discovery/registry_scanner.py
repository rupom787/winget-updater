"""Win32 software discovery via Windows Registry hives."""

import winreg
from typing import Dict, List, Optional
from winget_updater.models import PackageType, ProgramItem
from winget_updater.utils.logger import get_logger

logger = get_logger()

# Standard Windows Uninstall registry subkey
UNINSTALL_SUBKEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall"


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

        display_version = get_val("DisplayVersion") or "Unknown"
        publisher = get_val("Publisher")
        install_location = get_val("InstallLocation")
        uninstall_string = get_val("UninstallString") or ""
        windows_installer = get_val("WindowsInstaller")

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

