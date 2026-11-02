"""Discovery package exports."""

from winget_updater.discovery.composite import CompositeScanner
from winget_updater.discovery.driver_scanner import DriverScanner
from winget_updater.discovery.extension_scanner import BrowserExtensionScanner
from winget_updater.discovery.portable_scanner import PortableScanner
from winget_updater.discovery.registry_scanner import RegistryScanner
from winget_updater.discovery.store_scanner import StoreScanner

__all__ = [
    "CompositeScanner",
    "RegistryScanner",
    "StoreScanner",
    "PortableScanner",
    "BrowserExtensionScanner",
    "DriverScanner",
]

