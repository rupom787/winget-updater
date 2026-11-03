"""Silent subprocess execution utility preventing console windows from popping up on Windows."""

import subprocess
import sys
from typing import Any, List, Optional

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def get_hidden_startupinfo() -> Optional[subprocess.STARTUPINFO]:
    """Configures STARTUPINFO to hide command prompt and console windows on Windows."""
    if sys.platform == "win32":
        try:
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            return si
        except Exception:
            return None
    return None


def silent_run(cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
    """Executes a subprocess completely silently without popping up or flashing console windows.
    
    Guarantees:
    - Sets subprocess.CREATE_NO_WINDOW (0x08000000) on Windows.
    - Sets STARTF_USESHOWWINDOW / SW_HIDE in STARTUPINFO.
    - Captures output and decodes text by default if not otherwise specified.
    - Preserves all standard subprocess arguments (timeout, capture_output, text, etc.).
    """
    if "capture_output" not in kwargs and "stdout" not in kwargs and "stderr" not in kwargs:
        kwargs["capture_output"] = True
    if "text" not in kwargs and "universal_newlines" not in kwargs:
        kwargs["text"] = True

    if sys.platform == "win32":
        # Ensure CREATE_NO_WINDOW flag is combined
        flags = kwargs.get("creationflags", 0)
        kwargs["creationflags"] = flags | CREATE_NO_WINDOW

        # Ensure hidden startupinfo
        if "startupinfo" not in kwargs:
            si = get_hidden_startupinfo()
            if si:
                kwargs["startupinfo"] = si

    return subprocess.run(cmd, **kwargs)

