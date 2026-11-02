"""Unit tests for portable applications and browser extension discovery."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from winget_updater.discovery.extension_scanner import BrowserExtensionScanner, resolve_chromium_localized_name
from winget_updater.discovery.portable_scanner import PortableScanner, extract_pe_version_and_name
from winget_updater.models import PackageType


def test_portable_scanner_finds_executables(tmp_path):
    portable_dir = tmp_path / "PortableTools"
    portable_dir.mkdir()

    app_folder = portable_dir / "SubApp"
    app_folder.mkdir()
    dummy_exe = app_folder / "tool.exe"
    dummy_exe.write_text("binary content")

    uninstaller_exe = app_folder / "unins000.exe"
    uninstaller_exe.write_text("uninstaller content")

    with patch("winget_updater.discovery.portable_scanner.extract_pe_version_and_name", return_value=("3.2.1", "SuperTool", "ToolCorp")):
        scanner = PortableScanner(target_directories=[str(portable_dir)])
        results = scanner.scan()

        assert len(results) == 1
        item = results[0]
        assert item.name == "SuperTool"
        assert item.installed_version == "3.2.1"
        assert item.publisher == "ToolCorp"
        assert item.package_type == PackageType.PORTABLE


def test_browser_extension_scanner(tmp_path):
    # Setup dummy Chromium profile
    chrome_data = tmp_path / "Chrome" / "User Data" / "Default" / "Extensions" / "dummy_ext_id" / "1.0.0"
    chrome_data.mkdir(parents=True)

    manifest_file = chrome_data / "manifest.json"
    manifest_data = {
        "name": "uBlock Origin",
        "version": "1.58.0",
        "author": "Raymond Hill",
        "description": "An efficient blocker",
    }
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")

    scanner = BrowserExtensionScanner()
    scanner.local_appdata = str(tmp_path)
    scanner.appdata = ""

    items = []
    scanner._scan_chromium_browser("Google Chrome", tmp_path / "Chrome" / "User Data", items)

    assert len(items) == 1
    ext = items[0]
    assert "uBlock Origin" in ext.name
    assert ext.installed_version == "1.58.0"
    assert ext.package_type == PackageType.BROWSER_EXTENSION
    assert "listed only" in ext.notes.lower()


def test_localized_extension_name_resolution(tmp_path):
    ext_dir = tmp_path / "ext"
    locales = ext_dir / "_locales" / "en"
    locales.mkdir(parents=True)

    msg_file = locales / "messages.json"
    msg_file.write_text(json.dumps({"appName": {"message": "Dark Reader"}}), encoding="utf-8")

    resolved = resolve_chromium_localized_name(ext_dir, "__MSG_appName__")
    assert resolved == "Dark Reader"

    unresolved = resolve_chromium_localized_name(ext_dir, "Normal Name")
    assert unresolved == "Normal Name"

