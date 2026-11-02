"""Modern rounded UI widgets and native Windows 11 window styling.
Crafts smooth rounded-corner buttons, pill badges, and search inputs with anti-aliasing look.
"""

import ctypes
import sys
import tkinter as tk
from typing import Callable, Optional, Tuple


def apply_native_window_styling(window: tk.Tk) -> None:
    """Applies native Windows 11 DWM window attributes:
    - DWMWCP_ROUND (rounded window corners)
    - DWMWA_CAPTION_COLOR (clean titlebar matching app background)
    - DWMWA_TEXT_COLOR (dark readable titlebar text)
    """
    if sys.platform != "win32":
        return

    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()

        # DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2
        pref = ctypes.c_int(DWMWCP_ROUND)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(pref), ctypes.sizeof(pref)
        )

        # DWMWA_CAPTION_COLOR = 35 (BGR 0x00FAF8F8)
        DWMWA_CAPTION_COLOR = 35
        color_bgr = ctypes.c_int(0x00F8F8FA)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(color_bgr), ctypes.sizeof(color_bgr)
        )

        # DWMWA_TEXT_COLOR = 36 (Dark charcoal 0x00271811)
        DWMWA_TEXT_COLOR = 36
        text_bgr = ctypes.c_int(0x00271811)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_TEXT_COLOR, ctypes.byref(text_bgr), ctypes.sizeof(text_bgr)
        )
    except Exception:
        pass


