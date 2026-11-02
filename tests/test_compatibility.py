"""Unit tests for system compatibility checks (Architecture, OS build, Disk, and CPU)."""

from unittest.mock import MagicMock
from winget_updater.compatibility.checker import CompatibilityChecker
from winget_updater.compatibility.system_info import SystemInfoProvider
from winget_updater.models import CompatibilityStatus, ProgramItem
from winget_updater.winget.client import WingetPackageDetails


def test_compatibility_architecture_checks():
    sys_mock = MagicMock(spec=SystemInfoProvider)
    sys_mock.get_windows_build.return_value = 26100
    sys_mock.is_windows_11.return_value = True
    sys_mock.get_free_disk_space_mb.return_value = 10000.0
    sys_mock.get_cpu_load_percent.return_value = 10.0

    checker = CompatibilityChecker(system_info=sys_mock)
    item = ProgramItem(name="TestApp", id="Test.App")

    # Host x64 running x64
    sys_mock.get_architecture.return_value = "x64"
    details_x64 = WingetPackageDetails(id="Test.App", version="1.0", architecture="x64")
    res = checker.check(item, details_x64)
    assert res.is_compatible is True
    assert res.arch_ok is True

    # Host x64 running x86 (WOW64 supported)
    details_x86 = WingetPackageDetails(id="Test.App", version="1.0", architecture="x86")
    res = checker.check(item, details_x86)
    assert res.is_compatible is True
    assert res.arch_ok is True

    # Host x64 running native ARM64 (Incompatible!)
    details_arm = WingetPackageDetails(id="Test.App", version="1.0", architecture="arm64")
    res = checker.check(item, details_arm)
    assert res.is_compatible is False
    assert res.arch_ok is False
    assert "Incompatible architecture" in res.reasons[0]


def test_compatibility_os_build_checks():
    sys_mock = MagicMock(spec=SystemInfoProvider)
    sys_mock.get_architecture.return_value = "x64"
    sys_mock.get_free_disk_space_mb.return_value = 10000.0
    sys_mock.get_cpu_load_percent.return_value = 10.0

    checker = CompatibilityChecker(system_info=sys_mock)
    item = ProgramItem(name="TestApp", id="Test.App")

    # Host is Windows 10 (build 19045) -> Incompatible!
    sys_mock.get_windows_build.return_value = 19045
    sys_mock.is_windows_11.return_value = False
    res = checker.check(item)
    assert res.is_compatible is False
    assert res.os_ok is False
    assert "does not meet Windows 11 requirement" in res.reasons[0]

    # Host is Windows 11 (build 22000)
    sys_mock.get_windows_build.return_value = 22000
    sys_mock.is_windows_11.return_value = True

    # Package requires 10.0.22621 (Win 11 22H2)
    details = WingetPackageDetails(id="Test.App", version="1.0", min_os_version="10.0.22621")
    res = checker.check(item, details)
    assert res.is_compatible is False
    assert res.os_ok is False
    assert "requires Windows build >= 22621" in res.reasons[0]


def test_compatibility_disk_space_checks():
    sys_mock = MagicMock(spec=SystemInfoProvider)
    sys_mock.get_architecture.return_value = "x64"
    sys_mock.get_windows_build.return_value = 26100
    sys_mock.is_windows_11.return_value = True
    sys_mock.get_cpu_load_percent.return_value = 10.0

    # Free space only 250 MB (threshold is 500 MB)
    sys_mock.get_free_disk_space_mb.return_value = 250.0

    checker = CompatibilityChecker(min_disk_mb=500.0, system_info=sys_mock)
    item = ProgramItem(name="TestApp", id="Test.App")
    res = checker.check(item)

    assert res.is_compatible is False
    assert res.disk_ok is False
    assert "Insufficient disk space" in res.reasons[0]


def test_compatibility_cpu_capacity_checks():
    sys_mock = MagicMock(spec=SystemInfoProvider)
    sys_mock.get_architecture.return_value = "x64"
    sys_mock.get_windows_build.return_value = 26100
    sys_mock.is_windows_11.return_value = True
    sys_mock.get_free_disk_space_mb.return_value = 5000.0

    # CPU pegged at 98%
    sys_mock.get_cpu_load_percent.return_value = 98.0

    checker = CompatibilityChecker(max_cpu_percent=95.0, system_info=sys_mock)
    item = ProgramItem(name="TestApp", id="Test.App")
    res = checker.check(item)

    assert res.cpu_ok is False
    assert res.status == CompatibilityStatus.WARNING
    assert "High CPU utilization" in res.reasons[0]

