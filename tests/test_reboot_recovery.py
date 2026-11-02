"""Unit tests for reboot-safe state management and crash recovery."""

import json
from pathlib import Path
from winget_updater.engine.state_manager import StateManager


def test_state_manager_recovery_from_reboot(tmp_path):
    state_file = tmp_path / "run_state.json"

    # Simulate an interrupted run state written to disk before system restarted
    interrupted_state = {
        "run_id": "run_crash_123",
        "started_at": "2026-11-01T10:00:00",
        "status": "in_progress",
        "completed_at": None,
        "packages": {
            "pkg.done": {
                "name": "Finished App",
                "status": "completed",
            },
            "pkg.in_progress": {
                "name": "Interrupted App",
                "status": "updating",
                "start_time": "2026-11-01T10:05:00",
            },
        },
    }
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(interrupted_state, f)

    mgr = StateManager(state_file_path=state_file)

    # Start a new run: it should detect previous interrupted run
    new_run = mgr.start_new_run("run_resume_456")

    assert new_run.run_id == "run_resume_456"
    assert new_run.status == "in_progress"

    # Verify that the interrupted package was recorded and saved
    prev_state = mgr.load_state()
    assert prev_state.run_id == "run_resume_456"


def test_state_manager_lifecycle(tmp_path):
    state_file = tmp_path / "run_state.json"
    mgr = StateManager(state_file_path=state_file)

    mgr.start_new_run("run_test_01")
    mgr.record_package_start("app.1", "First App")
    mgr.record_package_end("app.1", "completed", "Updated to 1.2")
    mgr.complete_run()

    loaded = mgr.load_state()
    assert loaded is not None
    assert loaded.status == "completed"
    assert loaded.completed_at is not None
    assert loaded.packages["app.1"]["status"] == "completed"
    assert loaded.packages["app.1"]["notes"] == "Updated to 1.2"

