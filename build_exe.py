"""Build script to compile the application into a standalone Windows .exe with PyInstaller.
Bundles the uninstaller executable INSIDE WingetUpdater.exe so only a single executable is distributed.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def build():
    root_dir = Path(__file__).resolve().parent
    dist_dir = root_dir / "dist"
    build_dir = root_dir / "build"

    print("=== Building WingetUpdater.exe for Windows 11 ===")

    # 1. First compile Uninstall.exe so it exists for embedding inside the main installer
    from build_uninstaller import build_uninstaller
    print("\n--- Step 1: Compiling Bundled Uninstaller ---")
    if not build_uninstaller():
        print("Error: Failed to compile uninstaller.")
        return False

    uninstaller_path = dist_dir / "Uninstall.exe"
    if not uninstaller_path.exists():
        print(f"Error: {uninstaller_path} was not created.")
        return False

    print("\n--- Step 2: Compiling WingetUpdater.exe (with embedded Uninstaller) ---")
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "WingetUpdater",
        "--paths", str(root_dir / "src"),
        "--uac-admin",  # Embeds Windows UAC administrator manifest directly into EXE
        "--add-data", f"{root_dir / 'exclusions.json'};.",
        "--add-data", f"{root_dir / 'sources.json'};.",
        "--add-data", f"{uninstaller_path};.",  # Embeds Uninstall.exe inside WingetUpdater.exe!
        str(root_dir / "run.py"),
    ]

    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(root_dir))
    if res.returncode != 0:
        print(f"Build failed with exit code {res.returncode}")
        return False

    exe_path = dist_dir / "WingetUpdater.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 60)
        print("SUCCESS: Standalone WingetUpdater.exe created at:")
        print(f"  {exe_path}")
        print(f"  Size: {size_mb:.2f} MB")
        print("  Embedded components: Uninstall.exe, exclusions.json, sources.json")
        print("=" * 60)

        # Ensure default exclusions.json and sources.json exist in dist folder next to EXE
        for cfg_file in ("exclusions.json", "sources.json"):
            src_cfg = root_dir / cfg_file
            dst_cfg = dist_dir / cfg_file
            if src_cfg.exists() and not dst_cfg.exists():
                shutil.copy2(src_cfg, dst_cfg)
                print(f"Copied {cfg_file} to dist/")

        return True
    else:
        print("Error: Target executable was not found after build.")
        return False


if __name__ == "__main__":
    if not build():
        sys.exit(1)
