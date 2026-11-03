"""Source adapter for Node.js package manager (npm) global modules.
Discovers installed global npm packages, queries outdated releases, and handles install, update, and uninstall.
"""

import json
import shutil
from typing import Any, Dict, List, Optional, Tuple
from winget_updater.adapters.base import BaseSourceAdapter
from winget_updater.models import PackageType, ProgramItem, UpdateAction
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()


class NpmAdapter(BaseSourceAdapter):
    """Adapter for global Node.js npm packages."""

    def __init__(self, npm_path: Optional[str] = None):
        super().__init__(name="npm", display_name="Node.js (Npm)", enabled=True)
        self.npm_path = npm_path or shutil.which("npm.cmd") or shutil.which("npm") or "npm.cmd"

    def is_available(self) -> bool:
        """Checks if npm CLI is available."""
        try:
            res = silent_run([self.npm_path, "--version"], timeout=10)
            return res.returncode == 0
        except Exception:
            return False

    def get_version(self) -> Optional[str]:
        """Returns the npm version string."""
        try:
            res = silent_run([self.npm_path, "--version"], timeout=10)
            if res.returncode == 0 and res.stdout:
                return res.stdout.strip()
        except Exception:
            pass
        return None

    def get_installed_packages(self) -> List[ProgramItem]:
        """Discovers installed global npm packages via npm list -g --depth=0 --json."""
        if not self.is_available():
            return []

        try:
            res = silent_run([self.npm_path, "list", "-g", "--depth=0", "--json"], timeout=20)
            if not res.stdout:
                return []

            # npm outputs JSON even if returncode != 0 (e.g., peer dep warnings)
            try:
                data = json.loads(res.stdout)
            except Exception:
                return []

            deps = data.get("dependencies", {})
            items: List[ProgramItem] = []
            for pkg_name, info in deps.items():
                if not pkg_name:
                    continue
                ver = info.get("version", "1.0.0") if isinstance(info, dict) else "1.0.0"
                item = ProgramItem(
                    name=f"npm:{pkg_name}",
                    id=f"npm:{pkg_name}",
                    installed_version=ver,
                    package_type=PackageType.NPM,
                    source="npm",
                    publisher="Node Package Registry / OpenJS",
                    action=UpdateAction.UP_TO_DATE,
                    is_verified_winget=True,
                )
                items.append(item)
            return items
        except Exception as e:
            logger.error(f"Error querying npm global packages: {e}")
            return []

    def query_updates(self, installed_items: Optional[List[ProgramItem]] = None) -> Dict[str, Dict[str, str]]:
        """Queries outdated global npm packages via npm outdated -g --json."""
        if not self.is_available():
            return {}

        try:
            res = silent_run([self.npm_path, "outdated", "-g", "--json"], timeout=30)
            if not res.stdout:
                return {}

            try:
                data = json.loads(res.stdout)
            except Exception:
                return {}

            updates: Dict[str, Dict[str, str]] = {}
            for pkg_name, info in data.items():
                if isinstance(info, dict):
                    cur_v = info.get("current", "")
                    lat_v = info.get("latest", "")
                    updates[pkg_name.lower()] = {
                        "installed_version": cur_v,
                        "latest_version": lat_v,
                    }
            return updates
        except Exception as e:
            logger.error(f"Error checking npm outdated packages: {e}")
            return {}

    def verify_package(self, item: ProgramItem) -> Tuple[bool, str]:
        """Verifies that the package belongs to npm."""
        if item.source == "npm" or item.package_type == PackageType.NPM:
            return True, "Verified trusted npm registry source"
        return False, "Not an npm package"

    def install_package(self, pkg_id: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Installs a global npm package using npm install -g."""
        clean_name = pkg_id.replace("npm:", "")
        if dry_run:
            return True, f"[Dry Run] Simulated npm install -g for '{clean_name}'"

        try:
            res = silent_run([self.npm_path, "install", "-g", clean_name], timeout=180)
            if res.returncode == 0:
                return True, f"Successfully installed npm global package '{clean_name}'"
            return False, f"npm install failed (Code {res.returncode}): {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing npm install: {e}"

    def install_update(self, item: ProgramItem, dry_run: bool = False) -> Tuple[bool, str]:
        """Updates a global npm package using npm update -g."""
        clean_name = item.name.replace("npm:", "")
        if dry_run:
            return True, f"[Dry Run] Simulated npm update -g for '{clean_name}'"

        try:
            res = silent_run([self.npm_path, "update", "-g", clean_name], timeout=180)
            if res.returncode == 0:
                return True, f"Successfully updated npm package '{clean_name}'"
            return False, f"npm update failed (Code {res.returncode}): {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing npm update: {e}"

    def uninstall_package(self, pkg_id: str) -> Tuple[bool, str]:
        """Uninstalls a global npm package using npm uninstall -g."""
        clean_name = pkg_id.replace("npm:", "")
        try:
            res = silent_run([self.npm_path, "uninstall", "-g", clean_name], timeout=60)
            if res.returncode == 0:
                return True, f"Successfully uninstalled npm package '{clean_name}'"
            return False, f"npm uninstall failed: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing npm uninstall: {e}"

    def search_packages(self, query: str) -> List[ProgramItem]:
        """Discovers matching packages for catalog search."""
        q = query.strip().lower()
        if not q:
            return []

        POPULAR_NPM = [
            ("typescript", "TypeScript is a language for application-scale JavaScript development"),
            ("yarn", "Fast, reliable, and secure dependency management for Node.js"),
            ("pnpm", "Fast, disk space efficient package manager"),
            ("nodemon", "Tool that helps develop node.js based applications by automatically restarting"),
            ("eslint", "An AST-based pattern checker for JavaScript"),
            ("prettier", "Prettier is an opinionated code formatter"),
            ("create-react-app", "Set up a modern web app by running one command"),
            ("next", "The React Framework for the Web"),
            ("vite", "Next Generation Frontend Tooling"),
            ("webpack", "Packs CommonJs/AMD modules for the browser"),
            ("express", "Fast, unopinionated, minimalist web framework for node"),
            ("nest", "Progressive Node.js framework for building efficient and scalable server-side apps"),
            ("pm2", "Production Process Manager for Node.js applications with a built-in Load Balancer"),
            ("rimraf", "A deep deletion module for node (like rm -rf)"),
            ("serve", "Static file serving and directory listing"),
        ]

        matches: List[ProgramItem] = []
        for name, desc in POPULAR_NPM:
            if q in name.lower() or q in desc.lower():
                matches.append(
                    ProgramItem(
                        name=f"npm:{name}",
                        id=f"npm:{name}",
                        latest_version="Latest",
                        package_type=PackageType.NPM,
                        source="npm",
                        publisher="npm",
                        notes=desc,
                    )
                )
        return matches

