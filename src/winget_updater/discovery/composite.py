"""Unified software discovery orchestrator combining registry, store, portable, extension, and driver scanners."""

import concurrent.futures
from typing import Callable, List, Optional
from winget_updater.discovery.driver_scanner import DriverScanner
from winget_updater.discovery.extension_scanner import BrowserExtensionScanner
from winget_updater.discovery.portable_scanner import PortableScanner
from winget_updater.discovery.registry_scanner import RegistryScanner
from winget_updater.discovery.store_scanner import StoreScanner
from winget_updater.models import PackageType, ProgramItem
from winget_updater.utils.logger import get_logger

logger = get_logger()


class CompositeScanner:
    """Coordinates all discovery scanners and produces a deduplicated inventory."""

    def __init__(self, portable_directories: Optional[List[str]] = None):
        self.registry_scanner = RegistryScanner()
        self.store_scanner = StoreScanner()
        self.portable_scanner = PortableScanner(target_directories=portable_directories)
        self.extension_scanner = BrowserExtensionScanner()
        self.driver_scanner = DriverScanner()

    def scan_all(self, progress_callback: Optional[Callable[[str, int], None]] = None) -> List[ProgramItem]:
        """Runs all scanners concurrently and returns the full aggregated list."""
        all_items: List[ProgramItem] = []
        scanners = [
            ("Registry (Win32)", self.registry_scanner.scan),
            ("Store / MSIX", self.store_scanner.scan),
            ("Portable Apps", self.portable_scanner.scan),
            ("Browser Extensions", self.extension_scanner.scan),
            ("Device Drivers", self.driver_scanner.scan),
        ]

        logger.info("Starting comprehensive software inventory discovery across all subsystems...")
        completed_count = 0
        total_scanners = len(scanners)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_name = {executor.submit(scan_fn): name for name, scan_fn in scanners}
            for future in concurrent.futures.as_completed(future_to_name):
                name = future_to_name[future]
                completed_count += 1
                try:
                    res = future.result()
                    all_items.extend(res)
                    logger.debug(f"Scanner '{name}' completed with {len(res)} items.")
                except Exception as e:
                    logger.error(f"Scanner '{name}' failed: {e}")

                if progress_callback:
                    pct = int((completed_count / total_scanners) * 100)
                    progress_callback(f"Scanned {name} ({completed_count}/{total_scanners})", pct)

        deduped = self._deduplicate(all_items)
        logger.info(f"Inventory discovery finished. Total unique items discovered: {len(deduped)}")
        return deduped

    def _deduplicate(self, items: List[ProgramItem]) -> List[ProgramItem]:
        """Deduplicates items with matching names and package identities."""
        result: List[ProgramItem] = []
        seen_keys = set()

        for item in items:
            # Construct a canonical key
            norm_name = item.name.strip().lower()
            norm_id = (item.id or "").strip().lower()
            pkg_type = item.package_type.value

            # Primary key
            key = (norm_name, norm_id, pkg_type)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            result.append(item)

        return result

