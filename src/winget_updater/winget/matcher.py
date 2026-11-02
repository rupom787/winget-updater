"""Careful matching of discovered software to winget packages and vendor fallbacks.
Includes intelligent publisher matching, curated package aliases, and custom bindings.
"""

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


def normalize_publisher(pub: Optional[str]) -> str:
    """Normalizes publisher string by stripping legal corporate suffixes and punctuation."""
    if not pub:
        return ""
    p = pub.lower()
    p = re.sub(
        r"\b(llc|inc|incorporated|corp|corporation|ltd|limited|gmbh|co\.|co|software|foundation|technologies|team|holdings)\b",
        "",
        p,
        flags=re.IGNORECASE,
    )
    p = re.sub(r"[^\w\s]", "", p)
    return re.sub(r"\s+", " ", p).strip()


def publishers_match(pub1: Optional[str], pub2: Optional[str]) -> bool:
    """Checks if two publisher strings are compatible with high confidence."""
    if not pub1 or not pub2:
        return True  # Missing publisher is not considered a mismatch
    norm1 = normalize_publisher(pub1)
    norm2 = normalize_publisher(pub2)
    if not norm1 or not norm2:
        return True
    if norm1 == norm2 or norm1 in norm2 or norm2 in norm1:
        return True
    # Word token intersection (e.g., "Oracle America" & "Oracle")
    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())
    if tokens1 & tokens2:
        return True
    return False


