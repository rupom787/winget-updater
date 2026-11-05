# Standalone Executable Build Policy for WingetUpdater

## Core Requirement
The user starts and tests the application **only via `dist/WingetUpdater.exe`** (no direct python execution).

## Mandatory Actions on Every Code/UI Update
1. **Always Bump the Version on Every Update & Push**:
   - Every time code or UI is updated and pushed, increment the semantic version (e.g. `2.1.0` -> `2.2.0` or `2.2.1`).
   - Synchronize the new version string across all manifests:
     * `src/winget_updater/__init__.py` (`__version__ = "X.Y.Z"`)
     * `pyproject.toml` (`version = "X.Y.Z"`)
     * `run.py` (`version = "X.Y.Z"`)
     * `website/package.json` (`"version": "X.Y.Z"`)
     * `website/index.html` (`vX.Y.Z` badge, telemetry, and download links)
     * `README.md` (`vX.Y.Z` badges, download table, and quick start links)
2. **Rebuild the Executable**:
   - Run `python build_exe.py` whenever any source file, theme, or component is updated.
   - This compiles both `dist/Uninstall.exe` (~13.49 MB) and `dist/WingetUpdater.exe` (~34.25 MB) with all embedded assets (`Uninstall.exe`, `exclusions.json`, `sources.json`, `config.json`).
3. **Preserve Default Theme**:
   - Ensure `dist/config.json` and default `ConfigManager` settings remain locked to `"theme": "dark"` (Dream obsidian translucent acrylic glass mode) and `"font_scale": "normal"`.
4. **Synchronize Distribution & Releases**:
   - Compute SHA-256 for `dist/WingetUpdater.exe`.
   - Update `README.md` download table with latest hash and file size.
   - Publish or update the GitHub Release tag `vX.Y.Z` and upload binaries (`gh release create vX.Y.Z dist/WingetUpdater.exe dist/Uninstall.exe` or `gh release upload vX.Y.Z dist/WingetUpdater.exe dist/Uninstall.exe --clobber`).

