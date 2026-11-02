"""Unit tests for Windows Registry software scanner with mocked winreg."""

import winreg
from unittest.mock import MagicMock, patch
from winget_updater.discovery.registry_scanner import RegistryScanner
from winget_updater.models import PackageType


def test_registry_scanner_discovers_programs():
    scanner = RegistryScanner()

    mock_entries = {
        "App1": {
            "DisplayName": "Visual Studio Code",
            "DisplayVersion": "1.90.0",
            "Publisher": "Microsoft Corporation",
            "InstallLocation": r"C:\Program Files\Microsoft VS Code",
            "UninstallString": r'"C:\Program Files\Microsoft VS Code\unins000.exe"',
        },
        "App2": {
            "DisplayName": "Git version 2.45.0",
            "DisplayVersion": "2.45.0",
            "Publisher": "The Git Development Community",
            "UninstallString": r'"C:\Program Files\Git\unins000.exe"',
        },
        "App3_MSI": {
            "DisplayName": "Node.js",
            "DisplayVersion": "20.12.0",
            "Publisher": "Node.js Foundation",
            "UninstallString": "MsiExec.exe /I{12345678-ABCD-1234-ABCD-1234567890AB}",
            "WindowsInstaller": 1,
        },
        "HiddenComponent": {
            "DisplayName": "Internal Driver Component",
            "SystemComponent": 1,
        },
    }

    def mock_open_key(root, subkey, reserved=0, access=0):
        mock_key = MagicMock()
        return mock_key

    with patch("winreg.OpenKey") as mock_open:
        def open_side_effect(root, subkey, reserved=0, access=0):
            k = MagicMock()
            k.__enter__.return_value = k
            if subkey in [s[1] for s in scanner.targets]:
                k.name = "root"
            else:
                k.name = subkey
            return k

        mock_open.side_effect = open_side_effect

        def mock_query_info(key):
            return (len(mock_entries), 0, 0)

        def mock_enum_key(key, index):
            keys = list(mock_entries.keys())
            return keys[index]

        with patch("winreg.QueryInfoKey", side_effect=mock_query_info), \
             patch("winreg.EnumKey", side_effect=mock_enum_key), \
             patch("winreg.QueryValueEx") as mock_query_val:

            def query_val_side_effect(key, val_name):
                # Determine which entry from key.name
                entry_data = mock_entries.get(key.name, {})
                if val_name in entry_data:
                    return (entry_data[val_name], 1)
                raise OSError("Value not found")

            mock_query_val.side_effect = query_val_side_effect

            # Restrict to single target for controlled test
            scanner.targets = [(winreg.HKEY_LOCAL_MACHINE, "test_subkey", 0, "TestHive")]
            results = scanner.scan()

            assert len(results) == 3
            names = [r.name for r in results]
            assert "Visual Studio Code" in names
            assert "Git version 2.45.0" in names
            assert "Node.js" in names
            assert "Internal Driver Component" not in names  # Filtered because SystemComponent=1

            # Check MSI vs EXE detection
            node_item = next(r for r in results if r.name == "Node.js")
            assert node_item.package_type == PackageType.WIN32_MSI

            vscode_item = next(r for r in results if r.name == "Visual Studio Code")
            assert vscode_item.package_type == PackageType.WIN32_EXE
