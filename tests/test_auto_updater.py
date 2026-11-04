"""Unit tests for the Application Self-Update Checker and Notification Engine."""

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from winget_updater.engine.auto_updater import AppUpdateChecker


def test_update_checker_no_cache(tmp_path):
    cache_file = tmp_path / "test_cache.json"
    checker = AppUpdateChecker(cache_file=cache_file)
    assert checker._read_cache() is None


def test_update_checker_cache_write_and_read(tmp_path):
    cache_file = tmp_path / "test_cache.json"
    checker = AppUpdateChecker(cache_file=cache_file)

    sample_result = {
        "update_available": True,
        "current_version": "2.0.0",
        "latest_version": "2.1.0",
        "tag_name": "v2.1.0",
    }
    checker._write_cache(sample_result)
    assert cache_file.exists()

    cached = checker._read_cache()
    assert cached is not None
    assert cached["update_available"] is True
    assert cached["latest_version"] == "2.1.0"


def test_update_checker_cache_expiry(tmp_path):
    cache_file = tmp_path / "test_cache.json"
    checker = AppUpdateChecker(cache_file=cache_file)

    # Write expired payload (older than 4 hours)
    payload = {
        "timestamp": time.time() - (5 * 3600),
        "result": {"update_available": False},
    }
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(payload, f)

    assert checker._read_cache() is None


@patch("urllib.request.urlopen")
def test_update_checker_detects_newer_version(mock_urlopen, tmp_path):
    cache_file = tmp_path / "test_cache.json"
    checker = AppUpdateChecker(cache_file=cache_file)

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "tag_name": "v2.2.0",
        "name": "Release v2.2.0",
        "body": "Test release notes",
        "html_url": "https://github.com/rupom787/winget-updater/releases/tag/v2.2.0",
        "assets": [
            {
                "name": "WingetUpdater.exe",
                "browser_download_url": "https://github.com/rupom787/winget-updater/releases/download/v2.2.0/WingetUpdater.exe"
            }
        ],
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    res = checker.check_for_updates(force=True)
    assert res["update_available"] is True
    assert res["latest_version"] == "2.2.0"
    assert "WingetUpdater.exe" in res["download_url"]


@patch("urllib.request.urlopen")
def test_update_checker_detects_current_version(mock_urlopen, tmp_path):
    cache_file = tmp_path / "test_cache.json"
    checker = AppUpdateChecker(cache_file=cache_file)

    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "tag_name": "v2.0.0",
        "name": "Release v2.0.0",
        "body": "Older release",
        "html_url": "https://github.com/rupom787/winget-updater/releases/tag/v2.0.0",
        "assets": [],
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_resp

    res = checker.check_for_updates(force=True)
    # 2.0.0 is <= current version (2.1.0)
    assert res["update_available"] is False


def test_update_checker_background_thread(tmp_path):
    cache_file = tmp_path / "test_cache.json"
    checker = AppUpdateChecker(cache_file=cache_file)

    # Pre-cache result
    checker._write_cache({
        "update_available": True,
        "current_version": "2.0.0",
        "latest_version": "2.1.0",
    })

    received = []

    def callback(res):
        received.append(res)

    t = checker.check_in_background(callback=callback, force=False)
    t.join(timeout=2.0)

    assert len(received) == 1
    assert received[0]["update_available"] is True

