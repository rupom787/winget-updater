"""Deep unit and regression test suite verifying typography scaling, settings dialog,
prevention of phantom updates, Visual C++ runtime handling, and modern update summaries.
"""

import json
from pathlib import Path
import tkinter as tk
import pytest

from winget_updater.config import ConfigManager
from winget_updater.gui.dialogs import SettingsDialog, UpdateSummaryDialog
from winget_updater.gui.theme import DARK_THEME, LIGHT_THEME, get_typography
from winget_updater.models import (
    CompatibilityDetails,
    PackageType,
    ProgramItem,
    UpdateAction,
    UpdateOutcome,
)
from winget_updater.winget.matcher import PackageMatcher


@pytest.fixture
def tk_root():
    """Provides a headless Tkinter root for UI testing."""
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def test_can_auto_update_rejects_missing_or_phantom_versions():
    """Ensures can_auto_update() strictly rejects packages with no latest version or equal version."""
    # 1. Package with valid newer version -> should qualify
    valid_item = ProgramItem(
        name="Git",
        id="Git.Git",
        installed_version="2.45.0",
        latest_version="2.47.0",
        package_type=PackageType.WIN32_EXE,
        action=UpdateAction.AVAILABLE,
        is_verified_winget=True,
    )
    assert valid_item.can_auto_update() is True

    # 2. Package with dash latest version (phantom update) -> MUST REJECT
    phantom_item = ProgramItem(
        name="Microsoft Visual C++ 2010 x64",
        id="Microsoft.VCRedist.2010.x64",
        installed_version="10.0.40219",
        latest_version="—",
        package_type=PackageType.WIN32_EXE,
        action=UpdateAction.AVAILABLE,
        is_verified_winget=True,
    )
    assert phantom_item.can_auto_update() is False

    # 3. Package with latest == installed -> MUST REJECT
    equal_item = ProgramItem(
        name="VLC",
        id="VideoLAN.VLC",
        installed_version="3.0.21",
        latest_version="3.0.21",
        package_type=PackageType.WIN32_EXE,
        action=UpdateAction.AVAILABLE,
        is_verified_winget=True,
    )
    assert equal_item.can_auto_update() is False


def test_vcredist_static_runtime_safe_classification(tmp_path):
    """Ensures legacy Visual C++ runtimes are safely marked UP_TO_DATE as system components."""
    cfg = ConfigManager(base_dir=tmp_path)
    cfg.ignore_legacy_vcredist = True
    matcher = PackageMatcher(cfg)

    vcredist_item = ProgramItem(
        name="Microsoft Visual C++ 2010 x64 Redistributable - 10.0.40219",
        installed_version="10.0.40219",
        package_type=PackageType.WIN32_EXE,
    )

    # Empty upgrades and installed
    matched = matcher.match_all([vcredist_item], upgrades={}, installed={})
    assert len(matched) == 1
    res = matched[0]
    assert res.action == UpdateAction.UP_TO_DATE
    assert res.is_verified_winget is True
    assert "System Component" in res.notes


def test_store_app_safe_classification(tmp_path):
    """Ensures modern Store apps without winget upgrades are safely recognized as current."""
    cfg = ConfigManager(base_dir=tmp_path)
    matcher = PackageMatcher(cfg)

    store_item = ProgramItem(
        name="Photos",
        id="Microsoft.Windows.Photos_8wekyb3d8bbwe",
        installed_version="24.195.1008.0",
        package_type=PackageType.STORE_MSIX,
    )

    matched = matcher.match_all([store_item], upgrades={}, installed={})
    assert len(matched) == 1
    res = matched[0]
    assert res.action == UpdateAction.UP_TO_DATE
    assert res.is_verified_winget is True


def test_config_manager_settings_persistence(tmp_path):
    """Verifies that ConfigManager saves and reloads all user settings accurately."""
    cfg = ConfigManager(base_dir=tmp_path)
    cfg.font_scale = "large"
    cfg.theme = "dark"
    cfg.auto_close_apps = False
    cfg.enabled_managers["pip"] = False
    cfg.save_settings()

    # Re-read in fresh instance
    cfg2 = ConfigManager(base_dir=tmp_path)
    assert cfg2.font_scale == "large"
    assert cfg2.theme == "dark"
    assert cfg2.auto_close_apps is False
    assert cfg2.enabled_managers["pip"] is False
    assert cfg2.enabled_managers["winget"] is True


def test_typography_engine_presets():
    """Verifies typography presets generate valid fonts and scaling hierarchies."""
    for preset in ("compact", "normal", "large", "extra_large"):
        typo = get_typography(preset)
        assert typo.preset == preset
        assert typo.row_height > 20
        assert len(typo.title) >= 2
        assert len(typo.body) >= 2
        assert len(typo.table) >= 2

    # Normal should be larger than compact
    norm = get_typography("normal")
    comp = get_typography("compact")
    large = get_typography("large")
    assert norm.row_height > comp.row_height
    assert large.row_height > norm.row_height


def test_settings_dialog_initialization(tk_root, tmp_path):
    """Verifies SettingsDialog instantiates without crashing and displays tabs."""
    cfg = ConfigManager(base_dir=tmp_path)
    dlg = SettingsDialog(tk_root, config=cfg, theme=LIGHT_THEME)
    assert dlg.title() == "Settings & Preferences"
    assert hasattr(dlg, "font_scale_var")
    assert hasattr(dlg, "theme_var")
    assert hasattr(dlg, "manager_vars")
    dlg.destroy()


def test_update_summary_dialog_initialization(tk_root):
    """Verifies UpdateSummaryDialog renders with metrics and failure diagnosis without error."""
    from winget_updater.engine.updater import UpdateRunSummary

    summary = UpdateRunSummary(
        total_scanned=10,
        updated_count=5,
        failed_count=2,
        skipped_count=1,
        simulated_count=0,
    )
    failed_items = [
        ProgramItem(name="AppA", installed_version="1.0", latest_version="2.0", notes="Installer error 1603"),
        ProgramItem(name="AppB", installed_version="2.0", latest_version="3.0", notes="Access Denied"),
    ]

    dlg = UpdateSummaryDialog(tk_root, summary=summary, failed_items=failed_items, theme=DARK_THEME)
    assert "Completed" in dlg.title()
    dlg.destroy()
