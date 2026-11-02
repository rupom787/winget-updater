"""Source manager orchestrating modular update source adapters."""

from typing import Dict, List, Optional
from winget_updater.adapters.base import BaseSourceAdapter
from winget_updater.adapters.store_adapter import StoreAdapter
from winget_updater.adapters.vendor_adapter import VendorAdapter
from winget_updater.adapters.winget_adapter import WingetAdapter
from winget_updater.config import ConfigManager
from winget_updater.utils.logger import get_logger

logger = get_logger()


class SourceManager:
    """Discovers, tracks, and manages all update adapters."""

    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager()
        self.adapters: Dict[str, BaseSourceAdapter] = {}
        self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        """Initializes default source adapters."""
        winget = WingetAdapter()
        store = StoreAdapter()
        vendor = VendorAdapter(self.config)

        self.register_adapter(winget)
        self.register_adapter(store)
        self.register_adapter(vendor)

    def register_adapter(self, adapter: BaseSourceAdapter) -> None:
        """Registers a new source adapter."""
        self.adapters[adapter.name] = adapter
        logger.debug(f"Registered update adapter: {adapter.display_name} (available: {adapter.is_available()})")

    def get_adapter(self, name: str) -> Optional[BaseSourceAdapter]:
        return self.adapters.get(name)

    def get_available_sources(self) -> List[str]:
        """Returns names of all available, reachable sources."""
        return [
            adapter.name for adapter in self.adapters.values()
            if adapter.enabled and adapter.is_available()
        ]

    def set_adapter_enabled(self, name: str, enabled: bool) -> None:
        if name in self.adapters:
            self.adapters[name].enabled = enabled
            logger.info(f"Adapter '{name}' enabled status set to: {enabled}")

