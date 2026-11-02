"""Winget module exports."""

from winget_updater.winget.client import WingetClient, WingetPackageDetails, WingetPackageEntry
from winget_updater.winget.matcher import PackageMatcher
from winget_updater.winget.verifier import PackageVerifier
from winget_updater.winget.version_comparator import compare_versions

__all__ = [
    "WingetClient",
    "WingetPackageEntry",
    "WingetPackageDetails",
    "PackageMatcher",
    "PackageVerifier",
    "compare_versions",
]

