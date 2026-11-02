"""System hardware, OS version, disk, CPU, and power telemetry for Windows 11."""

import ctypes
import os
import platform
import shutil
import sys
import time
from ctypes import wintypes
from typing import Optional, Tuple
from winget_updater.utils.logger import get_logger

logger = get_logger()

# Minimum build number for Windows 11 (21H2 initial release was 22000)
WINDOWS_11_MIN_BUILD = 22000


class SYSTEM_POWER_STATUS(ctypes.Structure):
    _fields_ = [
        ("ACLineStatus", wintypes.BYTE),
        ("BatteryFlag", wintypes.BYTE),
        ("BatteryLifePercent", wintypes.BYTE),
        ("SystemStatusFlag", wintypes.BYTE),
        ("BatteryLifeTime", wintypes.DWORD),
        ("BatteryFullLifeTime", wintypes.DWORD),
    ]


class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_uint64),
        ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64),
        ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64),
        ("ullAvailVirtual", ctypes.c_uint64),
        ("ullAvailExtendedVirtual", ctypes.c_uint64),
    ]


class SystemInfoProvider:
    """Provides real-time host system telemetry."""

    @staticmethod
    def get_architecture() -> str:
        """Returns normalized host processor architecture (x64, arm64, x86)."""
        arch = platform.machine().lower()
        if arch in ("amd64", "x86_64", "x64"):
            return "x64"
        elif "arm" in arch:
            return "arm64" if "64" in arch else "arm"
        elif arch in ("x86", "i386", "i686"):
            return "x86"
        return arch

    @staticmethod
    def get_windows_build() -> int:
        """Returns the Windows kernel build number."""
        try:
            return sys.getwindowsversion().build
        except Exception:
            return 0

    @classmethod
    def is_windows_11(cls) -> bool:
        """Verifies if the host OS is Windows 11 (build >= 22000)."""
        return cls.get_windows_build() >= WINDOWS_11_MIN_BUILD

    @staticmethod
    def get_free_disk_space_mb(path: Optional[str] = None) -> float:
        """Returns available free disk space in Megabytes on target path or C:."""
        target = "C:\\"
        if path:
            try:
                # Extract drive root
                drive = os.path.splitdrive(path)[0]
                if drive:
                    target = f"{drive}\\"
            except Exception:
                target = "C:\\"

        try:
            usage = shutil.disk_usage(target)
            return usage.free / (1024 * 1024)
        except Exception as e:
            logger.debug(f"Failed to check disk usage on {target}: {e}")
            return 10240.0  # Fallback assumption 10GB if unable to probe

    @staticmethod
    def get_cpu_load_percent(sample_interval: float = 0.05) -> float:
        """Measures instant system CPU utilization via GetSystemTimes."""
        try:
            idle1, kernel1, user1 = FILETIME(), FILETIME(), FILETIME()
            if not ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle1), ctypes.byref(kernel1), ctypes.byref(user1)
            ):
                return 0.0

            time.sleep(sample_interval)

            idle2, kernel2, user2 = FILETIME(), FILETIME(), FILETIME()
            if not ctypes.windll.kernel32.GetSystemTimes(
                ctypes.byref(idle2), ctypes.byref(kernel2), ctypes.byref(user2)
            ):
                return 0.0

            def to_int(ft: FILETIME) -> int:
                return (ft.dwHighDateTime << 32) + ft.dwLowDateTime

            idle = to_int(idle2) - to_int(idle1)
            kernel = to_int(kernel2) - to_int(kernel1)
            user = to_int(user2) - to_int(user1)
            total = kernel + user

            if total <= 0:
                return 0.0

            cpu_pct = (1.0 - (idle / total)) * 100.0
            return max(0.0, min(100.0, cpu_pct))
        except Exception as e:
            logger.debug(f"CPU load sampling exception: {e}")
            return 0.0

    @staticmethod
    def get_memory_info() -> Tuple[float, float, int]:
        """Returns physical RAM usage tuple: (used_gb, total_gb, memory_load_percent)."""
        try:
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                total_gb = stat.ullTotalPhys / (1024 ** 3)
                used_gb = (stat.ullTotalPhys - stat.ullAvailPhys) / (1024 ** 3)
                return round(used_gb, 1), round(total_gb, 1), int(stat.dwMemoryLoad)
        except Exception as e:
            logger.debug(f"Memory status query failed: {e}")
        return 0.0, 0.0, 0

    @staticmethod
    def is_on_ac_power() -> Tuple[bool, str]:
        """Checks if device is running on AC power.
        
        Returns:
            (is_on_ac, status_description)
        """
        try:
            status = SYSTEM_POWER_STATUS()
            if ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
                # ACLineStatus: 0 = Offline (battery), 1 = Online (AC), 255 = Unknown
                if status.ACLineStatus == 1:
                    return True, "Connected to AC line power"
                elif status.ACLineStatus == 0:
                    pct = status.BatteryLifePercent
                    return False, f"Running on Battery power ({pct}% remaining)"
                else:
                    # 255 or desktop with no battery
                    return True, "Power status unknown / Desktop AC assumed"
            return True, "Power query not supported (assumed AC)"
        except Exception as e:
            logger.debug(f"Power status query failed: {e}")
            return True, "Power status check error (assumed AC)"

