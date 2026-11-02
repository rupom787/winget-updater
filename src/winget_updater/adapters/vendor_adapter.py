"""Vendor Fallback source adapter supporting verified direct downloads."""

from typing import Any, Dict, List, Optional, Tuple
from winget_updater.adapters.base import BaseSourceAdapter
from winget_updater.config import ConfigManager
from winget_updater.models import ProgramItem
from winget_updater.utils.logger import get_logger

logger = get_logger()


class VendorAdapter(BaseSourceAdapter):
    """Adapter for user-curated vendor sources with cryptographic signature verification."""

    def __init__(self, config: Optional[ConfigManager] = None):
        super().__init__(name="vendor_fallback", display_name="Curated Vendor Sources", enabled=True)
        self.config = config or ConfigManager()

    def is_available(self) -> bool:
        return True

    def query_updates(self, installed_items: List[ProgramItem]) -> Dict[str, Any]:
        """Matches installed items against vendor_sources.json."""
        matches = {}
        for item in installed_items:
            vendor_entry = self.config.match_vendor_source(item.name, item.id)
            if vendor_entry:
                matches[item.name.lower()] = vendor_entry
        return matches

    def verify_package(self, item: ProgramItem) -> Tuple[bool, str]:
        if not item.vendor_installer_url:
            return False, "No verified vendor download URL configured"
        if not item.vendor_installer_hash:
            return False, "No SHA-256 integrity hash configured for vendor package"
        return True, "Vendor configuration contains cryptographic checksum definition"

    def install_update(self, item: ProgramItem, dry_run: bool = False) -> Tuple[bool, str]:
        # Execution handled via update engine's execute_vendor_installer to enforce temp file cleanup and sig checks
        return True, "Ready for verified installation"

