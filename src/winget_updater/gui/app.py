"""Software & Package Updater — Clean High-Contrast Desktop Application.
Features a two-column sidebar navigation, 4-column installed software table,
prominent burgundy 'Scan for Updates' button, and a bottom details drawer.
"""

import csv
import json
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageDraw, ImageFilter, ImageTk
from typing import List, Optional, Set
from winget_updater.adapters import SourceManager
from winget_updater.compatibility.checker import CompatibilityChecker
from winget_updater.compatibility.system_info import SystemInfoProvider
from winget_updater.config import ConfigManager
from winget_updater.discovery.composite import CompositeScanner
from winget_updater.winget.catalog import get_popular_catalog, search_catalog_packages
from winget_updater.engine.cleanup import DiskCleanupManager
from winget_updater.engine.reports import ReportGenerator
from winget_updater.engine.process_lock import ProcessLockDetector
from winget_updater.engine.restore_point import RestorePointManager
from winget_updater.engine.scheduler import SchedulerManager
from winget_updater.engine.state_manager import StateManager
from winget_updater.engine.tracker import UpdateTracker
from winget_updater.engine.updater import UpdateEngine, UpdateRunSummary
from winget_updater.engine.auto_updater import AppUpdateChecker
from winget_updater.engine.uninstaller import Uninstaller
from winget_updater.engine.windows_update import WindowsUpdateManager
from winget_updater.gui.animations import (
    CyberLaserHeaderCanvas,
    FluentFloatingToast,
    GlassyTelemetryHUD,
    ScanningPulseAnimator,
    SmoothLerpProgressBar,
    SoftwareEngineeringHeroScene,
    TimelinePipelineHUD,
)
from winget_updater.gui.components import (
    DetailsDrawer,
    AppUpdateNotificationBanner,
    DiagnosticsResolutionBanner,
    ElevationBanner,
    FloatingGlassBatchDock,
    InspectorPane,
    LiveWarningBar,
    ProgramTableView,
    SearchFilterBar,
    SidebarNavigation,
    StatCardDeck,
)
from winget_updater.gui.dialogs import (
    BindWingetSourceDialog,
    AppUpdateTrackerDialog,
    CannotUpdateHelpDialog,
    DiskCleanupDialog,
    ExclusionManagerDialog,
    GameRuntimesDialog,
    ScheduleConfigDialog,
    SettingsDialog,
    StartupManagerDialog,
    UpdateSummaryDialog,
    prompt_downgrade_confirmation,
    prompt_unverified_allow_confirmation,
    prompt_vendor_installer_confirmation,
)
from winget_updater.gui.live_update_modal import LiveUpdateProgressDialog
from winget_updater.gui.rounded_widgets import (
    IOSStyleToggleSwitch,
    RoundedButton,
    RoundedPillBadge,
    apply_native_window_styling,
)
from winget_updater.gui.system_update_flow import CompleteSystemUpdateDialog
from winget_updater.gui.theme import LIGHT_THEME, ThemeColors, Typography, get_theme, get_typography
from winget_updater.models import PackageType, ProgramItem, UpdateAction, UpdateOutcome
from winget_updater.utils.logger import get_logger
from winget_updater.winget.client import WingetClient
from winget_updater.winget.matcher import PackageMatcher
from winget_updater.winget.version_comparator import compare_versions

logger = get_logger()


