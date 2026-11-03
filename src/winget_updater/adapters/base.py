"""Base abstractions for update source adapters."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from winget_updater.models import ProgramItem, UpdateAction


class BaseSourceAdapter(ABC):
    """Abstract interface representing a trusted software update repository or source."""

    def __init__(self, name: str, display_name: str, enabled: bool = True):
        self.name = name
        self.display_name = display_name
        self.enabled = enabled

    @abstractmethod
    def is_available(self) -> bool:
        """Determines whether the source or CLI tool is installed and reachable on the host."""
        pass

    @abstractmethod
    def query_updates(self, installed_items: List[ProgramItem]) -> Dict[str, Any]:
        """Queries available updates for the given list of installed programs."""
        pass

    @abstractmethod
    def verify_package(self, item: ProgramItem) -> Tuple[bool, str]:
        """Cryptographically or registry-verifies the package source before installation."""
        pass

    @abstractmethod
    def install_update(self, item: ProgramItem, dry_run: bool = False, **kwargs) -> Tuple[bool, str]:
        """Executes the package update using the adapter's verified installation mechanism."""
        pass

    def get_installed_packages(self) -> List[ProgramItem]:
        """Discovers and returns all installed packages tracked by this package manager."""
        return []

    def install_package(self, pkg_id: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Installs a new package from this source repository."""
        return False, f"Installation not supported by adapter '{self.name}'"

    def uninstall_package(self, pkg_id: str) -> Tuple[bool, str]:
        """Uninstalls an existing package managed by this adapter."""
        return False, f"Uninstallation not supported by adapter '{self.name}'"

    def search_packages(self, query: str) -> List[ProgramItem]:
        """Discovers and searches packages matching query in this repository."""
        return []

