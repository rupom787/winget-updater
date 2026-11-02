"""Unit tests for downgrade and newer-than-source handling."""

from unittest.mock import MagicMock
from winget_updater.config import ConfigManager
from winget_updater.engine.updater import UpdateEngine
from winget_updater.models import PackageType, ProgramItem, UpdateAction, UpdateOutcome
from winget_updater.winget.client import WingetClient, WingetPackageEntry
from winget_updater.winget.matcher import PackageMatcher


def test_newer_than_source_detection(tmp_path):
    config = ConfigManager(base_dir=tmp_path)
    matcher = PackageMatcher(config)

    upgrades = {
        "app.id": WingetPackageEntry(
            name="Custom App",
            id="app.id",
            version="1.0.0",
            available_version="1.5.0",  # Winget offers 1.5.0
            source="winget",
        )
    }
    installed = {}

    # Installed version is 2.0.0 (newer than winget's 1.5.0!)
    item = ProgramItem(
        name="Custom App",
        installed_version="2.0.0",
        id="app.id",
        package_type=PackageType.WIN32_EXE,
    )

    matcher.match_all([item], upgrades, installed)

    assert item.action == UpdateAction.NEWER_THAN_SOURCE
    assert item.outcome == UpdateOutcome.AWAITING_CONFIRMATION
    assert "newer than source version" in item.notes.lower()
    # Crucial safety check: can_auto_update MUST return False
    assert item.can_auto_update() is False


def test_batch_update_blocks_downgrade_automatically(tmp_path):
    mock_client = MagicMock(spec=WingetClient)
    mock_checker = MagicMock()
    mock_checker.check.return_value = MagicMock(is_compatible=True)

    engine = UpdateEngine(winget_client=mock_client, compatibility_checker=mock_checker)

    downgrade_item = ProgramItem(
        name="AppWithNewerLocalVersion",
        installed_version="3.0.0",
        latest_version="2.8.0",
        id="app.downgrade",
        action=UpdateAction.NEWER_THAN_SOURCE,
        outcome=UpdateOutcome.AWAITING_CONFIRMATION,
        package_type=PackageType.WIN32_EXE,
        is_verified_winget=True,
    )

    valid_item = ProgramItem(
        name="NormalApp",
        installed_version="1.0.0",
        latest_version="1.1.0",
        id="app.valid",
        action=UpdateAction.AVAILABLE,
        package_type=PackageType.WIN32_EXE,
        is_verified_winget=True,
    )

    mock_client.upgrade_package.return_value = (True, "Updated")

    summary = engine.execute_batch_update([downgrade_item, valid_item])

    # Only NormalApp was upgraded
    assert summary.updated_count == 1
    assert summary.downgrade_blocked_count == 1
    assert downgrade_item.outcome == UpdateOutcome.AWAITING_CONFIRMATION
    # Winget upgrade was only called once, for the valid app, never for the downgrade app!
    mock_client.upgrade_package.assert_called_once_with("app.valid", dry_run=False)

