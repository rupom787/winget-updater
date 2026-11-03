"""Unit and UI animation tests for LiveUpdateProgressDialog and subprocess streaming."""

import sys
import time
import tkinter as tk
from typing import List
import pytest
from winget_updater.gui.live_update_modal import LiveUpdateProgressDialog
from winget_updater.gui.theme import get_theme
from winget_updater.models import PackageType, ProgramItem, UpdateAction, UpdateOutcome
from winget_updater.utils.process import silent_popen_stream


def _make_sample_items() -> List[ProgramItem]:
    return [
        ProgramItem(
            name="Google Chrome",
            id="Google.Chrome",
            installed_version="120.0.6099.130",
            latest_version="121.0.6167.85",
            package_type=PackageType.WIN32_EXE,
            source="winget",
            action=UpdateAction.AVAILABLE,
            is_verified_winget=True,
        ),
        ProgramItem(
            name="Git",
            id="Git.Git",
            installed_version="2.42.0",
            latest_version="2.43.0",
            package_type=PackageType.WIN32_EXE,
            source="winget",
            action=UpdateAction.AVAILABLE,
            is_verified_winget=True,
        ),
        ProgramItem(
            name="requests",
            id="pip:requests",
            installed_version="2.31.0",
            latest_version="2.32.3",
            package_type=PackageType.PIP,
            source="pip",
            action=UpdateAction.AVAILABLE,
            is_verified_winget=True,
        ),
    ]


def test_silent_popen_stream_captures_lines():
    """Verifies silent_popen_stream runs silently, captures stdout lines, and returns returncode."""
    received_lines = []

    def on_line(line: str):
        received_lines.append(line)

    cmd = [
        sys.executable,
        "-c",
        "import sys, time; print('Line 1'); sys.stdout.flush(); print('Line 2'); sys.stdout.flush()",
    ]
    ret, full_out = silent_popen_stream(cmd, line_callback=on_line, timeout=10)

    assert ret == 0
    assert len(received_lines) == 2
    assert "Line 1" in received_lines[0]
    assert "Line 2" in received_lines[1]
    assert "Line 1" in full_out
    assert "Line 2" in full_out


def test_live_update_modal_initialization():
    """Verifies LiveUpdateProgressDialog instantiates correctly with all sections and queue rows."""
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception:
        pytest.skip("Tkinter display unavailable in test environment")

    items = _make_sample_items()
    dlg = LiveUpdateProgressDialog(root, items, theme=get_theme("light"))

    try:
        assert dlg.total_count == 3
        assert dlg.completed_count == 0
        assert dlg.succeeded_count == 0
        assert dlg.failed_count == 0
        assert not dlg.is_finished

        # Check queue checklist rows created
        assert len(dlg.item_row_widgets) == 3
        assert "Google.Chrome" in dlg.item_row_widgets
        assert "Git.Git" in dlg.item_row_widgets
        assert "pip:requests" in dlg.item_row_widgets

        # Check widgets existence
        assert dlg.header_canvas is not None
        assert dlg.bar_canvas is not None
        assert dlg.spotlight_card is not None
        assert dlg.terminal_text is not None
        assert dlg.btn_background is not None
        assert dlg.btn_cancel is not None
    finally:
        dlg.destroy()
        root.destroy()


def test_live_update_modal_lifecycle_and_drain():
    """Tests the full event pump cycle: start item -> log line -> complete item -> queue finished."""
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception:
        pytest.skip("Tkinter display unavailable in test environment")

    items = _make_sample_items()
    bg_called = []
    summary_called = []

    dlg = LiveUpdateProgressDialog(
        root,
        items,
        theme=get_theme("dark"),
        on_run_in_background=lambda: bg_called.append(True),
        on_complete_view_summary=lambda: summary_called.append(True),
    )

    try:
        item1 = items[0]
        dlg.notify_package_started(item1, 1, 3)
        dlg.notify_package_log(item1, "Downloading https://dl.google.com/chrome.msi")
        dlg.notify_package_log(item1, "SHA256 hash verified successfully")
        dlg.notify_package_log(item1, "Starting package install...")
        dlg.notify_package_completed(item1, True, "Updated successfully")

        # Pump queued UI messages
        dlg._drain_ui_queue()

        assert dlg.current_item == item1
        assert dlg.completed_count == 1
        assert dlg.succeeded_count == 1
        assert dlg.failed_count == 0
        assert "Google Chrome" in dlg.lbl_active_name.cget("text")
        assert "Succeeded" in dlg.item_row_widgets["Google.Chrome"]["status"].cget("text")
        assert "SHA256" in dlg.terminal_text.get("1.0", tk.END)

        # Fail item 2
        item2 = items[1]
        dlg.notify_package_started(item2, 2, 3)
        dlg.notify_package_log(item2, "Error 1618: Another installation is in progress")
        dlg.notify_package_completed(item2, False, "Error 1618")

        dlg._drain_ui_queue()
        assert dlg.completed_count == 2
        assert dlg.succeeded_count == 1
        assert dlg.failed_count == 1
        assert "Failed" in dlg.item_row_widgets["Git.Git"]["status"].cget("text")

        # Finish queue
        dlg.notify_queue_finished(None)
        dlg._drain_ui_queue()
        dlg.update()

        assert dlg.is_finished
        assert dlg.target_progress_pct == 100.0
        assert dlg.btn_complete_view.winfo_manager() == "pack"
        assert dlg.btn_cancel.winfo_manager() == ""

        # Test animation tick does not crash
        dlg._animation_tick()
    finally:
        dlg.destroy()
        root.destroy()


def test_live_update_modal_background_and_cancel():
    """Verifies background toggle, cancel request, and terminal visibility toggle."""
    try:
        root = tk.Tk()
        root.withdraw()
    except Exception:
        pytest.skip("Tkinter display unavailable in test environment")

    items = _make_sample_items()
    cancel_called = []
    bg_called = []

    dlg = LiveUpdateProgressDialog(
        root,
        items,
        theme=get_theme("light"),
        on_run_in_background=lambda: bg_called.append(True),
        on_cancel_queue=lambda: cancel_called.append(True),
    )

    try:
        # Test background minimization
        dlg.minimize_to_background()
        assert dlg.is_minimized_background
        assert len(bg_called) == 1

        # Test restore
        dlg.restore_from_background()
        assert not dlg.is_minimized_background

        # Test cancel click
        dlg._handle_cancel_click()
        assert dlg.cancel_requested
        assert len(cancel_called) == 1
        assert "Cancelling" in dlg.btn_cancel.cget("text")

        # Test terminal toggle
        assert dlg.terminal_frame.winfo_manager() == "pack"
        dlg._toggle_terminal_visibility()
        assert dlg.terminal_frame.winfo_manager() == ""
        dlg._toggle_terminal_visibility()
        assert dlg.terminal_frame.winfo_manager() == "pack"
    finally:
        dlg.destroy()
        root.destroy()
