"""Windows Task Scheduler integration and pre-run safety guards."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple
from winget_updater.compatibility.system_info import SystemInfoProvider
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()
TASK_NAME = "WingetUpdaterDaily"


class SchedulerManager:
    """Manages creation, query, and removal of the once-daily Windows scheduled task."""

    def __init__(self, task_name: str = TASK_NAME, sys_info: Optional[SystemInfoProvider] = None):
        self.task_name = task_name
        self.sys = sys_info or SystemInfoProvider()

    def check_safety_guards(self, allow_battery: bool = False) -> Tuple[bool, str]:
        """Validates all safety prerequisites before starting a scheduled run.
        
        Checks:
        1. PC must be connected to AC power (unless battery mode explicitly allowed).
        2. PC must not be heavily loaded (CPU < 90%).
        3. Sufficient disk space on system drive (>= 1.5 GB free).
        """
        if not allow_battery:
            is_ac, pwr_msg = self.sys.is_on_ac_power()
            if not is_ac:
                logger.warning(f"Scheduled run aborted: {pwr_msg}")
                return False, f"Safety check failed: {pwr_msg}. Scheduled runs require AC power."

        cpu_load = self.sys.get_cpu_load_percent()
        if cpu_load > 90.0:
            logger.warning(f"Scheduled run delayed: PC is heavily loaded (CPU: {cpu_load:.1f}%)")
            return False, f"Safety check failed: PC is heavily loaded ({cpu_load:.1f}% CPU)."

        # Check free disk space on system drive
        try:
            sys_drive = os.environ.get("SystemDrive", "C:")
            free_bytes = shutil.disk_usage(sys_drive).free
            free_gb = free_bytes / (1024 ** 3)
            if free_gb < 1.5:
                logger.warning(f"Scheduled run aborted: Low system disk space ({free_gb:.2f} GB free)")
                return False, f"Safety check failed: System drive low on space ({free_gb:.2f} GB free, requires >= 1.5 GB)."
        except Exception:
            pass

        return True, "Safety checks passed: AC power verified and CPU load within safe operational limits."

    def create_daily_task(self, time_hh_mm: str = "12:00") -> Tuple[bool, str]:
        """Creates or updates a Windows Task Scheduler job to run once daily while the user is logged in.
        
        Uses /IT to guarantee the job runs ONLY while the user is logged on,
        and /RL HIGHEST to execute with necessary elevated administrative permissions.
        """
        python_exe = sys.executable
        # Target execution script
        if hasattr(sys, "frozen"):
            cmd_target = f'"{python_exe}" --scheduled'
        else:
            main_script = Path.cwd() / "run.py"
            cmd_target = f'"{python_exe}" "{main_script}" --scheduled'

        schtasks_cmd = [
            "schtasks.exe",
            "/Create",
            "/TN", self.task_name,
            "/TR", cmd_target,
            "/SC", "DAILY",
            "/ST", time_hh_mm,
            "/IT",            # Run ONLY when the user is logged on
            "/RL", "HIGHEST", # Run with highest administrator privileges
            "/F",             # Overwrite existing task
        ]

        logger.info(f"Registering scheduled task '{self.task_name}' at {time_hh_mm} daily...")
        try:
            res = silent_run(
                schtasks_cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            if res.returncode == 0:
                msg = f"Scheduled task '{self.task_name}' successfully configured for {time_hh_mm} daily (logged-on only)."
                logger.info(msg)
                return True, msg
            else:
                err = res.stderr.strip() or res.stdout.strip()
                logger.error(f"Failed to create scheduled task: {err}")
                return False, err
        except Exception as e:
            logger.error(f"Error invoking schtasks.exe: {e}")
            return False, str(e)

    def delete_task(self) -> Tuple[bool, str]:
        """Deletes the scheduled task from Windows Task Scheduler."""
        cmd = ["schtasks.exe", "/Delete", "/TN", self.task_name, "/F"]
        try:
            res = silent_run(cmd, capture_output=True, text=True, timeout=20)
            if res.returncode == 0:
                return True, f"Scheduled task '{self.task_name}' deleted."
            return False, res.stderr.strip() or f"Error code {res.returncode}"
        except Exception as e:
            return False, str(e)

    def query_task(self) -> Optional[str]:
        """Queries the status of the scheduled task."""
        cmd = ["schtasks.exe", "/Query", "/TN", self.task_name, "/FO", "LIST"]
        try:
            res = silent_run(cmd, capture_output=True, text=True, timeout=20)
            if res.returncode == 0:
                return res.stdout.strip()
            return None
        except Exception:
            return None

    def is_scheduled_task_enabled(self) -> bool:
        """Checks if the scheduled task is actively registered in Windows Task Scheduler."""
        out = self.query_task()
        return out is not None and self.task_name.lower() in out.lower()

    def is_task_scheduled(self) -> Tuple[bool, str]:
        """Queries if task exists and returns (exists, details_string)."""
        info = self.query_task()
        if info and self.task_name.lower() in info.lower():
            return True, info
        return False, "No automated schedule configured"

    def delete_daily_task(self) -> Tuple[bool, str]:
        """Alias for delete_task to maintain compatibility."""
        return self.delete_task()

    def get_scheduled_time(self) -> Optional[str]:
        """Extracts the scheduled run time from task query output."""
        out = self.query_task()
        if not out:
            return None
        import re
        m = re.search(r"(?:Start Time|Schedule Time)\s*:\s*(\d{1,2}:\d{2})", out, re.IGNORECASE)
        if m:
            return m.group(1)
        return None

