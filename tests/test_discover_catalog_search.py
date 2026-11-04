"""Tests for Task 9: Discover, Catalog, and Search functionality."""

import pytest
from unittest.mock import MagicMock, patch
from winget_updater.models import PackageType, ProgramItem, UpdateAction
from winget_updater.winget.catalog import (
    CURATED_CATALOG,
    get_popular_catalog,
    search_catalog_packages,
)
from winget_updater.winget.client import WingetClient, WingetPackageEntry


def test_curated_catalog_rich_content():
    """Verify curated catalog has a rich set of essential Windows applications."""
    assert len(CURATED_CATALOG) >= 40
    categories = {entry.category for entry in CURATED_CATALOG}
    assert "Development" in categories
    assert "Browsers" in categories
    assert "Utilities" in categories
    assert "Media" in categories
    assert "Communication" in categories

    ids = [entry.id for entry in CURATED_CATALOG]
    assert "Microsoft.VisualStudioCode" in ids
    assert "Google.Chrome" in ids
    assert "Git.Git" in ids
    assert "7zip.7zip" in ids
    assert "VideoLAN.VLC" in ids


def test_catalog_cross_references_installed_state():
    """Verify catalog properly differentiates installed vs not installed apps."""
    installed = [
        ProgramItem(
            name="Google Chrome",
            id="Google.Chrome",
            installed_version="133.0.6943.142",
            latest_version="133.0.6943.142",
            package_type=PackageType.WIN32_EXE,
            source="winget",
            action=UpdateAction.UP_TO_DATE,
        )
    ]
    catalog = get_popular_catalog(installed_programs=installed)

    chrome_item = next(it for it in catalog if it.id == "Google.Chrome")
    assert chrome_item.installed_version == "133.0.6943.142"
    assert chrome_item.action == UpdateAction.UP_TO_DATE
    assert "Installed" in chrome_item.notes

    vscode_item = next(it for it in catalog if it.id == "Microsoft.VisualStudioCode")
    assert vscode_item.installed_version == "Not Installed"
    assert vscode_item.action == UpdateAction.AVAILABLE


def test_search_catalog_filtering():
    """Verify fast search over curated catalog with single and multi-word queries."""
    results_single = search_catalog_packages("chrome")
    assert any(it.id == "Google.Chrome" for it in results_single)

    results_multi = search_catalog_packages("visual studio code")
    assert any(it.id == "Microsoft.VisualStudioCode" for it in results_multi)

    results_cat = search_catalog_packages("browsers")
    assert len(results_cat) >= 3
    assert any(it.id == "Google.Chrome" for it in results_cat)
    assert any(it.id == "Mozilla.Firefox" for it in results_cat)


def test_search_catalog_merges_live_winget_and_secondary():
    """Verify catalog search deduplicates and merges live winget search results."""
    mock_winget_entry = WingetPackageEntry(
        name="Custom Winget Tool",
        id="Custom.Tool",
        version="1.0.0",
        source="winget",
    )
    mock_secondary_item = ProgramItem(
        name="fastapi",
        id="fastapi",
        installed_version="Not Installed",
        latest_version="0.115.0",
        package_type=PackageType.PIP,
        source="pip",
        action=UpdateAction.AVAILABLE,
    )

    merged = search_catalog_packages(
        "custom",
        winget_entries=[mock_winget_entry],
        secondary_items=[mock_secondary_item],
    )

    ids = [it.id for it in merged]
    assert "Custom.Tool" in ids
    assert "fastapi" in ids


def test_winget_client_clean_version_and_alias():
    """Verify WingetClient table parsing strips moniker/tag noise and has search_catalog alias."""
    client = WingetClient()
    assert hasattr(client, "search_catalog")
    assert callable(client.search_catalog)

    sample_output = (
        "Name                                     Id                         Version      Match           Source\n"
        "-------------------------------------------------------------------------------------------------------\n"
        "Microsoft Visual Studio Code             Microsoft.VisualStudioCode 1.97.0       Moniker: vscode winget\n"
        "Alex313031.Codium                         Alex313031.Codium          1.93.1.24277 Tag: vscode     winget\n"
    )
    parsed = client._parse_table_output(sample_output)
    assert "microsoft.visualstudiocode" in parsed
    entry = parsed["microsoft.visualstudiocode"]
    assert entry.version == "1.97.0"
    assert "Moniker" not in entry.version


def test_catalog_mode_isolation_and_filtering():
    """Verify MainWindow logic isolates catalog view from installed programs inventory."""
    from winget_updater.gui.app import MainWindow
    import tkinter as tk

    try:
        root = tk.Tk()
        root.withdraw()
    except Exception:
        pytest.skip("Tkinter display not available")

    try:
        app = MainWindow()
        app.all_programs = [
            ProgramItem(name="App A", id="app.a", installed_version="1.0", action=UpdateAction.UP_TO_DATE),
            ProgramItem(name="App B", id="app.b", installed_version="2.0", action=UpdateAction.AVAILABLE),
        ]

        # Switch to Software Catalog
        app._on_sidebar_filter_changed("Software Catalog")
        assert app.active_filter == "Software Catalog"
        assert len(app.catalog_items) >= 40
        assert app.filtered_programs == app.catalog_items

        # Change search query while on Software Catalog
        app.search_query = "Firefox"
        app.apply_filter()
        assert len(app.filtered_programs) >= 1
        assert any("Firefox" in it.name for it in app.filtered_programs)

        # Clear search
        app.search_query = ""
        app.apply_filter()
        assert len(app.filtered_programs) >= 40

        # Change category filter in catalog
        app.active_category = "Win32 Applications"
        app.apply_filter()
        assert len(app.filtered_programs) >= 1
        for it in app.filtered_programs:
            assert it.package_type in (PackageType.WIN32_EXE, PackageType.WIN32_MSI)

        root.destroy()
    except Exception:
        try:
            root.destroy()
        except Exception:
            pass
        raise

