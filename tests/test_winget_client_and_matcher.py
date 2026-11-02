"""Unit tests for winget table parsing, client methods, and package matching."""

from unittest.mock import MagicMock
from winget_updater.config import ConfigManager, VendorSourceEntry
from winget_updater.models import PackageType, ProgramItem, UpdateAction, UpdateOutcome
from winget_updater.winget.client import WingetClient, WingetPackageEntry
from winget_updater.winget.matcher import PackageMatcher, normalize_app_name

SAMPLE_WINGET_UPGRADE_OUTPUT = """
Name                Id                         Version Available Source
-----------------------------------------------------------------------
AB Download Manager amir1376.ABDownloadManager 1.11.1  1.11.2    winget
Git                 Git.Git                    2.44.0  2.45.0    winget
2 upgrades available.
"""

SAMPLE_WINGET_LIST_OUTPUT = """
Name                Id                         Version Available Source
-----------------------------------------------------------------------
AB Download Manager amir1376.ABDownloadManager 1.11.1  1.11.2    winget
Git                 Git.Git                    2.44.0            winget
Google Chrome       Google.Chrome              125.0.0           winget
Python 3.12         Python.Python.3.12         3.12.3            winget
"""

SAMPLE_WINGET_SHOW_OUTPUT = """
Found Git [Git.Git]
Version: 2.45.0
Publisher: The Git Development Community
Architecture: x64
Installer Type: inno
Installer Url: https://github.com/git-for-windows/git/releases/download/v2.45.0.windows.1/Git-2.45.0-64-bit.exe
Installer SHA256: 11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff
Minimum OS Version: 10.0.17763.0
"""


def test_parse_winget_table_output():
    client = WingetClient()
    upgrades = client._parse_table_output(SAMPLE_WINGET_UPGRADE_OUTPUT, is_upgrade_table=True)

    assert len(upgrades) == 2
    assert "amir1376.abdownloadmanager" in upgrades
    assert "git.git" in upgrades

    ab = upgrades["amir1376.abdownloadmanager"]
    assert ab.name == "AB Download Manager"
    assert ab.version == "1.11.1"
    assert ab.available_version == "1.11.2"
    assert ab.source == "winget"


def test_parse_winget_show_output():
    client = WingetClient()
    details = client._parse_show_output("Git.Git", SAMPLE_WINGET_SHOW_OUTPUT)

    assert details.id == "Git.Git"
    assert details.version == "2.45.0"
    assert details.architecture == "x64"
    assert details.installer_type == "inno"
    assert details.installer_sha256 == "11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff"
    assert details.min_os_version == "10.0.17763.0"


def test_normalize_app_name():
    assert normalize_app_name("Visual Studio Code (x64)") == "visual studio code"
    assert normalize_app_name("7-Zip 23.01 (64-bit)") == "7-zip 23.01"
    assert normalize_app_name("Git [x86]") == "git"


def test_package_matcher_workflow(tmp_path):
    config = ConfigManager(base_dir=tmp_path)
    config.exclusions = []
    config.vendor_sources = [
        VendorSourceEntry(
            name="Custom Internal Tool",
            match_name="InternalTool*",
            installer_url="https://internal.corp/setup.exe",
            version="3.0.0",
        )
    ]

    matcher = PackageMatcher(config)

    upgrades = {
        "git.git": WingetPackageEntry(name="Git", id="Git.Git", version="2.44.0", available_version="2.45.0", source="winget"),
    }
    installed = {
        "google.chrome": WingetPackageEntry(name="Google Chrome", id="Google.Chrome", version="125.0.0", source="winget"),
    }

    programs = [
        # 1. Update available in winget
        ProgramItem(name="Git", installed_version="2.44.0", id="Git.Git", package_type=PackageType.WIN32_EXE),
        # 2. Up to date in winget
        ProgramItem(name="Google Chrome", installed_version="125.0.0", id="Google.Chrome", package_type=PackageType.WIN32_EXE),
        # 3. Fallback to vendor source list
        ProgramItem(name="InternalTool Pro", installed_version="2.0.0", package_type=PackageType.PORTABLE),
        # 4. No update source found
        ProgramItem(name="Obscure Niche Freeware 1998", installed_version="1.0", package_type=PackageType.WIN32_EXE),
        # 5. Listed only driver
        ProgramItem(name="Realtek Audio Driver", installed_version="6.0.1", package_type=PackageType.DRIVER),
    ]

    matched = matcher.match_all(programs, upgrades, installed)

    # 1. Git -> AVAILABLE
    p_git = matched[0]
    assert p_git.action == UpdateAction.AVAILABLE
    assert p_git.latest_version == "2.45.0"
    assert p_git.is_verified_winget is True
    assert p_git.can_auto_update() is True

    # 2. Chrome -> UP_TO_DATE
    p_chrome = matched[1]
    assert p_chrome.action == UpdateAction.UP_TO_DATE
    assert p_chrome.outcome == UpdateOutcome.LISTED_ONLY

    # 3. InternalTool -> VENDOR_FALLBACK
    p_tool = matched[2]
    assert p_tool.action == UpdateAction.VENDOR_FALLBACK
    assert p_tool.outcome == UpdateOutcome.AWAITING_CONFIRMATION
    assert p_tool.vendor_installer_url == "https://internal.corp/setup.exe"
    assert p_tool.can_auto_update() is False  # Vendor fallback requires separate manual confirmation

    # 4. Obscure -> NO_SOURCE
    p_obscure = matched[3]
    assert p_obscure.action == UpdateAction.NO_SOURCE
    assert p_obscure.outcome == UpdateOutcome.LISTED_ONLY
    assert p_obscure.notes == "No update source found"

    # 5. Driver -> LIST_ONLY
    p_driver = matched[4]
    assert p_driver.action == UpdateAction.LIST_ONLY
    assert p_driver.outcome == UpdateOutcome.LISTED_ONLY


def test_smart_publisher_matching_and_custom_bindings(tmp_path):
    config = ConfigManager(base_dir=tmp_path)
    config.bind_custom_mapping("LegacyApp", "CustomVendor.LegacyApp")
    
    matcher = PackageMatcher(config)

    upgrades = {
        "customvendor.legacyapp": WingetPackageEntry(
            name="Legacy App", id="CustomVendor.LegacyApp", version="1.0", available_version="2.0", source="winget"
        ),
        "google.chrome": WingetPackageEntry(
            name="Google Chrome", id="Google.Chrome", version="125.0", available_version="126.0", source="winget", publisher="Google"
        ),
    }
    installed = {}

    programs = [
        # Bound app
        ProgramItem(name="LegacyApp", installed_version="1.0", package_type=PackageType.WIN32_EXE),
        # Smart publisher match: "Google LLC" vs "Google"
        ProgramItem(name="Google Chrome", installed_version="125.0", publisher="Google LLC", package_type=PackageType.WIN32_EXE),
    ]

    matched = matcher.match_all(programs, upgrades, installed)
    
    # Bound app should resolve to CustomVendor.LegacyApp and be AVAILABLE
    assert matched[0].id == "CustomVendor.LegacyApp"
    assert matched[0].action == UpdateAction.AVAILABLE
    assert matched[0].latest_version == "2.0"

    # Chrome should not trigger publisher mismatch false alarm
    assert matched[1].action == UpdateAction.AVAILABLE
    assert matched[1].latest_version == "126.0"


