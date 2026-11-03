"""Standalone Uninstaller for Software & Package Updater.

Provides both interactive graphical uninstallation and headless silent uninstallation.
Handles self-relocation from the installation directory to %TEMP% to prevent executable locking.
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Ensure src/ is on sys.path
root_dir = Path(__file__).resolve().parent
src_dir = root_dir / "src"
if src_dir.exists() and str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from winget_updater.engine.uninstaller import (
    APP_TITLE,
    APP_NAME,
    Uninstaller,
    UninstallSummary,
)
from winget_updater.utils.logger import get_logger

logger = get_logger()


def init_console_if_available() -> None:
    """If running as a frozen windowed app but called from a console, attach to parent console."""
    if hasattr(sys, "frozen") and sys.platform == "win32":
        import ctypes
        ATTACH_PARENT_PROCESS = -1
        try:
            if ctypes.windll.kernel32.AttachConsole(ATTACH_PARENT_PROCESS):
                sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
                sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
        except Exception:
            pass


init_console_if_available()


def is_inside_dir(child_path: Path, parent_dir: Path) -> bool:
    """Checks if child_path is located inside or equal to parent_dir."""
    try:
        c = child_path.resolve()
        p = parent_dir.resolve()
        return p in c.parents or p == c.parent or p == c
    except Exception:
        return False


def relocate_to_temp_and_relaunch(target_dir: Path, silent: bool = False) -> None:
    """Copies uninstaller executable to %TEMP% to unlock installation directory."""
    temp_dir = Path(os.environ.get("TEMP", r"C:\Windows\Temp")) / "WingetUpdaterUninstall"
    temp_dir.mkdir(parents=True, exist_ok=True)

    current_pid = os.getpid()

    # Pass all existing args except --relocated, --target-pid, and duplicate --target-dir
    orig_args = []
    skip_next = False
    for a in sys.argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if a in ("--relocated",):
            continue
        if a in ("--target-pid", "--target-dir"):
            skip_next = True
            continue
        if a.startswith("--target-pid=") or a.startswith("--target-dir="):
            continue
        orig_args.append(a)

    target_exe = temp_dir / "Uninstall.exe"
    try:
        shutil.copy2(sys.executable, target_exe)
    except Exception as e:
        logger.error(f"Failed to copy uninstaller to temp: {e}")
        return

    cmd = [
        str(target_exe),
        "--relocated",
        "--target-pid", str(current_pid),
        "--target-dir", str(target_dir),
    ] + orig_args

    DETACHED_PROCESS = 0x00000008
    subprocess.Popen(
        cmd,
        cwd=str(temp_dir),
        creationflags=DETACHED_PROCESS if sys.platform == "win32" else 0,
        close_fds=True,
    )
    # The parent process MUST exit immediately to unlock its binary in target_dir
    sys.exit(0)


def wait_for_parent_pid(pid: int, timeout: float = 6.0) -> None:
    """Waits for parent process to exit before modifying files using Win32 WaitForSingleObject."""
    if sys.platform == "win32":
        import ctypes
        SYNCHRONIZE = 0x00100000
        handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
        if handle:
            ctypes.windll.kernel32.WaitForSingleObject(handle, int(timeout * 1000))
            ctypes.windll.kernel32.CloseHandle(handle)
        # Give Windows kernel a brief moment to finish tearing down memory-mapped sections
        time.sleep(0.5)
    else:
        time.sleep(1.0)


def schedule_temp_cleanup() -> None:
    """Schedules self-deletion of the temporary uninstaller directory after this process exits."""
    temp_dir = Path(os.environ.get("TEMP", r"C:\Windows\Temp")) / "WingetUpdaterUninstall"
    if sys.platform == "win32" and temp_dir.exists():
        cmd = f'cmd.exe /c "timeout /t 2 /nobreak > nul & rmdir /s /q "{temp_dir}""'
        try:
            DETACHED_PROCESS = 0x00000008
            subprocess.Popen(
                cmd,
                shell=True,
                creationflags=DETACHED_PROCESS,
                close_fds=True,
            )
        except Exception:
            pass


class UninstallerGUI:
    """Modern Tkinter uninstallation wizard matching the application aesthetic."""

    def __init__(self, uninstaller: Uninstaller, target_dir: Optional[Path] = None, force: bool = False):
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.uninstaller = uninstaller
        self.target_dir = target_dir
        self.force = force

        self.root = tk.Tk()
        self.root.title(f"{APP_TITLE} — Complete Uninstaller")
        self.root.geometry("560x480")
        self.root.minsize(520, 440)
        self.root.configure(bg="#FAFAF9")

        # Center on screen
        self.root.update_idletasks()
        w = 560
        h = 480
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self._build_ui()

    def _build_ui(self) -> None:
        tk = self.tk
        ttk = self.ttk

        # Header Frame (Burgundy banner)
        header = tk.Frame(self.root, bg="#6B1D2F", padx=24, pady=20)
        header.pack(fill=tk.X)

        lbl_header_title = tk.Label(
            header,
            text=f"🗑️ Complete Uninstaller",
            bg="#6B1D2F",
            fg="#FFFFFF",
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        )
        lbl_header_title.pack(fill=tk.X)

        lbl_header_sub = tk.Label(
            header,
            text=f"Permanently remove {APP_TITLE} and all leftover data",
            bg="#6B1D2F",
            fg="#F3E8E8",
            font=("Segoe UI", 9),
            anchor="w",
        )
        lbl_header_sub.pack(fill=tk.X, pady=(2, 0))

        # Content Card
        self.content_frame = tk.Frame(self.root, bg="#FFFFFF", padx=24, pady=20, highlightbackground="#E7E5E4", highlightthickness=1)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=16)

        # Prompt text
        self.lbl_prompt = tk.Label(
            self.content_frame,
            text=f"Are you sure you want to completely uninstall {APP_TITLE}?",
            bg="#FFFFFF",
            fg="#1C1917",
            font=("Segoe UI", 11, "bold"),
            anchor="w",
        )
        self.lbl_prompt.pack(fill=tk.X)

        self.lbl_desc = tk.Label(
            self.content_frame,
            text="This will completely remove the following components with nothing left behind:",
            bg="#FFFFFF",
            fg="#57534E",
            font=("Segoe UI", 9),
            anchor="w",
        )
        self.lbl_desc.pack(fill=tk.X, pady=(4, 12))

        # Checklist preview
        items_frame = tk.Frame(self.content_frame, bg="#F5F5F4", padx=14, pady=12, highlightbackground="#E7E5E4", highlightthickness=1)
        items_frame.pack(fill=tk.X, pady=(0, 14))

        checklist = [
            "✔  Program executables, libraries, and installation files",
            "✔  Desktop, Start Menu, and Startup shortcuts",
            "✔  Windows Registry keys and Uninstall registrations",
            "✔  Scheduled daily background update tasks",
            "✔  Application cache, temporary logs, and local state",
        ]
        for item in checklist:
            tk.Label(
                items_frame,
                text=item,
                bg="#F5F5F4",
                fg="#292524",
                font=("Segoe UI", 9),
                anchor="w",
            ).pack(fill=tk.X, pady=2)

        # Checkbox for user data
        self.var_purge_all = tk.BooleanVar(value=True)
        self.chk_purge = tk.Checkbutton(
            self.content_frame,
            text="Also remove user backup archives, configuration files, and tracking history",
            variable=self.var_purge_all,
            bg="#FFFFFF",
            fg="#1C1917",
            activebackground="#FFFFFF",
            selectcolor="#FFFFFF",
            font=("Segoe UI", 9),
        )
        self.chk_purge.pack(anchor="w", pady=(0, 10))

        # Status and Progress Bar (hidden initially)
        self.progress_frame = tk.Frame(self.content_frame, bg="#FFFFFF")
        
        self.lbl_status = tk.Label(
            self.progress_frame,
            text="Ready to uninstall...",
            bg="#FFFFFF",
            fg="#78716C",
            font=("Segoe UI", 9, "italic"),
            anchor="w",
        )
        self.lbl_status.pack(fill=tk.X, pady=(0, 6))

        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            orient="horizontal",
            mode="determinate",
            length=480,
        )
        self.progress_bar.pack(fill=tk.X)

        # Bottom Button Bar
        self.bottom_bar = tk.Frame(self.root, bg="#FAFAF9", padx=20, pady=12)
        self.bottom_bar.pack(fill=tk.X, side=tk.BOTTOM)

        self.btn_cancel = tk.Button(
            self.bottom_bar,
            text="Cancel",
            bg="#E7E5E4",
            fg="#1C1917",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.root.destroy,
        )
        self.btn_cancel.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_uninstall = tk.Button(
            self.bottom_bar,
            text="Uninstall Now",
            bg="#B91C1C",
            fg="#FFFFFF",
            activebackground="#991B1B",
            activeforeground="#FFFFFF",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=18,
            pady=6,
            cursor="hand2",
            command=self._start_uninstall,
        )
        self.btn_uninstall.pack(side=tk.RIGHT)

    def _start_uninstall(self) -> None:
        self.btn_uninstall.config(state="disabled")
        self.btn_cancel.config(state="disabled")
        self.chk_purge.config(state="disabled")

        # Show progress
        self.progress_frame.pack(fill=tk.X, pady=(4, 0))
        self.root.update()

        # Run uninstallation in background thread
        import threading
        thread = threading.Thread(target=self._worker, daemon=True)
        thread.start()

    def _worker(self) -> None:
        def on_progress(msg: str, progress: float):
            self.root.after(0, lambda: self._update_progress(msg, progress))

        summary = self.uninstaller.execute_full_uninstall(
            target_dir=self.target_dir,
            force_delete_all=self.var_purge_all.get(),
            progress_callback=on_progress,
        )

        self.root.after(0, lambda: self._show_completed(summary))

    def _update_progress(self, msg: str, progress: float):
        self.lbl_status.config(text=msg)
        self.progress_bar["value"] = progress * 100
        self.root.update_idletasks()

    def _show_completed(self, summary: UninstallSummary):
        self.lbl_status.config(text="✔ All application components successfully removed.")
        self.progress_bar["value"] = 100

        # Swap content to Success screen
        for child in self.content_frame.winfo_children():
            child.destroy()

        lbl_success_icon = self.tk.Label(
            self.content_frame,
            text="✅",
            font=("Segoe UI", 32),
            bg="#FFFFFF",
            fg="#16A34A",
        )
        lbl_success_icon.pack(pady=(16, 6))

        lbl_success_title = self.tk.Label(
            self.content_frame,
            text="Uninstallation Completed Successfully",
            bg="#FFFFFF",
            fg="#15803D",
            font=("Segoe UI", 12, "bold"),
        )
        lbl_success_title.pack(pady=(0, 6))

        msg = (
            f"{APP_TITLE} has been completely removed from your system.\n\n"
            f"• Shortcuts removed: {len(summary.shortcuts_removed)}\n"
            f"• Registry entries deleted: {len(summary.registry_keys_removed) + len(summary.registry_values_removed)}\n"
            f"• Scheduled background tasks removed: {len(summary.tasks_removed)}\n"
            f"• Leftover AppData directories wiped: {len(summary.appdata_dirs_removed)}\n"
            f"• Files deleted: {len(summary.files_removed)}\n\n"
            f"Nothing was left behind."
        )

        lbl_details = self.tk.Label(
            self.content_frame,
            text=msg,
            bg="#FFFFFF",
            fg="#374151",
            font=("Segoe UI", 9),
            justify="center",
        )
        lbl_details.pack(pady=(0, 10))

        # Bottom button
        self.btn_cancel.destroy()
        self.btn_uninstall.config(
            text="Close",
            bg="#4B5563",
            activebackground="#374151",
            state="normal",
            command=self.root.destroy,
        )

    def run(self) -> None:
        self.root.mainloop()


def run_silent_uninstall(uninstaller: Uninstaller, target_dir: Optional[Path] = None, force_all: bool = True) -> int:
    """Executes silent uninstallation without GUI."""
    print(f"=== {APP_TITLE} Silent Uninstaller ===")
    print("Starting complete uninstallation...")

    def cli_progress(msg: str, progress: float):
        print(f"[{int(progress * 100):3d}%] {msg}")

    summary = uninstaller.execute_full_uninstall(
        target_dir=target_dir,
        force_delete_all=force_all,
        progress_callback=cli_progress,
    )

    print("\n" + "=" * 50)
    print("UNINSTALLATION SUMMARY:")
    print(f"  Shortcuts removed: {len(summary.shortcuts_removed)}")
    print(f"  Registry entries deleted: {len(summary.registry_keys_removed) + len(summary.registry_values_removed)}")
    print(f"  Scheduled tasks removed: {len(summary.tasks_removed)}")
    print(f"  AppData directories wiped: {len(summary.appdata_dirs_removed)}")
    print(f"  Files removed: {len(summary.files_removed)}")
    print(f"  Total items removed: {summary.total_items_removed}")
    print("=" * 50)
    print("Uninstallation completed successfully. Nothing left behind.")
    return 0


def run_dry_run(uninstaller: Uninstaller) -> int:
    """Discovers and displays all components that would be removed."""
    print(f"=== {APP_TITLE} Uninstaller — Dry Run Inspection ===")
    
    shortcuts = uninstaller.find_shortcuts()
    print(f"\n[Shortcuts to remove: {len(shortcuts)}]")
    for sc in shortcuts:
        print(f"  • {sc}")

    appdata = uninstaller.find_appdata_paths()
    print(f"\n[AppData directories to wipe: {len(appdata)}]")
    for ad in appdata:
        print(f"  • {ad}")

    install_dir = uninstaller.target_install_dir
    print(f"\n[Install directory detected: {install_dir}]")
    if install_dir and install_dir.exists():
        is_dev = uninstaller.is_dev_source_directory(install_dir)
        print(f"  • Type: {'Development Workspace (safe mode)' if is_dev else 'Standard Installation Folder'}")

    print("\nDry run completed. No files or settings were modified.")
    return 0


def main():
    parser = argparse.ArgumentParser(description=f"Complete Uninstaller for {APP_TITLE}")
    parser.add_argument("--silent", "-s", "--quiet", action="store_true", help="Run uninstallation silently without GUI")
    parser.add_argument("--dry-run", action="store_true", help="Inspect and list components to remove without deleting")
    parser.add_argument("--force", "-f", action="store_true", help="Bypass all confirmation prompts")
    parser.add_argument("--target-dir", type=str, default=None, help="Explicit installation directory to remove")
    parser.add_argument("--register", action="store_true", help="Register application in Windows Registry (Settings > Installed Apps)")
    parser.add_argument("--relocated", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--target-pid", type=int, default=None, help=argparse.SUPPRESS)

    args = parser.parse_args()

    target_path = Path(args.target_dir).resolve() if args.target_dir else None

    # Handle --register helper
    if args.register:
        inst_dir = target_path or Path.cwd()
        ok = Uninstaller.register_in_windows_registry(inst_dir)
        sys.exit(0 if ok else 1)

    uninstaller = Uninstaller(target_install_dir=target_path)
    effective_target = target_path or uninstaller.target_install_dir

    # Check if we should self-relocate to %TEMP% to prevent file-locking:
    # Only relocate if running as a frozen executable and running from INSIDE the target install directory
    if (
        hasattr(sys, "frozen")
        and not args.relocated
        and not args.dry_run
        and effective_target
        and is_inside_dir(Path(sys.executable), effective_target)
    ):
        relocate_to_temp_and_relaunch(target_dir=effective_target, silent=args.silent)
        return

    # If running as relocated child, wait for parent to exit
    if args.relocated and args.target_pid:
        wait_for_parent_pid(args.target_pid)


    if args.dry_run:
        sys.exit(run_dry_run(uninstaller))

    if args.silent:
        ret = run_silent_uninstall(uninstaller, target_dir=target_path, force_all=True)
        if args.relocated:
            schedule_temp_cleanup()
        sys.exit(ret)

    # Interactive GUI mode
    try:
        gui = UninstallerGUI(uninstaller, target_dir=target_path, force=args.force)
        gui.run()
        if args.relocated:
            schedule_temp_cleanup()
        sys.exit(0)
    except Exception as e:
        logger.error(f"GUI launch failed, falling back to silent execution: {e}")
        ret = run_silent_uninstall(uninstaller, target_dir=target_path, force_all=True)
        if args.relocated:
            schedule_temp_cleanup()
        sys.exit(ret)


if __name__ == "__main__":
    main()
