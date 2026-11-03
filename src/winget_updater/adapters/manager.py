"""Source manager orchestrating modular update source adapters.
Coordinates WinGet, Scoop, Chocolatey, Pip, Npm, Microsoft Store, and Vendor fallbacks.
"""

from typing import Any, Dict, List, Optional, Tuple
from winget_updater.adapters.base import BaseSourceAdapter
from winget_updater.adapters.chocolatey_adapter import ChocolateyAdapter
from winget_updater.adapters.npm_adapter import NpmAdapter
from winget_updater.adapters.pip_adapter import PipAdapter
from winget_updater.adapters.scoop_adapter import ScoopAdapter
from winget_updater.adapters.store_adapter import StoreAdapter
from winget_updater.adapters.vendor_adapter import VendorAdapter
from winget_updater.adapters.winget_adapter import WingetAdapter
from winget_updater.config import ConfigManager
from winget_updater.models import PackageType, ProgramItem, UpdateAction
from winget_updater.utils.logger import get_logger

logger = get_logger()


class SourceManager:
    """Discovers, tracks, and manages all update adapters across WinGet, Scoop, Choco, Pip, and Npm."""

    def __init__(self, config: Optional[ConfigManager] = None):
        self.config = config or ConfigManager()
        self.adapters: Dict[str, BaseSourceAdapter] = {}
        self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        """Initializes default source adapters."""
        winget = WingetAdapter()
        store = StoreAdapter()
        vendor = VendorAdapter(self.config)
        pip = PipAdapter()
        npm = NpmAdapter()
        scoop = ScoopAdapter()
        choco = ChocolateyAdapter()

        self.register_adapter(winget)
        self.register_adapter(store)
        self.register_adapter(vendor)
        self.register_adapter(pip)
        self.register_adapter(npm)
        self.register_adapter(scoop)
        self.register_adapter(choco)

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

    def get_available_adapters(self) -> List[BaseSourceAdapter]:
        """Returns list of all active and available adapters."""
        return [
            a for a in self.adapters.values()
            if a.enabled and a.is_available()
        ]

    def set_adapter_enabled(self, name: str, enabled: bool) -> None:
        if name in self.adapters:
            self.adapters[name].enabled = enabled
            logger.info(f"Adapter '{name}' enabled status set to: {enabled}")

    def scan_all_installed(self) -> List[ProgramItem]:
        """Queries all available secondary package managers (pip, npm, scoop, choco) for installed software."""
        secondary_items: List[ProgramItem] = []
        for name in ("pip", "npm", "scoop", "chocolatey"):
            adapter = self.get_adapter(name)
            if adapter and adapter.enabled and adapter.is_available():
                try:
                    pkgs = adapter.get_installed_packages()
                    secondary_items.extend(pkgs)
                    logger.debug(f"Adapter '{name}' discovered {len(pkgs)} installed packages.")
                except Exception as e:
                    logger.error(f"Error querying packages from adapter '{name}': {e}")
        return secondary_items

    def install_package(self, source: str, pkg_id: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Installs a package via the specified source adapter."""
        adapter = self.get_adapter(source.lower())
        if not adapter:
            return False, f"Unknown source manager '{source}'"
        if not adapter.is_available():
            return False, f"Package manager '{adapter.display_name}' is not installed or available on this PC."
        return adapter.install_package(pkg_id, dry_run=dry_run)

    def install_update(
        self,
        item: ProgramItem,
        dry_run: bool = False,
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """Updates an existing package using its designated source adapter."""
        source = (item.source or "").lower()
        adapter = self.get_adapter(source)
        if adapter and adapter.is_available():
            try:
                return adapter.install_update(item, dry_run=dry_run, log_callback=log_callback)
            except TypeError:
                return adapter.install_update(item, dry_run=dry_run)

        # Fallback to winget for standard Win32/Store items
        winget = self.get_adapter("winget")
        if winget:
            try:
                return winget.install_update(item, dry_run=dry_run, log_callback=log_callback)
            except TypeError:
                return winget.install_update(item, dry_run=dry_run)
        return False, f"No viable adapter available for updating '{item.name}'"

    def uninstall_package(self, item: ProgramItem) -> Tuple[bool, str]:
        """Uninstalls a package via its designated source adapter."""
        source = (item.source or "").lower()
        adapter = self.get_adapter(source)
        pkg_id = item.id or item.name

        if adapter and adapter.is_available():
            return adapter.uninstall_package(pkg_id)

        # Fallback to winget
        winget = self.get_adapter("winget")
        if winget:
            return winget.uninstall_package(pkg_id)
        return False, f"No viable adapter available for uninstalling '{item.name}'"

    def search_all(self, query: str, target_sources: Optional[List[str]] = None) -> List[ProgramItem]:
        """Discovers and searches packages across selected or all available adapters."""
        clean_q = query.strip()
        if not clean_q:
            return []

        results: List[ProgramItem] = []
        sources = target_sources or self.get_available_sources()

        for src_name in sources:
            adapter = self.get_adapter(src_name)
            if adapter and adapter.enabled and adapter.is_available():
                try:
                    matches = adapter.search_packages(clean_q)
                    results.extend(matches)
                except Exception as e:
                    logger.error(f"Error searching in adapter '{src_name}': {e}")

        return results

    def query_all_updates(self, installed_items: Optional[List[ProgramItem]] = None) -> Dict[str, Dict[str, Dict[str, str]]]:
        """Queries pending updates across secondary package managers (pip, npm, scoop, chocolatey)."""
        results: Dict[str, Dict[str, Dict[str, str]]] = {}
        target_adapters = ["pip", "npm", "scoop", "chocolatey"]
        for src in target_adapters:
            adapter = self.get_adapter(src)
            if adapter and adapter.enabled and adapter.is_available():
                try:
                    upd = adapter.query_updates(installed_items)
                    if upd:
                        results[src] = upd
                except Exception as e:
                    logger.error(f"Error querying updates for adapter '{src}': {e}")
        return results

