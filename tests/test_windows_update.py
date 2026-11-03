"""Unit tests for Windows Update manager, reboot detection, and OEM companion mapping."""

import winreg
from unittest.mock import MagicMock, patch
from winget_updater.engine.windows_update import (
    OemCompanionInfo,
    WindowsUpdateItem,
    WindowsUpdateManager,
)


def test_oem_companion_mapping_asus():
    with patch("winreg.OpenKey") as mock_open:
        with patch("winreg.QueryValueEx") as mock_query:
            mock_query.side_effect = [("ASUSTeK COMPUTER INC.", 1), ("TUF Gaming A15", 1)]
            info = WindowsUpdateManager.get_oem_info()
            assert "ASUS" in info.manufacturer.upper()
            assert "MyASUS" in info.companion_name
            assert "9NBLGGH51628" in info.store_uri


def test_oem_companion_mapping_lenovo():
    with patch("winreg.OpenKey") as mock_open:
        with patch("winreg.QueryValueEx") as mock_query:
            mock_query.side_effect = [("LENOVO", 1), ("ThinkPad X1 Carbon", 1)]
            info = WindowsUpdateManager.get_oem_info()
            assert "LENOVO" in info.manufacturer.upper()
            assert "Lenovo Vantage" in info.companion_name
            assert "9WZDNCRFJ4MV" in info.store_uri


def test_oem_companion_mapping_dell():
    with patch("winreg.OpenKey") as mock_open:
        with patch("winreg.QueryValueEx") as mock_query:
            mock_query.side_effect = [("Dell Inc.", 1), ("XPS 15 9520", 1)]
            info = WindowsUpdateManager.get_oem_info()
            assert "DELL" in info.manufacturer.upper()
            assert "Dell SupportAssist" in info.companion_name
            assert "9NM7CT8SSB5Q" in info.store_uri


def test_is_reboot_pending_logic():
    # Test on host system
    is_pending, reason = WindowsUpdateManager.is_reboot_pending()
    assert isinstance(is_pending, bool)
    assert isinstance(reason, str)


def test_windows_update_item_model():
    item = WindowsUpdateItem(
        title="2026-10 Cumulative Update for Windows 11 Version 24H2 (KB5044284)",
        kb_id="KB5044284",
        size_mb=684.2,
        severity="Critical",
        is_driver=False,
    )
    assert item.kb_id == "KB5044284"
    assert item.size_mb == 684.2
    assert item.is_mandatory is True
