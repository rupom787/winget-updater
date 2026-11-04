"""Build script to compile the standalone uninstaller into dist/Uninstall.exe with PyInstaller."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_uninstaller() -> bool:
    root_dir = Path(__file__).resolve().parent
    dist_dir = root_dir / "dist"

    print("=== Building Uninstall.exe for Windows 11 ===")

    workpath = Path(os.environ.get("TEMP", "C:/Temp")) / "pyinstaller_uninstaller"
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name", "Uninstall",
        "--paths", str(root_dir / "src"),
        "--workpath", str(workpath),
        "--uac-admin",  # Embeds Windows UAC administrator manifest for registry and shortcut cleanup
        str(root_dir / "uninstall.py"),
    ]

    print(f"Executing: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=str(root_dir))
    if res.returncode != 0:
        print(f"Build failed with exit code {res.returncode}")
        return False

    exe_path = dist_dir / "Uninstall.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 60)
        print("SUCCESS: Uninstaller executable created at:")
        print(f"  {exe_path}")
        print(f"  Size: {size_mb:.2f} MB")
        print("=" * 60)
        return True
    else:
        print("Error: Target executable was not found after build.")
        return False


if __name__ == "__main__":
    if not build_uninstaller():
        sys.exit(1)

