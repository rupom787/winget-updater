"""Reboot-safe execution state tracking and recovery."""

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from winget_updater.utils.logger import get_logger

logger = get_logger()
DEFAULT_STATE_FILE = "run_state.json"


@dataclass
class RunState:
    run_id: str
    started_at: str
    status: str = "in_progress"  # in_progress, completed, interrupted
    completed_at: Optional[str] = None
    packages: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class StateManager:
    """Maintains atomic run state on disk to guarantee reboot resilience."""

    def __init__(self, state_file_path: Optional[Path] = None):
        if state_file_path:
            self.state_file = state_file_path
        elif hasattr(sys, "frozen"):
            self.state_file = Path(sys.executable).resolve().parent / DEFAULT_STATE_FILE
        else:
            self.state_file = Path.cwd() / DEFAULT_STATE_FILE
        self.current_state: Optional[RunState] = None

    def load_state(self) -> Optional[RunState]:
        """Loads existing state from disk if present."""
        if not self.state_file.exists():
            return None
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.current_state = RunState(
                run_id=data.get("run_id", "unknown"),
                started_at=data.get("started_at", ""),
                status=data.get("status", "unknown"),
                completed_at=data.get("completed_at"),
                packages=data.get("packages", {}),
            )
            return self.current_state
        except Exception as e:
            logger.warning(f"Could not load state file {self.state_file}: {e}")
            return None

    def start_new_run(self, run_id: str) -> RunState:
        """Starts a new run, handling recovery from any previously interrupted run."""
        prev = self.load_state()
        if prev and prev.status == "in_progress":
            logger.warning(
                f"Recovered from interrupted run '{prev.run_id}' (likely interrupted by system reboot or shutdown)."
            )
            # Find any package that was mid-update
            for pkg_id, info in prev.packages.items():
                if info.get("status") == "updating":
                    logger.warning(
                        f"Package '{pkg_id}' was mid-update when reboot occurred. Marking as interrupted."
                    )
                    info["status"] = "interrupted"
                    info["error"] = "Interrupted by system reboot"

        self.current_state = RunState(
            run_id=run_id,
            started_at=datetime.now().isoformat(),
            status="in_progress",
            packages={},
        )
        self._save()
        return self.current_state

    def record_package_start(self, package_id: str, name: str) -> None:
        """Records that a package update has commenced."""
        if not self.current_state:
            return
        self.current_state.packages[package_id] = {
            "name": name,
            "status": "updating",
            "start_time": datetime.now().isoformat(),
        }
        self._save()

    def record_package_end(
        self,
        package_id: str,
        status: str,
        notes: str = "",
    ) -> None:
        """Records the completion, skip, or failure of a package update."""
        if not self.current_state:
            return
        pkg_record = self.current_state.packages.setdefault(package_id, {})
        pkg_record["status"] = status
        pkg_record["end_time"] = datetime.now().isoformat()
        pkg_record["notes"] = notes
        self._save()

    def complete_run(self) -> None:
        """Marks the current run as cleanly completed."""
        if not self.current_state:
            return
        self.current_state.status = "completed"
        self.current_state.completed_at = datetime.now().isoformat()
        self._save()

    def _save(self) -> None:
        """Atomically saves state to disk."""
        if not self.current_state:
            return
        try:
            temp_file = self.state_file.with_suffix(".tmp")
            data = asdict(self.current_state)
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.state_file)
        except Exception as e:
            logger.error(f"Failed to persist state to {self.state_file}: {e}")

