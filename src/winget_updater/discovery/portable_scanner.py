"""Portable application discovery from folders and portable directories."""

import ctypes
import os
from ctypes import wintypes
from pathlib import Path
from typing import List, Optional, Tuple
from winget_updater.models import PackageType, ProgramItem
from winget_updater.utils.logger import get_logger

logger = get_logger()


class VS_FIXEDFILEINFO(ctypes.Structure):
    _fields_ = [
        ("dwSignature", wintypes.DWORD),
        ("dwStrucVersion", wintypes.DWORD),
        ("dwFileVersionMS", wintypes.DWORD),
        ("dwFileVersionLS", wintypes.DWORD),
        ("dwProductVersionMS", wintypes.DWORD),
        ("dwProductVersionLS", wintypes.DWORD),
        ("dwFileFlagsMask", wintypes.DWORD),
        ("dwFileFlags", wintypes.DWORD),
        ("dwFileOS", wintypes.DWORD),
        ("dwFileType", wintypes.DWORD),
        ("dwFileSubtype", wintypes.DWORD),
        ("dwFileDateMS", wintypes.DWORD),
        ("dwFileDateLS", wintypes.DWORD),
    ]


def extract_pe_version_and_name(file_path: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extracts (file_version, product_name, company_name) from PE header using Windows Version API."""
    try:
        ver_dll = ctypes.windll.version
        size = ver_dll.GetFileVersionInfoSizeW(file_path, None)
        if not size:
            return None, None, None

        buffer = ctypes.create_string_buffer(size)
        if not ver_dll.GetFileVersionInfoW(file_path, 0, size, buffer):
            return None, None, None

        # Fixed file info for numeric version
        version_str = None
        p_val = wintypes.LPVOID()
        val_len = wintypes.UINT()
        if ver_dll.VerQueryValueW(buffer, "\\", ctypes.byref(p_val), ctypes.byref(val_len)):
            info = ctypes.cast(p_val, ctypes.POINTER(VS_FIXEDFILEINFO)).contents
            v_major = info.dwFileVersionMS >> 16
            v_minor = info.dwFileVersionMS & 0xFFFF
            v_build = info.dwFileVersionLS >> 16
            v_rev = info.dwFileVersionLS & 0xFFFF
            if v_rev != 0:
                version_str = f"{v_major}.{v_minor}.{v_build}.{v_rev}"
            elif v_build != 0:
                version_str = f"{v_major}.{v_minor}.{v_build}"
            else:
                version_str = f"{v_major}.{v_minor}"

        # String file info for Product Name & Company
        product_name = None
        company_name = None
        # Try reading standard translation (040904B0 or 040904E4)
        for sub_block in [r"\StringFileInfo\040904b0\ProductName", r"\StringFileInfo\040904E4\ProductName"]:
            p_str = wintypes.LPCWSTR()
            str_len = wintypes.UINT()
            if ver_dll.VerQueryValueW(buffer, sub_block, ctypes.byref(p_str), ctypes.byref(str_len)):
                if p_str.value:
                    product_name = str(p_str.value).strip()
                    break

        for sub_block in [r"\StringFileInfo\040904b0\CompanyName", r"\StringFileInfo\040904E4\CompanyName"]:
            p_str = wintypes.LPCWSTR()
            str_len = wintypes.UINT()
            if ver_dll.VerQueryValueW(buffer, sub_block, ctypes.byref(p_str), ctypes.byref(str_len)):
                if p_str.value:
                    company_name = str(p_str.value).strip()
                    break

        return version_str, product_name, company_name
    except Exception as e:
        logger.debug(f"Failed to read PE version for {file_path}: {e}")
        return None, None, None


class PortableScanner:
    """Discovers standalone/portable executables in user-configured or standard folders."""

    def __init__(self, target_directories: Optional[List[str]] = None, max_depth: int = 2):
        self.target_directories = target_directories or []
        self.max_depth = max_depth

    def scan(self) -> List[ProgramItem]:
        discovered: List[ProgramItem] = []
        seen_paths = set()

        for directory in self.target_directories:
            dir_path = Path(directory)
            if not dir_path.is_dir():
                continue

            try:
                self._scan_folder(dir_path, 0, discovered, seen_paths)
            except Exception as e:
                logger.debug(f"Error scanning portable folder {directory}: {e}")

        logger.info(f"Portable scanner found {len(discovered)} portable applications.")
        return discovered

    def _scan_folder(
        self,
        folder: Path,
        current_depth: int,
        discovered: List[ProgramItem],
        seen_paths: set,
    ) -> None:
        if current_depth > self.max_depth:
            return

        try:
            for entry in folder.iterdir():
                if entry.is_dir():
                    # Skip common cache/temp dirs
                    if entry.name.lower() in ("node_modules", ".git", "cache", "temp", "tmp", "__pycache__"):
                        continue
                    self._scan_folder(entry, current_depth + 1, discovered, seen_paths)
                elif entry.is_file() and entry.suffix.lower() == ".exe":
                    full_path = str(entry.resolve())
                    if full_path in seen_paths:
                        continue
                    seen_paths.add(full_path)

                    # Exclude uninstaller executables
                    fname_lower = entry.stem.lower()
                    if "unins" in fname_lower or "setup" in fname_lower or "update" in fname_lower:
                        continue

                    version, prod_name, company = extract_pe_version_and_name(full_path)
                    display_name = prod_name or entry.stem

                    discovered.append(
                        ProgramItem(
                            name=display_name,
                            installed_version=version or "Unknown",
                            id=f"Portable\\{entry.name}",
                            publisher=company,
                            install_location=str(folder),
                            package_type=PackageType.PORTABLE,
                            notes=f"Portable executable at {entry.name}",
                        )
                    )
        except (PermissionError, OSError) as e:
            logger.debug(f"Access error scanning {folder}: {e}")

