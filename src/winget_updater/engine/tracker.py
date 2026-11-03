"""App Update Tracker — Persistent discovery and pending update duration tracking for installed applications."""

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from winget_updater.models import ProgramItem, UpdateAction
from winget_updater.utils.logger import get_logger

logger = get_logger()
DEFAULT_TRACKER_FILE = "update_tracker.json"


@dataclass
class UpdateHistoryEvent:
    timestamp: str
    event: str  # "detected", "update_started", "update_succeeded", "update_failed", "skipped"
    installed_version: str
    target_version: str
    details: str = ""


@dataclass
class TrackedAppUpdate:
    package_id: str
    name: str
    installed_version: str
    available_version: str
    source: str
    first_detected: str
    last_seen: str
    status: str = "available"  # "available", "updated", "failed", "skipped"
    days_pending: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrackedAppUpdate":
        return cls(
            package_id=data.get("package_id", ""),
            name=data.get("name", "Unknown"),
            installed_version=data.get("installed_version", "0.0.0"),
            available_version=data.get("available_version", "0.0.0"),
            source=data.get("source", "winget"),
            first_detected=data.get("first_detected", datetime.now(timezone.utc).isoformat()),
            last_seen=data.get("last_seen", datetime.now(timezone.utc).isoformat()),
            status=data.get("status", "available"),
            days_pending=data.get("days_pending", 0),
            history=data.get("history", []),
        )


