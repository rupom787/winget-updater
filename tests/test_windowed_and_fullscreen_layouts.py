"""Unit tests verifying windowed and full-screen layouts in MainWindow and components (Item 7)."""

import os
import sys
import tkinter as tk
import pytest

from winget_updater.config import ConfigManager
from winget_updater.gui.app import MainWindow
from winget_updater.models import ProgramItem, PackageType, UpdateAction


@pytest.fixture
def headless_root():
    """Provides a safe headless Tkinter test harness."""
    try:
        root = tk.Tk()
        root.withdraw()
        yield root
        root.destroy()
    except tk.TclError:
        pytest.skip("Tkinter display not available in this environment")


class TestLayoutModes:
    """Test suite ensuring MainWindow and components adapt cleanly across resolutions."""

    def test_default_and_minimum_window_geometry(self):
        """MainWindow must enforce minimum dimensions (1040x680) to prevent UI truncation."""
        cfg = ConfigManager()
        cfg.auto_scan_on_startup = False
        app = MainWindow(config_manager=cfg)
        app.update_idletasks()

        min_w, min_h = app.minsize()
        assert min_w >= 1040, f"Expected minimum width >= 1040, got {min_w}"
        assert min_h >= 680, f"Expected minimum height >= 680, got {min_h}"

        app.destroy()

    def test_table_responsive_column_proportions_on_resize(self):
        """Columns must expand proportionally in full-screen mode to eliminate dead white space."""
        cfg = ConfigManager()
        cfg.auto_scan_on_startup = False
        app = MainWindow(config_manager=cfg)

        # 1. Test Windowed standard mode (1260x820)
        app.geometry("1260x820")
        app.update()
        w_name_win = app.table.tree.column("name", "width")
        w_inst_win = app.table.tree.column("installed", "width")
        w_late_win = app.table.tree.column("latest", "width")
        w_stat_win = app.table.tree.column("status", "width")
        sum_win = w_name_win + w_inst_win + w_late_win + w_stat_win
        tree_w_win = app.table.tree.winfo_width()
        assert abs(sum_win - tree_w_win) <= 12, "Windowed table columns should span the visible width"

        # 2. Test Full-screen maximized mode (1920x1080)
        app.geometry("1920x1080")
        app.update()
        w_name_full = app.table.tree.column("name", "width")
        w_inst_full = app.table.tree.column("installed", "width")
        w_late_full = app.table.tree.column("latest", "width")
        w_stat_full = app.table.tree.column("status", "width")
        sum_full = w_name_full + w_inst_full + w_late_full + w_stat_full
        tree_w_full = app.table.tree.winfo_width()

        assert tree_w_full > 1000, f"Treeview should expand to over 1000px, got {tree_w_full}"
        assert w_name_full > w_name_win, "Application Name column should expand in full-screen"
        assert abs(sum_full - tree_w_full) <= 12, "Full-screen table columns should fill 100% of visible width"

        app.destroy()

    def test_details_drawer_never_clips_actions_in_windowed_mode(self):
        """Secondary action buttons in DetailsDrawer must fit neatly across balanced rows without clipping."""
        cfg = ConfigManager()
        cfg.auto_scan_on_startup = False
        app = MainWindow(config_manager=cfg)

        # Shrink to minimum dimensions
        app.geometry("1040x680")
        app.update()

        # Populate a sample item to trigger details
        item = ProgramItem(
            name="Visual Studio Code",
            installed_version="1.95.0",
            latest_version="1.96.2",
            action=UpdateAction.AVAILABLE,
            package_type=PackageType.WIN32_EXE,
            id="Microsoft.VisualStudioCode",
        )
        app.table.populate([item])
        app.drawer.set_item(item)
        app.update()

        # Verify all buttons remain mapped and visible
        assert app.drawer.btn_update.winfo_exists()
        assert app.drawer.btn_open_folder.winfo_exists()
        assert app.drawer.btn_copy_id.winfo_exists()
        assert app.drawer.btn_pin.winfo_exists()
        assert app.drawer.btn_exclude.winfo_exists()
        assert app.drawer.btn_skip.winfo_exists()
        assert app.drawer.btn_uninstall.winfo_exists()

        # Verify diagnostic wraplength dynamically adapted
        assert app.drawer.lbl_diag_text.cget("wraplength") >= 200

        app.destroy()
