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
from typing import List, Optional, Set
from winget_updater.adapters import SourceManager
from winget_updater.compatibility.checker import CompatibilityChecker
from winget_updater.compatibility.system_info import SystemInfoProvider
from winget_updater.config import ConfigManager
from winget_updater.discovery.composite import CompositeScanner
from winget_updater.engine.cleanup import DiskCleanupManager
from winget_updater.engine.process_lock import ProcessLockDetector
from winget_updater.engine.restore_point import RestorePointManager
from winget_updater.engine.scheduler import SchedulerManager
from winget_updater.engine.state_manager import StateManager
from winget_updater.engine.tracker import UpdateTracker
from winget_updater.engine.updater import UpdateEngine, UpdateRunSummary
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
    ExclusionManagerDialog,
    ScheduleConfigDialog,
    SettingsDialog,
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

        # Apply native Windows 11 rounded window borders and titlebar styling
        try:
            apply_native_window_styling(self)
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

        # Core services
        self.config = config_manager or ConfigManager()
        self.current_theme: ThemeColors = get_theme(getattr(self.config, "theme", "light"))
        self.typography: Typography = get_typography(getattr(self.config, "font_scale", "normal"))
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
        FluentFloatingToast.show(self, text=text, icon=icon, duration_ms=2800)
        if hasattr(self, "status_lbl"):
            self.status_lbl.config(text=text)

    def _build_layout(self) -> None:
        self.configure(bg=self.current_theme.bg_root)

        # 1. Top Title Bar Frame
        self.top_bar = tk.Frame(self, bg="#ffffff", padx=18, pady=8, highlightbackground="#f3d5d9", highlightthickness=1)
        self.top_bar.pack(fill=tk.X)

        from winget_updater.engine.gpu import GpuAccelerationManager
        self.primary_gpu = GpuAccelerationManager.get_primary_gpu()
        gpu_display = self.primary_gpu.name
        if len(gpu_display) > 28:
            gpu_display = gpu_display.replace("NVIDIA ", "").replace("Graphics", "").strip()

        # 1. Top Right Controls (pack right first to guarantee visibility)
        self.top_controls = tk.Frame(self.top_bar, bg="#ffffff")
        self.top_controls.pack(side=tk.RIGHT, padx=(0, 2))

        self.btn_restore = RoundedButton(
            self.top_controls,
            text="Restore",
            command=self._import_software_backup,
            bg_color="#f8fafc",
            fg_color="#334155",
            hover_bg="#eff6ff",
            border_color="#e2e8f0",
            radius=6,
            height=28,
            font=("Segoe UI", 8),
            padding=(6, 4),
        )
        self.btn_restore.pack(side=tk.LEFT, padx=(2, 0))

        self.btn_backup = RoundedButton(
            self.top_controls,
            text="Backup",
            command=self._export_software_backup,
            bg_color="#f8fafc",
            fg_color="#334155",
            hover_bg="#ecfdf5",
            border_color="#e2e8f0",
            radius=6,
            height=28,
            font=("Segoe UI", 8),
            padding=(6, 4),
        )
        self.btn_backup.pack(side=tk.LEFT, padx=(2, 0))

        self.btn_sources = RoundedButton(
            self.top_controls,
            text="Refresh",
            command=self._refresh_sources_dialog,
            bg_color="#f8fafc",
            fg_color="#334155",
            hover_bg="#f1f5f9",
            border_color="#e2e8f0",
            radius=6,
            height=28,
            font=("Segoe UI", 8),
            padding=(6, 4),
        )
        self.btn_sources.pack(side=tk.LEFT, padx=(2, 0))

        self.btn_exclusions = RoundedButton(
            self.top_controls,
            text="Exclusions",
            command=self._open_exclusions,
            bg_color="#f8fafc",
            fg_color="#334155",
            hover_bg="#f1f5f9",
            border_color="#e2e8f0",
            radius=6,
            height=28,
            font=("Segoe UI", 8),
            padding=(6, 4),
        )
        self.btn_exclusions.pack(side=tk.LEFT, padx=(2, 0))

        self.btn_schedule = RoundedButton(
            self.top_controls,
            text="🕒 Schedule",
            command=self._open_schedule,
            bg_color="#f8fafc",
            fg_color="#334155",
            hover_bg="#f1f5f9",
            border_color="#e2e8f0",
            radius=6,
            height=28,
            font=("Segoe UI", 8),
            padding=(6, 4),
        )
        self.btn_schedule.pack(side=tk.LEFT, padx=(2, 0))

        self.btn_settings = RoundedButton(
            self.top_controls,
            text="⚙️ Settings",
            command=self._open_settings,
            bg_color="#f8fafc",
            fg_color="#334155",
            hover_bg="#f1f5f9",
            border_color="#e2e8f0",
            radius=6,
            height=28,
            font=("Segoe UI", 8, "bold"),
            padding=(6, 4),
        )
        self.btn_settings.pack(side=tk.LEFT, padx=(2, 0))

        self.btn_export = RoundedButton(
            self.top_controls,
            text="Export",
            command=self._export_report_dialog,
            bg_color="#f8fafc",
            fg_color="#334155",
            hover_bg="#f1f5f9",
            border_color="#e2e8f0",
            radius=6,
            height=28,
            font=("Segoe UI", 8),
            padding=(6, 4),
        )
        self.btn_export.pack(side=tk.LEFT, padx=(2, 0))

        # iOS-style Light / Dark Mode Switch
        self.theme_box = tk.Frame(self.top_controls, bg="#ffffff")
        self.theme_box.pack(side=tk.LEFT, padx=(6, 0))

        self.lbl_theme_mode = tk.Label(
            self.theme_box,
            text="Theme",
            bg="#ffffff",
            fg="#64748b",
            font=("Segoe UI", 8),
        )
        self.lbl_theme_mode.pack(side=tk.LEFT, padx=(0, 4))

        self.sw_theme = IOSStyleToggleSwitch(
            self.theme_box,
            variable=self.theme_var,
            command=self._on_theme_switch_toggled,
            width=38,
            height=20,
            on_color="#881337",
            off_color="#334155",
            parent_bg="#ffffff",
        )
        self.sw_theme.pack(side=tk.RIGHT)

        # 2. Top Left Brand & Status
        self.lbl_app_title = tk.Label(
            self.top_bar,
            text="Software & Package Updater",
            bg="#ffffff",
            fg="#881337",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        self.lbl_app_title.pack(side=tk.LEFT)

        self.lbl_app_sub = tk.Label(
            self.top_bar,
            text="  •  Win11",
            bg="#ffffff",
            fg="#64748b",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.lbl_app_sub.pack(side=tk.LEFT)

        # Frosted Glass Telemetry HUD
        self.hud = GlassyTelemetryHUD(self.top_bar, sys_info=self.sys_info, gpu_name=self.primary_gpu.name)
        self.hud.pack(side=tk.LEFT, padx=(12, 0))

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

        # 2. Main 3-Column Container
        self.main_body = tk.Frame(self, bg="#ffffff")
        self.main_body.pack(fill=tk.BOTH, expand=True)

        # Left Column: Sidebar Navigation (width 250)
        self.sidebar = SidebarNavigation(
            self.main_body,
            on_filter_changed=self._on_sidebar_filter_changed,
            on_search_changed=self._on_sidebar_search_changed,
            on_category_changed=self._on_sidebar_category_changed,
            on_open_tracker=self._open_update_tracker,
            sys_info=self.sys_info,
        )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        # Right Column: Action & Controls Sidebar (width 245)
        self.right_action_sidebar = tk.Frame(
            self.main_body,
            width=245,
            bg="#ffffff",
            padx=12,
            pady=12,
            highlightbackground="#f3d5d9",
            highlightthickness=1,
        )
        self.right_action_sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        self.right_action_sidebar.pack_propagate(False)

        # 2a. Top Section: iOS Switches Box
        self.switches_card = tk.Frame(
            self.right_action_sidebar,
            bg="#ffffff",
            padx=6,
            pady=6,
            highlightbackground="#f3d5d9",
            highlightthickness=1,
        )
        self.switches_card.pack(fill=tk.X, pady=(0, 10))

        # Row 1: Auto-close running
        self.row_sw1 = tk.Frame(self.switches_card, bg="#ffffff")
        self.row_sw1.pack(fill=tk.X, pady=3)
        self.lbl_sw_auto = tk.Label(self.row_sw1, text="Auto-close running", bg="#ffffff", fg="#334155", font=("Segoe UI", 8), anchor="w")
        self.lbl_sw_auto.pack(side=tk.LEFT)
        self.sw_auto_close = IOSStyleToggleSwitch(self.row_sw1, variable=self.auto_close_var, width=36, height=18, parent_bg="#ffffff")
        self.sw_auto_close.pack(side=tk.RIGHT)

        # Row 2: Create restore point
        self.row_sw2 = tk.Frame(self.switches_card, bg="#ffffff")
        self.row_sw2.pack(fill=tk.X, pady=3)
        self.lbl_sw_restore = tk.Label(self.row_sw2, text="Create restore point", bg="#ffffff", fg="#334155", font=("Segoe UI", 8), anchor="w")
        self.lbl_sw_restore.pack(side=tk.LEFT)
        self.sw_restore_point = IOSStyleToggleSwitch(self.row_sw2, variable=self.restore_point_var, width=36, height=18, parent_bg="#ffffff")
        self.sw_restore_point.pack(side=tk.RIGHT)

        # Row 3: Dry run (simulate only)
        self.row_sw3 = tk.Frame(self.switches_card, bg="#ffffff")
        self.row_sw3.pack(fill=tk.X, pady=3)
        self.lbl_sw_dry = tk.Label(self.row_sw3, text="Dry run (simulate only)", bg="#ffffff", fg="#334155", font=("Segoe UI", 8), anchor="w")
        self.lbl_sw_dry.pack(side=tk.LEFT)
        self.sw_dry_run = IOSStyleToggleSwitch(self.row_sw3, variable=self.dry_run_var, width=36, height=18, parent_bg="#ffffff")
        self.sw_dry_run.pack(side=tk.RIGHT)

        # Hidden Checkbuttons for backwards compatibility with tests
        self.chk_dry_run = tk.Checkbutton(self.right_action_sidebar, variable=self.dry_run_var)
        self.chk_restore_point = tk.Checkbutton(self.right_action_sidebar, variable=self.restore_point_var)
        self.chk_auto_close = tk.Checkbutton(self.right_action_sidebar, variable=self.auto_close_var)

        # 2b. Middle Section: Action Deck
        self.actions_card = tk.Frame(self.right_action_sidebar, bg="#ffffff")
        self.actions_card.pack(fill=tk.X, pady=(0, 10))

        self.lbl_action_deck = tk.Label(
            self.actions_card,
            text="Select updates",
            bg="#ffffff",
            fg="#64748b",
            font=("Segoe UI", 8, "bold"),
            anchor="w",
        )
        self.lbl_action_deck.pack(fill=tk.X, pady=(0, 4))

        self.btn_select_updates = RoundedButton(
            self.actions_card,
            text="Select updates",
            command=self._select_all_updates_clicked,
            bg_color="#ffffff",
            fg_color="#334155",
            hover_bg="#f1f5f9",
            border_color="#cbd5e1",
            radius=8,
            height=32,
            font=("Segoe UI", 9),
            padding=(8, 4),
        )

        self.btn_update_selected = RoundedButton(
            self.actions_card,
            text="Update selected",
            command=self._on_update_selected_clicked,
            bg_color="#ffffff",
            fg_color="#64748b",
            hover_bg="#f1f5f9",
            border_color="#e2e8f0",
            radius=8,
            height=32,
            font=("Segoe UI", 9),
            padding=(8, 4),
        )
        self.btn_update_selected.config(state="disabled")
        self.btn_update_selected.pack(fill=tk.X, pady=(0, 5))

        self.btn_update = RoundedButton(
            self.actions_card,
            text="Update all eligible",
            command=self.start_update_approved,
            bg_color="#881337",
            fg_color="#ffffff",
            hover_bg="#9f1239",
            radius=8,
            height=32,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 4),
        )
        self.btn_update.config(state="disabled")
        self.btn_update.pack(fill=tk.X, pady=(0, 5))

        self.btn_complete_system = RoundedButton(
            self.actions_card,
            text="⚡ Complete system update",
            command=self._open_complete_system_update,
            bg_color="#9f1239",
            fg_color="#ffffff",
            hover_bg="#be123c",
            radius=8,
            height=32,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 4),
        )
        self.btn_complete_system.pack(fill=tk.X, pady=(0, 5))

        self.btn_scan = RoundedButton(
            self.actions_card,
            text="Check for updates",
            command=self.start_scan,
            bg_color="#be123c",
            fg_color="#ffffff",
            hover_bg="#e11d48",
            radius=8,
            height=32,
            font=("Segoe UI", 9, "bold"),
            padding=(8, 4),
        )
        self.btn_scan.pack(fill=tk.X)

        # 2c. Bottom Section: Selected App Action Pills
        self.right_selected_card = tk.Frame(self.right_action_sidebar, bg="#ffffff")
        self.right_selected_card.pack(side=tk.BOTTOM, fill=tk.X)

        self.row_p1 = tk.Frame(self.right_selected_card, bg="#ffffff")
        self.row_p1.pack(fill=tk.X, pady=2)
        self.p_btn_exclude = RoundedButton(self.row_p1, text="Exclude", command=lambda: self._handle_context_exclude(self.selected_item) if self.selected_item else None, radius=6, height=24, font=("Segoe UI", 8), bg_color="#ffffff", fg_color="#334155", border_color="#e2e8f0")
        self.p_btn_exclude.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        self.p_btn_folder = RoundedButton(self.row_p1, text="Folder", command=lambda: self._open_app_folder(self.selected_item), radius=6, height=24, font=("Segoe UI", 8), bg_color="#ffffff", fg_color="#334155", border_color="#e2e8f0")
        self.p_btn_folder.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        self.row_p2 = tk.Frame(self.right_selected_card, bg="#ffffff")
        self.row_p2.pack(fill=tk.X, pady=2)
        self.p_btn_copy = RoundedButton(self.row_p2, text="Copy ID", command=lambda: self._copy_package_id(self.selected_item), radius=6, height=24, font=("Segoe UI", 8), bg_color="#ffffff", fg_color="#334155", border_color="#e2e8f0")
        self.p_btn_copy.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        self.p_btn_pin = RoundedButton(self.row_p2, text="Pin", command=lambda: self._handle_pin_item(self.selected_item) if self.selected_item else None, radius=6, height=24, font=("Segoe UI", 8), bg_color="#ffffff", fg_color="#334155", border_color="#e2e8f0")
        self.p_btn_pin.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 2))
        self.p_btn_skip = RoundedButton(self.row_p2, text="Skip", command=lambda: self._handle_skip_version(self.selected_item) if self.selected_item else None, radius=6, height=24, font=("Segoe UI", 8), bg_color="#ffffff", fg_color="#334155", border_color="#e2e8f0")
        self.p_btn_skip.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        self.row_p3 = tk.Frame(self.right_selected_card, bg="#ffffff")
        self.row_p3.pack(fill=tk.X, pady=(3, 0))
        self.p_btn_uninstall = RoundedButton(self.row_p3, text="Uninstall", command=lambda: self._handle_context_uninstall(self.selected_item) if self.selected_item else None, radius=6, height=26, font=("Segoe UI", 8), bg_color="#fef2f2", fg_color="#dc2626")
        self.p_btn_uninstall.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        self.p_btn_update = RoundedButton(self.row_p3, text="Update App", command=lambda: self._handle_context_update(self.selected_item) if self.selected_item else None, radius=6, height=26, font=("Segoe UI", 8, "bold"), bg_color="#881337", fg_color="#ffffff")
        self.p_btn_update.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        # Center Column: Main Content Container (expands)
        self.right_container = tk.Frame(self.main_body, bg="#ffffff")
        self.right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 3. Center Title Header Bar above the table
        self.action_header = tk.Frame(
            self.right_container,
            bg="#ffffff",
            padx=16,
            pady=10,
            highlightbackground="#f3d5d9",
            highlightthickness=1,
        )
        self.action_header.pack(fill=tk.X)

        self.header_title_box = tk.Frame(self.action_header, bg="#ffffff")
        self.header_title_box.pack(side=tk.LEFT)

        self.lbl_view_title = tk.Label(
            self.header_title_box,
            text="All Software",
            bg="#ffffff",
            fg="#111827",
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        )
        self.lbl_view_title.pack(anchor=tk.W)

        self.lbl_view_subtitle = tk.Label(
            self.header_title_box,
            text="Loading discovered software...",
            bg="#ffffff",
            fg="#6b7280",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.lbl_view_subtitle.pack(anchor=tk.W, pady=(2, 0))

        self.header_btn_box = tk.Frame(self.action_header, bg="#ffffff")
        self.header_btn_box.pack(side=tk.RIGHT)

        # 4. Progress bar frame for scanning / updates
        self.progress_frame = tk.Frame(self.right_container, bg="#ffffff", padx=16, pady=2)
        self.progress_frame.pack(fill=tk.X)

        self.status_lbl = tk.Label(
            self.progress_frame,
            text="Ready.",
            bg="#ffffff",
            fg="#6b7280",
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
            bg="#ffffff",
            fg="#059669",
            font=("Segoe UI", 8, "bold"),
            anchor="e",
        )
        self.lbl_gpu_badge.pack(side=tk.RIGHT, padx=(0, 12))

        # Animated status pulse
        self.scan_animator = ScanningPulseAnimator(self.status_lbl, "Scanning software and repositories...")

        # 5. Installed-Software Table (4 Columns: Name, Current Version, Latest Version, Status)
        self.table_container = tk.Frame(self.right_container, bg="#ffffff", padx=16, pady=4)
        self.table_container.pack(fill=tk.BOTH, expand=True)

        # Frosted glass banner for review & unverified software
        self.diag_banner = DiagnosticsResolutionBanner(
            self.table_container,
            on_auto_resolve_all=self._handle_batch_auto_resolve,
            on_open_help=self._open_cannot_update_help,
        )
        self.diag_banner.pack_forget()

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

        # Backwards-compatibility helper references
        self.inspector = self.drawer
        self.elevation_banner = ElevationBanner(self.main_body, sys_info=self.sys_info)
        self.elevation_banner.pack_forget()
        self.hero_scene = SoftwareEngineeringHeroScene(self.main_body, height=1)
        self.hero_scene.pack_forget()
        self.timeline = TimelinePipelineHUD(self.main_body, height=1)
        self.timeline.pack_forget()
        self.laser_header = CyberLaserHeaderCanvas(self.main_body, height=1)
        self.laser_header.pack_forget()
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
        self.bind("<Control-Shift-U>", lambda e: self._open_complete_system_update())
        self.bind("<Control-Shift-u>", lambda e: self._open_complete_system_update())

        self.set_theme(self.current_theme.name)

    def set_theme(self, mode: str) -> None:
        """Sets the application theme to either 'light' or 'dark' and updates all UI modules."""
        self.current_theme = get_theme(mode)
        t = self.current_theme

        self.configure(bg=t.bg_root)
        self.top_bar.config(bg=t.bg_header, highlightbackground=t.border)
        self.lbl_app_title.config(bg=t.bg_header, fg=t.accent_burgundy)
        self.lbl_app_sub.config(bg=t.bg_header, fg=t.fg_muted)
        self.top_controls.config(bg=t.bg_header)

        btn_txt = "Light mode" if t.name == "dark" else "Dark mode"
        self.btn_theme.config(text=btn_txt, bg=t.bg_button, fg=t.fg_primary)
        self.btn_schedule.config(bg=t.bg_button, fg=t.fg_primary)
        self.btn_exclusions.config(bg=t.bg_button, fg=t.fg_primary)
        if hasattr(self, "btn_sources"):
            self.btn_sources.config(bg=t.bg_button, fg=t.fg_primary)
        if hasattr(self, "btn_backup"):
            self.btn_backup.config(bg=t.bg_button, fg=t.fg_primary)
        if hasattr(self, "btn_restore"):
            self.btn_restore.config(bg=t.bg_button, fg=t.fg_primary)
        self.btn_export.config(bg=t.bg_button, fg=t.fg_primary)

        self.main_body.config(bg=t.bg_root)
        self.right_container.config(bg=t.bg_root)
        self.action_header.config(bg=t.bg_card, highlightbackground=t.border)
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
        if hasattr(self, "btn_select_updates"):
            self.btn_select_updates.config(bg=t.bg_button, fg=t.fg_primary)
        if hasattr(self, "btn_complete_system"):
            self.btn_complete_system.config(bg=t.accent_burgundy, fg="#ffffff")
        if hasattr(self, "reboot_badge"):
            is_reb, _ = WindowsUpdateManager.is_reboot_pending()
            if is_reb:
                self.reboot_badge.set_badge("⚠️ Restart Required", bg_color="#fef3c7", fg_color="#92400e")

        # Update Right Action Sidebar
        if hasattr(self, "right_action_sidebar"):
            self.right_action_sidebar.config(bg=t.bg_card, highlightbackground=t.border)
        if hasattr(self, "switches_card"):
            self.switches_card.config(bg=t.bg_card, highlightbackground=t.border)
            for r in (getattr(self, "row_sw1", None), getattr(self, "row_sw2", None), getattr(self, "row_sw3", None)):
                if r:
                    r.config(bg=t.bg_card)
            for lbl in (getattr(self, "lbl_sw_auto", None), getattr(self, "lbl_sw_restore", None), getattr(self, "lbl_sw_dry", None)):
                if lbl:
                    lbl.config(bg=t.bg_card, fg=t.fg_primary)
            if hasattr(self, "sw_auto_close"):
                self.sw_auto_close.set_colors(on_color=t.accent_burgundy, off_color="#334155" if t.name == "dark" else "#cbd5e1", parent_bg=t.bg_card)
            if hasattr(self, "sw_restore_point"):
                self.sw_restore_point.set_colors(on_color=t.accent_burgundy, off_color="#334155" if t.name == "dark" else "#cbd5e1", parent_bg=t.bg_card)
            if hasattr(self, "sw_dry_run"):
                self.sw_dry_run.set_colors(on_color=t.accent_burgundy, off_color="#334155" if t.name == "dark" else "#cbd5e1", parent_bg=t.bg_card)

        if hasattr(self, "actions_card"):
            self.actions_card.config(bg=t.bg_card)
        if hasattr(self, "lbl_action_deck"):
            self.lbl_action_deck.config(bg=t.bg_card, fg=t.fg_muted)

        if hasattr(self, "right_selected_card"):
            self.right_selected_card.config(bg=t.bg_card)
            for rp in (getattr(self, "row_p1", None), getattr(self, "row_p2", None), getattr(self, "row_p3", None)):
                if rp:
                    rp.config(bg=t.bg_card)
            for p_btn in (getattr(self, "p_btn_exclude", None), getattr(self, "p_btn_folder", None), getattr(self, "p_btn_copy", None), getattr(self, "p_btn_pin", None), getattr(self, "p_btn_skip", None)):
                if p_btn:
                    p_btn.config(bg=t.bg_button, fg=t.fg_primary, border_color=t.border)

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

    def _open_update_tracker(self) -> None:
        """Opens the App Update Tracker dialog."""
        AppUpdateTrackerDialog(self, tracker=self.update_tracker, theme=self.theme)

    def _open_settings(self) -> None:
        """Opens the Settings & System Configuration modal."""
        SettingsDialog(
            self,
            config=self.config,
            on_theme_changed=self.set_theme,
            on_font_scale_changed=self.set_font_scale,
            on_settings_saved=self._on_settings_saved,
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
        self.lbl_view_title.config(text=filter_name)
        if filter_name == "Software Catalog":
            if hasattr(self, "diag_banner"):
                self.diag_banner.pack_forget()
            self.lbl_view_subtitle.config(text="Search and install from over 6,000 official Windows packages")
            self.btn_update.config(state="disabled")
            self.btn_update_selected.config(state="disabled")
            self._search_catalog(self.search_query.strip() or "popular")
        elif filter_name in ("Cannot Update", "Review & cannot update", "Review & issues"):
            self.lbl_view_title.config(text="Review & Cannot Update")
            self.lbl_view_subtitle.config(text="Applications requiring review, publisher variance verification, or repository linking")
            if hasattr(self, "diag_banner"):
                self.diag_banner.pack(fill=tk.X, pady=(0, 8), before=self.table)
            self.apply_filter()
        elif filter_name == "Updates Available":
            if hasattr(self, "diag_banner"):
                self.diag_banner.pack_forget()
            self.lbl_view_subtitle.config(text="Compatible updates verified against official package repositories")
            self.apply_filter()
        elif filter_name == "Up to Date":
            if hasattr(self, "diag_banner"):
                self.diag_banner.pack_forget()
            self.lbl_view_subtitle.config(text="Applications currently running their latest available release")
            self.apply_filter()
        elif filter_name == "Ignored Updates":
            if hasattr(self, "diag_banner"):
                self.diag_banner.pack_forget()
            self.lbl_view_subtitle.config(text="Applications excluded from automated update checks")
            self.apply_filter()
        else:
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
            self.drawer.btn_update.config(
                state="normal",
                text="Install software",
                bg="#881337",
                fg="#ffffff",
            )
            self.btn_update_selected.config(
                state="normal",
                text="Install selected",
                bg="#881337",
                fg="#ffffff",
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
            self.btn_update_selected.config(
                state="disabled",
                text="Update selected",
                bg="#ffffff",
                fg="#9ca3af",
            )

        # Update bottom right action pill states
        has_sel = (item is not None)
        can_up = bool(item and item.can_auto_update())
        for p_btn in (
            getattr(self, "p_btn_exclude", None),
            getattr(self, "p_btn_folder", None),
            getattr(self, "p_btn_copy", None),
            getattr(self, "p_btn_pin", None),
            getattr(self, "p_btn_skip", None),
            getattr(self, "p_btn_uninstall", None),
        ):
            if p_btn:
                p_btn.config(state="normal" if has_sel else "disabled")
        if hasattr(self, "p_btn_update"):
            self.p_btn_update.config(state="normal" if can_up else "disabled")

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
        q = query.strip() or "popular"
        self.status_lbl.config(text=f"Searching repository catalogs for '{q}'...")
        self.table.show_skeleton()

        def worker():
            items = []
            # 1. Search secondary package managers (Pip, Npm, Scoop, Chocolatey)
            try:
                secondary_matches = self.source_manager.search_all(q)
                items.extend(secondary_matches)
            except Exception as e:
                logger.error(f"Catalog search error in source manager: {e}")

            # 2. Search official Winget catalog
            try:
                entries = self.winget.search_packages(q, count=25)
                for entry in entries:
                    it = ProgramItem(
                        name=entry.name,
                        id=entry.id,
                        installed_version="Not Installed",
                        latest_version=entry.version or "Latest",
                        package_type=PackageType.WIN32_EXE,
                        source=entry.source or "winget",
                        action=UpdateAction.AVAILABLE,
                        notes="Official winget package ready to install",
                    )
                    items.append(it)
            except Exception as e:
                logger.error(f"Catalog search error in winget: {e}")

            self.msg_queue.put(("CATALOG_RESULTS", items))

        threading.Thread(target=worker, daemon=True).start()

    def _on_catalog_results(self, items: List[ProgramItem]) -> None:
        self.table.populate(items)
        self.lbl_view_subtitle.config(text=f"Found {len(items)} catalog packages")
        self.status_lbl.config(text=f"Catalog ready: {len(items)} packages found.")

    def start_scan(self) -> None:
        if self.is_busy:
            return
        self.is_busy = True
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
                            item.latest_version = info.get("latest_version") or item.latest_version
                            item.action = UpdateAction.AVAILABLE
                            item.is_verified_winget = True
                            item.notes = f"Update available via {src.upper()}"
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
            self.btn_update.config(state="normal", bg="#881337", fg="#ffffff")
            self.lbl_view_subtitle.config(text=f"{total} programs scanned • {updates} verified updates ready")
            self.status_lbl.config(text=f"Scan complete: {updates} updates available.")
            self._show_floating_toast(f"Scan complete: {updates} updates ready", "✓")
        else:
            self.btn_update.config(state="disabled", bg="#fef2f2", fg="#9ca3af")
            self.lbl_view_subtitle.config(text=f"{total} programs scanned • All software up to date")
            self.status_lbl.config(text="Scan complete: All software is up to date.")
            self._show_floating_toast(f"Scan complete: {total} items analyzed", "✓")

    def apply_filter(self) -> None:
        """Filters the items based on sidebar view, search keyword, and category."""
        keyword = self.search_query.strip().lower()
        filter_mode = self.active_filter
        cat_mode = self.active_category

        filtered = []
        for item in self.all_programs:
            # 1. Search Query filter (by name or publisher)
            if keyword:
                name_match = keyword in item.name.lower()
                pub_match = item.publisher and keyword in item.publisher.lower()
                id_match = item.id and keyword in item.id.lower()
                if not (name_match or pub_match or id_match):
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
            if cat_mode == "Win32 Applications":
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
            title="Export Software Inventory Report",
            defaultextension=".csv",
            filetypes=[("CSV Spreadsheet (*.csv)", "*.csv"), ("JSON File (*.json)", "*.json")],
        )
        if not file_path:
            return

        try:
            if file_path.lower().endswith(".json"):
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
            self._show_floating_toast(f"Report saved: {os.path.basename(file_path)}", "✓")
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
        if hasattr(self.sidebar, "entry_search"):
            self.sidebar.entry_search.focus_set()
            self.sidebar.entry_search.select_range(0, tk.END)
            self._show_floating_toast("Quick search active (Type to filter)", "🔍")
        return "break"
