"""Source adapter for Chocolatey package manager.
Discovers installed Chocolatey packages, queries outdated releases, and handles install, update, and uninstall.
"""

import os
import shutil
from typing import Any, Dict, List, Optional, Tuple
from winget_updater.adapters.base import BaseSourceAdapter
from winget_updater.models import PackageType, ProgramItem, UpdateAction
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()


class ChocolateyAdapter(BaseSourceAdapter):
    """Adapter for Chocolatey package manager."""

    def __init__(self, choco_path: Optional[str] = None):
        super().__init__(name="chocolatey", display_name="Chocolatey", enabled=True)
        default_choco = "C:\\ProgramData\\chocolatey\\bin\\choco.exe"
        self.choco_path = choco_path or shutil.which("choco.exe") or shutil.which("choco") or (default_choco if os.path.isfile(default_choco) else "choco")

    def is_available(self) -> bool:
        """Checks if Chocolatey is installed."""
        if self.choco_path and (shutil.which(self.choco_path) or os.path.isfile(self.choco_path)):
            return True
        if shutil.which("choco") or shutil.which("choco.exe"):
            return True
        if os.path.isfile("C:\\ProgramData\\chocolatey\\bin\\choco.exe"):
            return True
        try:
            res = silent_run([self.choco_path, "-v"], timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def get_version(self) -> Optional[str]:
        """Returns Chocolatey version string."""
        try:
            res = silent_run([self.choco_path, "-v"], timeout=10)
            if res.returncode == 0 and res.stdout:
                return res.stdout.strip()
        except Exception:
            pass
        return None

    def get_installed_packages(self) -> List[ProgramItem]:
        """Discovers installed packages via choco list --local-only --limit-output."""
        if not self.is_available():
            return []

        try:
            res = silent_run([self.choco_path, "list", "--local-only", "--limit-output"], timeout=25)
            if res.returncode != 0 or not res.stdout:
                return []

            items: List[ProgramItem] = []
            for line in res.stdout.strip().splitlines():
                parts = line.split("|")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    ver = parts[1].strip()
                    item = ProgramItem(
                        name=f"choco:{name}",
                        id=f"choco:{name}",
                        installed_version=ver,
                        package_type=PackageType.CHOCOLATEY,
                        source="chocolatey",
                        publisher="Chocolatey Community",
                        action=UpdateAction.UP_TO_DATE,
                        is_verified_winget=True,
                    )
                    items.append(item)
            return items
        except Exception as e:
            logger.error(f"Error querying chocolatey list: {e}")
            return []

    def query_updates(self, installed_items: Optional[List[ProgramItem]] = None) -> Dict[str, Dict[str, str]]:
        """Queries outdated packages via choco outdated --limit-output."""
        if not self.is_available():
            return {}

        try:
            res = silent_run([self.choco_path, "outdated", "--limit-output"], timeout=35)
            if not res.stdout:
                return {}

            updates: Dict[str, Dict[str, str]] = {}
            for line in res.stdout.strip().splitlines():
                parts = line.split("|")
                # Format: PackageName|CurrentVersion|AvailableVersion|IsPinned
                if len(parts) >= 3:
                    name = parts[0].strip().lower()
                    cur_v = parts[1].strip()
                    lat_v = parts[2].strip()
                    updates[name] = {
                        "installed_version": cur_v,
                        "latest_version": lat_v,
                    }
            return updates
        except Exception as e:
            logger.error(f"Error checking chocolatey outdated: {e}")
            return {}

    def verify_package(self, item: ProgramItem) -> Tuple[bool, str]:
        """Verifies package source."""
        if item.source == "chocolatey" or item.package_type == PackageType.CHOCOLATEY:
            return True, "Verified trusted Chocolatey community repository"
        return False, "Not a chocolatey package"

    def install_package(self, pkg_id: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Installs a Chocolatey package."""
        clean_name = pkg_id.replace("choco:", "")
        if dry_run:
            return True, f"[Dry Run] Simulated choco install for '{clean_name}'"

        try:
            res = silent_run([self.choco_path, "install", clean_name, "-y", "--no-progress"], timeout=180)
            if res.returncode == 0:
                return True, f"Successfully installed chocolatey package '{clean_name}'"
            return False, f"choco install failed (Code {res.returncode}): {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing choco install: {e}"

    def install_update(self, item: ProgramItem, dry_run: bool = False) -> Tuple[bool, str]:
        """Updates an existing Chocolatey package."""
        clean_name = item.name.replace("choco:", "")
        if dry_run:
            return True, f"[Dry Run] Simulated choco upgrade for '{clean_name}'"

        try:
            res = silent_run([self.choco_path, "upgrade", clean_name, "-y", "--no-progress"], timeout=180)
            if res.returncode == 0:
                return True, f"Successfully updated chocolatey package '{clean_name}'"
            return False, f"choco upgrade failed: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing choco upgrade: {e}"

    def uninstall_package(self, pkg_id: str) -> Tuple[bool, str]:
        """Uninstalls a Chocolatey package."""
        clean_name = pkg_id.replace("choco:", "")
        try:
            res = silent_run([self.choco_path, "uninstall", clean_name, "-y", "--no-progress"], timeout=60)
            if res.returncode == 0:
                return True, f"Successfully uninstalled chocolatey package '{clean_name}'"
            return False, f"choco uninstall failed: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing choco uninstall: {e}"

    def search_packages(self, query: str) -> List[ProgramItem]:
        """Searches Chocolatey community repository."""
        if not self.is_available():
            return []

        clean_q = query.strip()
        if not clean_q:
            return []

        try:
            res = silent_run([self.choco_path, "search", clean_q, "--limit-output"], timeout=20)
            if not res.stdout:
                return []

            matches: List[ProgramItem] = []
            for line in res.stdout.strip().splitlines():
                parts = line.split("|")
                if len(parts) >= 2:
                    name = parts[0].strip()
                    ver = parts[1].strip()
                    matches.append(
                        ProgramItem(
                            name=f"choco:{name}",
                            id=f"choco:{name}",
                            latest_version=ver,
                            package_type=PackageType.CHOCOLATEY,
                            source="chocolatey",
                            publisher="Chocolatey",
                        )
                    )
            return matches
        except Exception as e:
            logger.error(f"Error searching chocolatey: {e}")
            return []
