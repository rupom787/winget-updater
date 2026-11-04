"""Modal dialogs for exclusions, scheduling, vendor fallbacks, and downgrade confirmations.
Designed with Clean White and Velvet Burgundy typography and rounded controls.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, List, Optional
from winget_updater.config import ConfigManager, ExclusionRule, VendorSourceEntry
from winget_updater.engine.scheduler import SchedulerManager
from winget_updater.gui.rounded_widgets import RoundedButton, RoundedPillBadge
from winget_updater.engine.tracker import TrackedAppUpdate, UpdateTracker
from winget_updater.gui.theme import LIGHT_THEME, ThemeColors
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
        self.theme = theme or LIGHT_THEME
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
        self.theme = theme or LIGHT_THEME
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
        self.theme = theme or LIGHT_THEME
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
        theme: Optional[ThemeColors] = None,
    ):
        super().__init__(parent)
        self.title("Settings & Preferences")
        self.geometry("680x560")
        self.minsize(580, 480)
        self.config = config
        self.on_theme_changed = on_theme_changed
        self.on_font_scale_changed = on_font_scale_changed
        self.on_settings_saved = on_settings_saved
        self.theme = theme or LIGHT_THEME
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
        style.configure("Settings.TNotebook.Tab", padding=[14, 8], font=("Segoe UI", 9, "bold"))
        self.notebook = ttk.Notebook(self, style="Settings.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=14)

        # Tab 1: Appearance & Display
        self.tab_appearance = tk.Frame(self.notebook, bg=t.bg_root, padx=14, pady=12)
        self.notebook.add(self.tab_appearance, text="🎨 Appearance & Text")
        self._build_appearance_tab()

        # Tab 2: Package Ecosystems
        self.tab_managers = tk.Frame(self.notebook, bg=t.bg_root, padx=14, pady=12)
        self.notebook.add(self.tab_managers, text="📦 Package Managers")
        self._build_managers_tab()

        # Tab 3: Safety & Automation
        self.tab_safety = tk.Frame(self.notebook, bg=t.bg_root, padx=14, pady=12)
        self.notebook.add(self.tab_safety, text="🛡️ Safety & Automation")
        self._build_safety_tab()

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

        self.theme_var = tk.StringVar(value=getattr(self.config, "theme", "light"))
        theme_options = [
            ("Clean Velvet Wine (Light)", "light"),
            ("Cyber Burgundy (Dark Mode)", "dark"),
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
        lbl_vc_sub.pack(anchor=tk.W, padx=(24, 0), pady=(0, 8))

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
        self.theme = theme or LIGHT_THEME
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
        self.theme = theme or LIGHT_THEME
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

