"""Tests verifying that all buttons and text labels accurately match their actual actions and state."""

import tkinter as tk
from unittest.mock import MagicMock
import pytest

from winget_updater.gui.components import DetailsDrawer, FloatingGlassBatchDock
from winget_updater.gui.dialogs import ScheduleConfigDialog
from winget_updater.gui.live_update_modal import LiveUpdateProgressDialog
from winget_updater.gui.theme import LIGHT_THEME
from winget_updater.models import (
    CompatibilityDetails,
    CompatibilityStatus,
    PackageType,
    ProgramItem,
    UpdateAction,
)


@pytest.fixture
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    try:
        r.destroy()
    except Exception:
        pass


def make_test_item(name="TestApp", action=UpdateAction.AVAILABLE, is_pinned=False, is_skipped=False):
    it = ProgramItem(
        id=f"Vendor.{name}",
        name=name,
        installed_version="1.0.0",
        latest_version="2.0.0",
        source="winget",
        package_type=PackageType.WIN32_EXE,
        action=action,
        is_pinned=is_pinned,
        is_verified_winget=True,
        compatibility=CompatibilityDetails(CompatibilityStatus.COMPATIBLE),
    )
    if is_skipped:
        it.action = UpdateAction.SKIPPED_VERSION
    return it


def test_details_drawer_button_text_accuracy(root):
    drawer = DetailsDrawer(root)

    # 1. Update available
    item_avail = make_test_item(action=UpdateAction.AVAILABLE)
    drawer.set_item(item_avail)
    assert drawer.btn_update.text == "Update application"
    assert drawer.btn_exclude.text == "Exclude"
    assert drawer.btn_pin.text == "📌 Pin"
    assert drawer.btn_skip.text == "⏭️ Skip"

    # 2. Up to date
    item_up = make_test_item(action=UpdateAction.UP_TO_DATE)
    item_up.latest_version = "1.0.0"
    drawer.set_item(item_up)
    assert drawer.btn_update.text == "Up to date"
    assert drawer.btn_update._state == "disabled"

    # 3. Pinned to version
    item_pinned = make_test_item(action=UpdateAction.PINNED, is_pinned=True)
    drawer.set_item(item_pinned)
    assert drawer.btn_update.text == "Pinned to version"
    assert drawer.btn_pin.text == "Unpin"

    # 4. Excluded
    item_excl = make_test_item(action=UpdateAction.EXCLUDED)
    drawer.set_item(item_excl)
    assert drawer.btn_update.text == "Excluded from updates"
    assert drawer.btn_exclude.text == "Un-exclude"

    # 5. Skipped version
    item_skip = make_test_item(action=UpdateAction.SKIPPED_VERSION, is_skipped=True)
    drawer.set_item(item_skip)
    assert drawer.btn_update.text == "Version skipped"
    assert drawer.btn_skip.text == "Unskip"


def test_floating_batch_dock_pin_text(root):
    dock = FloatingGlassBatchDock(root)

    it1 = make_test_item("App1", is_pinned=True)
    it2 = make_test_item("App2", is_pinned=True)
    dock.set_selected_items([it1, it2])
    assert "Unpin (2)" in dock.btn_pin.text

    it3 = make_test_item("App3", is_pinned=False)
    dock.set_selected_items([it1, it3])
    assert "Pin (2)" in dock.btn_pin.text


def test_schedule_dialog_button_label(root):
    mock_scheduler = MagicMock()

    # Case A: Schedule already active -> button should say Update
    mock_scheduler.is_task_scheduled.return_value = (True, "Runs daily at 03:00")
    dlg = ScheduleConfigDialog(root, mock_scheduler)
    assert dlg.btn_save.text == "Update Schedule Time"
    dlg.destroy()

    # Case B: Schedule inactive -> button should say Enable
    mock_scheduler.is_task_scheduled.return_value = (False, "")
    dlg2 = ScheduleConfigDialog(root, mock_scheduler)
    assert dlg2.btn_save.text == "Enable Daily Schedule"
    dlg2.destroy()


def test_live_update_modal_completion_buttons(root):
    items = [make_test_item("App1"), make_test_item("App2")]
    modal = LiveUpdateProgressDialog(root, items, theme=LIGHT_THEME)

    # All succeeded -> Done
    modal.succeeded_count = 2
    modal.failed_count = 0
    modal._on_ui_queue_done(MagicMock())
    assert modal.btn_complete_view.cget("text") == "✓ Done"

    # Some failed -> Close (with warnings)
    modal.succeeded_count = 1
    modal.failed_count = 1
    modal._on_ui_queue_done(MagicMock())
    assert modal.btn_complete_view.cget("text") == "Close (with warnings)"

    # All failed -> Close
    modal.succeeded_count = 0
    modal.failed_count = 2
    modal._on_ui_queue_done(MagicMock())
    assert modal.btn_complete_view.cget("text") == "✕ Close"

    modal.destroy()


def test_sidebar_filter_titles_and_pills(root, monkeypatch):
    from winget_updater.gui.app import MainWindow
    from winget_updater.config import ConfigManager

    monkeypatch.setattr(MainWindow, "_on_ready_startup", lambda self: None)
    app = MainWindow(config_manager=ConfigManager())
    app.withdraw()

    try:
        # Test 1: Title mappings match sidebar options
        expected_titles = {
            "All Software": "All Applications",
            "Updates Available": "Updates Available",
            "Cannot Update": "Review & Issues",
            "Up to Date": "Installed & Current Applications",
            "Ignored Updates": "Excluded Applications",
            "Software Catalog": "Discover & Install Packages",
        }
        for filter_key, expected_title in expected_titles.items():
            app._on_sidebar_filter_changed(filter_key)
            assert app.lbl_view_title.cget("text") == expected_title

        # Test 2: Top bar button labels
        assert app.btn_restore.text in ("Restore", "Restore Backup")
        assert app.btn_backup.text in ("Backup", "Backup Apps")
        assert app.btn_sources.text in ("Sources", "Refresh Sources")
        assert app.btn_export.text in ("Export", "Export Inventory")

        # Test 3: Action deck label
        assert app.lbl_action_deck.cget("text") == "ACTIONS"

        # Test 4: Right sidebar mini pill states and dynamic text
        app._on_sidebar_filter_changed("All Software")
        it_up = make_test_item("AppUp", action=UpdateAction.UP_TO_DATE)
        app._on_row_selected(it_up)
        assert app.btn_update_selected.text == "Up to date"
        assert app.btn_update_selected._state == "disabled"
        assert app.p_btn_update.text == "Up to Date"
        assert app.p_btn_update._state == "disabled"

        it_pinned = make_test_item("AppPin", action=UpdateAction.PINNED, is_pinned=True)
        app._on_row_selected(it_pinned)
        assert app.btn_update_selected.text == "Pinned to version"
        assert app.p_btn_pin.text == "Unpin"

        it_excl = make_test_item("AppExcl", action=UpdateAction.EXCLUDED)
        app._on_row_selected(it_excl)
        assert app.btn_update_selected.text == "Excluded"
        assert app.p_btn_exclude.text == "Un-exclude"

    finally:
        app.destroy()

