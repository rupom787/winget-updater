"""Ultra-smooth Software Engineering vector illustrations, Lottie-style animated canvas scenes, timelines, and shaders for Windows 11."""

import math
import random
import threading
import time
import tkinter as tk
from typing import Callable, Dict, List, Optional, Tuple
from winget_updater.gui.theme import DARK_THEME, LIGHT_THEME, ThemeColors


class SoftwareEngineeringHeroScene(tk.Canvas):
    """Lottie-style animated Software Engineering vector canvas scene.
    
    Features:
    - Left: Developer Terminal & Laptop with animated live typing code streams and blinking cursor.
    - Center: Dual mathematical meshing compiler gears (cogs) rotating in sync + circuit traces.
    - Center-Right: Floating binary/code particles (0, 1, {}, <>) drifting upwards.
    - Right: Radar sweep scanner with rotating beam and detected software blips.
    - Far-Right: Isometric 3D software deployment package cube with glowing energy wings.
    - Reactive animation speeds and modes (idle, scanning, updating, complete).
    - Multi-Theme: Adapts seamlessly between Dark Industrial and Light Industrial modes.
    """

    def __init__(self, parent: tk.Widget, height: int = 120, bg: str = "#07090e"):
        super().__init__(parent, height=height, bg=bg, highlightthickness=0, bd=0)
        self.height = height
        self.theme: ThemeColors = DARK_THEME
        self.gear_angle = 0.0
        self.radar_angle = 0.0
        self.mode = "idle"  # idle, scanning, updating, complete
        self.code_step = 0
        self.cursor_blink = True
        self.blink_timer = 0
        self.is_animating = False

        # Code lines for terminal typing
        self.code_lines = [
            "> winget.query(local_hives)",
            "> sha256_authenticode: PASS",
            "> ring0_privileges: ACTIVE",
            "> repo_sync: verified_manifest",
            "> memory_heap: optimal (60fps)",
        ]

        # Floating binary particles
        self.particles: List[Dict] = []
        for _ in range(16):
            self.particles.append({
                "x": random.uniform(340, 720),
                "y": random.uniform(20, height - 15),
                "speed": random.uniform(0.4, 1.2),
                "char": random.choice(["0", "1", "{}", "<>", "/*", "*/", "01", "10"]),
                "alpha_color": random.choice(["#1e293b", "#334155", "#0e7490", "#0284c7"]),
            })

        self.bind("<Configure>", lambda e: self._render())
        self.is_animating = False
        self._render()

    def apply_theme(self, theme: ThemeColors) -> None:
        """Adapts the entire hero vector scene to the specified theme."""
        self.theme = theme
        self.config(bg=theme.bg_canvas)
        particle_cols = (
            ["#cbd5e1", "#94a3b8", "#0284c7", "#0369a1"]
            if theme.name == "light"
            else ["#1e293b", "#334155", "#0e7490", "#0284c7"]
        )
        for p in self.particles:
            p["alpha_color"] = random.choice(particle_cols)
        self._render()

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        if mode in ("scanning", "updating"):
            self.start()
        elif mode == "complete":
            self.after(3500, lambda: self.set_mode("idle"))
        elif mode == "idle":
            self.stop()

    def start(self) -> None:
        if not self.is_animating:
            self.is_animating = True
            self._tick()

    def stop(self) -> None:
        self.is_animating = False

    def _tick(self) -> None:
        if not self.is_animating:
            return
        if not self.winfo_ismapped():
            # If the widget is hidden / unmapped, do not burn CPU compositing
            self.after(300, self._tick)
            return

        # Speed multipliers based on operational state
        speed_mult = 3.2 if self.mode == "scanning" else (4.0 if self.mode == "updating" else 1.0)

        # Rotate gears
        self.gear_angle = (self.gear_angle + 0.035 * speed_mult) % (2 * math.pi)

        # Rotate radar scanner
        self.radar_angle = (self.radar_angle + 0.05 * speed_mult) % (2 * math.pi)

        # Update floating particles
        for p in self.particles:
            p["y"] -= p["speed"] * (1.8 if self.mode == "scanning" else 1.0)
            if p["y"] < 10:
                p["y"] = self.height - 10
                p["x"] = random.uniform(340, min(740, self.winfo_width() - 200))

        # Update terminal typing
        self.blink_timer += 1
        if self.blink_timer % 16 == 0:
            self.cursor_blink = not self.cursor_blink
        if self.blink_timer % int(max(4, 14 // speed_mult)) == 0:
            self.code_step += 1

        self._render()
        self.after(25, self._tick)

    def _get_gear_points(self, cx: float, cy: float, r_in: float, r_out: float, teeth: int, offset: float) -> List[float]:
        pts = []
        tot = teeth * 4
        for i in range(tot):
            ang = offset + i * (2 * math.pi / tot)
            r = r_out if (i % 4 in (1, 2)) else r_in
            pts.extend([cx + r * math.cos(ang), cy + r * math.sin(ang)])
        return pts

    def _render(self) -> None:
        self.delete("all")
        w = self.winfo_width() or 1000
        h = self.height
        is_light = (self.theme.name == "light")

        # 1. Subtle Background Blueprint Grid
        grid_col = self.theme.grid_line
        for x in range(0, w, 32):
            self.create_line(x, 0, x, h, fill=grid_col, width=1)
        for y in range(0, h, 24):
            self.create_line(0, y, w, y, fill=grid_col, width=1)

        # 2. Left Section: Developer Terminal / Laptop Vector Illustration
        laptop_x = 20
        laptop_w = min(290, int(w * 0.28))
        if laptop_w > 180:
            bezel_bg = "#e2e8f0" if is_light else "#121622"
            title_bg = "#cbd5e1" if is_light else "#181d2c"
            glass_bg = "#f8fafc" if is_light else "#080a0f"
            border_col = self.theme.border

            # Screen Bezel
            self.create_rectangle(laptop_x, 14, laptop_x + laptop_w, h - 22, fill=bezel_bg, outline=border_col, width=1)
            # Title Bar
            self.create_rectangle(laptop_x, 14, laptop_x + laptop_w, 32, fill=title_bg, outline="")
            # Window Dots
            self.create_oval(laptop_x + 8, 20, laptop_x + 14, 26, fill="#ef4444", outline="")
            self.create_oval(laptop_x + 18, 20, laptop_x + 24, 26, fill="#f59e0b", outline="")
            self.create_oval(laptop_x + 28, 20, laptop_x + 34, 26, fill="#10b981", outline="")
            self.create_text(laptop_x + 42, 23, text="terminal // winget.engine", fill=self.theme.fg_muted, font=("Cascadia Code", 7), anchor="w")

            # Terminal Display Glass
            self.create_rectangle(laptop_x + 4, 34, laptop_x + laptop_w - 4, h - 26, fill=glass_bg, outline="")

            # Animated Typing Code Streams
            num_lines = len(self.code_lines)
            line_idx = (self.code_step // 20) % num_lines
            partial_len = (self.code_step % 20) * 2

            y_pos = 46
            for idx in range(3):
                cur_line_i = (line_idx + idx) % num_lines
                text_content = self.code_lines[cur_line_i]
                if idx == 0:
                    shown_text = text_content[:partial_len]
                    if self.cursor_blink:
                        shown_text += " █"
                    text_col = self.theme.accent_cyan
                else:
                    shown_text = text_content
                    text_col = self.theme.fg_primary if is_light else ("#38bdf8" if idx == 1 else "#334155")

                self.create_text(laptop_x + 10, y_pos, text=shown_text, fill=text_col, font=("Cascadia Code", 8, "bold"), anchor="w")
                y_pos += 16

            # Laptop Base Stand
            base_bg = "#cbd5e1" if is_light else "#181e2b"
            pad_bg = "#94a3b8" if is_light else "#252d40"
            self.create_polygon(
                laptop_x - 12, h - 14,
                laptop_x + laptop_w + 12, h - 14,
                laptop_x + laptop_w + 4, h - 22,
                laptop_x - 4, h - 22,
                fill=base_bg,
                outline=border_col,
            )
            self.create_rectangle(laptop_x + (laptop_w // 2) - 20, h - 14, laptop_x + (laptop_w // 2) + 20, h - 10, fill=pad_bg, outline="")

        # 3. Center Section: Circuit Traces & Floating Particles
        for p in self.particles:
            if p["x"] < w - 60:
                self.create_text(p["x"], p["y"], text=p["char"], fill=p["alpha_color"], font=("Cascadia Code", 8, "bold"))

        # Circuit connector lines
        mid_x = min(510, int(w * 0.48))
        if mid_x > 320:
            self.create_line(laptop_x + laptop_w, 55, mid_x - 40, 55, fill=self.theme.border_subtle, width=1.5)
            self.create_oval(mid_x - 44, 52, mid_x - 36, 58, fill=self.theme.accent_cyan, outline="")

        # 4. Center Meshing Compiler Gears (Cogs)
        gear1_x = min(540, int(w * 0.52))
        gear1_y = 60
        gear2_x = gear1_x + 56
        gear2_y = 48
        gear_fill = "#f1f5f9" if is_light else "#111622"

        if w > 650:
            # Gear 1 (Primary 10-tooth)
            g1_pts = self._get_gear_points(gear1_x, gear1_y, 18, 30, 10, self.gear_angle)
            g1_col = self.theme.accent_emerald if self.mode == "updating" else self.theme.accent_cyan
            self.create_polygon(g1_pts, fill=gear_fill, outline=g1_col, width=1.5)
            self.create_oval(gear1_x - 8, gear1_y - 8, gear1_x + 8, gear1_y + 8, fill=g1_col, outline="")

            # Gear 2 (Secondary 7-tooth meshing)
            gear2_angle = -self.gear_angle * (10.0 / 7.0) + (math.pi / 7.0)
            g2_pts = self._get_gear_points(gear2_x, gear2_y, 11, 19, 7, gear2_angle)
            g2_col = self.theme.accent_emerald if self.mode == "updating" else (self.theme.accent_cyan if is_light else "#38bdf8")
            self.create_polygon(g2_pts, fill=gear_fill, outline=g2_col, width=1.5)
            self.create_oval(gear2_x - 5, gear2_y - 5, gear2_x + 5, gear2_y + 5, fill=g2_col, outline="")

        # 5. Right Section: Radar Scanner
        radar_x = min(820, int(w * 0.78))
        radar_y = 60
        radar_r = 38
        if w > 820:
            # Radar concentric rings
            self.create_oval(radar_x - radar_r, radar_y - radar_r, radar_x + radar_r, radar_y + radar_r, outline=self.theme.border, width=1)
            self.create_oval(radar_x - (radar_r * 0.6), radar_y - (radar_r * 0.6), radar_x + (radar_r * 0.6), radar_y + (radar_r * 0.6), outline=self.theme.border_subtle, width=1)
            self.create_line(radar_x - radar_r, radar_y, radar_x + radar_r, radar_y, fill=self.theme.border_subtle, width=1)
            self.create_line(radar_x, radar_y - radar_r, radar_x, radar_y + radar_r, fill=self.theme.border_subtle, width=1)

            # Rotating Radar Sweep Beam
            beam_tip_x = radar_x + radar_r * math.cos(self.radar_angle)
            beam_tip_y = radar_y + radar_r * math.sin(self.radar_angle)
            self.create_line(radar_x, radar_y, beam_tip_x, beam_tip_y, fill=self.theme.accent_cyan, width=2)

            # Detected Target Blips
            blips = [
                (radar_x + 18, radar_y - 12),
                (radar_x - 14, radar_y + 16),
                (radar_x + 8, radar_y + 24),
            ]
            for bx, by in blips:
                self.create_oval(bx - 3, by - 3, bx + 3, by + 3, fill=self.theme.accent_emerald, outline="")

            self.create_text(radar_x, radar_y + radar_r + 12, text="RADAR // SWEEP", fill=self.theme.fg_muted, font=("Cascadia Code", 7, "bold"))

        # 6. Far-Right Section: 3D Isometric Software Package Deployment Cube
        cube_x = min(980, w - 80)
        cube_y = 60
        cube_s = 22
        if w > 960:
            ang_30 = math.pi / 6.0
            dx = cube_s * math.cos(ang_30)
            dy = cube_s * math.sin(ang_30)

            top_fill = "#e2e8f0" if is_light else "#1e293b"
            left_fill = "#cbd5e1" if is_light else "#0f172a"
            right_fill = "#f1f5f9" if is_light else "#182234"
            cube_outline = self.theme.accent_cyan

            # Top Face
            top_pts = [cube_x, cube_y - cube_s, cube_x + dx, cube_y - dy, cube_x, cube_y, cube_x - dx, cube_y - dy]
            self.create_polygon(top_pts, fill=top_fill, outline=cube_outline, width=1.5)

            # Left Face
            left_pts = [cube_x - dx, cube_y - dy, cube_x, cube_y, cube_x, cube_y + cube_s, cube_x - dx, cube_y + cube_s - dy]
            self.create_polygon(left_pts, fill=left_fill, outline=cube_outline, width=1.5)

            # Right Face
            right_pts = [cube_x, cube_y, cube_x + dx, cube_y - dy, cube_x + dx, cube_y + cube_s - dy, cube_x, cube_y + cube_s]
            self.create_polygon(right_pts, fill=right_fill, outline=cube_outline, width=1.5)

            # Glowing Package Arrow / Energy Wing
            self.create_line(cube_x, cube_y - 8, cube_x, cube_y + 8, fill=self.theme.accent_cyan, width=2)
            self.create_polygon(cube_x - 5, cube_y - 2, cube_x + 5, cube_y - 2, cube_x, cube_y - 8, fill=self.theme.accent_cyan, outline="")

            cube_label = "DEPLOY // OK" if self.mode == "complete" else "PACKAGE // REPO"
            self.create_text(cube_x, cube_y + cube_s + 14, text=cube_label, fill=self.theme.accent_cyan if self.mode == "complete" else self.theme.fg_muted, font=("Cascadia Code", 7, "bold"))


class TimelinePipelineHUD(tk.Canvas):
    """Vecteezy-style animation software timeline HUD displaying multi-stage pipeline status with animated scrubber."""

    STAGES = [
        ("01", "SUBSYSTEM DISCOVERY"),
        ("02", "REPO SYNC & MATCH"),
        ("03", "KERNEL COMPAT AUDIT"),
        ("04", "RING-0 DEPLOYMENT"),
    ]

    def __init__(self, parent: tk.Widget, height: int = 34, bg: str = "#090b10"):
        super().__init__(parent, height=height, bg=bg, highlightthickness=0, bd=0)
        self.height = height
        self.theme: ThemeColors = DARK_THEME
        self.current_stage = 0  # 0 to 4
        self.scrubber_x = 0.0
        self.target_scrubber_x = 0.0
        self.is_animating = False
        self.bind("<Configure>", lambda e: self._render())
        self.start()

    def apply_theme(self, theme: ThemeColors) -> None:
        """Applies theme colors dynamically to the timeline pipeline."""
        self.theme = theme
        self.config(bg=theme.bg_root)
        self._render()

    def set_stage(self, stage_idx: int) -> None:
        self.current_stage = max(0, min(len(self.STAGES), stage_idx))
        w = self.winfo_width() or 1000
        step_w = w / len(self.STAGES)
        self.target_scrubber_x = self.current_stage * step_w

    def start(self) -> None:
        if not self.is_animating:
            self.is_animating = True
            self._tick()

    def _tick(self) -> None:
        if not self.is_animating:
            return

        diff = self.target_scrubber_x - self.scrubber_x
        self.scrubber_x += diff * 0.18
        if abs(diff) < 0.2:
            self.scrubber_x = self.target_scrubber_x

        self._render()
        self.after(25, self._tick)

    def _render(self) -> None:
        self.delete("all")
        w = self.winfo_width() or 1000
        h = self.height

        # Base Track
        self.create_line(20, h // 2, w - 20, h // 2, fill=self.theme.border_subtle, width=2)

        # Active Completed Track
        if self.scrubber_x > 20:
            self.create_line(20, h // 2, min(w - 20, self.scrubber_x), h // 2, fill=self.theme.accent_cyan, width=2)

        # Stage Nodes
        num = len(self.STAGES)
        for idx, (num_str, title) in enumerate(self.STAGES):
            node_x = 40 + idx * ((w - 80) / max(1, num - 1))
            node_y = h // 2

            is_done = self.scrubber_x >= node_x - 5
            is_active = (idx == self.current_stage - 1) or (self.current_stage == 0 and idx == 0)

            node_col = self.theme.accent_cyan if is_done else (self.theme.accent_cyan if is_active else self.theme.border)
            node_fill = self.theme.bg_card if not is_done else self.theme.accent_cyan

            # Keyframe diamond marker
            d = 5
            self.create_polygon(
                node_x, node_y - d,
                node_x + d, node_y,
                node_x, node_y + d,
                node_x - d, node_y,
                fill=node_fill,
                outline=node_col,
                width=1.5,
            )

            # Stage label
            lbl_col = self.theme.fg_primary if is_done else (self.theme.accent_cyan if is_active else self.theme.fg_muted)
            self.create_text(node_x, node_y + 11, text=f"[{num_str}] {title}", fill=lbl_col, font=("Cascadia Code", 7, "bold"))

        # Animated Playhead / Scrubber Cursor
        cur_x = max(20, min(w - 20, self.scrubber_x))
        self.create_oval(cur_x - 5, (h // 2) - 5, cur_x + 5, (h // 2) + 5, fill=self.theme.fg_primary, outline=self.theme.accent_cyan, width=1.5)


class CyberLaserHeaderCanvas(tk.Canvas):
    """Sleek 4px cyber laser line divider with a traveling particle beam pulse."""

    def __init__(self, parent: tk.Widget, height: int = 4, bg: str = "#090b10"):
        super().__init__(parent, height=height, bg=bg, highlightthickness=0, bd=0)
        self.height = height
        self.theme: ThemeColors = DARK_THEME
        self.beam_x = 0.0
        self.mode = "idle"  # idle, scanning, updating
        self.is_animating = False
        self.bind("<Configure>", lambda e: self._render())
        self._render()

    def apply_theme(self, theme: ThemeColors) -> None:
        self.theme = theme
        self.config(bg=theme.bg_root)
        self._render()

    def set_mode(self, mode: str) -> None:
        self.mode = mode
        if mode in ("scanning", "updating"):
            self.start()
        elif mode == "idle":
            self.stop()

    def start(self) -> None:
        if not self.is_animating:
            self.is_animating = True
            self._tick()

    def stop(self) -> None:
        self.is_animating = False

    def _tick(self) -> None:
        if not self.is_animating:
            return
        if not self.winfo_ismapped():
            self.after(300, self._tick)
            return
        speed = 12.0 if self.mode == "scanning" else (18.0 if self.mode == "updating" else 4.0)
        w = self.winfo_width() or 1000
        self.beam_x = (self.beam_x + speed) % (w + 100)
        self._render()
        self.after(30, self._tick)

    def _render(self) -> None:
        self.delete("all")
        w = self.winfo_width() or 1000
        h = self.height
        # Dark laser channel
        self.create_line(0, h // 2, w, h // 2, fill=self.theme.border_subtle, width=2)
        # Traveling neon laser beam
        color = self.theme.accent_emerald if self.mode == "updating" else self.theme.accent_cyan
        glow_color = "#047857" if self.mode == "updating" else ("#7dd3fc" if self.theme.name == "light" else "#0284c7")
        bx = self.beam_x
        beam_len = 120
        self.create_line(bx - beam_len, h // 2, bx, h // 2, fill=glow_color, width=3)
        self.create_line(bx - (beam_len // 2), h // 2, bx, h // 2, fill=color, width=2)
        self.create_oval(bx - 3, (h // 2) - 2, bx + 3, (h // 2) + 2, fill=self.theme.fg_primary, outline=color)


class VectorIconDrawer:
    """Helper to draw crisp vector iconography for software engineering KPI cards."""

    @staticmethod
    def draw_cpu_chip(canvas: tk.Canvas, cx: int, cy: int, size: int = 14, is_light: bool = False) -> None:
        """Draws a vector microchip / CPU die with circuit pins."""
        canvas.delete("all")
        bg_col = "#f1f5f9" if is_light else "#121824"
        out_col = "#0284c7" if is_light else "#38bdf8"
        core_col = "#0284c7"
        canvas.create_rectangle(cx - size, cy - size, cx + size, cy + size, fill=bg_col, outline=out_col, width=1.5)
        canvas.create_rectangle(cx - (size // 2), cy - (size // 2), cx + (size // 2), cy + (size // 2), fill=core_col, outline="")
        for off in (-8, 0, 8):
            canvas.create_line(cx + off, cy - size, cx + off, cy - size - 4, fill=out_col, width=1.5)
            canvas.create_line(cx + off, cy + size, cx + off, cy + size + 4, fill=out_col, width=1.5)
            canvas.create_line(cx - size, cy + off, cx - size - 4, cy + off, fill=out_col, width=1.5)
            canvas.create_line(cx + size, cy + off, cx + size + 4, cy + off, fill=out_col, width=1.5)

    @staticmethod
    def draw_rocket_box(canvas: tk.Canvas, cx: int, cy: int, size: int = 14, is_light: bool = False) -> None:
        """Draws a vector software package box with upward deployment rocket arrow."""
        canvas.delete("all")
        bg_col = "#dcfce7" if is_light else "#064e3b"
        out_col = "#059669" if is_light else "#10b981"
        arr_col = "#059669" if is_light else "#34d399"
        canvas.create_rectangle(cx - size, cy - size + 4, cx + size, cy + size, fill=bg_col, outline=out_col, width=1.5)
        canvas.create_line(cx, cy + size - 2, cx, cy - size + 6, fill=arr_col, width=2)
        canvas.create_polygon(cx - 5, cy - size + 8, cx + 5, cy - size + 8, cx, cy - size + 2, fill=arr_col, outline="")

    @staticmethod
    def draw_shield_check(canvas: tk.Canvas, cx: int, cy: int, size: int = 14, is_light: bool = False) -> None:
        """Draws a vector digital security shield with verified checkmark."""
        canvas.delete("all")
        bg_col = "#e0f2fe" if is_light else "#0c4a6e"
        out_col = "#0284c7" if is_light else "#38bdf8"
        chk_col = "#0284c7" if is_light else "#ffffff"
        pts = [
            cx, cy - size,
            cx + size, cy - size + 4,
            cx + size, cy + 2,
            cx, cy + size + 2,
            cx - size, cy + 2,
            cx - size, cy - size + 4,
        ]
        canvas.create_polygon(pts, fill=bg_col, outline=out_col, width=1.5)
        canvas.create_line(cx - 5, cy, cx - 1, cy + 4, fill=chk_col, width=2)
        canvas.create_line(cx - 1, cy + 4, cx + 5, cy - 3, fill=chk_col, width=2)

    @staticmethod
    def draw_storage_drive(canvas: tk.Canvas, cx: int, cy: int, size: int = 14, is_light: bool = False) -> None:
        """Draws a vector local cylinder disk / database storage."""
        canvas.delete("all")
        bg_col = "#f1f5f9" if is_light else "#1e293b"
        out_col = "#64748b" if is_light else "#94a3b8"
        led_col = "#0284c7" if is_light else "#38bdf8"
        canvas.create_oval(cx - size, cy - size, cx + size, cy - size + 8, fill=bg_col, outline=out_col, width=1.5)
        canvas.create_rectangle(cx - size, cy - size + 4, cx + size, cy + size - 4, fill=bg_col, outline="")
        canvas.create_line(cx - size, cy - size + 4, cx - size, cy + size - 4, fill=out_col, width=1.5)
        canvas.create_line(cx + size, cy - size + 4, cx + size, cy + size - 4, fill=out_col, width=1.5)
        canvas.create_oval(cx - size, cy + size - 8, cx + size, cy + size, fill=bg_col, outline=out_col, width=1.5)
        canvas.create_oval(cx + 4, cy, cx + 7, cy + 3, fill=led_col, outline="")

    @staticmethod
    def draw_gpu_module(canvas: tk.Canvas, cx: int, cy: int, size: int = 14, is_light: bool = False) -> None:
        """Draws a vector GPU / hardware extension card with fans."""
        canvas.delete("all")
        bg_col = "#f3e8ff" if is_light else "#2e1065"
        out_col = "#9333ea" if is_light else "#c084fc"
        canvas.create_rectangle(cx - size, cy - size + 2, cx + size, cy + size - 2, fill=bg_col, outline=out_col, width=1.5)
        canvas.create_oval(cx - 6, cy - 6, cx + 6, cy + 6, outline=out_col, width=1)
        canvas.create_line(cx - 4, cy - 4, cx + 4, cy + 4, fill=out_col, width=1.5)
        canvas.create_line(cx - 4, cy + 4, cx + 4, cy - 4, fill=out_col, width=1.5)


class DeckCounterAnimator:
    """Coordinates a synchronized, smooth count-up animation across all stat cards without overloading the event loop."""

    @classmethod
    def animate_deck(
        cls,
        parent: tk.Widget,
        targets: Dict[str, int],
        update_fn: Callable[[Dict[str, int]], None],
        duration_ms: int = 400,
        total_frames: int = 16,
    ) -> None:
        def _step(frame: int):
            if frame >= total_frames:
                update_fn(targets)
                return

            t = frame / total_frames
            ease = 1.0 - pow(1.0 - t, 3)

            current_values = {
                key: int(round(val * ease)) for key, val in targets.items()
            }
            update_fn(current_values)

            delay = max(16, duration_ms // total_frames)
            try:
                parent.after(delay, lambda: _step(frame + 1))
            except Exception:
                update_fn(targets)

        _step(1)


class PulsingWarningBeacon:
    """Animates a gentle pulsing alert color transition on the elevation warning bar during active updates."""

    PULSE_COLORS = [
        "#2d1804",
        "#3d2208",
        "#4a2a0a",
        "#3d2208",
        "#2d1804",
        "#0e121a",
    ]

    def __init__(self, target_widget: tk.Widget):
        self.widget = target_widget
        self.is_pulsing = False
        self.color_idx = 0

    def start(self) -> None:
        if self.is_pulsing:
            return
        self.is_pulsing = True
        self._step()

    def stop(self, final_bg: str = "#0e121a") -> None:
        self.is_pulsing = False
        try:
            self.widget.config(bg=final_bg)
        except Exception:
            pass

    def _step(self) -> None:
        if not self.is_pulsing:
            return
        color = self.PULSE_COLORS[self.color_idx]
        self.color_idx = (self.color_idx + 1) % len(self.PULSE_COLORS)
        try:
            self.widget.config(bg=color)
            self.widget.after(140, self._step)
        except Exception:
            self.is_pulsing = False


class ScanningPulseAnimator:
    """Subtle pulsing braille spinner indicator for status during background inventory scanning."""

    FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, label_widget: tk.Label, base_text: str = "Scanning"):
        self.label = label_widget
        self.base_text = base_text
        self.is_active = False
        self.frame_idx = 0

    def start(self, text: Optional[str] = None) -> None:
        if text:
            self.base_text = text
        if self.is_active:
            return
        self.is_active = True
        self._tick()

    def update_text(self, text: str) -> None:
        self.base_text = text

    def stop(self, final_text: Optional[str] = None) -> None:
        self.is_active = False
        if final_text is not None:
            try:
                self.label.config(text=final_text)
            except Exception:
                pass

    def _tick(self) -> None:
        if not self.is_active:
            return
        spinner = self.FRAMES[self.frame_idx]
        self.frame_idx = (self.frame_idx + 1) % len(self.FRAMES)
        try:
            self.label.config(text=f"{spinner}  {self.base_text}", fg="#00f0ff")
            self.label.after(80, self._tick)
        except Exception:
            self.is_active = False


class ToastNotificationHelper:
    """Non-blocking inline toast feedback banner that auto-reverts after duration."""

    @staticmethod
    def show_toast(
        target_label: tk.Label,
        message: str,
        duration_ms: int = 2500,
        original_text: Optional[str] = None,
        toast_fg: str = "#00f0ff",
    ) -> None:
        prev_text = original_text if original_text is not None else target_label.cget("text")
        prev_fg = target_label.cget("fg")

        target_label.config(text=message, fg=toast_fg)

        def _revert():
            try:
                target_label.config(text=prev_text, fg=prev_fg)
            except Exception:
                pass

        target_label.after(duration_ms, _revert)


class FluentFloatingToast(tk.Frame):
    """Floating spring-animated modern glass pill notification that drops from top and auto-dismisses."""

    @classmethod
    def show(
        cls,
        root: tk.Tk,
        text: str,
        icon: str = "✓",
        bg: str = "#0b0f17",
        fg: str = "#f8fafc",
        border_col: str = "#00f0ff",
        icon_fg: str = "#00f0ff",
        duration_ms: int = 2800,
    ) -> None:
        toast = cls(root, text=text, icon=icon, bg=bg, fg=fg, border_col=border_col, icon_fg=icon_fg)
        toast.animate_in_and_out(duration_ms=duration_ms)

    def __init__(self, root: tk.Tk, text: str, icon: str, bg: str, fg: str, border_col: str = "#00f0ff", icon_fg: str = "#00f0ff"):
        super().__init__(root, bg=bg, padx=18, pady=9, relief=tk.SOLID, borderwidth=1, highlightbackground=border_col, highlightthickness=1)
        self.root = root
        self.y_pos = -60
        self.target_y = 16

        lbl_icon = tk.Label(self, text=icon, bg=bg, fg=icon_fg, font=("Segoe UI Emoji", 11, "bold"))
        lbl_icon.pack(side=tk.LEFT, padx=(0, 10))

        lbl_text = tk.Label(self, text=text, bg=bg, fg=fg, font=("Cascadia Code", 8, "bold"))
        lbl_text.pack(side=tk.LEFT)

    def animate_in_and_out(self, duration_ms: int = 2800):
        self.place(relx=0.5, y=self.y_pos, anchor="n")

        def _slide_in(step: int, total_steps: int = 12):
            if step >= total_steps:
                self.place(relx=0.5, y=self.target_y, anchor="n")
                self.after(duration_ms, _slide_out)
                return

            t = step / total_steps
            ease = 1.0 - math.cos(t * math.pi / 2.0)
            self.y_pos = int(-60 + (self.target_y + 60) * ease)
            self.place(relx=0.5, y=self.y_pos, anchor="n")
            self.after(16, lambda: _slide_in(step + 1))

        def _slide_out(step: int = 0, total_steps: int = 10):
            if step >= total_steps:
                try:
                    self.destroy()
                except Exception:
                    pass
                return

            t = step / total_steps
            ease = t * t
            cur_y = int(self.target_y - 80 * ease)
            try:
                self.place(relx=0.5, y=cur_y, anchor="n")
                self.after(16, lambda: _slide_out(step + 1))
            except Exception:
                pass

        _slide_in(1)


class AnimatedSkeletonOverlay(tk.Frame):
    """Modern dark industrial shimmering skeleton screen displaying animated light-sweeps during discovery."""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent, bg="#0c0e14")
        self.theme: ThemeColors = DARK_THEME
        self.canvas = tk.Canvas(self, bg="#0c0e14", highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.shimmer_x = -150
        self.is_shimmering = False
        self.bind("<Configure>", lambda e: self._draw_skeletons())

    def apply_theme(self, theme: ThemeColors) -> None:
        self.theme = theme
        self.config(bg=theme.bg_table)
        self.canvas.config(bg=theme.bg_table)
        self._draw_skeletons()

    def start_shimmer(self) -> None:
        self.is_shimmering = True
        self.shimmer_x = -150
        self._tick()

    def stop_shimmer(self) -> None:
        self.is_shimmering = False

    def _tick(self) -> None:
        if not self.is_shimmering:
            return
        if not self.winfo_ismapped():
            self.after(300, self._tick)
            return
        w = self.winfo_width() or 800
        self.shimmer_x += 16
        if self.shimmer_x > w + 200:
            self.shimmer_x = -180

        self._draw_skeletons()
        self.after(30, self._tick)

    def _draw_skeletons(self) -> None:
        self.canvas.delete("all")
        w = self.winfo_width() or 800
        h = self.winfo_height() or 400
        is_light = (self.theme.name == "light")

        self.canvas.create_text(
            30, 24,
            text="[SOFTWARE ENGINEERING HUD] // RECURSIVE DISCOVERY ACROSS REGISTRY, STORE, DRIVERS & EXTENSIONS...",
            fill=self.theme.accent_cyan,
            font=("Cascadia Code", 8, "bold"),
            anchor="w",
        )

        row_y = 56
        row_h = 34
        for i in range(10):
            if row_y > h - 20:
                break
            bg_col = self.theme.bg_table if i % 2 == 0 else self.theme.bg_table_alt
            box_fill = "#e2e8f0" if is_light else "#1e2433"
            self.canvas.create_rectangle(15, row_y, w - 15, row_y + row_h - 4, fill=bg_col, outline=self.theme.border_subtle)

            self.canvas.create_rectangle(30, row_y + 8, 48, row_y + 24, fill=box_fill, outline="")
            self.canvas.create_rectangle(56, row_y + 10, min(260, w - 220), row_y + 22, fill=box_fill, outline="")

            if w > 450:
                self.canvas.create_rectangle(290, row_y + 10, 360, row_y + 22, fill=box_fill, outline="")

            if w > 600:
                self.canvas.create_rectangle(400, row_y + 10, 460, row_y + 22, fill=box_fill, outline="")

            if w > 750:
                self.canvas.create_rectangle(500, row_y + 8, 620, row_y + 24, fill=box_fill, outline="")

            row_y += row_h

        beam_w = 140
        self.canvas.create_rectangle(
            self.shimmer_x, 48,
            self.shimmer_x + beam_w, min(h, row_y),
            fill=self.theme.accent_cyan,
            stipple="gray25",
            outline="",
        )


class SmoothLerpProgressBar(tk.Canvas):
    """Custom high-performance canvas progress bar with lerp interpolation and animated light bead."""

    def __init__(self, parent: tk.Widget, width: int = 240, height: int = 18):
        super().__init__(parent, width=width, height=height, bg="#0d1017", highlightthickness=1, highlightbackground="#1e2433", bd=0)
        self.bar_width = width
        self.bar_height = height
        self.theme: ThemeColors = DARK_THEME
        self.current_val = 0.0
        self.target_val = 0.0
        self.light_pos = 0.0
        self.is_running = False
        self._render()

    def apply_theme(self, theme: ThemeColors) -> None:
        self.theme = theme
        self.config(bg=theme.bg_root, highlightbackground=theme.border)
        self._render()

    def set_progress(self, target: float) -> None:
        self.target_val = max(0.0, min(100.0, float(target)))
        if not self.is_running and abs(self.target_val - self.current_val) > 0.05:
            self.is_running = True
            self._tick()

    def _tick(self) -> None:
        diff = self.target_val - self.current_val
        self.current_val += diff * 0.18
        if abs(diff) < 0.2:
            self.current_val = self.target_val

        self.light_pos = (self.light_pos + 4) % (self.bar_width + 40)
        self._render()

        if self.is_running and abs(self.target_val - self.current_val) > 0.1:
            self.after(25, self._tick)
        else:
            self.is_running = False

    def _render(self) -> None:
        self.delete("all")
        w = self.winfo_width() or self.bar_width
        h = self.bar_height

        self.create_rectangle(0, 0, w, h, fill=self.theme.bg_input, outline="")

        fill_w = int((self.current_val / 100.0) * w)
        if fill_w > 0:
            fill_col = self.theme.accent_emerald if self.current_val >= 99.5 else self.theme.accent_cyan
            self.create_rectangle(0, 0, fill_w, h, fill=fill_col, outline="")

            if self.light_pos < fill_w:
                self.create_rectangle(
                    max(0, self.light_pos - 15), 0,
                    min(fill_w, self.light_pos + 15), h,
                    fill="#ffffff",
                    outline="",
                )

        pct_text = f"{int(round(self.current_val))}%"
        txt_col = "#ffffff" if fill_w > (w / 2) else self.theme.fg_primary
        self.create_text(w // 2, h // 2, text=pct_text, fill=txt_col, font=("Cascadia Code", 8, "bold"))


class GlassyTelemetryHUD(tk.Frame):
    """3 Distinct Frosted Glass Telemetry Pills matching Windows 11 Acrylic Glass Table mockup."""

    def __init__(self, parent: tk.Widget, sys_info=None, gpu_name: str = "DirectX 12", **kwargs):
        super().__init__(
            parent,
            bg="#0c1220",
            highlightthickness=0,
            **kwargs,
        )
        self.sys_info = sys_info
        self.gpu_name = gpu_name
        self.theme: ThemeColors = LIGHT_THEME
        self._pulse_phase = 0.0
        self._cpu_val = 0.0
        self._ram_str = "RAM: 58%"
        self._mode = "idle"  # "idle", "scanning", "updating"
        self._is_active = True

        # Pill 1: CPU
        self.pill_cpu = tk.Frame(self, bg="#16132a", padx=6, pady=3, highlightthickness=1, highlightbackground="#2e254c")
        self.pill_cpu.pack(side=tk.LEFT, padx=(0, 5))
        self.lbl_cpu_icon = tk.Label(self.pill_cpu, text="▣", font=("Segoe UI", 7), bg="#16132a", fg="#00f0ff")
        self.lbl_cpu_icon.pack(side=tk.LEFT, padx=(0, 3))
        self.lbl_cpu = tk.Label(self.pill_cpu, text="CPU: 0%", font=("Segoe UI", 8, "bold"), bg="#10182b", fg="#34d399")
        self.lbl_cpu.pack(side=tk.LEFT)

        # Pill 2: RAM
        self.pill_ram = tk.Frame(self, bg="#16132a", padx=6, pady=3, highlightthickness=1, highlightbackground="#2e254c")
        self.pill_ram.pack(side=tk.LEFT, padx=(0, 5))
        self.lbl_ram_icon = tk.Label(self.pill_ram, text="▣", font=("Segoe UI", 7), bg="#16132a", fg="#a855f7")
        self.lbl_ram_icon.pack(side=tk.LEFT, padx=(0, 3))
        self.lbl_ram = tk.Label(self.pill_ram, text="RAM: 48%", font=("Segoe UI", 8), bg="#10182b", fg="#f8fafc")
        self.lbl_ram.pack(side=tk.LEFT)

        # Pill 3: GPU & Status Beacon
        self.pill_gpu = tk.Frame(self, bg="#16132a", padx=6, pady=3, highlightthickness=1, highlightbackground="#2e254c")
        self.pill_gpu.pack(side=tk.LEFT)
        self.lbl_gpu_icon = tk.Label(self.pill_gpu, text="▣", font=("Segoe UI", 7), bg="#16132a", fg="#10b981")
        self.lbl_gpu_icon.pack(side=tk.LEFT, padx=(0, 3))
        gpu_short = gpu_name
        for prefix in ("NVIDIA ", "GeForce ", "AMD ", "Radeon ", "Intel ", "Graphics"):
            gpu_short = gpu_short.replace(prefix, "")
        gpu_short = gpu_short.strip()
        if len(gpu_short) > 12:
            gpu_short = gpu_short[:12].strip()
        self.lbl_gpu = tk.Label(self.pill_gpu, text=f"GPU: {gpu_short}", font=("Segoe UI", 8, "bold"), bg="#10182b", fg="#f8fafc")
        self.lbl_gpu.pack(side=tk.LEFT, padx=(0, 6))

        # Beacon dot canvas
        self.beacon = tk.Canvas(self.pill_gpu, width=12, height=12, bg="#10182b", highlightthickness=0)
        self.beacon.pack(side=tk.LEFT)

        # Retained dummy labels for backward compatibility
        self.lbl_sep1 = tk.Label(self, text="", bg="#0c1220")
        self.lbl_sep2 = tk.Label(self, text="", bg="#0c1220")

        self._start_telemetry_thread()
        self._render_idle_beacon()

    def set_mode(self, mode: str) -> None:
        """Sets beacon operating state: 'idle', 'scanning', 'updating'."""
        old_mode = self._mode
        self._mode = mode
        if mode in ("scanning", "updating") and old_mode not in ("scanning", "updating"):
            self._pulse_tick()
        elif mode == "idle":
            self._render_idle_beacon()

    def _render_idle_beacon(self) -> None:
        if not self.winfo_exists():
            return
        self.beacon.delete("all")
        mode = getattr(self.theme, "name", "light")
        if mode == "bloom":
            halo_col = "#fae8ff"
            core_col = "#d946ef"
        elif mode == "dark":
            halo_col = "#064e3b"
            core_col = "#10b981"
        else:
            halo_col = "#d1fae5"
            core_col = "#10b981"
        self.beacon.create_oval(1, 1, 11, 11, fill=halo_col, outline="")
        self.beacon.create_oval(3, 3, 9, 9, fill=core_col, outline="")

    def _pulse_tick(self) -> None:
        if not self._is_active or not self.winfo_exists():
            return
        if self._mode == "idle":
            self._render_idle_beacon()
            return

        speed = 0.22
        self._pulse_phase = (self._pulse_phase + speed) % (2 * math.pi)
        scale = (math.sin(self._pulse_phase) + 1.0) / 2.0

        if self._mode == "scanning":
            core_col = "#e11d48"
            halo_col = "#4c0519" if self.theme.name == "dark" else "#ffe4e6"
        else:
            core_col = "#fbbf24"
            halo_col = "#451a03" if self.theme.name == "dark" else "#fef3c7"

        halo_radius = 3.0 + scale * 2.5
        self.beacon.delete("all")
        self.beacon.create_oval(6 - halo_radius, 6 - halo_radius, 6 + halo_radius, 6 + halo_radius, fill=halo_col, outline="")
        self.beacon.create_oval(4, 4, 8, 8, fill=core_col, outline="")

        self.after(80, self._pulse_tick)

    def _start_telemetry_thread(self) -> None:
        if not self.sys_info:
            return

        def worker():
            while self._is_active:
                try:
                    cpu = self.sys_info.get_cpu_load_percent(sample_interval=0.1)
                    used_gb, total_gb, ram_pct = self.sys_info.get_memory_info()
                    ram_text = f"RAM: {ram_pct}%"

                    def update_ui(c=cpu, r=ram_text):
                        if not self.winfo_exists():
                            return
                        self._cpu_val = c
                        if c > 80:
                            cpu_col = "#dc2626"
                        elif c > 50:
                            cpu_col = "#d97706"
                        else:
                            cpu_col = "#34d399" if self.theme.name == "dark" else "#059669"
                        self.lbl_cpu.config(text=f"CPU: {int(round(c))}%", fg=cpu_col)
                        self.lbl_ram.config(text=r)

                    self.after(0, update_ui)
                except Exception:
                    pass
                time.sleep(3.0)

        threading.Thread(target=worker, daemon=True).start()

    def apply_theme(self, theme: ThemeColors) -> None:
        self.theme = theme
        card_bg = theme.bg_card
        border_col = theme.border
        header_bg = theme.bg_header
        self.config(bg=header_bg)

        for pill in (self.pill_cpu, self.pill_ram, self.pill_gpu):
            pill.config(bg=card_bg, highlightbackground=border_col)

        self.beacon.config(bg=card_bg)
        if self._mode == "idle":
            self._render_idle_beacon()

        self.lbl_cpu_icon.config(bg=card_bg, fg=theme.fg_muted)
        self.lbl_cpu.config(bg=card_bg, fg="#34d399" if theme.name == "dark" else "#059669")

        self.lbl_ram_icon.config(bg=card_bg, fg=theme.fg_muted)
        self.lbl_ram.config(bg=card_bg, fg=theme.fg_primary)

        self.lbl_gpu_icon.config(bg=card_bg, fg=theme.fg_muted)
        gpu_fg = "#00f0ff" if theme.name == "dark" else (theme.accent_burgundy if theme.name == "light" else "#a855f7")
        self.lbl_gpu.config(bg=card_bg, fg=gpu_fg)

    def destroy(self) -> None:
        self._is_active = False
        super().destroy()


class SmoothLerpProgressBar(tk.Canvas):
    """Custom high-performance canvas progress bar with lerp interpolation and animated light bead."""

    def __init__(self, parent: tk.Widget, width: int = 240, height: int = 18):
        super().__init__(parent, width=width, height=height, bg="#0d1017", highlightthickness=1, highlightbackground="#1e2433", bd=0)
        self.bar_width = width
        self.bar_height = height
        self.theme: ThemeColors = DARK_THEME
        self.current_val = 0.0
        self.target_val = 0.0
        self.light_pos = 0.0
        self.is_running = False
        self._render()

    def apply_theme(self, theme: ThemeColors) -> None:
        self.theme = theme
        self.config(bg=theme.bg_root, highlightbackground=theme.border)
        self._render()

    def set_progress(self, target: float) -> None:
        self.target_val = max(0.0, min(100.0, float(target)))
        if not self.is_running and abs(self.target_val - self.current_val) > 0.05:
            self.is_running = True
            self._tick()

    def _tick(self) -> None:
        diff = self.target_val - self.current_val
        self.current_val += diff * 0.18
        if abs(diff) < 0.2:
            self.current_val = self.target_val

        self.light_pos = (self.light_pos + 4) % (self.bar_width + 40)
        self._render()

        if self.is_running and abs(self.target_val - self.current_val) > 0.1:
            self.after(25, self._tick)
        else:
            self.is_running = False

    def _render(self) -> None:
        self.delete("all")
        w = self.winfo_width() or self.bar_width
        h = self.bar_height

        self.create_rectangle(0, 0, w, h, fill=self.theme.bg_input, outline="")

        fill_w = int((self.current_val / 100.0) * w)
        if fill_w > 0:
            fill_col = self.theme.accent_emerald if self.current_val >= 99.5 else self.theme.accent_cyan
            self.create_rectangle(0, 0, fill_w, h, fill=fill_col, outline="")

            if self.light_pos < fill_w:
                self.create_rectangle(
                    max(0, self.light_pos - 15), 0,
                    min(fill_w, self.light_pos + 15), h,
                    fill="#ffffff",
                    outline="",
                )

        pct_text = f"{int(round(self.current_val))}%"
        txt_col = "#ffffff" if fill_w > (w / 2) else self.theme.fg_primary
        self.create_text(w // 2, h // 2, text=pct_text, fill=txt_col, font=("Cascadia Code", 8, "bold"))
