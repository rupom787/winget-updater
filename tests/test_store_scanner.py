"""Unit tests for Microsoft Store / Appx scanner with mocked PowerShell output."""

import json
import subprocess
from unittest.mock import MagicMock, patch
from winget_updater.discovery.store_scanner import StoreScanner
from winget_updater.models import PackageType


def test_store_scanner_parses_json_output():
    mock_json = [
        {
            "Name": "Microsoft.WindowsTerminal",
            "PackageFullName": "Microsoft.WindowsTerminal_1.19.10573.0_x64__8wekyb3d8bbwe",
            "Version": "1.19.10573.0",
            "Publisher": "CN=Microsoft Corporation, O=Microsoft Corporation, L=Redmond, S=Washington, C=US",
            "InstallLocation": r"C:\Program Files\WindowsApps\Microsoft.WindowsTerminal_1.19.10573.0_x64__8wekyb3d8bbwe",
        },
        {
            "Name": "SpotifyAB.SpotifyMusic",
            "PackageFullName": "SpotifyAB.SpotifyMusic_1.238.694.0_x86__zpdnekdrzrea0",
            "Version": "1.238.694.0",
            "Publisher": "CN=Spotify AB, O=Spotify AB, L=Stockholm, C=SE",
            "InstallLocation": r"C:\Program Files\WindowsApps\SpotifyAB.SpotifyMusic_1.238.694.0_x86__zpdnekdrzrea0",
        },
        {
            "Name": "Microsoft.Windows.ShellExperienceHost",
            "PackageFullName": "Microsoft.Windows.ShellExperienceHost_10.0.22621.1_neutral_neutral_cw5n1h2txyewy",
            "Version": "10.0.22621.1",
            "Publisher": "Microsoft Corporation",
            "InstallLocation": "",
        },
    ]

    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_res.stdout = json.dumps(mock_json)

    with patch("subprocess.run", return_value=mock_res):
        scanner = StoreScanner()
        items = scanner.scan()

        assert len(items) == 2
        names = [item.name for item in items]
        assert "Microsoft.WindowsTerminal" in names
        assert "SpotifyAB.SpotifyMusic" in names
        assert "Microsoft.Windows.ShellExperienceHost" not in names  # Filtered internal OS stub

        terminal = next(item for item in items if item.name == "Microsoft.WindowsTerminal")
        assert terminal.installed_version == "1.19.10573.0"
        assert terminal.package_type == PackageType.STORE_MSIX
        assert "MSIX\\" in terminal.id


def test_store_scanner_error_handling():
    mock_res = MagicMock()
    mock_res.returncode = 1
    mock_res.stderr = "PowerShell access denied"

    with patch("subprocess.run", return_value=mock_res):
        scanner = StoreScanner()
        items = scanner.scan()
        assert items == []

    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="powershell", timeout=5)):
        scanner = StoreScanner(timeout_sec=5)
        items = scanner.scan()
        assert items == []

