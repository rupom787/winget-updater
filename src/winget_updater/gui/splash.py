"""Minimalist, high-end editorial startup loading screen for Windows 11 Software & Package Updater.
Inspired by luxury studio motion graphics and editorial UI aesthetics.
"""

import math
import tkinter as tk
from typing import Callable, Optional
from winget_updater.gui.rounded_widgets import draw_rounded_rect


class EditorialStartupSplashScreen(tk.Toplevel):
    """Luxury editorial startup loading screen in ultra-deep obsidian black (#08090d)

    with ambient neon cyan and soft crimson rose glows.
    """

    def __init__(
        self,
        parent: Optional[tk.Tk] = None,
        on_complete: Optional[Callable[[], None]] = None,
        duration_ms: int = 450,
    ):
        super().__init__(parent)
        self.on_complete = on_complete
        self.duration_ms = duration_ms
        self.progress_val = 0.0
        self.target_progress = 100.0

        # Borderless luxury splash window
        self.overrideredirect(True)
        self.configure(bg="#08090d")
        self.attributes("-topmost", True)

        # Allow immediate click-to-skip or key-to-skip
        self.bind("<Button-1>", lambda e: self._finish_and_close())
        self.bind("<Key>", lambda e: self._finish_and_close())

        w, h = 760, 460
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Main ambient glow canvas
        self.canvas = tk.Canvas(
            self,
            width=w,
            height=h,
            bg="#08090d",
            highlightthickness=0,
            bd=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self._draw_ambient_glows(w, h)
        self._render_static_layout(w, h)

        self._start_time = None
        self._animate_loading()

    def _draw_ambient_glows(self, w: int, h: int) -> None:
        """Renders subtle ethereal cyan and crimson ambient edge glows."""
        # Top-left neon cyan ambient glow
        for r in range(140, 20, -20):
            alpha_col = "#042f2e" if r > 80 else "#083344"
            self.canvas.create_oval(
                -40 - r, -40 - r, 120 + r, 120 + r,
                fill=alpha_col, outline="",
            )

        # Bottom-right soft crimson rose ambient glow
        for r in range(160, 20, -20):
            alpha_col = "#1f0510" if r > 100 else "#2e0818"
            self.canvas.create_oval(
                w - 120 - r, h - 120 - r, w + 60 + r, h + 60 + r,
                fill=alpha_col, outline="",
            )

        # Subtle thin outer glass border
        draw_rounded_rect(self.canvas, 1, 1, w - 2, h - 2, radius=12, outline="#1e293b", width=1)

    def _render_static_layout(self, w: int, h: int) -> None:
        """Renders the editorial typography, metadata headers, and counters."""
        # 1. Top Header Metadata
        self.canvas.create_text(
            36,
            36,
            text="WINDOWS 11 EDITION // V2.4",
            fill="#78716c",
            font=("Cascadia Code", 8, "bold"),
            anchor="w",
        )
        self.canvas.create_text(
            w - 36,
            36,
            text="HARDWARE ACCELERATED • DIRECTX 12",
            fill="#a8a29e",
            font=("Cascadia Code", 8, "bold"),
            anchor="e",
        )

        # 2. Center Large Bold Editorial Display Typography
        self.canvas.create_text(
            w / 2,
            165,
            text="SOFTWARE & PACKAGE",
            fill="#f8fafc",
            font=("Segoe UI", 30, "bold"),
            anchor="center",
        )
        self.canvas.create_text(
            w / 2,
            215,
            text="SYSTEM UPDATER",
            fill="#f43f5e",
            font=("Segoe UI", 30, "bold"),
            anchor="center",
        )

        # Subtitle monospace status line
        self.status_item = self.canvas.create_text(
            w / 2,
            270,
            text="INITIALIZING CORE REPOSITORIES... [WINGET / MS STORE]",
            fill="#94a3b8",
            font=("Cascadia Code", 8),
            anchor="center",
        )

        # 3. Bottom Progress Line & Massive Counter
        # Progress track
        self.progress_x1 = 36
        self.progress_x2 = w - 160
        self.progress_y = h - 60

        self.canvas.create_line(
            self.progress_x1,
            self.progress_y,
            self.progress_x2,
            self.progress_y,
            fill="#1e293b",
            width=2,
        )

        # Active glowing progress line
        self.active_progress_line = self.canvas.create_line(
            self.progress_x1,
            self.progress_y,
            self.progress_x1 + 10,
            self.progress_y,
            fill="#38bdf8",
            width=3,
        )

        # Massive delicate monospaced numeric counter
        self.counter_item = self.canvas.create_text(
            w - 36,
            self.progress_y - 2,
            text="0%",
            fill="#f1f5f9",
            font=("Cascadia Code", 26, "bold"),
            anchor="e",
        )

    def set_status(self, text: str) -> None:
        """Updates the status line dynamically."""
        if hasattr(self, "status_item"):
            self.canvas.itemconfig(self.status_item, text=text)

    def set_progress(self, percent: float) -> None:
        """Sets the loading progress directly (0.0 to 100.0)."""
        self.progress_val = max(0.0, min(100.0, percent))
        self._update_progress_display()

    def _update_progress_display(self) -> None:
        track_w = self.progress_x2 - self.progress_x1
        cur_w = track_w * (self.progress_val / 100.0)
        self.canvas.coords(
            self.active_progress_line,
            self.progress_x1,
            self.progress_y,
            self.progress_x1 + max(2, cur_w),
            self.progress_y,
        )
        self.canvas.itemconfig(self.counter_item, text=f"{int(self.progress_val)}%")

    def _animate_loading(self) -> None:
        import time
        if self._start_time is None:
            self._start_time = time.time()

        elapsed = (time.time() - self._start_time) * 1000.0
        t = min(1.0, elapsed / float(self.duration_ms))

        # Cubic ease-out curve
        eased = 1.0 - math.pow(1.0 - t, 3)
        self.progress_val = eased * 100.0

        if self.progress_val > 40 and self.progress_val < 75:
            self.set_status("INITIALIZING CORE REPOSITORIES... [WINGET / MS STORE]")
        elif self.progress_val >= 75:
            self.set_status("COMPOSING DIRECTX 12 HARDWARE ACCELERATION...")

        self._update_progress_display()

        if t < 1.0:
            self.after(16, self._animate_loading)
        else:
            self.after(30, self._finish_and_close)

    def _finish_and_close(self) -> None:
        if self.on_complete:
            try:
                self.on_complete()
            except Exception:
                pass
        self.destroy()

