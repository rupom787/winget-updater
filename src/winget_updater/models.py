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
    SCOOP = "Scoop Package"
    CHOCOLATEY = "Chocolatey Package"
    PIP = "Python (Pip)"
    NPM = "Node.js (Npm)"
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
    PINNED = "Pinned Version"
    SKIPPED_VERSION = "Skipped Version"
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
    unavailability_reason: Optional[str] = None
    vendor_url: Optional[str] = None
    is_user_bound: bool = False
    is_pinned: bool = False
    pinned_version: Optional[str] = None
    skipped_version: Optional[str] = None

    def get_diagnostic_reason(self) -> str:
        """Returns clear, human-readable reason why an application cannot be updated automatically."""
        if self.unavailability_reason:
            return self.unavailability_reason
        if self.action == UpdateAction.PINNED:
            return f"Application is pinned to version {self.pinned_version or self.installed_version}."
        if self.action == UpdateAction.SKIPPED_VERSION:
            return f"Update version {self.skipped_version} was skipped by user."
        if self.action == UpdateAction.UP_TO_DATE:
            return "Application is already running the latest verified release."
        if self.action == UpdateAction.EXCLUDED:
            return "Application is excluded by user filter rule."
        if self.action == UpdateAction.UNVERIFIED:
            return "Package could not be verified automatically (ambiguous name or publisher mismatch). You can bind its Winget ID or review manually."
        if self.action == UpdateAction.NO_SOURCE:
            return "No public package source found in Winget or Store repositories. Use 'Bind Winget ID' or 'Visit Website'."
        if self.package_type == PackageType.DRIVER:
            return "Device drivers are OEM-signed and maintained safely via Windows Update or vendor firmware."
        if self.package_type == PackageType.BROWSER_EXTENSION:
            return "Browser extensions are updated automatically through their respective browser web store."
        if self.package_type == PackageType.PORTABLE:
            return "Standalone portable executable without package installer manifest."
        if not self.compatibility.is_compatible:
            return f"Incompatible system environment: {'; '.join(self.compatibility.reasons)}"
        return "Not eligible for automatic update."

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
        # Prevent phantom updates: reject placeholder dashes or identical versions
        if self.latest_version == "—":
            return False
        if self.installed_version and self.latest_version and str(self.latest_version).strip().lower() == str(self.installed_version).strip().lower():
            return False
        if not self.compatibility.is_compatible:
            return False
        if self.package_type not in (
            PackageType.WIN32_EXE,
            PackageType.WIN32_MSI,
            PackageType.STORE_MSIX,
            PackageType.PIP,
            PackageType.NPM,
            PackageType.SCOOP,
            PackageType.CHOCOLATEY,
        ):
            return False
        return True

