"""Modern rounded UI widgets and native Windows 11 window styling.
Crafts smooth rounded-corner buttons, pill badges, and search inputs with anti-aliasing look.
"""

import ctypes
import sys
import tkinter as tk
from typing import Callable, Optional, Tuple


def apply_native_window_styling(window: tk.Tk, theme: Optional[object] = None) -> None:
    """Applies native Windows 11 DWM window attributes:
    - DWMWCP_ROUND (rounded window corners)
    - DWMWA_USE_IMMERSIVE_DARK_MODE (native Windows dark/light frame)
    - DWMWA_SYSTEMBACKDROP_TYPE (DWMSBT_TRANSIENTWINDOW = 3 for Acrylic frosted glass)
    - DWMWA_CAPTION_COLOR (clean titlebar matching app background)
    - DWMWA_TEXT_COLOR (dark/light readable titlebar text)
    - Window level alpha transparency (-alpha 0.94 - 0.96)
    """
    # Apply Tkinter window-level alpha transparency for frosted translucent glass
    try:
        alpha = getattr(theme, "glass_backdrop_alpha", 0.95) if theme else 0.95
        window.wm_attributes("-alpha", alpha)
    except Exception:
        pass

    if sys.platform != "win32":
        return

    try:
        window.update_idletasks()
        GA_ROOT = 2
        hwnd = ctypes.windll.user32.GetAncestor(window.winfo_id(), GA_ROOT) or ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()

        # DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2
        pref = ctypes.c_int(DWMWCP_ROUND)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(pref), ctypes.sizeof(pref)
        )

        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        dark_mode_val = getattr(theme, "dwm_dark_mode", 0) if theme else 0
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        dark_pref = ctypes.c_int(dark_mode_val)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(dark_pref), ctypes.sizeof(dark_pref)
        )

        # DWMWA_SYSTEMBACKDROP_TYPE = 38 (3 = DWMSBT_TRANSIENTWINDOW: Acrylic frosted glass)
        backdrop_val = getattr(theme, "dwm_backdrop_type", 3) if theme else 3
        DWMWA_SYSTEMBACKDROP_TYPE = 38
        backdrop_pref = ctypes.c_int(backdrop_val)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_SYSTEMBACKDROP_TYPE, ctypes.byref(backdrop_pref), ctypes.sizeof(backdrop_pref)
        )

        # Windows 11 True Acrylic Blur Behind via SetWindowCompositionAttribute
        try:
            class ACCENT_POLICY(ctypes.Structure):
                _fields_ = [
                    ("AccentState", ctypes.c_int),
                    ("AccentFlags", ctypes.c_int),
                    ("GradientColor", ctypes.c_uint32),
                    ("AnimationId", ctypes.c_int),
                ]

            class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
                _fields_ = [
                    ("Attribute", ctypes.c_int),
                    ("Data", ctypes.c_void_p),
                    ("SizeOfData", ctypes.c_size_t),
                ]

            WCA_ACCENT_POLICY = 19
            ACCENT_ENABLE_ACRYLICBLURBEHIND = 4
            gradient_col = 0xCC241218 if dark_mode_val else 0xCCF2F7FA
            accent = ACCENT_POLICY(ACCENT_ENABLE_ACRYLICBLURBEHIND, 0, gradient_col, 0)
            data = WINDOWCOMPOSITIONATTRIBDATA(
                WCA_ACCENT_POLICY,
                ctypes.cast(ctypes.pointer(accent), ctypes.c_void_p),
                ctypes.sizeof(accent),
            )
            ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(data))
        except Exception:
            pass

        # DWMWA_CAPTION_COLOR = 35
        caption_bgr = getattr(theme, "dwm_caption_bgr", 0x00F8F8FA) if theme else 0x00F8F8FA
        DWMWA_CAPTION_COLOR = 35
        color_bgr = ctypes.c_int(caption_bgr)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(color_bgr), ctypes.sizeof(color_bgr)
        )

        # DWMWA_TEXT_COLOR = 36
        is_dark = bool(dark_mode_val)
        text_bgr = ctypes.c_int(0x00F0F4FC if is_dark else 0x00271811)
        DWMWA_TEXT_COLOR = 36
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
        is_dark_parent = str(parent_bg).lower().startswith(("#0", "#1", "#2"))
        if disabled_bg == "#f1f1f4" and is_dark_parent:
            disabled_bg = "#141d30"
            disabled_fg = "#475569"
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
        """Emulates standard widget config method with full theme-awareness."""
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

        if "bg" in kwargs or "bg_color" in kwargs:
            new_bg = kwargs.get("bg", kwargs.get("bg_color"))
            self.normal_bg = new_bg
            if self._state == "normal" and not self._is_hovered:
                self.current_bg = new_bg

        if "fg" in kwargs or "fg_color" in kwargs:
            new_fg = kwargs.get("fg", kwargs.get("fg_color"))
            self.normal_fg = new_fg
            if self._state == "normal" and not self._is_hovered:
                self.current_fg = new_fg

        if "border_color" in kwargs:
            self.border_color = kwargs["border_color"]

        if "disabled_bg" in kwargs:
            self.disabled_bg = kwargs["disabled_bg"]
            if self._state == "disabled":
                self.current_bg = self.disabled_bg

        if "disabled_fg" in kwargs:
            self.disabled_fg = kwargs["disabled_fg"]
            if self._state == "disabled":
                self.current_fg = self.disabled_fg

        if "hover_bg" in kwargs:
            self.hover_bg = kwargs["hover_bg"]

        if "hover_fg" in kwargs:
            self.hover_fg = kwargs["hover_fg"]

        if "parent_bg" in kwargs:
            self.parent_bg = kwargs["parent_bg"]
            canvas_kwargs["bg"] = kwargs["parent_bg"]

        if "radius" in kwargs:
            self.radius = kwargs["radius"]

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
        radius: Optional[int] = None,
        font: Tuple[str, int, str] = ("Segoe UI", 8, "bold"),
        height: int = 24,
        parent_bg: str = "#ffffff",
    ):
        self.text = text
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.border_color = border_color
        self.radius = radius
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

        rad = self.radius if self.radius is not None else h / 2
        draw_rounded_rect(self, 1, 1, w - 2, h - 2, radius=rad, **draw_kwargs)
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


