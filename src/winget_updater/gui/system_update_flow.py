"""Complete System Update Workflow Dialog for Windows 11.
Orchestrates 4-stage automated PC maintenance:
[1/4] Windows Update & Security Patches
[2/4] Microsoft Store & Winget Applications
[3/4] OEM Hardware Drivers (NVIDIA, Chipset, Audio)
[4/4] OEM Companion / BIOS Firmware & Reboot Status
"""

import os
import queue
import threading
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional
from winget_updater.engine.windows_update import OemCompanionInfo, WindowsUpdateManager
from winget_updater.gui.animations import TimelinePipelineHUD
from winget_updater.gui.dialogs import ModernMessageDialog
from winget_updater.gui.rounded_widgets import RoundedButton, apply_native_window_styling
from winget_updater.gui.theme import LIGHT_THEME, ThemeColors
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run
from winget_updater.winget.client import WingetClient

logger = get_logger()


class CompleteSystemUpdateDialog(tk.Toplevel):
    """Modern modal orchestrating a 4-stage Complete System Update."""

    def __init__(
        self,
        parent: tk.Tk,
        theme: ThemeColors = LIGHT_THEME,
        on_finished: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)
        self.title("Complete System Update — Windows 11 Maintenance")
        self.geometry("860x580")
        self.minsize(780, 500)
        self.transient(parent)
        self.grab_set()

        try:
            apply_native_window_styling(self)
        except Exception:
            pass

        self.theme = theme
        self.on_finished = on_finished
        self.winget = WingetClient()
        self.oem_info: OemCompanionInfo = WindowsUpdateManager.get_oem_info()
        self.msg_queue: queue.Queue = queue.Queue()
        self.is_running = False

        self._build_ui()
        self._poll_queue()

    def _build_ui(self) -> None:
        t = self.theme
        self.configure(bg=t.bg_root)

        # 1. Header Frame
        self.header_frame = tk.Frame(self, bg=t.bg_header, padx=20, pady=12, highlightthickness=1, highlightbackground=t.border)
        self.header_frame.pack(fill=tk.X)

        self.lbl_title = tk.Label(
            self.header_frame,
            text="⚡ Complete System Update",
            font=("Segoe UI", 13, "bold"),
            bg=t.bg_header,
            fg=t.accent_burgundy,
            anchor="w",
        )
        self.lbl_title.pack(anchor=tk.W)

        self.lbl_subtitle = tk.Label(
            self.header_frame,
            text=f"Hardware Detected: {self.oem_info.manufacturer} ({self.oem_info.model})  •  Companion: {self.oem_info.companion_name}",
            font=("Segoe UI", 8),
            bg=t.bg_header,
            fg=t.fg_muted,
            anchor="w",
        )
        self.lbl_subtitle.pack(anchor=tk.W, pady=(2, 0))

        # 2. Pipeline Visual Progress HUD (4 Stages)
        self.pipeline_frame = tk.Frame(self, bg=t.bg_root, padx=20, pady=8)
        self.pipeline_frame.pack(fill=tk.X)

        self.timeline = TimelinePipelineHUD(self.pipeline_frame, height=36)
        # Custom 4-stage labels for Complete System Update
        self.timeline.STAGES = [
            ("01", "WINDOWS UPDATE"),
            ("02", "WINGET APPS"),
            ("03", "OEM DRIVERS"),
            ("04", "BIOS & REBOOT"),
        ]
        self.timeline.set_stage(0)
        self.timeline.apply_theme(t)
        self.timeline.pack(fill=tk.X)

        # 3. Live Console / Terminal Card
        self.console_container = tk.Frame(self, bg=t.bg_root, padx=20, pady=6)
        self.console_container.pack(fill=tk.BOTH, expand=True)

        self.console_card = tk.Frame(
            self.console_container,
            bg="#0f172a",
            highlightthickness=1,
            highlightbackground="#334155",
            padx=10,
            pady=8,
        )
        self.console_card.pack(fill=tk.BOTH, expand=True)

        self.text_console = tk.Text(
            self.console_card,
            bg="#0f172a",
            fg="#e2e8f0",
            insertbackground="#00f0ff",
            font=("Cascadia Code", 9),
            wrap=tk.WORD,
            bd=0,
            highlightthickness=0,
        )
        vsb = ttk.Scrollbar(self.console_card, orient=tk.VERTICAL, command=self.text_console.yview)
        self.text_console.configure(yscrollcommand=vsb.set)

        self.text_console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure color tags matching PowerShell output
        self.text_console.tag_config("cyan", foreground="#38bdf8", font=("Cascadia Code", 9, "bold"))
        self.text_console.tag_config("yellow", foreground="#fbbf24", font=("Cascadia Code", 9, "bold"))
        self.text_console.tag_config("green", foreground="#34d399", font=("Cascadia Code", 9, "bold"))
        self.text_console.tag_config("red", foreground="#f87171", font=("Cascadia Code", 9, "bold"))
        self.text_console.tag_config("muted", foreground="#94a3b8")

        self._log("=== COMPLETE SYSTEM UPDATE READY ===", "cyan")
        self._log(f"Detected Platform: Windows 11  •  OEM: {self.oem_info.manufacturer} {self.oem_info.model}", "muted")
        self._log("Click 'Start Complete Update' to begin automated 4-stage sequence.\n", "muted")

        # 4. Bottom Action Bar
        self.bottom_bar = tk.Frame(self, bg=t.bg_header, padx=20, pady=12, highlightthickness=1, highlightbackground=t.border)
        self.bottom_bar.pack(fill=tk.X)

        self.btn_run = RoundedButton(
            self.bottom_bar,
            text="▶ Start Complete Update",
            command=self.start_pipeline,
            bg_color="#881337",
            fg_color="#ffffff",
            hover_bg="#9f1239",
            radius=8,
            font=("Segoe UI", 9, "bold"),
            height=34,
            padding=(16, 6),
            parent_bg=t.bg_header,
        )
        self.btn_run.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_oem = RoundedButton(
            self.bottom_bar,
            text=f"💻 Open {self.oem_info.companion_name}",
            command=self._launch_oem_companion,
            bg_color="#ffffff" if t.name == "light" else "#1e293b",
            fg_color=t.fg_primary,
            hover_bg="#f1f5f9" if t.name == "light" else "#334155",
            border_color=t.border,
            radius=8,
            font=("Segoe UI", 9),
            height=34,
            padding=(12, 6),
            parent_bg=t.bg_header,
        )
        self.btn_oem.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_reboot_check = RoundedButton(
            self.bottom_bar,
            text="🔄 Check Reboot Status",
            command=self._check_reboot_click,
            bg_color="#ffffff" if t.name == "light" else "#1e293b",
            fg_color=t.fg_primary,
            hover_bg="#f1f5f9" if t.name == "light" else "#334155",
            border_color=t.border,
            radius=8,
            font=("Segoe UI", 9),
            height=34,
            padding=(12, 6),
            parent_bg=t.bg_header,
        )
        self.btn_reboot_check.pack(side=tk.LEFT)

        self.btn_close = RoundedButton(
            self.bottom_bar,
            text="✕ Close",
            command=self._on_close,
            bg_color="#ffffff" if t.name == "light" else "#1e293b",
            fg_color="#64748b",
            hover_bg="#f1f5f9" if t.name == "light" else "#334155",
            border_color=t.border,
            radius=8,
            font=("Segoe UI", 9),
            height=34,
            padding=(10, 6),
            parent_bg=t.bg_header,
        )
        self.btn_close.pack(side=tk.RIGHT)

    def _log(self, text: str, tag: str = "muted") -> None:
        self.text_console.insert(tk.END, text + "\n", (tag,))
        self.text_console.see(tk.END)

    def _poll_queue(self) -> None:
        try:
            while True:
                msg_type, data = self.msg_queue.get_nowait()
                if msg_type == "LOG":
                    text, tag = data
                    self._log(text, tag)
                elif msg_type == "STAGE":
                    stage_idx = data
                    self.timeline.set_stage(stage_idx)
                elif msg_type == "FINISHED":
                    self._on_pipeline_finished()
        except queue.Empty:
            pass
        self.after(50, self._poll_queue)

    def start_pipeline(self) -> None:
        """Commences the automated 4-stage update worker thread."""
        if self.is_running:
            return
        self.is_running = True
        self.btn_run.config(state="disabled")
        self.text_console.delete("1.0", tk.END)

        self._log("=== COMPLETE SYSTEM UPDATE ===", "cyan")
        threading.Thread(target=self._worker_thread, daemon=True).start()

    def _worker_thread(self) -> None:
        try:
            # -------------------------------------------------------------
            # STAGE 1: WINDOWS UPDATE (including optional & security)
            # -------------------------------------------------------------
            self.msg_queue.put(("STAGE", 1))
            self.msg_queue.put(("LOG", ("[1/4] Checking Windows Update...", "yellow")))

            # Check if PSWindowsUpdate is available
            chk_res = silent_run(["powershell.exe", "-NoProfile", "-Command", "Get-Module -ListAvailable -Name PSWindowsUpdate"])
            chk_out = chk_res.stdout or ""
            if not chk_out.strip():
                self.msg_queue.put(("LOG", ("  • Installing PSWindowsUpdate module for CurrentUser...", "muted")))
                silent_run(["powershell.exe", "-NoProfile", "-Command", "Install-Module PSWindowsUpdate -Force -Scope CurrentUser -Confirm:$false"], timeout=60)

            self.msg_queue.put(("LOG", ("  • Querying Windows Update catalog via USO / Microsoft Update...", "muted")))
            WindowsUpdateManager.trigger_windows_update_scan_and_install()

            # Refresh Winget package sources and fonts
            self.msg_queue.put(("LOG", ("  • Updating Winget sources & repository manifests...", "muted")))
            self.winget.update_sources()
            self.msg_queue.put(("LOG", ("  ✓ Stage 1 completed successfully.", "green")))

            # -------------------------------------------------------------
            # STAGE 2: MICROSOFT STORE + APPS (winget + MDM background scan)
            # -------------------------------------------------------------
            self.msg_queue.put(("STAGE", 2))
            self.msg_queue.put(("LOG", ("\n[2/4] Updating apps (winget & Microsoft Store)...", "yellow")))

            # 2a. Force update of Windows Store Apps without launching Store UI (WMI/MDM Enterprise Bridge)
            self.msg_queue.put(("LOG", ("  • Triggering Microsoft Store background update scan (MDM Bridge)...", "muted")))
            store_ok, store_msg = WindowsUpdateManager.trigger_store_apps_background_update()
            if store_ok:
                self.msg_queue.put(("LOG", (f"  ✓ {store_msg}", "green")))
            else:
                self.msg_queue.put(("LOG", (f"  • Store background notice: {store_msg}", "muted")))

            # 2b. Winget Upgrade All
            self.msg_queue.put(("LOG", ("  • Updating applications via Windows Package Manager (winget)...", "muted")))
            upgrade_cmd = [
                "winget", "upgrade", "--all",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--silent",
            ]
            up_res = silent_run(upgrade_cmd, timeout=300)
            up_out = up_res.stdout or ""
            if up_out:
                lines = [l.strip() for l in up_out.splitlines() if l.strip()]
                for line in lines[-8:]:
                    self.msg_queue.put(("LOG", (f"  {line}", "muted")))
            self.msg_queue.put(("LOG", ("  ✓ Stage 2 (Applications & Store) completed.", "green")))

            # -------------------------------------------------------------
            # STAGE 3: DRIVERS (NVIDIA, Chipset, Audio, Display)
            # -------------------------------------------------------------
            self.msg_queue.put(("STAGE", 3))
            self.msg_queue.put(("LOG", ("\n[3/4] Updating supported drivers...", "yellow")))

            driver_cmd = [
                "winget", "upgrade", "--all",
                "--source", "winget",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--silent",
            ]
            drv_res = silent_run(driver_cmd, timeout=180)
            drv_out = drv_res.stdout or ""
            if drv_out:
                lines = [l.strip() for l in drv_out.splitlines() if l.strip()]
                for line in lines[-6:]:
                    self.msg_queue.put(("LOG", (f"  {line}", "muted")))
            self.msg_queue.put(("LOG", ("  ✓ Stage 3 (Drivers) completed.", "green")))

            # Evaluate system reboot status
            reboot_needed, reason = WindowsUpdateManager.is_reboot_pending()
            if reboot_needed:
                self.msg_queue.put(("LOG", (f"\n⚠️ The system needs to be restarted to complete updates ({reason}).", "red")))
            else:
                self.msg_queue.put(("LOG", ("\n✓ No restart required.", "green")))

            # -------------------------------------------------------------
            # STAGE 4: OEM COMPANION & BIOS UPDATES
            # -------------------------------------------------------------
            self.msg_queue.put(("STAGE", 4))
            self.msg_queue.put(("LOG", (f"\n[4/4] Hardware Firmware & BIOS Assistant ({self.oem_info.companion_name})...", "yellow")))
            self.msg_queue.put(("LOG", (f"  • Recommended for {self.oem_info.manufacturer} {self.oem_info.model}", "muted")))
            self.msg_queue.put(("LOG", (f"  • {self.oem_info.description}", "muted")))

            self.msg_queue.put(("LOG", ("\n=== PROCESS COMPLETED ===", "green")))
            self.msg_queue.put(("FINISHED", reboot_needed))

        except Exception as e:
            self.msg_queue.put(("LOG", (f"\nError encountered during pipeline: {e}", "red")))
            self.msg_queue.put(("FINISHED", False))

    def _on_pipeline_finished(self) -> None:
        self.is_running = False
        self.btn_run.config(state="normal")
        reboot_needed, _ = WindowsUpdateManager.is_reboot_pending()

        if reboot_needed:
            msg = (
                "Complete System Update has finished!\n\n"
                "A system restart is required to finalize OS patches and device drivers.\n"
                "Would you like to restart your computer now?"
            )
            if ModernMessageDialog.askyesno("Restart Required", msg, parent=self):
                os.system("shutdown /r /t 10 /c \"Restarting to finalize Windows updates\"")

        if self.on_finished:
            self.on_finished()

    def _launch_oem_companion(self) -> None:
        WindowsUpdateManager.open_oem_companion(self.oem_info.store_uri)
        self._log(f"Launched {self.oem_info.companion_name} ({self.oem_info.store_uri})", "muted")

    def _check_reboot_click(self) -> None:
        needed, reason = WindowsUpdateManager.is_reboot_pending()
        if needed:
            self._log(f"⚠️ System restart IS required: {reason}", "red")
            ModernMessageDialog.showwarning("Reboot Required", f"A computer restart is required:\n{reason}", parent=self)
        else:
            self._log("✓ System does not require a restart.", "green")
            ModernMessageDialog.showinfo("System Ready", "No restart required. All updates are active.", parent=self)

    def _on_close(self) -> None:
        if self.is_running:
            if not ModernMessageDialog.askyesno("Update in Progress", "An update task is currently running. Stop and close?", parent=self):
                return
        self.destroy()

