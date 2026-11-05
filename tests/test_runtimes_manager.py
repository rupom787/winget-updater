"""Unit tests for the Gaming & System Runtimes Manager."""

from unittest.mock import MagicMock, patch
import pytest

from winget_updater.engine.runtimes import (
    RECOMMENDED_RUNTIMES,
    RuntimeCategory,
    RuntimeDefinition,
    RuntimesManager,
    RuntimeState,
)


@pytest.fixture
def mock_winget_client():
    client = MagicMock()
    client.install_package.return_value = (True, "Installed successfully")
    return client


def test_recommended_runtimes_matrix():
    """Validates that all essential runtimes are specified with valid winget package IDs."""
    assert len(RECOMMENDED_RUNTIMES) >= 12
    vcredist_items = [r for r in RECOMMENDED_RUNTIMES if r.category == RuntimeCategory.VCREDIST]
    assert len(vcredist_items) >= 8
    assert any("2015+.x64" in r.winget_id for r in vcredist_items)
    assert any("2015+.x86" in r.winget_id for r in vcredist_items)
    assert any("DirectX" in r.winget_id for r in RECOMMENDED_RUNTIMES)
    assert any("DotNet.DesktopRuntime.8" in r.winget_id for r in RECOMMENDED_RUNTIMES)


def test_scan_all_runtimes_with_mocked_registry(mock_winget_client):
    manager = RuntimesManager(winget_client=mock_winget_client)

    mock_entries = [
        ("Microsoft Visual C++ 2015-2022 Redistributable (x64) - 14.40.33810", "14.40.33810"),
        ("Microsoft Visual C++ 2013 Redistributable (x64) - 12.0.40664", "12.0.40664"),
    ]

    with patch.object(manager, "get_installed_registry_entries", return_value=mock_entries):
        with patch.object(manager, "get_dotnet_desktop_versions", return_value=["8.0.33"]):
            with patch("os.path.isfile", return_value=False):
                results = manager.scan_all_runtimes()

                assert len(results) == len(RECOMMENDED_RUNTIMES)
                vcredist_x64 = next(r for r in results if r.definition.id == "vcredist_2015_2022_x64")
                assert vcredist_x64.state == RuntimeState.INSTALLED
                assert vcredist_x64.installed_version == "14.40.33810"

                dotnet_8 = next(r for r in results if r.definition.id == "dotnet_desktop_8_x64")
                assert dotnet_8.state == RuntimeState.INSTALLED
                assert dotnet_8.installed_version == "8.0.33"

                dotnet_9 = next(r for r in results if r.definition.id == "dotnet_desktop_9_x64")
                assert dotnet_9.state == RuntimeState.MISSING
                assert dotnet_9.is_missing is True


def test_scan_all_runtimes_with_winget_upgrade(mock_winget_client):
    manager = RuntimesManager(winget_client=mock_winget_client)
    mock_entries = [
        ("Microsoft Visual C++ 2015-2022 Redistributable (x64) - 14.38.0", "14.38.0"),
    ]

    with patch.object(manager, "get_installed_registry_entries", return_value=mock_entries):
        with patch.object(manager, "get_dotnet_desktop_versions", return_value=[]):
            with patch("os.path.isfile", return_value=False):
                results = manager.scan_all_runtimes(
                    winget_upgrades={"microsoft.vcredist.2015+.x64": "14.51.36247"}
                )
                vcredist_x64 = next(r for r in results if r.definition.id == "vcredist_2015_2022_x64")
                assert vcredist_x64.state == RuntimeState.UPDATE_AVAILABLE
                assert vcredist_x64.is_upgradable is True
                assert vcredist_x64.latest_version == "14.51.36247"


def test_install_runtime_delegation(mock_winget_client):
    manager = RuntimesManager(winget_client=mock_winget_client)
    success, msg = manager.install_runtime("vcredist_2015_2022_x64")
    assert success is True
    mock_winget_client.install_package.assert_called_once_with(
        package_id="Microsoft.VCRedist.2015+.x64",
        dry_run=False,
        source="winget",
    )


def test_batch_install_missing(mock_winget_client):
    manager = RuntimesManager(winget_client=mock_winget_client)
    from winget_updater.engine.runtimes import RuntimeScanResult

    dummy_def_1 = RECOMMENDED_RUNTIMES[0]
    dummy_def_2 = RECOMMENDED_RUNTIMES[1]

    items = [
        RuntimeScanResult(definition=dummy_def_1, state=RuntimeState.MISSING, is_missing=True),
        RuntimeScanResult(definition=dummy_def_2, state=RuntimeState.INSTALLED, is_missing=False),
    ]

    progress_calls = []
    def on_progress(label, cur, tot):
        progress_calls.append((label, cur, tot))

    outcomes = manager.batch_install_missing(items, on_progress=on_progress)
    assert len(outcomes) == 1
    assert dummy_def_1.id in outcomes
    assert len(progress_calls) == 1

