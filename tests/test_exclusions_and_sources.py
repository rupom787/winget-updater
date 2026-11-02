"""Unit tests for exclusions and user-maintained vendor source lists."""

import json
from pathlib import Path
from winget_updater.config import ConfigManager, ExclusionRule, VendorSourceEntry


def test_exclusions_json_roundtrip(tmp_path):
    excl_file = tmp_path / "exclusions.json"
    initial_data = [
        {"pattern": "Oracle.JavaRuntimeEnvironment", "reason": "Pinned for legacy ERP"},
        {"pattern": "VirtualBox*", "reason": "Custom kernel modules installed"},
    ]
    with open(excl_file, "w", encoding="utf-8") as f:
        json.dump(initial_data, f)

    mgr = ConfigManager(base_dir=tmp_path, exclusions_path=excl_file)

    assert len(mgr.exclusions) == 2
    assert mgr.is_excluded("VirtualBox 7.0") == "Custom kernel modules installed"
    assert mgr.is_excluded("AnyName", package_id="Oracle.JavaRuntimeEnvironment") == "Pinned for legacy ERP"
    assert mgr.is_excluded("Git") is None

    # Add new exclusion via API (same as GUI)
    mgr.add_exclusion("Steam*", "Gaming client pinned")
    assert len(mgr.exclusions) == 3

    # Reload from disk to verify single source of truth
    new_mgr = ConfigManager(base_dir=tmp_path, exclusions_path=excl_file)
    assert len(new_mgr.exclusions) == 3
    assert new_mgr.is_excluded("Steam Client") == "Gaming client pinned"

    # Remove exclusion
    removed = new_mgr.remove_exclusion("VirtualBox*")
    assert removed is True
    assert len(new_mgr.exclusions) == 2
    assert new_mgr.is_excluded("VirtualBox 7.0") is None


def test_vendor_sources_json_matching(tmp_path):
    sources_file = tmp_path / "sources.json"
    data = {
        "sources": [
            {
                "name": "Acme Database Viewer",
                "match_name": "AcmeDB*",
                "installer_url": "https://acme.com/dl/setup.exe",
                "version": "4.1.0",
                "expected_sha256": "abcdef123456",
            }
        ]
    }
    with open(sources_file, "w", encoding="utf-8") as f:
        json.dump(data, f)

    mgr = ConfigManager(base_dir=tmp_path, sources_path=sources_file)

    match = mgr.match_vendor_source("AcmeDB Enterprise Edition")
    assert match is not None
    assert match.name == "Acme Database Viewer"
    assert match.installer_url == "https://acme.com/dl/setup.exe"
    assert match.version == "4.1.0"

    no_match = mgr.match_vendor_source("CompletelyOtherApp")
    assert no_match is None

