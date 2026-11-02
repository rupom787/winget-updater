"""Windows System Restore Point creation utility before software updates."""

import sys
from typing import Tuple
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()


class RestorePointManager:
    """Manages creation of Windows System Restore Points (VSS snapshots) before batch updates."""

    @staticmethod
    def create_restore_point(description: str = "Pre-Software Update Snapshot") -> Tuple[bool, str]:
        """Creates a Windows System Restore Point using PowerShell Checkpoint-Computer.
        
        Requires Administrator privileges.
        Note: Windows imposes a 24-hour rate limit by default on client OS versions unless
        SystemRestorePointCreationFrequency is set to 0.
        """
        if sys.platform != "win32":
            return False, "System Restore is only available on Windows"

        ps_cmd = (
            f"Checkpoint-Computer -Description '{description}' "
            "-RestorePointType 'APPLICATION_INSTALL' -ErrorAction Stop"
        )
        cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]

        logger.info(f"Attempting to create Windows System Restore Point: '{description}'...")

        try:
            res = silent_run(cmd, capture_output=True, text=True, timeout=45)
            if res.returncode == 0:
                logger.info("Successfully created Windows System Restore Point.")
                return True, "System Restore Point created successfully"
            else:
                err = res.stderr.strip() or res.stdout.strip()
                # Check for common Windows 24-hour frequency limit or disabled status
                if "0x80042306" in err or "frequency" in err.lower():
                    msg = "A restore point was already created within the last 24 hours (Windows frequency guard)."
                    logger.warning(msg)
                    return True, msg
                elif "disabled" in err.lower() or "not enabled" in err.lower():
                    msg = "System Restore is currently disabled in Windows Protection settings."
                    logger.warning(msg)
                    return False, msg
                else:
                    logger.warning(f"Failed to create restore point: {err}")
                    return False, f"Restore point error: {err}"
        except Exception as e:
            logger.error(f"Exception during restore point creation: {e}")
            return False, str(e)

