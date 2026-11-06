"""Non-blocking synthesized sound effects and audio feedback manager for Windows 11."""

import os
import sys
import threading
from typing import Optional
from winget_updater.utils.logger import get_logger

logger = get_logger()

if sys.platform == "win32":
    try:
        import winsound
    except ImportError:
        winsound = None  # type: ignore
else:
    winsound = None  # type: ignore


class SoundManager:
    """Manages audio feedback and micro-interaction sound cues using native Windows audio APIs."""

    _instance: Optional["SoundManager"] = None
    _enabled: bool = True

    @classmethod
    def get_instance(cls) -> "SoundManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def is_enabled(cls) -> bool:
        return cls._enabled

    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        cls._enabled = enabled

    @classmethod
    def toggle_enabled(cls) -> bool:
        cls._enabled = not cls._enabled
        if cls._enabled:
            cls.play_click()
        return cls._enabled

    @classmethod
    def _async_play(cls, func) -> None:
        if not cls._enabled or winsound is None:
            return
        threading.Thread(target=func, daemon=True).start()

    @classmethod
    def play_click(cls) -> None:
        """Plays a crisp, high-frequency subtle UI click tone."""
        def _run():
            try:
                winsound.Beep(1200, 25)
            except Exception:
                pass
        cls._async_play(_run)

    @classmethod
    def play_toggle(cls) -> None:
        """Plays a gentle toggle frequency tone."""
        def _run():
            try:
                winsound.Beep(900, 35)
            except Exception:
                pass
        cls._async_play(_run)

    @classmethod
    def play_scan_complete(cls) -> None:
        """Plays a pleasant 2-tone chime upon completing system software inventory scan."""
        def _run():
            try:
                winsound.Beep(587, 60)
                winsound.Beep(880, 110)
            except Exception:
                pass
        cls._async_play(_run)

    @classmethod
    def play_update_success(cls) -> None:
        """Plays an ascending 3-tone triumph chord when updates successfully install."""
        def _run():
            try:
                winsound.Beep(523, 50)  # C5
                winsound.Beep(659, 50)  # E5
                winsound.Beep(784, 120) # G5
            except Exception:
                pass
        cls._async_play(_run)

    @classmethod
    def play_warning(cls) -> None:
        """Plays a soft caution tone on warnings."""
        def _run():
            try:
                winsound.Beep(650, 70)
                winsound.Beep(440, 120)
            except Exception:
                pass
        cls._async_play(_run)

    @classmethod
    def play_error(cls) -> None:
        """Plays an error tone."""
        def _run():
            try:
                winsound.Beep(330, 140)
            except Exception:
                pass
        cls._async_play(_run)
