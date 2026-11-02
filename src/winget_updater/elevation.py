"""Process elevation management and UAC self-relaunch for Windows 11."""

import ctypes
import os
import sys
from typing import List, Optional
from winget_updater.utils.logger import get_logger

logger = get_logger()
RELAUNCH_FLAG = "--relaunch-attempted"


def is_elevated() -> bool:
    """Checks if the current process is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except (AttributeError, OSError) as e:
        logger.debug(f"IsUserAnAdmin check failed or non-Windows system: {e}")
        return False


def relaunch_as_admin(custom_args: Optional[List[str]] = None) -> int:
    """Relaunches the current python process elevated using ShellExecuteW ('runas').
    
    Returns:
        Instance code / HINSTANCE from ShellExecuteW (> 32 means success).
    """
    if custom_args is not None:
        args_list = custom_args
    else:
        args_list = sys.argv[1:]

    # Add relaunch flag if not present to avoid infinite loops if user rejects UAC
    if RELAUNCH_FLAG not in args_list:
        args_list = [RELAUNCH_FLAG] + args_list

    # Determine command line parameters
    # If run as a python script, pass script name followed by args
    if hasattr(sys, "frozen"):
        executable = sys.executable
        params = " ".join(f'"{arg}"' if " " in arg else arg for arg in args_list)
    else:
        executable = sys.executable
        script = sys.argv[0]
        params = f'"{script}" ' + " ".join(f'"{arg}"' if " " in arg else arg for arg in args_list)

    logger.info("Requesting UAC elevation for process relaunch...")
    try:
        # ShellExecuteW: hwnd, operation ("runas"), file, parameters, directory, nShowCmd (1 = SW_SHOWNORMAL)
        ret = ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            executable,
            params,
            os.getcwd(),
            1
        )
        return int(ret)
    except Exception as e:
        logger.error(f"Failed to execute elevated relaunch: {e}")
        return 0


def ensure_elevated(exit_on_relaunch: bool = True) -> bool:
    """Ensures the application is running elevated.
    
    If not elevated and relaunch has not been attempted yet, triggers a single UAC prompt
    and optionally exits the current unprivileged process.
    If elevation failed or was declined by user, logs error and returns False.
    """
    if is_elevated():
        logger.info("Application is running with verified administrative privileges.")
        return True

    # If already attempted and still not elevated, user cancelled UAC or policy blocked it
    if RELAUNCH_FLAG in sys.argv:
        logger.error("Elevation was requested but declined or failed. Administrative rights are required.")
        return False

    logger.warning("Application requires administrator privileges. Initiating single UAC prompt...")
    ret = relaunch_as_admin()
    if ret > 32:
        logger.info("Elevated process spawned successfully.")
        if exit_on_relaunch:
            sys.exit(0)
        return True
    else:
        logger.error(f"UAC elevation prompt was cancelled or failed with code: {ret}")
        return False