class IOSStyleToggleSwitch(tk.Canvas):
    """Modern iOS / macOS styled animated pill toggle switch."""

    def __init__(
        self,
        parent: tk.Widget,
        variable: Optional[tk.BooleanVar] = None,
        command: Optional[Callable[[bool], None]] = None,
        width: int = 40,
        height: int = 22,
        on_color: str = "#881337",
        off_color: str = "#334155",
        thumb_color: str = "#ffffff",
        parent_bg: str = "#111827",
    ):
        self.variable = variable
        self.command = command
        self.sw_width = width
        self.sw_height = height
        self.on_color = on_color
        self.off_color = off_color
        self.thumb_color = thumb_color
        self.parent_bg = parent_bg

        self.is_on = bool(self.variable.get()) if self.variable else False
        self.current_x = float(self.sw_width - self.sw_height + 2) if self.is_on else 2.0
        self.target_x = self.current_x
        self._animating = False

        super().__init__(
            parent,
            width=self.sw_width,
            height=self.sw_height,
            bg=parent_bg,
            highlightthickness=0,
            cursor="hand2",
        )

        self.bind("<Button-1>", self._on_click)
        if self.variable:
            self.variable.trace_add("write", self._on_var_changed)

        self._draw_switch()

    def _on_click(self, event=None) -> None:
        self.is_on = not self.is_on
        if self.variable:
            self.variable.set(self.is_on)
        self.target_x = float(self.sw_width - self.sw_height + 2) if self.is_on else 2.0
        self._start_animation()
        if self.command:
            try:
                self.command(self.is_on)
            except Exception:
                pass

    def _on_var_changed(self, *args) -> None:
        if self.variable:
            val = bool(self.variable.get())
            if val != self.is_on:
                self.is_on = val
                self.target_x = float(self.sw_width - self.sw_height + 2) if self.is_on else 2.0
                self._start_animation()

    def _start_animation(self) -> None:
        if not self._animating:
            self._animating = True
            self._animate_step()

    def _animate_step(self) -> None:
        diff = self.target_x - self.current_x
        if abs(diff) < 0.8:
            self.current_x = self.target_x
            self._animating = False
            self._draw_switch()
            return

        self.current_x += diff * 0.35
        self._draw_switch()
        self.after(16, self._animate_step)

    def _draw_switch(self) -> None:
        self.delete("all")
        w = self.sw_width
        h = self.sw_height
        rad = h / 2.0

        bg_col = self.on_color if self.is_on else self.off_color
        draw_rounded_rect(self, 1, 1, w - 1, h - 1, radius=rad, fill=bg_col)

        # Thumb circle
        r = (h - 6) / 2.0
        thumb_x = self.current_x + r + 1
        thumb_y = h / 2.0

        self.create_oval(
            thumb_x - r,
            thumb_y - r,
            thumb_x + r,
            thumb_y + r,
            fill=self.thumb_color,
            outline="",
        )

    def set_colors(self, on_color: str, off_color: str, parent_bg: str) -> None:
        self.on_color = on_color
        self.off_color = off_color
        self.parent_bg = parent_bg
        self.config(bg=parent_bg)
        self._draw_switch()

