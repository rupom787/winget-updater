"""Modal dialogs for exclusions, scheduling, vendor fallbacks, and downgrade confirmations.
Designed with Clean White and Velvet Burgundy typography and rounded controls.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, List, Optional
from winget_updater.config import ConfigManager, ExclusionRule, VendorSourceEntry
from winget_updater.engine.scheduler import SchedulerManager
from winget_updater.gui.rounded_widgets import RoundedButton, RoundedPillBadge
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
            self.btn_delete.config(state="normal")
        else:
            self.lbl_status.config(
                text="Active Schedule: None\nAutomatic background updates are not currently active.",
                fg=self.theme.fg_muted,
            )
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
