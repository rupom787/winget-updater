"""Post-update cache and installer temporary disk cleanup utility."""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Tuple
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()


class DiskCleanupManager:
    """Cleans up temporary installer files and package caches to reclaim disk space."""

    @staticmethod
    def cleanup_temp_and_cache(winget_path: str = "winget") -> Tuple[int, str]:
        """Cleans temporary vendor installer downloads and runs winget cache purge if available.
        Returns (bytes_freed, summary_message).
        """
        bytes_freed = 0
        cleaned_dirs = []

        # 1. Clean vendor fallback downloads folder: %TEMP%\winget_updater_vendor
        vendor_temp = Path(tempfile.gettempdir()) / "winget_updater_vendor"
        if vendor_temp.exists():
            try:
                for entry in vendor_temp.iterdir():
                    try:
                        if entry.is_file():
                            bytes_freed += entry.stat().st_size
                            entry.unlink(missing_ok=True)
                        elif entry.is_dir():
                            shutil.rmtree(entry, ignore_errors=True)
                    except Exception:
                        pass
                cleaned_dirs.append(str(vendor_temp))
            except Exception as e:
                logger.debug(f"Error cleaning vendor temp folder: {e}")

        # 2. Check and clean standard %LOCALAPPDATA%\Temp\WinGet if present
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            winget_temp = Path(local_app_data) / "Temp" / "WinGet"
            if winget_temp.exists():
                try:
                    for entry in winget_temp.iterdir():
                        try:
                            if entry.is_file():
                                bytes_freed += entry.stat().st_size
                                entry.unlink(missing_ok=True)
                            elif entry.is_dir():
                                shutil.rmtree(entry, ignore_errors=True)
                        except Exception:
                            pass
                    cleaned_dirs.append(str(winget_temp))
                except Exception:
                    pass

        # 3. Optional winget cache purge
        try:
            silent_run([winget_path, "cache", "purge", "--force"], capture_output=True, timeout=15)
        except Exception:
            pass

        mb_freed = bytes_freed / (1024 * 1024)
        msg = f"Cleaned {mb_freed:.1f} MB of temporary installer files."
        logger.info(msg)
        return bytes_freed, msg

