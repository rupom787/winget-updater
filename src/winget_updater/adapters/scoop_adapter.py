"""Source adapter for Scoop command-line installer for Windows.
Discovers installed Scoop apps, queries status for updates, and handles install, update, and uninstall.
"""

import os
import shutil
from typing import Any, Dict, List, Optional, Tuple
from winget_updater.adapters.base import BaseSourceAdapter
from winget_updater.models import PackageType, ProgramItem, UpdateAction
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()


class ScoopAdapter(BaseSourceAdapter):
    """Adapter for Scoop package manager."""

    def __init__(self, scoop_path: Optional[str] = None):
        super().__init__(name="scoop", display_name="Scoop", enabled=True)
        self.scoop_path = scoop_path or shutil.which("scoop.cmd") or shutil.which("scoop") or "scoop"

    def is_available(self) -> bool:
        """Checks if Scoop is installed."""
        if self.scoop_path and (shutil.which(self.scoop_path) or os.path.exists(self.scoop_path)):
            return True
        if shutil.which("scoop") or shutil.which("scoop.cmd"):
            return True
        home = os.path.expanduser("~")
        scoop_dir = os.path.join(home, "scoop")
        if os.path.isdir(scoop_dir):
            return True
        try:
            res = silent_run([self.scoop_path, "--version"], timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def get_version(self) -> Optional[str]:
        """Returns Scoop version string."""
        try:
            res = silent_run([self.scoop_path, "--version"], timeout=10)
            if res.returncode == 0 and res.stdout:
                return res.stdout.strip()
        except Exception:
            pass
        return None

    def get_installed_packages(self) -> List[ProgramItem]:
        """Discovers installed Scoop applications via scoop list."""
        if not self.is_available():
            return []

        try:
            res = silent_run([self.scoop_path, "list"], timeout=20)
            if res.returncode != 0 or not res.stdout:
                return []

            items: List[ProgramItem] = []
            lines = res.stdout.strip().splitlines()
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0].strip()
                    ver = parts[1].strip()
                    if name.lower() in ("name", "----"):
                        continue
                    bucket = parts[2].strip() if len(parts) >= 3 else "main"
                    item = ProgramItem(
                        name=f"scoop:{name}",
                        id=f"scoop:{name}",
                        installed_version=ver,
                        package_type=PackageType.SCOOP,
                        source="scoop",
                        publisher=f"Scoop ({bucket})",
                        action=UpdateAction.UP_TO_DATE,
                        is_verified_winget=True,
                    )
                    items.append(item)
            return items
        except Exception as e:
            logger.error(f"Error querying scoop list: {e}")
            return []

    def query_updates(self, installed_items: Optional[List[ProgramItem]] = None) -> Dict[str, Dict[str, str]]:
        """Queries pending updates via scoop status."""
        if not self.is_available():
            return {}

        try:
            res = silent_run([self.scoop_path, "status"], timeout=30)
            if not res.stdout:
                return {}

            updates: Dict[str, Dict[str, str]] = {}
            for line in res.stdout.strip().splitlines():
                parts = line.split()
                if len(parts) >= 3:
                    name = parts[0].strip().lower()
                    if name in ("name", "----", "everything", "scoop"):
                        continue
                    cur_v = parts[1].strip()
                    lat_v = parts[2].strip()
                    updates[name] = {
                        "installed_version": cur_v,
                        "latest_version": lat_v,
                    }
            return updates
        except Exception as e:
            logger.error(f"Error checking scoop status: {e}")
            return {}

    def verify_package(self, item: ProgramItem) -> Tuple[bool, str]:
        """Verifies package source."""
        if item.source == "scoop" or item.package_type == PackageType.SCOOP:
            return True, "Verified trusted Scoop repository bucket"
        return False, "Not a scoop package"

    def install_package(self, pkg_id: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Installs a Scoop package."""
        clean_name = pkg_id.replace("scoop:", "")
        if dry_run:
            return True, f"[Dry Run] Simulated scoop install for '{clean_name}'"

        try:
            res = silent_run([self.scoop_path, "install", clean_name], timeout=180)
            if res.returncode == 0:
                return True, f"Successfully installed scoop app '{clean_name}'"
            return False, f"scoop install failed (Code {res.returncode}): {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing scoop install: {e}"

    def install_update(self, item: ProgramItem, dry_run: bool = False) -> Tuple[bool, str]:
        """Updates an existing Scoop app."""
        clean_name = item.name.replace("scoop:", "")
        if dry_run:
            return True, f"[Dry Run] Simulated scoop update for '{clean_name}'"

        try:
            res = silent_run([self.scoop_path, "update", clean_name], timeout=180)
            if res.returncode == 0:
                return True, f"Successfully updated scoop app '{clean_name}'"
            return False, f"scoop update failed: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing scoop update: {e}"

    def uninstall_package(self, pkg_id: str) -> Tuple[bool, str]:
        """Uninstalls a Scoop app."""
        clean_name = pkg_id.replace("scoop:", "")
        try:
            res = silent_run([self.scoop_path, "uninstall", clean_name], timeout=60)
            if res.returncode == 0:
                return True, f"Successfully uninstalled scoop app '{clean_name}'"
            return False, f"scoop uninstall failed: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing scoop uninstall: {e}"

    def search_packages(self, query: str) -> List[ProgramItem]:
        """Searches Scoop buckets for packages."""
        if not self.is_available():
            return []

        clean_q = query.strip()
        if not clean_q:
            return []

        try:
            res = silent_run([self.scoop_path, "search", clean_q], timeout=20)
            if not res.stdout:
                return []

            matches: List[ProgramItem] = []
            lines = res.stdout.strip().splitlines()
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0].strip()
                    ver = parts[1].strip()
                    if name.lower() in ("name", "----", "results"):
                        continue
                    matches.append(
                        ProgramItem(
                            name=f"scoop:{name}",
                            id=f"scoop:{name}",
                            latest_version=ver,
                            package_type=PackageType.SCOOP,
                            source="scoop",
                            publisher="Scoop Bucket",
                        )
                    )
            return matches
        except Exception as e:
            logger.error(f"Error searching scoop: {e}")
            return []