# Curated dictionary mapping common Windows software names to official Winget package IDs
KNOWN_PACKAGE_ALIASES: Dict[str, str] = {
    "google chrome": "Google.Chrome",
    "chrome": "Google.Chrome",
    "mozilla firefox": "Mozilla.Firefox",
    "firefox": "Mozilla.Firefox",
    "visual studio code": "Microsoft.VisualStudioCode",
    "vs code": "Microsoft.VisualStudioCode",
    "vscode": "Microsoft.VisualStudioCode",
    "git": "Git.Git",
    "vlc media player": "VideoLAN.VLC",
    "vlc": "VideoLAN.VLC",
    "node.js": "OpenJS.NodeJS",
    "nodejs": "OpenJS.NodeJS",
    "7-zip": "7zip.7zip",
    "7zip": "7zip.7zip",
    "notepad++": "Notepad++.Notepad++",
    "discord": "Discord.Discord",
    "spotify": "Spotify.Spotify",
    "steam": "Valve.Steam",
    "docker desktop": "Docker.DockerDesktop",
    "obs studio": "OBSProject.OBSStudio",
    "brave": "Brave.Brave",
    "microsoft powertoys": "Microsoft.PowerToys",
    "powertoys": "Microsoft.PowerToys",
    "winrar": "RARLab.WinRAR",
    "anydesk": "AnyDeskSoftwareGmbH.AnyDesk",
    "teamviewer": "TeamViewer.TeamViewer",
    "zoom": "Zoom.Zoom",
    "zoom workplace": "Zoom.Zoom",
    "slack": "SlackTechnologies.Slack",
    "telegram desktop": "Telegram.TelegramDesktop",
    "telegram": "Telegram.TelegramDesktop",
    "whatsapp": "WhatsApp.WhatsApp",
    "postman": "Postman.Postman",
    "wireshark": "WiresharkFoundation.Wireshark",
    "audacity": "Audacity.Audacity",
    "gimp": "GIMP.GIMP",
    "blender": "BlenderFoundation.Blender",
    "handbrake": "HandBrake.HandBrake",
    "sharex": "ShareX.ShareX",
    "everything": "voidtools.Everything",
    "keepassxc": "KeePassXCTeam.KeePassXC",
    "bitwarden": "Bitwarden.Bitwarden",
    "putty": "PuTTY.PuTTY",
    "filezilla": "TimKosse.FileZilla.Client",
    "epic games launcher": "EpicGames.EpicGamesLauncher",
    "qbittorrent": "qBittorrent.qBittorrent",
    "obsidian": "Obsidian.Obsidian",
    "notion": "Notion.Notion",
    "sublime text": "SublimeHQ.SublimeText.4",
    "android studio": "Google.AndroidStudio",
    "libreoffice": "TheDocumentFoundation.LibreOffice",
    "thunderbird": "Mozilla.Thunderbird",
    "wireguard": "WireGuard.WireGuard",
    "tailscale": "Tailscale.Tailscale",
    "proton vpn": "Proton.ProtonVPN",
    "nordvpn": "NordSecurity.NordVPN",
}


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
            item.unavailability_reason = f"Excluded by user rule: {exclusion_reason}"
            return

        # 2. Check if item type is strictly listed only (drivers and extensions)
        if item.package_type == PackageType.DRIVER:
            item.action = UpdateAction.LIST_ONLY
            item.outcome = UpdateOutcome.LISTED_ONLY
            item.notes = "Device drivers are OEM-signed and maintained safely via Windows Update."
            item.unavailability_reason = "OEM Device Driver: Maintained via Windows Update or vendor firmware."
            return

        if item.package_type == PackageType.BROWSER_EXTENSION:
            item.action = UpdateAction.LIST_ONLY
            item.outcome = UpdateOutcome.LISTED_ONLY
            item.notes = "Browser extensions are updated automatically through the browser web store."
            item.unavailability_reason = "Browser Extension: Handled automatically by your web browser store."
            return

        norm_name = normalize_app_name(item.name)
        norm_id = (item.id or "").strip().lower()

        # 3. Check custom user binding from custom_mappings.json
        custom_bound_id = self.config.get_custom_mapping(item.name, item.id)
        if custom_bound_id:
            bound_norm = custom_bound_id.strip().lower()
            item.id = custom_bound_id
            item.is_user_bound = True
            item.is_verified_winget = True
            # Check if this bound ID is in pending upgrades
            if bound_norm in upgrades_by_id:
                self._apply_winget_upgrade_match(item, upgrades_by_id[bound_norm])
                item.notes += " (Bound to verified Winget ID)"
                return
            if bound_norm in installed_by_id:
                self._apply_winget_installed_match(item, installed_by_id[bound_norm])
                item.notes += " (Bound to verified Winget ID)"
                return

        # 4. Check known curated aliases
        alias_id = KNOWN_PACKAGE_ALIASES.get(norm_name)
        if alias_id:
            alias_norm = alias_id.strip().lower()
            if alias_norm in upgrades_by_id:
                self._apply_winget_upgrade_match(item, upgrades_by_id[alias_norm])
                return
            if alias_norm in installed_by_id:
                self._apply_winget_installed_match(item, installed_by_id[alias_norm])
                return

        # 5. Direct ID match in pending upgrades
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
                item.unavailability_reason = (
                    f"Ambiguous candidates ({', '.join(c.id for c in candidates[:3])}). "
                    "Use 'Bind Winget ID' in drawer to select the correct package."
                )
                return

        if matched_upgrade:
            if item.publisher and getattr(matched_upgrade, "publisher", None):
                if not publishers_match(item.publisher, matched_upgrade.publisher):
                    item.action = UpdateAction.UNVERIFIED
                    item.outcome = UpdateOutcome.AWAITING_CONFIRMATION
                    item.is_ambiguous = True
                    item.notes = f"Publisher mismatch ({item.publisher} vs {matched_upgrade.publisher}). Marked for review."
                    item.unavailability_reason = (
                        f"Publisher mismatch: Installed '{item.publisher}' vs Winget '{matched_upgrade.publisher}'. "
                        "Click 'Review & Allow Update' to confirm."
                    )
                    return
            self._apply_winget_upgrade_match(item, matched_upgrade)
            return

        # 6. Match in general winget installed list
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
                item.unavailability_reason = (
                    f"Multiple candidate packages match name. Use 'Bind Winget ID' to link."
                )
                return

        if matched_installed:
            self._apply_winget_installed_match(item, matched_installed)
            return

        # 7. Check user-maintained fallback vendor source list
        vendor_entry = self.config.match_vendor_source(item.name, item.id)
        if vendor_entry:
            item.action = UpdateAction.VENDOR_FALLBACK
            item.outcome = UpdateOutcome.AWAITING_CONFIRMATION
            item.source = "vendor_list"
            item.latest_version = vendor_entry.version
            item.vendor_installer_url = vendor_entry.installer_url
            item.vendor_installer_hash = vendor_entry.expected_sha256
            item.notes = f"Fallback vendor source '{vendor_entry.name}' available. Requires separate confirmation."
            item.unavailability_reason = "Vendor installer source available. Requires signature confirmation before update."
            return

        # 8. No match found -> report "no update source found" rather than silently skipping
        item.action = UpdateAction.NO_SOURCE
        item.outcome = UpdateOutcome.LISTED_ONLY
        item.notes = "No update source found"
        item.unavailability_reason = (
            "No public package manifest found in Winget or Microsoft Store. "
            "Use 'Bind Winget ID' to search repository or 'Visit Website' to download update manually."
        )

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
            item.unavailability_reason = (
                f"Installed version ({item.installed_version}) is newer than source ({item.latest_version}). "
                "Downgrade protection active. Click 'Force Allow' to overwrite if desired."
            )
            return

        if not is_verified:
            item.action = UpdateAction.UNVERIFIED
            item.outcome = UpdateOutcome.AWAITING_CONFIRMATION
            item.notes = f"Unverified source '{entry.source}'. Marked for review."
            item.unavailability_reason = f"Unverified source '{entry.source}'. Marked for manual review."
            return

        item.action = UpdateAction.AVAILABLE
        item.outcome = UpdateOutcome.PENDING
        item.notes = f"Verified update available from {entry.source}"
        item.unavailability_reason = None

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
                item.unavailability_reason = "Installed version is newer than source listing (downgrade warning)."
                return
            elif comp is not None and comp < 0:
                item.action = UpdateAction.AVAILABLE
                item.outcome = UpdateOutcome.PENDING
                item.notes = f"Update available from {entry.source}"
                item.unavailability_reason = None
                return

        # Up to date
        item.action = UpdateAction.UP_TO_DATE
        item.latest_version = item.installed_version
        item.outcome = UpdateOutcome.LISTED_ONLY
        item.notes = f"Program is up to date (Source: {entry.source or 'winget'})"
        item.unavailability_reason = None
