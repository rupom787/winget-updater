"""Unit and integration tests for Uninstaller engine and standalone uninstaller."""

import os
import shutil
import sys
import tempfile
from pathlib import Path
import pytest

from winget_updater.engine.uninstaller import (
    APP_TITLE,
    APP_NAME,
    REGISTRY_UNINSTALL_SUBKEY,
    REGISTRY_SOFTWARE_SUBKEY,
    SHORTCUT_NAMES,
    Uninstaller,
    UninstallSummary,
)


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp(prefix="winget_uninst_test_")
    yield Path(d)
    if os.path.exists(d):
        shutil.rmtree(d, ignore_errors=True)


class TestUninstallerEngine:
    def test_detect_install_dir(self):
        detected = Uninstaller.detect_install_dir()
        assert detected is not None
        assert detected.exists()

    def test_is_dev_source_directory(self, temp_dir):
        # Current repo should be identified as dev source
        cwd = Path.cwd()
        assert Uninstaller.is_dev_source_directory(cwd) is True

        # Plain temp directory should not be dev source
        assert Uninstaller.is_dev_source_directory(temp_dir) is False

        # Temp directory with .git should be identified as dev source
        (temp_dir / ".git").mkdir()
        assert Uninstaller.is_dev_source_directory(temp_dir) is True

    def test_remove_shortcuts(self, temp_dir):
        sub_folder = temp_dir / "Software & Package Updater"
        sub_folder.mkdir()
        sc1 = sub_folder / "Software & Package Updater.lnk"
        sc1.write_text("dummy shortcut content")
        sc2 = temp_dir / "Winget Updater.lnk"
        sc2.write_text("dummy shortcut content")

        assert sc1.exists()
        assert sc2.exists()

        uninstaller = Uninstaller(target_install_dir=temp_dir)
        removed = uninstaller.remove_shortcuts([sc1, sc2])

        assert str(sc1) in removed
        assert str(sc2) in removed
        assert not sc1.exists()
        assert not sc2.exists()
        # Empty subfolder should also have been removed
        assert not sub_folder.exists()

    def test_remove_appdata(self, temp_dir):
        appdata_mock = temp_dir / "WingetUpdater"
        appdata_mock.mkdir()
        (appdata_mock / "winget_updater.log").write_text("log content")
        (appdata_mock / "cache.dat").write_text("cache")

        uninstaller = Uninstaller()
        removed = uninstaller.remove_appdata([appdata_mock])

        assert str(appdata_mock) in removed
        assert not appdata_mock.exists()

    def test_remove_install_directory_safe_dev_mode(self, temp_dir):
        # Simulate a dev workspace
        (temp_dir / ".git").mkdir()
        runtime_log = temp_dir / "winget_updater.log"
        runtime_log.write_text("log")
        runtime_tracker = temp_dir / "update_tracker.json"
        runtime_tracker.write_text("{}")
        code_file = temp_dir / "source.py"
        code_file.write_text("print('hello')")

        uninstaller = Uninstaller(target_install_dir=temp_dir)
        files_removed, dirs_removed = uninstaller.remove_install_directory(temp_dir, force_delete_all=False)

        assert str(runtime_log) in files_removed
        assert str(runtime_tracker) in files_removed
        assert not runtime_log.exists()
        assert not runtime_tracker.exists()
        # Code file must NOT be touched
        assert code_file.exists()
        assert (temp_dir / ".git").exists()

    def test_remove_install_directory_full_wipe(self, temp_dir):
        # Simulate an installed application folder
        app_folder = temp_dir / "InstalledApp"
        app_folder.mkdir()
        (app_folder / "WingetUpdater.exe").write_text("binary")
        (app_folder / "Uninstall.exe").write_text("binary")
        (app_folder / "data").mkdir()
        (app_folder / "data" / "config.json").write_text("{}")

        uninstaller = Uninstaller(target_install_dir=app_folder)
        files_removed, dirs_removed = uninstaller.remove_install_directory(app_folder, force_delete_all=True)

        assert not app_folder.exists()
        assert any("WingetUpdater.exe" in f for f in files_removed)
        assert any("Uninstall.exe" in f for f in files_removed)

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows registry required")
    def test_registry_tree_deletion_and_registration(self, temp_dir):
        import winreg

        test_key_name = r"Software\WingetUpdaterTestKey"
        # Create test hierarchy
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, test_key_name) as k:
            winreg.SetValueEx(k, "TestVal", 0, winreg.REG_SZ, "Hello")
            with winreg.CreateKey(k, "SubKey1") as sub:
                winreg.SetValueEx(sub, "SubVal", 0, winreg.REG_SZ, "World")

        # Verify it exists
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"{test_key_name}\\SubKey1") as k:
            val, _ = winreg.QueryValueEx(k, "SubVal")
            assert val == "World"

        # Delete key tree
        ok = Uninstaller._delete_reg_key_tree(winreg.HKEY_CURRENT_USER, test_key_name)
        assert ok is True

        # Verify it is deleted
        with pytest.raises(FileNotFoundError):
            winreg.OpenKey(winreg.HKEY_CURRENT_USER, test_key_name)

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows registry required")
    def test_windows_registry_lifecycle(self, temp_dir):
        import winreg

        test_install = temp_dir / "InstallFolder"
        test_install.mkdir()
        test_exe = test_install / "WingetUpdater.exe"
        test_exe.write_text("dummy")

        # 1. Register
        reg_ok = Uninstaller.register_in_windows_registry(test_install, version="2.0.0")
        assert reg_ok is True

        # 2. Verify key exists
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_UNINSTALL_SUBKEY) as k:
            disp_name, _ = winreg.QueryValueEx(k, "DisplayName")
            assert disp_name == APP_TITLE
            inst_loc, _ = winreg.QueryValueEx(k, "InstallLocation")
            assert inst_loc == str(test_install)

        # 3. Clean up via uninstaller
        uninstaller = Uninstaller()
        keys_rem, vals_rem = uninstaller.remove_registry_entries()
        assert any("Uninstall\\WingetUpdater" in k for k in keys_rem)

        # 4. Verify key is removed
        with pytest.raises(FileNotFoundError):
            winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_UNINSTALL_SUBKEY)

    def test_execute_full_uninstall_mocked(self, monkeypatch, temp_dir):
        uninstaller = Uninstaller(target_install_dir=temp_dir)

        # Mock out platform-specific calls
        monkeypatch.setattr(uninstaller, "kill_running_processes", lambda: ["WingetUpdater.exe"])
        monkeypatch.setattr(uninstaller, "remove_scheduled_tasks", lambda: ["WingetUpdaterDaily"])
        monkeypatch.setattr(uninstaller, "remove_shortcuts", lambda: ["C:\\Desktop\\App.lnk"])
        monkeypatch.setattr(uninstaller, "remove_registry_entries", lambda: (["HKCU\\Software\\WingetUpdater"], []))
        monkeypatch.setattr(uninstaller, "remove_appdata", lambda: ["C:\\AppData\\WingetUpdater"])

        progress_calls = []

        def cb(msg, pct):
            progress_calls.append((msg, pct))

        summary = uninstaller.execute_full_uninstall(target_dir=temp_dir, progress_callback=cb)

        assert isinstance(summary, UninstallSummary)
        assert summary.processes_killed == ["WingetUpdater.exe"]
        assert summary.tasks_removed == ["WingetUpdaterDaily"]
        assert summary.shortcuts_removed == ["C:\\Desktop\\App.lnk"]
        assert summary.registry_keys_removed == ["HKCU\\Software\\WingetUpdater"]
        assert summary.appdata_dirs_removed == ["C:\\AppData\\WingetUpdater"]
        assert summary.total_items_removed >= 5
        assert len(progress_calls) >= 5

