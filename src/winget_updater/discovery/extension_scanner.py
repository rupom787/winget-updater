"""Discovers browser extensions installed in Chrome, Edge, Brave, and Firefox."""

import json
import os
from pathlib import Path
from typing import List, Optional
from winget_updater.models import PackageType, ProgramItem
from winget_updater.utils.logger import get_logger

logger = get_logger()


def resolve_chromium_localized_name(ext_dir: Path, raw_name: str) -> str:
    """Resolves __MSG_manifest_name__ or similar localized strings from _locales."""
    if not raw_name.startswith("__MSG_") or not raw_name.endswith("__"):
        return raw_name

    msg_key = raw_name[6:-2]
    # Check locale folders
    locales_dir = ext_dir / "_locales"
    if not locales_dir.exists():
        return raw_name

    for lang in ("en", "en_US", "en_GB"):
        msg_file = locales_dir / lang / "messages.json"
        if msg_file.exists():
            try:
                with open(msg_file, "r", encoding="utf-8", errors="replace") as f:
                    data = json.load(f)
                    val = data.get(msg_key, {}).get("message")
                    if val:
                        return val
            except Exception:
                pass
    return raw_name


class BrowserExtensionScanner:
    """Discovers extensions installed across major web browsers on Windows."""

    def __init__(self):
        self.local_appdata = os.environ.get("LOCALAPPDATA", "")
        self.appdata = os.environ.get("APPDATA", "")

    def scan(self) -> List[ProgramItem]:
        discovered: List[ProgramItem] = []
        if self.local_appdata:
            self._scan_chromium_browser("Google Chrome", Path(self.local_appdata) / "Google" / "Chrome" / "User Data", discovered)
            self._scan_chromium_browser("Microsoft Edge", Path(self.local_appdata) / "Microsoft" / "Edge" / "User Data", discovered)
            self._scan_chromium_browser("Brave Browser", Path(self.local_appdata) / "BraveSoftware" / "Brave-Browser" / "User Data", discovered)

        if self.appdata:
            self._scan_firefox(Path(self.appdata) / "Mozilla" / "Firefox" / "Profiles", discovered)

        logger.info(f"Browser extension scanner found {len(discovered)} extensions.")
        return discovered

    def _scan_chromium_browser(self, browser_name: str, user_data_dir: Path, discovered: List[ProgramItem]) -> None:
        if not user_data_dir.is_dir():
            return

        try:
            # Check Default and Profile * directories
            for prof_dir in user_data_dir.iterdir():
                if not prof_dir.is_dir():
                    continue
                if prof_dir.name == "Default" or prof_dir.name.startswith("Profile "):
                    ext_base = prof_dir / "Extensions"
                    if not ext_base.is_dir():
                        continue
                    self._scan_chromium_extensions_dir(browser_name, ext_base, discovered)
        except Exception as e:
            logger.debug(f"Error scanning extensions for {browser_name}: {e}")

    def _scan_chromium_extensions_dir(self, browser_name: str, ext_base: Path, discovered: List[ProgramItem]) -> None:
        try:
            for ext_id_folder in ext_base.iterdir():
                if not ext_id_folder.is_dir():
                    continue
                # Extension folders contain version subdirectories
                for ver_folder in ext_id_folder.iterdir():
                    if not ver_folder.is_dir():
                        continue
                    manifest_file = ver_folder / "manifest.json"
                    if manifest_file.exists():
                        try:
                            with open(manifest_file, "r", encoding="utf-8", errors="replace") as f:
                                manifest = json.load(f)
                            raw_name = manifest.get("name") or ext_id_folder.name
                            name = resolve_chromium_localized_name(ver_folder, raw_name)
                            version = manifest.get("version") or ver_folder.name
                            author = manifest.get("author") or manifest.get("developer", {}).get("name")

                            discovered.append(
                                ProgramItem(
                                    name=f"{name} ({browser_name})",
                                    installed_version=version,
                                    id=f"Extension\\{browser_name}\\{ext_id_folder.name}",
                                    publisher=author or browser_name,
                                    install_location=str(ver_folder),
                                    package_type=PackageType.BROWSER_EXTENSION,
                                    notes=f"Browser extension for {browser_name} (listed only)",
                                )
                            )
                        except Exception:
                            continue
        except Exception as e:
            logger.debug(f"Error reading extension directory {ext_base}: {e}")

    def _scan_firefox(self, profiles_dir: Path, discovered: List[ProgramItem]) -> None:
        if not profiles_dir.is_dir():
            return

        try:
            for prof in profiles_dir.iterdir():
                if not prof.is_dir():
                    continue
                ext_json = prof / "extensions.json"
                if ext_json.exists():
                    try:
                        with open(ext_json, "r", encoding="utf-8", errors="replace") as f:
                            data = json.load(f)
                        addons = data.get("addons", [])
                        for addon in addons:
                            if addon.get("type") in ("extension", "webextension"):
                                name = addon.get("defaultLocale", {}).get("name") or addon.get("name")
                                version = addon.get("version") or "Unknown"
                                addon_id = addon.get("id")
                                creator = addon.get("defaultLocale", {}).get("creator")

                                if name:
                                    discovered.append(
                                        ProgramItem(
                                            name=f"{name} (Firefox)",
                                            installed_version=version,
                                            id=f"Extension\\Firefox\\{addon_id}",
                                            publisher=creator or "Mozilla Firefox Add-on",
                                            package_type=PackageType.BROWSER_EXTENSION,
                                            notes="Firefox browser extension (listed only)",
                                        )
                                    )
                    except Exception as e:
                        logger.debug(f"Failed parsing Firefox extensions.json in {prof}: {e}")
        except Exception as e:
            logger.debug(f"Error scanning Firefox profiles: {e}")

