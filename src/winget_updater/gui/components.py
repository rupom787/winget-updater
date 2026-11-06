"""Clean, human-crafted modern UI components for Software & Package Updater.
Features smooth rounded widgets, refined typography, two-column layout, and bottom details drawer.
"""

import os
import tkinter as tk
from PIL import Image, ImageDraw, ImageFont, ImageTk
from tkinter import messagebox, ttk
from typing import Callable, Dict, List, Optional
from winget_updater.gui.animations import (
    AnimatedSkeletonOverlay,
    DeckCounterAnimator,
    FluentFloatingToast,
    PulsingWarningBeacon,
    ToastNotificationHelper,
    VectorIconDrawer,
)
from winget_updater.gui.rounded_widgets import RoundedButton, RoundedPillBadge, draw_rounded_rect
from winget_updater.gui.theme import DARK_THEME, DREAM_THEME, LIGHT_THEME, ThemeColors
from winget_updater.models import CompatibilityStatus, PackageType, ProgramItem, UpdateAction, UpdateOutcome



class AppIconGenerator:
    """Generates and caches vibrant, high-DPI 22x22 macOS/Windows-11 rounded squircle icons
    for software packages in the table and details drawer.
    Bound per-toplevel Tk instance to guarantee robust multi-window and test suite safety.
    """
    _pil_cache: Dict[Tuple[str, int], Image.Image] = {}
    _photo_cache: Dict[Tuple[int, str, int], ImageTk.PhotoImage] = {}

    @classmethod
    def get_icon(cls, widget: tk.Widget, name: str, size: int = 22) -> Optional[ImageTk.PhotoImage]:
        clean_name = (name or "").strip()
        pil_key = (clean_name.lower(), size)

        # 1. Retrieve or generate the supersampled PIL Image
        if pil_key in cls._pil_cache:
            img_resized = cls._pil_cache[pil_key]
        else:
            scale = 2
            s = size * scale
            img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            n = clean_name.lower()

            if any(k in n for k in ["adguard", "adblock", "ublock", "blocker", "poper"]):
                bg1 = (16, 185, 129)  # Emerald
                icon_type = "shield"
            elif any(k in n for k in ["download", "idm", "aria", "torrent", "manager"]):
                bg1 = (6, 182, 212)   # Cyan / Teal
                icon_type = "download"
            elif any(k in n for k in ["git", "github", "gitlab", "version"]):
                bg1 = (249, 115, 22)  # Coral Orange
                icon_type = "diamond"
            elif "edge" in n:
                bg1 = (2, 132, 199)   # Ocean Blue
                icon_type = "globe"
            elif any(k in n for k in ["chrome", "google", "chromium"]):
                bg1 = (37, 99, 235)   # Google Blue
                icon_type = "globe"
            elif any(k in n for k in ["code", "visual studio", "cursor", "sublime"]):
                bg1 = (0, 122, 204)   # VS Blue
                icon_type = "code"
            elif "python" in n:
                bg1 = (48, 105, 152)  # Python Blue
                icon_type = "monogram"
            elif any(k in n for k in ["node", "npm", "yarn", "bun"]):
                bg1 = (22, 163, 74)   # Node Emerald
                icon_type = "hex"
            elif any(k in n for k in ["tampermonkey", "greasemonkey", "script"]):
                bg1 = (15, 118, 110)  # Slate Teal
                icon_type = "monogram"
            elif any(k in n for k in ["discord", "steam", "game"]):
                bg1 = (88, 101, 242)  # Blurple
                icon_type = "gamepad"
            elif any(k in n for k in ["spotify", "music", "audio", "vlc"]):
                bg1 = (29, 185, 84)   # Spotify Green
                icon_type = "play"
            elif any(k in n for k in ["security", "antivirus", "defender", "malware"]):
                bg1 = (225, 29, 72)   # Ruby Crimson
                icon_type = "shield"
            else:
                palette = [
                    (225, 29, 72),   # Crimson
                    (139, 92, 246),  # Violet
                    (99, 102, 241),  # Indigo
                    (16, 185, 129),  # Emerald
                    (245, 158, 11),  # Amber
                    (6, 182, 212),   # Cyan
                    (236, 72, 153),  # Pink
                    (2, 132, 199),   # Sky
                ]
                bg1 = palette[abs(hash(clean_name)) % len(palette)]
                icon_type = "monogram"

            rad = int(s * 0.28)
            draw.rounded_rectangle([0, 0, s - 1, s - 1], radius=rad, fill=bg1)
            draw.rounded_rectangle([1, 1, s - 2, s - 2], radius=rad - 1, outline=(255, 255, 255, 65), width=1)

            fg = (255, 255, 255, 245)
            cx, cy = s // 2, s // 2
            r = int(s * 0.26)

            if icon_type == "shield":
                pts = [(cx, cy - r), (cx + r, cy - r + 3), (cx + r - 2, cy + r - 2), (cx, cy + r + 2), (cx - r + 2, cy + r - 2), (cx - r, cy - r + 3)]
                draw.polygon(pts, fill=fg)
            elif icon_type == "download":
                draw.polygon([(cx - r, cy), (cx + r, cy), (cx, cy + r)], fill=fg)
                draw.rectangle([cx - 2, cy - r, cx + 2, cy], fill=fg)
                draw.rectangle([cx - r, cy + r + 2, cx + r, cy + r + 4], fill=fg)
            elif icon_type == "diamond":
                draw.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=fg)
            elif icon_type == "globe":
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fg, width=2)
                draw.line([(cx - r, cy), (cx + r, cy)], fill=fg, width=1)
                draw.ellipse([cx - r // 2, cy - r, cx + r // 2, cy + r], outline=fg, width=1)
            elif icon_type == "code":
                draw.line([(cx - 2, cy - r), (cx - r, cy), (cx - 2, cy + r)], fill=fg, width=2)
                draw.line([(cx + 2, cy - r), (cx + r, cy), (cx + 2, cy + r)], fill=fg, width=2)
            elif icon_type == "hex":
                draw.polygon([
                    (cx, cy - r),
                    (cx + r, cy - r // 2),
                    (cx + r, cy + r // 2),
                    (cx, cy + r),
                    (cx - r, cy + r // 2),
                    (cx - r, cy - r // 2)
                ], fill=fg)
            elif icon_type == "play":
                draw.polygon([(cx - r + 2, cy - r), (cx + r, cy), (cx - r + 2, cy + r)], fill=fg)
            elif icon_type == "gamepad":
                draw.rounded_rectangle([cx - r, cy - r // 2, cx + r, cy + r // 2], radius=3, fill=fg)
            else:
                ch = (clean_name[:1] or "A").upper()
                try:
                    font = ImageFont.truetype("segoeui.ttf", int(s * 0.52))
                except Exception:
                    font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), ch, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                draw.text((cx - tw // 2, cy - th // 2 - 2), ch, font=font, fill=fg)

            img_resized = img.resize((size, size), Image.Resampling.LANCZOS)
            cls._pil_cache[pil_key] = img_resized

        # 2. Bind PhotoImage to the current widget's root instance
        try:
            root_id = id(widget.winfo_toplevel()) if hasattr(widget, "winfo_toplevel") else id(widget)
        except Exception:
            root_id = 0

        photo_key = (root_id, clean_name.lower(), size)
        if photo_key in cls._photo_cache:
            return cls._photo_cache[photo_key]

        try:
            photo = ImageTk.PhotoImage(img_resized, master=widget)
            cls._photo_cache[photo_key] = photo
            return photo
        except Exception:
            return None


class SidebarNavigation(tk.Frame):
    """Clean left sidebar navigation with smooth rounded filter cards, search box, and live counts."""

    # Human-readable filter view definitions
    FILTERS = [
        ("All Software", "All applications"),
        ("Updates Available", "Updates available"),
        ("Cannot Update", "Review & issues"),
        ("Up to Date", "Installed & current"),
        ("Ignored Updates", "Excluded applications"),
        ("Software Catalog", "Discover & install"),
    ]

    FILTER_ICONS = {
        "All Software": ("#e11d48", "grid"),
        "Updates Available": ("#06b6d4", "download"),
        "Cannot Update": ("#f59e0b", "warning"),
        "Up to Date": ("#10b981", "check"),
        "Ignored Updates": ("#8b5cf6", "slash"),
        "Software Catalog": ("#ec4899", "sparkle"),
    }

    def __init__(
        self,
        parent: tk.Widget,
        on_filter_changed: Callable[[str], None],
        on_search_changed: Callable[[str], None],
        on_category_changed: Callable[[str], None],
        on_open_tracker: Optional[Callable[[], None]] = None,
        on_open_runtimes: Optional[Callable[[], None]] = None,
        on_open_disk_cleanup: Optional[Callable[[], None]] = None,
        sys_info=None,
    ):
        super().__init__(
            parent,
            bg="#faf6f6",
            width=260,
            padx=14,
            pady=16,
            highlightbackground="#f3d5d9",
            highlightthickness=1,
        )
        self.pack_propagate(False)
        self.on_filter_changed = on_filter_changed
        self.on_search_changed = on_search_changed
        self.on_category_changed = on_category_changed
        self.on_open_tracker = on_open_tracker
        self.on_open_runtimes = on_open_runtimes
        self.on_open_disk_cleanup = on_open_disk_cleanup
        self.sys_info = sys_info
        self.theme: ThemeColors = DREAM_THEME

        self.current_filter = "All Software"
        self.hovered_filter: Optional[str] = None
        self._debounce_timer: Optional[str] = None

        # 1. App Title / Brand with macOS Traffic Lights
        self.brand_frame = tk.Frame(self, bg="#faf6f6")
        self.brand_frame.pack(fill=tk.X, pady=(0, 16))

        # macOS Traffic Lights [● ● ●]
        self.traffic_lights_canvas = tk.Canvas(
            self.brand_frame,
            width=180,
            height=18,
            bg="#faf6f6",
            highlightthickness=0,
            cursor="hand2",
        )
        self.traffic_lights_canvas.pack(anchor=tk.W, pady=(0, 6))
        self.traffic_lights_canvas.bind("<Button-1>", self._on_traffic_lights_click)
        self._draw_traffic_lights()

        # Retained reference for backwards test compatibility without duplicate UI clutter
        self.lbl_title = tk.Label(
            self.brand_frame,
            text="Software Updater",
            bg="#faf6f6",
            fg="#881337",
            font=("Segoe UI", 12, "bold"),
            justify=tk.LEFT,
            anchor="w",
        )

        self.lbl_version_tag = tk.Label(
            self.brand_frame,
            text="Windows 11 Edition",
            bg="#faf6f6",
            fg="#64748b",
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.lbl_version_tag.pack(anchor=tk.W, pady=(2, 0))

        # 2. Section Header: Navigation
        self.lbl_nav_header = tk.Label(
            self,
            text="NAVIGATION",
            bg="#faf6f6",
            fg="#94a3b8",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_nav_header.pack(fill=tk.X, pady=(2, 6))

        # Navigation Buttons Container
        self.nav_buttons_frame = tk.Frame(self, bg="#faf6f6")
        self.nav_buttons_frame.pack(fill=tk.X)

        self.filter_buttons: Dict[str, Dict[str, tk.Widget]] = {}

        for internal_name, display_label in self.FILTERS:
            btn_canvas = tk.Canvas(
                self.nav_buttons_frame,
                bg="#faf6f6",
                height=38,
                highlightthickness=0,
                cursor="hand2",
            )
            btn_canvas.pack(fill=tk.X, pady=2)

            self.filter_buttons[internal_name] = {
                "canvas": btn_canvas,
                "display_label": display_label,
                "count": "0",
            }

            btn_canvas.bind("<Button-1>", lambda e, f=internal_name: self._on_filter_click(f))
            btn_canvas.bind("<Enter>", lambda e, f=internal_name: self._on_filter_hover(f, True))
            btn_canvas.bind("<Leave>", lambda e, f=internal_name: self._on_filter_hover(f, False))

        # Quick Update Tracker Button
        self.btn_open_tracker = RoundedButton(
            self,
            text="📊 App Update Tracker",
            command=self._on_tracker_click,
            bg_color="#ffffff",
            fg_color="#881337",
            hover_bg="#fff1f2",
            border_color="#f3d5d9",
            radius=8,
            height=30,
            font=("Segoe UI", 9, "bold"),
            padding=(6, 2),
        )
        self.btn_open_tracker.pack(fill=tk.X, pady=(6, 4))

        # Quick Gaming & System Runtimes Manager Button
        self.btn_open_runtimes = RoundedButton(
            self,
            text="🎮 Game Runtimes Doctor",
            command=self._on_runtimes_click,
            bg_color="#ffffff",
            fg_color="#881337",
            hover_bg="#fff1f2",
            border_color="#f3d5d9",
            radius=8,
            height=30,
            font=("Segoe UI", 9, "bold"),
            padding=(6, 2),
        )
        self.btn_open_runtimes.pack(fill=tk.X, pady=(0, 4))

        # Quick Disk Space Reclaimer Button
        self.btn_open_disk_clean = RoundedButton(
            self,
            text="🧹 Disk Space Reclaimer",
            command=self._on_disk_clean_click,
            bg_color="#ffffff",
            fg_color="#0369a1",
            hover_bg="#f0f9ff",
            border_color="#f3d5d9",
            radius=8,
            height=30,
            font=("Segoe UI", 9, "bold"),
            padding=(6, 2),
        )
        self.btn_open_disk_clean.pack(fill=tk.X, pady=(0, 0))

        # Separator line
        self.sep1 = tk.Frame(self, bg="#f3d5d9", height=1)
        self.sep1.pack(fill=tk.X, pady=14)

        # 3. Section: Search Box
        self.lbl_search_header = tk.Label(
            self,
            text="SEARCH",
            bg="#faf6f6",
            fg="#94a3b8",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_search_header.pack(fill=tk.X, pady=(0, 4))

        self.search_container = tk.Frame(
            self,
            bg="#ffffff",
            highlightbackground="#f3d5d9",
            highlightthickness=1,
            padx=8,
            pady=4,
        )
        self.search_container.pack(fill=tk.X)

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)

        self.search_entry = tk.Entry(
            self.search_container,
            textvariable=self.search_var,
            bg="#ffffff",
            fg="#0f172a",
            insertbackground="#881337",
            relief=tk.FLAT,
            font=("Segoe UI", 9),
        )
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_search = self.search_entry  # Backwards-compatibility alias
        self.search_entry.bind("<Return>", lambda e: self._on_search_return())
        self.search_entry.bind("<Escape>", lambda e: self._clear_search())

        self.btn_clear_search = tk.Button(
            self.search_container,
            text="×",
            command=self._clear_search,
            bg="#ffffff",
            fg="#94a3b8",
            activebackground="#ffffff",
            activeforeground="#881337",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            padx=2,
            pady=0,
        )
        self.btn_clear_search.pack(side=tk.RIGHT)

        # 4. Section: Categories Dropdown
        self.lbl_cat_header = tk.Label(
            self,
            text="CATEGORIES",
            bg="#faf6f6",
            fg="#94a3b8",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_cat_header.pack(fill=tk.X, pady=(14, 4))

        self.cat_var = tk.StringVar(value="All Categories")
        self.category_combo = ttk.Combobox(
            self,
            textvariable=self.cat_var,
            state="readonly",
            values=[
                "All Categories",
                "Gaming & Runtimes",
                "Win32 Applications",
                "Microsoft Store / MSIX",
                "WinGet Packages",
                "Scoop Packages",
                "Chocolatey Packages",
                "Python (Pip)",
                "Node.js (Npm)",
                "Portable Applications",
                "Drivers & Extensions",
            ],
            font=("Segoe UI", 9),
        )
        self.category_combo.pack(fill=tk.X)
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_select)

        # 5. Bottom System Telemetry Frame
        self.telemetry_box = tk.Frame(
            self,
            bg="#ffffff",
            padx=10,
            pady=8,
            highlightbackground="#f3d5d9",
            highlightthickness=1,
        )
        self.telemetry_box.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        bld = "26300"
        arch = "64-bit"
        if self.sys_info:
            try:
                bld = self.sys_info.get_windows_build()
                arch = "64-bit" if "64" in str(self.sys_info.get_architecture()) else "32-bit"
            except Exception:
                pass

        self.lbl_tele_sys = tk.Label(
            self.telemetry_box,
            text=f"Windows 11 Build {bld} ({arch})",
            bg="#ffffff",
            fg="#166534",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_tele_sys.pack(anchor=tk.W)

        try:
            from winget_updater.engine.gpu import GpuAccelerationManager
            primary_gpu = GpuAccelerationManager.get_primary_gpu()
            gpu_display = primary_gpu.name.replace("NVIDIA ", "").replace("GeForce ", "").replace("Graphics", "").strip()
            gpu_text = f"GPU: {gpu_display} • DX12"
        except Exception:
            gpu_text = "GPU: Hardware Accelerated"

        self.lbl_tele_gpu = tk.Label(
            self.telemetry_box,
            text=gpu_text,
            bg="#ffffff",
            fg="#0369a1",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_tele_gpu.pack(anchor=tk.W, pady=(2, 0))

        self.lbl_tele_mode = tk.Label(
            self.telemetry_box,
            text="Administrator privileges active",
            bg="#ffffff",
            fg="#64748b",
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.lbl_tele_mode.pack(anchor=tk.W, pady=(2, 0))

        try:
            from winget_updater.adapters.manager import SourceManager
            sm = SourceManager()
            avail_sources = [s.upper() for s in sm.get_available_sources() if s not in ("vendor", "store")]
            src_str = " • ".join(avail_sources) if avail_sources else "WINGET"
            src_text = f"Managers: {src_str}"
        except Exception:
            src_text = "Managers: WINGET"

        self.lbl_tele_managers = tk.Label(
            self.telemetry_box,
            text=src_text,
            bg="#ffffff",
            fg="#7c3aed",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_tele_managers.pack(anchor=tk.W, pady=(2, 0))

        # Initial render & theme
        self._render_navigation_items()
        self.apply_theme(self.theme)


    def _on_traffic_lights_click(self, event) -> None:
        """Handles click on macOS-style traffic lights: Red=Close, Yellow=Minimize, Green=Maximize/Restore."""
        try:
            top = self.winfo_toplevel()
            if event.x <= 17:
                top.destroy()
            elif event.x <= 34:
                top.iconify()
            elif event.x <= 52:
                state = top.wm_state()
                top.wm_state("normal" if state == "zoomed" else "zoomed")
        except Exception:
            pass

    def _draw_traffic_lights(self) -> None:
        """Draws classic macOS traffic light buttons: Close (red), Minimize (yellow), Maximize (green),
        along with the 01 // ACRYLIC UI badge matching the website mockup."""
        if not hasattr(self, "traffic_lights_canvas"):
            return
        c = self.traffic_lights_canvas
        c.delete("all")
        bg_col = getattr(self.theme, "bg_sidebar", "#10182b")
        c.config(bg=bg_col)
        # Red, Yellow, Green dots with subtle darker borders
        dots = [
            (9, 9, "#ff5f56", "#e0443e"),
            (26, 9, "#ffbd2e", "#dea123"),
            (43, 9, "#27c93f", "#1aab29"),
        ]
        for cx, cy, fill_col, border_col in dots:
            c.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, fill=fill_col, outline=border_col, width=1)

        # 01 // ACRYLIC UI Pill Badge
        is_dark = (getattr(self.theme, "name", "dark") == "dark")
        badge_bg = "#221a36" if is_dark else "#f1f5f9"
        badge_bd = "#382a56" if is_dark else "#e2e8f0"
        badge_fg = "#a78bfa" if is_dark else "#64748b"
        draw_rounded_rect(c, 58, 0, 168, 18, radius=8, fill=badge_bg, outline=badge_bd, width=1)
        c.create_text(113, 9, text="01 // ACRYLIC UI", fill=badge_fg, font=("Segoe UI", 7, "bold"))

    def _render_navigation_items(self) -> None:
        """Draws rounded pill tabs for each sidebar navigation item with smooth hover & active styling."""
        for internal_name, data in self.filter_buttons.items():
            canvas = data["canvas"]
            display_label = data["display_label"]
            count = data["count"]
            is_active = (internal_name == self.current_filter)
            is_hovered = (internal_name == self.hovered_filter) and not is_active

            canvas.delete("all")
            w = canvas.winfo_width() or 230
            h = 36

            t = self.theme
            mode = getattr(t, "name", "light")
            if is_active:
                if mode == "dark":
                    draw_rounded_rect(canvas, 1, 1, w - 2, h - 2, radius=10, fill="#7c122e", outline="#b91c47", width=1.5)
                    text_color = "#ffffff"
                    badge_bg = "#4c0519"
                    badge_fg = "#fda4af"
                elif mode == "bloom":
                    draw_rounded_rect(canvas, 1, 1, w - 2, h - 2, radius=10, fill="#7c3aed", outline="#d946ef", width=1.5)
                    text_color = "#ffffff"
                    badge_bg = "#ede9fe"
                    badge_fg = "#7c3aed"
                else:
                    draw_rounded_rect(canvas, 1, 1, w - 2, h - 2, radius=10, fill="#800020", outline="#b45309", width=1.5)
                    text_color = "#ffffff"
                    badge_bg = "#991b1b"
                    badge_fg = "#ffffff"
            elif is_hovered:
                if mode == "dark":
                    draw_rounded_rect(canvas, 1, 1, w - 2, h - 2, radius=8, fill="#181c4e", outline="#2e3875", width=1)
                    text_color = "#f0f4fc"
                    badge_bg = "#252e75"
                    badge_fg = "#00f0ff"
                elif mode == "bloom":
                    draw_rounded_rect(canvas, 1, 1, w - 2, h - 2, radius=8, fill="#e0e7f8", outline="#c7d2fe", width=1)
                    text_color = "#1e1b4b"
                    badge_bg = "#ede9fe"
                    badge_fg = "#7c3aed"
                else:
                    draw_rounded_rect(canvas, 1, 1, w - 2, h - 2, radius=8, fill="#eee7da", outline="#d5c7b3", width=1)
                    text_color = "#1c1917"
                    badge_bg = "#e5dcce"
                    badge_fg = "#800020"
            else:
                item_fill = "#1e1834" if mode == "dark" else t.bg_card
                item_bd = "#2e254c" if mode == "dark" else t.border
                draw_rounded_rect(canvas, 1, 1, w - 2, h - 2, radius=8, fill=item_fill, outline=item_bd, width=1)
                text_color = t.fg_primary
                if internal_name == "Updates Available" and count not in ("0", ""):
                    badge_bg = t.tag_available_bg
                    badge_fg = t.tag_available_fg
                elif internal_name == "Cannot Update" and count not in ("0", ""):
                    badge_bg = t.tag_unverified_bg
                    badge_fg = t.tag_unverified_fg
                else:
                    badge_bg = t.bg_panel
                    badge_fg = t.fg_muted

            # 1. Squircle icon container on the left (22x22, radius=6)
            sx, sy = 8, 7
            sw = 22
            sq_color, glyph = self.FILTER_ICONS.get(internal_name, ("#e11d48", "grid"))
            draw_rounded_rect(canvas, sx, sy, sx + sw, sy + sw, radius=6, fill=sq_color)

            # Specular top reflection
            canvas.create_line(sx + 3, sy + 1, sx + sw - 3, sy + 1, fill="#ffffff", width=1)

            # Vector icon glyph in bright white
            scx, scy = sx + sw // 2, sy + sw // 2
            if glyph == "grid":
                for gx in (-3, 3):
                    for gy in (-3, 3):
                        canvas.create_rectangle(scx + gx - 2, scy + gy - 2, scx + gx + 1, scy + gy + 1, fill="#ffffff", outline="")
            elif glyph == "download":
                canvas.create_line(scx, scy - 5, scx, scy + 3, fill="#ffffff", width=2)
                canvas.create_line(scx - 4, scy, scx, scy + 4, fill="#ffffff", width=2)
                canvas.create_line(scx + 4, scy, scx, scy + 4, fill="#ffffff", width=2)
                canvas.create_line(scx - 4, scy + 6, scx + 4, scy + 6, fill="#ffffff", width=2)
            elif glyph == "warning":
                canvas.create_polygon(scx, scy - 6, scx + 6, scy + 5, scx - 6, scy + 5, fill="#ffffff", outline="")
                canvas.create_line(scx, scy - 2, scx, scy + 1, fill=sq_color, width=2)
                canvas.create_oval(scx - 1, scy + 3, scx + 1, scy + 5, fill=sq_color, outline="")
            elif glyph == "check":
                canvas.create_line(scx - 5, scy, scx - 1, scy + 4, fill="#ffffff", width=2)
                canvas.create_line(scx - 1, scy + 4, scx + 5, scy - 4, fill="#ffffff", width=2)
            elif glyph == "slash":
                canvas.create_oval(scx - 5, scy - 5, scx + 5, scy + 5, outline="#ffffff", width=2)
                canvas.create_line(scx - 4, scy + 4, scx + 4, scy - 4, fill="#ffffff", width=2)
            elif glyph == "sparkle":
                canvas.create_polygon(scx, scy - 6, scx + 2, scy - 1, scx + 6, scy, scx + 2, scy + 1, scx, scy + 6, scx - 2, scy + 1, scx - 6, scy, scx - 2, scy - 1, fill="#ffffff", outline="")

            # 2. Label text (spaced neatly past squircle)
            canvas.create_text(
                38,
                h / 2,
                text=display_label,
                fill=text_color,
                font=("Segoe UI", 9, "bold" if is_active else "normal"),
                anchor="w",
            )

            # 3. Badge pill on right or active glowing dot
            if is_active:
                dot_cx = w - 16
                dot_cy = h / 2
                halo_col = "#4c0519" if mode == "dark" else ("#fbcfe8" if mode == "bloom" else "#fee2e2")
                core_col = "#e11d48" if mode == "dark" else ("#d946ef" if mode == "bloom" else "#ffffff")
                canvas.create_oval(dot_cx - 6, dot_cy - 6, dot_cx + 6, dot_cy + 6, fill=halo_col, outline="")
                canvas.create_oval(dot_cx - 3, dot_cy - 3, dot_cx + 3, dot_cy + 3, fill=core_col, outline="")
            elif count not in ("0", "", None):
                badge_text = str(count)
                badge_w = max(22, len(badge_text) * 7 + 10)
                bx2 = w - 10
                bx1 = bx2 - badge_w
                by1 = (h - 20) / 2
                by2 = by1 + 20

                draw_rounded_rect(canvas, bx1, by1, bx2, by2, radius=10, fill=badge_bg)
                canvas.create_text(
                    (bx1 + bx2) / 2,
                    (by1 + by2) / 2,
                    text=badge_text,
                    fill=badge_fg,
                    font=("Segoe UI", 8, "bold"),
                    anchor="center",
                )

    def _on_filter_hover(self, filter_name: str, entering: bool) -> None:
        self.hovered_filter = filter_name if entering else None
        self._render_navigation_items()

    def _on_tracker_click(self) -> None:
        if self.on_open_tracker:
            self.on_open_tracker()

    def _on_runtimes_click(self) -> None:
        if self.on_open_runtimes:
            self.on_open_runtimes()

    def _on_disk_clean_click(self) -> None:
        if self.on_open_disk_cleanup:
            self.on_open_disk_cleanup()
        elif hasattr(self.master, "_open_disk_cleanup"):
            self.master._open_disk_cleanup()

    def _on_filter_click(self, filter_name: str) -> None:
        self.current_filter = filter_name
        self._render_navigation_items()
        if self.on_filter_changed:
            self.on_filter_changed(filter_name)

    def _on_search_changed(self, *args) -> None:
        if self._debounce_timer:
            self.after_cancel(self._debounce_timer)
        self._debounce_timer = self.after(200, self._trigger_search)

    def _on_search_return(self) -> None:
        if self._debounce_timer:
            self.after_cancel(self._debounce_timer)
            self._debounce_timer = None
        self._trigger_search()

    def _trigger_search(self) -> None:
        self._debounce_timer = None
        if self.on_search_changed:
            self.on_search_changed(self.search_var.get().strip())

    def _clear_search(self) -> None:
        if self._debounce_timer:
            self.after_cancel(self._debounce_timer)
            self._debounce_timer = None
        self.search_var.set("")
        if self.on_search_changed:
            self.on_search_changed("")

    def _on_category_select(self, event=None) -> None:
        if self.on_category_changed:
            self.on_category_changed(self.cat_var.get())

    def update_counts(
        self,
        total: int,
        updates: int,
        uptodate: int,
        ignored: int,
        unverified: int = 0,
    ) -> None:
        """Updates live numeric badges on sidebar navigation items."""
        if "All Software" in self.filter_buttons:
            self.filter_buttons["All Software"]["count"] = str(total)
        if "Updates Available" in self.filter_buttons:
            self.filter_buttons["Updates Available"]["count"] = str(updates)
        if "Cannot Update" in self.filter_buttons:
            self.filter_buttons["Cannot Update"]["count"] = str(unverified)
        if "Up to Date" in self.filter_buttons:
            self.filter_buttons["Up to Date"]["count"] = str(uptodate)
        if "Ignored Updates" in self.filter_buttons:
            self.filter_buttons["Ignored Updates"]["count"] = str(ignored)
        if "Software Catalog" in self.filter_buttons:
            self.filter_buttons["Software Catalog"]["count"] = "6k+"
        self._render_navigation_items()
        self._render_navigation_items()

    def _on_details_resize(self, event: tk.Event) -> None:
        """Dynamically adjust diagnostic wraplength so text never clips or overflows."""
        if hasattr(self, "lbl_diag_text"):
            new_wrap = max(220, event.width - 36)
            self.lbl_diag_text.config(wraplength=new_wrap)

    def apply_theme(self, theme: ThemeColors) -> None:
        self.theme = theme
        self.config(bg=theme.bg_sidebar, highlightbackground=theme.border)
        self.brand_frame.config(bg=theme.bg_sidebar)
        self._draw_traffic_lights()
        self.lbl_title.config(bg=theme.bg_sidebar, fg=theme.accent_burgundy)
        self.lbl_version_tag.config(bg=theme.bg_sidebar, fg=theme.fg_muted)
        self.lbl_nav_header.config(bg=theme.bg_sidebar, fg=theme.fg_muted)
        self.nav_buttons_frame.config(bg=theme.bg_sidebar)
        self.sep1.config(bg=theme.border)
        self.lbl_search_header.config(bg=theme.bg_sidebar, fg=theme.fg_muted)
        self.search_container.config(bg=theme.bg_input, highlightbackground=theme.border)
        self.search_entry.config(bg=theme.bg_input, fg=theme.fg_primary, insertbackground=theme.accent_burgundy)
        self.btn_clear_search.config(bg=theme.bg_input, fg=theme.fg_muted)
        self.lbl_cat_header.config(bg=theme.bg_sidebar, fg=theme.fg_muted)
        try:
            combo_style = ttk.Style()
            if theme.name == "dark":
                combo_style.theme_use("clam")
                combo_style.configure("TCombobox", fieldbackground="#141d30", background="#141d30", foreground="#f8fafc", bordercolor="#1e2c45", darkcolor="#141d30", lightcolor="#141d30")
                combo_style.map("TCombobox", fieldbackground=[("readonly", "#141d30")], foreground=[("readonly", "#f8fafc")])
            else:
                combo_style.theme_use("clam")
                combo_style.configure("TCombobox", fieldbackground="#ffffff", background="#f8fafc", foreground="#1e293b", bordercolor="#cbd5e1")
                combo_style.map("TCombobox", fieldbackground=[("readonly", "#ffffff")], foreground=[("readonly", "#1e293b")])
        except Exception:
            pass
        self.telemetry_box.config(bg=theme.bg_card, highlightbackground=theme.border)
        mode = getattr(theme, "name", "light")
        if mode == "dark":
            self.lbl_title.config(bg=theme.bg_sidebar, fg="#ffffff")
            self.lbl_tele_sys.config(bg=theme.bg_card, fg="#cbd5e1")
            if hasattr(self, "lbl_tele_gpu"):
                self.lbl_tele_gpu.config(bg=theme.bg_card, fg="#10b981")
            self.lbl_tele_mode.config(bg=theme.bg_card, fg="#64748b")
            if hasattr(self, "lbl_tele_managers"):
                self.lbl_tele_managers.config(text="Managers: WINGET • MSSTORE", bg=theme.bg_card, fg="#00f0ff")
        elif mode == "bloom":
            self.lbl_tele_sys.config(bg=theme.bg_card, fg="#7c3aed")
            if hasattr(self, "lbl_tele_gpu"):
                self.lbl_tele_gpu.config(bg=theme.bg_card, fg="#d946ef")
            self.lbl_tele_mode.config(bg=theme.bg_card, fg="#6366f1")
            if hasattr(self, "lbl_tele_managers"):
                self.lbl_tele_managers.config(bg=theme.bg_card, fg="#7c3aed")
        else:
            self.lbl_tele_sys.config(bg=theme.bg_card, fg=theme.accent_emerald)
            if hasattr(self, "lbl_tele_gpu"):
                self.lbl_tele_gpu.config(bg=theme.bg_card, fg="#800020")
            self.lbl_tele_mode.config(bg=theme.bg_card, fg=theme.fg_muted)
            if hasattr(self, "lbl_tele_managers"):
                self.lbl_tele_managers.config(bg=theme.bg_card, fg="#b45309")
        if hasattr(self, "btn_open_tracker"):
            self.btn_open_tracker.config(
                bg=theme.bg_button,
                fg=theme.fg_primary,
                border_color=theme.border,
                parent_bg=theme.bg_sidebar,
            )
        if hasattr(self, "btn_open_runtimes"):
            self.btn_open_runtimes.config(
                bg=theme.bg_button,
                fg=theme.fg_primary,
                border_color=theme.border,
                parent_bg=theme.bg_sidebar,
            )
        if hasattr(self, "btn_open_disk_clean"):
            self.btn_open_disk_clean.config(
                bg=theme.bg_button,
                fg="#38bdf8" if mode == "dark" else "#0284c7",
                border_color=theme.border,
                parent_bg=theme.bg_sidebar,
            )
        self._render_navigation_items()
        for d in self.filter_buttons.values():
            d["canvas"].config(bg=theme.bg_sidebar)
        self._render_navigation_items()

    def apply_typography(self, typo) -> None:
        """Applies dynamic font scaling to sidebar elements."""
        self.lbl_title.config(font=getattr(typo, "title", ("Segoe UI", 12, "bold")))
        self.lbl_version_tag.config(font=getattr(typo, "caption", ("Segoe UI", 9)))
        self.lbl_nav_header.config(font=getattr(typo, "section", ("Segoe UI", 9, "bold")))
        self.lbl_search_header.config(font=getattr(typo, "section", ("Segoe UI", 9, "bold")))
        self.lbl_cat_header.config(font=getattr(typo, "section", ("Segoe UI", 9, "bold")))
        self._render_navigation_items()


class DetailsDrawer(tk.Frame):
    """Bottom slide-up details drawer showing selected program icon, metadata, and rounded action buttons."""

    def __init__(
        self,
        parent: tk.Widget,
        on_single_update: Optional[Callable[[ProgramItem], None]] = None,
        on_exclude_item: Optional[Callable[[ProgramItem], None]] = None,
        on_uninstall_item: Optional[Callable[[ProgramItem], None]] = None,
        on_toast_message: Optional[Callable[[str, str], None]] = None,
        on_bind_source: Optional[Callable[[ProgramItem], None]] = None,
        on_allow_unverified: Optional[Callable[[ProgramItem], None]] = None,
        on_open_website: Optional[Callable[[ProgramItem], None]] = None,
        on_pin_item: Optional[Callable[[ProgramItem], None]] = None,
        on_skip_version: Optional[Callable[[ProgramItem], None]] = None,
    ):
        super().__init__(
            parent,
            bg="#161022",
            padx=16,
            pady=10,
            highlightbackground="#2d1b3b",
            highlightthickness=1,
        )
        self.on_single_update = on_single_update
        self.on_exclude_item = on_exclude_item
        self.on_uninstall_item = on_uninstall_item
        self.on_toast_message = on_toast_message
        self.on_bind_source = on_bind_source
        self.on_allow_unverified = on_allow_unverified
        self.on_open_website = on_open_website
        self.on_pin_item = on_pin_item
        self.on_skip_version = on_skip_version
        self.current_item: Optional[ProgramItem] = None
        self.theme: ThemeColors = DREAM_THEME

        # Right / Actions Container (packed first to guarantee right-side space)
        self.actions_container = tk.Frame(self, bg="#161022")
        self.actions_container.pack(side=tk.RIGHT, padx=(16, 12))

        # Left / Details Container
        self.details_container = tk.Frame(self, bg="#161022")
        self.details_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.details_container.bind("<Configure>", self._on_details_resize)

        # Header Row: Program Avatar, Title, and Rounded Status Pill
        self.header_row = tk.Frame(self.details_container, bg="#161022")
        self.header_row.pack(fill=tk.X, anchor=tk.W)

        # Rounded Avatar Canvas
        self.avatar_canvas = tk.Canvas(self.header_row, width=34, height=34, bg="#161022", highlightthickness=0)
        self.avatar_canvas.pack(side=tk.LEFT, padx=(0, 10))
        draw_rounded_rect(self.avatar_canvas, 1, 1, 33, 33, radius=10, fill="#20142e", outline="#361e4a", width=1)
        self.avatar_canvas.create_text(17, 17, text="A", fill="#e11d48", font=("Segoe UI", 11, "bold"))

        self.lbl_name = tk.Label(
            self.header_row,
            text="Select an application to view details",
            bg="#161022",
            fg="#cbd5e1",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        self.lbl_name.pack(side=tk.LEFT)

        # Rounded Status Pill Badge
        self.status_pill = RoundedPillBadge(self.header_row, text="", bg_color="#20142e", fg_color="#cbd5e1", parent_bg="#161022")
        # Kept hidden initially until an item is actively selected
        self.status_pill.pack_forget()

        # Metadata grid
        self.meta_frame = tk.Frame(self.details_container, bg="#161022")
        self.meta_frame.pack(fill=tk.X, pady=(4, 0))

        self.lbl_pub = tk.Label(
            self.meta_frame,
            text="Publisher: —",
            bg="#161022",
            fg="#94a3b8",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.lbl_pub.pack(anchor=tk.W)

        self.lbl_versions = tk.Label(
            self.meta_frame,
            text="Installed: —  •  Latest: —  •  Source: —",
            bg="#161022",
            fg="#f8fafc",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.lbl_versions.pack(anchor=tk.W, pady=(1, 0))

        self.lbl_id_path = tk.Label(
            self.meta_frame,
            text="Package ID: —  •  Location: —",
            bg="#161022",
            fg="#64748b",
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.lbl_id_path.pack(anchor=tk.W, pady=(1, 0))

        self.lbl_notes = tk.Label(
            self.meta_frame,
            text="",
            bg="#161022",
            fg="#e11d48",
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.lbl_notes.pack(anchor=tk.W, pady=(1, 0))

        # Dedicated Diagnostic Explanation Alert Box (Shows why item cannot update)
        self.diagnostic_box = tk.Frame(
            self.details_container,
            bg="#fffbeb",
            highlightbackground="#fef3c7",
            highlightthickness=1,
            padx=10,
            pady=4,
        )
        self.lbl_diag_icon = tk.Label(
            self.diagnostic_box,
            text="ℹ️",
            bg="#fffbeb",
            font=("Segoe UI", 9),
        )
        self.lbl_diag_icon.pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_diag_text = tk.Label(
            self.diagnostic_box,
            text="",
            bg="#fffbeb",
            fg="#92400e",
            font=("Segoe UI", 8),
            anchor="w",
            wraplength=600,
            justify=tk.LEFT,
        )
        self.lbl_diag_text.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 3 Rows of Action Pills inside self.actions_container

        # 3 Rows of Action Pills matching crop_mockup_right.png exactly:
        # Row 1: [ Exclude ] [ Folder ]
        self.row_act1 = tk.Frame(self.actions_container, bg="#161022")
        self.row_act1.pack(fill=tk.X, anchor=tk.E, pady=(0, 3))

        self.btn_exclude = RoundedButton(
            self.row_act1,
            text="Exclude",
            command=self._on_exclude_click,
            bg_color="#141d30",
            fg_color="#f8fafc",
            hover_bg="#1e2c45",
            border_color="#1e2c45",
            radius=8,
            font=("Segoe UI", 8),
            height=24,
            padding=(8, 2),
            parent_bg="#10182b",
        )
        self.btn_exclude.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_open_folder = RoundedButton(
            self.row_act1,
            text="Folder",
            command=self._on_open_folder_click,
            bg_color="#141d30",
            fg_color="#f8fafc",
            hover_bg="#1e2c45",
            border_color="#1e2c45",
            radius=8,
            font=("Segoe UI", 8),
            height=24,
            padding=(8, 2),
            parent_bg="#10182b",
        )
        self.btn_open_folder.pack(side=tk.LEFT)

        # Row 2: [ Copy ID ] [ Pin ] [ Skip ]
        self.row_act2 = tk.Frame(self.actions_container, bg="#161022")
        self.row_act2.pack(fill=tk.X, anchor=tk.E, pady=(0, 3))

        self.btn_copy_id = RoundedButton(
            self.row_act2,
            text="Copy ID",
            command=self._on_copy_id_click,
            bg_color="#141d30",
            fg_color="#f8fafc",
            hover_bg="#1e2c45",
            border_color="#1e2c45",
            radius=8,
            font=("Segoe UI", 8),
            height=24,
            padding=(8, 2),
            parent_bg="#10182b",
        )
        self.btn_copy_id.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_pin = RoundedButton(
            self.row_act2,
            text="Pin",
            command=self._on_pin_click,
            bg_color="#141d30",
            fg_color="#f8fafc",
            hover_bg="#1e2c45",
            border_color="#1e2c45",
            radius=8,
            font=("Segoe UI", 8),
            height=24,
            padding=(8, 2),
            parent_bg="#10182b",
        )
        self.btn_pin.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_skip = RoundedButton(
            self.row_act2,
            text="Skip",
            command=self._on_skip_click,
            bg_color="#141d30",
            fg_color="#64748b",
            hover_bg="#1e2c45",
            border_color="#1e2c45",
            radius=8,
            font=("Segoe UI", 8),
            height=24,
            padding=(8, 2),
            parent_bg="#10182b",
        )
        self.btn_skip.pack(side=tk.LEFT)

        # Row 3: [ Uninstall ] [ Update application ]
        self.row_act3 = tk.Frame(self.actions_container, bg="#161022")
        self.row_act3.pack(fill=tk.X, anchor=tk.E, pady=(0, 1))

        self.btn_uninstall = RoundedButton(
            self.row_act3,
            text="Uninstall",
            command=self._on_uninstall_click,
            bg_color="#141d30",
            fg_color="#f87171",
            hover_bg="#2e0b17",
            border_color="#450a0a",
            radius=8,
            font=("Segoe UI", 8),
            height=26,
            padding=(8, 2),
            parent_bg="#10182b",
        )
        self.btn_uninstall.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_update = RoundedButton(
            self.row_act3,
            text="Update application",
            command=self._on_update_click,
            bg_color="#680b26",
            fg_color="#ffffff",
            hover_bg="#881337",
            border_color="#9f1239",
            radius=8,
            font=("Segoe UI", 8, "bold"),
            height=26,
            padding=(8, 2),
            parent_bg="#10182b",
        )
        self.btn_update.pack(side=tk.LEFT)

        # Row 3: Extended Package Resolution & Fallback Actions
        self.resolution_actions = tk.Frame(self.actions_container, bg="#161022")
        self.resolution_actions.pack(fill=tk.X)

        self.btn_bind = RoundedButton(
            self.resolution_actions,
            text="🔗 Bind Winget ID",
            command=self._on_bind_click,
            bg_color="#ecfdf5",
            fg_color="#065f46",
            hover_bg="#d1fae5",
            border_color="#a7f3d0",
            radius=6,
            font=("Segoe UI", 8, "bold"),
            width=100,
            height=26,
            parent_bg="#161022",
        )
        self.btn_bind.pack(side=tk.LEFT, padx=(0, 3))

        self.btn_allow_unverified = RoundedButton(
            self.resolution_actions,
            text="⚡ Allow Update",
            command=self._on_allow_click,
            bg_color="#fef3c7",
            fg_color="#92400e",
            hover_bg="#fde68a",
            border_color="#fcd34d",
            radius=6,
            font=("Segoe UI", 8, "bold"),
            width=90,
            height=26,
            parent_bg="#faf6f6",
        )

        self.btn_website = RoundedButton(
            self.resolution_actions,
            text="🌐 Visit Site",
            command=self._on_website_click,
            bg_color="#f0f9ff",
            fg_color="#0369a1",
            hover_bg="#e0f2fe",
            border_color="#bae6fd",
            radius=6,
            font=("Segoe UI", 8),
            width=75,
            height=26,
            parent_bg="#faf6f6",
        )

    def set_item(self, item: Optional[ProgramItem]) -> None:
        """Populates the details drawer with program metadata and activates permissible actions."""
        self.current_item = item
        if not item:
            self.lbl_name.config(text="Select an application to view details", fg=self.theme.fg_muted)
            self.lbl_pub.config(text="Click any application in the table above to inspect version telemetry & actions.")
            self.lbl_versions.config(text="")
            self.lbl_id_path.config(text="")
            self.lbl_notes.config(text="")
            self.avatar_canvas.pack_forget()
            self.status_pill.pack_forget()
            self.actions_container.pack(side=tk.RIGHT, padx=(16, 0))
            is_dark = (self.theme.name == "dark")
            dis_bg = "#141d30" if is_dark else "#f1f5f9"
            dis_fg = "#64748b" if is_dark else "#94a3b8"
            up_dis_bg = "#7c122e" if is_dark else dis_bg
            up_dis_fg = "#ffffff" if is_dark else dis_fg
            pill_dis_bg = "#2d1b46" if is_dark else dis_bg
            pill_dis_fg = "#e2e8f0" if is_dark else dis_fg
            self.btn_update.config(state="disabled", text="Update application", bg=up_dis_bg, fg=up_dis_fg)
            self.btn_exclude.config(state="disabled", text="Exclude", bg=pill_dis_bg, fg=pill_dis_fg)
            self.btn_open_folder.config(state="disabled", text="Folder", bg=pill_dis_bg, fg=pill_dis_fg)
            self.btn_copy_id.config(state="disabled", text="Copy ID", bg=pill_dis_bg, fg=pill_dis_fg)
            self.btn_pin.config(state="disabled", text="Pin", bg=pill_dis_bg, fg=pill_dis_fg)
            self.btn_skip.pack(side=tk.LEFT)
            self.btn_skip.config(state="disabled", text="Skip", bg=pill_dis_bg, fg=pill_dis_fg)
            self.btn_uninstall.config(state="disabled", text="Uninstall", bg=pill_dis_bg, fg=pill_dis_fg)
            self.btn_bind.config(state="disabled")
            self.diagnostic_box.pack_forget()
            self.btn_allow_unverified.pack_forget()
            self.btn_website.pack_forget()
            self.resolution_actions.pack_forget()
            return

        # Restore widgets for selected item
        self.actions_container.pack(side=tk.RIGHT, padx=(16, 0))
        self.avatar_canvas.pack(side=tk.LEFT, padx=(0, 10), before=self.lbl_name)
        self.status_pill.pack(side=tk.LEFT, padx=(12, 0))

        # Name & Publisher
        self.lbl_name.config(text=item.name, fg=self.theme.fg_primary)
        pub_text = item.publisher or "Standard Publisher"
        self.lbl_pub.config(text=f"Publisher: {pub_text}")

        # Update initial avatar with theme-matched glass pill
        initial = (item.name.strip()[0] if item.name else "A").upper()
        self.avatar_canvas.delete("all")
        t = self.theme
        draw_rounded_rect(self.avatar_canvas, 1, 1, 33, 33, radius=10, fill=t.bg_card, outline=t.border, width=1)
        self.avatar_canvas.create_text(17, 17, text=initial, fill=t.accent_burgundy, font=("Segoe UI", 11, "bold"))

        # Versions & Source
        cur_v = item.installed_version or "Unknown"
        lat_v = item.latest_version or "—"
        src = item.source or "winget"
        pkg_id = item.id or item.name

        loc = item.install_location or "Standard system directory"
        compat = item.compatibility.status.value

        self.lbl_pub.config(text=f"Publisher: {pub_text}   •   Package Identifier: {pkg_id}")
        self.lbl_versions.config(text=f"Installed Version: {cur_v}   →   Available Release: {lat_v}   (Source: {src})")
        self.lbl_id_path.config(text=f"Compatibility: {compat}   •   Location: {loc}")

        # Status pill badge
        status_text, pill_bg, pill_fg = self._get_status_pill_info(item)
        self.status_pill.set_badge(status_text, bg_color=pill_bg, fg_color=pill_fg)
        self.lbl_notes.config(text=f"Note: {item.notes}" if item.notes else "")

        # Diagnostic Explanation Box
        reason = item.get_diagnostic_reason()
        is_catalog = item.installed_version in ("Not Installed", "None", None, "")
        if (not item.can_auto_update()) and item.action != UpdateAction.UP_TO_DATE and not is_catalog:
            self.lbl_diag_text.config(text=f"Why can't this update automatically? {reason}")
            self.diagnostic_box.pack(fill=tk.X, pady=(5, 0))
        else:
            self.diagnostic_box.pack_forget()

        # Update button state
        can_update = item.can_auto_update()

        if is_catalog:
            self.lbl_versions.config(text=f"Repository Source: {src.upper()}   •   Available Release: {lat_v}")
            self.btn_update.config(state="normal", text="Install software", bg="#881337", fg="#ffffff")
            self.btn_exclude.config(state="disabled")
            self.btn_open_folder.config(state="disabled")
            self.btn_uninstall.config(state="disabled")
            self.btn_pin.config(state="disabled", text="📌 Pin")
        elif can_update:
            self.btn_update.config(state="normal", text="Update application", bg="#881337", fg="#ffffff")
        else:
            if item.action == UpdateAction.UP_TO_DATE:
                txt = "Up to date"
            elif item.is_pinned:
                txt = "Pinned to version"
            elif item.action == UpdateAction.EXCLUDED:
                txt = "Excluded from updates"
            elif item.action == UpdateAction.SKIPPED_VERSION:
                txt = "Version skipped"
            elif item.action == UpdateAction.UNVERIFIED:
                txt = "Verification required"
            elif item.action == UpdateAction.NO_SOURCE:
                txt = "No repository source"
            else:
                txt = "Update unavailable"
            self.btn_update.config(state="disabled", text=txt)

        is_ignored = (item.action == UpdateAction.EXCLUDED)
        self.btn_exclude.config(state="normal", text="Un-exclude" if is_ignored else "Exclude")
        self.btn_open_folder.config(state="normal" if item.install_location else "disabled")
        self.btn_copy_id.config(state="normal")
        self.btn_bind.config(state="normal")
        self.btn_uninstall.config(state="normal")

        # Pin / Unpin Button state
        self.btn_pin.config(
            state="normal",
            text="Unpin" if item.is_pinned else "📌 Pin",
            fg_color="#059669" if item.is_pinned else ("#f8fafc" if self.theme.name == "dark" else "#334155"),
        )

        # Skip / Unskip Button state
        if item.action == UpdateAction.AVAILABLE and item.latest_version:
            self.btn_skip.pack(side=tk.LEFT)
            self.btn_skip.config(state="normal", text="⏭️ Skip")
        elif item.action == UpdateAction.SKIPPED_VERSION:
            self.btn_skip.pack(side=tk.LEFT)
            self.btn_skip.config(state="normal", text="Unskip")
        else:
            self.btn_skip.pack_forget()

        # Contextual action buttons pack / forget
        if item.action == UpdateAction.UNVERIFIED:
            self.btn_allow_unverified.pack(side=tk.LEFT, padx=(0, 3))
            self.btn_allow_unverified.config(state="normal")
        else:
            self.btn_allow_unverified.pack_forget()

        if item.action in (UpdateAction.NO_SOURCE, UpdateAction.UNVERIFIED, UpdateAction.LIST_ONLY):
            self.btn_website.pack(side=tk.LEFT)
            self.btn_website.config(state="normal")
        else:
            self.btn_website.pack_forget()

    def _get_status_pill_info(self, item: ProgramItem) -> tuple[str, str, str]:
        if item.installed_version in ("Not Installed", "None", None, ""):
            return "Ready to install", "#ecfdf5", "#065f46"
        if item.outcome == UpdateOutcome.UPDATED:
            return "Updated", "#ecfdf5", "#065f46"
        if item.outcome == UpdateOutcome.SIMULATED:
            return "Simulated", "#ecfdf5", "#065f46"
        if item.outcome == UpdateOutcome.FAILED:
            return "Failed", "#fee2e2", "#991b1b"
        if item.action == UpdateAction.AVAILABLE:
            return "Update available", "#ffe4e6", "#9f1239"
        if item.action == UpdateAction.UP_TO_DATE:
            return "Up to date", "#ecfdf5", "#065f46"
        if item.action == UpdateAction.PINNED:
            return "Pinned", "#eff6ff", "#1e40af"
        if item.action == UpdateAction.SKIPPED_VERSION:
            return "Version skipped", "#f3e8ff", "#6b21a8"
        if item.action == UpdateAction.UNVERIFIED:
            return "Could not verify", "#fef3c7", "#92400e"
        if item.action == UpdateAction.SCAN_FAILED:
            return "Scan failed", "#fee2e2", "#991b1b"
        if item.action == UpdateAction.EXCLUDED:
            return "Excluded", "#f3e8ff", "#6b21a8"
        if item.action == UpdateAction.NEWER_THAN_SOURCE:
            return "Newer than source", "#fef3c7", "#92400e"
        if item.action == UpdateAction.VENDOR_FALLBACK:
            return "Vendor fallback", "#eff6ff", "#1e40af"
        if item.action == UpdateAction.NO_SOURCE:
            return "No update source", "#f1f5f9", "#475569"
        return item.action.value, "#f1f5f9", "#475569"

    def _on_update_click(self) -> None:
        if self.current_item and self.on_single_update:
            self.on_single_update(self.current_item)

    def _on_exclude_click(self) -> None:
        if self.current_item and self.on_exclude_item:
            self.on_exclude_item(self.current_item)

    def _on_open_folder_click(self) -> None:
        if self.current_item and self.current_item.install_location:
            loc = self.current_item.install_location
            if os.path.exists(loc):
                try:
                    os.startfile(loc)
                except Exception:
                    pass
            else:
                if self.on_toast_message:
                    self.on_toast_message(f"Directory not found: {loc}", "info")

    def _on_copy_id_click(self) -> None:
        if self.current_item:
            cid = self.current_item.id or self.current_item.name
            self.clipboard_clear()
            self.clipboard_append(cid)
            if self.on_toast_message:
                self.on_toast_message(f"Copied package ID: {cid}", "info")
            else:
                ToastNotificationHelper.show_toast(self.lbl_name, f"Copied: {cid}")

    def _on_uninstall_click(self) -> None:
        if self.current_item and self.on_uninstall_item:
            self.on_uninstall_item(self.current_item)

    def _on_bind_click(self) -> None:
        if self.current_item and self.on_bind_source:
            self.on_bind_source(self.current_item)

    def _on_allow_click(self) -> None:
        if self.current_item and self.on_allow_unverified:
            self.on_allow_unverified(self.current_item)

    def _on_website_click(self) -> None:
        if self.current_item and self.on_open_website:
            self.on_open_website(self.current_item)

    def _on_pin_click(self) -> None:
        if self.current_item and self.on_pin_item:
            self.on_pin_item(self.current_item)

    def _on_skip_click(self) -> None:
        if self.current_item and self.on_skip_version:
            self.on_skip_version(self.current_item)

    def _on_details_resize(self, event: tk.Event) -> None:
        """Dynamically adjust diagnostic wraplength so text never clips or overflows."""
        if hasattr(self, "lbl_diag_text"):
            new_wrap = max(220, event.width - 36)
            self.lbl_diag_text.config(wraplength=new_wrap)

    def apply_theme(self, theme: ThemeColors) -> None:
        self.theme = theme
        is_dark = (theme.name == "dark")
        bg_col = "#1e1330" if is_dark else theme.bg_sidebar
        border_col = "#42265c" if is_dark else theme.border
        btn_bg = "#2d1b46" if is_dark else theme.bg_button
        btn_border = "#4f2e78" if is_dark else theme.border
        btn_fg = "#e2e8f0" if is_dark else theme.fg_primary

        self.config(bg=bg_col, highlightbackground=border_col)
        self.details_container.config(bg=bg_col)
        self.header_row.config(bg=bg_col)
        self.avatar_canvas.config(bg=bg_col)
        self.lbl_name.config(bg=bg_col, fg=theme.fg_primary if self.current_item else theme.fg_muted)
        self.meta_frame.config(bg=bg_col)
        self.lbl_pub.config(bg=bg_col, fg=theme.fg_secondary)
        self.lbl_versions.config(bg=bg_col, fg=theme.fg_primary)
        self.lbl_id_path.config(bg=bg_col, fg=theme.fg_muted)
        self.lbl_notes.config(bg=bg_col, fg=theme.accent_burgundy)
        self.actions_container.config(bg=bg_col)
        for r_act in (getattr(self, "row_act1", None), getattr(self, "row_act2", None), getattr(self, "row_act3", None), getattr(self, "secondary_actions", None), getattr(self, "secondary_row_b", None)):
            if r_act:
                r_act.config(bg=bg_col)
        self.resolution_actions.config(bg=bg_col)
        self.status_pill.config(bg=bg_col)
        if hasattr(self, "diagnostic_box"):
            box_bg = "#261908" if is_dark else "#fffbeb"
            box_border = "#78350f" if is_dark else "#fef3c7"
            box_fg = "#fef3c7" if is_dark else "#92400e"
            self.diagnostic_box.config(bg=box_bg, highlightbackground=box_border)
            if hasattr(self, "lbl_diag_icon"):
                self.lbl_diag_icon.config(bg=box_bg)
            if hasattr(self, "lbl_diag_text"):
                self.lbl_diag_text.config(bg=box_bg, fg=box_fg)

        # Theme drawer action buttons
        for btn in (
            getattr(self, "btn_open_folder", None),
            getattr(self, "btn_copy_id", None),
            getattr(self, "btn_pin", None),
            getattr(self, "btn_exclude", None),
            getattr(self, "btn_skip", None),
            getattr(self, "btn_uninstall", None),
            getattr(self, "btn_bind", None),
            getattr(self, "btn_allow", None),
            getattr(self, "btn_website", None),
        ):
            if btn:
                btn.disabled_bg = "#20142e" if is_dark else theme.bg_button
                btn.disabled_fg = "#64748b" if is_dark else theme.fg_muted
                btn.config(
                    bg=btn_bg,
                    fg=btn_fg,
                    border_color=btn_border,
                    parent_bg=bg_col,
                    disabled_bg=btn.disabled_bg,
                    disabled_fg=btn.disabled_fg,
                )
        if hasattr(self, "btn_update"):
            up_bg = "#7c122e" if is_dark else theme.accent_burgundy
            self.btn_update.disabled_bg = up_bg
            self.btn_update.disabled_fg = "#ffffff"
            self.btn_update.config(
                bg=up_bg,
                fg="#ffffff",
                border_color="#b91c47" if is_dark else theme.border,
                parent_bg=bg_col,
                hover_bg="#9f1239" if is_dark else theme.accent_burgundy_hover,
                disabled_bg=up_bg,
                disabled_fg="#ffffff",
            )


class DiagnosticsResolutionBanner(tk.Frame):
    """Frosted amber banner surfaced above table when filtering software that cannot auto-update.
    Provides clear context on missing manifests or publisher variance, plus 1-click batch auto-resolution.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_auto_resolve_all: Optional[Callable[[], None]] = None,
        on_open_help: Optional[Callable[[], None]] = None,
    ):
        super().__init__(
            parent,
            bg="#fffbeb",
            highlightbackground="#fde68a",
            highlightthickness=1,
            padx=14,
            pady=8,
        )
        self.on_auto_resolve_all = on_auto_resolve_all
        self.on_open_help = on_open_help

        # Left: Icon & Explanatory text
        self.left_col = tk.Frame(self, bg="#fffbeb")
        self.left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.title_row = tk.Frame(self.left_col, bg="#fffbeb")
        self.title_row.pack(anchor="w")

        self.lbl_badge = RoundedPillBadge(
            self.title_row,
            text="DIAGNOSTIC INSPECTOR",
            bg_color="#fef3c7",
            fg_color="#92400e",
            radius=6,
            font=("Segoe UI", 8, "bold"),
            height=20,
            parent_bg="#fffbeb",
        )
        self.lbl_badge.pack(side=tk.LEFT, padx=(0, 8))

        self.lbl_headline = tk.Label(
            self.title_row,
            text="Software Requiring Review or Lacking Public Manifests",
            bg="#fffbeb",
            fg="#78350f",
            font=("Segoe UI", 9, "bold"),
        )
        self.lbl_headline.pack(side=tk.LEFT)

        self.lbl_desc = tk.Label(
            self.left_col,
            text="These applications cannot update automatically due to publisher name differences, ambiguous matches, or missing repository IDs. Review reasons below or use 1-click unlock tools.",
            bg="#fffbeb",
            fg="#92400e",
            font=("Segoe UI", 8),
            anchor="w",
            justify=tk.LEFT,
        )
        self.lbl_desc.pack(anchor="w", pady=(2, 0))

        # Right: Quick action buttons
        self.right_actions = tk.Frame(self, bg="#fffbeb")
        self.right_actions.pack(side=tk.RIGHT, padx=(12, 0))

        self.btn_auto_resolve = RoundedButton(
            self.right_actions,
            text="⚡ Auto-Approve Closest Matches",
            command=self._on_auto_resolve_click,
            bg_color="#881337",
            fg_color="#ffffff",
            hover_bg="#9f1239",
            radius=6,
            font=("Segoe UI", 8, "bold"),
            width=200,
            height=28,
            parent_bg="#fffbeb",
        )
        self.btn_auto_resolve.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_help = RoundedButton(
            self.right_actions,
            text="❓ Why Can't These Update?",
            command=self._on_help_click,
            bg_color="#ffffff",
            fg_color="#78350f",
            border_color="#fcd34d",
            hover_bg="#fef3c7",
            radius=6,
            font=("Segoe UI", 8),
            width=165,
            height=28,
            parent_bg="#fffbeb",
        )
        self.btn_help.pack(side=tk.LEFT)

    def _on_auto_resolve_click(self) -> None:
        if self.on_auto_resolve_all:
            self.on_auto_resolve_all()

    def _on_help_click(self) -> None:
        if self.on_open_help:
            self.on_open_help()

    def set_stats(self, count: int, unverified: int, no_source: int) -> None:
        """Updates banner summary text with live counts."""
        txt = (
            f"Showing {count} items: {unverified} awaiting confirmation (publisher/name difference), "
            f"{no_source} with no public winget manifest. Select any item to view diagnosis & bind package."
        )
        self.lbl_desc.config(text=txt)

    def _on_details_resize(self, event: tk.Event) -> None:
        """Dynamically adjust diagnostic wraplength so text never clips or overflows."""
        if hasattr(self, "lbl_diag_text"):
            new_wrap = max(220, event.width - 36)
            self.lbl_diag_text.config(wraplength=new_wrap)

    def apply_theme(self, theme: ThemeColors) -> None:
        is_dark = (theme.name == "dark")
        bg_col = "#261908" if is_dark else "#fffbeb"
        border_col = "#78350f" if is_dark else "#fde68a"
        fg_col = "#fef3c7" if is_dark else "#78350f"
        desc_col = "#fef08a" if is_dark else "#92400e"

        self.config(bg=bg_col, highlightbackground=border_col)
        self.left_col.config(bg=bg_col)
        self.title_row.config(bg=bg_col)
        self.lbl_headline.config(bg=bg_col, fg=fg_col)
        self.lbl_desc.config(bg=bg_col, fg=desc_col)
        self.right_actions.config(bg=bg_col)


class ProgramTableView(tk.Frame):
    """4-Column Installed Software Table view with clear status pills, virtualized rendering,
    and extended multi-selection batch capabilities.
    Columns: Application Name, Installed Version, Available Version, Status.
    """

    COLUMNS = [
        ("name", "Application Name", 280),
        ("installed", "Installed", 120),
        ("latest", "Available", 120),
        ("status", "Status", 140),
    ]

    def __init__(
        self,
        parent: tk.Widget,
        on_double_click: Optional[Callable[[ProgramItem], None]] = None,
        on_select_item: Optional[Callable[[Optional[ProgramItem]], None]] = None,
        on_exclude_item: Optional[Callable[[ProgramItem], None]] = None,
        on_single_update: Optional[Callable[[ProgramItem], None]] = None,
        on_uninstall_item: Optional[Callable[[ProgramItem], None]] = None,
        on_toast_message: Optional[Callable[[str, str], None]] = None,
        on_batch_select: Optional[Callable[[List[ProgramItem]], None]] = None,
        on_bind_source: Optional[Callable[[ProgramItem], None]] = None,
        on_allow_unverified: Optional[Callable[[ProgramItem], None]] = None,
        on_open_website: Optional[Callable[[ProgramItem], None]] = None,
        on_pin_item: Optional[Callable[[ProgramItem], None]] = None,
        on_skip_version: Optional[Callable[[ProgramItem], None]] = None,
        on_batch_update: Optional[Callable[[List[ProgramItem]], None]] = None,
        on_batch_pin: Optional[Callable[[List[ProgramItem]], None]] = None,
        on_batch_exclude: Optional[Callable[[List[ProgramItem]], None]] = None,
        on_batch_allow: Optional[Callable[[List[ProgramItem]], None]] = None,
    ):
        super().__init__(parent, bg="#10182b")
        self.theme: ThemeColors = DREAM_THEME
        self.on_double_click = on_double_click
        self.on_select_item = on_select_item
        self.on_exclude_item = on_exclude_item
        self.on_single_update = on_single_update
        self.on_uninstall_item = on_uninstall_item
        self.on_toast_message = on_toast_message
        self.on_batch_select = on_batch_select
        self.on_bind_source = on_bind_source
        self.on_allow_unverified = on_allow_unverified
        self.on_open_website = on_open_website
        self.on_pin_item = on_pin_item
        self.on_skip_version = on_skip_version
        self.on_batch_update = on_batch_update
        self.on_batch_pin = on_batch_pin
        self.on_batch_exclude = on_batch_exclude
        self.on_batch_allow = on_batch_allow
        self.items_by_iid: Dict[str, ProgramItem] = {}
        self._current_generation: int = 0

        # Configure High-Contrast Clean Treeview Style
        style = ttk.Style()
        style.configure(
            "CleanWine.Treeview",
            background="#ffffff",
            foreground="#0f172a",
            fieldbackground="#ffffff",
            rowheight=34,
            font=("Segoe UI", 9),
            borderwidth=0,
        )
        style.configure(
            "CleanWine.Treeview.Heading",
            background="#faf6f6",
            foreground="#881337",
            relief="flat",
            borderwidth=1,
            font=("Segoe UI", 9, "bold"),
        )
        style.map(
            "CleanWine.Treeview.Heading",
            background=[("active", "#fff1f2")],
            foreground=[("active", "#9f1239")],
        )
        style.map(
            "CleanWine.Treeview",
            background=[("selected", "#ffe4e6")],
            foreground=[("selected", "#881337")],
        )

        cols = ("installed", "latest", "status")
        self.tree = ttk.Treeview(self, columns=cols, show="tree headings", selectmode="extended", style="CleanWine.Treeview")

        _orig_col = self.tree.column
        _orig_head = self.tree.heading

        def _safe_column(col_id, *args, **kwargs):
            actual = "#0" if col_id == "name" else col_id
            return _orig_col(actual, *args, **kwargs)

        def _safe_heading(col_id, *args, **kwargs):
            actual = "#0" if col_id == "name" else col_id
            return _orig_head(actual, *args, **kwargs)

        self.tree.column = _safe_column
        self.tree.heading = _safe_heading

        self.tree.heading("#0", text="Application Name", command=lambda: self._sort_column("name", False))
        self.tree.column("#0", width=340, minwidth=140, anchor=tk.W)

        self._last_configured_width: int = 0
        for col_id, col_text, col_width in self.COLUMNS[1:]:
            _orig_head(col_id, text=col_text, command=lambda c=col_id: self._sort_column(c, False))
            _orig_col(col_id, width=col_width, minwidth=80, anchor=tk.W)

        # Clear Status Badge Tags
        self.tree.tag_configure("tag_catalog", background="#f0fdf4", foreground="#166534")
        self.tree.tag_configure("tag_available", background="#fef2f2", foreground="#991b1b")
        self.tree.tag_configure("tag_uptodate", background="#ffffff", foreground="#166534")
        self.tree.tag_configure("tag_uptodate_alt", background="#fdfafa", foreground="#166534")
        self.tree.tag_configure("tag_downgrade", background="#fffbeb", foreground="#92400e")
        self.tree.tag_configure("tag_fallback", background="#eff6ff", foreground="#1e40af")
        self.tree.tag_configure("tag_unverified", background="#fffbeb", foreground="#92400e")
        self.tree.tag_configure("tag_ignored", background="#f5f3ff", foreground="#5b21b6")
        self.tree.tag_configure("tag_incompat", background="#fef2f2", foreground="#991b1b")
        self.tree.tag_configure("tag_nosource", background="#ffffff", foreground="#475569")
        self.tree.tag_configure("tag_nosource_alt", background="#fdfafa", foreground="#475569")

        # Clean Frosted Scrollbars
        self.vsb = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview, style="CleanWine.Vertical.TScrollbar")
        self.hsb = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.vsb.set, xscrollcommand=self.hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.vsb.grid(row=0, column=1, sticky="ns")

        # Shimmering Skeleton Loader Screen
        self.skeleton = AnimatedSkeletonOverlay(self)
        self.skeleton.grid(row=0, column=0, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Bind events
        self.tree.bind("<Double-1>", self._handle_double_click)
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self._handle_select)
        self.tree.bind("<MouseWheel>", self._on_mousewheel)
        self.tree.bind("<Motion>", self._on_tree_motion)
        self.tree.bind("<Leave>", self._on_tree_leave)
        self.bind("<Configure>", self._on_table_resize)

        # Context Menu
        self.context_menu = tk.Menu(self, tearoff=0, bg="#ffffff", fg="#0f172a", activebackground="#fff1f2", activeforeground="#881337")
        self.apply_theme(self.theme)

    def _on_details_resize(self, event: tk.Event) -> None:
        """Dynamically adjust diagnostic wraplength so text never clips or overflows."""
        if hasattr(self, "lbl_diag_text"):
            new_wrap = max(220, event.width - 36)
            self.lbl_diag_text.config(wraplength=new_wrap)

    def apply_theme(self, theme: ThemeColors) -> None:
        self.theme = theme
        self.config(bg=theme.bg_card)
        style = ttk.Style()
        is_dark = (theme.name == "dark")
        style.configure(
            "CleanWine.Treeview",
            background=theme.bg_table,
            foreground=theme.fg_primary,
            fieldbackground=theme.bg_table,
            borderwidth=0,
            relief="flat",
        )
        style.configure(
            "CleanWine.Treeview.Heading",
            background=theme.bg_header,
            foreground="#94a3b8" if is_dark else theme.accent_burgundy,
            borderwidth=0,
            relief="flat",
            font=("Segoe UI", 9, "bold"),
        )
        try:
            style.layout("CleanWine.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
        except Exception:
            pass
        if is_dark:
            style.configure(
                "CleanWine.Vertical.TScrollbar",
                width=6,
                arrowsize=0,
                background="#4c3b6e",
                troughcolor="#141126",
                bordercolor="#141126",
                darkcolor="#4c3b6e",
                lightcolor="#4c3b6e",
                relief="flat",
                borderwidth=0,
            )
            try:
                style.layout("CleanWine.Vertical.TScrollbar", [
                    ("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
                        ("Vertical.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})
                    ]})
                ])
            except Exception:
                pass
        else:
            style.configure(
                "CleanWine.Vertical.TScrollbar",
                background="#f1f5f9",
                troughcolor="#faf7f2",
                bordercolor="#e2e8f0",
                arrowcolor="#64748b",
                relief="flat",
                borderwidth=0,
            )
        is_dark = (theme.name == "dark")
        sel_bg = "#065f46" if is_dark else theme.bg_card_selected
        sel_fg = "#ffffff" if is_dark else theme.accent_burgundy
        style.map(
            "CleanWine.Treeview",
            background=[("selected", sel_bg)],
            foreground=[("selected", sel_fg)],
        )

        # Subtle alternating dark glass rows so icons and text pop cleanly
        bg_even = "#141126" if is_dark else "#ffffff"
        bg_odd = "#18142e" if is_dark else "#fdfcf9"

        self.tree.tag_configure("tag_catalog", background=bg_even, foreground="#34d399" if is_dark else "#065f46")
        self.tree.tag_configure("tag_available", background="#2a1224" if is_dark else "#fff1f2", foreground="#fda4af" if is_dark else "#991b1b")
        self.tree.tag_configure("tag_uptodate", background=bg_even, foreground="#34d399" if is_dark else "#166534")
        self.tree.tag_configure("tag_uptodate_alt", background=bg_odd, foreground="#34d399" if is_dark else "#166534")
        self.tree.tag_configure("tag_downgrade", background=bg_even, foreground="#fbbf24" if is_dark else "#92400e")
        self.tree.tag_configure("tag_fallback", background=bg_odd, foreground="#a5b4fc" if is_dark else "#1e40af")
        self.tree.tag_configure("tag_unverified", background=bg_even, foreground="#fbbf24" if is_dark else "#92400e")
        self.tree.tag_configure("tag_ignored", background=bg_odd, foreground="#c084fc" if is_dark else "#5b21b6")
        self.tree.tag_configure("tag_incompat", background="#180c16" if is_dark else "#fff1f2", foreground="#f87171" if is_dark else "#991b1b")
        self.tree.tag_configure("tag_nosource", background=bg_even, foreground="#94a3b8" if is_dark else "#475569")
        self.tree.tag_configure("tag_nosource_alt", background=bg_odd, foreground="#94a3b8" if is_dark else "#475569")
        self.tree.tag_configure("tag_hover", background="#251c3d" if is_dark else "#f1f5f9")

        self.skeleton.apply_theme(theme)
        self.context_menu.config(bg=theme.bg_card, fg=theme.fg_primary, activebackground=theme.bg_card_hover, activeforeground=theme.accent_burgundy)

    def apply_typography(self, typo) -> None:
        """Applies dynamic font scaling and row height to treeview."""
        style = ttk.Style()
        style.configure(
            "CleanWine.Treeview",
            rowheight=getattr(typo, "row_height", 36),
            font=getattr(typo, "table", ("Segoe UI", 10)),
        )
        style.configure(
            "CleanWine.Treeview.Heading",
            font=getattr(typo, "table_bold", ("Segoe UI", 10, "bold")),
        )

    def show_skeleton(self) -> None:
        self.skeleton.lift()
        self.skeleton.start_shimmer()

    def hide_skeleton(self) -> None:
        self.skeleton.stop_shimmer()
        self.skeleton.lower()

    def _on_table_resize(self, event: tk.Event) -> None:
        """Dynamically adjust column widths so they proportionally fill 100% of visible table space."""
        total_w = event.width
        if total_w < 50 or abs(total_w - self._last_configured_width) < 6:
            return
        self._last_configured_width = total_w

        # Account for vertical scrollbar (~18px) and border padding (~4px)
        available = max(total_w - 22, 500)

        min_installed = 110
        min_latest = 110
        min_status = 140
        min_name = 220
        min_total = min_installed + min_latest + min_status + min_name  # 580

        if available <= min_total:
            self.tree.column("name", width=min_name, stretch=False)
            self.tree.column("installed", width=min_installed, stretch=False)
            self.tree.column("latest", width=min_latest, stretch=False)
            self.tree.column("status", width=min_status, stretch=False)
        else:
            w_inst = max(min_installed, int(available * 0.17))
            w_late = max(min_latest, int(available * 0.17))
            w_stat = max(min_status, int(available * 0.18))
            w_name = available - (w_inst + w_late + w_stat)

            self.tree.column("name", width=w_name, stretch=True)
            self.tree.column("installed", width=w_inst, stretch=False)
            self.tree.column("latest", width=w_late, stretch=False)
            self.tree.column("status", width=w_stat, stretch=False)

    def _on_mousewheel(self, event):
        delta = getattr(event, "delta", 0)
        units = -(delta / 120.0) if delta != 0 else 0
        if not hasattr(self, "_scroll_velocity"):
            self._scroll_velocity = 0.0
            self._is_smooth_scrolling = False
        self._scroll_velocity += units * 0.035
        if not self._is_smooth_scrolling:
            self._is_smooth_scrolling = True
            self._smooth_scroll_step()
        return "break"

    def _smooth_scroll_step(self):
        if not self.winfo_ismapped():
            self._is_smooth_scrolling = False
            return
        current_y = self.tree.yview()[0]
        target_y = max(0.0, min(1.0, current_y + self._scroll_velocity))
        new_y = current_y + (target_y - current_y) * 0.45
        self.tree.yview_moveto(new_y)
        self._scroll_velocity *= 0.72
        if abs(self._scroll_velocity) > 0.001:
            self.after(8, self._smooth_scroll_step)
        else:
            self._scroll_velocity = 0.0
            self._is_smooth_scrolling = False

    def _on_tree_motion(self, event):
        iid = self.tree.identify_row(event.y)
        old_iid = getattr(self, "_hovered_iid", None)
        if iid == old_iid:
            return
        self._hovered_iid = iid
        if old_iid and old_iid in self.items_by_iid and old_iid not in self.tree.selection():
            self._restore_row_tags(old_iid)
        if iid and iid in self.items_by_iid and iid not in self.tree.selection():
            tags = list(self.tree.item(iid, "tags"))
            if "tag_hover" not in tags:
                tags.append("tag_hover")
                self.tree.item(iid, tags=tags)

    def _on_tree_leave(self, event=None):
        old_iid = getattr(self, "_hovered_iid", None)
        self._hovered_iid = None
        if old_iid and old_iid in self.items_by_iid and old_iid not in self.tree.selection():
            self._restore_row_tags(old_iid)

    def _restore_row_tags(self, iid: str):
        item = self.items_by_iid.get(iid)
        if not item:
            return
        tag = self._get_item_tag(item)
        self.tree.item(iid, tags=(tag,))

    def _get_item_tag(self, item: ProgramItem, idx: int = 0) -> str:
        if item.installed_version in ("Not Installed", "None", None, ""):
            return "tag_catalog"
        if item.outcome in (UpdateOutcome.UPDATED, UpdateOutcome.SIMULATED):
            return "tag_uptodate" if (idx % 2 == 0) else "tag_uptodate_alt"
        if item.outcome == UpdateOutcome.FAILED:
            return "tag_incompat"
        if item.action == UpdateAction.AVAILABLE:
            return "tag_available"
        if item.action == UpdateAction.UP_TO_DATE:
            return "tag_uptodate" if (idx % 2 == 0) else "tag_uptodate_alt"
        if item.action == UpdateAction.UNVERIFIED:
            return "tag_unverified"
        if item.action == UpdateAction.SCAN_FAILED:
            return "tag_incompat"
        if item.action == UpdateAction.EXCLUDED:
            return "tag_ignored"
        if item.action == UpdateAction.NEWER_THAN_SOURCE:
            return "tag_downgrade"
        if item.action == UpdateAction.VENDOR_FALLBACK:
            return "tag_fallback"
        return "tag_nosource" if (idx % 2 == 0) else "tag_nosource_alt"

    def populate(self, items: List[ProgramItem], chunk_size: int = 50) -> None:
        """Progressive chunked population preventing UI hitches on 300+ item inventories."""
        self.hide_skeleton()
        self._current_generation += 1
        gen_id = self._current_generation

        self.tree.delete(*self.tree.get_children())
        self.items_by_iid.clear()

        total = len(items)
        if total == 0:
            if self.on_select_item:
                self.on_select_item(None)
            return

        def _insert_chunk(start_idx: int):
            if gen_id != self._current_generation:
                return

            end_idx = min(start_idx + chunk_size, total)
            for idx in range(start_idx, end_idx):
                item = items[idx]
                iid = f"item_{idx}"
                self.items_by_iid[iid] = item

                # Determine badge string and color tag
                if item.installed_version in ("Not Installed", "None", None, ""):
                    status_str = "Ready to install"
                    tag = "tag_catalog"
                elif item.outcome == UpdateOutcome.UPDATED:
                    status_str = "Updated"
                    tag = "tag_uptodate"
                elif item.outcome == UpdateOutcome.SIMULATED:
                    status_str = "Simulated"
                    tag = "tag_uptodate"
                elif item.outcome == UpdateOutcome.FAILED:
                    status_str = "Failed"
                    tag = "tag_incompat"
                elif item.action == UpdateAction.AVAILABLE:
                    status_str = "Update available"
                    tag = "tag_available"
                elif item.action == UpdateAction.UP_TO_DATE:
                    status_str = "Up to date"
                    tag = "tag_uptodate" if (idx % 2 == 0) else "tag_uptodate_alt"
                elif item.action == UpdateAction.UNVERIFIED:
                    status_str = "Could not verify"
                    tag = "tag_unverified"
                elif item.action == UpdateAction.SCAN_FAILED:
                    status_str = "Scan failed"
                    tag = "tag_incompat"
                elif item.action == UpdateAction.EXCLUDED:
                    status_str = "Excluded"
                    tag = "tag_ignored"
                elif item.action == UpdateAction.NEWER_THAN_SOURCE:
                    status_str = "Newer than source"
                    tag = "tag_downgrade"
                elif item.action == UpdateAction.VENDOR_FALLBACK:
                    status_str = "Vendor fallback"
                    tag = "tag_fallback"
                elif item.action == UpdateAction.NO_SOURCE:
                    status_str = "Listed Only"
                    tag = "tag_nosource" if (idx % 2 == 0) else "tag_nosource_alt"
                else:
                    status_str = "Listed Only" if item.action.value == "No update source" else item.action.value
                    tag = "tag_nosource" if (idx % 2 == 0) else "tag_nosource_alt"

                values = (
                    item.installed_version or "Unknown",
                    item.latest_version or "—",
                    status_str,
                )
                icon = AppIconGenerator.get_icon(self.tree, item.name)
                try:
                    if icon:
                        self.tree.insert("", tk.END, iid=iid, text="  " + item.name, image=icon, values=values, tags=(tag,))
                    else:
                        self.tree.insert("", tk.END, iid=iid, text="  " + item.name, values=values, tags=(tag,))
                except Exception:
                    self.tree.insert("", tk.END, iid=iid, text="  " + item.name, values=values, tags=(tag,))

            if end_idx < total:
                self.after(6, lambda: _insert_chunk(end_idx))
            else:
                if self.on_select_item:
                    self.on_select_item(None)

        _insert_chunk(0)

    def update_item(self, item: ProgramItem) -> None:
        """Updates the tree row values and status badge for a single program item in-place."""
        for iid, existing in self.items_by_iid.items():
            if existing is item or (existing.name == item.name and existing.id == item.id):
                if item.outcome == UpdateOutcome.UPDATED:
                    status_str = "Updated"
                    tag = "tag_uptodate"
                elif item.outcome == UpdateOutcome.SIMULATED:
                    status_str = "Simulated"
                    tag = "tag_uptodate"
                elif item.outcome == UpdateOutcome.FAILED:
                    status_str = "Failed"
                    tag = "tag_incompat"
                elif item.action == UpdateAction.AVAILABLE:
                    status_str = "Update available"
                    tag = "tag_available"
                elif item.action == UpdateAction.UP_TO_DATE:
                    status_str = "Up to date"
                    tag = "tag_uptodate"
                elif item.action == UpdateAction.UNVERIFIED:
                    status_str = "Could not verify"
                    tag = "tag_unverified"
                elif item.action == UpdateAction.SCAN_FAILED:
                    status_str = "Scan failed"
                    tag = "tag_incompat"
                elif item.action == UpdateAction.EXCLUDED:
                    status_str = "Excluded"
                    tag = "tag_ignored"
                elif item.action == UpdateAction.NEWER_THAN_SOURCE:
                    status_str = "Newer than source"
                    tag = "tag_downgrade"
                elif item.action == UpdateAction.VENDOR_FALLBACK:
                    status_str = "Vendor fallback"
                    tag = "tag_fallback"
                elif item.action == UpdateAction.NO_SOURCE:
                    status_str = "No update source"
                    tag = "tag_nosource"
                else:
                    status_str = item.action.value
                    tag = "tag_nosource"

                icon = AppIconGenerator.get_icon(self.tree, item.name)
                values = (
                    item.installed_version or "Unknown",
                    item.latest_version or "—",
                    status_str,
                )
                try:
                    self.tree.item(iid, text="  " + item.name, image=icon, values=values, tags=(tag,))
                except Exception:
                    pass
                break

    def get_selected_items(self) -> List[ProgramItem]:
        """Returns all currently selected ProgramItem models."""
        sel = self.tree.selection()
        return [self.items_by_iid[i] for i in sel if i in self.items_by_iid]

    def _get_selected_item(self) -> Optional[ProgramItem]:
        sel = self.tree.selection()
        if not sel:
            return None
        return self.items_by_iid.get(sel[0])

    def _handle_select(self, event=None) -> None:
        sel = self.tree.selection()
        if not sel:
            if self.on_select_item:
                self.on_select_item(None)
            if self.on_batch_select:
                self.on_batch_select([])
            return

        selected_items = [self.items_by_iid[iid] for iid in sel if iid in self.items_by_iid]
        if len(selected_items) == 1:
            if self.on_select_item:
                self.on_select_item(selected_items[0])
            if self.on_batch_select:
                self.on_batch_select([])
        else:
            if self.on_select_item:
                self.on_select_item(None)
            if self.on_batch_select:
                self.on_batch_select(selected_items)

    def select_all(self) -> None:
        """Selects all items currently displayed in the table."""
        all_iids = self.tree.get_children("")
        self.tree.selection_set(all_iids)
        self._handle_select()

    def select_updates_only(self) -> None:
        """Selects only items that have verified updates ready."""
        u_iids = [
            iid for iid, it in self.items_by_iid.items()
            if it.can_auto_update() or (it.action == UpdateAction.AVAILABLE and it.is_verified_winget)
        ]
        if u_iids:
            self.tree.selection_set(u_iids)
            self._handle_select()

    def select_unverified_only(self) -> None:
        """Selects only items marked as could not verify or ambiguous."""
        unver_iids = [
            iid for iid, it in self.items_by_iid.items()
            if it.action == UpdateAction.UNVERIFIED
        ]
        if unver_iids:
            self.tree.selection_set(unver_iids)
            self._handle_select()

    def clear_selection(self) -> None:
        """Clears all table row selections."""
        self.tree.selection_set(())
        self._handle_select()

    def _handle_double_click(self, event) -> None:
        item = self._get_selected_item()
        if item and self.on_double_click:
            self.on_double_click(item)

    def _show_context_menu(self, event) -> None:
        iid = self.tree.identify_row(event.y)
        if not iid:
            return

        current_sel = self.tree.selection()
        if iid not in current_sel:
            self.tree.selection_set(iid)
            self._handle_select(None)

        self._build_context_menu()
        self.context_menu.post(event.x_root, event.y_root)

    def _build_context_menu(self) -> None:
        """Dynamically populates context menu based on whether single or multiple items are selected."""
        self.context_menu.delete(0, tk.END)
        items = self.get_selected_items()
        if not items:
            return

        if len(items) == 1:
            item = items[0]
            # Primary action
            if item.action == UpdateAction.UNVERIFIED:
                self.context_menu.add_command(
                    label="⚡ Review & Allow Update",
                    command=self._menu_allow_unverified,
                    font=("Segoe UI", 9, "bold"),
                )
            elif item.action == UpdateAction.AVAILABLE:
                self.context_menu.add_command(
                    label="🚀 Update This Application",
                    command=self._menu_update_single,
                    font=("Segoe UI", 9, "bold"),
                )
            else:
                self.context_menu.add_command(
                    label="🔍 View Application Details",
                    command=self._menu_view_details,
                    font=("Segoe UI", 9, "bold"),
                )

            self.context_menu.add_separator()
            self.context_menu.add_command(label="🔗 Bind Winget ID...", command=self._menu_bind_source)

            # Pin / Unpin
            if item.is_pinned:
                self.context_menu.add_command(label="📌 Unpin Application", command=self._menu_pin)
            else:
                self.context_menu.add_command(label=f"📌 Pin to {item.installed_version}", command=self._menu_pin)

            # Skip / Unskip
            if item.action == UpdateAction.AVAILABLE and item.latest_version:
                self.context_menu.add_command(label=f"⏭️ Skip Release {item.latest_version}", command=self._menu_skip)
            elif item.action == UpdateAction.SKIPPED_VERSION:
                self.context_menu.add_command(label="⏭️ Unskip Release", command=self._menu_skip)

            self.context_menu.add_command(label="🌐 Visit Official Website", command=self._menu_open_website)
            self.context_menu.add_separator()
            self.context_menu.add_command(label="📂 Open Installation Folder", command=self._menu_open_folder)
            self.context_menu.add_command(label="📋 Copy Package Identifier", command=self._menu_copy_info)
            self.context_menu.add_command(label="🛡️ Exclude from Updates", command=self._menu_exclude)
            self.context_menu.add_separator()
            self.context_menu.add_command(label="🗑️ Uninstall Application", command=self._menu_uninstall)
        else:
            # Multi-selection batch operations
            up_items = [it for it in items if it.can_auto_update() or (it.action == UpdateAction.AVAILABLE and it.is_verified_winget)]
            unver_items = [it for it in items if it.action == UpdateAction.UNVERIFIED]

            if up_items:
                self.context_menu.add_command(
                    label=f"🚀 Update Selected ({len(up_items)} updates)",
                    command=self._menu_batch_update,
                    font=("Segoe UI", 9, "bold"),
                )
            if unver_items:
                self.context_menu.add_command(
                    label=f"⚡ Approve Selected Unverified ({len(unver_items)} packages)",
                    command=self._menu_batch_allow,
                    font=("Segoe UI", 9, "bold"),
                )
            self.context_menu.add_command(
                label=f"📌 Pin Selected ({len(items)} packages)",
                command=self._menu_batch_pin,
            )
            self.context_menu.add_command(
                label=f"🛡️ Exclude Selected ({len(items)} packages)",
                command=self._menu_batch_exclude,
            )
            self.context_menu.add_separator()
            self.context_menu.add_command(label="✕ Deselect All", command=self.clear_selection)

    def _menu_view_details(self) -> None:
        item = self._get_selected_item()
        if item and self.on_double_click:
            self.on_double_click(item)

    def _menu_update_single(self) -> None:
        item = self._get_selected_item()
        if item and self.on_single_update:
            self.on_single_update(item)

    def _menu_allow_unverified(self) -> None:
        item = self._get_selected_item()
        if item and self.on_allow_unverified:
            self.on_allow_unverified(item)

    def _menu_bind_source(self) -> None:
        item = self._get_selected_item()
        if item and self.on_bind_source:
            self.on_bind_source(item)

    def _menu_pin(self) -> None:
        item = self._get_selected_item()
        if item and self.on_pin_item:
            self.on_pin_item(item)

    def _menu_skip(self) -> None:
        item = self._get_selected_item()
        if item and self.on_skip_version:
            self.on_skip_version(item)

    def _menu_open_website(self) -> None:
        item = self._get_selected_item()
        if item and self.on_open_website:
            self.on_open_website(item)

    def _menu_exclude(self) -> None:
        item = self._get_selected_item()
        if item and self.on_exclude_item:
            self.on_exclude_item(item)

    def _menu_open_folder(self) -> None:
        item = self._get_selected_item()
        if not item or not item.install_location:
            if self.on_toast_message:
                self.on_toast_message("No registered install directory", "info")
            return
        loc = item.install_location
        if os.path.exists(loc):
            try:
                os.startfile(loc)
            except Exception:
                pass
        else:
            if self.on_toast_message:
                self.on_toast_message(f"Directory not found: {loc}", "warning")

    def _menu_copy_info(self) -> None:
        item = self._get_selected_item()
        if not item:
            return
        info = f"{item.name} | ID: {item.id or 'N/A'} | Version: {item.installed_version}"
        self.clipboard_clear()
        self.clipboard_append(info)
        if self.on_toast_message:
            self.on_toast_message(f"Copied package ID: {item.name}", "info")

    def _menu_uninstall(self) -> None:
        item = self._get_selected_item()
        if item and self.on_uninstall_item:
            self.on_uninstall_item(item)

    def _menu_batch_update(self) -> None:
        items = [it for it in self.get_selected_items() if it.can_auto_update() or (it.action == UpdateAction.AVAILABLE and it.is_verified_winget)]
        if items and self.on_batch_update:
            self.on_batch_update(items)

    def _menu_batch_allow(self) -> None:
        items = [it for it in self.get_selected_items() if it.action == UpdateAction.UNVERIFIED]
        if items and self.on_batch_allow:
            self.on_batch_allow(items)

    def _menu_batch_pin(self) -> None:
        items = self.get_selected_items()
        if items and self.on_batch_pin:
            self.on_batch_pin(items)

    def _menu_batch_exclude(self) -> None:
        items = self.get_selected_items()
        if items and self.on_batch_exclude:
            self.on_batch_exclude(items)

    def _sort_column(self, col: str, reverse: bool) -> None:
        if col in ("name", "#0"):
            l = [(self.tree.item(k, "text").strip().lower(), k) for k in self.tree.get_children("")]
        else:
            l = [(str(self.tree.set(k, col)).lower(), k) for k in self.tree.get_children("")]
        l.sort(reverse=reverse)
        for index, (_, k) in enumerate(l):
            self.tree.move(k, "", index)
        self.tree.heading(col, command=lambda: self._sort_column(col, not reverse))


class FloatingGlassBatchDock(tk.Frame):
    """Frosted Glass Action Dock that slides in at the bottom when multiple applications are selected."""

    def __init__(
        self,
        parent: tk.Widget,
        on_batch_update: Optional[Callable[[List[ProgramItem]], None]] = None,
        on_batch_allow: Optional[Callable[[List[ProgramItem]], None]] = None,
        on_batch_pin: Optional[Callable[[List[ProgramItem]], None]] = None,
        on_batch_exclude: Optional[Callable[[List[ProgramItem]], None]] = None,
        on_clear_selection: Optional[Callable[[], None]] = None,
    ):
        super().__init__(
            parent,
            bg="#faf6f6",
            padx=18,
            pady=10,
            highlightbackground="#f3d5d9",
            highlightthickness=1,
        )
        self.on_batch_update = on_batch_update
        self.on_batch_allow = on_batch_allow
        self.on_batch_pin = on_batch_pin
        self.on_batch_exclude = on_batch_exclude
        self.on_clear_selection = on_clear_selection
        self.selected_items: List[ProgramItem] = []
        self.theme: ThemeColors = DREAM_THEME

        # Left Info Stack
        self.info_stack = tk.Frame(self, bg="#faf6f6")
        self.info_stack.pack(side=tk.LEFT, fill=tk.Y)

        self.lbl_title = tk.Label(
            self.info_stack,
            text="0 Applications Selected",
            bg="#faf6f6",
            fg="#881337",
            font=("Segoe UI", 10, "bold"),
            anchor="w",
        )
        self.lbl_title.pack(anchor=tk.W)

        self.lbl_sub = tk.Label(
            self.info_stack,
            text="",
            bg="#faf6f6",
            fg="#64748b",
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.lbl_sub.pack(anchor=tk.W, pady=(1, 0))

        # Right Action Buttons
        self.btn_box = tk.Frame(self, bg="#faf6f6")
        self.btn_box.pack(side=tk.RIGHT)

        self.btn_update = RoundedButton(
            self.btn_box,
            text="Update Selected",
            command=self._on_update_clicked,
            bg_color="#881337",
            fg_color="#ffffff",
            hover_bg="#9f1239",
            radius=8,
            font=("Segoe UI", 9, "bold"),
            height=32,
            padding=(14, 6),
            parent_bg="#faf6f6",
        )
        self.btn_update.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_allow = RoundedButton(
            self.btn_box,
            text="⚡ Approve Unverified",
            command=self._on_allow_clicked,
            bg_color="#fef3c7",
            fg_color="#92400e",
            hover_bg="#fde68a",
            border_color="#fcd34d",
            radius=8,
            font=("Segoe UI", 8, "bold"),
            height=32,
            padding=(10, 6),
            parent_bg="#faf6f6",
        )

        self.btn_pin = RoundedButton(
            self.btn_box,
            text="📌 Pin",
            command=self._on_pin_clicked,
            bg_color="#ffffff",
            fg_color="#334155",
            hover_bg="#fff1f2",
            border_color="#e2e8f0",
            radius=8,
            font=("Segoe UI", 8),
            height=32,
            padding=(10, 6),
            parent_bg="#faf6f6",
        )
        self.btn_pin.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_clear = RoundedButton(
            self.btn_box,
            text="✕ Deselect",
            command=self._on_clear_clicked,
            bg_color="#ffffff",
            fg_color="#64748b",
            hover_bg="#f1f5f9",
            border_color="#e2e8f0",
            radius=8,
            font=("Segoe UI", 8),
            height=32,
            padding=(8, 6),
            parent_bg="#faf6f6",
        )
        self.btn_clear.pack(side=tk.LEFT)

    def set_selected_items(self, items: List[ProgramItem]) -> None:
        """Configures dock counts and enables batch actions based on selected models."""
        self.selected_items = items
        total = len(items)
        if total == 0:
            return

        up_items = [it for it in items if it.can_auto_update() or (it.action == UpdateAction.AVAILABLE and it.is_verified_winget)]
        unver_items = [it for it in items if it.action == UpdateAction.UNVERIFIED]
        upto_date = [it for it in items if it.action == UpdateAction.UP_TO_DATE]

        self.lbl_title.config(text=f"📦 {total} Applications Selected")
        sub_parts = []
        if up_items:
            sub_parts.append(f"{len(up_items)} verified updates")
        if unver_items:
            sub_parts.append(f"{len(unver_items)} unverified")
        if upto_date:
            sub_parts.append(f"{len(upto_date)} up to date")
        self.lbl_sub.config(text="  •  ".join(sub_parts) if sub_parts else "Multiple selections active")

        if up_items:
            self.btn_update.config(state="normal", text=f"🚀 Update Selected ({len(up_items)})", bg="#881337", fg="#ffffff")
        else:
            self.btn_update.config(state="disabled", text="Update Selected", bg="#f1f5f9", fg="#94a3b8")

        if unver_items:
            self.btn_allow.pack(side=tk.LEFT, padx=(0, 6))
            self.btn_allow.config(state="normal", text=f"⚡ Approve ({len(unver_items)})")
        else:
            self.btn_allow.pack_forget()

        all_pinned = all(it.is_pinned for it in items)
        self.btn_pin.config(text=f"Unpin ({total})" if all_pinned else f"📌 Pin ({total})")

    def _on_update_clicked(self) -> None:
        if self.on_batch_update and self.selected_items:
            up_items = [it for it in self.selected_items if it.can_auto_update() or (it.action == UpdateAction.AVAILABLE and it.is_verified_winget)]
            if up_items:
                self.on_batch_update(up_items)

    def _on_allow_clicked(self) -> None:
        if self.on_batch_allow and self.selected_items:
            unver_items = [it for it in self.selected_items if it.action == UpdateAction.UNVERIFIED]
            if unver_items:
                self.on_batch_allow(unver_items)

    def _on_pin_clicked(self) -> None:
        if self.on_batch_pin and self.selected_items:
            self.on_batch_pin(self.selected_items)

    def _on_clear_clicked(self) -> None:
        if self.on_clear_selection:
            self.on_clear_selection()

    def _on_details_resize(self, event: tk.Event) -> None:
        """Dynamically adjust diagnostic wraplength so text never clips or overflows."""
        if hasattr(self, "lbl_diag_text"):
            new_wrap = max(220, event.width - 36)
            self.lbl_diag_text.config(wraplength=new_wrap)

    def apply_theme(self, theme: ThemeColors) -> None:
        self.theme = theme
        bg_col = theme.bg_sidebar
        border_col = theme.border
        self.config(bg=bg_col, highlightbackground=border_col)
        self.info_stack.config(bg=bg_col)
        self.btn_box.config(bg=bg_col)
        self.lbl_title.config(bg=bg_col, fg=theme.accent_burgundy)
        self.lbl_sub.config(bg=bg_col, fg=theme.fg_muted)



# --- Legacy / Backwards-Compatibility Component Aliases ---
class ElevationBanner(tk.Frame):
    def __init__(self, parent: tk.Widget, sys_info=None, on_toggle_theme: Optional[Callable[[], None]] = None):
        super().__init__(parent, bg="#ffffff", padx=16, pady=6, highlightbackground="#f3d5d9", highlightthickness=1)
        self.sys_info = sys_info
        self.on_toggle_theme = on_toggle_theme
        self.theme: ThemeColors = DREAM_THEME
        self.pack(fill=tk.X)

        self.lbl_logo = tk.Label(self, text="Software & Package Updater", font=("Segoe UI", 11, "bold"), bg="#ffffff", fg="#881337")
        self.lbl_logo.pack(side=tk.LEFT)

        self.btn_theme = tk.Button(self, text="Dark mode", command=self._on_click, font=("Segoe UI", 8, "bold"), bg="#faf6f6", fg="#1e293b", relief=tk.FLAT, bd=0, padx=8, pady=3, cursor="hand2")
        self.btn_theme.pack(side=tk.RIGHT)

    def _on_click(self):
        if self.on_toggle_theme:
            self.on_toggle_theme()

    def apply_theme(self, theme: ThemeColors):
        self.theme = theme
        self.config(bg=theme.bg_header, highlightbackground=theme.border)
        self.lbl_logo.config(bg=theme.bg_header, fg=theme.accent_burgundy)
        txt = "Light mode" if theme.name == "dark" else "Dark mode"
        self.btn_theme.config(text=txt, bg=theme.bg_button, fg=theme.fg_primary)


class StatCard(tk.Frame):
    def __init__(self, parent, tag_num, title, subtitle, accent_color, filter_name, on_click, icon_type="cpu"):
        super().__init__(parent, bg="#10182b")
        self.title = title
        self.lbl = tk.Label(self, text=title, bg="#ffffff", fg="#0f172a")
        self.lbl.pack()

    def set_value(self, val: int):
        pass

    def apply_theme(self, theme):
        self.config(bg=theme.bg_card)


class StatCardDeck(tk.Frame):
    def __init__(self, parent, on_select_filter):
        super().__init__(parent, bg="#fafafa")
        self.on_select_filter = on_select_filter

    def update_metrics(self, **kwargs):
        pass

    def apply_theme(self, theme):
        self.config(bg=theme.bg_card)


class SearchFilterBar(tk.Frame):
    def __init__(self, parent, on_filter_change, on_export_click=None):
        super().__init__(parent, bg="#fafafa")
        self.on_filter_change = on_filter_change

    def get_search_query(self) -> str:
        return ""

    def get_selected_category(self) -> str:
        return "All Categories"

    def apply_theme(self, theme):
        pass


class LiveWarningBar(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#fafafa")

    def show_warning(self, msg):
        pass

    def hide_warning(self):
        pass

    def apply_theme(self, theme):
        pass


class InspectorPane(DetailsDrawer):
    """Backwards compatibility alias for DetailsDrawer."""
    pass


class AppUpdateNotificationBanner(tk.Frame):
    """Modern notification banner surfaced when a newer version of Winget Updater is available on GitHub."""

    def __init__(
        self,
        parent: tk.Widget,
        on_download_click: Optional[Callable[[str], None]] = None,
        on_dismiss_click: Optional[Callable[[], None]] = None,
    ):
        super().__init__(
            parent,
            bg="#fdf2f8",
            highlightbackground="#fbcfe8",
            highlightthickness=1,
            padx=14,
            pady=8,
        )
        self.on_download_click = on_download_click
        self.on_dismiss_click = on_dismiss_click
        self.current_download_url = ""
        self.latest_version = ""

        # Left Column: Badge & Details
        self.left_col = tk.Frame(self, bg="#fdf2f8")
        self.left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.title_row = tk.Frame(self.left_col, bg="#fdf2f8")
        self.title_row.pack(anchor="w")

        self.lbl_badge = RoundedPillBadge(
            self.title_row,
            text="APP UPDATE AVAILABLE",
            bg_color="#fce7f3",
            fg_color="#9d174d",
            radius=6,
            font=("Segoe UI", 8, "bold"),
            height=20,
            parent_bg="#fdf2f8",
        )
        self.lbl_badge.pack(side=tk.LEFT, padx=(0, 8))

        self.lbl_headline = tk.Label(
            self.title_row,
            text="A new release of Winget Updater is ready",
            bg="#fdf2f8",
            fg="#831843",
            font=("Segoe UI", 9, "bold"),
        )
        self.lbl_headline.pack(side=tk.LEFT)

        self.lbl_desc = tk.Label(
            self.left_col,
            text="Click Update Now to view release notes and download the verified executable.",
            bg="#fdf2f8",
            fg="#9d174d",
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.lbl_desc.pack(anchor="w", pady=(2, 0))

        # Right Column: Action Deck
        self.right_col = tk.Frame(self, bg="#fdf2f8")
        self.right_col.pack(side=tk.RIGHT, fill=tk.Y)

        self.btn_download = RoundedButton(
            self.right_col,
            text="⚡ Update Now",
            width=115,
            height=28,
            bg_color="#881337",
            fg_color="#ffffff",
            hover_bg="#9f1239",
            radius=8,
            font=("Segoe UI", 8, "bold"),
            command=self._handle_download,
            parent_bg="#fdf2f8",
        )
        self.btn_download.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_dismiss = RoundedButton(
            self.right_col,
            text="✕ Dismiss",
            width=76,
            height=28,
            bg_color="#fce7f3",
            fg_color="#831843",
            hover_bg="#fbcfe8",
            radius=8,
            font=("Segoe UI", 8),
            command=self._handle_dismiss,
            parent_bg="#fdf2f8",
        )
        self.btn_dismiss.pack(side=tk.LEFT)

    def set_update_info(self, version: str, download_url: str):
        self.latest_version = version
        self.current_download_url = download_url
        self.lbl_headline.config(text=f"A new release of Winget Updater is ready: v{version}")

    def _handle_download(self):
        if self.on_download_click:
            self.on_download_click(self.current_download_url)
        else:
            import webbrowser
            url = self.current_download_url or "https://github.com/rupom787/winget-updater/releases/latest"
            webbrowser.open(url)

    def _handle_dismiss(self):
        self.pack_forget()
        if self.on_dismiss_click:
            self.on_dismiss_click()

    def apply_theme(self, theme):
        is_dark = getattr(theme, "is_dark", False)
        bg = "#2a1215" if is_dark else "#fdf2f8"
        border = "#4c1d24" if is_dark else "#fbcfe8"
        text_fg = "#fce7f3" if is_dark else "#831843"
        desc_fg = "#f472b6" if is_dark else "#9d174d"

        self.config(bg=bg, highlightbackground=border)
        self.left_col.config(bg=bg)
        self.title_row.config(bg=bg)
        self.right_col.config(bg=bg)
        self.lbl_headline.config(bg=bg, fg=text_fg)
        self.lbl_desc.config(bg=bg, fg=desc_fg)