def draw_rounded_rect(
    canvas: tk.Canvas,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    radius: float = 8.0,
    **kwargs
) -> int:
    """Draws a smooth rounded rectangle on a Tkinter Canvas using a multi-point spline."""
    points = [
        x1 + radius, y1,
        x1 + radius, y1,
        x2 - radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class RoundedButton(tk.Canvas):
    """Bespoke rounded button widget with smooth corner curves and reactive hover feedback."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str = "",
        command: Optional[Callable[[], None]] = None,
        bg_color: str = "#800020",
        fg_color: str = "#ffffff",
        hover_bg: Optional[str] = None,
        hover_fg: Optional[str] = None,
        disabled_bg: str = "#f1f1f4",
        disabled_fg: str = "#9ca3af",
        border_color: Optional[str] = None,
        radius: int = 8,
        font: Tuple[str, int, str] = ("Segoe UI", 9, "bold"),
        width: Optional[int] = None,
        height: int = 34,
        padding: Tuple[int, int] = (16, 8),
        parent_bg: str = "#ffffff",
        cursor: str = "hand2",
    ):
        self.text = text
        self.command = command
        self.normal_bg = bg_color
        self.normal_fg = fg_color
        self.hover_bg = hover_bg or self._tint_color(bg_color, 1.15)
        self.hover_fg = hover_fg or fg_color
        self.disabled_bg = disabled_bg
        self.disabled_fg = disabled_fg
        self.border_color = border_color
        self.radius = radius
        self.custom_font = font
        self.fixed_width = width
        self.fixed_height = height
        self.padding = padding
        self.parent_bg = parent_bg
        self.cursor_style = cursor

        self.current_bg = self.normal_bg
        self.current_fg = self.normal_fg
        self._state = "normal"
        self._is_hovered = False

        # Measure dimensions
        w = width if width else (len(text) * 8 + padding[0] * 2)
        h = height

        super().__init__(
            parent,
            width=w,
            height=h,
            bg=parent_bg,
            highlightthickness=0,
            relief=tk.FLAT,
            cursor=cursor if self._state == "normal" else "arrow",
        )

        self.bind("<Configure>", self._on_resize)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

        self._redraw()

    def _on_resize(self, event) -> None:
        self._redraw()

    def _redraw(self, offset_y: int = 0) -> None:
        self.delete("all")
        w = self.winfo_width() or self.fixed_width or (len(self.text) * 8 + self.padding[0] * 2)
        h = self.winfo_height() or self.fixed_height

        # Draw rounded background
        draw_kwargs = {"fill": self.current_bg}
        if self.border_color:
            draw_kwargs["outline"] = self.border_color
            draw_kwargs["width"] = 1

        draw_rounded_rect(self, 1, 1, w - 2, h - 2, radius=self.radius, **draw_kwargs)

        # Draw centered text
        self.create_text(
            w / 2,
            (h / 2) + offset_y,
            text=self.text,
            fill=self.current_fg,
            font=self.custom_font,
            anchor="center",
        )

    def _on_enter(self, event) -> None:
        if self._state == "normal":
            self._is_hovered = True
            self.current_bg = self.hover_bg
            self.current_fg = self.hover_fg
            self._redraw()

    def _on_leave(self, event) -> None:
        if self._state == "normal":
            self._is_hovered = False
            self.current_bg = self.normal_bg
            self.current_fg = self.normal_fg
            self._redraw()

    def _on_press(self, event) -> None:
        if self._state == "normal":
            self._redraw(offset_y=1)

    def _on_release(self, event) -> None:
        if self._state == "normal":
            self._redraw(offset_y=0)
            if self.command:
                self.command()

    def config(self, **kwargs) -> None:
        """Emulates standard widget config method."""
        canvas_kwargs = {}
        if "state" in kwargs:
            self._state = kwargs["state"]
            if self._state in ("disabled", tk.DISABLED):
                self._state = "disabled"
                self.current_bg = self.disabled_bg
                self.current_fg = self.disabled_fg
                self.config_cursor("arrow")
            else:
                self._state = "normal"
                self.current_bg = self.normal_bg
                self.current_fg = self.normal_fg
                self.config_cursor(self.cursor_style)

        if "text" in kwargs:
            self.text = kwargs["text"]

        if "bg" in kwargs:
            self.normal_bg = kwargs["bg"]
            if self._state == "normal" and not self._is_hovered:
                self.current_bg = kwargs["bg"]

        if "fg" in kwargs:
            self.normal_fg = kwargs["fg"]
            if self._state == "normal" and not self._is_hovered:
                self.current_fg = kwargs["fg"]

        if "command" in kwargs:
            self.command = kwargs["command"]

        if "width" in kwargs:
            self.fixed_width = kwargs["width"]
            canvas_kwargs["width"] = kwargs["width"]

        if "height" in kwargs:
            self.fixed_height = kwargs["height"]
            canvas_kwargs["height"] = kwargs["height"]

        if canvas_kwargs:
            try:
                super().config(**canvas_kwargs)
            except Exception:
                pass

        self._redraw()

    configure = config

    def __setitem__(self, key: str, value) -> None:
        self.config(**{key: value})

    def __getitem__(self, key: str):
        if key == "state":
            return self._state
        if key == "text":
            return self.text
        if key == "bg":
            return self.normal_bg
        if key == "fg":
            return self.normal_fg
        return super().__getitem__(key)

    def config_cursor(self, cursor: str) -> None:
        try:
            super().config(cursor=cursor)
        except Exception:
            pass

    @staticmethod
    def _tint_color(hex_color: str, factor: float) -> str:
        """Subtly brightens or darkens a hex color for hover states."""
        try:
            h = hex_color.lstrip("#")
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color


class RoundedPillBadge(tk.Canvas):
    """Smooth rounded pill capsule for status labels, counts, and category badges."""

    def __init__(
        self,
        parent: tk.Widget,
        text: str = "",
        bg_color: str = "#f1f5f9",
        fg_color: str = "#475569",
        border_color: Optional[str] = None,
        font: Tuple[str, int, str] = ("Segoe UI", 8, "bold"),
        height: int = 24,
        parent_bg: str = "#ffffff",
    ):
        self.text = text
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.border_color = border_color
        self.font = font
        self.fixed_height = height
        self.parent_bg = parent_bg

        w = max(40, len(text) * 7 + 16)

        super().__init__(
            parent,
            width=w,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            relief=tk.FLAT,
        )
        self._redraw()

    def _redraw(self) -> None:
        self.delete("all")
        w = max(40, len(self.text) * 7 + 16)
        self.config(width=w)
        h = self.fixed_height

        draw_kwargs = {"fill": self.bg_color}
        if self.border_color:
            draw_kwargs["outline"] = self.border_color
            draw_kwargs["width"] = 1

        draw_rounded_rect(self, 1, 1, w - 2, h - 2, radius=h / 2, **draw_kwargs)
        self.create_text(
            w / 2,
            h / 2,
            text=self.text,
            fill=self.fg_color,
            font=self.font,
            anchor="center",
        )

    def set_badge(self, text: str, bg_color: Optional[str] = None, fg_color: Optional[str] = None) -> None:
        self.text = text
        if bg_color:
            self.bg_color = bg_color
        if fg_color:
            self.fg_color = fg_color
        self._redraw()
