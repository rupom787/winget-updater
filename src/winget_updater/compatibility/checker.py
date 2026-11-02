"""Pre-update compatibility validation evaluating Architecture, Windows build, Disk, and CPU."""

import re
from typing import Optional
from winget_updater.compatibility.system_info import SystemInfoProvider
from winget_updater.models import CompatibilityDetails, CompatibilityStatus, ProgramItem
from winget_updater.utils.logger import get_logger
from winget_updater.winget.client import WingetPackageDetails

logger = get_logger()

# Minimum disk headroom required before attempting an update (in Megabytes)
MIN_FREE_DISK_MB = 500.0

# Max CPU load threshold where updating would cause severe system degradation
MAX_CPU_LOAD_PERCENT = 95.0


class CompatibilityChecker:
    """Validates host PC compatibility before permitting package updates."""

    def __init__(
        self,
        min_disk_mb: float = MIN_FREE_DISK_MB,
        max_cpu_percent: float = MAX_CPU_LOAD_PERCENT,
        system_info: Optional[SystemInfoProvider] = None,
    ):
        self.min_disk_mb = min_disk_mb
        self.max_cpu_percent = max_cpu_percent
        self.sys = system_info or SystemInfoProvider()

    def check(
        self,
        item: ProgramItem,
        details: Optional[WingetPackageDetails] = None,
    ) -> CompatibilityDetails:
        """Performs full compatibility check on the package against this PC."""
        reasons = []
        status = CompatibilityStatus.COMPATIBLE
        arch_ok = True
        os_ok = True
        disk_ok = True
        cpu_ok = True

        host_arch = self.sys.get_architecture()
        host_build = self.sys.get_windows_build()
        is_win11 = self.sys.is_windows_11()

        # 1. Target OS check: Tool targets Windows 11 only
        if not is_win11:
            os_ok = False
            status = CompatibilityStatus.INCOMPATIBLE
            reasons.append(
                f"Incompatible OS: Host build {host_build} does not meet Windows 11 requirement (>= 22000)"
            )

        # Check package-specific minimum OS version if known
        if details and details.min_os_version:
            # e.g., "10.0.22621" -> build 22621
            match = re.search(r"(\d{5,})", details.min_os_version)
            if match:
                req_build = int(match.group(1))
                if host_build < req_build:
                    os_ok = False
                    status = CompatibilityStatus.INCOMPATIBLE
                    reasons.append(
                        f"Package requires Windows build >= {req_build}, host is {host_build}"
                    )

        # 2. Architecture compatibility check
        target_arch = (details.architecture if details else None)
        if target_arch:
            norm_target = target_arch.strip().lower()
            if not self._is_arch_compatible(host_arch, norm_target):
                arch_ok = False
                status = CompatibilityStatus.INCOMPATIBLE
                reasons.append(
                    f"Incompatible architecture: Package targets '{target_arch}' but PC is '{host_arch}'"
                )

        # 3. Disk space check on installation drive
        install_path = item.install_location or "C:\\"
        free_mb = self.sys.get_free_disk_space_mb(install_path)
        if free_mb < self.min_disk_mb:
            disk_ok = False
            status = CompatibilityStatus.INCOMPATIBLE
            reasons.append(
                f"Insufficient disk space: {free_mb:.1f} MB available, requires at least {self.min_disk_mb:.1f} MB"
            )

        # 4. CPU capacity check
        cpu_load = self.sys.get_cpu_load_percent()
        if cpu_load >= self.max_cpu_percent:
            cpu_ok = False
            # If everything else passed, excessive CPU load marks as warning or capacity-constrained
            if status != CompatibilityStatus.INCOMPATIBLE:
                status = CompatibilityStatus.WARNING
            reasons.append(
                f"High CPU utilization: System load is {cpu_load:.1f}% (threshold {self.max_cpu_percent:.1f}%)"
            )

        details_obj = CompatibilityDetails(
            status=status,
            reasons=reasons,
            arch_ok=arch_ok,
            os_ok=os_ok,
            disk_ok=disk_ok,
            cpu_ok=cpu_ok,
        )
        item.compatibility = details_obj
        return details_obj

    def _is_arch_compatible(self, host_arch: str, target_arch: str) -> bool:
        """Determines if host architecture can execute the target installer."""
        if target_arch in ("neutral", "all", "any"):
            return True

        if host_arch == "x64":
            # x64 runs x64 and x86 (via WOW64). Cannot run ARM64 native binaries.
            return target_arch in ("x64", "x86", "x86_64", "amd64", "win32")

        if host_arch == "arm64":
            # Windows 11 ARM64 natively executes ARM64 and provides emulation for x64 and x86
            return True

        if host_arch == "x86":
            # 32-bit x86 can only run 32-bit x86 binaries
            return target_arch in ("x86", "win32", "i386")

        return True

