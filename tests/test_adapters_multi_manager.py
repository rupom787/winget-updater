"""Comprehensive test suite for Universal Multi-Package Manager Adapters:
Pip, Npm, Scoop, Chocolatey, and SourceManager.
"""

import json
from unittest.mock import MagicMock, patch
import pytest

from winget_updater.adapters.chocolatey_adapter import ChocolateyAdapter
from winget_updater.adapters.manager import SourceManager
from winget_updater.adapters.npm_adapter import NpmAdapter
from winget_updater.adapters.pip_adapter import PipAdapter
from winget_updater.adapters.scoop_adapter import ScoopAdapter
from winget_updater.models import PackageType, ProgramItem, UpdateAction


# ---------------------------------------------------------------------------
# PipAdapter Tests
# ---------------------------------------------------------------------------

def test_pip_adapter_installed_and_updates():
    pip_adapter = PipAdapter(python_path="fake_python.exe")

    mock_installed = json.dumps([
        {"name": "requests", "version": "2.31.0"},
        {"name": "urllib3", "version": "2.0.0"},
    ])
    mock_outdated = json.dumps([
        {"name": "requests", "version": "2.31.0", "latest_version": "2.32.3"},
    ])

    with patch("winget_updater.adapters.pip_adapter.silent_run") as mock_run:
        # Mock availability
        mock_run.return_value = MagicMock(returncode=0, stdout="pip 24.0", stderr="")
        assert pip_adapter.is_available() is True
        assert pip_adapter.get_version() == "24.0"

        # Mock installed
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_installed, stderr="")
        items = pip_adapter.get_installed_packages()
        assert len(items) == 2
        assert items[0].name == "requests"
        assert items[0].id == "pip:requests"
        assert items[0].installed_version == "2.31.0"
        assert items[0].package_type == PackageType.PIP
        assert items[0].source == "pip"

        # Mock query updates
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_outdated, stderr="")
        upd = pip_adapter.query_updates()
        assert "requests" in upd
        assert upd["requests"]["latest_version"] == "2.32.3"


def test_pip_adapter_install_update_uninstall():
    pip_adapter = PipAdapter(python_path="fake_python.exe")

    with patch("winget_updater.adapters.pip_adapter.silent_run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Successfully installed", stderr="")

        # Dry run install
        ok, msg = pip_adapter.install_package("pip:flask", dry_run=True)
        assert ok is True
        assert "[Dry Run]" in msg

        # Real install
        ok, msg = pip_adapter.install_package("pip:flask", dry_run=False)
        assert ok is True
        assert "Successfully installed" in msg

        # Update
        item = ProgramItem(name="pip:requests", id="pip:requests", installed_version="2.31.0", source="pip")
        ok, msg = pip_adapter.install_update(item, dry_run=False)
        assert ok is True
        assert "Successfully updated" in msg

        # Uninstall
        ok, msg = pip_adapter.uninstall_package("pip:flask")
        assert ok is True
        assert "Successfully uninstalled" in msg


# ---------------------------------------------------------------------------
# NpmAdapter Tests
# ---------------------------------------------------------------------------

def test_npm_adapter_installed_and_updates():
    npm_adapter = NpmAdapter(npm_path="fake_npm.cmd")

    mock_installed = json.dumps({
        "dependencies": {
            "typescript": {"version": "5.3.3"},
            "yarn": {"version": "1.22.19"},
        }
    })
    mock_outdated = json.dumps({
        "typescript": {
            "current": "5.3.3",
            "wanted": "5.4.0",
            "latest": "5.4.5",
        }
    })

    with patch("winget_updater.adapters.npm_adapter.silent_run") as mock_run, \
         patch.object(NpmAdapter, "get_node_prefixes", return_value=["C:\\mock_prefix"]):
        mock_run.return_value = MagicMock(returncode=0, stdout="10.2.4", stderr="")
        assert npm_adapter.is_available() is True
        assert npm_adapter.get_version() == "10.2.4"

        # Installed
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_installed, stderr="")
        items = npm_adapter.get_installed_packages()
        assert len(items) == 2
        assert items[0].name == "typescript"
        assert items[0].id == "npm:typescript"
        assert items[0].installed_version == "5.3.3"
        assert items[0].package_type == PackageType.NPM

        # Outdated
        mock_run.return_value = MagicMock(returncode=0, stdout=mock_outdated, stderr="")
        upd = npm_adapter.query_updates()
        assert "typescript" in upd
        assert upd["typescript"]["latest_version"] == "5.4.5"


