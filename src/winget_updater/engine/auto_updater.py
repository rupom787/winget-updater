"""Application Self-Update Checker & Notification Engine.
Monitors GitHub releases for new versions of Winget Updater, caches check results,
and provides non-intrusive notifications and one-click upgrades.
"""

import json
import os
import sys
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from winget_updater import __version__
from winget_updater.utils.logger import get_logger
from winget_updater.winget.version_comparator import compare_versions

logger = get_logger()

GITHUB_REPO = "rupom787/winget-updater"
API_LATEST_RELEASE = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CACHE_EXPIRY_SECONDS = 4 * 3600  # 4 hours


class AppUpdateChecker:
    """Queries GitHub releases API to detect when a new version of the app is available."""

    def __init__(self, cache_file: Optional[Path] = None):
        if cache_file:
            self.cache_file = Path(cache_file)
        elif hasattr(sys, "frozen"):
            self.cache_file = Path(sys.executable).resolve().parent / "app_update_cache.json"
        else:
            self.cache_file = Path.cwd() / "app_update_cache.json"

    def _read_cache(self) -> Optional[Dict[str, Any]]:
        """Reads cached release check results if still fresh."""
        if not self.cache_file.exists():
            return None
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            cached_time = data.get("timestamp", 0)
            if time.time() - cached_time < CACHE_EXPIRY_SECONDS:
                return data.get("result")
        except Exception as e:
            logger.debug(f"Failed to read update cache: {e}")
        return None

    def _write_cache(self, result: Dict[str, Any]) -> None:
        """Saves release check result to local cache."""
        try:
            payload = {
                "timestamp": time.time(),
                "result": result,
            }
            tmp_path = self.cache_file.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            if self.cache_file.exists():
                self.cache_file.unlink()
            tmp_path.rename(self.cache_file)
        except Exception as e:
            logger.debug(f"Failed to write update cache: {e}")

    def check_for_updates(self, force: bool = False) -> Dict[str, Any]:
        """Checks GitHub for new releases. Returns dict with status and details."""
        if not force:
            cached = self._read_cache()
            if cached is not None:
                return cached

        current_ver = __version__.lstrip("v")
        default_res: Dict[str, Any] = {
            "update_available": False,
            "current_version": current_ver,
            "latest_version": current_ver,
            "tag_name": f"v{current_ver}",
            "release_name": "",
            "release_notes": "",
            "html_url": f"https://github.com/{GITHUB_REPO}/releases/latest",
            "download_url": "",
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            req = urllib.request.Request(
                API_LATEST_RELEASE,
                headers={
                    "User-Agent": f"WingetUpdater/{current_ver} (Windows 11)",
                    "Accept": "application/vnd.github.v3+json",
                },
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status != 200:
                    logger.debug(f"GitHub API returned status {resp.status}")
                    return default_res

                raw_data = resp.read().decode("utf-8")
                data = json.loads(raw_data)

            tag = data.get("tag_name", "").strip()
            latest_ver = tag.lstrip("v")
            if not latest_ver:
                return default_res

            # Find standalone WingetUpdater.exe asset download url
            download_url = data.get("html_url", "")
            for asset in data.get("assets", []):
                if asset.get("name", "").lower() == "wingetupdater.exe":
                    download_url = asset.get("browser_download_url", download_url)
                    break

            is_newer = compare_versions(latest_ver, current_ver) > 0

            result = {
                "update_available": is_newer,
                "current_version": current_ver,
                "latest_version": latest_ver,
                "tag_name": tag,
                "release_name": data.get("name", tag),
                "release_notes": data.get("body", ""),
                "html_url": data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases/latest"),
                "download_url": download_url,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }

            self._write_cache(result)
            if is_newer:
                logger.info(f"New application version available: {latest_ver} (current: {current_ver})")
            return result

        except Exception as e:
            logger.debug(f"Update check failed (offline or network error): {e}")
            return default_res

    def check_in_background(
        self,
        callback: Callable[[Dict[str, Any]], None],
        force: bool = False,
    ) -> threading.Thread:
        """Runs update check asynchronously in background thread without blocking UI."""
        def worker():
            res = self.check_for_updates(force=force)
            try:
                callback(res)
            except Exception as ex:
                logger.debug(f"Update check callback error: {ex}")

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return thread
