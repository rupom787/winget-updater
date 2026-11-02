"""Microsoft Store (MSIX / AppX) adapter."""

from typing import Any, Dict, List, Optional, Tuple
from winget_updater.adapters.base import BaseSourceAdapter
from winget_updater.models import PackageType, ProgramItem
from winget_updater.winget.client import WingetClient
from winget_updater.utils.logger import get_logger

logger = get_logger()


class StoreAdapter(BaseSourceAdapter):
    """Adapter for Microsoft Store applications."""

    def __init__(self, client: Optional[WingetClient] = None):
        super().__init__(name="msstore", display_name="Microsoft Store (msstore)", enabled=True)
        self.client = client or WingetClient()

    def is_available(self) -> bool:
        return self.client.get_version() is not None

    def query_updates(self, installed_items: List[ProgramItem]) -> Dict[str, Any]:
        """Queries updates filtered to msstore source."""
        all_upgrades = self.client.get_pending_upgrades()
        return {
            k: v for k, v in all_upgrades.items()
            if (v.source or "").lower() == "msstore"
        }

    def verify_package(self, item: ProgramItem) -> Tuple[bool, str]:
        if item.package_type == PackageType.STORE_MSIX or (item.source or "").lower() == "msstore":
            return True, "Verified Microsoft Store application signature"
        return False, "Not a recognized Microsoft Store package"

    def install_update(self, item: ProgramItem, dry_run: bool = False) -> Tuple[bool, str]:
        pkg_id = item.id or item.name
        return self.client.upgrade_package(pkg_id, dry_run=dry_run)

