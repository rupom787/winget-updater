"""Source adapter for Python Package Index (pip).
Discovers installed Python packages, queries outdated releases, and handles install, update, and uninstall.
"""

import glob
import json
import os
import shutil
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple
from winget_updater.adapters.base import BaseSourceAdapter
from winget_updater.models import PackageType, ProgramItem, UpdateAction
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_popen_stream, silent_run

logger = get_logger()


class PipAdapter(BaseSourceAdapter):
    """Adapter for Python pip packages."""

    @staticmethod
    def get_python_executables() -> List[str]:
        """Discovers all installed Python interpreter binaries on the Windows system.
        Covers PATH python, py launcher, AppData User Programs, and Program Files."""
        executables: List[str] = []
        seen = set()

        def add_exe(p: Optional[str]):
            if p and os.path.isfile(p):
                norm = os.path.normcase(os.path.abspath(p))
                if norm not in seen:
                    base = os.path.basename(norm).lower()
                    if base in ("python.exe", "python3.exe", "py.exe"):
                        seen.add(norm)
                        executables.append(norm)

        # 1. PATH python / py
        add_exe(shutil.which("python"))
        add_exe(shutil.which("python3"))
        add_exe(shutil.which("py"))

        # 2. LocalAppData Programs
        for p in glob.glob(os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python*\python.exe")):
            add_exe(p)

        # 3. Program Files
        for p in glob.glob(os.path.expandvars(r"%ProgramFiles%\Python*\python.exe")):
            add_exe(p)
        for p in glob.glob(os.path.expandvars(r"%ProgramFiles(x86)%\Python*\python.exe")):
            add_exe(p)

        # Fallback to sys.executable if it is actually python
        if sys.executable and "python" in os.path.basename(sys.executable).lower():
            add_exe(sys.executable)

        return executables

    def __init__(self, python_path: Optional[str] = None):
        super().__init__(name="pip", display_name="Python (Pip)", enabled=True)
        py_candidates = self.get_python_executables()
        self.python_path = python_path or (py_candidates[0] if py_candidates else (shutil.which("python") or "python"))
        self.all_python_paths = [python_path] if python_path else py_candidates

    def is_available(self) -> bool:
        """Checks if python with pip is available."""
        paths_to_test = self.all_python_paths or [self.python_path]
        for py in paths_to_test:
            try:
                res = silent_run([py, "-m", "pip", "--version"], timeout=10)
                if res.returncode == 0:
                    self.python_path = py
                    return True
            except Exception:
                continue
        return False

    def get_version(self) -> Optional[str]:
        """Returns the installed pip version string."""
        try:
            res = silent_run([self.python_path, "-m", "pip", "--version"], timeout=10)
            if res.returncode == 0 and res.stdout:
                parts = res.stdout.strip().split()
                if len(parts) >= 2:
                    return parts[1]
        except Exception:
            pass
        return None

    def get_installed_packages(self) -> List[ProgramItem]:
        """Discovers all installed Python packages via pip list --format=json across Python runtimes."""
        if not self.is_available():
            return []

        paths_to_query = self.all_python_paths or [self.python_path]
        items_by_name: Dict[str, ProgramItem] = {}

        for py in paths_to_query:
            try:
                res = silent_run([py, "-m", "pip", "list", "--format=json"], timeout=20)
                if res.returncode != 0 or not res.stdout:
                    continue

                data = json.loads(res.stdout)
                for entry in data:
                    pkg_name = entry.get("name", "")
                    if not pkg_name:
                        continue
                    pkg_ver = entry.get("version", "")
                    clean_name = pkg_name.strip()
                    k = clean_name.lower()
                    if k not in items_by_name:
                        item = ProgramItem(
                            name=clean_name,
                            id=f"pip:{clean_name}",
                            installed_version=pkg_ver,
                            package_type=PackageType.PIP,
                            source="pip",
                            publisher="Python Software Foundation / PyPI",
                            action=UpdateAction.UP_TO_DATE,
                            is_verified_winget=True,
                        )
                        items_by_name[k] = item
            except Exception as e:
                logger.debug(f"Error querying pip installed packages on {py}: {e}")

        return list(items_by_name.values())

    def query_updates(self, installed_items: Optional[List[ProgramItem]] = None) -> Dict[str, Dict[str, str]]:
        """Queries outdated Python packages via pip list --outdated --format=json across Python runtimes."""
        if not self.is_available():
            return {}

        paths_to_query = self.all_python_paths or [self.python_path]
        updates: Dict[str, Dict[str, str]] = {}

        for py in paths_to_query:
            try:
                res = silent_run([py, "-m", "pip", "list", "--outdated", "--format=json"], timeout=30)
                if res.returncode != 0 or not res.stdout:
                    continue

                data = json.loads(res.stdout)
                for entry in data:
                    pkg_name = entry.get("name", "")
                    if not pkg_name:
                        continue
                    cur_v = entry.get("version", "")
                    lat_v = entry.get("latest_version", "")
                    from winget_updater.winget.version_comparator import compare_versions
                    comp = compare_versions(cur_v, lat_v)
                    if comp is not None and comp >= 0:
                        continue
                    clean_k = pkg_name.strip().lower()
                    updates[clean_k] = {
                        "installed_version": cur_v,
                        "latest_version": lat_v,
                    }
            except Exception as e:
                logger.debug(f"Error checking pip outdated packages on {py}: {e}")

        return updates

    def verify_package(self, item: ProgramItem) -> Tuple[bool, str]:
        """Verifies that the package belongs to the pip repository."""
        if item.source == "pip" or item.package_type == PackageType.PIP:
            return True, "Verified trusted PyPI repository"
        return False, "Not a pip package"

    def get_package_version(self, pkg_name: str) -> Optional[str]:
        """Queries the current installed version of a specific Python package."""
        clean_name = pkg_name.replace("pip:", "").strip()
        paths_to_query = self.all_python_paths or [self.python_path]
        for py in paths_to_query:
            try:
                res = silent_run([py, "-m", "pip", "show", clean_name], timeout=15)
                if res.returncode == 0 and res.stdout:
                    for line in res.stdout.splitlines():
                        if line.lower().startswith("version:"):
                            return line.split(":", 1)[1].strip()
            except Exception:
                pass
        return None

    def install_package(self, pkg_id: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Installs a new package using pip install."""
        clean_name = pkg_id.replace("pip:", "")
        if dry_run:
            return True, f"[Dry Run] Simulated pip install for '{clean_name}'"

        try:
            res = silent_run([self.python_path, "-m", "pip", "install", "--no-warn-script-location", "--disable-pip-version-check", "--no-color", clean_name], timeout=180)
            if res.returncode == 0:
                return True, f"Successfully installed pip package '{clean_name}'"
            return False, f"pip install failed (Code {res.returncode}): {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing pip install: {e}"

    def install_update(
        self,
        item: ProgramItem,
        dry_run: bool = False,
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """Updates an existing Python package using pip install --upgrade."""
        clean_name = item.name.replace("pip:", "")
        if dry_run:
            return True, f"[Dry Run] Simulated pip upgrade for '{clean_name}'"

        cmd = [self.python_path, "-m", "pip", "install", "--upgrade", "--no-warn-script-location", "--disable-pip-version-check", "--no-color", clean_name]
        try:
            if log_callback:
                ret, out = silent_popen_stream(cmd, line_callback=log_callback, timeout=180)
                if ret == 0:
                    return True, f"Successfully updated pip package '{clean_name}'"
                lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
                return False, f"pip update failed: {lines[-1] if lines else f'Code {ret}'}"
            res = silent_run(cmd, timeout=180)
            if res.returncode == 0:
                return True, f"Successfully updated pip package '{clean_name}'"
            return False, f"pip update failed (Code {res.returncode}): {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing pip update: {e}"

    def uninstall_package(self, pkg_id: str) -> Tuple[bool, str]:
        """Uninstalls a Python package using pip uninstall -y."""
        clean_name = pkg_id.replace("pip:", "")
        try:
            res = silent_run([self.python_path, "-m", "pip", "uninstall", "-y", "--disable-pip-version-check", "--no-color", clean_name], timeout=60)
            if res.returncode == 0:
                return True, f"Successfully uninstalled pip package '{clean_name}'"
            return False, f"pip uninstall failed: {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing pip uninstall: {e}"

    def search_packages(self, query: str) -> List[ProgramItem]:
        """Discovers matching packages for catalog search."""
        # Clean query
        q = query.strip().lower()
        if not q:
            return []

        # Popular Python packages catalog discovery list
        POPULAR_PIP = [
            ("requests", "HTTP for Humans - fast, reliable Python requests client"),
            ("numpy", "Fundamental package for scientific computing with Python"),
            ("pandas", "Powerful data structures for data analysis and manipulation"),
            ("fastapi", "Modern, fast high-performance web framework for building APIs"),
            ("uvicorn", "Lightning-fast ASGI server implementation"),
            ("flask", "Lightweight WSGI web application framework"),
            ("django", "High-level Python web framework that encourages rapid design"),
            ("pytest", "Simple and powerful framework for writing effective tests"),
            ("scikit-learn", "Machine learning library for predictive data analysis"),
            ("torch", "Tensors and dynamic neural networks in Python with strong GPU acceleration"),
            ("tensorflow", "Open source platform for machine learning"),
            ("matplotlib", "Comprehensive library for creating static and animated visualizations"),
            ("beautifulsoup4", "Screen-scraping library to extract data from HTML/XML files"),
            ("black", "The uncompromising Python code formatter"),
            ("ruff", "An extremely fast Python linter and code formatter"),
            ("pydantic", "Data validation and settings management using Python type annotations"),
            ("sqlalchemy", "Database toolkit and Object Relational Mapper for Python"),
            ("httpx", "Next generation HTTP client for Python with async support"),
            ("rich", "Rich text and beautiful terminal formatting"),
            ("click", "Package for creating beautiful command line interfaces"),
        ]

        matches: List[ProgramItem] = []
        for name, desc in POPULAR_PIP:
            if q in name.lower() or q in desc.lower():
                matches.append(
                    ProgramItem(
                        name=f"pip:{name}",
                        id=f"pip:{name}",
                        latest_version="Latest",
                        package_type=PackageType.PIP,
                        source="pip",
                        publisher="PyPI",
                        notes=desc,
                    )
                )
        return matches

