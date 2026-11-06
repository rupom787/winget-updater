"""Modal dialogs for exclusions, scheduling, vendor fallbacks, and downgrade confirmations.
Designed with Clean White and Velvet Burgundy typography and rounded controls.
"""

import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, List, Optional
from winget_updater.config import ConfigManager, ExclusionRule, VendorSourceEntry
from winget_updater.engine.scheduler import SchedulerManager
from winget_updater.gui.rounded_widgets import RoundedButton, RoundedPillBadge, apply_native_window_styling
from winget_updater.engine.tracker import TrackedAppUpdate, UpdateTracker
from winget_updater.gui.theme import DARK_THEME, DREAM_THEME, LIGHT_THEME, ThemeColors, get_theme
from winget_updater.engine.cleanup import DiskCleanupManager
from winget_updater.engine.startup import StartupItem, StartupManager
from winget_updater.models import ProgramItem


class ExclusionManagerDialog(tk.Toplevel):
    """Dialog for managing application exclusions."""

    def __init__(
        self,
        parent: tk.Widget,
        config: ConfigManager,
        on_change: Optional[Callable[[], None]] = None,
        theme: Optional[ThemeColors] = None,
    ):
        super().__init__(parent)
        self.title("Manage Excluded Software")
        self.geometry("640x480")
        self.minsize(540, 380)
        self.config = config
        self.on_change = on_change
        self.theme = theme or DARK_THEME
        try:
            apply_native_window_styling(self, self.theme)
        except Exception:
            pass
        self.configure(bg=self.theme.bg_root)

        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._refresh_list()

    def _build_ui(self) -> None:
        t = self.theme
        frame = tk.Frame(self, bg=t.bg_root, padx=20, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        lbl_title = tk.Label(
            frame,
            text="Application Exclusions",
            bg=t.bg_root,
            fg=t.accent_burgundy,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        lbl_title.pack(anchor=tk.W)

        lbl_desc = tk.Label(
            frame,
            text="Programs matching these names or package identifiers are ignored and will not receive automatic updates.",
            bg=t.bg_root,
            fg=t.fg_muted,
            font=("Segoe UI", 9),
            anchor="w",
            wraplength=580,
            justify=tk.LEFT,
        )
        lbl_desc.pack(anchor=tk.W, pady=(2, 12))

        # Table container
        table_frame = tk.Frame(
            frame,
            bg=t.bg_card,
            highlightbackground=t.border,
            highlightthickness=1,
        )
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("Pattern", "Reason")
        self.tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("Pattern", text="Application / Package ID")
        self.tree.heading("Reason", text="Reason for Exclusion")
        self.tree.column("Pattern", width=260)
        self.tree.column("Reason", width=320)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Input card
        input_frame = tk.Frame(
            frame,
            bg=t.bg_card,
            padx=14,
            pady=12,
            highlightbackground=t.border,
            highlightthickness=1,
        )
        input_frame.pack(fill=tk.X, pady=(12, 12))

        f1 = tk.Frame(input_frame, bg=t.bg_card)
        f1.pack(fill=tk.X, pady=3)
        tk.Label(
            f1,
            text="Program / ID:",
            width=14,
            bg=t.bg_card,
            fg=t.fg_primary,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(side=tk.LEFT)
        self.entry_pattern = tk.Entry(
            f1,
            bg=t.bg_input,
            fg=t.fg_primary,
            relief=tk.SOLID,
            bd=1,
            font=("Segoe UI", 9),
        )
        self.entry_pattern.pack(side=tk.LEFT, fill=tk.X, expand=True)

        f2 = tk.Frame(input_frame, bg=t.bg_card)
        f2.pack(fill=tk.X, pady=3)
        tk.Label(
            f2,
            text="Reason:",
            width=14,
            bg=t.bg_card,
            fg=t.fg_primary,
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(side=tk.LEFT)
        self.entry_reason = tk.Entry(
            f2,
            bg=t.bg_input,
            fg=t.fg_primary,
            relief=tk.SOLID,
            bd=1,
            font=("Segoe UI", 9),
        )
        self.entry_reason.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.entry_reason.insert(0, "User excluded")

        f3 = tk.Frame(input_frame, bg=t.bg_card)
        f3.pack(fill=tk.X, pady=(6, 0))
        btn_add = RoundedButton(
            f3,
            text="Add Exclusion",
            command=self._add_rule,
            bg_color=t.accent_burgundy,
            fg_color="#ffffff",
            radius=6,
            height=30,
            font=("Segoe UI", 9, "bold"),
            padding=(14, 4),
        )
        btn_add.pack(side=tk.RIGHT)

        # Footer Actions
        btn_frame = tk.Frame(frame, bg=t.bg_root)
        btn_frame.pack(fill=tk.X)

        btn_remove = RoundedButton(
            btn_frame,
            text="Remove Selected",
            command=self._remove_selected,
            bg_color="#ffffff",
            fg_color="#b91c1c",
            border_color="#fca5a5",
            radius=6,
            height=32,
            font=("Segoe UI", 9),
            padding=(12, 6),
        )
        btn_remove.pack(side=tk.LEFT)

        btn_close = RoundedButton(
            btn_frame,
            text="Close",
            command=self.destroy,
            bg_color="#ffffff",
            fg_color=t.fg_secondary,
            border_color=t.border,
            radius=6,
            height=32,
            font=("Segoe UI", 9),
            padding=(16, 6),
        )
        btn_close.pack(side=tk.RIGHT)

    def _refresh_list(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for rule in self.config.exclusions:
            self.tree.insert("", tk.END, values=(rule.pattern, rule.reason))

    def _add_rule(self) -> None:
        pat = self.entry_pattern.get().strip()
        reason = self.entry_reason.get().strip() or "User excluded"
        if not pat:
            messagebox.showwarning("Validation Error", "Please provide a program name or package identifier.", parent=self)
            return

        self.config.add_exclusion(pat, reason)
        self.entry_pattern.delete(0, tk.END)
        self._refresh_list()
        if self.on_change:
            self.on_change()

    def _remove_selected(self) -> None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selection Required", "Please select an exclusion rule from the table to remove.", parent=self)
            return

        values = self.tree.item(sel[0], "values")
        if values:
            pat = values[0]
            if messagebox.askyesno("Confirm Removal", f"Remove exclusion for '{pat}'?", parent=self):
                self.config.remove_exclusion(pat)
                self._refresh_list()
                if self.on_change:
                    self.on_change()


class ScheduleConfigDialog(tk.Toplevel):
    """Dialog to configure or remove the Windows Task Scheduler background update task."""

    def __init__(self, parent: tk.Widget, scheduler: SchedulerManager, theme: Optional[ThemeColors] = None):
        super().__init__(parent)
        self.title("Daily Update Schedule")
        self.geometry("560x420")
        self.minsize(480, 360)
        self.scheduler = scheduler
        self.theme = theme or DARK_THEME
        try:
            apply_native_window_styling(self, self.theme)
        except Exception:
            pass
        self.configure(bg=self.theme.bg_root)

        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._refresh_status()

    def _build_ui(self) -> None:
        t = self.theme
        frame = tk.Frame(self, bg=t.bg_root, padx=22, pady=18)
        frame.pack(fill=tk.BOTH, expand=True)

        lbl_title = tk.Label(
            frame,
            text="Scheduled Updates",
            bg=t.bg_root,
            fg=t.accent_burgundy,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        lbl_title.pack(anchor=tk.W)

        desc = (
            "Configure a once-daily background update check via Windows Task Scheduler.\n\n"
            "Safety Policies:\n"
            "• Executes only while an active interactive session is open\n"
            "• Automatically pauses if running on battery power (requires AC power)\n"
            "• Automatically pauses if system CPU utilization is heavy\n"
            "• Never updates excluded or unverified packages"
        )
        tk.Label(
            frame,
            text=desc,
            bg=t.bg_root,
            fg=t.fg_secondary,
            font=("Segoe UI", 9),
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(4, 14))

        # Status card
        self.status_box = tk.Frame(
            frame,
            bg=t.bg_card,
            padx=14,
            pady=12,
            highlightbackground=t.border,
            highlightthickness=1,
        )
        self.status_box.pack(fill=tk.X, pady=(0, 14))

        self.lbl_status = tk.Label(
            self.status_box,
            text="Checking Windows Task Scheduler status...",
            bg=t.bg_card,
            fg=t.fg_primary,
            font=("Segoe UI", 9),
            anchor="w",
            justify=tk.LEFT,
        )
        self.lbl_status.pack(anchor=tk.W)

        # Time picker row
        time_frame = tk.Frame(frame, bg=t.bg_root)
        time_frame.pack(fill=tk.X, pady=(0, 16))

        tk.Label(
            time_frame,
            text="Daily schedule time (HH:MM 24-hour):",
            bg=t.bg_root,
            fg=t.fg_primary,
            font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.entry_time = tk.Entry(
            time_frame,
            width=10,
            bg=t.bg_input,
            fg=t.fg_primary,
            font=("Segoe UI", 10),
            relief=tk.SOLID,
            bd=1,
        )
        self.entry_time.insert(0, "03:00")
        self.entry_time.pack(side=tk.LEFT)

        # Action buttons
        btn_frame = tk.Frame(frame, bg=t.bg_root)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        self.btn_save = RoundedButton(
            btn_frame,
            text="Enable Daily Schedule",
            command=self._save_task,
            bg_color=t.accent_burgundy,
            fg_color="#ffffff",
            radius=6,
            height=34,
            font=("Segoe UI", 9, "bold"),
            padding=(16, 6),
        )
        self.btn_save.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_delete = RoundedButton(
            btn_frame,
            text="Disable Schedule",
            command=self._delete_task,
            bg_color="#ffffff",
            fg_color="#b91c1c",
            border_color="#fca5a5",
            radius=6,
            height=34,
            font=("Segoe UI", 9),
            padding=(14, 6),
        )
        self.btn_delete.pack(side=tk.LEFT)

        btn_close = RoundedButton(
            btn_frame,
            text="Close",
            command=self.destroy,
            bg_color="#ffffff",
            fg_color=t.fg_secondary,
            border_color=t.border,
            radius=6,
            height=34,
            font=("Segoe UI", 9),
            padding=(16, 6),
        )
        btn_close.pack(side=tk.RIGHT)

    def _refresh_status(self) -> None:
        exists, info = self.scheduler.is_task_scheduled()
        if exists:
            self.lbl_status.config(
                text=f"Active Schedule: Configured\n{info}",
                fg="#059669",
            )
            self.btn_save.config(text="Update Schedule Time")
            self.btn_delete.config(state="normal")
        else:
            self.lbl_status.config(
                text="Active Schedule: None\nAutomatic background updates are not currently active.",
                fg=self.theme.fg_muted,
            )
            self.btn_save.config(text="Enable Daily Schedule")
            self.btn_delete.config(state="disabled")

    def _save_task(self) -> None:
        t_str = self.entry_time.get().strip()
        parts = t_str.split(":")
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            messagebox.showwarning("Validation Error", "Please specify time in 24-hr format (e.g. 03:00 or 14:30).", parent=self)
            return

        h, m = int(parts[0]), int(parts[1])
        if not (0 <= h <= 23 and 0 <= m <= 59):
            messagebox.showwarning("Validation Error", "Invalid hour (0-23) or minute (0-59).", parent=self)
            return

        success, msg = self.scheduler.create_daily_task(t_str)
        if success:
            messagebox.showinfo("Schedule Created", msg, parent=self)
            self._refresh_status()
        else:
            messagebox.showerror("Scheduler Error", f"Failed to register task: {msg}", parent=self)

    def _delete_task(self) -> None:
        success, msg = self.scheduler.delete_daily_task()
        if success:
            messagebox.showinfo("Schedule Disabled", msg, parent=self)
            self._refresh_status()
        else:
            messagebox.showwarning("Notice", f"Could not remove task: {msg}", parent=self)


def prompt_downgrade_confirmation(parent: tk.Widget, item: ProgramItem) -> bool:
    """Explicit confirmation dialog for packages with older versions in the repository."""
    msg = (
        f"Installed program: '{item.name}' is version {item.installed_version}.\n"
        f"The version in the repository is older: {item.latest_version}.\n\n"
        f"By default, newer versions are protected from automatic downgrades.\n\n"
        f"Do you want to proceed with downgrading this package?"
    )
    return messagebox.askyesno(
        "Confirm Version Downgrade",
        msg,
        icon="warning",
        parent=parent,
    )


def prompt_vendor_installer_confirmation(parent: tk.Widget, item: ProgramItem) -> bool:
    """Explicit confirmation for fallback vendor installer downloads."""
    msg = (
        f"No package was found in winget for '{item.name}'.\n"
        f"A verified vendor installer URL was matched from your verified sources catalog.\n\n"
        f"URL: {item.notes}\n\n"
        f"The installer is verified against its SHA-256 hash before execution.\n\n"
        f"Do you want to download and install this vendor package with Administrator privileges?"
    )
    return messagebox.askyesno(
        "Confirm Vendor Installer",
        msg,
        icon="question",
        parent=parent,
    )


def prompt_unverified_allow_confirmation(parent: tk.Widget, item: ProgramItem) -> bool:
    """Confirmation to review and approve unverified or ambiguous packages."""
    pkg_id = item.id or item.name
    msg = (
        f"Application: '{item.name}'\n"
        f"Candidate Package ID: {pkg_id}\n"
        f"Installed Publisher: {item.publisher or 'Unknown'}\n\n"
        f"Review Reason:\n{item.notes or item.get_diagnostic_reason()}\n\n"
        f"Do you want to approve this package identifier and enable updating it?"
    )
    return messagebox.askyesno(
        "Review & Approve Package Source",
        msg,
        icon="warning",
        parent=parent,
    )


class BindWingetSourceDialog(tk.Toplevel):
    """Modal dialog allowing users to search Winget and bind any software to an official package ID."""

    def __init__(
        self,
        parent: tk.Widget,
        item: ProgramItem,
        config: ConfigManager,
        on_bound: Optional[Callable[[str], None]] = None,
        theme: Optional[ThemeColors] = None,
        winget_client=None,
    ):
        super().__init__(parent)
        self.title(f"Bind Winget Source — {item.name}")
        self.geometry("680x520")
        self.minsize(580, 420)
        self.item = item
        self.config = config
        self.on_bound = on_bound
        self.theme = theme or DARK_THEME
        try:
            apply_native_window_styling(self, self.theme)
        except Exception:
            pass
        self.winget_client = winget_client
        self.configure(bg=self.theme.bg_root)

        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._initial_search()

    def _build_ui(self) -> None:
        t = self.theme
        frame = tk.Frame(self, bg=t.bg_root, padx=20, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        lbl_title = tk.Label(
            frame,
            text=f"Bind Package Source: {self.item.name}",
            bg=t.bg_root,
            fg=t.accent_burgundy,
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        lbl_title.pack(anchor=tk.W)

        lbl_desc = tk.Label(
            frame,
            text="Search the official Windows Package Manager (winget) catalog to link this application to its verified package identifier.",
            bg=t.bg_root,
            fg=t.fg_muted,
            font=("Segoe UI", 9),
            anchor="w",
            wraplength=620,
            justify=tk.LEFT,
        )
        lbl_desc.pack(anchor=tk.W, pady=(2, 10))

        # Search bar row
        search_row = tk.Frame(frame, bg=t.bg_root)
        search_row.pack(fill=tk.X, pady=(0, 10))

        self.entry_query = tk.Entry(
            search_row,
            font=("Segoe UI", 10),
            bg=t.bg_card,
            fg=t.fg_primary,
            relief=tk.FLAT,
            highlightbackground=t.border,
            highlightthickness=1,
        )
        self.entry_query.insert(0, self.item.name)
        self.entry_query.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6, padx=(0, 8))
        self.entry_query.bind("<Return>", lambda e: self._do_search())

        btn_search = RoundedButton(
            search_row,
            text="Search Catalog",
            command=self._do_search,
            bg_color=t.accent_burgundy,
            fg_color="#ffffff",
            radius=6,
            height=32,
            font=("Segoe UI", 9, "bold"),
            padding=(16, 6),
        )
        btn_search.pack(side=tk.RIGHT)

        # Status label
        self.lbl_search_status = tk.Label(
            frame,
            text="Ready to search repository...",
            bg=t.bg_root,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.lbl_search_status.pack(anchor=tk.W, pady=(0, 6))

        # Results Treeview
        table_frame = tk.Frame(
            frame,
            bg=t.bg_card,
            highlightbackground=t.border,
            highlightthickness=1,
        )
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("Name", "Package ID", "Version", "Source")
        self.tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("Name", text="Application Name")
        self.tree.heading("Package ID", text="Winget Identifier")
        self.tree.heading("Version", text="Latest Version")
        self.tree.heading("Source", text="Repository")

        self.tree.column("Name", width=180, anchor="w")
        self.tree.column("Package ID", width=220, anchor="w")
        self.tree.column("Version", width=90, anchor="center")
        self.tree.column("Source", width=80, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select_item)

        # Bottom manual entry and action buttons
        bottom_box = tk.Frame(frame, bg=t.bg_root, pady=10)
        bottom_box.pack(fill=tk.X)

        manual_row = tk.Frame(bottom_box, bg=t.bg_root)
        manual_row.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            manual_row,
            text="Direct Package ID:",
            bg=t.bg_root,
            fg=t.fg_secondary,
            font=("Segoe UI", 9, "bold"),
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.entry_manual_id = tk.Entry(
            manual_row,
            font=("Segoe UI", 9),
            bg=t.bg_card,
            fg=t.fg_primary,
            relief=tk.FLAT,
            highlightbackground=t.border,
            highlightthickness=1,
        )
        existing_id = self.config.get_custom_mapping(self.item.name, self.item.id) or self.item.id or ""
        self.entry_manual_id.insert(0, existing_id)
        self.entry_manual_id.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)

        btn_row = tk.Frame(bottom_box, bg=t.bg_root)
        btn_row.pack(fill=tk.X)

        self.btn_bind = RoundedButton(
            btn_row,
            text="Bind & Save Source",
            command=self._apply_binding,
            bg_color="#059669",
            fg_color="#ffffff",
            radius=6,
            height=34,
            font=("Segoe UI", 9, "bold"),
            padding=(16, 6),
        )
        self.btn_bind.pack(side=tk.LEFT, padx=(0, 8))

        if self.config.get_custom_mapping(self.item.name, self.item.id):
            btn_unbind = RoundedButton(
                btn_row,
                text="Remove Binding",
                command=self._remove_binding,
                bg_color="#fee2e2",
                fg_color="#991b1b",
                border_color="#fecdd3",
                radius=6,
                height=34,
                font=("Segoe UI", 9),
                padding=(14, 6),
            )
            btn_unbind.pack(side=tk.LEFT, padx=(0, 8))

        btn_cancel = RoundedButton(
            btn_row,
            text="Cancel",
            command=self.destroy,
            bg_color="#ffffff",
            fg_color=t.fg_secondary,
            border_color=t.border,
            radius=6,
            height=34,
            font=("Segoe UI", 9),
            padding=(16, 6),
        )
        btn_cancel.pack(side=tk.RIGHT)

    def _initial_search(self) -> None:
        self.after(100, self._do_search)

    def _do_search(self) -> None:
        q = self.entry_query.get().strip()
        if not q:
            return

        self.lbl_search_status.config(text=f"Searching repository for '{q}'...", fg=self.theme.accent_burgundy)
        for row in self.tree.get_children():
            self.tree.delete(row)

        import threading

        def _worker():
            results = []
            if self.winget_client:
                try:
                    results = self.winget_client.search_catalog(q)
                except Exception:
                    results = []
            self.after(0, lambda: self._show_results(results, q))

        threading.Thread(target=_worker, daemon=True).start()

    def _show_results(self, results, query: str) -> None:
        if not results:
            self.lbl_search_status.config(
                text=f"No packages found matching '{query}'. You can enter the exact Package ID manually below.",
                fg=self.theme.fg_muted,
            )
            return

        self.lbl_search_status.config(
            text=f"Found {len(results)} candidate package(s) in repository:",
            fg="#059669",
        )
        for r in results:
            self.tree.insert(
                "",
                tk.END,
                values=(r.name, r.id, r.version or "—", r.source or "winget"),
            )

    def _on_select_item(self, event) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        vals = self.tree.item(sel[0], "values")
        if vals and len(vals) >= 2:
            self.entry_manual_id.delete(0, tk.END)
            self.entry_manual_id.insert(0, vals[1])

    def _apply_binding(self) -> None:
        bound_id = self.entry_manual_id.get().strip()
        if not bound_id:
            messagebox.showwarning("Validation Error", "Please select or type a valid Winget Package ID.", parent=self)
            return

        self.config.bind_custom_mapping(self.item.name, bound_id)
        self.item.id = bound_id
        self.item.is_user_bound = True
        self.item.is_verified_winget = True

        if self.on_bound:
            self.on_bound(bound_id)

        messagebox.showinfo(
            "Source Bound",
            f"Successfully linked '{self.item.name}' to Winget package '{bound_id}'.\n"
            "This application is now verified and eligible for updates.",
            parent=self,
        )
        self.destroy()

    def _remove_binding(self) -> None:
        self.config.remove_custom_mapping(self.item.name)
        if self.item.id:
            self.config.remove_custom_mapping(self.item.id)

        if self.on_bound:
            self.on_bound("")

        messagebox.showinfo(
            "Binding Removed",
            f"Removed custom package binding for '{self.item.name}'.",
            parent=self,
        )
        self.destroy()


class CannotUpdateHelpDialog(tk.Toplevel):
    """Educational modal explaining why applications cannot update automatically
    and providing actionable solutions for verification and repository linking.
    """

    def __init__(self, parent: tk.Widget, theme: ThemeColors = LIGHT_THEME):
        super().__init__(parent)
        self.theme = theme
        self.title("Software Verification & Diagnostic Resolution Guide")
        self.geometry("720x600")
        self.minsize(640, 500)
        self.transient(parent)
        self.grab_set()

        t = self.theme
        self.configure(bg=t.bg_root)

        # Header Frame
        header = tk.Frame(self, bg=t.bg_sidebar, padx=20, pady=16, highlightbackground=t.border, highlightthickness=1)
        header.pack(fill=tk.X)

        lbl_badge = RoundedPillBadge(
            header,
            text="SAFETY & VERIFICATION GUIDE",
            bg_color="#fef3c7" if t.name != "dark" else "#78350f",
            fg_color="#92400e" if t.name != "dark" else "#fef3c7",
            radius=6,
            font=("Segoe UI", 8, "bold"),
            height=20,
            parent_bg=t.bg_sidebar,
        )
        lbl_badge.pack(anchor="w", pady=(0, 4))

        lbl_title = tk.Label(
            header,
            text="Why Cannot Some Software Update Automatically?",
            bg=t.bg_sidebar,
            fg=t.accent_burgundy,
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        lbl_title.pack(anchor="w")

        lbl_sub = tk.Label(
            header,
            text="Winget Updater enforces enterprise-grade safety checks to ensure your PC is never broken by incorrect installers.",
            bg=t.bg_sidebar,
            fg=t.fg_muted,
            font=("Segoe UI", 9),
            anchor="w",
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

        # Main Content Scrollable Canvas
        content_frame = tk.Frame(self, bg=t.bg_root, padx=20, pady=14)
        content_frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(content_frame, bg=t.bg_root, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient=tk.VERTICAL, command=canvas.yview)
        inner = tk.Frame(canvas, bg=t.bg_root)

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 4 Topic Cards
        topics = [
            (
                "1. Publisher Name Variance (\"Could not verify\")",
                "⚠️ Status: Could not verify",
                "#fef3c7",
                "#92400e",
                "Why it happens: The Windows Registry often records a formal legal corporation name (e.g. 'Google LLC', 'Valve Corp.', 'Oracle America, Inc.'), whereas the Winget package manifest uses a shorter brand name (e.g. 'Google', 'Valve', 'Oracle'). To protect you from impersonation attacks, the updater marks this for review.\n\n"
                "How to update it:\n"
                "• Click '⚡ Allow Update' in the bottom drawer to approve the package and start updating immediately.\n"
                "• Or select multiple items and click '⚡ Approve Selected' in the floating dock.\n"
                "• Once approved, it is permanently verified for future update checks.",
            ),
            (
                "2. Ambiguous Package Matches",
                "🔍 Status: Ambiguous candidates",
                "#eff6ff",
                "#1e40af",
                "Why it happens: A software name matches multiple packages in the official repository (for example: Visual Studio Code vs Visual Studio Code Insiders, or 32-bit vs 64-bit builds).\n\n"
                "How to update it:\n"
                "• Click '🔗 Bind Winget ID' in the bottom drawer.\n"
                "• Search the repository by keyword and select the exact package you want linked.\n"
                "• The updater remembers your choice permanently in custom_mappings.json.",
            ),
            (
                "3. Missing Public Repository Manifest (\"No update source\")",
                "🌐 Status: No update source",
                "#f1f5f9",
                "#475569",
                "Why it happens: The application was installed via direct download or proprietary media, and the vendor has not submitted a manifest to Microsoft Winget or Microsoft Store.\n\n"
                "How to update it:\n"
                "• Click '🌐 Visit Site' in the bottom drawer to open the vendor's official website directly in your browser.\n"
                "• If the software does have a Winget package under another name, click '🔗 Bind Winget ID' to link it manually.",
            ),
            (
                "4. Pinned Versions or Excluded Applications",
                "📌 Status: Pinned / Excluded",
                "#f3e8ff",
                "#6b21a8",
                "Why it happens: You or an administrator previously locked this software to prevent unexpected updates from breaking workflows.\n\n"
                "How to update it:\n"
                "• Click 'Unpin' or 'Un-exclude' in the bottom drawer to restore automated update checks.\n"
                "• Manage all rules in '⚙️ Manage Excluded Applications' under the action bar.",
            ),
        ]

        for title, badge, bbg, bfg, body in topics:
            card = tk.Frame(inner, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=12)
            card.pack(fill=tk.X, pady=(0, 10))

            top_row = tk.Frame(card, bg=t.bg_card)
            top_row.pack(fill=tk.X)

            lbl_ctitle = tk.Label(top_row, text=title, bg=t.bg_card, fg=t.fg_primary, font=("Segoe UI", 10, "bold"), anchor="w")
            lbl_ctitle.pack(side=tk.LEFT)

            pill = RoundedPillBadge(top_row, text=badge, bg_color=bbg, fg_color=bfg, radius=6, font=("Segoe UI", 8, "bold"), height=20, parent_bg=t.bg_card)
            pill.pack(side=tk.RIGHT)

            lbl_cbody = tk.Label(card, text=body, bg=t.bg_card, fg=t.fg_secondary, font=("Segoe UI", 9), justify=tk.LEFT, anchor="w", wraplength=640)
            lbl_cbody.pack(fill=tk.X, pady=(8, 0))

        # Bottom Bar
        bottom = tk.Frame(self, bg=t.bg_sidebar, padx=20, pady=12, highlightbackground=t.border, highlightthickness=1)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)

        btn_close = RoundedButton(
            bottom,
            text="Got it, close guide",
            command=self.destroy,
            bg_color=t.accent_burgundy,
            fg_color="#ffffff",
            hover_bg=t.accent_burgundy_hover,
            radius=6,
            font=("Segoe UI", 9, "bold"),
            width=160,
            height=32,
            parent_bg=t.bg_sidebar,
        )
        btn_close.pack(side=tk.RIGHT)



class SettingsDialog(tk.Toplevel):
    """Modern Settings modal with Velvet Burgundy aesthetic, typography scaling, manager toggles, and safety options."""

    def __init__(
        self,
        parent: tk.Widget,
        config: ConfigManager,
        on_theme_changed: Optional[Callable[[str], None]] = None,
        on_font_scale_changed: Optional[Callable[[str], None]] = None,
        on_settings_saved: Optional[Callable[[], None]] = None,
        on_backup_stack: Optional[Callable[[], None]] = None,
        on_restore_stack: Optional[Callable[[], None]] = None,
        on_refresh_sources: Optional[Callable[[], None]] = None,
        on_open_exclusions: Optional[Callable[[], None]] = None,
        on_open_sources: Optional[Callable[[], None]] = None,
        on_open_schedule: Optional[Callable[[], None]] = None,
        on_open_runtimes: Optional[Callable[[], None]] = None,
        on_open_disk_cleanup: Optional[Callable[[], None]] = None,
        on_open_startup_manager: Optional[Callable[[], None]] = None,
        on_export_inventory: Optional[Callable[[], None]] = None,
        on_uninstall_app: Optional[Callable[[], None]] = None,
        scheduler=None,
        theme: Optional[ThemeColors] = None,
    ):
        super().__init__(parent)
        self.title("Settings & Preferences")
        self.geometry("820x640")
        self.minsize(720, 560)
        self.config = config
        self.on_theme_changed = on_theme_changed
        self.on_font_scale_changed = on_font_scale_changed
        self.on_settings_saved = on_settings_saved
        self.on_backup_stack = on_backup_stack
        self.on_restore_stack = on_restore_stack
        self.on_refresh_sources = on_refresh_sources
        self.on_open_exclusions = on_open_exclusions
        self.on_open_sources = on_open_sources
        self.on_open_schedule = on_open_schedule
        self.on_open_runtimes = on_open_runtimes
        self.on_open_disk_cleanup = on_open_disk_cleanup
        self.on_open_startup_manager = on_open_startup_manager
        self.on_export_inventory = on_export_inventory
        self.on_uninstall_app = on_uninstall_app
        self.scheduler = scheduler
        self.theme = theme or DARK_THEME
        try:
            apply_native_window_styling(self, self.theme)
        except Exception:
            pass
        self.configure(bg=self.theme.bg_root)

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        t = self.theme

        # Top Header
        top_header = tk.Frame(self, bg=t.bg_card, padx=20, pady=16, highlightbackground=t.border, highlightthickness=1)
        top_header.pack(fill=tk.X)

        lbl_title = tk.Label(
            top_header,
            text="⚙️ Preferences & System Configuration",
            bg=t.bg_card,
            fg=t.accent_burgundy,
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        lbl_title.pack(anchor=tk.W)

        lbl_desc = tk.Label(
            top_header,
            text="Customize font scaling, UI themes, package ecosystems, safety parameters, and update behaviors.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 9),
            anchor="w",
        )
        lbl_desc.pack(anchor=tk.W, pady=(2, 0))

        # Main notebook
        style = ttk.Style()
        style.configure("Settings.TNotebook", background=t.bg_root, borderwidth=0)
        style.configure("Settings.TNotebook.Tab", padding=[10, 6], font=("Segoe UI", 9, "bold"))
        self.notebook = ttk.Notebook(self, style="Settings.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=14)

        # Tab 1: Appearance & Display
        self.tab_appearance = tk.Frame(self.notebook, bg=t.bg_root, padx=14, pady=12)
        self.notebook.add(self.tab_appearance, text="Appearance")
        self._build_appearance_tab()

        # Tab 2: Package Ecosystems & Sources
        self.tab_managers = tk.Frame(self.notebook, bg=t.bg_root, padx=14, pady=12)
        self.notebook.add(self.tab_managers, text="Packages")
        self._build_managers_tab()

        # Tab 3: Safety & Exclusions
        self.tab_safety = tk.Frame(self.notebook, bg=t.bg_root, padx=14, pady=12)
        self.notebook.add(self.tab_safety, text="Safety")
        self._build_safety_tab()

        # Tab 4: Schedule & Automation
        self.tab_schedule = tk.Frame(self.notebook, bg=t.bg_root, padx=14, pady=12)
        self.notebook.add(self.tab_schedule, text="Schedule")
        self._build_schedule_tab()

        # Tab 5: Backup & Export
        self.tab_backup = tk.Frame(self.notebook, bg=t.bg_root, padx=14, pady=12)
        self.notebook.add(self.tab_backup, text="Backup")
        self._build_backup_tab()

        # Tab 6: Application Maintenance & Uninstaller
        self.tab_maintenance = tk.Frame(self.notebook, bg=t.bg_root, padx=14, pady=12)
        self.notebook.add(self.tab_maintenance, text="Maintenance")
        self._build_maintenance_tab()

        # Bottom Action Bar
        bottom = tk.Frame(self, bg=t.bg_sidebar, padx=20, pady=12, highlightbackground=t.border, highlightthickness=1)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)

        btn_save = RoundedButton(
            bottom,
            text="Save Preferences",
            command=self._save_and_close,
            bg_color=t.accent_burgundy,
            fg_color="#ffffff",
            hover_bg=t.accent_burgundy_hover,
            radius=6,
            font=("Segoe UI", 9, "bold"),
            width=140,
            height=32,
            parent_bg=t.bg_sidebar,
        )
        btn_save.pack(side=tk.RIGHT, padx=(8, 0))

        btn_cancel = RoundedButton(
            bottom,
            text="Cancel",
            command=self.destroy,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            hover_bg=t.bg_button_hover,
            radius=6,
            font=("Segoe UI", 9),
            width=90,
            height=32,
            parent_bg=t.bg_sidebar,
        )
        btn_cancel.pack(side=tk.RIGHT)

    def _build_appearance_tab(self) -> None:
        t = self.theme

        # Typography scaling
        card_font = tk.Frame(self.tab_appearance, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=12)
        card_font.pack(fill=tk.X, pady=(0, 10))

        lbl_fhead = tk.Label(card_font, text="Text & Font Size Scaling", bg=t.bg_card, fg=t.fg_primary, font=("Segoe UI", 10, "bold"), anchor="w")
        lbl_fhead.pack(anchor=tk.W)

        lbl_fdesc = tk.Label(
            card_font,
            text="Choose typography sizing calibrated for your monitor resolution (improves legibility on 1080p, 1440p, and 4K).",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
        )
        lbl_fdesc.pack(anchor=tk.W, pady=(2, 8))

        self.font_scale_var = tk.StringVar(value=getattr(self.config, "font_scale", "normal"))
        font_options = [
            ("Compact (90%) - For small displays", "compact"),
            ("Normal (100%) - Recommended standard", "normal"),
            ("Large (115%) - Clearer, larger typography", "large"),
            ("Extra Large (130%) - High-DPI & accessibility", "extra_large"),
        ]
        for label, val in font_options:
            rb = tk.Radiobutton(
                card_font,
                text=label,
                value=val,
                variable=self.font_scale_var,
                bg=t.bg_card,
                fg=t.fg_primary,
                activebackground=t.bg_card,
                activeforeground=t.accent_burgundy,
                selectcolor=t.bg_input,
                font=("Segoe UI", 9),
            )
            rb.pack(anchor=tk.W, pady=2)

        # Theme selection
        card_theme = tk.Frame(self.tab_appearance, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=12)
        card_theme.pack(fill=tk.X, pady=(0, 10))

        lbl_thead = tk.Label(card_theme, text="Color Theme", bg=t.bg_card, fg=t.fg_primary, font=("Segoe UI", 10, "bold"), anchor="w")
        lbl_thead.pack(anchor=tk.W)

        self.theme_var = tk.StringVar(value=getattr(self.config, "theme", "dark"))
        theme_options = [
            ("🌙 Obsidian Dream (Dark Glass • Default)", "dark"),
            ("🌸 Amethyst Bloom (Surreal Architecture)", "bloom"),
            ("☀️ Ivory Wake (Light Mode)", "light"),
        ]
        for label, val in theme_options:
            rb = tk.Radiobutton(
                card_theme,
                text=label,
                value=val,
                variable=self.theme_var,
                bg=t.bg_card,
                fg=t.fg_primary,
                activebackground=t.bg_card,
                activeforeground=t.accent_burgundy,
                selectcolor=t.bg_input,
                font=("Segoe UI", 9),
            )
            rb.pack(anchor=tk.W, pady=2)

        # Smooth animations toggle
        card_anim = tk.Frame(self.tab_appearance, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=12)
        card_anim.pack(fill=tk.X)

        self.anim_var = tk.BooleanVar(value=getattr(self.config, "smooth_animations", True))
        chk_anim = tk.Checkbutton(
            card_anim,
            text="Enable fluid 60 FPS animations, deck counters, and laser scanning pulses",
            variable=self.anim_var,
            bg=t.bg_card,
            fg=t.fg_primary,
            activebackground=t.bg_card,
            activeforeground=t.accent_burgundy,
            selectcolor=t.bg_input,
            font=("Segoe UI", 9),
        )
        chk_anim.pack(anchor=tk.W)

    def _build_managers_tab(self) -> None:
        t = self.theme
        card = tk.Frame(self.tab_managers, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=12)
        card.pack(fill=tk.BOTH, expand=True)

        lbl_head = tk.Label(card, text="Integrated Package Managers", bg=t.bg_card, fg=t.fg_primary, font=("Segoe UI", 10, "bold"), anchor="w")
        lbl_head.pack(anchor=tk.W)

        lbl_desc = tk.Label(
            card,
            text="Enable or disable package ecosystems queried during scans and updates.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
        )
        lbl_desc.pack(anchor=tk.W, pady=(2, 10))

        self.manager_vars: Dict[str, tk.BooleanVar] = {}
        managers = [
            ("winget", "Windows Package Manager (WinGet)", "Native Microsoft package catalog (MSIX, InnoSetup, MSI)"),
            ("pip", "Python Package Index (Pip)", "Audits outdated libraries across all discovered Python runtimes"),
            ("npm", "Node.js (Npm & Corepack)", "Global Node.js CLI packages and toolchains"),
            ("scoop", "Scoop Package Manager", "Developer toolchain command-line installer"),
            ("chocolatey", "Chocolatey (choco)", "Windows community package repository"),
            ("store", "Microsoft Store Apps", "Modern UWP packaged store applications"),
        ]

        cfg_managers = getattr(self.config, "enabled_managers", {})
        for key, name, desc in managers:
            var = tk.BooleanVar(value=cfg_managers.get(key, True))
            self.manager_vars[key] = var

            m_row = tk.Frame(card, bg=t.bg_card)
            m_row.pack(fill=tk.X, pady=4)

            chk = tk.Checkbutton(
                m_row,
                text=name,
                variable=var,
                bg=t.bg_card,
                fg=t.fg_primary,
                activebackground=t.bg_card,
                activeforeground=t.accent_burgundy,
                selectcolor=t.bg_input,
                font=("Segoe UI", 9, "bold"),
            )
            chk.pack(anchor=tk.W)

            lbl_sub = tk.Label(m_row, text=desc, bg=t.bg_card, fg=t.fg_muted, font=("Segoe UI", 8))
            lbl_sub.pack(anchor=tk.W, padx=(24, 0))

        # Repository & Source Actions
        card_sources = tk.Frame(self.tab_managers, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=12)
        card_sources.pack(fill=tk.X, pady=(10, 0))

        lbl_shead = tk.Label(card_sources, text="Repository Indices & Custom Sources", bg=t.bg_card, fg=t.fg_primary, font=("Segoe UI", 10, "bold"), anchor="w")
        lbl_shead.pack(anchor=tk.W)

        lbl_sdesc = tk.Label(
            card_sources,
            text="Update local package manager database indices or configure custom download URLs for unsupported software.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
        )
        lbl_sdesc.pack(anchor=tk.W, pady=(2, 8))

        s_btn_row = tk.Frame(card_sources, bg=t.bg_card)
        s_btn_row.pack(fill=tk.X)

        btn_ref_src = RoundedButton(
            s_btn_row,
            text="🔄 Refresh Package Sources",
            command=self._do_refresh_sources,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            border_color=t.border,
            radius=6,
            height=30,
            font=("Segoe UI", 9),
            padding=(12, 4),
        )
        btn_ref_src.pack(side=tk.LEFT, padx=(0, 8))

        btn_cust_src = RoundedButton(
            s_btn_row,
            text="🌐 Manage Vendor Sources",
            command=self._do_open_sources,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            border_color=t.border,
            radius=6,
            height=30,
            font=("Segoe UI", 9),
            padding=(12, 4),
        )
        btn_cust_src.pack(side=tk.LEFT)

    def _build_safety_tab(self) -> None:
        t = self.theme
        card = tk.Frame(self.tab_safety, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=12)
        card.pack(fill=tk.BOTH, expand=True)

        lbl_head = tk.Label(card, text="Safety Guards & Automation", bg=t.bg_card, fg=t.fg_primary, font=("Segoe UI", 10, "bold"), anchor="w")
        lbl_head.pack(anchor=tk.W)

        self.vcredist_var = tk.BooleanVar(value=getattr(self.config, "ignore_legacy_vcredist", True))
        chk_vc = tk.Checkbutton(
            card,
            text="Safely ignore legacy Visual C++ runtime DLLs from batch updates (Recommended)",
            variable=self.vcredist_var,
            bg=t.bg_card,
            fg=t.fg_primary,
            activebackground=t.bg_card,
            activeforeground=t.accent_burgundy,
            selectcolor=t.bg_input,
            font=("Segoe UI", 9, "bold"),
        )
        chk_vc.pack(anchor=tk.W, pady=(8, 0))
        lbl_vc_sub = tk.Label(
            card,
            text="Treats static Visual C++ 2005-2013 runtimes as stable system components, preventing failed update errors.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
        )
        lbl_vc_sub.pack(anchor=tk.W, padx=(24, 0), pady=(0, 4))

        btn_launch_runtimes = RoundedButton(
            card,
            text="🎮 Open Gaming & System Runtimes Manager",
            command=self._do_open_runtimes,
            bg_color=t.bg_button,
            fg_color=t.accent_burgundy,
            hover_bg=t.bg_button_hover,
            border_color=t.border,
            radius=6,
            font=("Segoe UI", 8, "bold"),
            height=26,
            parent_bg=t.bg_card,
        )
        btn_launch_runtimes.pack(anchor=tk.W, padx=(24, 0), pady=(0, 8))

        self.restore_var = tk.BooleanVar(value=getattr(self.config, "create_restore_point", False))
        chk_rp = tk.Checkbutton(
            card,
            text="Create Windows System Restore Point prior to batch updating",
            variable=self.restore_var,
            bg=t.bg_card,
            fg=t.fg_primary,
            activebackground=t.bg_card,
            activeforeground=t.accent_burgundy,
            selectcolor=t.bg_input,
            font=("Segoe UI", 9, "bold"),
        )
        chk_rp.pack(anchor=tk.W, pady=(4, 0))

        self.autoclose_var = tk.BooleanVar(value=getattr(self.config, "auto_close_apps", True))
        chk_ac = tk.Checkbutton(
            card,
            text="Gracefully close running applications before updating to prevent installer lock errors",
            variable=self.autoclose_var,
            bg=t.bg_card,
            fg=t.fg_primary,
            activebackground=t.bg_card,
            activeforeground=t.accent_burgundy,
            selectcolor=t.bg_input,
            font=("Segoe UI", 9, "bold"),
        )
        chk_ac.pack(anchor=tk.W, pady=(4, 0))

        # Exclusions management card
        card_excl = tk.Frame(self.tab_safety, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=12)
        card_excl.pack(fill=tk.X, pady=(10, 0))

        lbl_ehead = tk.Label(card_excl, text="Application Exclusions", bg=t.bg_card, fg=t.fg_primary, font=("Segoe UI", 10, "bold"), anchor="w")
        lbl_ehead.pack(anchor=tk.W)

        lbl_edesc = tk.Label(
            card_excl,
            text="Prevent specific software or package IDs from appearing in update scans or receiving automated updates.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
        )
        lbl_edesc.pack(anchor=tk.W, pady=(2, 8))

        btn_manage_excl = RoundedButton(
            card_excl,
            text="⊘ Manage Application Exclusions",
            command=self._do_open_exclusions,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            border_color=t.border,
            radius=6,
            height=30,
            font=("Segoe UI", 9),
            padding=(14, 4),
        )
        btn_manage_excl.pack(anchor=tk.W)

        self.cleanup_var = tk.BooleanVar(value=getattr(self.config, "cleanup_temp_cache", True))
        chk_cl = tk.Checkbutton(
            card,
            text="Automatically purge installer cache & temporary setup files after update routine",
            variable=self.cleanup_var,
            bg=t.bg_card,
            fg=t.fg_primary,
            activebackground=t.bg_card,
            activeforeground=t.accent_burgundy,
            selectcolor=t.bg_input,
            font=("Segoe UI", 9, "bold"),
        )
        chk_cl.pack(anchor=tk.W, pady=(4, 0))

        self.autoscan_var = tk.BooleanVar(value=getattr(self.config, "auto_scan_on_startup", True))
        chk_as = tk.Checkbutton(
            card,
            text="Automatically check for software updates upon launch",
            variable=self.autoscan_var,
            bg=t.bg_card,
            fg=t.fg_primary,
            activebackground=t.bg_card,
            activeforeground=t.accent_burgundy,
            selectcolor=t.bg_input,
            font=("Segoe UI", 9, "bold"),
        )
        chk_as.pack(anchor=tk.W, pady=(4, 0))


    def _build_schedule_tab(self) -> None:
        t = self.theme
        card = tk.Frame(self.tab_schedule, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=16, pady=16)
        card.pack(fill=tk.BOTH, expand=True)

        lbl_head = tk.Label(card, text="Windows Task Scheduler Daily Updates & Automation", bg=t.bg_card, fg=t.fg_primary, font=("Segoe UI", 11, "bold"), anchor="w")
        lbl_head.pack(anchor=tk.W)

        lbl_desc = tk.Label(
            card,
            text="Configure automated background updates via Windows Task Scheduler. Safety guards automatically pause execution on battery power or heavy CPU load.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
            justify=tk.LEFT,
        )
        lbl_desc.pack(anchor=tk.W, pady=(2, 12))

        # Status & Time Box
        box = tk.Frame(card, bg=t.bg_root, padx=12, pady=10, highlightbackground=t.border, highlightthickness=1)
        box.pack(fill=tk.X, pady=(0, 12))

        # Check current status
        sched_mgr = self.scheduler
        is_active = False
        sched_time = "12:00"
        if sched_mgr:
            try:
                is_active = sched_mgr.is_scheduled_task_enabled()
                extracted = sched_mgr.get_scheduled_time()
                if extracted:
                    sched_time = extracted
            except Exception:
                pass

        status_text = f"● Active Daily Schedule ({sched_time})" if is_active else "○ Daily Schedule: Inactive (Disabled)"
        status_color = "#059669" if is_active else t.fg_muted

        self.lbl_sched_status = tk.Label(
            box,
            text=status_text,
            bg=t.bg_root,
            fg=status_color,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        )
        self.lbl_sched_status.pack(anchor=tk.W, pady=(0, 6))

        time_row = tk.Frame(box, bg=t.bg_root)
        time_row.pack(fill=tk.X)

        tk.Label(
            time_row,
            text="Scheduled execution time (HH:MM 24-hr):",
            bg=t.bg_root,
            fg=t.fg_primary,
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT, padx=(0, 8))

        self.sched_time_entry = tk.Entry(
            time_row,
            width=8,
            bg=t.bg_input,
            fg=t.fg_primary,
            font=("Segoe UI", 9, "bold"),
            relief=tk.SOLID,
            bd=1,
            justify=tk.CENTER,
        )
        self.sched_time_entry.insert(0, sched_time)
        self.sched_time_entry.pack(side=tk.LEFT, padx=(0, 10))

        # Automation Safety Options
        opt_box = tk.Frame(card, bg=t.bg_card)
        opt_box.pack(fill=tk.X, pady=(0, 12))

        self.sched_battery_guard = tk.BooleanVar(value=True)
        chk_bat = tk.Checkbutton(
            opt_box,
            text="AC Power Safety Guard: Pause scheduled run if laptop is on battery power",
            variable=self.sched_battery_guard,
            bg=t.bg_card,
            fg=t.fg_primary,
            activebackground=t.bg_card,
            selectcolor=t.bg_input,
            font=("Segoe UI", 9),
        )
        chk_bat.pack(anchor=tk.W, pady=(2, 2))

        self.sched_cpu_guard = tk.BooleanVar(value=True)
        chk_cpu = tk.Checkbutton(
            opt_box,
            text="CPU Utilization Guard: Delay update if CPU load exceeds 90%",
            variable=self.sched_cpu_guard,
            bg=t.bg_card,
            fg=t.fg_primary,
            activebackground=t.bg_card,
            selectcolor=t.bg_input,
            font=("Segoe UI", 9),
        )
        chk_cpu.pack(anchor=tk.W, pady=(2, 2))

        # Action Buttons row
        btn_row = tk.Frame(card, bg=t.bg_card)
        btn_row.pack(fill=tk.X, pady=(4, 0))

        def _apply_schedule_direct():
            t_val = self.sched_time_entry.get().strip()
            if sched_mgr:
                ok, msg = sched_mgr.create_daily_task(t_val)
                if ok:
                    self.lbl_sched_status.config(text=f"● Active Daily Schedule ({t_val})", fg="#059669")
                    messagebox.showinfo("Schedule Applied", msg, parent=self)
                else:
                    messagebox.showerror("Schedule Error", msg, parent=self)

        def _disable_schedule_direct():
            if sched_mgr:
                ok, msg = sched_mgr.delete_task()
                if ok:
                    self.lbl_sched_status.config(text="○ Daily Schedule: Inactive (Disabled)", fg=t.fg_muted)
                    messagebox.showinfo("Schedule Disabled", msg, parent=self)
                else:
                    messagebox.showerror("Schedule Error", msg, parent=self)

        btn_enable = RoundedButton(
            btn_row,
            text="✓ Apply Daily Schedule",
            command=_apply_schedule_direct,
            bg_color=t.accent_burgundy,
            fg_color="#ffffff",
            radius=6,
            height=32,
            font=("Segoe UI", 9, "bold"),
            padding=(14, 6),
        )
        btn_enable.pack(side=tk.LEFT, padx=(0, 8))

        btn_disable = RoundedButton(
            btn_row,
            text="Disable Schedule",
            command=_disable_schedule_direct,
            bg_color="#ffffff",
            fg_color="#b91c1c",
            border_color="#fca5a5",
            radius=6,
            height=32,
            font=("Segoe UI", 9),
            padding=(12, 6),
        )
        btn_disable.pack(side=tk.LEFT, padx=(0, 8))

        btn_modal = RoundedButton(
            btn_row,
            text="Open Advanced View...",
            command=self._do_open_schedule,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            border_color=t.border,
            radius=6,
            height=32,
            font=("Segoe UI", 9),
            padding=(12, 6),
        )
        btn_modal.pack(side=tk.LEFT)

    def _build_backup_tab(self) -> None:
        t = self.theme
        card = tk.Frame(self.tab_backup, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=14)
        card.pack(fill=tk.BOTH, expand=True)

        lbl_head = tk.Label(card, text="Software Backup & Machine Provisioning", bg=t.bg_card, fg=t.fg_primary, font=("Segoe UI", 10, "bold"), anchor="w")
        lbl_head.pack(anchor=tk.W)

        lbl_desc = tk.Label(
            card,
            text="Save a complete snapshot manifest of all installed software to restore on new PCs, or export spreadsheets.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
        )
        lbl_desc.pack(anchor=tk.W, pady=(2, 12))

        b_row = tk.Frame(card, bg=t.bg_card)
        b_row.pack(fill=tk.X, pady=(0, 10))

        btn_bk = RoundedButton(
            b_row,
            text="📤 Backup Apps Manifest",
            command=self._do_backup_stack,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            border_color=t.border,
            radius=6,
            height=32,
            font=("Segoe UI", 9),
            padding=(14, 6),
        )
        btn_bk.pack(side=tk.LEFT, padx=(0, 8))

        btn_rs = RoundedButton(
            b_row,
            text="📥 Restore Backup Manifest",
            command=self._do_restore_stack,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            border_color=t.border,
            radius=6,
            height=32,
            font=("Segoe UI", 9),
            padding=(14, 6),
        )
        btn_rs.pack(side=tk.LEFT, padx=(0, 8))

        btn_exp = RoundedButton(
            b_row,
            text="📋 Export Inventory Report",
            command=self._do_export_inventory,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            border_color=t.border,
            radius=6,
            height=32,
            font=("Segoe UI", 9),
            padding=(14, 6),
        )
        btn_exp.pack(side=tk.LEFT)

    def _build_maintenance_tab(self) -> None:
        t = self.theme

        # 1. Disk Space Reclaimer Card
        card_disk = tk.Frame(self.tab_maintenance, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=12)
        card_disk.pack(fill=tk.X, pady=(0, 10))

        lbl_dhead = tk.Label(card_disk, text="🧹 Disk Space Reclaimer & Cache Purge", bg=t.bg_card, fg=t.fg_primary, font=("Segoe UI", 10, "bold"), anchor="w")
        lbl_dhead.pack(anchor=tk.W)

        lbl_ddesc = tk.Label(
            card_disk,
            text="Scan and reclaim disk space from WinGet installer caches, diagnostic logs, and temporary setup residues.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
        )
        lbl_ddesc.pack(anchor=tk.W, pady=(2, 8))

        btn_disk = RoundedButton(
            card_disk,
            text="🧹 Launch Disk Space Reclaimer",
            command=self._do_open_disk_cleanup,
            bg_color=t.accent_burgundy,
            fg_color="#ffffff",
            border_color=t.accent_crimson,
            radius=6,
            height=30,
            font=("Segoe UI", 9, "bold"),
            padding=(14, 4),
        )
        btn_disk.pack(anchor=tk.W)

        # 2. Windows Startup & Autorun Optimizer Card
        card_startup = tk.Frame(self.tab_maintenance, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=12)
        card_startup.pack(fill=tk.X, pady=(0, 10))

        lbl_shead = tk.Label(card_startup, text="🚀 Windows Startup & Autorun Optimizer", bg=t.bg_card, fg=t.fg_primary, font=("Segoe UI", 10, "bold"), anchor="w")
        lbl_shead.pack(anchor=tk.W)

        lbl_sdesc = tk.Label(
            card_startup,
            text="Inspect and toggle background apps running at logon across HKCU, HKLM, and startup folders to accelerate boot times.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
        )
        lbl_sdesc.pack(anchor=tk.W, pady=(2, 8))

        btn_startup = RoundedButton(
            card_startup,
            text="🚀 Manage Startup Applications",
            command=self._do_open_startup_manager,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            border_color=t.border,
            radius=6,
            height=30,
            font=("Segoe UI", 9),
            padding=(14, 4),
        )
        btn_startup.pack(anchor=tk.W)

        # 3. Complete Application Uninstaller Card
        card_uninst = tk.Frame(self.tab_maintenance, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=12)
        card_uninst.pack(fill=tk.X)

        lbl_head = tk.Label(card_uninst, text="🗑️ Complete Application Uninstaller", bg=t.bg_card, fg=t.accent_crimson, font=("Segoe UI", 10, "bold"), anchor="w")
        lbl_head.pack(anchor=tk.W)

        lbl_desc = tk.Label(
            card_uninst,
            text="Permanently remove Software & Package Updater, shortcuts, registry keys, and cache files with nothing left behind.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
        )
        lbl_desc.pack(anchor=tk.W, pady=(2, 8))

        btn_uninst = RoundedButton(
            card_uninst,
            text="🗑️ Launch Complete Uninstaller (Uninstall.exe)",
            command=self._do_uninstall_app,
            bg_color="#fee2e2",
            fg_color="#b91c1c",
            border_color="#fca5a5",
            radius=6,
            height=30,
            font=("Segoe UI", 9, "bold"),
            padding=(14, 4),
        )
        btn_uninst.pack(anchor=tk.W)

    def _do_refresh_sources(self) -> None:
        if self.on_refresh_sources:
            self.on_refresh_sources()
        elif hasattr(self.master, "_refresh_sources_dialog"):
            self.master._refresh_sources_dialog()

    def _do_open_sources(self) -> None:
        if self.on_open_sources:
            self.on_open_sources()
        elif hasattr(self.master, "_open_sources_dialog"):
            self.master._open_sources_dialog()

    def _do_open_exclusions(self) -> None:
        if self.on_open_exclusions:
            self.on_open_exclusions()
        elif hasattr(self.master, "_open_exclusions_dialog"):
            self.master._open_exclusions_dialog()

    def _do_open_schedule(self) -> None:
        if self.on_open_schedule:
            self.on_open_schedule()
        elif hasattr(self.master, "_open_schedule_dialog"):
            self.master._open_schedule_dialog()

    def _do_open_runtimes(self) -> None:
        if self.on_open_runtimes:
            self.on_open_runtimes()
        elif hasattr(self.master, "_open_runtimes_manager"):
            self.master._open_runtimes_manager()

    def _do_open_disk_cleanup(self) -> None:
        if self.on_open_disk_cleanup:
            self.on_open_disk_cleanup()
        elif hasattr(self.master, "_open_disk_cleanup"):
            self.master._open_disk_cleanup()

    def _do_open_startup_manager(self) -> None:
        if self.on_open_startup_manager:
            self.on_open_startup_manager()
        elif hasattr(self.master, "_open_startup_manager"):
            self.master._open_startup_manager()

    def _do_backup_stack(self) -> None:
        if self.on_backup_stack:
            self.on_backup_stack()
        elif hasattr(self.master, "_export_software_backup"):
            self.master._export_software_backup()

    def _do_restore_stack(self) -> None:
        if self.on_restore_stack:
            self.on_restore_stack()
        elif hasattr(self.master, "_import_software_backup"):
            self.master._import_software_backup()

    def _do_export_inventory(self) -> None:
        if self.on_export_inventory:
            self.on_export_inventory()
        elif hasattr(self.master, "_export_report_dialog"):
            self.master._export_report_dialog()

    def _do_uninstall_app(self) -> None:
        if self.on_uninstall_app:
            self.on_uninstall_app()
        elif hasattr(self.master, "_launch_app_uninstaller"):
            self.master._launch_app_uninstaller()

    def _save_and_close(self) -> None:
        # Save font scale
        old_scale = getattr(self.config, "font_scale", "normal")
        new_scale = self.font_scale_var.get()
        self.config.font_scale = new_scale

        # Save theme
        old_theme = getattr(self.config, "theme", "light")
        new_theme = self.theme_var.get()
        self.config.theme = new_theme

        # Save safety flags
        self.config.smooth_animations = self.anim_var.get()
        self.config.ignore_legacy_vcredist = self.vcredist_var.get()
        self.config.create_restore_point = self.restore_var.get()
        self.config.auto_close_apps = self.autoclose_var.get()
        self.config.cleanup_temp_cache = self.cleanup_var.get()
        self.config.auto_scan_on_startup = self.autoscan_var.get()

        # Save manager states
        for k, v in self.manager_vars.items():
            self.config.enabled_managers[k] = v.get()

        self.config.save_settings()

        # Fire callbacks if values changed
        if old_theme != new_theme and self.on_theme_changed:
            self.on_theme_changed(new_theme)
        if old_scale != new_scale and self.on_font_scale_changed:
            self.on_font_scale_changed(new_scale)
        if self.on_settings_saved:
            self.on_settings_saved()

        self.destroy()


class UpdateSummaryDialog(tk.Toplevel):
    """Modern velvet glass modal displaying batch update results, failure diagnosis, and retry capabilities."""

    def __init__(
        self,
        parent: tk.Widget,
        summary,
        failed_items: Optional[List[ProgramItem]] = None,
        on_retry: Optional[Callable[[List[ProgramItem]], None]] = None,
        theme: Optional[ThemeColors] = None,
    ):
        super().__init__(parent)
        self.title("Update Routine Completed")
        self.geometry("620x520" if (failed_items and len(failed_items) > 0) else "540x360")
        self.minsize(500, 340)
        self.summary = summary
        self.failed_items = failed_items or []
        self.on_retry = on_retry
        self.theme = theme or DARK_THEME
        try:
            apply_native_window_styling(self, self.theme)
        except Exception:
            pass
        self.configure(bg=self.theme.bg_root)

        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self) -> None:
        t = self.theme

        # Header Frame
        header = tk.Frame(self, bg=t.bg_card, padx=20, pady=16, highlightbackground=t.border, highlightthickness=1)
        header.pack(fill=tk.X)

        title_text = "🎉 Update Routine Completed" if self.summary.failed_count == 0 else "⚠️ Update Routine Completed with Warnings"
        lbl_title = tk.Label(
            header,
            text=title_text,
            bg=t.bg_card,
            fg=t.accent_emerald if self.summary.failed_count == 0 else t.accent_burgundy,
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        lbl_title.pack(anchor=tk.W)

        lbl_sub = tk.Label(
            header,
            text="All system software statuses have been reconciled with repositories.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 9),
            anchor="w",
        )
        lbl_sub.pack(anchor=tk.W, pady=(2, 0))

        # Metric Tiles Container
        body = tk.Frame(self, bg=t.bg_root, padx=20, pady=16)
        body.pack(fill=tk.BOTH, expand=True)

        tiles_frame = tk.Frame(body, bg=t.bg_root)
        tiles_frame.pack(fill=tk.X, pady=(0, 12))

        metrics = [
            ("Updated", str(self.summary.updated_count), "#10b981", "#ecfdf5"),
            ("Failed", str(self.summary.failed_count), "#ef4444" if self.summary.failed_count > 0 else "#6b7280", "#fef2f2" if self.summary.failed_count > 0 else "#f3f4f6"),
            ("Skipped", str(self.summary.skipped_count), "#f59e0b", "#fffbeb"),
            ("Simulated", str(self.summary.simulated_count), "#3b82f6", "#eff6ff"),
        ]

        for i, (m_title, m_val, col_fg, col_bg) in enumerate(metrics):
            card = tk.Frame(tiles_frame, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=12, pady=10)
            card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0 if i == 0 else 8, 0))

            lbl_v = tk.Label(card, text=m_val, bg=t.bg_card, fg=col_fg, font=("Segoe UI", 16, "bold"))
            lbl_v.pack()

            lbl_lbl = tk.Label(card, text=m_title, bg=t.bg_card, fg=t.fg_muted, font=("Segoe UI", 8, "bold"))
            lbl_lbl.pack()

        # Detailed Failure Diagnosis if any items failed
        if self.failed_items and len(self.failed_items) > 0:
            diag_frame = tk.Frame(body, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=12, pady=10)
            diag_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

            lbl_fhead = tk.Label(
                diag_frame,
                text="Diagnostic Failure Details (Inspect issues below):",
                bg=t.bg_card,
                fg=t.accent_crimson,
                font=("Segoe UI", 9, "bold"),
                anchor="w",
            )
            lbl_fhead.pack(anchor=tk.W, pady=(0, 6))

            # Scrollable text list
            txt_box = tk.Text(
                diag_frame,
                bg=t.bg_root,
                fg=t.fg_primary,
                font=("Cascadia Code", 8),
                height=8,
                relief=tk.FLAT,
                highlightbackground=t.border,
                highlightthickness=1,
                padx=8,
                pady=6,
            )
            txt_box.pack(fill=tk.BOTH, expand=True)

            for it in self.failed_items:
                reason = it.notes or "Update installer reported failure."
                txt_box.insert(tk.END, f"• {it.name} ({it.installed_version} -> {it.latest_version or 'Latest'})\n")
                txt_box.insert(tk.END, f"  Issue: {reason}\n\n")

            txt_box.config(state="disabled")

        # Bottom Bar
        bottom = tk.Frame(self, bg=t.bg_sidebar, padx=20, pady=12, highlightbackground=t.border, highlightthickness=1)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)

        btn_done = RoundedButton(
            bottom,
            text="Done",
            command=self.destroy,
            bg_color=t.accent_burgundy,
            fg_color="#ffffff",
            hover_bg=t.accent_burgundy_hover,
            radius=6,
            font=("Segoe UI", 9, "bold"),
            width=100,
            height=32,
            parent_bg=t.bg_sidebar,
        )
        btn_done.pack(side=tk.RIGHT)

        if self.failed_items and len(self.failed_items) > 0 and self.on_retry:
            btn_retry = RoundedButton(
                bottom,
                text="🔄 Retry Failed Updates",
                command=self._do_retry,
                bg_color=t.bg_button,
                fg_color=t.fg_primary,
                hover_bg=t.bg_button_hover,
                radius=6,
                font=("Segoe UI", 9),
                width=160,
                height=32,
                parent_bg=t.bg_sidebar,
            )
            btn_retry.pack(side=tk.RIGHT, padx=(0, 8))

    def _do_retry(self) -> None:
        items = list(self.failed_items)
        self.destroy()
        if self.on_retry:
            self.on_retry(items)



class AppUpdateTrackerDialog(tk.Toplevel):
    """Interactive dashboard dialog displaying tracked available updates, pending durations, and evolution history."""

    def __init__(
        self,
        parent: tk.Widget,
        tracker: UpdateTracker,
        theme: Optional[ThemeColors] = None,
        on_update_requested: Optional[Callable[[List[str]], None]] = None,
    ):
        super().__init__(parent)
        self.title("App Update Tracker — Windows 11 Edition")
        self.geometry("820x560")
        self.minsize(700, 440)
        self.tracker = tracker
        self.theme = theme or DARK_THEME
        try:
            apply_native_window_styling(self, self.theme)
        except Exception:
            pass
        self.on_update_requested = on_update_requested
        self.current_filter = "all"

        self.configure(bg=self.theme.bg_root)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._refresh_data()

    def _build_ui(self) -> None:
        t = self.theme
        root_frame = tk.Frame(self, bg=t.bg_root, padx=20, pady=16)
        root_frame.pack(fill=tk.BOTH, expand=True)

        # Header Title
        header_frame = tk.Frame(root_frame, bg=t.bg_root)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        lbl_title = tk.Label(
            header_frame,
            text="📊 App Update Tracker",
            bg=t.bg_root,
            fg=t.accent_burgundy,
            font=("Segoe UI", 13, "bold"),
        )
        lbl_title.pack(anchor=tk.W)

        lbl_sub = tk.Label(
            header_frame,
            text="Continuously tracks when updates become available for installed applications, measuring pending duration and version jumps.",
            bg=t.bg_root,
            fg=t.fg_secondary,
            font=("Segoe UI", 9),
        )
        lbl_sub.pack(anchor=tk.W, pady=(2, 0))

        # Metrics Ribbon (4 Cards)
        self.metrics_frame = tk.Frame(root_frame, bg=t.bg_root)
        self.metrics_frame.pack(fill=tk.X, pady=(0, 12))

        self.card_total = self._create_metric_card(self.metrics_frame, "TOTAL TRACKED", "0", "#334155")
        self.card_pending = self._create_metric_card(self.metrics_frame, "PENDING UPDATES", "0", "#881337")
        self.card_updated = self._create_metric_card(self.metrics_frame, "RESOLVED / CURRENT", "0", "#059669")
        self.card_oldest = self._create_metric_card(self.metrics_frame, "OLDEST PENDING", "0d", "#d97706")

        # Filter Tabs Row
        filter_bar = tk.Frame(root_frame, bg=t.bg_root)
        filter_bar.pack(fill=tk.X, pady=(0, 8))

        self.btn_tab_all = RoundedButton(
            filter_bar,
            text="All Tracked",
            command=lambda: self._set_filter("all"),
            bg_color=t.accent_burgundy,
            fg_color="#ffffff",
            radius=6,
            height=26,
            font=("Segoe UI", 8, "bold"),
            padding=(8, 2),
        )
        self.btn_tab_all.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_tab_pending = RoundedButton(
            filter_bar,
            text="⏳ Pending Only",
            command=lambda: self._set_filter("available"),
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            radius=6,
            height=26,
            font=("Segoe UI", 8),
            padding=(8, 2),
        )
        self.btn_tab_pending.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_tab_updated = RoundedButton(
            filter_bar,
            text="✅ Updated",
            command=lambda: self._set_filter("updated"),
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            radius=6,
            height=26,
            font=("Segoe UI", 8),
            padding=(8, 2),
        )
        self.btn_tab_updated.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_tab_failed = RoundedButton(
            filter_bar,
            text="❌ Failed Attempts",
            command=lambda: self._set_filter("failed"),
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            radius=6,
            height=26,
            font=("Segoe UI", 8),
            padding=(8, 2),
        )
        self.btn_tab_failed.pack(side=tk.LEFT, padx=(0, 4))

        # Main Table Container
        table_frame = tk.Frame(
            root_frame,
            bg=t.bg_card,
            highlightbackground=t.border,
            highlightthickness=1,
        )
        table_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("Name", "Source", "Installed", "Available", "PendingDays", "FirstSeen", "Status")
        self.tree = ttk.Treeview(
            table_frame,
            columns=cols,
            show="headings",
            selectmode="browse",
        )
        self.tree.heading("Name", text="Application Name")
        self.tree.heading("Source", text="Manager")
        self.tree.heading("Installed", text="Installed Ver")
        self.tree.heading("Available", text="Available Target")
        self.tree.heading("PendingDays", text="Days Pending")
        self.tree.heading("FirstSeen", text="First Detected")
        self.tree.heading("Status", text="Tracking State")

        self.tree.column("Name", width=190, anchor="w")
        self.tree.column("Source", width=80, anchor="center")
        self.tree.column("Installed", width=95, anchor="center")
        self.tree.column("Available", width=105, anchor="center")
        self.tree.column("PendingDays", width=85, anchor="center")
        self.tree.column("FirstSeen", width=110, anchor="center")
        self.tree.column("Status", width=95, anchor="center")

        scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bottom Action Controls
        bottom_frame = tk.Frame(root_frame, bg=t.bg_root)
        bottom_frame.pack(fill=tk.X, pady=(12, 0))

        self.lbl_status = tk.Label(
            bottom_frame,
            text="",
            bg=t.bg_root,
            fg=t.fg_secondary,
            font=("Segoe UI", 8),
        )
        self.lbl_status.pack(side=tk.LEFT)

        btn_close = RoundedButton(
            bottom_frame,
            text="Close",
            command=self.destroy,
            bg_color=t.accent_burgundy,
            fg_color="#ffffff",
            radius=6,
            height=28,
            font=("Segoe UI", 9, "bold"),
            width=80,
            parent_bg=t.bg_root,
        )
        btn_close.pack(side=tk.RIGHT)

        btn_clear = RoundedButton(
            bottom_frame,
            text="🧹 Clear Resolved",
            command=self._clear_resolved,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            radius=6,
            height=28,
            font=("Segoe UI", 8),
            width=120,
            parent_bg=t.bg_root,
        )
        btn_clear.pack(side=tk.RIGHT, padx=(0, 6))

        btn_refresh = RoundedButton(
            bottom_frame,
            text="🔄 Refresh",
            command=self._refresh_data,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            radius=6,
            height=28,
            font=("Segoe UI", 8),
            width=90,
            parent_bg=t.bg_root,
        )
        btn_refresh.pack(side=tk.RIGHT, padx=(0, 6))

    def _create_metric_card(self, parent: tk.Widget, label: str, init_val: str, color: str) -> Dict[str, Any]:
        t = self.theme
        card = tk.Frame(
            parent,
            bg=t.bg_card,
            padx=12,
            pady=8,
            highlightbackground=t.border,
            highlightthickness=1,
        )
        card.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        lbl_caption = tk.Label(card, text=label, bg=t.bg_card, fg=t.fg_secondary, font=("Segoe UI", 7, "bold"), anchor="w")
        lbl_caption.pack(anchor=tk.W)

        lbl_val = tk.Label(card, text=init_val, bg=t.bg_card, fg=color, font=("Segoe UI", 14, "bold"), anchor="w")
        lbl_val.pack(anchor=tk.W)

        return {"frame": card, "val": lbl_val}

    def _set_filter(self, filter_name: str) -> None:
        self.current_filter = filter_name
        t = self.theme

        # Reset button colors
        for btn, name in [
            (self.btn_tab_all, "all"),
            (self.btn_tab_pending, "available"),
            (self.btn_tab_updated, "updated"),
            (self.btn_tab_failed, "failed"),
        ]:
            if name == filter_name:
                btn.config(bg=t.accent_burgundy, fg="#ffffff")
            else:
                btn.config(bg=t.bg_button, fg=t.fg_primary)

        self._refresh_data()

    def _refresh_data(self) -> None:
        metrics = self.tracker.get_metrics()
        self.card_total["val"].config(text=str(metrics["total_tracked"]))
        self.card_pending["val"].config(text=str(metrics["pending_count"]))
        self.card_updated["val"].config(text=str(metrics["updated_count"]))
        self.card_oldest["val"].config(text=f"{metrics['oldest_pending_days']}d")

        # Clear tree
        for row in self.tree.get_children():
            self.tree.delete(row)

        filter_arg = None if self.current_filter == "all" else self.current_filter
        items = self.tracker.get_tracked_items(filter_arg)

        for it in items:
            dt_str = it.first_detected[:10] if len(it.first_detected) >= 10 else it.first_detected
            status_display = {
                "available": f"⏳ Pending ({it.days_pending}d)",
                "updated": "✅ Up to Date",
                "failed": "❌ Failed",
                "skipped": "⏭️ Skipped",
            }.get(it.status, it.status.capitalize())

            self.tree.insert(
                "",
                tk.END,
                values=(
                    it.name,
                    it.source.upper(),
                    it.installed_version,
                    it.available_version,
                    f"{it.days_pending} day{'s' if it.days_pending != 1 else ''}",
                    dt_str,
                    status_display,
                ),
            )

        self.lbl_status.config(text=f"Showing {len(items)} tracked update records.")

    def _clear_resolved(self) -> None:
        count = self.tracker.clear_resolved()
        self._refresh_data()
        self.lbl_status.config(text=f"Cleared {count} resolved records.")



class GameRuntimesDialog(tk.Toplevel):
    """Interactive Gaming & System Runtimes Manager.
    Automatically scans the Windows registry and file system for all essential Visual C++,
    .NET Desktop, DirectX, and media runtimes, allowing one-click batch installation of missing dependencies.
    """

    def __init__(
        self,
        parent: tk.Widget,
        theme: Optional[ThemeColors] = None,
        on_runtime_installed: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.title("Gaming & System Runtimes Manager — Windows 11")
        self.geometry("860x640")
        self.minsize(740, 520)
        self.theme = theme or DARK_THEME
        try:
            apply_native_window_styling(self, self.theme)
        except Exception:
            pass

        self.on_runtime_installed = on_runtime_installed
        self.current_filter = "all"
        self.scan_results: List[Any] = []
        self._is_busy = False
        self.msg_queue: queue.Queue = queue.Queue()

        from winget_updater.engine.runtimes import RuntimesManager
        self.runtimes_mgr = RuntimesManager()

        self.configure(bg=self.theme.bg_root)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._process_queue()
        self._start_async_scan()

    def _process_queue(self) -> None:
        """Processes cross-thread asynchronous UI messages."""
        try:
            while True:
                msg_type, payload = self.msg_queue.get_nowait()
                if msg_type == "SCAN_COMPLETE":
                    self._on_scan_completed(payload)
                elif msg_type == "SCAN_FAILED":
                    self._on_scan_failed(payload)
                elif msg_type == "STATUS":
                    self.lbl_status.config(text=payload)
                elif msg_type == "PROGRESS":
                    self.progress_bar.config(value=payload)
                elif msg_type == "JOB_DONE":
                    successes, failures, total = payload
                    self._on_install_job_done(successes, failures, total)
        except queue.Empty:
            pass
        except Exception:
            pass
        finally:
            if self.winfo_exists():
                self.after(50, self._process_queue)

    def _build_ui(self) -> None:
        t = self.theme
        root_frame = tk.Frame(self, bg=t.bg_root, padx=20, pady=16)
        root_frame.pack(fill=tk.BOTH, expand=True)

        # Header Title Area
        header = tk.Frame(root_frame, bg=t.bg_root)
        header.pack(fill=tk.X, pady=(0, 12))

        lbl_title = tk.Label(
            header,
            text="🎮 Gaming & System Runtimes Manager",
            bg=t.bg_root,
            fg=t.fg_primary,
            font=("Segoe UI", 16, "bold"),
            anchor="w",
        )
        lbl_title.pack(anchor=tk.W)

        lbl_sub = tk.Label(
            header,
            text="Automated scan & repair for Microsoft Visual C++, .NET Desktop, DirectX, and OpenAL gaming prerequisites.",
            bg=t.bg_root,
            fg=t.fg_muted,
            font=("Segoe UI", 9),
            anchor="w",
        )
        lbl_sub.pack(anchor=tk.W, pady=(2, 0))

        # Metrics Overview Row
        self.metrics_frame = tk.Frame(root_frame, bg=t.bg_root)
        self.metrics_frame.pack(fill=tk.X, pady=(0, 12))

        self.card_total = self._create_metric_card(self.metrics_frame, "Analyzed", "0", t.fg_primary)
        self.card_healthy = self._create_metric_card(self.metrics_frame, "Healthy", "0", "#10b981")
        self.card_missing = self._create_metric_card(self.metrics_frame, "Missing", "0", "#ef4444")
        self.card_updates = self._create_metric_card(self.metrics_frame, "Updatable", "0", "#f59e0b")

        # Category Filter Pills
        filter_bar = tk.Frame(root_frame, bg=t.bg_root)
        filter_bar.pack(fill=tk.X, pady=(0, 8))

        self.filter_buttons: Dict[str, tk.Button] = {}
        filters = [
            ("all", "All Runtimes"),
            ("vcredist", "Visual C++ (2005-2022)"),
            ("dotnet", ".NET Desktop"),
            ("directx_media", "DirectX & Multimedia"),
            ("missing_only", "Missing / Required"),
        ]

        for fid, flabel in filters:
            btn = tk.Button(
                filter_bar,
                text=flabel,
                command=lambda f=fid: self._set_filter(f),
                bg=t.accent_burgundy if fid == self.current_filter else t.bg_card,
                fg="#ffffff" if fid == self.current_filter else t.fg_secondary,
                activebackground=t.accent_burgundy_hover,
                activeforeground="#ffffff",
                relief=tk.FLAT,
                bd=0,
                padx=10,
                pady=4,
                font=("Segoe UI", 8, "bold" if fid == self.current_filter else "normal"),
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=(0, 6))
            self.filter_buttons[fid] = btn

        # Data Treeview inside Framed Card
        tree_card = tk.Frame(
            root_frame,
            bg=t.bg_card,
            highlightbackground=t.border,
            highlightthickness=1,
            padx=2,
            pady=2,
        )
        tree_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        cols = ("name", "arch", "category", "installed", "status", "winget_id")
        self.tree = ttk.Treeview(
            tree_card,
            columns=cols,
            show="headings",
            selectmode="browse",
        )

        self.tree.heading("name", text="Runtime Dependency")
        self.tree.heading("arch", text="Arch")
        self.tree.heading("category", text="Component Class")
        self.tree.heading("installed", text="Installed Build")
        self.tree.heading("status", text="Health Status")
        self.tree.heading("winget_id", text="Winget Identifier")

        self.tree.column("name", width=260, anchor=tk.W)
        self.tree.column("arch", width=60, anchor=tk.CENTER)
        self.tree.column("category", width=140, anchor=tk.W)
        self.tree.column("installed", width=100, anchor=tk.CENTER)
        self.tree.column("status", width=170, anchor=tk.W)
        self.tree.column("winget_id", width=180, anchor=tk.W)

        tree_scroll = ttk.Scrollbar(tree_card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind("<<TreeviewSelect>>", self._on_item_selected)

        # Bottom Details Card
        self.desc_card = tk.Frame(
            root_frame,
            bg=t.bg_card,
            highlightbackground=t.border,
            highlightthickness=1,
            padx=12,
            pady=8,
        )
        self.desc_card.pack(fill=tk.X, pady=(0, 10))

        self.lbl_selected_title = tk.Label(
            self.desc_card,
            text="Select a runtime component above to view gaming compatibility details.",
            bg=t.bg_card,
            fg=t.fg_primary,
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        )
        self.lbl_selected_title.pack(anchor=tk.W)

        self.lbl_selected_desc = tk.Label(
            self.desc_card,
            text="Microsoft Visual C++ and .NET runtimes allow games, emulators, and 3D applications to execute without missing DLL crashes.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
            wraplength=800,
            justify=tk.LEFT,
        )
        self.lbl_selected_desc.pack(anchor=tk.W, pady=(2, 0))

        # Live Progress & Action Footer
        footer = tk.Frame(root_frame, bg=t.bg_root)
        footer.pack(fill=tk.X)

        self.progress_bar = ttk.Progressbar(footer, orient=tk.HORIZONTAL, mode="determinate")
        self.progress_bar.pack(fill=tk.X, pady=(0, 6))

        action_row = tk.Frame(footer, bg=t.bg_root)
        action_row.pack(fill=tk.X)

        self.lbl_status = tk.Label(
            action_row,
            text="Initializing runtime scan...",
            bg=t.bg_root,
            fg=t.fg_muted,
            font=("Segoe UI", 8),
            anchor="w",
        )
        self.lbl_status.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.btn_rescan = tk.Button(
            action_row,
            text="🔄 Re-Scan",
            command=self._start_async_scan,
            bg=t.bg_card,
            fg=t.fg_secondary,
            activebackground=t.border,
            relief=tk.FLAT,
            bd=0,
            padx=12,
            pady=6,
            font=("Segoe UI", 9),
            cursor="hand2",
        )
        self.btn_rescan.pack(side=tk.RIGHT, padx=(6, 0))

        self.btn_install_selected = tk.Button(
            action_row,
            text="Install Selected",
            command=self._install_selected,
            bg=t.bg_card,
            fg=t.fg_primary,
            activebackground=t.border,
            relief=tk.FLAT,
            bd=0,
            padx=14,
            pady=6,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
            state="disabled",
        )
        self.btn_install_selected.pack(side=tk.RIGHT, padx=(6, 0))

        self.btn_batch_install = tk.Button(
            action_row,
            text="⚡ Install All Missing Runtimes",
            command=self._install_all_missing,
            bg=t.accent_burgundy,
            fg="#ffffff",
            activebackground=t.accent_burgundy_hover,
            activeforeground="#ffffff",
            relief=tk.FLAT,
            bd=0,
            padx=16,
            pady=6,
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        self.btn_batch_install.pack(side=tk.RIGHT)

    def _create_metric_card(self, parent: tk.Widget, title: str, init_val: str, val_color: str) -> Dict[str, Any]:
        t = self.theme
        card = tk.Frame(
            parent,
            bg=t.bg_card,
            highlightbackground=t.border,
            highlightthickness=1,
            padx=12,
            pady=8,
        )
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        lbl_val = tk.Label(card, text=init_val, bg=t.bg_card, fg=val_color, font=("Segoe UI", 16, "bold"))
        lbl_val.pack()

        lbl_t = tk.Label(card, text=title, bg=t.bg_card, fg=t.fg_muted, font=("Segoe UI", 8, "bold"))
        lbl_t.pack()

        return {"frame": card, "val": lbl_val, "title": lbl_t}

    def _set_filter(self, fid: str) -> None:
        self.current_filter = fid
        t = self.theme
        for f, btn in self.filter_buttons.items():
            if f == fid:
                btn.config(bg=t.accent_burgundy, fg="#ffffff", font=("Segoe UI", 8, "bold"))
            else:
                btn.config(bg=t.bg_card, fg=t.fg_secondary, font=("Segoe UI", 8, "normal"))
        self._render_tree()

    def _start_async_scan(self) -> None:
        if self._is_busy:
            return
        self._is_busy = True
        self.lbl_status.config(text="Scanning system registry and file system for runtime prerequisites...")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start(15)
        self.btn_rescan.config(state="disabled")
        self.btn_batch_install.config(state="disabled")

        def worker():
            try:
                results = self.runtimes_mgr.scan_all_runtimes()
                self.msg_queue.put(("SCAN_COMPLETE", results))
            except Exception as e:
                self.msg_queue.put(("SCAN_FAILED", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_scan_completed(self, results: List[Any]) -> None:
        self._is_busy = False
        self.scan_results = results
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate", value=0)
        self.btn_rescan.config(state="normal")
        self.btn_batch_install.config(state="normal")

        # Update metric cards
        total = len(results)
        healthy = len([r for r in results if not r.is_missing and not r.is_upgradable])
        missing = len([r for r in results if r.is_missing])
        upgradable = len([r for r in results if r.is_upgradable])

        self.card_total["val"].config(text=str(total))
        self.card_healthy["val"].config(text=str(healthy))
        self.card_missing["val"].config(text=str(missing))
        self.card_updates["val"].config(text=str(upgradable))

        self.lbl_status.config(
            text=f"Scan complete: {healthy} runtimes healthy, {missing} missing, {upgradable} updates available."
        )

        if missing == 0 and upgradable == 0:
            self.btn_batch_install.config(text="✓ All Runtimes Healthy", state="disabled")
        else:
            self.btn_batch_install.config(
                text=f"⚡ Install All Missing ({missing + upgradable})",
                state="normal"
            )

        self._render_tree()

    def _on_scan_failed(self, err: str) -> None:
        self._is_busy = False
        self.progress_bar.stop()
        self.btn_rescan.config(state="normal")
        self.lbl_status.config(text=f"Scan failed: {err}")

    def _render_tree(self) -> None:
        for it in self.tree.get_children():
            self.tree.delete(it)

        from winget_updater.engine.runtimes import RuntimeCategory

        filtered: List[Any] = []
        for r in self.scan_results:
            if self.current_filter == "vcredist" and r.definition.category != RuntimeCategory.VCREDIST:
                continue
            elif self.current_filter == "dotnet" and r.definition.category != RuntimeCategory.DOTNET:
                continue
            elif self.current_filter == "directx_media" and r.definition.category not in (
                RuntimeCategory.DIRECTX_GRAPHICS, RuntimeCategory.AUDIO_MEDIA
            ):
                continue
            elif self.current_filter == "missing_only" and not (r.is_missing or r.is_upgradable):
                continue
            filtered.append(r)

        for r in filtered:
            status_text = "✅ Installed" if not r.is_missing and not r.is_upgradable else (
                "❌ Missing from System" if r.is_missing else "🟡 Update Available"
            )
            item_id = self.tree.insert(
                "",
                tk.END,
                values=(
                    r.definition.name,
                    r.definition.architecture.upper(),
                    r.definition.category.value,
                    r.installed_version or "—",
                    status_text,
                    r.definition.winget_id,
                ),
            )
            # Store object reference on item
            self.tree.item(item_id, tags=(r.definition.id,))

    def _on_item_selected(self, event) -> None:
        selected = self.tree.selection()
        if not selected:
            self.btn_install_selected.config(state="disabled")
            return

        item_vals = self.tree.item(selected[0], "values")
        if not item_vals:
            return

        name = item_vals[0]
        r_item = next((r for r in self.scan_results if r.definition.name == name), None)
        if not r_item:
            return

        self.lbl_selected_title.config(text=f"{r_item.definition.name} ({r_item.definition.winget_id})")
        self.lbl_selected_desc.config(text=f"{r_item.definition.description}\nStatus: {r_item.status_message}")

        if r_item.is_missing or r_item.is_upgradable:
            btn_text = "Install Selected" if r_item.is_missing else "Update Selected"
            self.btn_install_selected.config(text=btn_text, state="normal")
        else:
            self.btn_install_selected.config(text="Already Installed", state="disabled")

    def _install_selected(self) -> None:
        selected = self.tree.selection()
        if not selected or self._is_busy:
            return

        item_vals = self.tree.item(selected[0], "values")
        name = item_vals[0]
        r_item = next((r for r in self.scan_results if r.definition.name == name), None)
        if not r_item:
            return

        if not messagebox.askyesno(
            "Confirm Runtime Installation",
            f"Install runtime package '{r_item.definition.name}'?\n\n"
            f"Package Identifier: {r_item.definition.winget_id}\n\n"
            f"Winget will download and execute the official signed Microsoft / vendor installer silently.",
            parent=self,
        ):
            return

        self._run_install_job([r_item])

    def _install_all_missing(self) -> None:
        if self._is_busy:
            return

        missing_items = [r for r in self.scan_results if r.is_missing or r.is_upgradable]
        if not missing_items:
            messagebox.showinfo(
                "All Runtimes Healthy",
                "All essential gaming runtimes (Visual C++, .NET, DirectX) are already installed and healthy on this PC!",
                parent=self,
            )
            return

        names_preview = "\n".join(f"• {r.definition.name}" for r in missing_items[:8])
        if len(missing_items) > 8:
            names_preview += f"\n... and {len(missing_items) - 8} more."

        if not messagebox.askyesno(
            "Batch Runtime Installation",
            f"Found {len(missing_items)} missing or upgradable gaming prerequisites:\n\n"
            f"{names_preview}\n\n"
            f"Would you like to install all recommended gaming runtimes now in the background?",
            parent=self,
        ):
            return

        self._run_install_job(missing_items)

    def _run_install_job(self, items: List[Any]) -> None:
        self._is_busy = True
        self.btn_batch_install.config(state="disabled")
        self.btn_install_selected.config(state="disabled")
        self.btn_rescan.config(state="disabled")

        total = len(items)
        self.progress_bar.config(mode="determinate", maximum=total, value=0)

        def worker():
            successes = 0
            failures = 0
            for idx, it in enumerate(items, 1):
                name = it.definition.name
                pkg_id = it.definition.winget_id
                self.msg_queue.put(("STATUS", f"Installing {name} ({idx}/{total})..."))
                self.msg_queue.put(("PROGRESS", idx - 1))

                success, msg = self.runtimes_mgr.install_runtime(pkg_id)
                if success:
                    successes += 1
                else:
                    failures += 1

            self.msg_queue.put(("JOB_DONE", (successes, failures, total)))

        threading.Thread(target=worker, daemon=True).start()

    def _on_install_job_done(self, successes: int, failures: int, total: int) -> None:
        self._is_busy = False
        self.progress_bar.config(value=total)
        self.btn_rescan.config(state="normal")

        if failures == 0:
            messagebox.showinfo(
                "Runtime Installation Succeeded",
                f"Successfully installed all {successes} runtime prerequisites!\n\n"
                f"Your PC is now fully configured with the recommended Visual C++, .NET, and DirectX gaming libraries.",
                parent=self,
            )
        else:
            messagebox.showwarning(
                "Installation Completed with Warnings",
                f"Installed {successes} of {total} runtimes.\n{failures} packages reported warnings or require manual confirmation.",
                parent=self,
            )

        if self.on_runtime_installed:
            self.on_runtime_installed()

        self._start_async_scan()


class DiskCleanupDialog(tk.Toplevel):
    """Interactive Disk Space Reclaimer & Installer Purge dialog.
    Scans temporary installer files, WinGet diagnostic logs, and package caches,
    allowing users to safely reclaim disk space with 1 click.
    """

    def __init__(
        self,
        parent: tk.Widget,
        theme: Optional[ThemeColors] = None,
        on_cleanup_done: Optional[Callable[[int], None]] = None,
    ):
        super().__init__(parent)
        self.title("Disk Space Reclaimer & Cache Purge — Windows 11")
        self.geometry("860x600")
        self.minsize(740, 480)
        self.theme = theme or DARK_THEME
        try:
            apply_native_window_styling(self, self.theme)
        except Exception:
            pass

        self.on_cleanup_done = on_cleanup_done
        self.scanned_targets: List[Dict[str, Any]] = []
        self.target_vars: Dict[str, tk.BooleanVar] = {}
        self._is_busy = False
        self.msg_queue: queue.Queue = queue.Queue()

        self.configure(bg=self.theme.bg_root)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._process_queue()
        self._start_async_scan()

    def _process_queue(self) -> None:
        """Processes cross-thread asynchronous UI messages."""
        try:
            while True:
                msg_type, payload = self.msg_queue.get_nowait()
                if msg_type == "SCAN_COMPLETE":
                    self._on_scan_completed(payload)
                elif msg_type == "STATUS":
                    self.lbl_status.config(text=payload)
                elif msg_type == "PROGRESS":
                    self.progress_bar.config(value=payload)
                elif msg_type == "CLEAN_DONE":
                    self._on_cleanup_completed(payload)
        except queue.Empty:
            pass
        finally:
            self.after(50, self._process_queue)

    def _build_ui(self) -> None:
        t = self.theme

        # Top Header
        top_header = tk.Frame(self, bg=t.bg_card, padx=22, pady=16, highlightbackground=t.border, highlightthickness=1)
        top_header.pack(fill=tk.X)

        header_row = tk.Frame(top_header, bg=t.bg_card)
        header_row.pack(fill=tk.X)

        lbl_icon = tk.Label(header_row, text="🧹", font=("Segoe UI Emoji", 20), bg=t.bg_card)
        lbl_icon.pack(side=tk.LEFT, padx=(0, 10))

        header_text_box = tk.Frame(header_row, bg=t.bg_card)
        header_text_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        lbl_title = tk.Label(
            header_text_box,
            text="Disk Space Reclaimer & Installer Purge",
            bg=t.bg_card,
            fg=t.accent_burgundy,
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        lbl_title.pack(anchor=tk.W)

        lbl_desc = tk.Label(
            header_text_box,
            text="Scan and purge accumulated WinGet installer binaries, diagnostic trace logs, and vendor cache files.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 9),
            anchor="w",
        )
        lbl_desc.pack(anchor=tk.W, pady=(2, 0))

        # Main Body
        main_body = tk.Frame(self, bg=t.bg_root, padx=20, pady=14)
        main_body.pack(fill=tk.BOTH, expand=True)

        # Metrics Deck
        metrics_deck = tk.Frame(main_body, bg=t.bg_root)
        metrics_deck.pack(fill=tk.X, pady=(0, 12))

        # Metric 1: Space Reclaimable
        self.card_space = tk.Frame(metrics_deck, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=10)
        self.card_space.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.lbl_space_val = tk.Label(self.card_space, text="Scanning...", font=("Segoe UI", 16, "bold"), fg=t.accent_crimson, bg=t.bg_card)
        self.lbl_space_val.pack(anchor=tk.W)
        lbl_s_sub = tk.Label(self.card_space, text="Total Reclaimable Space", font=("Segoe UI", 8), fg=t.fg_muted, bg=t.bg_card)
        lbl_s_sub.pack(anchor=tk.W)

        # Metric 2: Total Files
        self.card_files = tk.Frame(metrics_deck, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=10)
        self.card_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.lbl_files_val = tk.Label(self.card_files, text="Scanning...", font=("Segoe UI", 16, "bold"), fg="#38bdf8", bg=t.bg_card)
        self.lbl_files_val.pack(anchor=tk.W)
        lbl_f_sub = tk.Label(self.card_files, text="Installer & Log Files", font=("Segoe UI", 8), fg=t.fg_muted, bg=t.bg_card)
        lbl_f_sub.pack(anchor=tk.W)

        # Metric 3: Safety Status
        self.card_safety = tk.Frame(metrics_deck, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=10)
        self.card_safety.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.lbl_safety_val = tk.Label(self.card_safety, text="100% Safe", font=("Segoe UI", 16, "bold"), fg="#34d399", bg=t.bg_card)
        self.lbl_safety_val.pack(anchor=tk.W)
        lbl_safe_sub = tk.Label(self.card_safety, text="Zero Personal Data Loss", font=("Segoe UI", 8), fg=t.fg_muted, bg=t.bg_card)
        lbl_safe_sub.pack(anchor=tk.W)

        # Targets Container
        self.table_card = tk.Frame(main_body, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=2, pady=2)
        self.table_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        columns = ("select", "name", "files", "size", "description")
        self.tree = ttk.Treeview(self.table_card, columns=columns, show="headings", height=8, selectmode="browse")

        self.tree.heading("select", text="Clean?")
        self.tree.heading("name", text="Cache Category")
        self.tree.heading("files", text="Files")
        self.tree.heading("size", text="Reclaimable")
        self.tree.heading("description", text="Description")

        self.tree.column("select", width=65, anchor="center")
        self.tree.column("name", width=220, anchor="w")
        self.tree.column("files", width=80, anchor="center")
        self.tree.column("size", width=110, anchor="center")
        self.tree.column("description", width=340, anchor="w")

        tree_scroll = ttk.Scrollbar(self.table_card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<ButtonRelease-1>", self._on_tree_click)

        # Selection bar
        sel_row = tk.Frame(main_body, bg=t.bg_root)
        sel_row.pack(fill=tk.X, pady=(0, 6))

        btn_sel_all = tk.Button(sel_row, text="Select All", font=("Segoe UI", 8), bg=t.bg_card, fg=t.fg_primary, bd=0, command=self._select_all)
        btn_sel_all.pack(side=tk.LEFT, padx=(0, 8))

        btn_desel_all = tk.Button(sel_row, text="Deselect All", font=("Segoe UI", 8), bg=t.bg_card, fg=t.fg_muted, bd=0, command=self._deselect_all)
        btn_desel_all.pack(side=tk.LEFT)

        # Progress bar
        self.progress_bar = ttk.Progressbar(main_body, mode="indeterminate")
        self.progress_bar.pack(fill=tk.X, pady=(0, 10))

        # Bottom Action Bar
        bottom = tk.Frame(self, bg=t.bg_sidebar, padx=20, pady=12, highlightbackground=t.border, highlightthickness=1)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_status = tk.Label(bottom, text="Scanning disk caches...", bg=t.bg_sidebar, fg=t.fg_muted, font=("Segoe UI", 9))
        self.lbl_status.pack(side=tk.LEFT)

        self.btn_close = RoundedButton(
            bottom,
            text="Close",
            command=self.destroy,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            hover_bg=t.bg_button_hover,
            radius=6,
            font=("Segoe UI", 9),
            width=90,
            height=32,
            parent_bg=t.bg_sidebar,
        )
        self.btn_close.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_clean = RoundedButton(
            bottom,
            text="🧹 Clean Selected Space",
            command=self._do_purge,
            bg_color=t.accent_burgundy,
            fg_color="#ffffff",
            hover_bg=t.accent_burgundy_hover,
            radius=6,
            font=("Segoe UI", 9, "bold"),
            padding=(16, 4),
            height=32,
            parent_bg=t.bg_sidebar,
        )
        self.btn_clean.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_rescan = RoundedButton(
            bottom,
            text="🔄 Rescan",
            command=self._start_async_scan,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            hover_bg=t.bg_button_hover,
            radius=6,
            font=("Segoe UI", 9),
            padding=(12, 4),
            height=32,
            parent_bg=t.bg_sidebar,
        )
        self.btn_rescan.pack(side=tk.RIGHT)

    def _start_async_scan(self) -> None:
        if self._is_busy:
            return
        self._is_busy = True
        self.btn_clean.config(state="disabled")
        self.btn_rescan.config(state="disabled")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start(10)
        self.lbl_status.config(text="Scanning installer directories and diagnostic logs...")

        def worker():
            try:
                results = DiskCleanupManager.scan_targets()
                self.msg_queue.put(("SCAN_COMPLETE", results))
            except Exception as e:
                self.msg_queue.put(("STATUS", f"Scan error: {e}"))
                self.msg_queue.put(("SCAN_COMPLETE", []))

        threading.Thread(target=worker, daemon=True).start()

    def _on_scan_completed(self, results: List[Dict[str, Any]]) -> None:
        self._is_busy = False
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate", value=0)
        self.btn_clean.config(state="normal")
        self.btn_rescan.config(state="normal")

        self.scanned_targets = results
        total_bytes = sum(t["bytes"] for t in results)
        total_files = sum(t["files_count"] for t in results)
        total_mb = total_bytes / (1024 * 1024)

        if total_mb < 1024:
            self.lbl_space_val.config(text=f"{total_mb:.2f} MB")
        else:
            self.lbl_space_val.config(text=f"{total_mb / 1024:.2f} GB")

        self.lbl_files_val.config(text=f"{total_files:,}")

        for item in self.tree.get_children():
            self.tree.delete(item)

        for t in results:
            tid = t["id"]
            if tid not in self.target_vars:
                # Select by default if it has files
                self.target_vars[tid] = tk.BooleanVar(value=t["files_count"] > 0)
            check_str = "☑ YES" if self.target_vars[tid].get() else "☐ NO"
            self.tree.insert(
                "",
                tk.END,
                iid=tid,
                values=(
                    check_str,
                    t["name"],
                    f"{t['files_count']:,}",
                    t["formatted_size"],
                    t["description"],
                ),
            )

        self.lbl_status.config(text=f"Scan complete: Found {total_files:,} files ready for cleanup.")

    def _on_tree_click(self, event: tk.Event) -> None:
        item_id = self.tree.focus()
        if not item_id or item_id not in self.target_vars:
            return
        var = self.target_vars[item_id]
        var.set(not var.get())
        new_check = "☑ YES" if var.get() else "☐ NO"
        vals = list(self.tree.item(item_id, "values"))
        if vals:
            vals[0] = new_check
            self.tree.item(item_id, values=vals)

    def _select_all(self) -> None:
        for tid, var in self.target_vars.items():
            var.set(True)
            if self.tree.exists(tid):
                vals = list(self.tree.item(tid, "values"))
                vals[0] = "☑ YES"
                self.tree.item(tid, values=vals)

    def _deselect_all(self) -> None:
        for tid, var in self.target_vars.items():
            var.set(False)
            if self.tree.exists(tid):
                vals = list(self.tree.item(tid, "values"))
                vals[0] = "☐ NO"
                self.tree.item(tid, values=vals)

    def _do_purge(self) -> None:
        if self._is_busy:
            return

        selected_ids = [tid for tid, var in self.target_vars.items() if var.get()]
        if not selected_ids:
            messagebox.showinfo("No Targets Selected", "Please select at least one cache category to clean.", parent=self)
            return

        selected_targets = [t for t in self.scanned_targets if t["id"] in selected_ids]
        est_mb = sum(t["mb"] for t in selected_targets)
        est_files = sum(t["files_count"] for t in selected_targets)

        if est_files == 0:
            messagebox.showinfo("Caches Clean", "Selected categories are already empty (0 files).", parent=self)
            return

        if not messagebox.askyesno(
            "Confirm Disk Space Reclaimer",
            f"Are you sure you want to permanently purge the selected installer caches?\n\n"
            f"Estimated reclaimable space: {est_mb:.2f} MB across {est_files:,} files.\n\n"
            f"This will safely remove transient setup files with zero impact on installed applications.",
            parent=self,
        ):
            return

        self._is_busy = True
        self.btn_clean.config(state="disabled")
        self.btn_rescan.config(state="disabled")
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start(10)
        self.lbl_status.config(text="Purging selected caches and temporary installer files...")

        def worker():
            try:
                res = DiskCleanupManager.purge_targets(selected_ids)
                self.msg_queue.put(("CLEAN_DONE", res))
            except Exception as e:
                self.msg_queue.put(("STATUS", f"Cleanup error: {e}"))
                self.msg_queue.put(("CLEAN_DONE", {"freed_bytes": 0, "freed_mb": 0.0, "removed_files": 0, "summary": str(e)}))

        threading.Thread(target=worker, daemon=True).start()

    def _on_cleanup_completed(self, res: Dict[str, Any]) -> None:
        self._is_busy = False
        self.progress_bar.stop()
        self.progress_bar.config(mode="determinate", value=0)
        self.btn_clean.config(state="normal")
        self.btn_rescan.config(state="normal")

        freed_mb = res.get("freed_mb", 0.0)
        files = res.get("removed_files", 0)

        messagebox.showinfo(
            "Disk Space Reclaimed",
            f"Successfully reclaimed {freed_mb:.2f} MB of disk space!\n\n"
            f"Removed {files:,} orphaned installer and diagnostic trace files.",
            parent=self,
        )

        if self.on_cleanup_done:
            self.on_cleanup_done(res.get("freed_bytes", 0))

        self._start_async_scan()


class StartupManagerDialog(tk.Toplevel):
    """Interactive Windows Startup & Autorun Optimizer dialog.
    Inspects, enables, disables, and removes startup programs across HKCU, HKLM,
    and user startup folders using Windows 11 StartupApproved standards.
    """

    def __init__(
        self,
        parent: tk.Widget,
        theme: Optional[ThemeColors] = None,
    ):
        super().__init__(parent)
        self.title("Windows Startup & Autorun Optimizer — Windows 11")
        self.geometry("920x620")
        self.minsize(760, 500)
        self.theme = theme or DARK_THEME
        try:
            apply_native_window_styling(self, self.theme)
        except Exception:
            pass

        self.items: List[StartupItem] = []
        self._is_busy = False
        self.msg_queue: queue.Queue = queue.Queue()

        self.configure(bg=self.theme.bg_root)
        self.transient(parent)
        self.grab_set()

        self._build_ui()
        self._process_queue()
        self._start_async_scan()

    def _process_queue(self) -> None:
        try:
            while True:
                msg_type, payload = self.msg_queue.get_nowait()
                if msg_type == "SCAN_COMPLETE":
                    self._on_scan_completed(payload)
                elif msg_type == "STATUS":
                    self.lbl_status.config(text=payload)
        except queue.Empty:
            pass
        finally:
            self.after(50, self._process_queue)

    def _build_ui(self) -> None:
        t = self.theme

        # Top Header
        top_header = tk.Frame(self, bg=t.bg_card, padx=22, pady=16, highlightbackground=t.border, highlightthickness=1)
        top_header.pack(fill=tk.X)

        header_row = tk.Frame(top_header, bg=t.bg_card)
        header_row.pack(fill=tk.X)

        lbl_icon = tk.Label(header_row, text="🚀", font=("Segoe UI Emoji", 20), bg=t.bg_card)
        lbl_icon.pack(side=tk.LEFT, padx=(0, 10))

        header_text_box = tk.Frame(header_row, bg=t.bg_card)
        header_text_box.pack(side=tk.LEFT, fill=tk.X, expand=True)

        lbl_title = tk.Label(
            header_text_box,
            text="Windows Startup & Autorun Optimizer",
            bg=t.bg_card,
            fg=t.accent_burgundy,
            font=("Segoe UI", 13, "bold"),
            anchor="w",
        )
        lbl_title.pack(anchor=tk.W)

        lbl_desc = tk.Label(
            header_text_box,
            text="Inspect and toggle background apps running at logon across HKCU, HKLM, and startup folders to accelerate boot times.",
            bg=t.bg_card,
            fg=t.fg_muted,
            font=("Segoe UI", 9),
            anchor="w",
        )
        lbl_desc.pack(anchor=tk.W, pady=(2, 0))

        # Main Body
        main_body = tk.Frame(self, bg=t.bg_root, padx=20, pady=14)
        main_body.pack(fill=tk.BOTH, expand=True)

        # Metrics Deck
        metrics_deck = tk.Frame(main_body, bg=t.bg_root)
        metrics_deck.pack(fill=tk.X, pady=(0, 12))

        # Metric 1: Total
        self.card_total = tk.Frame(metrics_deck, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=10)
        self.card_total.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.lbl_total_val = tk.Label(self.card_total, text="Scanning...", font=("Segoe UI", 16, "bold"), fg=t.fg_primary, bg=t.bg_card)
        self.lbl_total_val.pack(anchor=tk.W)
        lbl_tot_sub = tk.Label(self.card_total, text="Total Startup Apps", font=("Segoe UI", 8), fg=t.fg_muted, bg=t.bg_card)
        lbl_tot_sub.pack(anchor=tk.W)

        # Metric 2: Enabled
        self.card_enabled = tk.Frame(metrics_deck, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=10)
        self.card_enabled.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.lbl_enabled_val = tk.Label(self.card_enabled, text="Scanning...", font=("Segoe UI", 16, "bold"), fg="#34d399", bg=t.bg_card)
        self.lbl_enabled_val.pack(anchor=tk.W)
        lbl_en_sub = tk.Label(self.card_enabled, text="Active at Boot", font=("Segoe UI", 8), fg=t.fg_muted, bg=t.bg_card)
        lbl_en_sub.pack(anchor=tk.W)

        # Metric 3: Disabled
        self.card_disabled = tk.Frame(metrics_deck, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=10)
        self.card_disabled.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        self.lbl_disabled_val = tk.Label(self.card_disabled, text="Scanning...", font=("Segoe UI", 16, "bold"), fg=t.fg_muted, bg=t.bg_card)
        self.lbl_disabled_val.pack(anchor=tk.W)
        lbl_dis_sub = tk.Label(self.card_disabled, text="Disabled / Optimized", font=("Segoe UI", 8), fg=t.fg_muted, bg=t.bg_card)
        lbl_dis_sub.pack(anchor=tk.W)

        # Metric 4: Broken (Missing files)
        self.card_broken = tk.Frame(metrics_deck, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=14, pady=10)
        self.card_broken.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.lbl_broken_val = tk.Label(self.card_broken, text="0", font=("Segoe UI", 16, "bold"), fg="#f43f5e", bg=t.bg_card)
        self.lbl_broken_val.pack(anchor=tk.W)
        lbl_brk_sub = tk.Label(self.card_broken, text="Orphan / Missing Exe", font=("Segoe UI", 8), fg=t.fg_muted, bg=t.bg_card)
        lbl_brk_sub.pack(anchor=tk.W)

        # Table Container
        self.table_card = tk.Frame(main_body, bg=t.bg_card, highlightbackground=t.border, highlightthickness=1, padx=2, pady=2)
        self.table_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        columns = ("name", "status", "source", "path")
        self.tree = ttk.Treeview(self.table_card, columns=columns, show="headings", height=10, selectmode="browse")

        self.tree.heading("name", text="Application Name")
        self.tree.heading("status", text="Startup State")
        self.tree.heading("source", text="Location")
        self.tree.heading("path", text="Command / Executable Path")

        self.tree.column("name", width=200, anchor="w")
        self.tree.column("status", width=120, anchor="center")
        self.tree.column("source", width=160, anchor="w")
        self.tree.column("path", width=380, anchor="w")

        tree_scroll = ttk.Scrollbar(self.table_card, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Action bar under table
        btn_bar = tk.Frame(main_body, bg=t.bg_root)
        btn_bar.pack(fill=tk.X, pady=(0, 6))

        self.btn_toggle = RoundedButton(
            btn_bar,
            text="⚡ Toggle Enabled / Disabled",
            command=self._toggle_selected,
            bg_color=t.accent_burgundy,
            fg_color="#ffffff",
            border_color=t.accent_crimson,
            radius=6,
            height=28,
            font=("Segoe UI", 9, "bold"),
            padding=(12, 3),
        )
        self.btn_toggle.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_reveal = RoundedButton(
            btn_bar,
            text="📁 Reveal in File Explorer",
            command=self._reveal_selected,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            border_color=t.border,
            radius=6,
            height=28,
            font=("Segoe UI", 9),
            padding=(12, 3),
        )
        self.btn_reveal.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_delete = RoundedButton(
            btn_bar,
            text="🗑️ Remove Entry",
            command=self._delete_selected,
            bg_color="#3b1120" if t.name == "dark" else "#fee2e2",
            fg_color="#f43f5e" if t.name == "dark" else "#b91c1c",
            border_color="#7c1e38" if t.name == "dark" else "#fca5a5",
            radius=6,
            height=28,
            font=("Segoe UI", 9, "bold"),
            padding=(12, 3),
        )
        self.btn_delete.pack(side=tk.LEFT)

        # Bottom Bar
        bottom = tk.Frame(self, bg=t.bg_sidebar, padx=20, pady=12, highlightbackground=t.border, highlightthickness=1)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_status = tk.Label(bottom, text="Scanning startup registry keys...", bg=t.bg_sidebar, fg=t.fg_muted, font=("Segoe UI", 9))
        self.lbl_status.pack(side=tk.LEFT)

        self.btn_close = RoundedButton(
            bottom,
            text="Close",
            command=self.destroy,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            hover_bg=t.bg_button_hover,
            radius=6,
            font=("Segoe UI", 9),
            width=90,
            height=32,
            parent_bg=t.bg_sidebar,
        )
        self.btn_close.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_rescan = RoundedButton(
            bottom,
            text="🔄 Refresh",
            command=self._start_async_scan,
            bg_color=t.bg_button,
            fg_color=t.fg_primary,
            hover_bg=t.bg_button_hover,
            radius=6,
            font=("Segoe UI", 9),
            padding=(12, 4),
            height=32,
            parent_bg=t.bg_sidebar,
        )
        self.btn_rescan.pack(side=tk.RIGHT)

    def _start_async_scan(self) -> None:
        if self._is_busy:
            return
        self._is_busy = True
        self.lbl_status.config(text="Inspecting Windows startup programs...")

        def worker():
            try:
                items = StartupManager.get_startup_items()
                self.msg_queue.put(("SCAN_COMPLETE", items))
            except Exception as e:
                self.msg_queue.put(("STATUS", f"Scan error: {e}"))
                self.msg_queue.put(("SCAN_COMPLETE", []))

        threading.Thread(target=worker, daemon=True).start()

    def _on_scan_completed(self, items: List[StartupItem]) -> None:
        self._is_busy = False
        self.items = items

        total = len(items)
        enabled = sum(1 for it in items if it.enabled)
        disabled = total - enabled
        broken = sum(1 for it in items if not it.exists)

        self.lbl_total_val.config(text=str(total))
        self.lbl_enabled_val.config(text=str(enabled))
        self.lbl_disabled_val.config(text=str(disabled))
        self.lbl_broken_val.config(text=str(broken))

        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, it in enumerate(items):
            status_text = "● Enabled" if it.enabled else "○ Disabled"
            if not it.exists:
                status_text += " [Missing File]"
            self.tree.insert(
                "",
                tk.END,
                iid=str(idx),
                values=(
                    it.name,
                    status_text,
                    it.source,
                    it.command,
                ),
            )

        self.lbl_status.config(text=f"Loaded {total} startup applications.")

    def _get_selected_item(self) -> Optional[StartupItem]:
        sel = self.tree.selection()
        if not sel:
            return None
        idx = int(sel[0])
        if 0 <= idx < len(self.items):
            return self.items[idx]
        return None

    def _on_select(self, event: tk.Event) -> None:
        it = self._get_selected_item()
        if it:
            toggle_text = "○ Disable Program" if it.enabled else "● Enable Program"
            self.btn_toggle.config(text=toggle_text)

    def _toggle_selected(self) -> None:
        it = self._get_selected_item()
        if not it:
            messagebox.showinfo("Select Item", "Please select a startup program from the list.", parent=self)
            return

        new_state = not it.enabled
        success = StartupManager.set_enabled(it, new_state)
        if success:
            it.enabled = new_state
            self._start_async_scan()
        else:
            messagebox.showerror("Error", f"Failed to modify startup state for '{it.name}'. Administrator privileges may be required.", parent=self)

    def _reveal_selected(self) -> None:
        it = self._get_selected_item()
        if not it:
            messagebox.showinfo("Select Item", "Please select a startup program from the list.", parent=self)
            return

        if not it.clean_path:
            messagebox.showwarning("No Path", f"Could not determine file path for '{it.name}'.", parent=self)
            return

        success = StartupManager.reveal_in_explorer(it.clean_path)
        if not success:
            messagebox.showwarning("File Missing", f"Target file does not exist on disk:\n{it.clean_path}", parent=self)

    def _delete_selected(self) -> None:
        it = self._get_selected_item()
        if not it:
            messagebox.showinfo("Select Item", "Please select a startup program from the list.", parent=self)
            return

        if not messagebox.askyesno(
            "Confirm Removal",
            f"Are you sure you want to delete startup entry '{it.name}'?\n\n"
            f"Location: {it.source}\nCommand: {it.command}\n\n"
            f"This will stop the program from launching on boot. The application files will not be deleted.",
            parent=self,
        ):
            return

        success = StartupManager.delete_item(it)
        if success:
            self._start_async_scan()
        else:
            messagebox.showerror("Error", f"Failed to delete startup entry '{it.name}'.", parent=self)



