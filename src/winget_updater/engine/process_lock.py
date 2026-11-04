"""Running process detection and termination for software updates.
Detects if an application's executables are actively running before applying an update
to prevent file locking and installer error 1618.
"""

import os
import subprocess
from typing import List, Optional, Tuple
from winget_updater.models import ProgramItem
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()


class ProcessLockDetector:
    """Detects and gracefully manages running processes associated with software packages."""

    @staticmethod
    def get_all_running_processes() -> List[Tuple[int, str]]:
        """Returns a list of (pid, process_name) currently active on Windows."""
        processes = []
        try:
            # Run tasklist in CSV format: "Image Name","PID","Session Name","Session#","Mem Usage"
            res = silent_run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )
            if res.returncode == 0:
                for line in res.stdout.splitlines():
                    parts = [p.strip('"') for p in line.split('","')]
                    if len(parts) >= 2:
                        p_name = parts[0].strip().strip('"')
                        try:
                            pid = int(parts[1].strip().strip('"'))
                            processes.append((pid, p_name))
                        except ValueError:
                            pass
        except Exception as e:
            logger.debug(f"Error querying tasklist: {e}")
        return processes

    @classmethod
    def find_running_processes_for_item(cls, item: ProgramItem) -> List[Tuple[int, str]]:
        """Identifies running processes that belong to or are likely locking the specified program."""
        active = cls.get_all_running_processes()
        if not active:
            return []

        # Derive candidate executable names
        candidates = set()

        # 1. From item name: e.g. "Google Chrome" -> "chrome.exe", "VLC media player" -> "vlc.exe"
        raw_name = item.name.lower()
        if "chrome" in raw_name:
            candidates.add("chrome.exe")
        elif "firefox" in raw_name:
            candidates.add("firefox.exe")
        elif "vlc" in raw_name:
            candidates.add("vlc.exe")
        elif "discord" in raw_name:
            candidates.add("discord.exe")
        elif "slack" in raw_name:
            candidates.add("slack.exe")
        elif "zoom" in raw_name:
            candidates.add("zoom.exe")
        elif "spotify" in raw_name:
            candidates.add("spotify.exe")
        elif "steam" in raw_name:
            candidates.add("steam.exe")
        elif "git" in raw_name:
            candidates.add("git.exe")
        elif "notepad++" in raw_name or "notepadplusplus" in raw_name:
            candidates.add("notepad++.exe")
        elif "visual studio code" in raw_name or "vscode" in raw_name:
            candidates.add("code.exe")
        elif "node.js" in raw_name or "nodejs" in raw_name or "npm" in raw_name or (item.source and item.source.lower() == "npm"):
            candidates.add("node.exe")
            candidates.add("npm.cmd")
        elif "pip" in raw_name or (item.source and item.source.lower() == "pip"):
            candidates.add("python.exe")
            candidates.add("pythonw.exe")

        # Generic name simplification: first word + .exe
        first_word = raw_name.split()[0].replace(".", "").replace("-", "")
        if len(first_word) >= 3:
            candidates.add(f"{first_word}.exe")

        # 2. From package ID: e.g. "Git.Git" -> "git.exe", "Mozilla.Firefox" -> "firefox.exe"
        if item.id:
            id_parts = item.id.lower().split(".")
            for part in id_parts:
                if len(part) >= 3:
                    candidates.add(f"{part}.exe")

        # 3. From install location: scan for .exe files in top-level directory
        if item.install_location and os.path.exists(item.install_location):
            try:
                for entry in os.scandir(item.install_location):
                    if entry.is_file() and entry.name.lower().endswith(".exe"):
                        candidates.add(entry.name.lower())
            except Exception:
                pass

        matched = []
        for pid, p_name in active:
            if p_name.lower() in candidates:
                # Exclude Windows system processes
                if p_name.lower() not in ("explorer.exe", "svchost.exe", "system", "cmd.exe", "powershell.exe"):
                    matched.append((pid, p_name))

        return matched

    @staticmethod
    def terminate_processes(pids: List[int], force: bool = True) -> Tuple[bool, str]:
        """Terminates specified process IDs (gracefully first, then forcibly if requested)."""
        if not pids:
            return True, "No processes to terminate"

        success_all = True
        messages = []

        for pid in pids:
            cmd = ["taskkill", "/PID", str(pid)]
            if force:
                cmd.append("/F")

            try:
                res = silent_run(cmd, capture_output=True, text=True, timeout=10)
                if res.returncode == 0:
                    messages.append(f"Terminated PID {pid}")
                else:
                    success_all = False
                    messages.append(f"Could not terminate PID {pid}: {res.stderr.strip() or res.stdout.strip()}")
            except Exception as e:
                success_all = False
                messages.append(f"Error terminating PID {pid}: {e}")

        return success_all, "; ".join(messages)

