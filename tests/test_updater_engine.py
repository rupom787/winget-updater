"""Unit tests for the update execution engine, dry-run mode, and per-app elevation notices."""

from pathlib import Path
from unittest.mock import MagicMock, patch
from winget_updater.engine.updater import UpdateEngine
from winget_updater.models import CompatibilityStatus, PackageType, ProgramItem, UpdateAction, UpdateOutcome
from winget_updater.winget.client import WingetClient
from winget_updater.winget.verifier import PackageVerifier


def test_dry_run_simulation_mode():
    mock_client = MagicMock(spec=WingetClient)
    mock_checker = MagicMock()
    mock_checker.check.return_value = MagicMock(is_compatible=True)

    engine = UpdateEngine(winget_client=mock_client, compatibility_checker=mock_checker)

    item = ProgramItem(
        name="7-Zip",
        installed_version="23.01",
        latest_version="24.05",
        id="7zip.7zip",
        action=UpdateAction.AVAILABLE,
        package_type=PackageType.WIN32_EXE,
        is_verified_winget=True,
    )

    summary = engine.execute_batch_update([item], dry_run=True)

    assert summary.simulated_count == 1
    assert summary.updated_count == 0
    assert item.outcome == UpdateOutcome.SIMULATED
    # WingetClient was called with dry_run=True
    mock_client.upgrade_package.assert_not_called()  # When dry_run, updater engine marks simulated directly without invoking real binary


def test_per_app_elevation_warning_callback():
    mock_client = MagicMock(spec=WingetClient)
    mock_client.upgrade_package.return_value = (True, "Upgraded")
    mock_checker = MagicMock()
    mock_checker.check.return_value = MagicMock(is_compatible=True)

    engine = UpdateEngine(winget_client=mock_client, compatibility_checker=mock_checker)

    item = ProgramItem(
        name="VLC media player",
        installed_version="3.0.18",
        latest_version="3.0.20",
        id="VideoLAN.VLC",
        action=UpdateAction.AVAILABLE,
        package_type=PackageType.WIN32_EXE,
        is_verified_winget=True,
    )

    warning_events = []

    def on_warn(p: ProgramItem):
        warning_events.append(p.name)

    summary = engine.execute_batch_update([item], elevation_warning_callback=on_warn)

    assert summary.updated_count == 1
    assert len(warning_events) == 1
    assert warning_events[0] == "VLC media player"


def test_failure_isolation_per_package():
    mock_client = MagicMock(spec=WingetClient)
    # First app fails, second app succeeds
    mock_client.upgrade_package.side_effect = [
        (False, "Hash mismatch / corrupted download"),
        (True, "Success"),
    ]
    mock_checker = MagicMock()
    mock_checker.check.return_value = MagicMock(is_compatible=True)

    engine = UpdateEngine(winget_client=mock_client, compatibility_checker=mock_checker)

    item1 = ProgramItem(
        name="FailingApp",
        id="app.fail",
        action=UpdateAction.AVAILABLE,
        package_type=PackageType.WIN32_EXE,
        is_verified_winget=True,
    )
    item2 = ProgramItem(
        name="SucceedingApp",
        id="app.success",
        action=UpdateAction.AVAILABLE,
        package_type=PackageType.WIN32_EXE,
        is_verified_winget=True,
    )

    summary = engine.execute_batch_update([item1, item2])

    assert summary.failed_count == 1
    assert summary.updated_count == 1
    assert item1.outcome == UpdateOutcome.FAILED
    assert item2.outcome == UpdateOutcome.UPDATED


def test_vendor_fallback_signature_rejection(tmp_path):
    mock_client = MagicMock(spec=WingetClient)
    engine = UpdateEngine(winget_client=mock_client)

    item = ProgramItem(
        name="UntrustedApp",
        package_type=PackageType.WIN32_EXE,
        action=UpdateAction.VENDOR_FALLBACK,
        vendor_installer_url="https://example.com/untrusted.exe",
        vendor_installer_hash="abcdef",
    )

    with patch("urllib.request.urlretrieve"), \
         patch("winget_updater.winget.verifier.PackageVerifier.verify_file_hash", return_value=(False, "SHA-256 mismatch")):
        success, msg = engine.execute_vendor_installer(item)
        assert success is False
        assert "verification failed" in msg.lower()

