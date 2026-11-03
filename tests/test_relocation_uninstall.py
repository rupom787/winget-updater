"""Test verifying that Uninstall.exe running from INSIDE the install directory can completely delete itself and its parent directory."""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def test_relocation_uninstall():
    print("=== Testing Self-Relocation Uninstallation ===")
    temp_base = Path(os.environ.get("TEMP", r"C:\Windows\Temp")) / "WingetUpdaterRelocTest"
    if temp_base.exists():
        shutil.rmtree(temp_base, ignore_errors=True)
    temp_base.mkdir(parents=True, exist_ok=True)

    # Mock install folder
    mock_install = temp_base / "AppFolder"
    mock_install.mkdir(parents=True, exist_ok=True)

    # Copy Uninstall.exe into the mock install folder
    src_uninstaller = Path.cwd() / "dist" / "Uninstall.exe"
    target_uninstaller = mock_install / "Uninstall.exe"
    shutil.copy2(src_uninstaller, target_uninstaller)

    # Add other mock files
    (mock_install / "WingetUpdater.exe").write_bytes(b"MOCK_APP")
    (mock_install / "config.json").write_text("{}")
    (mock_install / "update_tracker.json").write_text("{}")

    assert target_uninstaller.exists()
    print(f"Copied uninstaller to: {target_uninstaller}")

    # Launch target_uninstaller from within mock_install in silent mode
    print("Launching uninstaller from inside the directory being uninstalled...")
    cmd = [str(target_uninstaller), "--silent", "--force", "--target-dir", str(mock_install)]
    res = subprocess.run(cmd, cwd=str(mock_install), capture_output=True, text=True)
    print("Exit code:", res.returncode)

    # Wait up to 8 seconds for the relocated uninstaller in %TEMP% to wipe the install folder
    start = time.time()
    while time.time() - start < 8.0:
        if not mock_install.exists():
            break
        time.sleep(0.5)

    if mock_install.exists():
        remaining = list(mock_install.iterdir())
        print(f"FAILED: Directory still exists. Remaining files: {remaining}")
        shutil.rmtree(temp_base, ignore_errors=True)
        assert False, f"Directory still exists. Remaining files: {remaining}"
    else:
        print("SUCCESS: Installation folder and running Uninstall.exe were completely deleted via self-relocation!")
        shutil.rmtree(temp_base, ignore_errors=True)
        assert True


if __name__ == "__main__":
    test_relocation_uninstall()
