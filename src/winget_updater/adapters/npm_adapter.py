"""Source adapter for Node.js package manager (npm) global modules.
Discovers installed global npm packages, queries outdated releases, and handles install, update, and uninstall.
"""

import glob
import json
import os
import shutil
from typing import Any, Callable, Dict, List, Optional, Tuple
from winget_updater.adapters.base import BaseSourceAdapter
from winget_updater.models import PackageType, ProgramItem, UpdateAction
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_popen_stream, silent_run

logger = get_logger()


class NpmAdapter(BaseSourceAdapter):
    """Adapter for global Node.js npm packages."""

    @staticmethod
    def get_node_prefixes() -> List[str]:
        """Discovers all active Node.js / npm installation prefixes on the system.
        Covers WinGet NodeJS packages, Program Files, AppData roaming npm, and NVM."""
        prefixes = set()

        # 1. User Roaming npm directory
        roaming = os.path.expandvars(r"%APPDATA%\npm")
        if os.path.isdir(roaming):
            prefixes.add(roaming)

        # 2. WinGet NodeJS Packages (e.g. OpenJS.NodeJS.LTS)
        winget_pattern = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\OpenJS.NodeJS*\*")
        for p in glob.glob(winget_pattern):
            if os.path.isdir(os.path.join(p, "node_modules")):
                prefixes.add(p)

        # 3. Standard Program Files
        for pf in [os.path.expandvars(r"%ProgramFiles%\nodejs"), os.path.expandvars(r"%ProgramFiles(x86)%\nodejs")]:
            if os.path.isdir(os.path.join(pf, "node_modules")):
                prefixes.add(pf)

        # 4. NVM for Windows / Volta / FNM
        for nvm_dir in [os.path.expandvars(r"%APPDATA%\nvm"), os.path.expandvars(r"%LOCALAPPDATA%\nvm")]:
            if os.path.isdir(nvm_dir):
                for p in glob.glob(os.path.join(nvm_dir, "v*")):
                    if os.path.isdir(os.path.join(p, "node_modules")):
                        prefixes.add(p)

        return list(prefixes)

    @staticmethod
    def get_npm_executables() -> List[str]:
        """Discovers all npm.cmd or npm binaries available on the host."""
        exes = []
        seen = set()

        def add_exe(p: Optional[str]):
            if p and os.path.isfile(p):
                norm = os.path.normcase(os.path.abspath(p))
                if norm not in seen:
                    seen.add(norm)
                    exes.append(norm)

        # 1. PATH npm
        add_exe(shutil.which("npm.cmd"))
        add_exe(shutil.which("npm"))

        # 2. WinGet NodeJS packages
        for p in glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\OpenJS.NodeJS*\*\npm.cmd")):
            add_exe(p)

        # 3. Program Files
        add_exe(os.path.expandvars(r"%ProgramFiles%\nodejs\npm.cmd"))
        add_exe(os.path.expandvars(r"%ProgramFiles(x86)%\nodejs\npm.cmd"))

        return exes

    def __init__(self, npm_path: Optional[str] = None):
        super().__init__(name="npm", display_name="Node.js (Npm)", enabled=True)
        npm_candidates = self.get_npm_executables()
        self.npm_path = npm_path or (npm_candidates[0] if npm_candidates else (shutil.which("npm.cmd") or shutil.which("npm") or "npm.cmd"))
        self.all_npm_paths = [npm_path] if npm_path else npm_candidates

    def is_available(self) -> bool:
        """Checks if npm CLI is available."""
        paths_to_test = self.all_npm_paths or [self.npm_path]
        for exe in paths_to_test:
            try:
                res = silent_run([exe, "--version"], timeout=10)
                if res.returncode == 0:
                    self.npm_path = exe
                    return True
            except Exception:
                continue
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
        """Discovers installed global npm packages across all Node prefixes."""
        if not self.is_available():
            return []

        prefixes = self.get_node_prefixes()
        items_by_name: Dict[str, ProgramItem] = {}

        # 1. Direct filesystem inspection of node_modules in prefixes (fastest & most reliable)
        for prefix in prefixes:
            nm = os.path.join(prefix, "node_modules")
            if os.path.isdir(nm):
                for pkg_dir in os.listdir(nm):
                    pj = os.path.join(nm, pkg_dir, "package.json")
                    if os.path.isfile(pj):
                        try:
                            with open(pj, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                pkg_name = data.get("name", pkg_dir)
                                pkg_ver = data.get("version", "1.0.0")
                                clean_name = pkg_name.strip()
                                k = clean_name.lower()
                                if k not in items_by_name:
                                    items_by_name[k] = ProgramItem(
                                        name=clean_name,
                                        id=f"npm:{clean_name}",
                                        installed_version=pkg_ver,
                                        package_type=PackageType.NPM,
                                        source="npm",
                                        publisher="Node Package Registry / OpenJS",
                                        action=UpdateAction.UP_TO_DATE,
                                        is_verified_winget=True,
                                    )
                        except Exception:
                            pass

        # 2. CLI fallback via npm list -g --depth=0 --json
        for prefix in prefixes:
            try:
                cmd = [self.npm_path, "list", "-g", "--depth=0", "--json", "--prefix", prefix]
                res = silent_run(cmd, timeout=15)
                if res.stdout:
                    try:
                        data = json.loads(res.stdout)
                        deps = data.get("dependencies", {})
                        for pkg_name, info in deps.items():
                            clean_name = pkg_name.strip()
                            k = clean_name.lower()
                            if k not in items_by_name:
                                ver = info.get("version", "1.0.0") if isinstance(info, dict) else "1.0.0"
                                items_by_name[k] = ProgramItem(
                                    name=clean_name,
                                    id=f"npm:{clean_name}",
                                    installed_version=ver,
                                    package_type=PackageType.NPM,
                                    source="npm",
                                    publisher="Node Package Registry / OpenJS",
                                    action=UpdateAction.UP_TO_DATE,
                                    is_verified_winget=True,
                                )
                    except Exception:
                        pass
            except Exception:
                pass

        return list(items_by_name.values())

    def query_updates(self, installed_items: Optional[List[ProgramItem]] = None) -> Dict[str, Dict[str, str]]:
        """Queries outdated global npm packages via npm outdated -g --json across all Node prefixes."""
        if not self.is_available():
            return {}

        prefixes = self.get_node_prefixes()
        updates: Dict[str, Dict[str, str]] = {}

        for prefix in prefixes:
            try:
                # Run with explicit prefix to prevent ENOENT on missing AppData roaming directories
                cmd = [self.npm_path, "outdated", "-g", "--json", "--prefix", prefix]
                res = silent_run(cmd, timeout=30)
                if not res.stdout:
                    continue

                try:
                    data = json.loads(res.stdout)
                    if isinstance(data, dict):
                        for pkg_name, info in data.items():
                            if isinstance(info, dict):
                                cur_v = info.get("current", "")
                                lat_v = info.get("latest", "")
                                clean_k = pkg_name.strip().lower()
                                updates[clean_k] = {
                                    "installed_version": cur_v,
                                    "latest_version": lat_v,
                                }
                except Exception:
                    pass
            except Exception as e:
                logger.debug(f"Error checking npm outdated packages with prefix {prefix}: {e}")

        return updates

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

    def get_package_version(self, pkg_name: str) -> Optional[str]:
        """Queries the current installed version of a specific global npm package."""
        clean_name = pkg_name.replace("npm:", "").strip()

        # 1. Direct filesystem check in node_modules across prefixes (fastest & most accurate)
        prefixes = self.get_node_prefixes()
        for prefix in prefixes:
            pj = os.path.join(prefix, "node_modules", clean_name, "package.json")
            if os.path.isfile(pj):
                try:
                    with open(pj, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        v = data.get("version")
                        if v:
                            return str(v).strip()
                except Exception:
                    pass

        # 2. CLI check via npm list -g --depth=0 <clean_name> --json
        for prefix in prefixes:
            try:
                cmd = [self.npm_path, "list", "-g", "--depth=0", clean_name, "--json", "--prefix", prefix]
                res = silent_run(cmd, timeout=15)
                if res.stdout:
                    data = json.loads(res.stdout)
                    deps = data.get("dependencies", {})
                    if clean_name in deps:
                        info = deps[clean_name]
                        ver = info.get("version") if isinstance(info, dict) else info
                        if ver:
                            return str(ver).strip()
            except Exception:
                pass

        # 3. Direct binary version check if package is npm or corepack
        if clean_name.lower() == "npm":
            try:
                res = silent_run([self.npm_path, "--version"], timeout=10)
                if res.returncode == 0 and res.stdout:
                    return res.stdout.strip()
            except Exception:
                pass
        elif clean_name.lower() == "corepack":
            try:
                cp_path = shutil.which("corepack") or "corepack"
                res = silent_run([cp_path, "--version"], timeout=10)
                if res.returncode == 0 and res.stdout:
                    return res.stdout.strip()
            except Exception:
                pass

        return None

    def install_update(
        self,
        item: ProgramItem,
        dry_run: bool = False,
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """Updates a global npm package using npm install -g <pkg>@latest."""
        clean_name = item.name.replace("npm:", "").strip()
        if dry_run:
            return True, f"[Dry Run] Simulated npm install -g for '{clean_name}@latest'"

        # Use npm install -g <pkg>@latest to ensure major and breaking updates apply correctly
        cmd = [self.npm_path, "install", "-g", f"{clean_name}@latest"]
        try:
            if log_callback:
                ret, out = silent_popen_stream(cmd, line_callback=log_callback, timeout=240)
                if ret == 0:
                    return True, f"Successfully updated npm package '{clean_name}'"
                lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
                return False, f"npm update failed: {lines[-1] if lines else f'Code {ret}'}"
            res = silent_run(cmd, timeout=240)
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

