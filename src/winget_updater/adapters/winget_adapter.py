"""Winget source adapter for official Windows Package Manager repositories."""

from typing import Any, Dict, List, Optional, Tuple
from winget_updater.adapters.base import BaseSourceAdapter
from winget_updater.models import ProgramItem, UpdateAction
from winget_updater.winget.client import WingetClient, WingetPackageEntry
from winget_updater.utils.logger import get_logger

logger = get_logger()


class WingetAdapter(BaseSourceAdapter):
    """Adapter for official winget repository."""

    def __init__(self, client: Optional[WingetClient] = None):
        super().__init__(name="winget", display_name="Windows Package Manager (winget)", enabled=True)
        self.client = client or WingetClient()

    def is_available(self) -> bool:
        ver = self.client.get_version()
        return ver is not None

    def query_updates(self, installed_items: List[ProgramItem]) -> Dict[str, WingetPackageEntry]:
        """Fetches pending upgrades from winget."""
        return self.client.get_pending_upgrades()

    def get_installed_packages(self) -> Dict[str, WingetPackageEntry]:
        """Fetches all packages recognized by winget."""
        return self.client.get_installed_packages()

    def verify_package(self, item: ProgramItem) -> Tuple[bool, str]:
        """Validates that the package ID belongs to trusted sources (winget or msstore)."""
        if not item.id:
            return False, "Missing package identifier"
        src = (item.source or "").lower()
        if src in ("winget", "msstore"):
            return True, f"Verified trusted repository source: {src}"
        return False, f"Unverified source repository: {item.source}"

    def install_update(self, item: ProgramItem, dry_run: bool = False) -> Tuple[bool, str]:
        """Executes winget upgrade for the package with speed optimization."""
        pkg_id = item.id or item.name
        return self.client.upgrade_package(pkg_id, dry_run=dry_run)

    def install_package(self, pkg_id: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Installs a package directly via winget with fast silent execution."""
        return self.client.install_package(pkg_id, dry_run=dry_run)

    def uninstall_package(self, pkg_id: str) -> Tuple[bool, str]:
        """Uninstalls a package cleanly and rapidly via silent winget."""
        return self.client.uninstall_package(pkg_id, dry_run=False)

    def update_sources(self) -> Tuple[bool, str]:
        """Synchronizes and updates the winget package index."""
        return self.client.update_sources()

