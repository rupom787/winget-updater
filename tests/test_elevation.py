"""Unit tests for administrative elevation check and single UAC self-relaunch."""

import sys
from unittest.mock import MagicMock, patch
from winget_updater.elevation import RELAUNCH_FLAG, ensure_elevated, is_elevated, relaunch_as_admin


def test_is_elevated():
    with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=1):
        assert is_elevated() is True

    with patch("ctypes.windll.shell32.IsUserAnAdmin", return_value=0):
        assert is_elevated() is False


def test_relaunch_as_admin():
    with patch("ctypes.windll.shell32.ShellExecuteW", return_value=42) as mock_shell:
        code = relaunch_as_admin(custom_args=["--scan"])
        assert code == 42
        assert mock_shell.called
        args = mock_shell.call_args[0]
        # args: (hwnd, operation, file, params, directory, showCmd)
        assert args[1] == "runas"
        assert RELAUNCH_FLAG in args[3]


def test_ensure_elevated_already_admin():
    with patch("winget_updater.elevation.is_elevated", return_value=True):
        assert ensure_elevated() is True


def test_ensure_elevated_loop_prevention():
    # If RELAUNCH_FLAG is in sys.argv, do not loop again; return False cleanly
    with patch("winget_updater.elevation.is_elevated", return_value=False), \
         patch.object(sys, "argv", ["app.py", RELAUNCH_FLAG]):
        assert ensure_elevated() is False


def test_ensure_elevated_triggers_relaunch():
    with patch("winget_updater.elevation.is_elevated", return_value=False), \
         patch("winget_updater.elevation.relaunch_as_admin", return_value=42), \
         patch.object(sys, "argv", ["app.py"]):
        assert ensure_elevated(exit_on_relaunch=False) is True

