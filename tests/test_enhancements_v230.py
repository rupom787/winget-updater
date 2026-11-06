"""Unit tests for v2.3.0 enhancements: Disk Cleanup, Startup Manager, and Report Generator."""

import os
from unittest.mock import MagicMock, patch
from winget_updater.engine.cleanup import DiskCleanupManager
from winget_updater.engine.startup import StartupItem, StartupManager
from winget_updater.engine.reports import ReportGenerator
from winget_updater.models import ProgramItem, UpdateAction


def test_cleanup_scan_and_purge(tmp_path):
    fake_temp = tmp_path / "fake_winget"
    fake_temp.mkdir(parents=True)
    f1 = fake_temp / "installer.msi"
    f1.write_bytes(b"A" * 1024)  # 1 KB

    fake_targets = [
        {
            "id": "test_target",
            "name": "Test Cache",
            "description": "Test cache description",
            "paths": [str(fake_temp)],
            "safe": True,
        }
    ]

    with patch.object(DiskCleanupManager, "get_cleanup_targets", return_value=fake_targets):
        scanned = DiskCleanupManager.scan_targets()
        assert len(scanned) == 1
        assert scanned[0]["files_count"] == 1
        assert scanned[0]["bytes"] == 1024

        res = DiskCleanupManager.purge_targets(["test_target"])
        assert res["freed_bytes"] == 1024
        assert res["removed_files"] == 1
        assert not f1.exists()


def test_startup_clean_path_extractor():
    assert StartupManager._extract_clean_path('"C:\\Program Files\\App\\app.exe" --silent') == "C:\\Program Files\\App\\app.exe"
    assert StartupManager._extract_clean_path("C:\\App\\tool.exe -background") == "C:\\App\\tool.exe"
    assert StartupManager._extract_clean_path("") == ""


def test_startup_item_to_dict():
    it = StartupItem(
        name="TestApp",
        command="test.exe",
        clean_path="C:\\test.exe",
        source="Registry (Current User)",
        hive="HKCU",
        enabled=True,
        exists=False,
    )
    d = it.to_dict()
    assert d["name"] == "TestApp"
    assert d["enabled"] is True
    assert d["exists"] is False


def test_report_generator_html():
    p1 = ProgramItem(
        name="Chrome",
        installed_version="120.0",
        latest_version="121.0",
        action=UpdateAction.AVAILABLE,
        id="Google.Chrome",
        source="WINGET",
    )
    p2 = ProgramItem(
        name="Git",
        installed_version="2.43.0",
        latest_version="2.43.0",
        action=UpdateAction.UP_TO_DATE,
        id="Git.Git",
        source="WINGET",
    )

    html = ReportGenerator.generate_html_report([p1, p2], app_version="2.3.0")
    assert "Google.Chrome" in html
    assert "Git.Git" in html
    assert "v2.3.0" in html
    assert "Software Inventory &amp; System Audit" in html


def test_report_generator_batch_and_ps1():
    p1 = ProgramItem(
        name="VLC",
        installed_version="3.0.18",
        latest_version="3.0.20",
        action=UpdateAction.AVAILABLE,
        id="VideoLAN.VLC",
        source="WINGET",
    )

    bat = ReportGenerator.generate_batch_script([p1])
    assert "winget install --id \"VideoLAN.VLC\" -e --silent" in bat

    ps1 = ReportGenerator.generate_ps1_script([p1])
    assert "'VideoLAN.VLC'" in ps1
    assert "winget install --id $pkg -e --silent" in ps1

