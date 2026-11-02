"""Configuration management for exclusions and user-maintained vendor source lists."""

import fnmatch
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from winget_updater.utils.logger import get_logger

logger = get_logger()

DEFAULT_EXCLUSIONS_FILE = "exclusions.json"
DEFAULT_SOURCES_FILE = "sources.json"
DEFAULT_CONFIG_FILE = "config.json"
DEFAULT_MAPPINGS_FILE = "custom_mappings.json"


@dataclass
class VendorSourceEntry:
    """Entry in the user-maintained fallback installer list."""
    name: str
    match_name: str
    installer_url: str
    version: Optional[str] = None
    expected_sha256: Optional[str] = None
    expected_publisher: Optional[str] = None
    target_arch: Optional[str] = None  # e.g. "x64", "arm64", "x86"
    notes: Optional[str] = None


@dataclass
class ExclusionRule:
    """Exclusion pattern or ID with optional reason."""
    pattern: str
    reason: str = "Excluded by user"


class ConfigManager:
    """Manages exclusions.json, sources.json, and general settings."""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        exclusions_path: Optional[Path] = None,
        sources_path: Optional[Path] = None,
    ):
        if base_dir is not None:
            self.base_dir = base_dir
        elif hasattr(sys, "frozen"):
            self.base_dir = Path(sys.executable).resolve().parent
        else:
            self.base_dir = Path.cwd()

        self.exclusions_path = exclusions_path or (self.base_dir / DEFAULT_EXCLUSIONS_FILE)
        self.sources_path = sources_path or (self.base_dir / DEFAULT_SOURCES_FILE)
        self.config_path = self.base_dir / DEFAULT_CONFIG_FILE
        self.mappings_path = self.base_dir / DEFAULT_MAPPINGS_FILE
        
        self.theme: str = "light"
        self.exclusions: List[ExclusionRule] = []
        self.vendor_sources: List[VendorSourceEntry] = []
        self.custom_mappings: Dict[str, str] = {}
        self.portable_directories: List[str] = self._get_default_portable_dirs()
        
        self.load_all()

    def _get_default_portable_dirs(self) -> List[str]:
        """Provides default directories where portable applications commonly live."""
        dirs = []
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            dirs.append(str(Path(local_app_data) / "Programs"))
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            dirs.append(str(Path(user_profile) / "PortableApps"))
            dirs.append(str(Path(user_profile) / "Tools"))
        # Check standard drive roots
        for drive in ("C:\\", "D:\\"):
            p_dir = Path(drive) / "PortableApps"
            if p_dir.exists():
                dirs.append(str(p_dir))
        return [d for d in dirs if os.path.exists(d)]

    def load_all(self) -> None:
        """Loads configuration settings, exclusions, vendor sources, and custom mappings from disk."""
        self.load_settings()
        self.load_exclusions()
        self.load_vendor_sources()
        self.load_custom_mappings()

    def load_custom_mappings(self) -> Dict[str, str]:
        """Loads user-bound program-to-winget package ID mappings."""
        self.custom_mappings = {}
        if self.mappings_path.exists():
            try:
                with open(self.mappings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.custom_mappings = {k.lower(): str(v).strip() for k, v in data.items()}
                logger.info(f"Loaded {len(self.custom_mappings)} custom package mappings from {self.mappings_path.name}")
            except Exception as e:
                logger.error(f"Error reading custom mappings file {self.mappings_path}: {e}")
        return self.custom_mappings

    def save_custom_mappings(self) -> None:
        """Persists custom package mappings to custom_mappings.json."""
        try:
            with open(self.mappings_path, "w", encoding="utf-8") as f:
                json.dump(self.custom_mappings, f, indent=2)
            logger.info(f"Saved {len(self.custom_mappings)} custom package mappings to {self.mappings_path.name}")
        except Exception as e:
            logger.error(f"Error saving custom mappings file {self.mappings_path}: {e}")

    def bind_custom_mapping(self, app_key: str, winget_id: str) -> None:
        """Binds a discovered program name or identifier directly to a verified Winget package ID."""
        if not app_key or not winget_id:
            return
        self.custom_mappings[app_key.strip().lower()] = winget_id.strip()
        self.save_custom_mappings()

    def get_custom_mapping(self, app_name: str, app_id: Optional[str] = None) -> Optional[str]:
        """Retrieves manually bound Winget package ID for an application if one exists."""
        if app_id and app_id.strip().lower() in self.custom_mappings:
            return self.custom_mappings[app_id.strip().lower()]
        if app_name and app_name.strip().lower() in self.custom_mappings:
            return self.custom_mappings[app_name.strip().lower()]
        return None

    def remove_custom_mapping(self, app_key: str) -> bool:
        """Removes a custom package mapping by app name or identifier."""
        key = app_key.strip().lower()
        if key in self.custom_mappings:
            del self.custom_mappings[key]
            self.save_custom_mappings()
            return True
        return False

    def load_settings(self) -> None:
        """Loads persistent user configuration preferences like theme."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.theme = data.get("theme", "light")
            except Exception as e:
                logger.error(f"Error loading {self.config_path.name}: {e}")

    def set_theme(self, theme: str) -> None:
        """Persists the user theme preference ('dark' or 'light') to config.json."""
        self.theme = theme.lower()
        try:
            data = {}
            if self.config_path.exists():
                try:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data["theme"] = self.theme
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Theme preference saved: {self.theme}")
        except Exception as e:
            logger.error(f"Error saving theme to {self.config_path.name}: {e}")

    def load_exclusions(self) -> List[ExclusionRule]:
        """Loads human-readable exclusions from exclusions.json."""
        self.exclusions = []
        if not self.exclusions_path.exists():
            self._save_default_exclusions()
            return self.exclusions

        try:
            with open(self.exclusions_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Accept both list of strings or list of dicts/patterns
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, str):
                        self.exclusions.append(ExclusionRule(pattern=item.strip()))
                    elif isinstance(item, dict) and "pattern" in item:
                        self.exclusions.append(
                            ExclusionRule(
                                pattern=item["pattern"].strip(),
                                reason=item.get("reason", "Excluded by user")
                            )
                        )
            elif isinstance(data, dict):
                # { "excluded_patterns": [...], "reasons": {...} }
                patterns = data.get("excluded_patterns", [])
                reasons = data.get("reasons", {})
                for pat in patterns:
                    reason = reasons.get(pat, "Excluded by user")
                    self.exclusions.append(ExclusionRule(pattern=pat.strip(), reason=reason))

            logger.info(f"Loaded {len(self.exclusions)} exclusion rules from {self.exclusions_path.name}")
        except Exception as e:
            logger.error(f"Error parsing {self.exclusions_path}: {e}")
        return self.exclusions

    def save_exclusions(self) -> None:
        """Saves current exclusion rules to exclusions.json in clean human-readable JSON."""
        try:
            data = [
                {"pattern": rule.pattern, "reason": rule.reason}
                for rule in self.exclusions
            ]
            with open(self.exclusions_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.exclusions)} exclusions to {self.exclusions_path}")
        except Exception as e:
            logger.error(f"Failed to save exclusions to {self.exclusions_path}: {e}")
            raise

    def add_exclusion(self, pattern: str, reason: str = "Excluded via GUI") -> None:
        """Adds a new exclusion pattern and saves to file."""
        clean_pat = pattern.strip()
        if not clean_pat:
            return
        # Avoid duplicate
        for rule in self.exclusions:
            if rule.pattern.lower() == clean_pat.lower():
                rule.reason = reason
                self.save_exclusions()
                return
        self.exclusions.append(ExclusionRule(pattern=clean_pat, reason=reason))
        self.save_exclusions()

    def remove_exclusion(self, pattern: str) -> bool:
        """Removes an exclusion rule by pattern and saves to file."""
        initial_len = len(self.exclusions)
        self.exclusions = [r for r in self.exclusions if r.pattern.lower() != pattern.strip().lower()]
        if len(self.exclusions) < initial_len:
            self.save_exclusions()
            return True
        return False

    def is_excluded(self, program_name: str, package_id: Optional[str] = None) -> Optional[str]:
        """Checks if a program is excluded. Returns reason if excluded, or None."""
        name_lower = (program_name or "").lower()
        id_lower = (package_id or "").lower()

        for rule in self.exclusions:
            pat_lower = rule.pattern.lower()
            # Direct match or wildcard match on name or ID
            if fnmatch.fnmatch(name_lower, pat_lower):
                return rule.reason
            if id_lower and fnmatch.fnmatch(id_lower, pat_lower):
                return rule.reason
        return None

    def load_vendor_sources(self) -> List[VendorSourceEntry]:
        """Loads optional vendor installer fallback sources from sources.json."""
        self.vendor_sources = []
        if not self.sources_path.exists():
            self._save_default_sources()
            return self.vendor_sources

        try:
            with open(self.sources_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            entries = data.get("sources", []) if isinstance(data, dict) else data
            for item in entries:
                if isinstance(item, dict) and "installer_url" in item:
                    self.vendor_sources.append(
                        VendorSourceEntry(
                            name=item.get("name", ""),
                            match_name=item.get("match_name", item.get("name", "")),
                            installer_url=item["installer_url"],
                            version=item.get("version"),
                            expected_sha256=item.get("expected_sha256"),
                            expected_publisher=item.get("expected_publisher"),
                            target_arch=item.get("target_arch"),
                            notes=item.get("notes"),
                        )
                    )
            logger.info(f"Loaded {len(self.vendor_sources)} vendor fallback sources from {self.sources_path.name}")
        except Exception as e:
            logger.error(f"Error reading vendor sources file {self.sources_path}: {e}")
        return self.vendor_sources

    def match_vendor_source(self, program_name: str, package_id: Optional[str] = None) -> Optional[VendorSourceEntry]:
        """Finds matching fallback vendor source entry if one exists."""
        name_lower = (program_name or "").lower()
        id_lower = (package_id or "").lower()

        for entry in self.vendor_sources:
            match_pat = entry.match_name.lower()
            if fnmatch.fnmatch(name_lower, match_pat) or (id_lower and fnmatch.fnmatch(id_lower, match_pat)):
                return entry
            if entry.name and fnmatch.fnmatch(name_lower, entry.name.lower()):
                return entry
        return None

    def _save_default_exclusions(self) -> None:
        """Initializes default empty exclusions.json with helpful comments/examples."""
        template = [
            {
                "pattern": "ExampleAppToExclude*",
                "reason": "Example exclusion pattern (wildcards supported)"
            }
        ]
        try:
            with open(self.exclusions_path, "w", encoding="utf-8") as f:
                json.dump(template, f, indent=2)
            logger.info(f"Created default exclusions file at {self.exclusions_path}")
        except Exception as e:
            logger.warning(f"Failed to create default exclusions file: {e}")

    def _save_default_sources(self) -> None:
        """Initializes default empty sources.json with template for manual editing."""
        template = {
            "sources": [
                {
                    "name": "Example Vendor Tool",
                    "match_name": "ExampleTool*",
                    "installer_url": "https://example.com/downloads/tool_setup.exe",
                    "version": "2.0.0",
                    "expected_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                    "expected_publisher": "Example Corp",
                    "target_arch": "x64",
                    "notes": "Manual fallback when winget has no package"
                }
            ]
        }
        try:
            with open(self.sources_path, "w", encoding="utf-8") as f:
                json.dump(template, f, indent=2)
            logger.info(f"Created default vendor sources file at {self.sources_path}")
        except Exception as e:
            logger.warning(f"Failed to create default vendor sources file: {e}")

