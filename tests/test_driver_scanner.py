"""Unit tests for third-party device driver discovery using pnputil."""

from winget_updater.discovery.driver_scanner import DriverScanner
from winget_updater.models import PackageType

SAMPLE_PNPUTIL_OUTPUT = """Microsoft PnP Utility

Published Name:     oem44.inf
Original Name:      amdacpbus.inf
Provider Name:      Advanced Micro Devices, Inc.
Class Name:         System
Class GUID:         {4d36e97d-e325-11ce-bfc1-08002be10318}
Driver Version:     12/23/2025 6.0.2.118
Signer Name:        Microsoft Windows Hardware Compatibility Publisher

Published Name:     oem19.inf
Original Name:      nvvad.inf
Provider Name:      NVIDIA Corporation
Class Name:         MEDIA
Class GUID:         {4d36e96c-e325-11ce-bfc1-08002be10318}
Driver Version:     08/04/2026 4.92.0.0
Signer Name:        Microsoft Windows Hardware Compatibility Publisher
"""


def test_driver_scanner_parses_pnputil_output():
    scanner = DriverScanner()
    items = scanner.parse_pnputil_output(SAMPLE_PNPUTIL_OUTPUT)

    assert len(items) == 2

    d1 = items[0]
    assert "amdacpbus.inf" in d1.name
    assert d1.installed_version == "6.0.2.118"
    assert d1.id == "Driver\\oem44.inf"
    assert d1.package_type == PackageType.DRIVER
    assert d1.publisher == "Advanced Micro Devices, Inc."
    assert "listed only" in d1.notes.lower()

    d2 = items[1]
    assert "nvvad.inf" in d2.name
    assert d2.installed_version == "4.92.0.0"
    assert d2.id == "Driver\\oem19.inf"
    assert d2.publisher == "NVIDIA Corporation"

