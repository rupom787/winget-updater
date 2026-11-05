# Standalone Executable Build Policy for WingetUpdater

## Core Requirement
The user starts and tests the application **only via `dist/WingetUpdater.exe`** (no direct python execution).

## Mandatory Actions on Every Code/UI Update
1. **Rebuild the Executable**:
   - Run `python build_exe.py` whenever any source file, theme, or component is updated.
   - This compiles both `dist/Uninstall.exe` (13.48 MB) and `dist/WingetUpdater.exe` (~34-35 MB) with all embedded assets (`Uninstall.exe`, `exclusions.json`, `sources.json`, `config.json`).
2. **Preserve Default Theme**:
   - Ensure `dist/config.json` and default `ConfigManager` settings remain locked to `"theme": "dark"` (Dream obsidian translucent acrylic glass mode) and `"font_scale": "normal"`.
3. **Synchronize Distribution**:
   - Compute SHA-256 for `dist/WingetUpdater.exe`.
   - Update GitHub Release assets (`gh release upload v... dist/WingetUpdater.exe --clobber`) and release notes.
   - Rebuild website if any assets or version info changed.
