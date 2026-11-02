"""Careful matching of discovered software to winget packages and vendor fallbacks."""

import re
from typing import Dict, List, Optional, Tuple
from winget_updater.config import ConfigManager
from winget_updater.models import PackageType, ProgramItem, UpdateAction, UpdateOutcome
from winget_updater.utils.logger import get_logger
from winget_updater.winget.client import WingetPackageEntry
from winget_updater.winget.version_comparator import compare_versions

logger = get_logger()


def normalize_app_name(name: str) -> str:
    """Normalizes an application name by stripping architecture and common noise."""
    if not name:
        return ""
    n = name.lower()
    # Remove architecture annotations
    n = re.sub(r"\b(x86|x64|arm64|32-bit|64-bit)\b", "", n, flags=re.IGNORECASE)
    # Remove common brackets and release notes
    n = re.sub(r"\(.*?\)", "", n)
    n = re.sub(r"\[.*?\]", "", n)
    # Remove multiple spaces
    n = re.sub(r"\s+", " ", n).strip()
    return n


class PackageMatcher:
    """Matches discovered programs to winget packages or vendor fallback sources."""

    def __init__(self, config: ConfigManager):
        self.config = config

    def match_all(
        self,
        programs: List[ProgramItem],
        upgrades: Dict[str, WingetPackageEntry],
        installed: Dict[str, WingetPackageEntry],
    ) -> List[ProgramItem]:
        """Matches all discovered programs against winget repositories and vendor fallback entries."""
        logger.info("Correlating discovered inventory against winget package registry and fallback lists...")
        
        # Build normalized lookup index from winget entries
        name_to_upgrade: Dict[str, List[WingetPackageEntry]] = {}
        for entry in upgrades.values():
            norm = normalize_app_name(entry.name)
            name_to_upgrade.setdefault(norm, []).append(entry)

        name_to_installed: Dict[str, List[WingetPackageEntry]] = {}
        for entry in installed.values():
            norm = normalize_app_name(entry.name)
            name_to_installed.setdefault(norm, []).append(entry)

        for item in programs:
            self._match_single(item, upgrades, installed, name_to_upgrade, name_to_installed)

        logger.info("Matching complete.")
        return programs

    def _match_single(
        self,
        item: ProgramItem,
        upgrades_by_id: Dict[str, WingetPackageEntry],
        installed_by_id: Dict[str, WingetPackageEntry],
        name_to_upgrade: Dict[str, List[WingetPackageEntry]],
        name_to_installed: Dict[str, List[WingetPackageEntry]],
    ) -> None:
        # 1. Check user exclusion rule
        exclusion_reason = self.config.is_excluded(item.name, item.id)
        if exclusion_reason:
            item.action = UpdateAction.EXCLUDED
            item.outcome = UpdateOutcome.SKIPPED
            item.notes = f"Excluded: {exclusion_reason}"
            return

        # 2. Check if item type is strictly listed only (drivers and extensions)
        if item.package_type in (PackageType.BROWSER_EXTENSION, PackageType.DRIVER):
            item.action = UpdateAction.LIST_ONLY
            item.outcome = UpdateOutcome.LISTED_ONLY
            return

        norm_name = normalize_app_name(item.name)
        norm_id = (item.id or "").strip().lower()

        # 3. Direct ID match in pending upgrades
        matched_upgrade = upgrades_by_id.get(norm_id) if norm_id else None
        if not matched_upgrade and norm_name in name_to_upgrade:
            candidates = name_to_upgrade[norm_name]
            if len(candidates) == 1:
                matched_upgrade = candidates[0]
            else:
                logger.warning(f"Multiple winget upgrade candidates for '{item.name}'. Ambiguous match marked for review.")
                item.action = UpdateAction.UNVERIFIED
                item.outcome = UpdateOutcome.AWAITING_CONFIRMATION
                item.is_ambiguous = True
                item.notes = f"Ambiguous match ({len(candidates)} packages match). Marked for review."
                return

        if matched_upgrade:
            if item.publisher and getattr(matched_upgrade, "publisher", None):
                if item.publisher.strip().lower() not in matched_upgrade.publisher.strip().lower():
                    item.action = UpdateAction.UNVERIFIED
                    item.outcome = UpdateOutcome.AWAITING_CONFIRMATION
                    item.is_ambiguous = True
                    item.notes = f"Publisher mismatch ({item.publisher} vs {matched_upgrade.publisher}). Marked for review."
                    return
            self._apply_winget_upgrade_match(item, matched_upgrade)
            return

        # 4. Match in general winget installed list
        matched_installed = installed_by_id.get(norm_id) if norm_id else None
        if not matched_installed and norm_name in name_to_installed:
            candidates = name_to_installed[norm_name]
            if len(candidates) == 1:
                matched_installed = candidates[0]
            else:
                logger.warning(f"Multiple winget installed candidates for '{item.name}'. Ambiguous match marked for review.")
                item.action = UpdateAction.UNVERIFIED
                item.outcome = UpdateOutcome.AWAITING_CONFIRMATION
                item.is_ambiguous = True
                item.notes = f"Ambiguous match ({len(candidates)} packages match). Marked for review."
                return

        if matched_installed:
            self._apply_winget_installed_match(item, matched_installed)
            return

        # 5. Check user-maintained fallback vendor source list
        vendor_entry = self.config.match_vendor_source(item.name, item.id)
        if vendor_entry:
            item.action = UpdateAction.VENDOR_FALLBACK
            item.outcome = UpdateOutcome.AWAITING_CONFIRMATION
            item.source = "vendor_list"
            item.latest_version = vendor_entry.version
            item.vendor_installer_url = vendor_entry.installer_url
            item.vendor_installer_hash = vendor_entry.expected_sha256
            item.notes = f"Fallback vendor source '{vendor_entry.name}' available. Requires separate confirmation."
            return

        # 6. No match found -> report "no update source found" rather than silently skipping
        item.action = UpdateAction.NO_SOURCE
        item.outcome = UpdateOutcome.LISTED_ONLY
        item.notes = "No update source found"

    def _apply_winget_upgrade_match(self, item: ProgramItem, entry: WingetPackageEntry) -> None:
        """Applies matched pending upgrade and verifies version order."""
        item.id = entry.id
        item.source = entry.source
        item.latest_version = entry.available_version or entry.version
        is_verified = (entry.source or "").lower() in ("winget", "msstore")
        item.is_verified_winget = is_verified

        # Downgrade check
        comp = compare_versions(item.installed_version, item.latest_version)
        if comp is not None and comp > 0:
            # Installed is NEWER than source!
            item.action = UpdateAction.NEWER_THAN_SOURCE
            item.outcome = UpdateOutcome.AWAITING_CONFIRMATION
            item.notes = (
                f"Installed version ({item.installed_version}) is newer than "
                f"source version ({item.latest_version}). Downgrade blocked; per-app confirmation required."
            )
            return

        if not is_verified:
            item.action = UpdateAction.UNVERIFIED
            item.outcome = UpdateOutcome.AWAITING_CONFIRMATION
            item.notes = f"Unverified source '{entry.source}'. Marked for review."
            return

        item.action = UpdateAction.AVAILABLE
        item.outcome = UpdateOutcome.PENDING
        item.notes = f"Verified update available from {entry.source}"

    def _apply_winget_installed_match(self, item: ProgramItem, entry: WingetPackageEntry) -> None:
        """Applies matched installed package that is not currently marked for upgrade."""
        item.id = entry.id
        item.source = entry.source
        is_verified = (entry.source or "").lower() in ("winget", "msstore")
        item.is_verified_winget = is_verified

        if entry.available_version:
            # Winget reports an available version
            item.latest_version = entry.available_version
            comp = compare_versions(item.installed_version, entry.available_version)
            if comp is not None and comp > 0:
                item.action = UpdateAction.NEWER_THAN_SOURCE
                item.outcome = UpdateOutcome.AWAITING_CONFIRMATION
                item.notes = "Installed version is newer than source listing (downgrade warning)."
                return
            elif comp is not None and comp < 0:
                item.action = UpdateAction.AVAILABLE
                item.outcome = UpdateOutcome.PENDING
                item.notes = f"Update available from {entry.source}"
                return

        # Up to date
        item.action = UpdateAction.UP_TO_DATE
        item.latest_version = item.installed_version
        item.outcome = UpdateOutcome.LISTED_ONLY
        item.notes = f"Program is up to date (Source: {entry.source or 'winget'})"

