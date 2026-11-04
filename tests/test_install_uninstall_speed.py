"""Unit tests verifying speed optimizations for installation and uninstallation routines (Item 8)."""

import pytest
from unittest.mock import MagicMock, patch
from winget_updater.winget.client import WingetClient
from winget_updater.adapters.winget_adapter import WingetAdapter
from winget_updater.adapters.pip_adapter import PipAdapter
from winget_updater.adapters.npm_adapter import NpmAdapter
from winget_updater.adapters.chocolatey_adapter import ChocolateyAdapter
from winget_updater.models import ProgramItem, PackageType, UpdateAction


class TestSpeedOptimizations:
    """Verifies that install and uninstall commands are optimized for maximum throughput."""

    def test_winget_upgrade_speed_flags(self):
        """Winget upgrade should use --silent and target specific --source to skip multi-CDN latency."""
        client = WingetClient()
        with patch("winget_updater.winget.client.silent_popen_stream") as mock_stream:
            mock_stream.return_value = (0, "Successfully installed")
            
            # 1. Standard winget ID with dot
            client.upgrade_package("Mozilla.Firefox", dry_run=False, log_callback=lambda l: None)
            cmd = mock_stream.call_args[0][0]
            assert "--silent" in cmd, "Winget upgrade must include --silent"
            assert "--source" in cmd
            idx = cmd.index("--source")
            assert cmd[idx + 1] == "winget"

            # 2. Microsoft Store package ID
            client.upgrade_package("msstore:9NBLGGH4NNS1", dry_run=False, log_callback=lambda l: None)
            cmd = mock_stream.call_args[0][0]
            assert "--silent" in cmd
            assert "--source" in cmd
            idx = cmd.index("--source")
            assert cmd[idx + 1] == "msstore"

    def test_winget_install_speed_flags(self):
        """Winget install should use --silent, --no-upgrade, and targeted --source."""
        client = WingetClient()
        with patch("winget_updater.winget.client.silent_run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            client.install_package("Git.Git", dry_run=False)
            cmd = mock_run.call_args[0][0]
            assert "--silent" in cmd, "Winget install must include --silent"
            assert "--no-upgrade" in cmd, "Winget install must include --no-upgrade to skip redundant checks"
            assert "--source" in cmd
            idx = cmd.index("--source")
            assert cmd[idx + 1] == "winget"

    def test_winget_uninstall_speed_flags(self):
        """Winget uninstall should use --silent and target source."""
        client = WingetClient()
        with patch("winget_updater.winget.client.silent_run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            client.uninstall_package("Microsoft.PowerToys", dry_run=False)
            cmd = mock_run.call_args[0][0]
            assert "--silent" in cmd, "Winget uninstall must include --silent to bypass uninstaller UI"
            assert "--source" in cmd
            idx = cmd.index("--source")
            assert cmd[idx + 1] == "winget"

    def test_winget_adapter_direct_methods(self):
        """WingetAdapter must directly implement install_package and uninstall_package without fall-through errors."""
        mock_client = MagicMock(spec=WingetClient)
        mock_client.install_package.return_value = (True, "Installed")
        mock_client.uninstall_package.return_value = (True, "Uninstalled")

        adapter = WingetAdapter(client=mock_client)
        ok_inst, _ = adapter.install_package("VLC.VLC")
        assert ok_inst is True
        mock_client.install_package.assert_called_with("VLC.VLC", dry_run=False)

        ok_uninst, _ = adapter.uninstall_package("VLC.VLC")
        assert ok_uninst is True
        mock_client.uninstall_package.assert_called_with("VLC.VLC", dry_run=False)

    def test_pip_adapter_fast_flags(self):
        """Pip adapter must use --disable-pip-version-check and --no-warn-script-location."""
        adapter = PipAdapter()
        with patch("winget_updater.adapters.pip_adapter.silent_run") as mock_run, \
             patch("winget_updater.adapters.pip_adapter.silent_popen_stream") as mock_stream:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            mock_stream.return_value = (0, "Successfully installed")

            # Install
            adapter.install_package("requests")
            cmd_inst = mock_run.call_args[0][0]
            assert "--disable-pip-version-check" in cmd_inst
            assert "--no-warn-script-location" in cmd_inst

            # Update
            item = ProgramItem(name="requests", installed_version="2.31.0", latest_version="2.32.0", action=UpdateAction.AVAILABLE)
            adapter.install_update(item, log_callback=lambda l: None)
            cmd_up = mock_stream.call_args[0][0]
            assert "--disable-pip-version-check" in cmd_up
            assert "--no-warn-script-location" in cmd_up

            # Uninstall
            adapter.uninstall_package("requests")
            cmd_un = mock_run.call_args[0][0]
            assert "--disable-pip-version-check" in cmd_un

    def test_npm_adapter_fast_flags(self):
        """Npm adapter must use --no-audit and --no-fund to skip redundant network audits."""
        adapter = NpmAdapter()
        with patch("winget_updater.adapters.npm_adapter.silent_run") as mock_run, \
             patch("winget_updater.adapters.npm_adapter.silent_popen_stream") as mock_stream:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            mock_stream.return_value = (0, "added 1 package")

            # Install
            adapter.install_package("typescript")
            cmd_inst = mock_run.call_args[0][0]
            assert "--no-audit" in cmd_inst
            assert "--no-fund" in cmd_inst

            # Update
            item = ProgramItem(name="typescript", installed_version="5.3.0", latest_version="5.4.0", action=UpdateAction.AVAILABLE)
            adapter.install_update(item, log_callback=lambda l: None)
            cmd_up = mock_stream.call_args[0][0]
            assert "--no-audit" in cmd_up
            assert "--no-fund" in cmd_up

            # Uninstall
            adapter.uninstall_package("typescript")
            cmd_un = mock_run.call_args[0][0]
            assert "--no-audit" in cmd_un
            assert "--no-fund" in cmd_un

    def test_chocolatey_fast_flags(self):
        """Chocolatey adapter must include --no-progress to eliminate terminal rendering overhead."""
        adapter = ChocolateyAdapter()
        with patch("winget_updater.adapters.chocolatey_adapter.silent_run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            adapter.install_package("curl")
            cmd_inst = mock_run.call_args[0][0]
            assert "--no-progress" in cmd_inst

            adapter.uninstall_package("curl")
            cmd_un = mock_run.call_args[0][0]
            assert "--no-progress" in cmd_un
