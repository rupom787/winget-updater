"""Unit tests for the App Update Tracker engine and UI dashboard."""

import json
from pathlib import Path
import tkinter as tk
import pytest
from winget_updater.engine.tracker import TrackedAppUpdate, UpdateTracker
from winget_updater.gui.dialogs import AppUpdateTrackerDialog
from winget_updater.gui.theme import get_theme
from winget_updater.models import PackageType, ProgramItem, UpdateAction


@pytest.fixture
def temp_tracker(tmp_path):
    storage_file = tmp_path / "test_tracker.json"
    tracker = UpdateTracker(storage_path=storage_file)
    return tracker


def test_tracker_initialization(temp_tracker):
    assert temp_tracker.tracked_updates == {}
    metrics = temp_tracker.get_metrics()
    assert metrics["total_tracked"] == 0
    assert metrics["pending_count"] == 0


def test_track_scan_results_adds_available_updates(temp_tracker):
    item1 = ProgramItem(
        name="Node.js",
        id="OpenJS.NodeJS",
        installed_version="20.10.0",
        latest_version="22.2.0",
        package_type=PackageType.WIN32_EXE,
        source="winget",
        action=UpdateAction.AVAILABLE,
    )
    item2 = ProgramItem(
        name="Python",
        id="Python.Python.3.11",
        installed_version="3.11.0",
        latest_version="3.11.0",
        package_type=PackageType.WIN32_EXE,
        source="winget",
        action=UpdateAction.UP_TO_DATE,
    )

    res = temp_tracker.track_scan_results([item1, item2])
    assert res["new_tracked"] == 1
    assert res["total_pending"] == 1

    tracked = temp_tracker.get_tracked_items()
    assert len(tracked) == 1
    assert tracked[0].name == "Node.js"
    assert tracked[0].installed_version == "20.10.0"
    assert tracked[0].available_version == "22.2.0"
    assert tracked[0].status == "available"
    assert len(tracked[0].history) == 1


def test_track_scan_results_advances_version(temp_tracker):
    item = ProgramItem(
        name="npm",
        id="npm:npm",
        installed_version="11.20.0",
        latest_version="12.0.0",
        package_type=PackageType.NPM,
        source="npm",
        action=UpdateAction.AVAILABLE,
    )
    temp_tracker.track_scan_results([item])

    # Now version advances to 12.2.1
    item.latest_version = "12.2.1"
    res = temp_tracker.track_scan_results([item])
    assert res["updated_tracked"] == 1

    tracked = temp_tracker.get_tracked_items()
    assert len(tracked) == 1
    assert tracked[0].available_version == "12.2.1"
    assert len(tracked[0].history) == 2
    assert tracked[0].history[-1]["event"] == "version_advanced"


def test_track_scan_results_resolves_when_installed(temp_tracker):
    item = ProgramItem(
        name="Git",
        id="Git.Git",
        installed_version="2.40.0",
        latest_version="2.42.0",
        package_type=PackageType.WIN32_EXE,
        source="winget",
        action=UpdateAction.AVAILABLE,
    )
    temp_tracker.track_scan_results([item])
    assert temp_tracker.get_metrics()["pending_count"] == 1

    # App is now updated
    item.installed_version = "2.42.0"
    item.action = UpdateAction.UP_TO_DATE
    temp_tracker.track_scan_results([item])

    metrics = temp_tracker.get_metrics()
    assert metrics["pending_count"] == 0
    assert metrics["updated_count"] == 1


def test_record_update_attempt_success_and_failure(temp_tracker):
    item = ProgramItem(
        name="Chrome",
        id="Google.Chrome",
        installed_version="120.0",
        latest_version="121.0",
        package_type=PackageType.WIN32_EXE,
        source="winget",
        action=UpdateAction.AVAILABLE,
    )
    temp_tracker.track_scan_results([item])

    # Record failure
    temp_tracker.record_update_attempt("Google.Chrome", False, "120.0", "Locked by chrome.exe")
    tracked = temp_tracker.get_tracked_items()[0]
    assert tracked.status == "failed"
    assert "chrome.exe" in tracked.history[-1]["details"]

    # Record subsequent success
    temp_tracker.record_update_attempt("Google.Chrome", True, "121.0", "Updated successfully")
    tracked = temp_tracker.get_tracked_items()[0]
    assert tracked.status == "updated"
    assert tracked.installed_version == "121.0"


def test_clear_resolved_and_metrics(temp_tracker):
    item = ProgramItem(
        name="TestApp",
        id="test:app",
        installed_version="1.0.0",
        latest_version="2.0.0",
        package_type=PackageType.PIP,
        source="pip",
        action=UpdateAction.AVAILABLE,
    )
    temp_tracker.track_scan_results([item])
    temp_tracker.record_update_attempt("test:app", True, "2.0.0", "Success")

    assert temp_tracker.get_metrics()["updated_count"] == 1
    cleared = temp_tracker.clear_resolved()
    assert cleared == 1
    assert temp_tracker.get_metrics()["total_tracked"] == 0


def test_update_tracker_dialog_ui(temp_tracker):
    """Verifies AppUpdateTrackerDialog renders without crashing."""
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception:
        pytest.skip("Tkinter display not available")

    try:
        item = ProgramItem(
            name="SampleApp",
            id="Sample.App",
            installed_version="1.0.0",
            latest_version="1.1.0",
            package_type=PackageType.WIN32_EXE,
            source="winget",
            action=UpdateAction.AVAILABLE,
        )
        temp_tracker.track_scan_results([item])

        dlg = AppUpdateTrackerDialog(root, tracker=temp_tracker, theme=get_theme("light"))
        assert dlg.tree is not None
        assert len(dlg.tree.get_children()) == 1

        # Test filter switching
        dlg._set_filter("available")
        assert len(dlg.tree.get_children()) == 1

        dlg._set_filter("updated")
        assert len(dlg.tree.get_children()) == 0

        dlg._set_filter("all")
        assert len(dlg.tree.get_children()) == 1
    finally:
        dlg.destroy()
        root.destroy()