class UpdateTracker:
    """Core tracking engine monitoring available software updates over time."""

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path:
            self.storage_path = Path(storage_path)
        elif hasattr(sys, "frozen"):
            self.storage_path = Path(sys.executable).resolve().parent / DEFAULT_TRACKER_FILE
        else:
            self.storage_path = Path.cwd() / DEFAULT_TRACKER_FILE

        self.tracked_updates: Dict[str, TrackedAppUpdate] = {}
        self.load()

    def load(self) -> Dict[str, TrackedAppUpdate]:
        """Loads tracker database from disk atomically."""
        if not self.storage_path.exists():
            self.tracked_updates = {}
            return self.tracked_updates

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            tracked = {}
            for pkg_id, entry_data in raw_data.get("updates", {}).items():
                try:
                    tracked[pkg_id] = TrackedAppUpdate.from_dict(entry_data)
                except Exception as ex:
                    logger.warning(f"Error parsing tracked update for {pkg_id}: {ex}")

            self.tracked_updates = tracked
            self._recalculate_days_pending()
            return self.tracked_updates
        except Exception as e:
            logger.error(f"Failed to load update tracker file {self.storage_path}: {e}")
            self.tracked_updates = {}
            return self.tracked_updates

    def save(self) -> bool:
        """Persists tracking state to disk with atomic write."""
        try:
            self._recalculate_days_pending()
            payload = {
                "version": "1.0",
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "total_tracked": len(self.tracked_updates),
                "updates": {k: v.to_dict() for k, v in self.tracked_updates.items()},
            }
            tmp_path = self.storage_path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            if self.storage_path.exists():
                self.storage_path.unlink()
            tmp_path.rename(self.storage_path)
            return True
        except Exception as e:
            logger.error(f"Failed to save update tracker {self.storage_path}: {e}")
            return False

    def _recalculate_days_pending(self) -> None:
        """Recalculates the days_pending counter for all currently pending updates."""
        now = datetime.now(timezone.utc)
        for entry in self.tracked_updates.values():
            if entry.status in ("available", "failed"):
                try:
                    dt_first = datetime.fromisoformat(entry.first_detected)
                    if dt_first.tzinfo is None:
                        dt_first = dt_first.replace(tzinfo=timezone.utc)
                    entry.days_pending = max(0, (now - dt_first).days)
                except Exception:
                    entry.days_pending = 0

    def track_scan_results(self, items: List[ProgramItem]) -> Dict[str, Any]:
        """Scans current inventory and records newly discovered or evolving available updates."""
        now_iso = datetime.now(timezone.utc).isoformat()
        new_count = 0
        updated_in_tracker = 0

        # Create quick lookup by package id and name
        item_map: Dict[str, ProgramItem] = {}
        for it in items:
            item_map[it.id] = it
            if it.name:
                item_map[it.name.lower()] = it

        # 1. Update/Add items that have available updates
        for it in items:
            has_update = (
                it.action == UpdateAction.AVAILABLE
                or (it.can_auto_update() and it.latest_version and it.latest_version != it.installed_version)
            )

            if not has_update:
                continue

            pkg_id = it.id or f"{it.source}:{it.name}"
            avail_ver = it.latest_version or "Unknown"
            inst_ver = it.installed_version or "Unknown"

            if pkg_id in self.tracked_updates:
                tracked = self.tracked_updates[pkg_id]
                tracked.last_seen = now_iso
                tracked.installed_version = inst_ver

                # Version changed since last tracking
                if tracked.available_version != avail_ver:
                    tracked.available_version = avail_ver
                    tracked.status = "available"
                    tracked.history.append({
                        "timestamp": now_iso,
                        "event": "version_advanced",
                        "installed_version": inst_ver,
                        "target_version": avail_ver,
                        "details": f"Available version advanced to {avail_ver}",
                    })
                    updated_in_tracker += 1
                elif tracked.status == "updated":
                    # Re-opened update
                    tracked.status = "available"
                    tracked.first_detected = now_iso
                    updated_in_tracker += 1
            else:
                # Newly tracked available update
                new_entry = TrackedAppUpdate(
                    package_id=pkg_id,
                    name=it.name,
                    installed_version=inst_ver,
                    available_version=avail_ver,
                    source=it.source or "winget",
                    first_detected=now_iso,
                    last_seen=now_iso,
                    status="available",
                    days_pending=0,
                    history=[{
                        "timestamp": now_iso,
                        "event": "detected",
                        "installed_version": inst_ver,
                        "target_version": avail_ver,
                        "details": f"Update detected: {inst_ver} -> {avail_ver} via {it.source or 'winget'}",
                    }],
                )
                self.tracked_updates[pkg_id] = new_entry
                new_count += 1

        # 2. Reconcile items that were previously tracked as available but are now up to date
        for pkg_id, tracked in self.tracked_updates.items():
            if tracked.status == "available":
                matched_item = item_map.get(pkg_id) or item_map.get(tracked.name.lower())
                if matched_item and matched_item.action == UpdateAction.UP_TO_DATE:
                    tracked.status = "updated"
                    tracked.installed_version = matched_item.installed_version or tracked.available_version
                    tracked.history.append({
                        "timestamp": now_iso,
                        "event": "resolved_current",
                        "installed_version": tracked.installed_version,
                        "target_version": tracked.available_version,
                        "details": "Application verified as current/up-to-date",
                    })

        self.save()
        return {
            "new_tracked": new_count,
            "updated_tracked": updated_in_tracker,
            "total_pending": sum(1 for t in self.tracked_updates.values() if t.status == "available"),
        }

    def record_update_attempt(
        self,
        package_id: str,
        success: bool,
        current_version: str = "",
        message: str = "",
    ) -> None:
        """Records an execution outcome for a tracked update."""
        now_iso = datetime.now(timezone.utc).isoformat()
        tracked = self.tracked_updates.get(package_id)

        if not tracked:
            # Fallback search by name if package_id altered
            for t in self.tracked_updates.values():
                if t.name.lower() == package_id.lower():
                    tracked = t
                    break

        if not tracked:
            return

        if success:
            tracked.status = "updated"
            if current_version:
                tracked.installed_version = current_version
            tracked.history.append({
                "timestamp": now_iso,
                "event": "update_succeeded",
                "installed_version": tracked.installed_version,
                "target_version": tracked.available_version,
                "details": message or "Update applied successfully",
            })
        else:
            tracked.status = "failed"
            tracked.history.append({
                "timestamp": now_iso,
                "event": "update_failed",
                "installed_version": tracked.installed_version,
                "target_version": tracked.available_version,
                "details": message or "Update attempt failed",
            })

        self.save()

    def get_tracked_items(self, status_filter: Optional[str] = None) -> List[TrackedAppUpdate]:
        """Returns list of tracked updates sorted by pending days (oldest first)."""
        self._recalculate_days_pending()
        items = list(self.tracked_updates.values())
        if status_filter:
            items = [it for it in items if it.status.lower() == status_filter.lower()]
        return sorted(items, key=lambda x: (x.status != "available", -x.days_pending, x.name.lower()))

    def get_metrics(self) -> Dict[str, Any]:
        """Returns aggregate tracker metrics."""
        self._recalculate_days_pending()
        pending = [t for t in self.tracked_updates.values() if t.status == "available"]
        updated = [t for t in self.tracked_updates.values() if t.status == "updated"]
        failed = [t for t in self.tracked_updates.values() if t.status == "failed"]

        oldest_days = max([t.days_pending for t in pending], default=0)
        avg_pending = (sum(t.days_pending for t in pending) / len(pending)) if pending else 0.0

        return {
            "total_tracked": len(self.tracked_updates),
            "pending_count": len(pending),
            "updated_count": len(updated),
            "failed_count": len(failed),
            "oldest_pending_days": oldest_days,
            "average_pending_days": round(avg_pending, 1),
        }

    def remove_tracked(self, package_id: str) -> bool:
        """Removes a package from update tracking."""
        if package_id in self.tracked_updates:
            del self.tracked_updates[package_id]
            self.save()
            return True
        return False

    def clear_resolved(self) -> int:
        """Purges items marked as updated to keep storage streamlined."""
        to_del = [k for k, v in self.tracked_updates.items() if v.status == "updated"]
        for k in to_del:
            del self.tracked_updates[k]
        if to_del:
            self.save()
        return len(to_del)
