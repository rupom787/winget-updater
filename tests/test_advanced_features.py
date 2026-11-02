"""Unit tests for advanced updater features inspired by Patch My PC analysis:
- Running Process Lock Detection and Termination
- System Restore Point Creation
- Post-Update Disk and Cache Cleanup
- Package Uninstallation and Catalog Search
"""

import os
from unittest.mock import MagicMock, patch
from winget_updater.engine.cleanup import DiskCleanupManager
from winget_updater.engine.process_lock import ProcessLockDetector
from winget_updater.engine.restore_point import RestorePointManager
from winget_updater.models import PackageType, ProgramItem, UpdateAction
from winget_updater.winget.client import WingetClient


def test_process_lock_detection():
    # Mock tasklist output
    sample_csv = (
        '"chrome.exe","1234","Console","1","100,000 K"\n'
        '"vlc.exe","5678","Console","1","50,000 K"\n'
        '"notepad.exe","9999","Console","1","10,000 K"\n'
    )
    with patch("winget_updater.engine.process_lock.silent_run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=sample_csv)
        procs = ProcessLockDetector.get_all_running_processes()
        assert len(procs) == 3
        assert (1234, "chrome.exe") in procs
        assert (5678, "vlc.exe") in procs

        # Test finding processes for Chrome item
        item_chrome = ProgramItem(name="Google Chrome", id="Google.Chrome")
        locked = ProcessLockDetector.find_running_processes_for_item(item_chrome)
        assert len(locked) == 1
        assert locked[0] == (1234, "chrome.exe")

        # Test item without running process
        item_git = ProgramItem(name="Git", id="Git.Git")
        locked_git = ProcessLockDetector.find_running_processes_for_item(item_git)
        assert len(locked_git) == 0


def test_process_termination():
    with patch("winget_updater.engine.process_lock.silent_run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="SUCCESS", stderr="")
        success, msg = ProcessLockDetector.terminate_processes([1234], force=False)
        assert success is True
        mock_run.assert_called_once_with(["taskkill", "/PID", "1234"], capture_output=True, text=True, timeout=10)


def test_system_restore_point_manager():
    with patch("winget_updater.engine.restore_point.silent_run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        success, msg = RestorePointManager.create_restore_point("Pre-Update Snapshot")
        assert success is True
        assert "successfully" in msg.lower()


def test_disk_cleanup_manager(tmp_path):
    # Create fake vendor temp directory
    vendor_temp = tmp_path / "winget_updater_vendor"
    vendor_temp.mkdir()
    fake_file = vendor_temp / "temp_installer.exe"
    fake_file.write_bytes(b"A" * 1024)  # 1 KB

    with patch("tempfile.gettempdir", return_value=str(tmp_path)):
        with patch("winget_updater.engine.cleanup.silent_run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            freed, msg = DiskCleanupManager.cleanup_temp_and_cache()
            assert freed >= 1024
            assert "Cleaned" in msg


def test_winget_client_uninstall_and_install():
    client = WingetClient()

    with patch("winget_updater.winget.client.silent_run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Successfully uninstalled", stderr="")
        success, msg = client.uninstall_package("Git.Git")
        assert success is True

    with patch("winget_updater.winget.client.silent_run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="Successfully installed", stderr="")
        success, msg = client.install_package("Git.Git")
        assert success is True


def test_winget_catalog_search():
    client = WingetClient()
    sample_table = (
        "Name               Id           Version   Source\n"
        "-------------------------------------------------\n"
        "VLC media player   VideoLAN.VLC 3.0.21    winget\n"
        "7-Zip              7zip.7zip    24.05     winget\n"
    )
    with patch("winget_updater.winget.client.silent_run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout=sample_table, stderr="")
        results = client.search_packages("vlc")
        assert len(results) >= 1
        assert any(r.id == "VideoLAN.VLC" for r in results)


def test_gpu_acceleration_manager():
    from winget_updater.engine.gpu import GpuAccelerationManager

    gpus = GpuAccelerationManager.detect_gpus()
    assert len(gpus) >= 1
    assert any(g.status in ("Active", "OK") for g in gpus)

    primary = GpuAccelerationManager.get_primary_gpu()
    assert primary is not None
    assert len(primary.name) > 0
    assert "DirectX" in primary.display_text or primary.vram_mb >= 0

    ok, msg = GpuAccelerationManager.enable_high_performance_gpu()
    assert ok is True
    assert "GPU" in msg


def test_version_pinning_and_skipping(tmp_path):
    from winget_updater.config import ConfigManager
    from winget_updater.models import ProgramItem, UpdateAction
    from winget_updater.winget.client import WingetPackageEntry
    from winget_updater.winget.matcher import PackageMatcher

    cfg = ConfigManager(base_dir=tmp_path)
    cfg.pin_package("Git", "2.44.0")
    cfg.skip_version("VLC media player", "3.0.24")

    matcher = PackageMatcher(cfg)

    upgrades = {
        "git.git": WingetPackageEntry(name="Git", id="Git.Git", version="2.44.0", available_version="2.45.0", source="winget"),
        "videolan.vlc": WingetPackageEntry(name="VLC media player", id="VideoLAN.VLC", version="3.0.21", available_version="3.0.24", source="winget"),
    }
    installed = {}

    items = [
        ProgramItem(name="Git", installed_version="2.44.0", id="Git.Git"),
        ProgramItem(name="VLC media player", installed_version="3.0.21", id="VideoLAN.VLC"),
    ]

    matched = matcher.match_all(items, upgrades, installed)

    # Git should be PINNED
    assert matched[0].action == UpdateAction.PINNED
    assert matched[0].is_pinned is True
    assert matched[0].pinned_version == "2.44.0"

    # VLC should be SKIPPED_VERSION because 3.0.24 was skipped
    assert matched[1].action == UpdateAction.SKIPPED_VERSION
    assert matched[1].skipped_version == "3.0.24"


def test_software_manifest_export_import(tmp_path):
    client = WingetClient()
    export_file = tmp_path / "test_backup.json"

    with patch("winget_updater.winget.client.silent_run") as mock_run:
        # Simulate successful export creating the file
        def side_effect(cmd, **kwargs):
            if "export" in cmd:
                export_file.write_text('{"CreationDate": "2026-11-02"}')
                return MagicMock(returncode=0, stdout="Export complete", stderr="")
            if "import" in cmd:
                return MagicMock(returncode=0, stdout="Import complete", stderr="")
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect

        success, msg = client.export_software_manifest(str(export_file))
        assert success is True
        assert export_file.exists()

        success, msg = client.import_software_manifest(str(export_file))
        assert success is True
        assert "successfully" in msg



