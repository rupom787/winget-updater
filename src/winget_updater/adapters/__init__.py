"""Source adapters package."""

from winget_updater.adapters.base import BaseSourceAdapter
from winget_updater.adapters.chocolatey_adapter import ChocolateyAdapter
from winget_updater.adapters.manager import SourceManager
from winget_updater.adapters.npm_adapter import NpmAdapter
from winget_updater.adapters.pip_adapter import PipAdapter
from winget_updater.adapters.scoop_adapter import ScoopAdapter
from winget_updater.adapters.store_adapter import StoreAdapter
from winget_updater.adapters.vendor_adapter import VendorAdapter
from winget_updater.adapters.winget_adapter import WingetAdapter

__all__ = [
    "BaseSourceAdapter",
    "WingetAdapter",
    "StoreAdapter",
    "VendorAdapter",
    "PipAdapter",
    "NpmAdapter",
    "ScoopAdapter",
    "ChocolateyAdapter",
    "SourceManager",
]

