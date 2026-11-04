"""Unit tests verifying top bar simplification and expanded Settings options."""

import tkinter as tk
from unittest.mock import MagicMock
import pytest

from winget_updater.config import ConfigManager
from winget_updater.gui.app import MainWindow
from winget_updater.gui.dialogs import SettingsDialog
from winget_updater.gui.theme import LIGHT_THEME


@pytest.fixture
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def test_top_bar_is_simplified(monkeypatch):
    """Verifies that the top bar is uncluttered and only packs essential controls."""
    monkeypatch.setattr(MainWindow, "_on_ready_startup", lambda self: None)
    app = MainWindow(config_manager=ConfigManager())
    app.withdraw()

    try:
        # Check children packed in top_controls
        packed_children = app.top_controls.pack_slaves()
        # Should only contain Settings button and Theme switch box
        assert len(packed_children) == 2
        assert app.btn_settings in packed_children
        assert app.theme_box in packed_children

        # Secondary options are preserved on self but NOT packed in top_controls
        assert app.btn_restore not in packed_children
        assert app.btn_backup not in packed_children
        assert app.btn_sources not in packed_children
        assert app.btn_exclusions not in packed_children
        assert app.btn_schedule not in packed_children
        assert app.btn_export not in packed_children
    finally:
        app.destroy()


def test_settings_dialog_houses_all_moved_options(tk_root):
    """Verifies that SettingsDialog contains 6 well-organized tabs housing all secondary options."""
    cfg = ConfigManager()
    cb_backup = MagicMock()
    cb_restore = MagicMock()
    cb_refresh = MagicMock()
    cb_excl = MagicMock()
    cb_sources = MagicMock()
    cb_sched = MagicMock()
    cb_export = MagicMock()
    cb_uninst = MagicMock()

    dlg = SettingsDialog(
        tk_root,
        config=cfg,
        on_backup_stack=cb_backup,
        on_restore_stack=cb_restore,
        on_refresh_sources=cb_refresh,
        on_open_exclusions=cb_excl,
        on_open_sources=cb_sources,
        on_open_schedule=cb_sched,
        on_export_inventory=cb_export,
        on_uninstall_app=cb_uninst,
        theme=LIGHT_THEME,
    )

    try:
        # Check that all 6 tabs exist in notebook
        tabs = dlg.notebook.tabs()
        assert len(tabs) == 6

        # Check action delegations
        dlg._do_backup_stack()
        cb_backup.assert_called_once()

        dlg._do_restore_stack()
        cb_restore.assert_called_once()

        dlg._do_refresh_sources()
        cb_refresh.assert_called_once()

        dlg._do_open_exclusions()
        cb_excl.assert_called_once()

        dlg._do_open_sources()
        cb_sources.assert_called_once()

        dlg._do_open_schedule()
        cb_sched.assert_called_once()

        dlg._do_export_inventory()
        cb_export.assert_called_once()

        dlg._do_uninstall_app()
        cb_uninst.assert_called_once()

    finally:
        dlg.destroy()

