"""Unit tests for Windows Task Scheduler safety checks and registration."""

from unittest.mock import MagicMock, patch
from winget_updater.compatibility.system_info import SystemInfoProvider
from winget_updater.engine.scheduler import SchedulerManager


def test_scheduler_safety_guards_aborts_on_battery():
    sys_mock = MagicMock(spec=SystemInfoProvider)
    # Running on battery
    sys_mock.is_on_ac_power.return_value = (False, "Running on Battery power (45% remaining)")
    sys_mock.get_cpu_load_percent.return_value = 10.0

    scheduler = SchedulerManager(sys_info=sys_mock)
    safe, msg = scheduler.check_safety_guards()

    assert safe is False
    assert "require AC power" in msg


def test_scheduler_safety_guards_aborts_on_heavy_cpu():
    sys_mock = MagicMock(spec=SystemInfoProvider)
    sys_mock.is_on_ac_power.return_value = (True, "Connected to AC line power")
    # CPU at 95%
    sys_mock.get_cpu_load_percent.return_value = 95.0

    scheduler = SchedulerManager(sys_info=sys_mock)
    safe, msg = scheduler.check_safety_guards()

    assert safe is False
    assert "heavily loaded" in msg


def test_scheduler_safety_guards_passes_when_safe():
    sys_mock = MagicMock(spec=SystemInfoProvider)
    sys_mock.is_on_ac_power.return_value = (True, "Connected to AC line power")
    sys_mock.get_cpu_load_percent.return_value = 15.0

    scheduler = SchedulerManager(sys_info=sys_mock)
    safe, msg = scheduler.check_safety_guards()

    assert safe is True
    assert "passed" in msg.lower()


def test_create_daily_task_command_structure():
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = "SUCCESS: The scheduled task 'WingetUpdaterDaily' has successfully been created."

    with patch("subprocess.run", return_value=mock_res) as mock_run:
        scheduler = SchedulerManager()
        success, msg = scheduler.create_daily_task(time_hh_mm="14:30")

        assert success is True
        assert mock_run.called
        cmd_args = mock_run.call_args[0][0]

        # Verify critical flags
        assert "schtasks.exe" in cmd_args[0]
        assert "/Create" in cmd_args
        assert "/SC" in cmd_args and "DAILY" in cmd_args
        assert "/ST" in cmd_args and "14:30" in cmd_args
        assert "/IT" in cmd_args       # Ensures task runs ONLY when user is logged on
        assert "/RL" in cmd_args and "HIGHEST" in cmd_args # Elevated admin execution

