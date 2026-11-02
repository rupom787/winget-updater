"""Top-level executable entry point for Windows 11 Software & Package Updater."""

import ctypes
import os
import sys
from pathlib import Path

# If frozen without a console (windowed), attach to parent console if invoked from CLI or terminal
if hasattr(sys, "frozen"):
    ATTACH_PARENT_PROCESS = -1
    attached = False
    try:
        if ctypes.windll.kernel32.AttachConsole(ATTACH_PARENT_PROCESS):
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            attached = True
    except Exception:
        pass

    if not attached:
        if sys.__stdout__ is not None:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        elif sys.stdout is None:
            class DummyStream:
                def write(self, *args, **kwargs): pass
                def flush(self): pass
            sys.stdout = DummyStream()
            sys.stderr = DummyStream()

# Add src directory to Python path
src_dir = Path(__file__).resolve().parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from winget_updater.cli import main

if __name__ == "__main__":
    sys.exit(main())