class MainWindow(tk.Tk):
    """Primary application GUI window with a Clean White and Burgundy two-column design."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        super().__init__()
        self.title("Software & Package Updater")
        self.geometry("1260x820")
        self.minsize(1040, 680)

        # Core services & theme
        self.config = config_manager or ConfigManager()
        self.current_theme: ThemeColors = get_theme(getattr(self.config, "theme", "dark"))
        self.typography: Typography = get_typography(getattr(self.config, "font_scale", "normal"))

        # Apply native Windows 11 rounded window borders and dark titlebar styling
        try:
            apply_native_window_styling(self, self.current_theme)
        except Exception:
            pass

        # Apply GPU hardware acceleration and DWM DirectComposition
        try:
            from winget_updater.engine.gpu import GpuAccelerationManager
            GpuAccelerationManager.apply_hardware_window_acceleration(self)
        except Exception:
            pass

        # Style configuration
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

        # Core services initialized above
        self.winget = WingetClient()
        self.sys_info = SystemInfoProvider()
        self.checker = CompatibilityChecker(system_info=self.sys_info)
        self.state_mgr = StateManager()
        self.update_tracker = UpdateTracker()
        self.scheduler = SchedulerManager(sys_info=self.sys_info)
        self.source_manager = SourceManager(config=self.config)
        self.engine = UpdateEngine(
            winget_client=self.winget,
            compatibility_checker=self.checker,
            state_manager=self.state_mgr,
            source_manager=self.source_manager,
        )

        # State data
        self.all_programs: List[ProgramItem] = []
        self.filtered_programs: List[ProgramItem] = []
        self.active_filter: str = "All Software"
        self.search_query: str = ""
        self.catalog_items: List[ProgramItem] = []
        self._catalog_search_generation: int = 0
        self.active_category: str = "All Categories"
        self.selected_item: Optional[ProgramItem] = None
        self.updating_package_ids: Set[str] = set()
        self.is_busy = False
        self.cancel_update_requested = False
        self.live_update_dialog: Optional[LiveUpdateProgressDialog] = None
        self._last_update_summary: Optional[UpdateRunSummary] = None
        self.msg_queue: queue.Queue = queue.Queue()

        self.dry_run_var = tk.BooleanVar(value=False)
        self.restore_point_var = tk.BooleanVar(value=getattr(self.config, "create_restore_point", False))
        self.auto_close_var = tk.BooleanVar(value=getattr(self.config, "auto_close_apps", True))
        self.theme_var = tk.BooleanVar(value=(getattr(self.current_theme, "name", "light") == "dark"))

        self._build_layout()
        self._poll_queue()

        # Non-blocking initial scan
        self.after(50, self._on_ready_startup)

    def _on_ready_startup(self) -> None:
        self.set_font_scale(getattr(self.config, "font_scale", "normal"))
        if getattr(self.config, "auto_scan_on_startup", True):
            self.start_scan()

    def _show_floating_toast(self, text: str, icon: str = "✓") -> None:
        """Presents a clean floating notification dropping from top."""
        t = getattr(self, "current_theme", None)
        bg = t.bg_card if t else "#0b0f17"
        fg = t.fg_primary if t else "#f8fafc"
        border_col = t.border_accent if t else "#00f0ff"
        icon_fg = t.fg_laser if t else "#00f0ff"
        FluentFloatingToast.show(self, text=text, icon=icon, bg=bg, fg=fg, border_col=border_col, icon_fg=icon_fg, duration_ms=2800)
        if hasattr(self, "status_lbl"):
            self.status_lbl.config(text=text)

    def _build_layout(self) -> None:
        self.configure(bg=self.current_theme.bg_root)

        # 1. Top Title Bar Frame
        self.top_bar = tk.Frame(self, bg=self.current_theme.bg_header, padx=18, pady=8, highlightbackground=self.current_theme.border, highlightthickness=1)
        self.top_bar.pack(fill=tk.X)

        from winget_updater.engine.gpu import GpuAccelerationManager
        self.primary_gpu = GpuAccelerationManager.get_primary_gpu()
        gpu_display = self.primary_gpu.name
        if len(gpu_display) > 28:
            gpu_display = gpu_display.replace("NVIDIA ", "").replace("Graphics", "").strip()

        # 1. Top Right Controls (pack right first to guarantee visibility)
        self.top_controls = tk.Frame(self.top_bar, bg=self.current_theme.bg_header)
        self.top_controls.pack(side=tk.RIGHT, padx=(0, 2))

        # Settings Button (Primary Top Control)
        self.btn_settings = RoundedButton(
            self.top_controls,
            text="⚙️ Settings",
            command=self._open_settings,
            bg_color="#221c38" if self.current_theme.name == "dark" else "#881337",
            fg_color="#e2e8f0" if self.current_theme.name == "dark" else "#ffffff",
            hover_bg="#352c54" if self.current_theme.name == "dark" else "#9f1239",
            border_color="#3d335c" if self.current_theme.name == "dark" else self.current_theme.border,
            radius=10,
            height=28,
            font=("Segoe UI", 8, "bold"),
            padding=(10, 4),
        )
        self.btn_settings.pack(side=tk.LEFT, padx=(4, 0))

        # Secondary options are housed in top_dock_bar and Settings

        # 3-Way Luxury Glass Mode Switcher: WAKE [●] / DREAM [○] / BLOOM [○]
        self.theme_box = tk.Frame(self.top_controls, bg=self.current_theme.bg_header)
        self.theme_box.pack(side=tk.LEFT, padx=(6, 0))

        initial_theme_txt = (
            "🌙 DREAM" if self.current_theme.name == "dark"
            else ("🌸 BLOOM" if self.current_theme.name == "bloom"
            else "☀️ WAKE")
        )
        self.btn_theme_cycle = RoundedButton(
            self.theme_box,
            text=initial_theme_txt,
            command=self.cycle_theme,
            bg_color="#221c38" if self.current_theme.name == "dark" else self.current_theme.bg_card,
            fg_color="#e2e8f0" if self.current_theme.name == "dark" else self.current_theme.fg_primary,
            hover_bg="#352c54" if self.current_theme.name == "dark" else self.current_theme.bg_card_hover,
            border_color="#3d335c" if self.current_theme.name == "dark" else self.current_theme.border,
            radius=10,
            width=96,
            height=28,
            font=("Segoe UI", 8, "bold"),
            padding=(6, 2),
            parent_bg=self.current_theme.bg_header,
        )
        self.btn_theme_cycle.pack(side=tk.LEFT, padx=(4, 0))

        # Hidden iOS toggle switch retained for backwards test compatibility
        self.sw_theme = IOSStyleToggleSwitch(
            self.theme_box,
            variable=self.theme_var,
            command=self._on_theme_switch_toggled,
            width=36,
            height=18,
            on_color="#e11d48",
            off_color="#1e2c45",
            parent_bg=self.current_theme.bg_header,
        )
        self.lbl_theme_mode = tk.Label(
            self.theme_box,
            text="Light / Dark",
            font=("Segoe UI", 8, "bold"),
            bg=self.current_theme.bg_header,
            fg=self.current_theme.fg_muted,
        )

        # 2. Top Left Brand & Status
        self.brand_title_box = tk.Frame(self.top_bar, bg=self.current_theme.bg_header)
        self.brand_title_box.pack(side=tk.LEFT)

        self.lbl_app_icon = tk.Label(
            self.brand_title_box,
            text="🔄",
            bg=self.current_theme.bg_header,
            fg="#00f0ff" if self.current_theme.name == "dark" else self.current_theme.accent_burgundy,
            font=("Segoe UI", 12),
        )
        self.lbl_app_icon.pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_app_title = tk.Label(
            self.brand_title_box,
            text="Software & Package Updater",
            bg=self.current_theme.bg_header,
            fg="#ffffff" if self.current_theme.name == "dark" else self.current_theme.accent_burgundy,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        self.lbl_app_title.pack(side=tk.LEFT)

        self.lbl_app_sub = tk.Label(
            self.brand_title_box,
            text=" • Win11",
            bg=self.current_theme.bg_header,
            fg=self.current_theme.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.lbl_app_sub.pack(side=tk.LEFT, padx=(4, 0))

        # Frosted Glass Telemetry HUD
        self.hud = GlassyTelemetryHUD(self.top_bar, sys_info=self.sys_info, gpu_name=self.primary_gpu.name)
        self.hud.pack(side=tk.LEFT, padx=(14, 0))

        # Pending Reboot Required Indicator
        is_reboot, r_reason = WindowsUpdateManager.is_reboot_pending()
        self.reboot_badge = RoundedPillBadge(
            self.top_bar,
            text="⚠️ Restart Required" if is_reboot else "",
            bg_color="#fef3c7" if is_reboot else "#ffffff",
            fg_color="#92400e" if is_reboot else "#ffffff",
            parent_bg="#ffffff",
        )
        if is_reboot:
            self.reboot_badge.pack(side=tk.LEFT, padx=(10, 0))

        # Backwards compatible btn_theme
        self.btn_theme = RoundedButton(
            self.top_controls,
            text="Dark mode",
            command=self.toggle_theme,
            bg_color="#f8fafc",
            fg_color="#334155",
            radius=6,
            height=28,
        )

        # Cyber laser pulse divider beneath header
        self.laser_header = CyberLaserHeaderCanvas(self, height=2, bg=self.current_theme.bg_root)
        self.laser_header.pack(fill=tk.X)
        self.laser_header.start()

        # 2. Main 3-Column Container with Translucent Ambient Aurora Glass Backdrop
        self.main_body = tk.Canvas(self, bg=self.current_theme.bg_root, highlightthickness=0, bd=0)
        self.main_body.pack(fill=tk.BOTH, expand=True)
        self.main_body.bind("<Configure>", self._update_aurora_bg)

        # Left Column: Sidebar Navigation (width 250)
        self.sidebar = SidebarNavigation(
            self.main_body,
            on_filter_changed=self._on_sidebar_filter_changed,
            on_search_changed=self._on_sidebar_search_changed,
            on_category_changed=self._on_sidebar_category_changed,
            on_open_tracker=self._open_update_tracker,
            on_open_runtimes=self._open_runtimes_manager,
            on_open_disk_cleanup=self._open_disk_cleanup,
            sys_info=self.sys_info,
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(12, 6), pady=12)

        # Right Column: Action & Controls Sidebar (width 245)
        self.right_action_sidebar = tk.Frame(
            self.main_body,
            width=245,
            bg=self.current_theme.bg_card,
            padx=12,
            pady=12,
            highlightbackground=self.current_theme.border,
            highlightthickness=1,
        )
        self.right_action_sidebar.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 12), pady=12)
        self.right_action_sidebar.pack_propagate(False)

        # 2a. Top Section: iOS Switches Box
        self.switches_card = tk.Frame(
            self.right_action_sidebar,
            bg=self.current_theme.bg_card,
            padx=8,
            pady=8,
            highlightbackground=self.current_theme.border,
            highlightthickness=1,
        )
        self.switches_card.pack(fill=tk.X, pady=(0, 10))

        # Row 1: Auto-close running
        self.row_sw1 = tk.Frame(self.switches_card, bg=self.current_theme.bg_card)
        self.row_sw1.pack(fill=tk.X, pady=3)
        self.lbl_sw_auto = tk.Label(self.row_sw1, text="Auto-close running", bg=self.current_theme.bg_card, fg=self.current_theme.fg_primary, font=("Segoe UI", 8), anchor="w")
        self.lbl_sw_auto.pack(side=tk.LEFT)
        self.sw_auto_close = IOSStyleToggleSwitch(self.row_sw1, variable=self.auto_close_var, width=36, height=18, parent_bg=self.current_theme.bg_card, on_color=self.current_theme.accent_crimson, off_color="#334155" if self.current_theme.name == "dark" else "#cbd5e1")
        self.sw_auto_close.pack(side=tk.RIGHT)

        # Row 2: Create restore point
        self.row_sw2 = tk.Frame(self.switches_card, bg=self.current_theme.bg_card)
        self.row_sw2.pack(fill=tk.X, pady=3)
        self.lbl_sw_restore = tk.Label(self.row_sw2, text="Create restore point", bg=self.current_theme.bg_card, fg=self.current_theme.fg_primary, font=("Segoe UI", 8), anchor="w")
        self.lbl_sw_restore.pack(side=tk.LEFT)
        self.sw_restore_point = IOSStyleToggleSwitch(self.row_sw2, variable=self.restore_point_var, width=36, height=18, parent_bg=self.current_theme.bg_card, on_color=self.current_theme.accent_crimson, off_color="#334155" if self.current_theme.name == "dark" else "#cbd5e1")
        self.sw_restore_point.pack(side=tk.RIGHT)

        # Row 3: Dry run (simulate only)
        self.row_sw3 = tk.Frame(self.switches_card, bg=self.current_theme.bg_card)
        self.row_sw3.pack(fill=tk.X, pady=3)
        self.lbl_sw_dry = tk.Label(self.row_sw3, text="Dry run (simulate only)", bg=self.current_theme.bg_card, fg=self.current_theme.fg_primary, font=("Segoe UI", 8), anchor="w")
        self.lbl_sw_dry.pack(side=tk.LEFT)
        self.sw_dry_run = IOSStyleToggleSwitch(self.row_sw3, variable=self.dry_run_var, width=36, height=18, parent_bg=self.current_theme.bg_card, on_color=self.current_theme.accent_crimson, off_color="#334155" if self.current_theme.name == "dark" else "#cbd5e1")
        self.sw_dry_run.pack(side=tk.RIGHT)

        # Hidden Checkbuttons for backwards compatibility with tests
        self.chk_dry_run = tk.Checkbutton(self.right_action_sidebar, variable=self.dry_run_var)
        self.chk_restore_point = tk.Checkbutton(self.right_action_sidebar, variable=self.restore_point_var)
        self.chk_auto_close = tk.Checkbutton(self.right_action_sidebar, variable=self.auto_close_var)

        # 2b. Middle Section: Action Deck
        self.actions_card = tk.Frame(self.right_action_sidebar, bg=self.current_theme.bg_card)
        self.actions_card.pack(fill=tk.X, pady=(0, 10))

        self.lbl_action_deck = tk.Label(
            self.actions_card,
            text="ACTIONS",
            bg=self.current_theme.bg_card,
            fg=self.current_theme.fg_muted,
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_action_deck.pack(fill=tk.X, pady=(0, 6))

        self.btn_select_updates = RoundedButton(
            self.actions_card,
            text="Select updates",
            command=self._select_all_updates_clicked,
            bg_color="#221c38" if self.current_theme.name == "dark" else "#ffffff",
            fg_color=self.current_theme.fg_primary,
            hover_bg="#1e2c45" if self.current_theme.name == "dark" else "#f1f5f9",
            border_color=self.current_theme.border,
            radius=10,
            height=32,
            font=("Segoe UI", 9),
            padding=(8, 4),
            parent_bg=self.current_theme.bg_card,
        )

        self.btn_update_selected = RoundedButton(
            self.actions_card,
            text="Update selected",
            command=self._on_update_selected_clicked,
            bg_color="#221c38" if self.current_theme.name == "dark" else "#ffffff",
            fg_color="#64748b" if self.current_theme.name == "dark" else "#64748b",
            hover_bg="#1e2c45" if self.current_theme.name == "dark" else "#f1f5f9",
            border_color=self.current_theme.border,
            radius=10,
            height=32,
            font=("Segoe UI", 9),
            padding=(8, 4),
            parent_bg=self.current_theme.bg_card,
        )
        self.btn_update_selected.config(state="disabled")
        self.btn_update_selected.pack(fill=tk.X, pady=(0, 6))

        self.btn_update = RoundedButton(
            self.actions_card,
            text="Update all eligible",
            command=self.start_update_approved,
            bg_color="#541528" if self.current_theme.name == "dark" else "#3b0d1e",
            fg_color="#ffffff",
            hover_bg="#6b1a33",
            border_color="#7c1e38" if self.current_theme.name == "dark" else "#e11d48",
            radius=10,
            height=32,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 4),
            parent_bg=self.current_theme.bg_card,
        )
        self.btn_update.config(state="disabled")
        self.btn_update.pack(fill=tk.X, pady=(0, 6))

        self.btn_complete_system = RoundedButton(
            self.actions_card,
            text="⚡ Complete system update",
            command=self._open_complete_system_update,
            bg_color="#7c122e" if self.current_theme.name == "dark" else "#680b26",
            fg_color="#ffffff",
            hover_bg="#941838",
            border_color="#a81b40" if self.current_theme.name == "dark" else "#9f1239",
            radius=10,
            height=32,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 4),
            parent_bg=self.current_theme.bg_card,
        )
        self.btn_complete_system.pack(fill=tk.X, pady=(0, 6))

        self.btn_scan = RoundedButton(
            self.actions_card,
            text="Check for updates",
            command=self.start_scan,
            bg_color="#b91c47" if self.current_theme.name == "dark" else "#e11d48",
            fg_color="#ffffff",
            hover_bg="#d92455",
            border_color="#e11d48",
            radius=10,
            height=32,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 4),
            parent_bg=self.current_theme.bg_card,
        )
        self.btn_scan.pack(fill=tk.X)

        # 2c. System Engine Specs Card (fills lower space with luxury frosted telemetry)
        self.specs_card = tk.Frame(
            self.right_action_sidebar,
            bg="#16132a" if self.current_theme.name == "dark" else self.current_theme.bg_card,
            padx=10,
            pady=10,
            highlightbackground="#2e254c" if self.current_theme.name == "dark" else self.current_theme.border,
            highlightthickness=1,
        )
        self.specs_card.pack(fill=tk.X, pady=(16, 0))

        self.lbl_specs_head = tk.Label(self.specs_card, text="SYSTEM INTEG // METRICS", bg=self.specs_card.cget("bg"), fg="#a78bfa" if self.current_theme.name == "dark" else "#64748b", font=("Cascadia Code", 7, "bold"), anchor="w")
        self.lbl_specs_head.pack(fill=tk.X, pady=(0, 6))

        for spec_k, spec_v, spec_col in [
            ("Mica Blur", "ACTIVE (DWM)", "#10b981"),
            ("Refresh", "120Hz Lerp", "#00f0ff"),
            ("Scan Engine", "Multi-Source", "#f43f5e"),
            ("Scan Speed", "< 2.0s Instant", "#38bdf8"),
        ]:
            row = tk.Frame(self.specs_card, bg=self.specs_card.cget("bg"))
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=spec_k, bg=self.specs_card.cget("bg"), fg="#94a3b8", font=("Segoe UI", 7), anchor="w").pack(side=tk.LEFT)
            tk.Label(row, text=spec_v, bg=self.specs_card.cget("bg"), fg=spec_col, font=("Segoe UI", 7, "bold"), anchor="e").pack(side=tk.RIGHT)

        # Center Column: Main Content Container (expands)
        self.right_container = tk.Frame(self.main_body, bg=self.current_theme.bg_root)
        self.right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=12)

        # Floating Pill Dock Bar right above table (matches 1:1 with mockup dock)
        self.top_dock_bar = tk.Frame(self.right_container, bg=self.current_theme.bg_root, pady=4)
        self.top_dock_bar.pack(fill=tk.X, padx=0, pady=(0, 6))

        self.btn_restore = RoundedButton(self.top_dock_bar, text="Restore", command=self._import_software_backup, bg_color="#221c38" if self.current_theme.name == "dark" else "#ffffff", fg_color=self.current_theme.fg_primary, border_color="#3d335c" if self.current_theme.name == "dark" else self.current_theme.border, radius=10, height=26, font=("Segoe UI", 8), padding=(8, 2), parent_bg=self.current_theme.bg_root)
        self.btn_restore.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_backup = RoundedButton(self.top_dock_bar, text="Backup", command=self._export_software_backup, bg_color="#221c38" if self.current_theme.name == "dark" else "#ffffff", fg_color=self.current_theme.fg_primary, border_color="#3d335c" if self.current_theme.name == "dark" else self.current_theme.border, radius=10, height=26, font=("Segoe UI", 8), padding=(8, 2), parent_bg=self.current_theme.bg_root)
        self.btn_backup.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_sources = RoundedButton(self.top_dock_bar, text="Sources", command=self._refresh_sources_dialog, bg_color="#221c38" if self.current_theme.name == "dark" else "#ffffff", fg_color=self.current_theme.fg_primary, border_color="#3d335c" if self.current_theme.name == "dark" else self.current_theme.border, radius=10, height=26, font=("Segoe UI", 8), padding=(8, 2), parent_bg=self.current_theme.bg_root)
        self.btn_sources.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_exclusions = RoundedButton(self.top_dock_bar, text="Exclusions", command=self._open_exclusions, bg_color="#221c38" if self.current_theme.name == "dark" else "#ffffff", fg_color=self.current_theme.fg_primary, border_color="#3d335c" if self.current_theme.name == "dark" else self.current_theme.border, radius=10, height=26, font=("Segoe UI", 8), padding=(8, 2), parent_bg=self.current_theme.bg_root)
        self.btn_exclusions.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_schedule = RoundedButton(self.top_dock_bar, text="Schedule", command=self._open_schedule, bg_color="#221c38" if self.current_theme.name == "dark" else "#ffffff", fg_color=self.current_theme.fg_primary, border_color="#3d335c" if self.current_theme.name == "dark" else self.current_theme.border, radius=10, height=26, font=("Segoe UI", 8), padding=(8, 2), parent_bg=self.current_theme.bg_root)
        self.btn_schedule.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_export = RoundedButton(self.top_dock_bar, text="Export", command=self._export_report_dialog, bg_color="#221c38" if self.current_theme.name == "dark" else "#ffffff", fg_color=self.current_theme.fg_primary, border_color="#3d335c" if self.current_theme.name == "dark" else self.current_theme.border, radius=10, height=26, font=("Segoe UI", 8), padding=(8, 2), parent_bg=self.current_theme.bg_root)
        self.btn_export.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_runtimes = RoundedButton(
            self.top_dock_bar,
            text="🎮 Game Runtimes",
            command=self._open_runtimes_manager,
            bg_color="#3b1120" if self.current_theme.name == "dark" else "#fff1f2",
            fg_color="#f43f5e" if self.current_theme.name == "dark" else "#e11d48",
            border_color="#7c1e38" if self.current_theme.name == "dark" else "#fda4af",
            radius=10,
            height=26,
            font=("Segoe UI", 8, "bold"),
            padding=(8, 2),
            parent_bg=self.current_theme.bg_root,
        )
        self.btn_runtimes.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_disk_clean = RoundedButton(
            self.top_dock_bar,
            text="🧹 Clean Disk",
            command=self._open_disk_cleanup,
            bg_color="#182738" if self.current_theme.name == "dark" else "#f0f9ff",
            fg_color="#38bdf8" if self.current_theme.name == "dark" else "#0284c7",
            border_color="#075985" if self.current_theme.name == "dark" else "#bae6fd",
            radius=10,
            height=26,
            font=("Segoe UI", 8, "bold"),
            padding=(8, 2),
            parent_bg=self.current_theme.bg_root,
        )
        self.btn_disk_clean.pack(side=tk.LEFT, padx=(0, 4))

        # 3. Unified Center Card: Frosted Glass container housing All Software header and Data Table
        self.table_card = tk.Frame(
            self.right_container,
            bg=self.current_theme.bg_card,
            highlightbackground=self.current_theme.border,
            highlightthickness=1,
            padx=2,
            pady=2,
        )
        self.table_card.pack(fill=tk.BOTH, expand=True, padx=0, pady=(0, 8))

        # Title Header directly inside the frosted card
        self.action_header = tk.Frame(
            self.table_card,
            bg=self.current_theme.bg_card,
            padx=16,
            pady=10,
            highlightthickness=0,
        )
        self.action_header.pack(fill=tk.X)

        self.header_title_box = tk.Frame(self.action_header, bg=self.current_theme.bg_card)
        self.header_title_box.pack(side=tk.LEFT)

        self.lbl_view_title = tk.Label(
            self.header_title_box,
            text="All Software",
            bg=self.current_theme.bg_card,
            fg=self.current_theme.fg_primary,
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        )
        self.lbl_view_title.pack(anchor=tk.W)

        self.lbl_view_subtitle = tk.Label(
            self.header_title_box,
            text="Loading discovered software...",
            bg=self.current_theme.bg_card,
            fg=self.current_theme.fg_muted,
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.lbl_view_subtitle.pack(anchor=tk.W, pady=(2, 0))

        self.header_btn_box = tk.Frame(self.action_header, bg=self.current_theme.bg_card)
        self.header_btn_box.pack(side=tk.RIGHT)

        # 4. Progress bar frame for scanning / updates (hidden when idle to match clean table layout)
        self.progress_frame = tk.Frame(self.table_card, bg=self.current_theme.bg_card, padx=16, pady=2)

        self.status_lbl = tk.Label(
            self.progress_frame,
            text="Ready.",
            bg=self.current_theme.bg_card,
            fg=self.current_theme.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
            cursor="hand2",
        )
        self.status_lbl.pack(side=tk.LEFT)
        self.status_lbl.bind("<Button-1>", self._restore_live_modal_if_background)

        self.progress_bar = SmoothLerpProgressBar(self.progress_frame, width=180, height=14)
        self.progress_bar.pack(side=tk.RIGHT)

        self.lbl_gpu_badge = tk.Label(
            self.progress_frame,
            text=f"DirectX 12 GPU: {self.primary_gpu.name}",
            bg=self.current_theme.bg_card,
            fg="#10b981" if self.current_theme.name == "dark" else "#059669",
            font=("Segoe UI", 8, "bold"),
            anchor="e",
        )
        # Retained hidden to preserve space for progress bar and prevent line collisions

        # Animated status pulse
        self.scan_animator = ScanningPulseAnimator(self.status_lbl, "Scanning software and repositories...")

        # 5. Installed-Software Table (4 Columns: Name, Current Version, Latest Version, Status)
        self.table_container = tk.Frame(self.table_card, bg=self.current_theme.bg_card, padx=8, pady=4, highlightthickness=0)
        self.table_container.pack(fill=tk.BOTH, expand=True)

        # Frosted glass banner for review & unverified software
        self.diag_banner = DiagnosticsResolutionBanner(
            self.table_container,
            on_auto_resolve_all=self._handle_batch_auto_resolve,
            on_open_help=self._open_cannot_update_help,
        )
        self.diag_banner.pack_forget()

        # Notification banner for app updates
        self.app_update_banner = AppUpdateNotificationBanner(
            self.table_container,
            on_download_click=self._handle_app_update_download,
            on_dismiss_click=self._handle_app_update_dismiss,
        )
        self.app_update_banner.pack_forget()

        self.table = ProgramTableView(
            self.table_container,
            on_double_click=self._handle_row_double_click,
            on_select_item=self._on_row_selected,
            on_batch_select=self._on_batch_selected,
            on_exclude_item=self._handle_context_exclude,
            on_single_update=self._handle_context_update,
            on_uninstall_item=self._handle_context_uninstall,
            on_toast_message=self._show_floating_toast,
            on_bind_source=self._open_bind_source_dialog,
            on_allow_unverified=self._handle_allow_unverified,
            on_open_website=self._handle_open_website,
            on_pin_item=self._handle_pin_item,
            on_skip_version=self._handle_skip_version,
            on_batch_update=self._handle_batch_update,
            on_batch_pin=self._handle_batch_pin,
            on_batch_exclude=self._handle_batch_exclude,
            on_batch_allow=self._handle_batch_allow,
        )
        self.table.pack(fill=tk.BOTH, expand=True)

        # 6. Floating Glass Batch Action Dock (Appears when multiple items selected)
        self.batch_dock = FloatingGlassBatchDock(
            self.right_container,
            on_batch_update=self._handle_batch_update,
            on_batch_allow=self._handle_batch_allow,
            on_batch_pin=self._handle_batch_pin,
            on_batch_exclude=self._handle_batch_exclude,
            on_clear_selection=self.table.clear_selection,
        )
        self.batch_dock.pack_forget()

        # 7. Bottom Details Drawer
        self.drawer = DetailsDrawer(
            self.right_container,
            on_single_update=self._handle_context_update,
            on_exclude_item=self._handle_context_exclude,
            on_uninstall_item=self._handle_context_uninstall,
            on_toast_message=self._show_floating_toast,
            on_bind_source=self._open_bind_source_dialog,
            on_allow_unverified=self._handle_allow_unverified,
            on_open_website=self._handle_open_website,
            on_pin_item=self._handle_pin_item,
            on_skip_version=self._handle_skip_version,
        )
        self.drawer.pack(fill=tk.X)

        # Seamless aliases for test compatibility & unified single-point action control
        self.p_btn_exclude = self.drawer.btn_exclude
        self.p_btn_folder = self.drawer.btn_open_folder
        self.p_btn_copy = self.drawer.btn_copy_id
        self.p_btn_pin = self.drawer.btn_pin
        self.p_btn_skip = self.drawer.btn_skip
        self.p_btn_uninstall = self.drawer.btn_uninstall
        self.p_btn_update = self.drawer.btn_update

        # Backwards-compatibility helper references
        self.inspector = self.drawer
        self.elevation_banner = ElevationBanner(self.main_body, sys_info=self.sys_info)
        self.elevation_banner.pack_forget()
        self.hero_scene = SoftwareEngineeringHeroScene(self.main_body, height=1)
        self.hero_scene.pack_forget()
        self.timeline = TimelinePipelineHUD(self.main_body, height=1)
        self.timeline.pack_forget()
# CyberLaserHeaderCanvas active between top_bar and main_body
        self.stat_cards = StatCardDeck(self.main_body, on_select_filter=lambda f: None)
        self.stat_cards.pack_forget()
        self.warning_bar = LiveWarningBar(self.main_body)
        self.warning_bar.pack_forget()
        self.filter_bar = SearchFilterBar(self.main_body, on_filter_change=lambda: None)
        self.filter_bar.pack_forget()

        # Keyboard shortcuts
        self.bind("<Control-f>", lambda e: self._shortcut_focus_search())
        self.bind("<slash>", lambda e: self._shortcut_focus_search())
        self.bind("<F5>", lambda e: self._start_scan_async())
        self.bind("<Control-r>", lambda e: self._start_scan_async())
        self.bind("<Control-b>", lambda e: self._export_software_backup())
        self.bind("<Control-i>", lambda e: self._import_software_backup())
        self.bind("<Control-e>", lambda e: self._open_exclusions_dialog())
        self.bind("<Control-t>", lambda e: self._open_update_tracker())
        self.bind("<Control-T>", lambda e: self._open_update_tracker())
        self.bind("<Control-g>", lambda e: self._open_runtimes_manager())
        self.bind("<Control-G>", lambda e: self._open_runtimes_manager())
        self.bind("<Control-k>", lambda e: self._open_disk_cleanup())
        self.bind("<Control-K>", lambda e: self._open_disk_cleanup())
        self.bind("<Control-Shift-S>", lambda e: self._open_startup_manager())
        self.bind("<Control-Shift-s>", lambda e: self._open_startup_manager())
        self.bind("<Control-Shift-U>", lambda e: self._open_complete_system_update())
        self.bind("<Control-Shift-u>", lambda e: self._open_complete_system_update())

        self.set_theme(self.current_theme.name)

    def apply_theme(self, theme) -> None:
        mode = getattr(theme, 'name', str(theme))
        self.set_theme(mode)

    def _update_aurora_bg(self, event=None):
        if not hasattr(self, "main_body") or not isinstance(self.main_body, tk.Canvas):
            return
        t = getattr(self, "current_theme", None)
        if not t or t.name != "dark":
            self.main_body.delete("aurora_bg")
            self.main_body.config(bg=t.bg_root if t else "#090d16")
            return

        w = self.main_body.winfo_width()
        h = self.main_body.winfo_height()
        if w < 100 or h < 100:
            w, h = 1260, 740

        cache_key = (w, h)
        if getattr(self, "_last_aurora_size", None) == cache_key and hasattr(self, "_aurora_photo"):
            photo = self._aurora_photo
        else:
            base = Image.new("RGB", (w, h), (12, 13, 24))
            draw = ImageDraw.Draw(base)
            # 1. Expanded radiant magenta/fuchsia bloom in center-bottom
            draw.ellipse([int(w * 0.15), int(h * 0.32), int(w * 0.90), int(h * 1.20)], fill=(175, 22, 80))
            draw.ellipse([int(w * 0.25), int(h * 0.44), int(w * 0.82), int(h * 1.10)], fill=(225, 29, 72))
            draw.ellipse([int(w * 0.35), int(h * 0.54), int(w * 0.75), int(h * 1.00)], fill=(244, 63, 94))
            draw.ellipse([int(w * 0.45), int(h * 0.64), int(w * 0.68), int(h * 0.90)], fill=(251, 113, 133))
            # 2. Radiant sapphire/cyan in top-right
            draw.ellipse([int(w * 0.50), -100, int(w * 1.20), int(h * 0.65)], fill=(2, 132, 199))
            draw.ellipse([int(w * 0.65), -60, int(w * 1.10), int(h * 0.45)], fill=(6, 182, 212))
            draw.ellipse([int(w * 0.75), -30, int(w * 1.00), int(h * 0.32)], fill=(103, 232, 249))
            # 3. Radiant purple/violet on left & mid-left
            draw.ellipse([-120, int(h * 0.10), int(w * 0.40), int(h * 0.90)], fill=(88, 28, 135))
            draw.ellipse([-50, int(h * 0.25), int(w * 0.30), int(h * 0.75)], fill=(147, 51, 234))
            # 4. Subtle emerald/teal on bottom-left
            draw.ellipse([-20, int(h * 0.72), int(w * 0.28), int(h * 1.05)], fill=(13, 148, 136))

            blurred = base.filter(ImageFilter.GaussianBlur(radius=85))
            try:
                photo = ImageTk.PhotoImage(blurred, master=self.main_body)
                self._aurora_photo = photo
                self._last_aurora_size = cache_key
            except Exception:
                return

        try:
            self.main_body.delete("aurora_bg")
            self.main_body.create_image(0, 0, image=photo, anchor="nw", tags="aurora_bg")
            self.main_body.tag_lower("aurora_bg")
        except Exception:
            pass

    def set_theme(self, mode: str) -> None:
        """Sets the application theme (wake/light, dream/dark, bloom) and updates all UI modules."""
        self.current_theme = get_theme(mode)
        t = self.current_theme

        # Re-apply native Windows 11 DWM backdrop and titlebar styling
        try:
            apply_native_window_styling(self, t)
        except Exception:
            pass

        self.configure(bg=t.bg_root)
        self.top_bar.config(bg=t.bg_header, highlightbackground=t.border)
        self.lbl_app_title.config(bg=t.bg_header, fg="#ffffff" if t.name == "dark" else t.accent_burgundy)
        self.lbl_app_sub.config(bg=t.bg_header, fg=t.fg_muted)
        self.top_controls.config(bg=t.bg_header)
        if hasattr(self, "laser_header"):
            self.laser_header.apply_theme(t)
        self._update_aurora_bg()

        # Update Mode Switcher button
        if hasattr(self, "btn_theme_cycle"):
            if t.name == "dark":
                txt = "🌙 DREAM"
            elif t.name == "bloom":
                txt = "🌸 BLOOM"
            else:
                txt = "☀️ WAKE"
            self.btn_theme_cycle.config(
                text=txt,
                bg=t.bg_card,
                fg=t.fg_primary,
                hover_bg=t.bg_card_hover,
            )
            self.btn_theme_cycle.border_color = t.border

        btn_txt = "Light mode" if t.name == "dark" else "Dark mode"
        self.btn_theme.config(text=btn_txt, bg=t.bg_button, fg=t.fg_primary)
        st_bg = "#221c38" if t.name == "dark" else t.accent_burgundy
        st_fg = "#e2e8f0" if t.name == "dark" else "#ffffff"
        st_hov = "#352c54" if t.name == "dark" else t.accent_burgundy_hover
        st_bd = "#3d335c" if t.name == "dark" else t.border
        self.btn_settings.config(bg=st_bg, fg=st_fg, hover_bg=st_hov, border_color=st_bd)
        if hasattr(self, "top_dock_bar"):
            self.top_dock_bar.config(bg=t.bg_root)
        for b in (getattr(self, "btn_restore", None), getattr(self, "btn_backup", None), getattr(self, "btn_sources", None), getattr(self, "btn_exclusions", None), getattr(self, "btn_schedule", None), getattr(self, "btn_export", None)):
            if b:
                b.config(bg=t.bg_button, fg=t.fg_primary, border_color=t.border, parent_bg=t.bg_root)
        if hasattr(self, "brand_title_box"):
            self.brand_title_box.config(bg=t.bg_header)
        if hasattr(self, "lbl_app_icon"):
            self.lbl_app_icon.config(bg=t.bg_header, fg="#00f0ff" if t.name == "dark" else t.accent_burgundy)

        self.main_body.config(bg=t.bg_root)
        self.right_container.config(bg=t.bg_root)
        if hasattr(self, "right_action_sidebar"):
            self.right_action_sidebar.config(bg=t.bg_sidebar if hasattr(t, "bg_sidebar") else t.bg_card, highlightbackground=t.border)
        if hasattr(self, "switches_card"):
            self.switches_card.config(bg=t.bg_card)
        if hasattr(self, "actions_card"):
            self.actions_card.config(bg=t.bg_card)
        if hasattr(self, "lbl_action_deck"):
            self.lbl_action_deck.config(bg=t.bg_card, fg=t.fg_muted)
        if hasattr(self, "specs_card"):
            self.specs_card.config(bg=t.bg_card, highlightbackground=t.border)
        if hasattr(self, "lbl_specs_head"):
            self.lbl_specs_head.config(bg=t.bg_card, fg="#a78bfa" if t.name == "dark" else t.fg_muted)
        if hasattr(self, "table_card"): self.table_card.config(bg=t.bg_card, highlightbackground=t.border)
        self.action_header.config(bg=t.bg_card, highlightthickness=0)
        self.header_title_box.config(bg=t.bg_card)
        self.header_btn_box.config(bg=t.bg_card)
        self.lbl_view_title.config(bg=t.bg_card, fg=t.fg_primary)
        self.lbl_view_subtitle.config(bg=t.bg_card, fg=t.fg_muted)
        self.chk_dry_run.config(bg=t.bg_card, fg=t.fg_secondary, selectcolor=t.bg_input)
        if hasattr(self, "chk_restore_point"):
            self.chk_restore_point.config(bg=t.bg_card, fg=t.fg_secondary, selectcolor=t.bg_input)
        if hasattr(self, "chk_auto_close"):
            self.chk_auto_close.config(bg=t.bg_card, fg=t.fg_secondary, selectcolor=t.bg_input)
        self.progress_frame.config(bg=t.bg_card)
        self.status_lbl.config(bg=t.bg_card, fg=t.fg_muted)
        if hasattr(self, "lbl_gpu_badge"):
            self.lbl_gpu_badge.config(bg=t.bg_card, fg="#10b981" if t.name == "dark" else "#059669")
        self.table_container.config(bg=t.bg_root)

        # Propagate to sub-components
        self.sidebar.apply_theme(t)
        self.table.apply_theme(t)
        self.drawer.apply_theme(t)
        self.progress_bar.apply_theme(t)
        if hasattr(self, "hud"):
            self.hud.apply_theme(t)
        if hasattr(self, "batch_dock"):
            self.batch_dock.apply_theme(t)
        if hasattr(self, "diag_banner"):
            self.diag_banner.apply_theme(t)
        if hasattr(self, "app_update_banner"):
            self.app_update_banner.apply_theme(t)
        if hasattr(self, "btn_select_updates"):
            self.btn_select_updates.config(bg=t.bg_button, fg=t.fg_primary)
        for act_b in (getattr(self, "btn_update_selected", None), getattr(self, "btn_update", None), getattr(self, "btn_complete_system", None), getattr(self, "btn_scan", None), getattr(self, "btn_select_updates", None)):
            if act_b:
                act_b.parent_bg = t.bg_card
                act_b.disabled_bg = "#141d30" if t.name == "dark" else "#f1f5f9"
                act_b.disabled_fg = "#475569" if t.name == "dark" else "#9ca3af"
                act_b.config(parent_bg=t.bg_card, disabled_bg=act_b.disabled_bg, disabled_fg=act_b.disabled_fg)

        if hasattr(self, "btn_complete_system"):
            cs_bg = "#7c122e" if t.name == "dark" else t.accent_burgundy
            self.btn_complete_system.disabled_bg = cs_bg
            self.btn_complete_system.disabled_fg = "#ffffff"
            self.btn_complete_system.config(bg=cs_bg, fg="#ffffff", hover_bg="#941838", border_color="#a81b40" if t.name == "dark" else "#9f1239", disabled_bg=cs_bg, disabled_fg="#ffffff")
        if hasattr(self, "btn_update"):
            up_bg = "#541528" if t.name == "dark" else t.accent_burgundy
            self.btn_update.disabled_bg = up_bg
            self.btn_update.disabled_fg = "#ffffff"
            self.btn_update.config(bg=up_bg, fg="#ffffff", hover_bg="#6b1a33", border_color="#7c1e38" if t.name == "dark" else "#e11d48", disabled_bg=up_bg, disabled_fg="#ffffff")
        if hasattr(self, "btn_scan"):
            sc_bg = "#b91c47" if t.name == "dark" else t.accent_burgundy
            self.btn_scan.disabled_bg = sc_bg
            self.btn_scan.disabled_fg = "#ffffff"
            self.btn_scan.config(bg=sc_bg, fg="#ffffff", hover_bg="#d92455", border_color="#e11d48", disabled_bg=sc_bg, disabled_fg="#ffffff")
        if hasattr(self, "reboot_badge"):
            is_reb, _ = WindowsUpdateManager.is_reboot_pending()
            if is_reb:
                self.reboot_badge.set_badge("⚠️ Restart Required", bg_color="#fef3c7", fg_color="#92400e")

        # Update Right Action Sidebar
        if hasattr(self, "right_action_sidebar"):
            self.right_action_sidebar.config(bg=t.bg_card, highlightbackground=t.border)
        if hasattr(self, "switches_card"):
            sw_card_bg = "#1c1836" if t.name == "dark" else t.bg_card
            sw_card_bd = "#362e58" if t.name == "dark" else t.border
            self.switches_card.config(bg=sw_card_bg, highlightbackground=sw_card_bd)
            for r in (getattr(self, "row_sw1", None), getattr(self, "row_sw2", None), getattr(self, "row_sw3", None)):
                if r:
                    r.config(bg=sw_card_bg)
            for lbl in (getattr(self, "lbl_sw_auto", None), getattr(self, "lbl_sw_restore", None), getattr(self, "lbl_sw_dry", None)):
                if lbl:
                    lbl.config(bg=sw_card_bg, fg=t.fg_primary)
            if hasattr(self, "sw_auto_close"):
                self.sw_auto_close.set_colors(on_color=t.accent_crimson, off_color="#332a4e" if t.name == "dark" else "#cbd5e1", parent_bg=sw_card_bg)
            if hasattr(self, "sw_restore_point"):
                self.sw_restore_point.set_colors(on_color=t.accent_crimson, off_color="#332a4e" if t.name == "dark" else "#cbd5e1", parent_bg=sw_card_bg)
            if hasattr(self, "sw_dry_run"):
                self.sw_dry_run.set_colors(on_color=t.accent_crimson, off_color="#332a4e" if t.name == "dark" else "#cbd5e1", parent_bg=sw_card_bg)

        if hasattr(self, "actions_card"):
            self.actions_card.config(bg=t.bg_card)
        if hasattr(self, "lbl_action_deck"):
            self.lbl_action_deck.config(bg=t.bg_card, fg=t.fg_muted)

        if hasattr(self, "right_selected_card"):
            self.right_selected_card.config(bg=t.bg_card)
            for rp in (getattr(self, "row_p1", None), getattr(self, "row_p2", None), getattr(self, "row_p3", None)):
                if rp:
                    rp.config(bg=t.bg_card)
            for p_btn in (getattr(self, "p_btn_exclude", None), getattr(self, "p_btn_folder", None), getattr(self, "p_btn_copy", None), getattr(self, "p_btn_pin", None), getattr(self, "p_btn_skip", None), getattr(self, "p_btn_uninstall", None), getattr(self, "p_btn_update", None), getattr(self, "btn_update_selected", None)):
                if p_btn:
                    p_btn.disabled_bg = t.bg_button
                    p_btn.disabled_fg = t.fg_muted
                    p_btn.config(bg=t.bg_button, fg=t.fg_primary, border_color=t.border, parent_bg=t.bg_card, disabled_bg=t.bg_button, disabled_fg=t.fg_muted)

        if hasattr(self, "specs_card"):
            sc_bg = "#16132a" if t.name == "dark" else t.bg_card
            sc_bd = "#2e254c" if t.name == "dark" else t.border
            self.specs_card.config(bg=sc_bg, highlightbackground=sc_bd)
            if hasattr(self, "lbl_specs_head"):
                self.lbl_specs_head.config(bg=sc_bg, fg="#a78bfa" if t.name == "dark" else "#64748b")
            for ch in self.specs_card.winfo_children():
                if isinstance(ch, tk.Frame):
                    ch.config(bg=sc_bg)
                    for lbl in ch.winfo_children():
                        if isinstance(lbl, tk.Label):
                            lbl.config(bg=sc_bg)

        if hasattr(self, "sw_theme"):
            self.sw_theme.set_colors(on_color=t.accent_burgundy, off_color="#334155" if t.name == "dark" else "#cbd5e1", parent_bg=t.bg_header)
        if hasattr(self, "theme_box"):
            self.theme_box.config(bg=t.bg_header)
        if hasattr(self, "lbl_theme_mode"):
            self.lbl_theme_mode.config(bg=t.bg_header, fg=t.fg_muted)
        if hasattr(self, "theme_var"):
            self.theme_var.set(t.name == "dark")

        self.config.set_theme(t.name)

    def _on_theme_switch_toggled(self, is_dark: bool) -> None:
        target = "dark" if is_dark else "light"
        if self.current_theme.name != target:
            self.set_theme(target)
            self._show_floating_toast(f"Switched to {target.capitalize()} Mode", "✓")

    def _open_app_folder(self, item: Optional[ProgramItem]) -> None:
        if self.drawer:
            self.drawer._on_open_folder_click()

    def _copy_package_id(self, item: Optional[ProgramItem]) -> None:
        if self.drawer:
            self.drawer._on_copy_id_click()

    @property
    def theme(self) -> ThemeColors:
        return self.current_theme

    def _open_update_tracker(self) -> None:
        """Opens the App Update Tracker dialog."""
        AppUpdateTrackerDialog(self, tracker=self.update_tracker, theme=self.current_theme)

    def _open_runtimes_manager(self) -> None:
        """Opens the Gaming & System Runtimes Manager modal."""
        try:
            dlg = GameRuntimesDialog(
                self,
                theme=self.current_theme,
                on_runtime_installed=self.start_scan,
            )
            dlg.focus_force()
        except Exception as e:
            logger.error(f"Failed to open GameRuntimesDialog: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to open Runtimes Manager:\n{e}", parent=self)

    def _open_disk_cleanup(self) -> None:
        """Opens the Disk Space Reclaimer & Installer Purge dialog."""
        try:
            dlg = DiskCleanupDialog(
                self,
                theme=self.current_theme,
                on_cleanup_done=lambda freed: self._show_floating_toast(f"Reclaimed {freed / (1024*1024):.1f} MB disk space", "🧹"),
            )
            dlg.focus_force()
        except Exception as e:
            logger.error(f"Failed to open DiskCleanupDialog: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to open Disk Cleanup:\n{e}", parent=self)

    def _open_startup_manager(self) -> None:
        """Opens the Windows Startup & Autorun Optimizer modal."""
        try:
            dlg = StartupManagerDialog(
                self,
                theme=self.current_theme,
            )
            dlg.focus_force()
        except Exception as e:
            logger.error(f"Failed to open StartupManagerDialog: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to open Startup Manager:\n{e}", parent=self)

    def _launch_app_uninstaller(self) -> None:
        """Launches the standalone complete uninstaller executable or script."""
        import subprocess, sys
        uninst_exe = Path.cwd() / "dist" / "Uninstall.exe"
        if uninst_exe.exists():
            subprocess.Popen([str(uninst_exe)])
        else:
            uninst_py = Path.cwd() / "uninstall.py"
            if uninst_py.exists():
                subprocess.Popen([sys.executable, str(uninst_py)])

    def _open_settings(self) -> None:
        """Opens the Settings & System Configuration modal."""
        SettingsDialog(
            self,
            config=self.config,
            on_theme_changed=self.set_theme,
            on_font_scale_changed=self.set_font_scale,
            on_settings_saved=self._on_settings_saved,
            on_backup_stack=self._export_software_backup,
            on_restore_stack=self._import_software_backup,
            on_refresh_sources=self._refresh_sources_dialog,
            on_open_exclusions=self._open_exclusions,
            on_open_schedule=self._open_schedule,
            on_open_runtimes=self._open_runtimes_manager,
            on_open_disk_cleanup=self._open_disk_cleanup,
            on_open_startup_manager=self._open_startup_manager,
            on_export_inventory=self._export_report_dialog,
            on_uninstall_app=self._launch_app_uninstaller,
            scheduler=self.scheduler,
            theme=self.current_theme,
        )

    def set_font_scale(self, scale: str) -> None:
        """Applies typography font scale dynamically across UI components."""
        self.typography = get_typography(scale)
        if hasattr(self, "table") and hasattr(self.table, "apply_typography"):
            self.table.apply_typography(self.typography)
        if hasattr(self, "sidebar") and hasattr(self.sidebar, "apply_typography"):
            self.sidebar.apply_typography(self.typography)
        self._show_floating_toast(f"Font scale set to {scale.replace('_', ' ').capitalize()}", "🔍")

    def _on_settings_saved(self) -> None:
        """Invoked when user updates configuration settings."""
        self._show_floating_toast("Settings saved successfully", "✓")

    def _open_complete_system_update(self) -> None:
        """Launches the 4-stage Complete System Update workflow dialog."""
        CompleteSystemUpdateDialog(self, theme=self.current_theme, on_finished=self.start_scan)

    def cycle_theme(self) -> None:
        """Cycles across all 3 luxury modes: WAKE -> DREAM -> BLOOM -> WAKE."""
        curr = getattr(self.current_theme, "name", "light")
        if curr in ("light", "wake"):
            nxt = "dream"
        elif curr in ("dark", "dream"):
            nxt = "bloom"
        else:
            nxt = "wake"
        self.set_theme(nxt)
        self._show_floating_toast(f"Switched to {nxt.upper()} Mode", "✨")

    def toggle_theme(self) -> None:
        """Toggles between Dark Mode and Light Mode."""
        new_theme = "dark" if self.current_theme.name == "light" else "light"
        self.set_theme(new_theme)
        self._show_floating_toast(f"Switched to {new_theme.capitalize()} Mode", "✓")

    def _refresh_sources_dialog(self) -> None:
        """Triggers a background refresh of winget sources and package manager indices."""
        if self.is_busy:
            return
        self.status_lbl.config(text="Refreshing package sources and manifests...")
        self._show_floating_toast("Refreshing repository sources...", "i")

        def worker():
            success, msg = self.winget.update_sources()
            if success:
                self.msg_queue.put(("STATUS", "Repository sources updated successfully."))
                self._show_floating_toast("Repository sources up to date", "✓")
            else:
                self.msg_queue.put(("STATUS", f"Source update note: {msg}"))
                self._show_floating_toast("Source check completed", "i")

        threading.Thread(target=worker, daemon=True).start()

    def _poll_queue(self) -> None:
        """Batch-drains messages from worker threads onto the UI thread."""
        try:
            while True:
                msg_type, data = self.msg_queue.get_nowait()
                if msg_type == "STATUS":
                    if self.is_busy:
                        self.scan_animator.update_text(data)
                    else:
                        self.status_lbl.config(text=data)
                elif msg_type == "PROGRESS":
                    self.progress_bar.set_progress(data)
                elif msg_type == "SCAN_COMPLETE":
                    self._on_scan_completed(data)
                elif msg_type == "UPDATE_COMPLETE":
                    self._on_update_completed(data)
                elif msg_type == "CATALOG_RESULTS":
                    if isinstance(data, tuple) and len(data) == 3:
                        items, gen_id, q_term = data
                        if gen_id == self._catalog_search_generation:
                            self._on_catalog_results(items, query=q_term)
                    else:
                        self._on_catalog_results(data)
                elif msg_type == "REFRESH_ITEM":
                    self.table.update_item(data)
                    if self.drawer.current_item and self.drawer.current_item.name == data.name:
                        self.drawer.set_item(data)
                    self._refresh_counts()
                elif msg_type == "ERROR":
                    self.status_lbl.config(text=f"Error: {data}", fg=self.current_theme.accent_crimson)
                    self._show_floating_toast(f"Error: {data}", "✕")
        except queue.Empty:
            pass
        self.after(40, self._poll_queue)

    def _on_sidebar_filter_changed(self, filter_name: str) -> None:
        self.active_filter = filter_name
        if filter_name == "Software Catalog":
            self.lbl_view_title.config(text="Discover & Install Packages")
            if hasattr(self, "diag_banner"):
                self.diag_banner.pack_forget()
            self.lbl_view_subtitle.config(text="Discover, search, and install software from official Windows repositories")
            self.btn_update.config(state="disabled")
            self.btn_update_selected.config(state="disabled")
            self._search_catalog(self.search_query.strip())
        elif filter_name in ("Cannot Update", "Review & cannot update", "Review & issues"):
            self.lbl_view_title.config(text="Review & Issues")
            self.lbl_view_subtitle.config(text="Applications requiring review, publisher variance verification, or repository linking")
            if hasattr(self, "diag_banner"):
                self.diag_banner.pack(fill=tk.X, pady=(0, 8), before=self.table)
            self.apply_filter()
        elif filter_name == "Updates Available":
            self.lbl_view_title.config(text="Updates Available")
            if hasattr(self, "diag_banner"):
                self.diag_banner.pack_forget()
            self.lbl_view_subtitle.config(text="Compatible updates verified against official package repositories")
            self.apply_filter()
        elif filter_name == "Up to Date":
            self.lbl_view_title.config(text="Installed & Current Applications")
            if hasattr(self, "diag_banner"):
                self.diag_banner.pack_forget()
            self.lbl_view_subtitle.config(text="Applications currently running their latest available release")
            self.apply_filter()
        elif filter_name == "Ignored Updates":
            self.lbl_view_title.config(text="Excluded Applications")
            if hasattr(self, "diag_banner"):
                self.diag_banner.pack_forget()
            self.lbl_view_subtitle.config(text="Applications excluded from automated update checks")
            self.apply_filter()
        else:
            self.lbl_view_title.config(text="All Applications")
            if hasattr(self, "diag_banner"):
                self.diag_banner.pack_forget()
            self.lbl_view_subtitle.config(text="All discovered software applications across this computer")
            self.apply_filter()

    def _on_sidebar_search_changed(self, query: str) -> None:
        self.search_query = query
        if self.active_filter == "Software Catalog":
            self._search_catalog(query)
        else:
            self.apply_filter()

    def _on_sidebar_category_changed(self, category: str) -> None:
        self.active_category = category
        self.apply_filter()

    def _on_row_selected(self, item: Optional[ProgramItem]) -> None:
        self.selected_item = item
        self.drawer.set_item(item)

        if self.active_filter == "Software Catalog" and item:
            is_installed = item.installed_version not in ("Not Installed", "None", None, "")
            if is_installed:
                if item.action == UpdateAction.UP_TO_DATE:
                    txt = "Up to date"
                    st = "disabled"
                    bg_c = "#ffffff"
                    fg_c = "#9ca3af"
                else:
                    txt = "Update application"
                    st = "normal"
                    bg_c = "#881337"
                    fg_c = "#ffffff"
            else:
                txt = "Install software"
                st = "normal"
                bg_c = "#881337"
                fg_c = "#ffffff"

            self.drawer.btn_update.config(
                state=st,
                text=txt,
                bg=bg_c,
                fg=fg_c,
            )
            self.btn_update_selected.config(
                state=st,
                text="Install selected" if not is_installed else txt,
                bg=bg_c,
                fg=fg_c,
            )
            return

        if item and (item.can_auto_update() or (item.action == UpdateAction.AVAILABLE and item.is_verified_winget)):
            self.btn_update_selected.config(
                state="normal",
                text="Update selected",
                bg="#881337",
                fg="#ffffff",
            )
        else:
            if item and item.action == UpdateAction.UP_TO_DATE:
                txt = "Up to date"
            elif item and item.is_pinned:
                txt = "Pinned to version"
            elif item and item.action == UpdateAction.EXCLUDED:
                txt = "Excluded"
            elif item and item.action == UpdateAction.SKIPPED_VERSION:
                txt = "Version skipped"
            elif item and item.action == UpdateAction.UNVERIFIED:
                txt = "Verification required"
            else:
                txt = "Update selected"
            dis_bg = "#141d30" if self.current_theme.name == "dark" else "#ffffff"
            dis_fg = "#64748b" if self.current_theme.name == "dark" else "#9ca3af"
            self.btn_update_selected.config(
                state="disabled",
                text=txt,
                bg=dis_bg,
                fg=dis_fg,
                border_color=self.current_theme.border,
            )

        # Update bottom right action pill states with exact matching dynamic labels
        has_sel = (item is not None)
        can_up = bool(item and item.can_auto_update())
        if hasattr(self, "p_btn_exclude") and self.p_btn_exclude:
            is_excl = bool(item and item.action == UpdateAction.EXCLUDED)
            self.p_btn_exclude.config(
                state="normal" if has_sel else "disabled",
                text="Un-exclude" if is_excl else "Exclude",
            )
        if hasattr(self, "p_btn_folder") and self.p_btn_folder:
            has_folder = bool(item and item.install_location and os.path.exists(item.install_location))
            self.p_btn_folder.config(state="normal" if has_folder else "disabled")
        if hasattr(self, "p_btn_copy") and self.p_btn_copy:
            self.p_btn_copy.config(state="normal" if has_sel else "disabled")
        if hasattr(self, "p_btn_pin") and self.p_btn_pin:
            is_pinned = bool(item and item.is_pinned)
            self.p_btn_pin.config(
                state="normal" if has_sel else "disabled",
                text="Unpin" if is_pinned else "Pin",
            )
        if hasattr(self, "p_btn_skip") and self.p_btn_skip:
            is_skipped = bool(item and item.action == UpdateAction.SKIPPED_VERSION)
            self.p_btn_skip.config(
                state="normal" if has_sel else "disabled",
                text="Unskip" if is_skipped else "Skip",
            )
        if hasattr(self, "p_btn_uninstall") and self.p_btn_uninstall:
            self.p_btn_uninstall.config(state="normal" if has_sel else "disabled")
        if hasattr(self, "p_btn_update") and self.p_btn_update:
            up_text = "Update application" if can_up else ("Up to Date" if item and item.action == UpdateAction.UP_TO_DATE else "Update application")
            self.p_btn_update.config(state="normal" if can_up else "disabled", text=up_text)

    def _on_update_selected_clicked(self) -> None:
        sel_items = self.table.get_selected_items()
        if len(sel_items) > 1:
            self._handle_batch_update(sel_items)
        elif self.selected_item:
            self._handle_context_update(self.selected_item)

    def _select_all_updates_clicked(self) -> None:
        """Selects all available updates in the table."""
        self.table.select_updates_only()

    def _on_batch_selected(self, items: List[ProgramItem]) -> None:
        """Invoked when multiple rows or 0 rows are selected in the table."""
        if len(items) > 1:
            self.drawer.pack_forget()
            self.batch_dock.set_selected_items(items)
            self.batch_dock.pack(fill=tk.X, side=tk.BOTTOM)
            up_count = len([i for i in items if i.can_auto_update() or (i.action == UpdateAction.AVAILABLE and i.is_verified_winget)])
            self.btn_update_selected.config(
                state="normal" if up_count > 0 else "disabled",
                text=f"Update ({up_count})",
                bg="#881337" if up_count > 0 else "#ffffff",
                fg="#ffffff" if up_count > 0 else "#9ca3af",
            )
        else:
            self.batch_dock.pack_forget()
            self.drawer.pack(fill=tk.X, side=tk.BOTTOM)
            if len(items) == 1:
                self._on_row_selected(items[0])
            else:
                self._on_row_selected(None)

    def _handle_batch_update(self, items: List[ProgramItem]) -> None:
        """Executes bulk updates for multiple selected items."""
        eligible = [it for it in items if it.can_auto_update() or (it.action == UpdateAction.AVAILABLE and it.is_verified_winget)]
        if not eligible:
            self._show_floating_toast("No eligible updates in current selection", "i")
            return

        dry_run = self.dry_run_var.get()
        mode_str = "Simulation Only (Dry-run)" if dry_run else "Standard Installation"
        msg = (
            f"Ready to update {len(eligible)} selected applications:\n\n"
            + "\n".join(f"• {it.name} ({it.installed_version} → {it.latest_version})" for it in eligible[:6])
            + (f"\n...and {len(eligible) - 6} more." if len(eligible) > 6 else "")
            + f"\n\nExecution Mode: {mode_str}\nProceed with updating {len(eligible)} selected packages?"
        )
        if not messagebox.askyesno("Confirm Batch Update", msg, icon="question", parent=self):
            return

        self._execute_update_queue(eligible, dry_run=dry_run)

    def _handle_batch_allow(self, items: List[ProgramItem]) -> None:
        """Approves and verifies all selected unverified packages."""
        count = 0
        for it in items:
            if it.action == UpdateAction.UNVERIFIED:
                it.is_verified_winget = True
                it.action = UpdateAction.AVAILABLE
                it.unavailability_reason = None
                it.notes = "Approved by user in batch"
                self.table.update_item(it)
                count += 1
        if count > 0:
            self._refresh_counts()
            self.apply_filter()
            self._show_floating_toast(f"Approved {count} packages for updates", "✓")

    def _handle_batch_pin(self, items: List[ProgramItem]) -> None:
        """Pins all selected items so they are preserved at their current version."""
        count = 0
        for it in items:
            self.config.pin_package(it.name, it.installed_version, it.id)
            it.is_pinned = True
            it.pinned_version = it.installed_version
            it.action = UpdateAction.PINNED
            it.notes = f"Pinned to version {it.installed_version}"
            it.unavailability_reason = f"Application is pinned to version {it.installed_version}."
            self.table.update_item(it)
            count += 1
        self._refresh_counts()
        self.apply_filter()
        self._show_floating_toast(f"Pinned {count} packages to current version", "📌")

    def _handle_batch_exclude(self, items: List[ProgramItem]) -> None:
        """Excludes all selected items from automated scans and updates."""
        count = 0
        for it in items:
            self.config.add_exclusion(it.name, reason="Batch excluded by user", package_id=it.id)
            it.action = UpdateAction.EXCLUDED
            it.notes = "Excluded by user"
            it.unavailability_reason = "Application is excluded by user filter rule."
            self.table.update_item(it)
            count += 1
        self._refresh_counts()
        self.apply_filter()
        self._show_floating_toast(f"Excluded {count} packages", "🛡️")

    def _search_catalog(self, query: str) -> None:
        self._catalog_search_generation += 1
        gen_id = self._catalog_search_generation
        q = query.strip()

        # If query is empty, immediately render the curated popular Windows software catalog
        if not q:
            items = get_popular_catalog(self.all_programs)
            self.catalog_items = items
            self.filtered_programs = items
            self.table.populate(items)
            self.lbl_view_subtitle.config(text=f"Curated Popular Windows Catalog ({len(items)} packages)")
            self.status_lbl.config(text=f"Catalog ready: {len(items)} popular packages ready to install.")
            return

        # Immediate fast display of local curated matches
        immediate_matches = search_catalog_packages(q, installed_programs=self.all_programs)
        if immediate_matches:
            self.catalog_items = immediate_matches
            self.filtered_programs = immediate_matches
            self.table.populate(immediate_matches)
            self.lbl_view_subtitle.config(text=f"Found {len(immediate_matches)} packages matching '{q}'...")

        self.status_lbl.config(text=f"Searching repository catalogs for '{q}'...")

        def worker():
            secondary_matches = []
            try:
                secondary_matches = self.source_manager.search_all(q)
            except Exception as e:
                logger.error(f"Catalog search error in source manager: {e}")

            winget_entries = []
            try:
                winget_entries = self.winget.search_packages(q, count=25)
            except Exception as e:
                logger.error(f"Catalog search error in winget: {e}")

            merged_items = search_catalog_packages(
                q,
                winget_entries=winget_entries,
                installed_programs=self.all_programs,
                secondary_items=secondary_matches,
            )

            self.msg_queue.put(("CATALOG_RESULTS", (merged_items, gen_id, q)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_catalog_results(self, items: List[ProgramItem], query: str = "") -> None:
        self.catalog_items = items
        self.apply_filter()
        q_label = f" matching '{query}'" if query else ""
        self.lbl_view_subtitle.config(text=f"Found {len(items)} catalog packages{q_label}")
        self.status_lbl.config(text=f"Catalog ready: {len(items)} packages found.")

    def start_scan(self) -> None:
        if self.is_busy:
            return
        self.is_busy = True
        if hasattr(self, "progress_frame"):
            self.progress_frame.pack(fill=tk.X, before=self.table_container)
        self.btn_scan.config(state="disabled")
        self.btn_update.config(state="disabled")
        self.btn_update_selected.config(state="disabled")
        if hasattr(self, "btn_select_updates"):
            self.btn_select_updates.config(state="disabled")
        self.progress_bar.set_progress(0)
        self.table.show_skeleton()
        self.scan_animator.start("Scanning discovered software inventory...")
        self.lbl_view_subtitle.config(text="Auditing installed packages across system...")
        if hasattr(self, "hud"):
            self.hud.set_mode("scanning")

        threading.Thread(target=self._scan_worker, daemon=True).start()

    def _scan_worker(self) -> None:
        try:
            self.msg_queue.put(("STATUS", "Discovering installed programs across registry and system..."))
            scanner = CompositeScanner(portable_directories=self.config.portable_directories)
            items = scanner.scan_all()

            self.msg_queue.put(("PROGRESS", 40))
            self.msg_queue.put(("STATUS", "Querying Windows Package Manager (winget) repositories..."))
            upgrades = self.winget.get_available_upgrades()

            self.msg_queue.put(("PROGRESS", 70))
            self.msg_queue.put(("STATUS", "Querying installed package registry..."))
            installed = self.winget.get_installed_packages()

            self.msg_queue.put(("PROGRESS", 85))
            self.msg_queue.put(("STATUS", "Correlating software against verified sources and fallbacks..."))
            matcher = PackageMatcher(self.config)
            matched_items = matcher.match_all(items, upgrades, installed)

            # Check pending updates from secondary package managers (Pip, Npm, Scoop, Chocolatey)
            try:
                secondary_updates = self.source_manager.query_all_updates(matched_items)
                for item in matched_items:
                    src = (item.source or "").lower()
                    if src in secondary_updates:
                        pkg_candidates = [
                            item.name.lower(),
                            item.name.replace(f"{src}:", "").strip().lower(),
                            (item.id or "").replace(f"{src}:", "").strip().lower(),
                        ]
                        match_key = next((k for k in pkg_candidates if k in secondary_updates[src]), None)
                        if match_key:
                            info = secondary_updates[src][match_key]
                            target_v = info.get("latest_version") or item.latest_version
                            comp = compare_versions(item.installed_version, target_v)
                            if comp is not None and comp < 0:
                                item.latest_version = target_v
                                item.action = UpdateAction.AVAILABLE
                                item.is_verified_winget = True
                                item.notes = f"Update available via {src.upper()}"
                            elif comp is not None and comp >= 0:
                                item.latest_version = target_v
                                item.action = UpdateAction.UP_TO_DATE
                                item.notes = f"Up to date via {src.upper()} ({item.installed_version})"
            except Exception as e:
                logger.error(f"Error checking secondary package updates: {e}")

            # Pre-evaluate compatibility
            for item in matched_items:
                if item.action == UpdateAction.AVAILABLE:
                    self.checker.check(item)

            self.msg_queue.put(("PROGRESS", 100))
            self.msg_queue.put(("SCAN_COMPLETE", matched_items))
        except Exception as e:
            logger.error(f"Scan worker encountered error: {e}")
            self.msg_queue.put(("ERROR", str(e)))
            self.msg_queue.put(("STATUS", "Scan failed."))

    def _on_scan_completed(self, items: List[ProgramItem]) -> None:
        self.all_programs = items
        self.is_busy = False
        self.btn_scan.config(state="normal", bg="#881337", fg="#ffffff")
        if hasattr(self, "btn_select_updates"):
            self.btn_select_updates.config(state="normal")
        self.scan_animator.stop()
        if hasattr(self, "hud"):
            self.hud.set_mode("idle")

        total = len(items)
        updates = sum(1 for it in items if it.can_auto_update())
        uptodate = sum(1 for it in items if it.action == UpdateAction.UP_TO_DATE)
        ignored = sum(1 for it in items if it.action == UpdateAction.EXCLUDED)
        unverified = sum(
            1 for it in items
            if it.action in (UpdateAction.UNVERIFIED, UpdateAction.NO_SOURCE, UpdateAction.NEWER_THAN_SOURCE)
        )

        # Update sidebar live counts
        # Record to App Update Tracker
        if hasattr(self, "update_tracker"):
            self.update_tracker.track_scan_results(items)

        self.sidebar.update_counts(
            total=total,
            updates=updates,
            uptodate=uptodate,
            ignored=ignored,
            unverified=unverified,
        )

        self.apply_filter()

        if updates > 0:
            self.btn_update.config(state="normal", text=f"Update all eligible ({updates})", bg="#881337", fg="#ffffff")
            self.lbl_view_subtitle.config(text=f"{total} programs scanned • {updates} verified updates ready")
            self.status_lbl.config(text=f"Scan complete: {updates} updates available.")
            self._show_floating_toast(f"Scan complete: {updates} updates ready", "✓")
        else:
            dis_bg = "#141d30" if self.current_theme.name == "dark" else "#fef2f2"
            dis_fg = "#64748b" if self.current_theme.name == "dark" else "#9ca3af"
            self.btn_update.config(state="disabled", text="Update all eligible", bg=dis_bg, fg=dis_fg, border_color=self.current_theme.border)
            self.lbl_view_subtitle.config(text=f"{total} programs scanned • All software up to date")
            self.status_lbl.config(text="Scan complete: All software is up to date.")
            self._show_floating_toast(f"Scan complete: {total} items analyzed", "✓")

    def apply_filter(self) -> None:
        """Filters the items based on sidebar view, search keyword, and category."""
        keyword = self.search_query.strip().lower()
        filter_mode = self.active_filter
        cat_mode = self.active_category

        # Handle Software Catalog mode without polluting from installed programs
        if filter_mode == "Software Catalog":
            raw_catalog = getattr(self, "catalog_items", None)
            if not raw_catalog:
                self.catalog_items = get_popular_catalog(self.all_programs)
                raw_catalog = self.catalog_items

            filtered = []
            terms = keyword.split() if keyword else []
            for item in raw_catalog:
                if terms:
                    searchable = f"{item.name} {item.id or ''} {item.publisher or ''} {item.source or ''} {item.notes or ''}".lower()
                    if not all(tok in searchable for tok in terms):
                        continue

                # Category Filter for catalog
                if cat_mode == "Gaming & Runtimes":
                    lower_search = f"{item.name} {item.id or ''} {item.notes or ''}".lower()
                    if not any(k in lower_search for k in ("runtime", "vcredist", "visual c++", "directx", "openal", "vulkan", ".net desktop", "framework")):
                        continue
                elif cat_mode == "Win32 Applications":
                    if item.package_type not in (PackageType.WIN32_EXE, PackageType.WIN32_MSI):
                        continue
                elif cat_mode == "Microsoft Store / MSIX":
                    if item.package_type != PackageType.STORE_MSIX:
                        continue
                elif cat_mode == "WinGet Packages":
                    if (item.source or "").lower() != "winget" and not item.is_verified_winget:
                        continue
                elif cat_mode == "Python (Pip)":
                    if item.package_type != PackageType.PIP and (item.source or "").lower() != "pip":
                        continue
                elif cat_mode == "Node.js (Npm)":
                    if item.package_type != PackageType.NPM and (item.source or "").lower() != "npm":
                        continue

                filtered.append(item)

            self.filtered_programs = filtered
            self.table.populate(filtered)
            count = len(filtered)
            self.lbl_view_subtitle.config(text=f"Found {count} packages available in catalog")
            return

        filtered = []
        terms = keyword.split() if keyword else []
        for item in self.all_programs:
            # 1. Search Query filter (by all keywords across name, publisher, id, source, version, notes)
            if terms:
                searchable = f"{item.name} {item.id or ''} {item.publisher or ''} {item.source or ''} {item.package_type.value if hasattr(item.package_type, 'value') else ''} {item.installed_version or ''} {item.latest_version or ''} {item.notes or ''}".lower()
                if not all(tok in searchable for tok in terms):
                    continue

            # 2. Sidebar Navigation Filter
            if filter_mode == "Updates Available":
                if item.action != UpdateAction.AVAILABLE:
                    continue
            elif filter_mode in ("Cannot Update", "Review & cannot update", "Review & issues"):
                if item.action not in (
                    UpdateAction.UNVERIFIED,
                    UpdateAction.NO_SOURCE,
                    UpdateAction.NEWER_THAN_SOURCE,
                    UpdateAction.SCAN_FAILED,
                ) and not (item.is_ambiguous or (item.action == UpdateAction.PINNED and not item.can_auto_update())):
                    continue
            elif filter_mode == "Up to Date":
                if item.action != UpdateAction.UP_TO_DATE:
                    continue
            elif filter_mode == "Ignored Updates":
                if item.action != UpdateAction.EXCLUDED:
                    continue

            # 3. Category Filter
            if cat_mode == "Gaming & Runtimes":
                lower_search = f"{item.name} {item.id or ''} {item.notes or ''}".lower()
                if not any(k in lower_search for k in ("runtime", "vcredist", "visual c++", "directx", "openal", "vulkan", ".net desktop", "framework", "redistributable")):
                    continue
            elif cat_mode == "Win32 Applications":
                if item.package_type not in (PackageType.WIN32_EXE, PackageType.WIN32_MSI):
                    continue
            elif cat_mode == "Microsoft Store / MSIX":
                if item.package_type != PackageType.STORE_MSIX:
                    continue
            elif cat_mode == "WinGet Packages":
                if (item.source or "").lower() != "winget" and not item.is_verified_winget:
                    continue
            elif cat_mode == "Scoop Packages":
                if item.package_type != PackageType.SCOOP and (item.source or "").lower() != "scoop":
                    continue
            elif cat_mode == "Chocolatey Packages":
                if item.package_type != PackageType.CHOCOLATEY and (item.source or "").lower() != "chocolatey":
                    continue
            elif cat_mode == "Python (Pip)":
                if item.package_type != PackageType.PIP and (item.source or "").lower() != "pip":
                    continue
            elif cat_mode == "Node.js (Npm)":
                if item.package_type != PackageType.NPM and (item.source or "").lower() != "npm":
                    continue
            elif cat_mode == "Portable Applications":
                if item.package_type != PackageType.PORTABLE:
                    continue
            elif cat_mode == "Drivers & Extensions":
                if item.package_type not in (PackageType.BROWSER_EXTENSION, PackageType.DRIVER):
                    continue

            filtered.append(item)

        self.filtered_programs = filtered
        self.table.populate(filtered)
        count = len(filtered)
        if self.active_filter in ("Cannot Update", "Review & cannot update", "Review & issues"):
            unverified_cnt = sum(1 for it in filtered if it.action == UpdateAction.UNVERIFIED)
            no_source_cnt = sum(1 for it in filtered if it.action == UpdateAction.NO_SOURCE)
            self.lbl_view_subtitle.config(
                text=f"{count} applications cannot update automatically. Inspect diagnostic reasons below or use 1-click unlock actions."
            )
            if hasattr(self, "diag_banner"):
                self.diag_banner.set_stats(count, unverified_cnt, no_source_cnt)
        elif self.active_filter == "Updates Available":
            self.lbl_view_subtitle.config(text=f"{count} verified updates ready for installation")
        elif self.active_filter == "Up to Date":
            self.lbl_view_subtitle.config(text=f"{count} applications verified up to date")
        elif self.active_filter == "Ignored Updates":
            self.lbl_view_subtitle.config(text=f"{count} applications excluded from updates")
        else:
            self.lbl_view_subtitle.config(text=f"Showing {count} of {len(self.all_programs)} discovered programs")

    def start_update_approved(self) -> None:
        """Confirms and executes batch update for all verified compatible packages."""
        if self.is_busy:
            return

        candidates = [item for item in self.all_programs if item.can_auto_update()]
        if not candidates:
            self._show_floating_toast("No packages qualify for automatic update.", "i")
            return

        dry_run = self.dry_run_var.get()
        mode_str = "Simulation Only (Dry-run)" if dry_run else "Standard Installation"

        msg = (
            f"Ready to update {len(candidates)} verified applications.\n\n"
            f"Execution Mode: {mode_str}\n"
            f"Hardware Acceleration: DirectX 12 / DWM Active ({self.primary_gpu.name})\n\n"
            f"Updates will download from official repository sources and install with Administrator privileges.\n\n"
            f"Do you want to proceed with updating all {len(candidates)} packages?"
        )

        if not messagebox.askyesno("Confirm Software Updates", msg, icon="question", parent=self):
            return

        self._execute_update_queue(candidates, dry_run=dry_run)

    def _execute_update_queue(self, target_items: List[ProgramItem], dry_run: bool) -> None:
        """Dispatches an asynchronous batch update queue on background thread."""
        if self.is_busy:
            return

        candidates = [it for it in target_items if it.can_auto_update()]
        if not candidates:
            self._show_floating_toast("No eligible packages to update", "i")
            return

        self.is_busy = True
        self.cancel_update_requested = False
        self.btn_scan.config(state=tk.DISABLED)
        self.btn_update.config(state=tk.DISABLED)
        self.btn_update_selected.config(state=tk.DISABLED)
        if hasattr(self, "btn_select_updates"):
            self.btn_select_updates.config(state=tk.DISABLED)
        self.progress_bar.set_progress(0)
        self.status_lbl.config(text=f"Updating {len(candidates)} packages...")
        if hasattr(self, "hud"):
            self.hud.set_mode("updating")

        # Open modern animated live update modal
        def on_run_in_background():
            self._show_floating_toast(
                f"Updating {len(candidates)} packages in background. Click status bar to view.",
                "⬇",
            )

        def on_cancel_queue():
            self.cancel_update_requested = True
            self._show_floating_toast("Cancelling queue after active installation concludes...", "⏹")

        def on_complete_view_summary():
            if hasattr(self, "_last_update_summary") and self._last_update_summary:
                failed_items = [it for it in self.all_programs if it.outcome == UpdateOutcome.FAILED]
                UpdateSummaryDialog(
                    self,
                    summary=self._last_update_summary,
                    failed_items=failed_items,
                    on_retry=self._retry_failed_updates,
                    theme=self.current_theme,
                )

        try:
            self.live_update_dialog = LiveUpdateProgressDialog(
                self,
                items=candidates,
                theme=self.current_theme,
                on_run_in_background=on_run_in_background,
                on_cancel_queue=on_cancel_queue,
                on_complete_view_summary=on_complete_view_summary,
            )
        except Exception as e:
            logger.warning(f"Failed to create LiveUpdateProgressDialog: {e}")
            self.live_update_dialog = None

        threading.Thread(target=self._update_worker_custom, args=(candidates, dry_run), daemon=True).start()

    def _restore_live_modal_if_background(self, event=None) -> None:
        """Restores the live update modal to foreground when user clicks status bar."""
        if hasattr(self, "live_update_dialog") and self.live_update_dialog and self.live_update_dialog.winfo_exists():
            self.live_update_dialog.restore_from_background()

    def _update_worker(self, dry_run: bool) -> None:
        self._update_worker_custom(self.all_programs, dry_run)

    def _update_worker_custom(self, target_items: List[ProgramItem], dry_run: bool) -> None:
        def on_progress(item: ProgramItem, cur: int, tot: int) -> None:
            pct = int((cur / tot) * 100) if tot > 0 else 0
            self.msg_queue.put(("PROGRESS", pct))
            self.msg_queue.put(("STATUS", f"Updating [{cur}/{tot}]: {item.name}..."))
            if hasattr(self, "live_update_dialog") and self.live_update_dialog and self.live_update_dialog.winfo_exists():
                self.live_update_dialog.notify_package_started(item, cur, tot)

        def on_log(item: ProgramItem, line: str) -> None:
            if hasattr(self, "live_update_dialog") and self.live_update_dialog and self.live_update_dialog.winfo_exists():
                self.live_update_dialog.notify_package_log(item, line)

        def on_item_complete(item: ProgramItem, success: bool, message: str) -> None:
            if hasattr(self, "live_update_dialog") and self.live_update_dialog and self.live_update_dialog.winfo_exists():
                self.live_update_dialog.notify_package_completed(item, success, message)

        def is_cancelled() -> bool:
            return getattr(self, "cancel_update_requested", False)

        try:
            summary = self.engine.execute_batch_update(
                target_items,
                dry_run=dry_run,
                is_scheduled=False,
                create_restore_point=self.restore_point_var.get(),
                auto_close_apps=self.auto_close_var.get(),
                cleanup_after=True,
                progress_callback=on_progress,
                log_callback=on_log,
                item_complete_callback=on_item_complete,
                cancel_check_callback=is_cancelled,
            )
            self._last_update_summary = summary
            if hasattr(self, "live_update_dialog") and self.live_update_dialog and self.live_update_dialog.winfo_exists():
                self.live_update_dialog.notify_queue_finished(summary)
            self.msg_queue.put(("UPDATE_COMPLETE", summary))
        except Exception as e:
            logger.error(f"Update error: {e}")
            self.msg_queue.put(("ERROR", str(e)))

    def _on_update_completed(self, summary: UpdateRunSummary) -> None:
        self.is_busy = False
        self.btn_scan.config(state="normal", bg="#881337", fg="#ffffff")
        if hasattr(self, "btn_select_updates"):
            self.btn_select_updates.config(state="normal")
        if hasattr(self, "hud"):
            self.hud.set_mode("idle")
        self.progress_bar.set_progress(100)

        # Automatic temporary installer cleanup
        if not self.dry_run_var.get():
            bytes_freed, cleanup_msg = DiskCleanupManager.cleanup_temp_and_cache()
            if bytes_freed > 0:
                self._show_floating_toast(cleanup_msg, "✓")

        # Check and update pending reboot badge
        if hasattr(self, "reboot_badge"):
            is_reb, _ = WindowsUpdateManager.is_reboot_pending()
            if is_reb:
                self.reboot_badge.set_badge("⚠️ Restart Required", bg_color="#fef3c7", fg_color="#92400e")
                if not self.reboot_badge.winfo_ismapped():
                    self.reboot_badge.pack(side=tk.LEFT, padx=(12, 0))
            else:
                self.reboot_badge.pack_forget()

        # Refresh table and drawer
        self.apply_filter()
        if self.selected_item:
            self.drawer.set_item(self.selected_item)

        self._refresh_counts()
        self._show_floating_toast(f"Updated {summary.updated_count} packages", "✓")

        # If live_update_dialog was not created or already closed, open UpdateSummaryDialog directly
        if not (hasattr(self, "live_update_dialog") and self.live_update_dialog and self.live_update_dialog.winfo_exists()):
            failed_items = [it for it in self.all_programs if it.outcome == UpdateOutcome.FAILED]
            UpdateSummaryDialog(
                self,
                summary=summary,
                failed_items=failed_items,
                on_retry=self._retry_failed_updates,
                theme=self.current_theme,
            )

    def _retry_failed_updates(self, items: List[ProgramItem]) -> None:
        """Retries installation for failed updates."""
        if items:
            self._execute_update_queue(items, dry_run=self.dry_run_var.get())

    def _handle_row_double_click(self, item: ProgramItem) -> None:
        if item.action == UpdateAction.NEWER_THAN_SOURCE:
            if prompt_downgrade_confirmation(self, item):
                self._run_isolated_single_update(item)
        elif item.action == UpdateAction.VENDOR_FALLBACK:
            if prompt_vendor_installer_confirmation(self, item):
                self._run_isolated_vendor_installer(item)
        elif item.can_auto_update():
            self._handle_context_update(item)
        else:
            self._on_row_selected(item)

    def _handle_context_exclude(self, item: ProgramItem) -> None:
        pat = item.id or item.name
        is_already_ignored = item.action == UpdateAction.EXCLUDED

        if is_already_ignored:
            self.config.remove_exclusion(pat)
            item.action = UpdateAction.NO_SOURCE
            matcher = PackageMatcher(self.config)
            matcher.match_all([item], {}, {})
            self._show_floating_toast(f"Removed '{pat}' from exclusions", "✓")
        else:
            if messagebox.askyesno(
                "Confirm Exclusion",
                f"Exclude '{item.name}' from all future updates?\n"
                f"Package: {pat}",
                parent=self,
            ):
                self.config.add_exclusion(pat, f"Excluded {item.name}")
                item.action = UpdateAction.EXCLUDED
                item.outcome = UpdateOutcome.SKIPPED
                self._show_floating_toast(f"Ignored '{pat}'", "✓")

        self.apply_filter()
        self.drawer.set_item(item)
        self._on_row_selected(item)

    def _handle_context_update(self, item: ProgramItem) -> None:
        if self.active_filter == "Software Catalog":
            self._install_catalog_package(item)
            return

        pkg_id = item.id or item.name

        # Prevent duplicate update requests for the same program
        if pkg_id in self.updating_package_ids:
            self._show_floating_toast(f"Update already in progress for '{item.name}'", "!")
            return

        if not item.id or item.package_type in (PackageType.BROWSER_EXTENSION, PackageType.DRIVER):
            self._show_floating_toast("Item cannot be updated individually via winget.", "i")
            return

        # Pre-condition: Must have a valid available version
        if not item.latest_version or str(item.latest_version).strip() in ("", "—", "None", "Unknown", "Not Installed"):
            self._show_floating_toast(f"No update release available for '{item.name}'", "i")
            return

        if item.installed_version and str(item.latest_version).strip().lower() == str(item.installed_version).strip().lower():
            self._show_floating_toast(f"'{item.name}' is already up to date ({item.installed_version})", "✓")
            return

        # Confirm before starting an update
        if messagebox.askyesno(
            "Confirm Update",
            f"Update '{item.name}' to version {item.latest_version or 'latest'}?\n\n"
            f"Package ID: {item.id}\n"
            f"Source: {item.source or 'winget'}\n\n"
            f"This installer requires Administrator privileges.",
            parent=self,
        ):
            self._run_isolated_single_update(item)

    def _install_catalog_package(self, item: ProgramItem) -> None:
        if not item or not (item.id or item.name):
            return
        pkg_id = item.id or item.name
        source_name = (item.source or "winget").lower()
        if messagebox.askyesno(
            "Confirm Installation",
            f"Install '{item.name}' ({pkg_id}) from source '{source_name.upper()}'?\n\n"
            f"This will download and install the package using the appropriate package manager.",
            parent=self,
        ):
            self.status_lbl.config(text=f"Installing {item.name} via {source_name.upper()}...")
            self._show_floating_toast(f"Installing {item.name}...", "i")
            self.drawer.btn_update.config(state="disabled", text="Installing...")

            def worker():
                dry_run = self.dry_run_var.get()
                if dry_run:
                    success, msg = True, f"[Dry Run] Simulated installation of {item.name} from {source_name.upper()}"
                else:
                    success, msg = self.source_manager.install_package(source_name, pkg_id)
                if success:
                    self._show_floating_toast(f"Successfully installed {item.name}!", "✓")
                    self.start_scan()
                else:
                    self._show_floating_toast(f"Installation failed: {msg}", "✕")
                self.msg_queue.put(("STATUS", f"Install result: {msg}"))

            threading.Thread(target=worker, daemon=True).start()

    def _handle_context_uninstall(self, item: ProgramItem) -> None:
        if not item:
            return
        pkg_id = item.id or item.name
        source_label = (item.source or "winget").upper()
        if messagebox.askyesno(
            "Confirm Uninstallation",
            f"Are you sure you want to uninstall '{item.name}'?\n\n"
            f"Package Identifier: {pkg_id}\n"
            f"Package Manager: {source_label}\n\n"
            f"This will remove the application from your computer.",
            parent=self,
            icon="warning",
        ):
            self.status_lbl.config(text=f"Uninstalling {item.name}...")
            self._show_floating_toast(f"Uninstalling {item.name}...", "i")
            self.drawer.btn_uninstall.config(state="disabled", text="Uninstalling...")

            def worker():
                success, msg = self.source_manager.uninstall_package(item)
                if success:
                    self._show_floating_toast(f"Successfully uninstalled {item.name}", "✓")
                    self.all_programs = [it for it in self.all_programs if it != item]
                    self.msg_queue.put(("STATUS", f"Uninstalled {item.name}"))
                else:
                    self._show_floating_toast(f"Uninstall notice: {msg}", "✕")
                    self.msg_queue.put(("STATUS", f"Uninstall error for {item.name}: {msg}"))
                self.apply_filter()
                self.drawer.set_item(None)

            threading.Thread(target=worker, daemon=True).start()

    def _run_isolated_single_update(self, item: ProgramItem) -> None:
        """Executes single package update via the live animated update modal."""
        if not item.can_auto_update():
            self._show_floating_toast("Package is not eligible for automatic update", "i")
            return
        self._execute_update_queue([item], dry_run=self.dry_run_var.get())

    def _run_isolated_vendor_installer(self, item: ProgramItem) -> None:
        pkg_id = item.id or item.name
        self.updating_package_ids.add(pkg_id)
        self.status_lbl.config(text=f"Installing vendor package for {item.name}...")

        def worker():
            dry_run = self.dry_run_var.get()
            success, msg = self.engine.execute_vendor_installer(item, dry_run=dry_run)
            self.updating_package_ids.discard(pkg_id)

            self.msg_queue.put(("STATUS", f"Vendor install for {item.name}: {msg}"))
            self.apply_filter()
            self.drawer.set_item(item)

        threading.Thread(target=worker, daemon=True).start()

    def _open_bind_source_dialog(self, item: ProgramItem) -> None:
        """Opens dialog to search the repository and bind an unverified or no-source application."""
        BindWingetSourceDialog(
            parent=self,
            item=item,
            config=self.config,
            on_bound=lambda bound_id: self._on_package_source_bound(item, bound_id),
            theme=self.current_theme,
            winget_client=self.winget,
        )

    def _on_package_source_bound(self, item: ProgramItem, bound_id: str) -> None:
        """Handles user binding a program to an official Winget package ID."""
        if not bound_id:
            item.is_user_bound = False
            item.action = UpdateAction.NO_SOURCE
            self.table.update_item(item)
            self.drawer.set_item(item)
            self._refresh_counts()
            return

        self._show_floating_toast(f"Linked '{item.name}' to {bound_id}", "✓")

        def worker():
            details = self.winget.get_package_details(bound_id)
            if details:
                item.latest_version = details.version
                comp = compare_versions(item.installed_version, details.version)
                if comp is not None and comp < 0:
                    item.action = UpdateAction.AVAILABLE
                else:
                    item.action = UpdateAction.UP_TO_DATE
                item.is_verified_winget = True
                item.source = "winget"
                item.unavailability_reason = None
            else:
                item.action = UpdateAction.AVAILABLE
                item.is_verified_winget = True
                item.unavailability_reason = None
            self.msg_queue.put(("REFRESH_ITEM", item))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_allow_unverified(self, item: ProgramItem) -> None:
        """Allows user to explicitly review and approve an unverified or ambiguous package match."""
        if prompt_unverified_allow_confirmation(self, item):
            item.is_verified_winget = True
            item.action = UpdateAction.AVAILABLE
            item.unavailability_reason = None
            item.notes = "Approved by user after review"
            self.table.update_item(item)
            self.drawer.set_item(item)
            self._refresh_counts()
            self._show_floating_toast(f"Approved '{item.name}' for updates", "✓")
            self._handle_context_update(item)

    def _handle_open_website(self, item: ProgramItem) -> None:
        """Opens the official website or search page in the user's browser."""
        import urllib.parse
        import webbrowser
        if item.vendor_installer_url:
            webbrowser.open(item.vendor_installer_url)
            return
        query = f"{item.name} official download"
        if item.publisher:
            query = f"{item.publisher} {item.name} official download"
        url = f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        webbrowser.open(url)
        self._show_floating_toast(f"Opening official download page for {item.name}", "🌐")

    def _refresh_counts(self) -> None:
        """Recalculates summary counts across current inventory and refreshes sidebar badges."""
        total = len(self.all_programs)
        updates = sum(1 for it in self.all_programs if it.can_auto_update())
        uptodate = sum(1 for it in self.all_programs if it.action == UpdateAction.UP_TO_DATE)
        ignored = sum(1 for it in self.all_programs if it.action == UpdateAction.EXCLUDED)
        unverified = sum(
            1 for it in self.all_programs
            if it.action in (UpdateAction.UNVERIFIED, UpdateAction.NO_SOURCE, UpdateAction.NEWER_THAN_SOURCE)
        )
        self.sidebar.update_counts(
            total=total,
            updates=updates,
            uptodate=uptodate,
            ignored=ignored,
            unverified=unverified,
        )

    def _handle_batch_auto_resolve(self) -> None:
        """Auto-approves all unverified or ambiguous packages in the inventory."""
        unverified_items = [
            it for it in self.all_programs
            if it.action == UpdateAction.UNVERIFIED
        ]
        if not unverified_items:
            self._show_floating_toast("No unverified packages awaiting resolution.", "i")
            return

        resolved_count = 0
        for it in unverified_items:
            it.is_verified_winget = True
            it.action = UpdateAction.AVAILABLE
            it.unavailability_reason = None
            it.notes = "Auto-approved closest matching package"
            self.table.update_item(it)
            resolved_count += 1

        self._refresh_counts()
        self.apply_filter()
        self._show_floating_toast(f"Auto-approved {resolved_count} applications for updates!", "✓")

    def _open_cannot_update_help(self) -> None:
        """Opens the diagnostic educational guide dialog."""
        dlg = CannotUpdateHelpDialog(self, theme=self.current_theme)
        self.wait_window(dlg)

    def _export_report_dialog(self) -> None:
        if not self.all_programs:
            self._show_floating_toast("No inventory data to export. Please run a scan first.", "i")
            return

        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Software Inventory & Setup Scripts",
            defaultextension=".html",
            filetypes=[
                ("Interactive HTML Audit Report (*.html)", "*.html"),
                ("Automated PC Setup Script (*.bat)", "*.bat"),
                ("PowerShell Setup Script (*.ps1)", "*.ps1"),
                ("CSV Spreadsheet (*.csv)", "*.csv"),
                ("JSON Data File (*.json)", "*.json"),
            ],
        )
        if not file_path:
            return

        try:
            lower = file_path.lower()
            if lower.endswith(".html"):
                html_content = ReportGenerator.generate_html_report(self.all_programs, app_version="2.3.0")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
            elif lower.endswith(".bat"):
                bat_content = ReportGenerator.generate_batch_script(self.all_programs)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(bat_content)
            elif lower.endswith(".ps1"):
                ps1_content = ReportGenerator.generate_ps1_script(self.all_programs)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(ps1_content)
            elif lower.endswith(".json"):
                data = [
                    {
                        "name": it.name,
                        "id": it.id,
                        "installed_version": it.installed_version,
                        "latest_version": it.latest_version,
                        "status": it.action.value,
                        "source": it.source,
                        "install_location": it.install_location,
                        "notes": it.notes,
                    }
                    for it in self.all_programs
                ]
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            else:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Name", "Current Version", "Latest Version", "Status", "Package ID", "Source", "Location", "Notes"])
                    for it in self.all_programs:
                        writer.writerow([
                            it.name,
                            it.installed_version,
                            it.latest_version or "",
                            it.action.value,
                            it.id or "",
                            it.source or "",
                            it.install_location or "",
                            it.notes or "",
                        ])
            self._show_floating_toast(f"Saved: {os.path.basename(file_path)}", "✓")
        except Exception as e:
            self._show_floating_toast(f"Export error: {e}", "✕")

    def _open_exclusions(self) -> None:
        dlg = ExclusionManagerDialog(self, self.config, on_change=self.apply_filter, theme=self.current_theme)
        self.wait_window(dlg)
        matcher = PackageMatcher(self.config)
        matcher.match_all(self.all_programs, {}, {})
        self.apply_filter()

    _open_exclusions_dialog = _open_exclusions

    def _open_schedule(self) -> None:
        dlg = ScheduleConfigDialog(self, self.scheduler, theme=self.current_theme)
        self.wait_window(dlg)

    def _handle_pin_item(self, item: ProgramItem) -> None:
        """Toggles pinning an application to its current installed version."""
        if item.is_pinned:
            self.config.unpin_package(item.name)
            if item.id:
                self.config.unpin_package(item.id)
            item.is_pinned = False
            item.pinned_version = None
            item.action = UpdateAction.AVAILABLE if item.latest_version and item.latest_version != item.installed_version else UpdateAction.UP_TO_DATE
            item.unavailability_reason = None
            self._show_floating_toast(f"Unpinned '{item.name}'", "✓")
        else:
            ver = item.installed_version or "1.0"
            self.config.pin_package(item.name, ver)
            if item.id:
                self.config.pin_package(item.id, ver)
            item.is_pinned = True
            item.pinned_version = ver
            item.action = UpdateAction.PINNED
            item.unavailability_reason = f"Application is pinned to version {ver}."
            self._show_floating_toast(f"Pinned '{item.name}' to version {ver}", "📌")

        self.table.update_item(item)
        self.drawer.set_item(item)
        self._on_row_selected(item)
        self._refresh_counts()

    def _handle_skip_version(self, item: ProgramItem) -> None:
        """Toggles skipping a specific release version for an application."""
        if item.action == UpdateAction.SKIPPED_VERSION:
            self.config.unskip_version(item.name)
            if item.id:
                self.config.unskip_version(item.id)
            item.action = UpdateAction.AVAILABLE
            item.skipped_version = None
            item.unavailability_reason = None
            self._show_floating_toast(f"Restored update notifications for '{item.name}'", "✓")
        else:
            ver_to_skip = item.latest_version
            if not ver_to_skip:
                return
            self.config.skip_version(item.name, ver_to_skip)
            if item.id:
                self.config.skip_version(item.id, ver_to_skip)
            item.action = UpdateAction.SKIPPED_VERSION
            item.skipped_version = ver_to_skip
            item.unavailability_reason = f"Release {ver_to_skip} was skipped by user."
            self._show_floating_toast(f"Skipped release {ver_to_skip} for '{item.name}'", "⏭️")

        self.table.update_item(item)
        self.drawer.set_item(item)
        self._on_row_selected(item)
        self._refresh_counts()

    def _export_software_backup(self) -> None:
        """Exports the PC software stack to a portable Winget-compatible backup manifest."""
        file_path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Machine Software Backup Manifest",
            initialfile="winget-software-backup.json",
            defaultextension=".json",
            filetypes=[("Winget Package Manifest (*.json)", "*.json")],
        )
        if not file_path:
            return

        self.status_lbl.config(text="Exporting software backup manifest...")
        self._show_floating_toast("Generating software stack backup...", "i")

        def worker():
            success, msg = self.winget.export_software_manifest(file_path, include_versions=True)
            if success:
                self._show_floating_toast(f"Backup manifest saved: {os.path.basename(file_path)}", "✓")
                self.msg_queue.put(("STATUS", f"Export completed: {os.path.basename(file_path)}"))
            else:
                self._show_floating_toast(f"Export note: {msg}", "i")
                self.msg_queue.put(("STATUS", f"Export notice: {msg}"))

        threading.Thread(target=worker, daemon=True).start()

    def _import_software_backup(self) -> None:
        """Restores and provisions a software stack on this PC from a backup manifest."""
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Select Software Backup Manifest to Restore",
            filetypes=[("Winget Package Manifest (*.json)", "*.json"), ("All Files (*.*)", "*.*")],
        )
        if not file_path:
            return

        if not messagebox.askyesno(
            "Confirm Software Stack Restoration",
            f"Do you want to restore and install software packages listed in:\n{os.path.basename(file_path)}?\n\n"
            "This will download and install the verified packages using Windows Package Manager.",
            parent=self,
            icon="question",
        ):
            return

        self.status_lbl.config(text=f"Restoring software stack from {os.path.basename(file_path)}...")
        self._show_floating_toast("Restoring software stack in background...", "i")

        def worker():
            success, msg = self.winget.import_software_manifest(file_path, ignore_unavailable=True)
            if success:
                self._show_floating_toast("Software stack restored successfully!", "✓")
                self.msg_queue.put(("STATUS", "Restoration complete."))
                self._start_scan_async()
            else:
                self._show_floating_toast(f"Import note: {msg}", "i")
                self.msg_queue.put(("STATUS", f"Import note: {msg}"))

        threading.Thread(target=worker, daemon=True).start()

    def _shortcut_focus_search(self) -> str:
        """Focuses the sidebar search input via shortcut key (Ctrl+F or /)."""
        entry = getattr(self.sidebar, "search_entry", None) or getattr(self.sidebar, "entry_search", None)
        if entry:
            entry.focus_set()
            entry.select_range(0, tk.END)
            self._show_floating_toast("Quick search active (Type to filter)", "🔍")
        return "break"


    def _ensure_uninstaller_extracted(self) -> None:
        """Extracts bundled uninstaller next to executable and registers in Windows Settings."""
        try:
            if hasattr(sys, "frozen"):
                app_dir = Path(sys.executable).resolve().parent
                uninstaller_target = app_dir / "Uninstall.exe"

                # Check if bundled in PyInstaller MEIPASS
                meipass = getattr(sys, "_MEIPASS", None)
                if meipass:
                    bundled_uninstaller = Path(meipass) / "Uninstall.exe"
                    if bundled_uninstaller.exists() and not uninstaller_target.exists():
                        import shutil
                        shutil.copy2(bundled_uninstaller, uninstaller_target)
                        logger.info(f"Extracted bundled Uninstall.exe to {uninstaller_target}")

                from winget_updater import __version__
                Uninstaller.register_in_windows_registry(
                    install_dir=app_dir,
                    version=__version__,
                    uninstall_exe_path=uninstaller_target if uninstaller_target.exists() else None,
                )
        except Exception as e:
            logger.debug(f"Error in uninstaller registration: {e}")

    def _check_app_updates_async(self, force: bool = False) -> None:
        """Checks GitHub releases in background and notifies user if an update is available."""
        if hasattr(self, "app_updater"):
            self.app_updater.check_in_background(self._on_app_update_result, force=force)

    def _on_app_update_result(self, result: dict) -> None:
        """Callback executed when GitHub release query completes."""
        if result and result.get("update_available"):
            self.after(0, lambda: self._show_app_update_banner(result))

    def _show_app_update_banner(self, result: dict) -> None:
        """Surfaces the update notification banner above the table."""
        if hasattr(self, "app_update_banner"):
            ver = result.get("latest_version", "latest")
            url = result.get("download_url") or result.get("html_url", "")
            self.app_update_banner.set_update_info(ver, url)
            self.app_update_banner.pack(fill=tk.X, pady=(0, 8), before=self.table)
            self._show_floating_toast(f"⚡ Winget Updater v{ver} is available!", icon="⚡")

    def _handle_app_update_download(self, url: str) -> None:
        """Opens the GitHub release page or direct download link."""
        import webbrowser
        target_url = url or "https://github.com/rupom787/winget-updater/releases/latest"
        webbrowser.open(target_url)
        self._show_floating_toast("Opening GitHub release page in your browser...", icon="🌐")

    def _handle_app_update_dismiss(self) -> None:
        """Dismisses the update banner."""
        if hasattr(self, "app_update_banner"):
            self.app_update_banner.pack_forget()
