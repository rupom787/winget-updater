"""Live update progress dialog with hardware-smooth 60 FPS animations, real-time stdout streaming, and queue tracking."""

import math
import queue
import time
import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional
from winget_updater.gui.theme import ThemeColors, get_theme
from winget_updater.models import ProgramItem, UpdateOutcome


class LiveUpdateProgressDialog(tk.Toplevel):
    """Modern, animated modal displaying real-time package update progress, 60 FPS canvas motion,
    live stdout streaming terminal, and queue status indicators.
    """

    def __init__(
        self,
        parent: tk.Tk,
        items: List[ProgramItem],
        theme: Optional[ThemeColors] = None,
        on_run_in_background: Optional[Callable[[], None]] = None,
        on_cancel_queue: Optional[Callable[[], None]] = None,
        on_complete_view_summary: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.parent = parent
        self.items = items
        self.theme = theme or get_theme("light")
        self.is_dark = getattr(self.theme, "name", "light") == "dark"
        self.on_run_in_background = on_run_in_background
        self.on_cancel_queue = on_cancel_queue
        self.on_complete_view_summary = on_complete_view_summary

        self.title("Software Stack Update Engine")
        self.resizable(False, False)
        self.transient(parent)

        # Modal sizing & positioning centered over parent
        self.dlg_width = 640
        self.dlg_height = 680
        self._center_over_parent()

        # Thread-safe message queue for UI events
        self.ui_queue: queue.Queue = queue.Queue()

        # State tracking
        self.total_count = len(items)
        self.completed_count = 0
        self.succeeded_count = 0
        self.failed_count = 0
        self.current_item: Optional[ProgramItem] = None
        self.is_finished = False
        self.cancel_requested = False
        self.is_minimized_background = False

        # Animation states
        self.start_time = time.time()
        self.last_tick_time = time.time()
        self.spinner_angle = 0.0
        self.current_progress_pct = 0.0
        self.target_progress_pct = 0.0
        self.shimmer_offset = 0.0
        self.checkmark_progress = 0.0
        self.active_phase_text = "Preparing update environment..."
        self.terminal_visible = True

        # Item checklist row widgets mapping
        self.item_row_widgets: Dict[str, Dict[str, tk.Widget]] = {}

        self._apply_styles()
        self._build_ui()

        # Intercept window close to perform Run in Background instead of killing process
        self.protocol("WM_DELETE_WINDOW", self.minimize_to_background)

        # Start non-blocking 60 FPS animation scheduler and UI event pump
        self.after(16, self._animation_tick)
        self.after(25, self._drain_ui_queue)

    def _center_over_parent(self) -> None:
        try:
            self.parent.update_idletasks()
            pw = self.parent.winfo_width()
            ph = self.parent.winfo_height()
            px = self.parent.winfo_rootx()
            py = self.parent.winfo_rooty()

            if pw <= 1 or ph <= 1:
                pw = self.winfo_screenwidth()
                ph = self.winfo_screenheight()
                px = 0
                py = 0

            x = max(20, px + (pw - self.dlg_width) // 2)
            y = max(20, py + (ph - self.dlg_height) // 2)
            self.geometry(f"{self.dlg_width}x{self.dlg_height}+{x}+{y}")
        except Exception:
            self.geometry(f"{self.dlg_width}x{self.dlg_height}+150+100")

    def _apply_styles(self) -> None:
        is_dark = self.is_dark
        self.c_bg = "#0f172a" if is_dark else "#ffffff"
        self.c_card_bg = "#1e293b" if is_dark else "#f8fafc"
        self.c_border = "#334155" if is_dark else "#e2e8f0"
        self.c_text_main = "#f8fafc" if is_dark else "#0f172a"
        self.c_text_muted = "#94a3b8" if is_dark else "#64748b"
        self.c_accent = "#881337" if not is_dark else "#9f1239"
        self.c_accent_light = "#f43f5e"
        self.c_success = "#059669"
        self.c_failed = "#dc2626"
        self.c_terminal_bg = "#070a13"
        self.c_terminal_fg = "#e2e8f0"

        self.configure(bg=self.c_bg)

    def _build_ui(self) -> None:
        # Top 60 FPS Fluid Canvas Header
        self.header_canvas = tk.Canvas(
            self,
            width=self.dlg_width,
            height=105,
            bg="#090d16" if self.is_dark else "#881337",
            highlightthickness=0,
        )
        self.header_canvas.pack(fill=tk.X)

        # Container Frame
        self.main_container = tk.Frame(self, bg=self.c_bg, padx=18, pady=12)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # 1. Overall Queue Progress & Metric Ribbon
        self.progress_meta_frame = tk.Frame(self.main_container, bg=self.c_bg)
        self.progress_meta_frame.pack(fill=tk.X, pady=(0, 4))

        self.lbl_queue_metric = tk.Label(
            self.progress_meta_frame,
            text=f"Queue Progress: 0 of {self.total_count} completed (0%)",
            bg=self.c_bg,
            fg=self.c_text_main,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        )
        self.lbl_queue_metric.pack(side=tk.LEFT)

        self.lbl_counts_badge = tk.Label(
            self.progress_meta_frame,
            text="0 succeeded • 0 failed",
            bg=self.c_bg,
            fg=self.c_text_muted,
            font=("Segoe UI", 9),
            anchor="e",
        )
        self.lbl_counts_badge.pack(side=tk.RIGHT)

        # Custom Canvas-drawn Smooth Progress Bar
        self.bar_canvas = tk.Canvas(
            self.main_container,
            width=self.dlg_width - 36,
            height=12,
            bg=self.c_border,
            highlightthickness=0,
        )
        self.bar_canvas.pack(fill=tk.X, pady=(0, 12))

        # 2. Spotlight Card for Current Active Package
        self.spotlight_card = tk.Frame(
            self.main_container,
            bg=self.c_card_bg,
            highlightbackground=self.c_border,
            highlightthickness=1,
            padx=14,
            pady=10,
        )
        self.spotlight_card.pack(fill=tk.X, pady=(0, 10))

        # Spotlight header row
        self.spot_header = tk.Frame(self.spotlight_card, bg=self.c_card_bg)
        self.spot_header.pack(fill=tk.X)

        self.lbl_source_badge = tk.Label(
            self.spot_header,
            text="QUEUE",
            bg=self.c_accent,
            fg="#ffffff",
            font=("Segoe UI", 7, "bold"),
            padx=6,
            pady=2,
        )
        self.lbl_source_badge.pack(side=tk.LEFT, padx=(0, 8))

        self.lbl_active_name = tk.Label(
            self.spot_header,
            text="Waiting for next package...",
            bg=self.c_card_bg,
            fg=self.c_text_main,
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        self.lbl_active_name.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.lbl_active_version = tk.Label(
            self.spot_header,
            text="—",
            bg="#e0f2fe" if not self.is_dark else "#075985",
            fg="#0369a1" if not self.is_dark else "#38bdf8",
            font=("Segoe UI", 8, "bold"),
            padx=6,
            pady=2,
        )
        self.lbl_active_version.pack(side=tk.RIGHT)

        # Spotlight phase row with live indicator
        self.spot_phase_row = tk.Frame(self.spotlight_card, bg=self.c_card_bg)
        self.spot_phase_row.pack(fill=tk.X, pady=(6, 0))

        self.lbl_active_phase = tk.Label(
            self.spot_phase_row,
            text="⚡ Initializing update pipeline...",
            bg=self.c_card_bg,
            fg=self.c_accent if not self.is_dark else "#38bdf8",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.lbl_active_phase.pack(side=tk.LEFT)

        # Indeterminate shimmering micro-bar on active card
        self.shimmer_canvas = tk.Canvas(
            self.spotlight_card,
            height=3,
            bg=self.c_border,
            highlightthickness=0,
        )
        self.shimmer_canvas.pack(fill=tk.X, pady=(6, 0))

        # 3. Middle Section: Package Queue Checklist (Scrollable)
        self.queue_frame_label = tk.Label(
            self.main_container,
            text="UPDATE QUEUE",
            bg=self.c_bg,
            fg=self.c_text_muted,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.queue_frame_label.pack(fill=tk.X, pady=(0, 2))

        self.queue_scroll_container = tk.Frame(
            self.main_container,
            bg=self.c_card_bg,
            highlightbackground=self.c_border,
            highlightthickness=1,
            height=140,
        )
        self.queue_scroll_container.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        self.queue_scroll_container.pack_propagate(False)

        self.queue_canvas = tk.Canvas(
            self.queue_scroll_container,
            bg=self.c_card_bg,
            highlightthickness=0,
        )
        self.queue_scrollbar = ttk.Scrollbar(
            self.queue_scroll_container,
            orient="vertical",
            command=self.queue_canvas.yview,
        )
        self.queue_items_frame = tk.Frame(self.queue_canvas, bg=self.c_card_bg)

        self.queue_canvas.create_window((0, 0), window=self.queue_items_frame, anchor="nw", tags="inner")
        self.queue_canvas.configure(xscrollincrement=1, yscrollcommand=self.queue_scrollbar.set)

        self.queue_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.queue_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.queue_items_frame.bind(
            "<Configure>",
            lambda e: self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all")),
        )
        self._populate_queue_checklist()

        # 4. Live Rolling Monospace Subprocess Terminal
        self.term_header_frame = tk.Frame(self.main_container, bg=self.c_bg)
        self.term_header_frame.pack(fill=tk.X, pady=(0, 2))

        self.lbl_terminal_title = tk.Label(
            self.term_header_frame,
            text="LIVE STREAM OUTPUT",
            bg=self.c_bg,
            fg=self.c_text_muted,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_terminal_title.pack(side=tk.LEFT)

        self.btn_toggle_terminal = tk.Button(
            self.term_header_frame,
            text="Terminal [ - ]",
            bg=self.c_bg,
            fg=self.c_text_muted,
            activebackground=self.c_bg,
            relief=tk.FLAT,
            font=("Segoe UI", 8),
            cursor="hand2",
            command=self._toggle_terminal_visibility,
        )
        self.btn_toggle_terminal.pack(side=tk.RIGHT)

        self.terminal_frame = tk.Frame(
            self.main_container,
            bg=self.c_terminal_bg,
            highlightbackground="#1e293b",
            highlightthickness=1,
            height=130,
        )
        self.terminal_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.terminal_frame.pack_propagate(False)

        self.terminal_text = tk.Text(
            self.terminal_frame,
            bg=self.c_terminal_bg,
            fg=self.c_terminal_fg,
            insertbackground="#ffffff",
            font=("Cascadia Code", 8),
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=8,
            pady=6,
        )
        self.term_scrollbar = ttk.Scrollbar(
            self.terminal_frame,
            orient="vertical",
            command=self.terminal_text.yview,
        )
        self.terminal_text.configure(yscrollcommand=self.term_scrollbar.set)
        self.terminal_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.term_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Syntax color tags for terminal lines
        self.terminal_text.tag_configure("info", foreground="#38bdf8")
        self.terminal_text.tag_configure("success", foreground="#34d399")
        self.terminal_text.tag_configure("warn", foreground="#fbbf24")
        self.terminal_text.tag_configure("error", foreground="#f87171")
        self.terminal_text.tag_configure("timestamp", foreground="#64748b")

        # 5. Bottom Action Controls
        self.action_bar = tk.Frame(self.main_container, bg=self.c_bg)
        self.action_bar.pack(fill=tk.X, pady=(2, 0))

        self.btn_background = tk.Button(
            self.action_bar,
            text="⬇ Run in Background",
            bg=self.c_card_bg,
            fg=self.c_text_main,
            activebackground=self.c_border,
            relief=tk.FLAT,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.minimize_to_background,
        )
        self.btn_background.pack(side=tk.LEFT)

        self.btn_cancel = tk.Button(
            self.action_bar,
            text="⏹ Cancel Queue",
            bg="#fef2f2" if not self.is_dark else "#450a0a",
            fg=self.c_failed if not self.is_dark else "#fca5a5",
            activebackground="#fee2e2",
            relief=tk.FLAT,
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=6,
            cursor="hand2",
            command=self._handle_cancel_click,
        )
        self.btn_cancel.pack(side=tk.RIGHT)

        self.btn_complete_view = tk.Button(
            self.action_bar,
            text="✓ View Summary & Close",
            bg=self.c_accent,
            fg="#ffffff",
            activebackground=self.c_accent_light,
            relief=tk.FLAT,
            font=("Segoe UI", 9, "bold"),
            padx=16,
            pady=6,
            cursor="hand2",
            command=self._handle_view_summary_click,
        )
        # Hidden until finished
        self.btn_complete_view.pack_forget()

    def _populate_queue_checklist(self) -> None:
        """Builds clean checklist rows for all queued packages."""
        for idx, item in enumerate(self.items):
            row = tk.Frame(self.queue_items_frame, bg=self.c_card_bg, pady=3, padx=8)
            row.pack(fill=tk.X, expand=True)

            lbl_num = tk.Label(
                row,
                text=f"{idx + 1}.",
                bg=self.c_card_bg,
                fg=self.c_text_muted,
                font=("Segoe UI", 8),
                width=3,
                anchor="w",
            )
            lbl_num.pack(side=tk.LEFT)

            lbl_name = tk.Label(
                row,
                text=item.name,
                bg=self.c_card_bg,
                fg=self.c_text_main,
                font=("Segoe UI", 9),
                anchor="w",
            )
            lbl_name.pack(side=tk.LEFT, fill=tk.X, expand=True)

            ver_text = f"{item.installed_version or '—'} → {item.latest_version or 'Latest'}"
            lbl_ver = tk.Label(
                row,
                text=ver_text,
                bg=self.c_card_bg,
                fg=self.c_text_muted,
                font=("Segoe UI", 8),
                anchor="e",
            )
            lbl_ver.pack(side=tk.LEFT, padx=8)

            lbl_status = tk.Label(
                row,
                text="⏳ Pending",
                bg=self.c_card_bg,
                fg=self.c_text_muted,
                font=("Segoe UI", 8, "bold"),
                anchor="e",
                width=14,
            )
            lbl_status.pack(side=tk.RIGHT)

            k = item.id or item.name
            self.item_row_widgets[k] = {
                "row": row,
                "name": lbl_name,
                "status": lbl_status,
                "ver": lbl_ver,
            }

    # --------------------------------------------------------------------------
    # Thread-Safe Event Dispatching (Called from Background Worker)
    # --------------------------------------------------------------------------

    def notify_package_started(self, item: ProgramItem, cur: int, tot: int) -> None:
        """Enqueues package start notification."""
        self.ui_queue.put(("ITEM_START", (item, cur, tot)))

    def notify_package_log(self, item: ProgramItem, line: str) -> None:
        """Enqueues real-time stdout line."""
        self.ui_queue.put(("ITEM_LOG", (item, line)))

    def notify_package_completed(self, item: ProgramItem, success: bool, message: str) -> None:
        """Enqueues package completion notification."""
        self.ui_queue.put(("ITEM_END", (item, success, message)))

    def notify_queue_finished(self, summary) -> None:
        """Enqueues all-done signal."""
        self.ui_queue.put(("QUEUE_DONE", summary))

    def _drain_ui_queue(self) -> None:
        """Pumps messages from the worker thread to the UI smoothly."""
        try:
            while not self.ui_queue.empty():
                msg_type, payload = self.ui_queue.get_nowait()
                if msg_type == "ITEM_START":
                    item, cur, tot = payload
                    self._on_ui_item_start(item, cur, tot)
                elif msg_type == "ITEM_LOG":
                    item, line = payload
                    self._on_ui_item_log(item, line)
                elif msg_type == "ITEM_END":
                    item, success, message = payload
                    self._on_ui_item_end(item, success, message)
                elif msg_type == "QUEUE_DONE":
                    summary = payload
                    self._on_ui_queue_done(summary)
        except Exception:
            pass

        if not self.is_finished:
            self.after(25, self._drain_ui_queue)

    def _on_ui_item_start(self, item: ProgramItem, cur: int, tot: int) -> None:
        self.current_item = item
        src = (item.source or "WINGET").upper()
        self.lbl_source_badge.config(text=src)
        self.lbl_active_name.config(text=item.name)
        v_from = item.installed_version or "—"
        v_to = item.latest_version or "Latest"
        self.lbl_active_version.config(text=f"{v_from}  ➔  {v_to}")
        self.active_phase_text = f"⚡ Initializing upgrade payload for '{item.name}'..."
        self.lbl_active_phase.config(text=self.active_phase_text)

        # Update checklist row
        k = item.id or item.name
        if k in self.item_row_widgets:
            widgets = self.item_row_widgets[k]
            widgets["status"].config(
                text="⚡ Installing...",
                fg="#f59e0b" if not self.is_dark else "#fbbf24",
            )
            widgets["row"].config(bg="#f1f5f9" if not self.is_dark else "#334155")
            widgets["name"].config(font=("Segoe UI", 9, "bold"))

        # Update queue progress metrics
        self.target_progress_pct = ((cur - 1) / max(1, tot)) * 100.0
        self.lbl_queue_metric.config(
            text=f"Queue Progress: {self.completed_count} of {tot} completed ({int(self.target_progress_pct)}%)"
        )

        # Append start header to live log
        t_str = time.strftime("%H:%M:%S")
        self.terminal_text.insert(
            tk.END,
            f"\n[{t_str}] ════════════════════════════════════════════════════\n",
            "timestamp",
        )
        self.terminal_text.insert(
            tk.END,
            f"[{t_str}] Starting update: {item.name} ({item.id}) via {src}\n",
            "info",
        )
        self.terminal_text.see(tk.END)

    def _on_ui_item_log(self, item: ProgramItem, line: str) -> None:
        clean = line.strip()
        if not clean:
            return

        # Dynamically detect active installation phase
        lower_line = clean.lower()
        if "download" in lower_line or "downloading" in lower_line:
            self.active_phase_text = "📥 Downloading verified installer payload..."
        elif "hash" in lower_line or "verif" in lower_line or "signature" in lower_line:
            self.active_phase_text = "🔒 Verifying installer signature & SHA-256..."
        elif "start" in lower_line or "install" in lower_line or "running" in lower_line:
            self.active_phase_text = "⚙️ Executing silent package installer..."
        elif "success" in lower_line or "complete" in lower_line:
            self.active_phase_text = "✅ Installation finalized successfully!"

        self.lbl_active_phase.config(text=self.active_phase_text)

        # Append to terminal with appropriate color tagging
        tag = "info"
        if "error" in lower_line or "failed" in lower_line or "1618" in lower_line:
            tag = "error"
        elif "warning" in lower_line or "skip" in lower_line:
            tag = "warn"
        elif "success" in lower_line or "completed" in lower_line or "verified" in lower_line:
            tag = "success"

        t_str = time.strftime("%H:%M:%S")
        self.terminal_text.insert(tk.END, f"[{t_str}]  {clean}\n", tag)
        self.terminal_text.see(tk.END)

    def _on_ui_item_end(self, item: ProgramItem, success: bool, message: str) -> None:
        self.completed_count += 1
        if success:
            self.succeeded_count += 1
        else:
            self.failed_count += 1

        self.target_progress_pct = (self.completed_count / max(1, self.total_count)) * 100.0
        pct_int = int(self.target_progress_pct)

        self.lbl_queue_metric.config(
            text=f"Queue Progress: {self.completed_count} of {self.total_count} completed ({pct_int}%)"
        )
        self.lbl_counts_badge.config(
            text=f"{self.succeeded_count} succeeded • {self.failed_count} failed"
        )

        k = item.id or item.name
        if k in self.item_row_widgets:
            widgets = self.item_row_widgets[k]
            if success:
                widgets["status"].config(text="✅ Succeeded", fg=self.c_success)
            else:
                widgets["status"].config(text="❌ Failed", fg=self.c_failed)
            widgets["row"].config(bg=self.c_card_bg)

        # Log completion in terminal
        t_str = time.strftime("%H:%M:%S")
        status_tag = "success" if success else "error"
        res_str = "SUCCEEDED" if success else "FAILED"
        self.terminal_text.insert(
            tk.END,
            f"[{t_str}] Outcome: [{res_str}] {item.name} -> {message}\n",
            status_tag,
        )
        self.terminal_text.see(tk.END)

    def _on_ui_queue_done(self, summary) -> None:
        self.is_finished = True
        self.target_progress_pct = 100.0

        self.lbl_queue_metric.config(
            text=f"Queue Finished: {self.succeeded_count} updated, {self.failed_count} failed."
        )
        self.lbl_active_name.config(text="All queued updates completed.")
        self.lbl_active_phase.config(
            text="✓ Transaction resolved. You can inspect logs or view full summary.",
            fg=self.c_success,
        )

        # Switch action buttons
        self.btn_cancel.pack_forget()
        self.btn_background.pack_forget()
        self.btn_complete_view.pack(side=tk.RIGHT)

        # If window was minimized to background, restore it cleanly
        if self.is_minimized_background:
            self.restore_from_background()

    # --------------------------------------------------------------------------
    # 60 FPS Canvas Micro-Animations (Desktop-UI-Animation Skill Standards)
    # --------------------------------------------------------------------------

    def _animation_tick(self) -> None:
        """60 FPS Non-blocking tick loop applying delta-time normalized interpolation."""
        now = time.time()
        dt = max(0.001, min(0.1, now - self.last_tick_time))
        self.last_tick_time = now

        # 1. Delta-time normalized lerping for progress bar
        # current += (target - current) * (1 - exp(-speed * dt))
        lerp_factor = 1.0 - math.exp(-8.0 * dt)
        self.current_progress_pct += (self.target_progress_pct - self.current_progress_pct) * lerp_factor

        # 2. Advance spinner angle and shimmer wave
        if not self.is_finished:
            self.spinner_angle = (self.spinner_angle + 240.0 * dt) % 360.0
            self.shimmer_offset = (self.shimmer_offset + 220.0 * dt) % max(1.0, float(self.dlg_width))
        else:
            # Morph spinner into drawn checkmark
            self.checkmark_progress = min(1.0, self.checkmark_progress + 3.0 * dt)

        # 3. Redraw Header Canvas & Progress Bars
        self._draw_header_canvas()
        self._draw_progress_bar()
        self._draw_shimmer_bar()

        # Reschedule tick at ~60 FPS only while active or completing checkmark animation
        if not self.is_finished or self.checkmark_progress < 1.0:
            self.after(16, self._animation_tick)

    def _draw_header_canvas(self) -> None:
        """Renders the revolving neon gradient arc spinner and ambient telemetry."""
        cv = self.header_canvas
        w = cv.winfo_width() or self.dlg_width
        h = 105

        cv.delete("all")

        # Subtle dark velvet background with ambient grid line
        bg_color = "#090d16" if self.is_dark else "#881337"
        cv.create_rectangle(0, 0, w, h, fill=bg_color, width=0)

        # Center coordinates for spinner
        cx = 58
        cy = h // 2
        r = 30

        if not self.is_finished:
            # Ambient energy glow ring behind spinner
            cv.create_oval(
                cx - r - 4,
                cy - r - 4,
                cx + r + 4,
                cy + r + 4,
                outline="#4c0519" if not self.is_dark else "#1e293b",
                width=4,
            )

            # Revolving primary neon arc
            start_ang = self.spinner_angle
            cv.create_arc(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                start=start_ang,
                extent=110,
                outline=self.c_accent_light,
                width=4,
                style=tk.ARC,
            )

            # Secondary trailing cyan arc for high-tech neon styling
            cv.create_arc(
                cx - r + 3,
                cy - r + 3,
                cx + r - 3,
                cy + r - 3,
                start=(start_ang + 180) % 360,
                extent=60,
                outline="#06b6d4",
                width=3,
                style=tk.ARC,
            )

            # Center pulse dot
            pulse_r = 5 + int(math.sin(time.time() * 6) * 2)
            cv.create_oval(
                cx - pulse_r,
                cy - pulse_r,
                cx + pulse_r,
                cy + pulse_r,
                fill="#ffffff",
                outline="",
            )
        else:
            # Succeeded state: Drawn animated emerald checkmark with cubic ease-out
            # Circle base
            cv.create_oval(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                fill="#059669",
                outline="#10b981",
                width=3,
            )

            # Draw checkmark segments based on checkmark_progress (0.0 to 1.0)
            # Checkmark points: p1=(cx-10, cy), p2=(cx-2, cy+8), p3=(cx+12, cy-8)
            p1 = (cx - 11, cy)
            p2 = (cx - 2, cy + 9)
            p3 = (cx + 12, cy - 8)

            t = self.checkmark_progress
            # Cubic ease-out
            eased_t = 1.0 - math.pow(1.0 - t, 3)

            if eased_t <= 0.4:
                seg_t = eased_t / 0.4
                curr_x = p1[0] + (p2[0] - p1[0]) * seg_t
                curr_y = p1[1] + (p2[1] - p1[1]) * seg_t
                cv.create_line(p1[0], p1[1], curr_x, curr_y, fill="#ffffff", width=4, capstyle=tk.ROUND)
            else:
                cv.create_line(p1[0], p1[1], p2[0], p2[1], fill="#ffffff", width=4, capstyle=tk.ROUND)
                seg_t = (eased_t - 0.4) / 0.6
                curr_x = p2[0] + (p3[0] - p2[0]) * seg_t
                curr_y = p2[1] + (p3[1] - p2[1]) * seg_t
                cv.create_line(p2[0], p2[1], curr_x, curr_y, fill="#ffffff", width=4, capstyle=tk.ROUND)

        # Header Titles & Telemetry
        title_text = "UPDATING SYSTEM SOFTWARE" if not self.is_finished else "UPDATE BATCH COMPLETED"
        cv.create_text(
            110,
            cy - 12,
            text=title_text,
            fill="#ffffff",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )

        sub_text = (
            f"Active: {self.current_item.name if self.current_item else 'Waiting...'} • Safe Execution"
            if not self.is_finished
            else f"Finished: {self.succeeded_count} updated successfully, {self.failed_count} failed."
        )
        cv.create_text(
            110,
            cy + 12,
            text=sub_text,
            fill="#e2e8f0" if not self.is_dark else "#94a3b8",
            font=("Segoe UI", 9),
            anchor="w",
        )

    def _draw_progress_bar(self) -> None:
        """Renders smoothly lerped overall progress bar."""
        cv = self.bar_canvas
        w = cv.winfo_width() or (self.dlg_width - 36)
        h = 12

        cv.delete("all")

        # Track background pill
        cv.create_rectangle(0, 0, w, h, fill=self.c_border, width=0)

        # Lerped progress fill
        fill_w = max(0.0, min(float(w), (self.current_progress_pct / 100.0) * float(w)))
        if fill_w > 0:
            fill_color = self.c_accent if not self.is_finished else self.c_success
            cv.create_rectangle(0, 0, fill_w, h, fill=fill_color, width=0)

            # Subtle glow cap on leading edge
            if fill_w < w - 2 and not self.is_finished:
                cv.create_rectangle(fill_w - 3, 0, fill_w, h, fill=self.c_accent_light, width=0)

    def _draw_shimmer_bar(self) -> None:
        """Renders indeterminate light-sweep animation across active card."""
        if self.is_finished:
            self.shimmer_canvas.delete("all")
            return

        cv = self.shimmer_canvas
        w = cv.winfo_width() or (self.dlg_width - 64)
        h = 3

        cv.delete("all")
        cv.create_rectangle(0, 0, w, h, fill=self.c_border, width=0)

        # Shimmer light beam
        beam_w = 120
        start_x = self.shimmer_offset - beam_w
        end_x = self.shimmer_offset

        cv.create_rectangle(
            max(0, start_x),
            0,
            min(w, end_x),
            h,
            fill=self.c_accent_light,
            width=0,
        )

    # --------------------------------------------------------------------------
    # Interactive Controls & Background Minimization
    # --------------------------------------------------------------------------

    def minimize_to_background(self) -> None:
        """Hides the dialog and triggers background notification toast."""
        self.is_minimized_background = True
        self.withdraw()
        if self.on_run_in_background:
            self.on_run_in_background()

    def restore_from_background(self) -> None:
        """Restores modal to foreground when user clicks notification or status."""
        self.is_minimized_background = False
        self.deiconify()
        self.lift()
        self.focus_force()

    def _handle_cancel_click(self) -> None:
        if self.cancel_requested:
            return
        self.cancel_requested = True
        self.btn_cancel.config(
            text="⏳ Cancelling after current...",
            state=tk.DISABLED,
            bg="#f1f5f9",
            fg=self.c_text_muted,
        )
        self.active_phase_text = "Stopping queue after active installation concludes..."
        self.lbl_active_phase.config(text=self.active_phase_text)
        if self.on_cancel_queue:
            self.on_cancel_queue()

    def _handle_view_summary_click(self) -> None:
        self.destroy()
        if self.on_complete_view_summary:
            self.on_complete_view_summary()

    def _toggle_terminal_visibility(self) -> None:
        if self.terminal_visible:
            self.terminal_frame.pack_forget()
            self.btn_toggle_terminal.config(text="Terminal [ + ]")
            self.terminal_visible = False
            self.geometry(f"{self.dlg_width}x540")
        else:
            self.terminal_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
            self.btn_toggle_terminal.config(text="Terminal [ - ]")
            self.terminal_visible = True
            self.geometry(f"{self.dlg_width}x{self.dlg_height}")
