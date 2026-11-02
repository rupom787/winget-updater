"""Tests for silent subprocess execution preventing console popups on Windows."""

import subprocess
from unittest.mock import MagicMock, patch
from winget_updater.utils.process import CREATE_NO_WINDOW, get_hidden_startupinfo, silent_run


def test_hidden_startupinfo_windows():
    si = get_hidden_startupinfo()
    if si is not None:
        assert si.dwFlags & subprocess.STARTF_USESHOWWINDOW
        assert si.wShowWindow == subprocess.SW_HIDE


@patch("subprocess.run")
def test_silent_run_injects_no_window_flag(mock_run):
    mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

    silent_run(["cmd.exe", "/c", "echo test"], capture_output=True, text=True)

    assert mock_run.called
    args, kwargs = mock_run.call_args
    assert kwargs.get("creationflags", 0) & CREATE_NO_WINDOW
    if "startupinfo" in kwargs and kwargs["startupinfo"] is not None:
        assert kwargs["startupinfo"].wShowWindow == subprocess.SW_HIDE

