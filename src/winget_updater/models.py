"""Data models and enumerations for the software update management system."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PackageType(str, Enum):
    """Categorization of installed software."""
    WIN32_EXE = "Win32 (.exe)"
    WIN32_MSI = "Win32 (.msi)"
    STORE_MSIX = "Store / MSIX"
    PORTABLE = "Portable App"
    BROWSER_EXTENSION = "Browser Extension"
    DRIVER = "Device Driver"
    OTHER = "Other"


class UpdateAction(str, Enum):
    """Action state determined by update checking."""
    UP_TO_DATE = "Up to date"
    AVAILABLE = "Update available"
    NO_SOURCE = "No update source"
    UNVERIFIED = "Could not verify"
    SCAN_FAILED = "Scan failed"
    VENDOR_FALLBACK = "Vendor Fallback Available"
    NEWER_THAN_SOURCE = "Installed is Newer (Downgrade Risk)"
    EXCLUDED = "Ignored"
    INCOMPATIBLE = "Incompatible System"
    LIST_ONLY = "Listed Only"


class UpdateOutcome(str, Enum):
    """Final outcome of an update attempt or run."""
    PENDING = "Pending"
    UPDATED = "Updated"
    SKIPPED = "Skipped"
    FAILED = "Failed"
    LISTED_ONLY = "Listed Only"
    AWAITING_CONFIRMATION = "Awaiting Confirmation"
    SIMULATED = "Simulated (Dry Run)"


class CompatibilityStatus(str, Enum):
    """Compatibility check evaluation result."""
    COMPATIBLE = "Compatible"
    INCOMPATIBLE = "Incompatible"
    WARNING = "Warning"


@dataclass
class CompatibilityDetails:
    """Detailed evaluation of hardware and OS compatibility."""
    status: CompatibilityStatus = CompatibilityStatus.COMPATIBLE
    reasons: List[str] = field(default_factory=list)
    arch_ok: bool = True
    os_ok: bool = True
    disk_ok: bool = True
    cpu_ok: bool = True

    @property
    def is_compatible(self) -> bool:
        return self.status != CompatibilityStatus.INCOMPATIBLE


@dataclass
class ProgramItem:
    """Represents a discovered software program, driver, or extension."""
    name: str
    installed_version: str = "Unknown"
    id: Optional[str] = None
    publisher: Optional[str] = None
    install_location: Optional[str] = None
    package_type: PackageType = PackageType.OTHER
    source: Optional[str] = None  # e.g., "winget", "msstore", "vendor_list", None
    latest_version: Optional[str] = None
    action: UpdateAction = UpdateAction.NO_SOURCE
    compatibility: CompatibilityDetails = field(default_factory=CompatibilityDetails)
    outcome: UpdateOutcome = UpdateOutcome.PENDING
    notes: str = ""
    is_verified_winget: bool = False
    vendor_installer_url: Optional[str] = None
    vendor_installer_hash: Optional[str] = None
    requires_admin: bool = True
    is_ambiguous: bool = False
    supports_rollback: bool = False

    def can_auto_update(self) -> bool:
        """Determines if the program qualifies for single-approval automatic update.
        
        Strict requirement: Automatic updates (after single approval) cover only
        packaged apps (winget, Store, MSIX) with a verified winget source.
        All others (portable, extensions, drivers, vendor fallback, unverified Win32)
        are listed only or require explicit per-app confirmation.
        """
        if not self.is_verified_winget:
            return False
        if self.action != UpdateAction.AVAILABLE:
            return False
        if not self.compatibility.is_compatible:
            return False
        if self.package_type not in (PackageType.WIN32_EXE, PackageType.WIN32_MSI, PackageType.STORE_MSIX):
            return False
        return True