def test_npm_adapter_install_update_uninstall():
    npm_adapter = NpmAdapter(npm_path="fake_npm.cmd")

    with patch("winget_updater.adapters.npm_adapter.silent_run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="added 1 package", stderr="")

        ok, msg = npm_adapter.install_package("npm:prettier", dry_run=True)
        assert ok is True
        assert "[Dry Run]" in msg

        ok, msg = npm_adapter.install_package("npm:prettier", dry_run=False)
        assert ok is True
        assert "Successfully installed" in msg

        item = ProgramItem(name="npm:typescript", id="npm:typescript", source="npm")
        ok, msg = npm_adapter.install_update(item, dry_run=False)
        assert ok is True
        assert "Successfully updated" in msg

        ok, msg = npm_adapter.uninstall_package("npm:prettier")
        assert ok is True
        assert "Successfully uninstalled" in msg


# ---------------------------------------------------------------------------
# ScoopAdapter Tests
# ---------------------------------------------------------------------------

def test_scoop_adapter_workflow():
    scoop_adapter = ScoopAdapter(scoop_path="fake_scoop.cmd")

    mock_list_output = (
        "Name        Version   Source  Updated\n"
        "----        -------   ------  -------\n"
        "7zip        24.08     main    2026-01-01\n"
        "git         2.44.0    main    2026-01-01\n"
    )
    mock_status_output = (
        "Name    Installed Version Latest Version Missing Dependencies Info\n"
        "----    ----------------- -------------- -------------------- ----\n"
        "git     2.44.0            2.45.0\n"
    )

    with patch("winget_updater.adapters.scoop_adapter.silent_run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="v0.3.1", stderr="")
        assert scoop_adapter.is_available() is True

        mock_run.return_value = MagicMock(returncode=0, stdout=mock_list_output, stderr="")
        items = scoop_adapter.get_installed_packages()
        assert len(items) == 2
        assert items[0].name == "scoop:7zip"
        assert items[0].package_type == PackageType.SCOOP

        mock_run.return_value = MagicMock(returncode=0, stdout=mock_status_output, stderr="")
        upd = scoop_adapter.query_updates()
        assert "git" in upd
        assert upd["git"]["latest_version"] == "2.45.0"

        ok, msg = scoop_adapter.install_package("scoop:neovim", dry_run=False)
        assert ok is True

        item = ProgramItem(name="scoop:git", id="scoop:git", source="scoop")
        ok, msg = scoop_adapter.install_update(item, dry_run=False)
        assert ok is True

        ok, msg = scoop_adapter.uninstall_package("scoop:neovim")
        assert ok is True


# ---------------------------------------------------------------------------
# ChocolateyAdapter Tests
# ---------------------------------------------------------------------------

def test_chocolatey_adapter_workflow():
    choco_adapter = ChocolateyAdapter(choco_path="fake_choco.exe")

    mock_list_output = (
        "git|2.44.0\n"
        "curl|8.6.0\n"
    )
    mock_outdated_output = (
        "git|2.44.0|2.45.0|false\n"
    )

    with patch("winget_updater.adapters.chocolatey_adapter.silent_run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="2.2.2", stderr="")
        assert choco_adapter.is_available() is True

        mock_run.return_value = MagicMock(returncode=0, stdout=mock_list_output, stderr="")
        items = choco_adapter.get_installed_packages()
        assert len(items) == 2
        assert items[0].name == "choco:git"
        assert items[0].package_type == PackageType.CHOCOLATEY

        mock_run.return_value = MagicMock(returncode=0, stdout=mock_outdated_output, stderr="")
        upd = choco_adapter.query_updates()
        assert "git" in upd
        assert upd["git"]["latest_version"] == "2.45.0"

        ok, msg = choco_adapter.install_package("choco:vlc", dry_run=False)
        assert ok is True

        item = ProgramItem(name="choco:git", id="choco:git", source="chocolatey")
        ok, msg = choco_adapter.install_update(item, dry_run=False)
        assert ok is True

        ok, msg = choco_adapter.uninstall_package("choco:vlc")
        assert ok is True


# ---------------------------------------------------------------------------
# SourceManager Dispatch & Orchestration Tests
# ---------------------------------------------------------------------------

def test_source_manager_orchestration():
    mgr = SourceManager()

    # Verify adapter registration
    assert mgr.get_adapter("pip") is not None
    assert mgr.get_adapter("npm") is not None
    assert mgr.get_adapter("scoop") is not None
    assert mgr.get_adapter("chocolatey") is not None
    assert mgr.get_adapter("winget") is not None

    mock_pip = MagicMock(spec=PipAdapter)
    mock_pip.name = "pip"
    mock_pip.display_name = "Python (Pip)"
    mock_pip.enabled = True
    mock_pip.is_available.return_value = True
    mock_pip.install_package.return_value = (True, "Installed mock pip package")
    mock_pip.install_update.return_value = (True, "Updated mock pip package")
    mock_pip.uninstall_package.return_value = (True, "Uninstalled mock pip package")
    mock_pip.search_packages.return_value = [
        ProgramItem(name="pip:numpy", id="pip:numpy", source="pip", package_type=PackageType.PIP)
    ]
    mock_pip.query_updates.return_value = {
        "numpy": {"installed_version": "1.24.0", "latest_version": "1.26.4"}
    }

    mgr.register_adapter(mock_pip)

    # Test install routing
    ok, msg = mgr.install_package("pip", "numpy")
    assert ok is True
    assert msg == "Installed mock pip package"

    # Test update routing
    pip_item = ProgramItem(name="pip:numpy", id="pip:numpy", source="pip")
    ok, msg = mgr.install_update(pip_item)
    assert ok is True
    assert msg == "Updated mock pip package"

    # Test uninstall routing
    ok, msg = mgr.uninstall_package(pip_item)
    assert ok is True
    assert msg == "Uninstalled mock pip package"

    # Test search_all
    results = mgr.search_all("numpy", target_sources=["pip"])
    assert len(results) == 1
    assert results[0].name == "pip:numpy"

    # Test query_all_updates
    all_upd = mgr.query_all_updates()
    assert "pip" in all_upd
    assert "numpy" in all_upd["pip"]
