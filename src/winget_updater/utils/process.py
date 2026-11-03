"""Silent subprocess execution utility preventing console windows from popping up on Windows."""

import subprocess
import sys
from typing import Any, Callable, List, Optional, Tuple

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


def silent_popen_stream(
    cmd: List[str],
    line_callback: Optional[Callable[[str], None]] = None,
    timeout: Optional[int] = None,
    encoding: str = "utf-8",
    errors: str = "replace",
) -> Tuple[int, str]:
    """Executes a subprocess completely silently, streaming lines to line_callback in real time.
    
    Guarantees:
    - Never shows or flashes console windows on Windows (SW_HIDE + CREATE_NO_WINDOW).
    - Yields on \\r and \\n (universal newlines) for real-time download/progress streaming.
    - Captures the complete combined output.
    - Handles timeout and cleanup gracefully.
    """
    flags = CREATE_NO_WINDOW if sys.platform == "win32" else 0
    si = get_hidden_startupinfo()

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            creationflags=flags,
            startupinfo=si,
            text=True,
            encoding=encoding,
            errors=errors,
            bufsize=1,
        )
    except Exception as e:
        return -1, str(e)

    full_lines: List[str] = []
    try:
        if proc.stdout:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                cleaned = line.rstrip("\r\n")
                if cleaned:
                    full_lines.append(cleaned)
                    if line_callback:
                        try:
                            line_callback(cleaned)
                        except Exception:
                            pass
            proc.stdout.close()
        proc.wait(timeout=timeout)
        return proc.returncode, "\n".join(full_lines)
    except subprocess.TimeoutExpired:
        try:
            proc.kill()
            proc.wait()
        except Exception:
            pass
        return -1, "\n".join(full_lines) or "Process timed out"
    except Exception as e:
        try:
            proc.kill()
            proc.wait()
        except Exception:
            pass
        return -1, str(e)


