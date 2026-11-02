"""Unit tests for version comparator and semantic parsing."""

from winget_updater.winget.version_comparator import clean_version_string, compare_versions


def test_clean_version_string():
    assert clean_version_string("v1.2.3") == "1.2.3"
    assert clean_version_string("V2.0") == "2.0"
    assert clean_version_string("  1.4.0+build123  ") == "1.4.0"
    assert clean_version_string("3.0.0-beta") == "3.0.0-beta"


def test_compare_versions_standard():
    # v1 < v2 -> -1
    assert compare_versions("1.0.0", "1.0.1") == -1
    assert compare_versions("1.11.1", "1.11.2") == -1
    assert compare_versions("2.4", "2.10") == -1

    # v1 == v2 -> 0
    assert compare_versions("1.2.3", "1.2.3") == 0
    assert compare_versions("v1.2.3", "1.2.3") == 0
    assert compare_versions("2.0.0", "v2.0.0") == 0

    # v1 > v2 -> 1 (Downgrade risk condition!)
    assert compare_versions("2.0.0", "1.9.9") == 1
    assert compare_versions("1.11.2", "1.11.1") == 1
    assert compare_versions("26.1027.3384.0", "25.0.0.0") == 1


def test_compare_versions_fallback():
    # Non-PEP 440 versions
    assert compare_versions("1.0.5.1_is1", "1.0.5.2_is1") == -1
    assert compare_versions("1.0.5.2_is1", "1.0.5.1_is1") == 1
    assert compare_versions("2024-01-01", "2024-02-01") == -1


def test_compare_versions_unknown_or_missing():
    assert compare_versions(None, "1.0.0") is None
    assert compare_versions("1.0.0", None) is None
    assert compare_versions("Unknown", "1.0.0") is None
    assert compare_versions("1.0.0", "Unknown") is None
    assert compare_versions("", "") is None

