"""Live virtual test verifying dist/Uninstall.exe end-to-end against mock files, shortcuts, registry, and app data."""

import os
import shutil
import subprocess
import sys
import winreg
from pathlib import Path


def run_virtual_test():
    print("=== Starting Virtual Integration Test of Uninstall.exe ===")

    temp_base = Path(os.environ.get("TEMP", r"C:\Windows\Temp")) / "WingetUpdaterVirtualTest"
    if temp_base.exists():
        shutil.rmtree(temp_base, ignore_errors=True)
    temp_base.mkdir(parents=True, exist_ok=True)

    # 1. Setup mock install directory
    mock_install = temp_base / "ProgramFiles" / "WingetUpdater"
    mock_install.mkdir(parents=True, exist_ok=True)
    (mock_install / "WingetUpdater.exe").write_bytes(b"DUMMY_EXE_CONTENT")
    (mock_install / "config.json").write_text('{"theme": "light"}')
    (mock_install / "update_tracker.json").write_text("{}")
    (mock_install / "exclusions.json").write_text("[]")
    (mock_install / "sources.json").write_text("[]")

    # 2. Setup mock shortcuts in user desktop and start menu
    user_profile = Path(os.environ["USERPROFILE"])
    onedrive = os.environ.get("OneDrive")
    if onedrive and (Path(onedrive) / "Desktop").exists():
        desktop = Path(onedrive) / "Desktop"
    else:
        desktop = user_profile / "Desktop"
        desktop.mkdir(parents=True, exist_ok=True)

    start_menu = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    start_menu.mkdir(parents=True, exist_ok=True)

    mock_sc_desktop = desktop / "Winget Updater.lnk"
    mock_sc_desktop.write_text("LNK_DATA")

    mock_sc_start = start_menu / "WingetUpdater.lnk"
    mock_sc_start.write_text("LNK_DATA")

    print(f"Created mock desktop shortcut: {mock_sc_desktop.exists()}")
    print(f"Created mock start menu shortcut: {mock_sc_start.exists()}")

    # 3. Setup mock registry keys
    test_uninst_key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\WingetUpdater"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, test_uninst_key) as k:
        winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, "Software & Package Updater")
        winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, str(mock_install))

    test_soft_key = r"Software\WingetUpdater"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, test_soft_key) as k:
        winreg.SetValueEx(k, "Configured", 0, winreg.REG_DWORD, 1)

    test_run_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, test_run_key, 0, winreg.KEY_SET_VALUE) as k:
        winreg.SetValueEx(k, "WingetUpdater", 0, winreg.REG_SZ, f'"{mock_install}\\WingetUpdater.exe" --scheduled')

    print("Created mock registry keys in HKCU.")

    # 4. Setup mock AppData
    mock_appdata = Path(os.environ["LOCALAPPDATA"]) / "WingetUpdater"
    mock_appdata.mkdir(parents=True, exist_ok=True)
    (mock_appdata / "virtual_test.log").write_text("TEST LOG DATA")
    print(f"Created mock AppData at {mock_appdata}: {mock_appdata.exists()}")

    # 5. Run compiled dist/Uninstall.exe in silent mode against the target mock install directory
    uninstaller_exe = Path.cwd() / "dist" / "Uninstall.exe"
    print(f"Executing uninstaller: {uninstaller_exe}")
    cmd = [str(uninstaller_exe), "--silent", "--force", "--target-dir", str(mock_install)]

    res = subprocess.run(cmd, capture_output=True, text=True)
    print("Uninstaller exit code:", res.returncode)

    # 6. Verify full removal
    errors = []

    if mock_install.exists():
        errors.append(f"Install directory still exists: {mock_install}")

    if mock_sc_desktop.exists():
        errors.append(f"Desktop shortcut still exists: {mock_sc_desktop}")

    if mock_sc_start.exists():
        errors.append(f"Start menu shortcut still exists: {mock_sc_start}")

    if mock_appdata.exists():
        errors.append(f"AppData directory still exists: {mock_appdata}")

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, test_uninst_key):
            errors.append(f"Registry key still exists: {test_uninst_key}")
    except FileNotFoundError:
        pass

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, test_soft_key):
            errors.append(f"Registry key still exists: {test_soft_key}")
    except FileNotFoundError:
        pass

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, test_run_key, 0, winreg.KEY_READ) as k:
            winreg.QueryValueEx(k, "WingetUpdater")
            errors.append("Registry Run key value still exists: WingetUpdater")
    except (FileNotFoundError, OSError):
        pass

    # Cleanup test base
    shutil.rmtree(temp_base, ignore_errors=True)

    if errors:
        print("VERIFICATION FAILED:")
        for err in errors:
            print(" -", err)
        return False
    else:
        print("VERIFICATION SUCCESSFUL: 100% of files, shortcuts, registry entries, and app data were completely removed with nothing left behind!")
        return True


if __name__ == "__main__":
    success = run_virtual_test()
    sys.exit(0 if success else 1)
