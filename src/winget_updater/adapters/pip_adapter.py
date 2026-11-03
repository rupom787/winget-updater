"""Source adapter for Python Package Index (pip).
Discovers installed Python packages, queries outdated releases, and handles install, update, and uninstall.
"""

import json
import shutil
import sys
from typing import Any, Dict, List, Optional, Tuple
from winget_updater.adapters.base import BaseSourceAdapter
from winget_updater.models import PackageType, ProgramItem, UpdateAction
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()


class PipAdapter(BaseSourceAdapter):
    """Adapter for Python pip packages."""

    def __init__(self, python_path: Optional[str] = None):
        super().__init__(name="pip", display_name="Python (Pip)", enabled=True)
        self.python_path = python_path or sys.executable

    def is_available(self) -> bool:
        """Checks if python with pip is available."""
        try:
            res = silent_run([self.python_path, "-m", "pip", "--version"], timeout=10)
            return res.returncode == 0
        except Exception:
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
        """Discovers all installed Python packages via pip list --format=json."""
        if not self.is_available():
            return []

        try:
            res = silent_run([self.python_path, "-m", "pip", "list", "--format=json"], timeout=20)
            if res.returncode != 0 or not res.stdout:
                return []

            data = json.loads(res.stdout)
            items: List[ProgramItem] = []
            for entry in data:
                pkg_name = entry.get("name", "")
                if not pkg_name:
                    continue
                pkg_ver = entry.get("version", "")
                item = ProgramItem(
                    name=f"pip:{pkg_name}",
                    id=f"pip:{pkg_name}",
                    installed_version=pkg_ver,
                    package_type=PackageType.PIP,
                    source="pip",
                    publisher="Python Software Foundation / PyPI",
                    action=UpdateAction.UP_TO_DATE,
                    is_verified_winget=True,
                )
                items.append(item)
            return items
        except Exception as e:
            logger.error(f"Error querying pip installed packages: {e}")
            return []

    def query_updates(self, installed_items: Optional[List[ProgramItem]] = None) -> Dict[str, Dict[str, str]]:
        """Queries outdated Python packages via pip list --outdated --format=json."""
        if not self.is_available():
            return {}

        try:
            res = silent_run([self.python_path, "-m", "pip", "list", "--outdated", "--format=json"], timeout=30)
            if res.returncode != 0 or not res.stdout:
                return {}

            data = json.loads(res.stdout)
            updates: Dict[str, Dict[str, str]] = {}
            for entry in data:
                pkg_name = entry.get("name", "")
                if not pkg_name:
                    continue
                cur_v = entry.get("version", "")
                lat_v = entry.get("latest_version", "")
                updates[pkg_name.lower()] = {
                    "installed_version": cur_v,
                    "latest_version": lat_v,
                }
            return updates
        except Exception as e:
            logger.error(f"Error checking pip outdated packages: {e}")
            return {}

    def verify_package(self, item: ProgramItem) -> Tuple[bool, str]:
        """Verifies that the package belongs to the pip repository."""
        if item.source == "pip" or item.package_type == PackageType.PIP:
            return True, "Verified trusted PyPI repository"
        return False, "Not a pip package"

    def install_package(self, pkg_id: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Installs a new package using pip install."""
        clean_name = pkg_id.replace("pip:", "")
        if dry_run:
            return True, f"[Dry Run] Simulated pip install for '{clean_name}'"

        try:
            res = silent_run([self.python_path, "-m", "pip", "install", clean_name], timeout=180)
            if res.returncode == 0:
                return True, f"Successfully installed pip package '{clean_name}'"
            return False, f"pip install failed (Code {res.returncode}): {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing pip install: {e}"

    def install_update(self, item: ProgramItem, dry_run: bool = False) -> Tuple[bool, str]:
        """Updates an existing Python package using pip install --upgrade."""
        clean_name = item.name.replace("pip:", "")
        if dry_run:
            return True, f"[Dry Run] Simulated pip upgrade for '{clean_name}'"

        try:
            res = silent_run([self.python_path, "-m", "pip", "install", "--upgrade", clean_name], timeout=180)
            if res.returncode == 0:
                return True, f"Successfully updated pip package '{clean_name}'"
            return False, f"pip update failed (Code {res.returncode}): {res.stderr.strip() or res.stdout.strip()}"
        except Exception as e:
            return False, f"Exception executing pip update: {e}"

    def uninstall_package(self, pkg_id: str) -> Tuple[bool, str]:
        """Uninstalls a Python package using pip uninstall -y."""
        clean_name = pkg_id.replace("pip:", "")
        try:
            res = silent_run([self.python_path, "-m", "pip", "uninstall", "-y", clean_name], timeout=60)
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
