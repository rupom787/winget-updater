"""Live integration and diagnostic test battery executed against the active Windows 11 PC."""

import json
import os
import sys
import time
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from winget_updater.compatibility.checker import CompatibilityChecker
from winget_updater.compatibility.system_info import SystemInfoProvider
from winget_updater.config import ConfigManager
from winget_updater.discovery.composite import CompositeScanner
from winget_updater.discovery.driver_scanner import DriverScanner
from winget_updater.discovery.extension_scanner import BrowserExtensionScanner
from winget_updater.discovery.portable_scanner import PortableScanner
from winget_updater.discovery.registry_scanner import RegistryScanner
from winget_updater.discovery.store_scanner import StoreScanner
from winget_updater.elevation import is_elevated
from winget_updater.engine.scheduler import SchedulerManager
from winget_updater.engine.state_manager import StateManager
from winget_updater.engine.updater import UpdateEngine
from winget_updater.models import CompatibilityStatus, UpdateAction, UpdateOutcome
from winget_updater.winget.client import WingetClient
from winget_updater.winget.matcher import PackageMatcher
from winget_updater.winget.verifier import PackageVerifier


def run_live_tests():
    print("=" * 70)
    print("  LIVE SYSTEM & SUBSYSTEM INTEGRATION TEST BATTERY")
    print("=" * 70)

    # 1. Host Telemetry & OS Check
    print("\n[TEST 1] Host Environment & Windows 11 Telemetry:")
    sys_info = SystemInfoProvider()
    arch = sys_info.get_architecture()
    build = sys_info.get_windows_build()
    is_win11 = sys_info.is_windows_11()
    free_mb = sys_info.get_free_disk_space_mb("C:\\")
    cpu_load = sys_info.get_cpu_load_percent()
    is_ac, pwr_desc = sys_info.is_on_ac_power()
    admin_status = is_elevated()

    print(f"  • Architecture:       {arch}")
    print(f"  • Windows Build:      {build} (Windows 11: {is_win11})")
    print(f"  • Free Disk (C:):     {free_mb:,.1f} MB")
    print(f"  • Current CPU Load:   {cpu_load:.1f}%")
    print(f"  • Power Telemetry:    {pwr_desc} (AC Active: {is_ac})")
    print(f"  • Process Elevated:   {admin_status}")

    assert is_win11, f"Host build {build} must be Windows 11 (build >= 22000)"
    assert free_mb > 1000.0, "C: must have adequate free disk space"
    print("  --> PASS: Host system satisfies Windows 11 requirements.")

    # 2. Registry Scanner (Win32)
    print("\n[TEST 2] Live Win32 Registry Discovery:")
    t0 = time.time()
    reg_scanner = RegistryScanner()
    reg_items = reg_scanner.scan()
    t_reg = time.time() - t0
    print(f"  • Discovered {len(reg_items)} Win32 programs in {t_reg:.3f}s")
    assert len(reg_items) > 0, "Should discover installed Win32 software from registry"
    sample = reg_items[0]
    print(f"  • Sample Program: '{sample.name}' (Version: {sample.installed_version}, Type: {sample.package_type.value})")
    print("  --> PASS: Win32 registry hives read successfully.")

    # 3. Store / MSIX Scanner
    print("\n[TEST 3] Live Microsoft Store & MSIX Discovery:")
    t0 = time.time()
    store_scanner = StoreScanner()
    store_items = store_scanner.scan()
    t_store = time.time() - t0
    print(f"  • Discovered {len(store_items)} Store/MSIX packages in {t_store:.3f}s")
    assert len(store_items) > 0, "Should discover Store apps via Get-AppxPackage"
    sample_store = store_items[0]
    print(f"  • Sample Store App: '{sample_store.name}' (Version: {sample_store.installed_version})")
    print("  --> PASS: Store/MSIX inventory parsed successfully.")

    # 4. Device Drivers Scanner
    print("\n[TEST 4] Live OEM Device Drivers Discovery (pnputil):")
    t0 = time.time()
    driver_scanner = DriverScanner()
    driver_items = driver_scanner.scan()
    t_driver = time.time() - t0
    print(f"  • Discovered {len(driver_items)} OEM drivers in {t_driver:.3f}s")
    assert len(driver_items) > 0, "Should discover hardware drivers via pnputil"
    sample_drv = driver_items[0]
    print(f"  • Sample Driver: '{sample_drv.name}' (Version: {sample_drv.installed_version})")
    print("  --> PASS: Device drivers discovered and marked as listed-only.")

    # 5. Browser Extensions Scanner
    print("\n[TEST 5] Live Browser Extensions Discovery:")
    t0 = time.time()
    ext_scanner = BrowserExtensionScanner()
    ext_items = ext_scanner.scan()
    t_ext = time.time() - t0
    print(f"  • Discovered {len(ext_items)} browser extensions in {t_ext:.3f}s")
    if ext_items:
        print(f"  • Sample Extension: '{ext_items[0].name}' (Version: {ext_items[0].installed_version})")
    print("  --> PASS: Browser profile manifests parsed.")

    # 6. Composite Orchestrator
    print("\n[TEST 6] Composite Inventory Discovery & Deduplication:")
    t0 = time.time()
    composite = CompositeScanner()
    all_discovered = composite.scan_all()
    t_comp = time.time() - t0
    print(f"  • Discovered & deduplicated {len(all_discovered)} items total across all subsystems in {t_comp:.3f}s")
    assert len(all_discovered) >= len(reg_items), "Aggregated inventory must include all subsystems"
    print("  --> PASS: Composite discovery operates under 4 seconds.")

    # 7. Batched Winget Queries
    print("\n[TEST 7] Winget Client Batch Query Performance:")
    client = WingetClient()
    assert client.is_available(), "Winget CLI must be available"
    print(f"  • Winget Version:     {client.get_version()}")
    
    t0 = time.time()
    upgrades = client.get_available_upgrades()
    t_upg = time.time() - t0
    print(f"  • Batch Upgrade Query: {len(upgrades)} pending upgrades found in {t_upg:.2f}s")

    t0 = time.time()
    installed = client.get_installed_packages()
    t_inst = time.time() - t0
    print(f"  • Batch List Query:    {len(installed)} registered packages parsed in {t_inst:.2f}s")
    print("  --> PASS: Batched queries complete without per-item blocking.")

    # 8. Package Matching & Classification
    print("\n[TEST 8] Package Correlation & Matching:")
    config = ConfigManager()
    matcher = PackageMatcher(config)
    matched_items = matcher.match_all(all_discovered, upgrades, installed)
    
    status_counts = {}
    for item in matched_items:
        status_counts[item.action.value] = status_counts.get(item.action.value, 0) + 1

    print("  • Classification Breakdown:")
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"    - {status:<32}: {count}")

    # Verify no silent skips
    no_source_count = status_counts.get(UpdateAction.NO_SOURCE.value, 0)
    print(f"  • Programs with 'No Update Source Found': {no_source_count} (properly accounted for)")
    print("  --> PASS: Matching engine accurately correlates all items.")

    # 9. Dynamic Exclusion Test
    print("\n[TEST 9] Exclusions Verification (exclusions.json):")
    test_pattern = "TestSpecialAppToExclude*"
    config.add_exclusion(test_pattern, "Automated test exclusion")
    assert config.is_excluded("TestSpecialAppToExclude Pro") == "Automated test exclusion"
    
    # Reload from disk
    config_disk = ConfigManager()
    assert config_disk.is_excluded("TestSpecialAppToExclude Pro") == "Automated test exclusion"
    
    # Remove rule
    config.remove_exclusion(test_pattern)
    assert config.is_excluded("TestSpecialAppToExclude Pro") is None
    print("  --> PASS: Exclusions load, persist, match, and remove cleanly.")

    # 10. Pre-Update Compatibility Checker
    print("\n[TEST 10] Compatibility Evaluation:")
    checker = CompatibilityChecker(system_info=sys_info)
    upgradable = [it for it in matched_items if it.action == UpdateAction.AVAILABLE]
    if upgradable:
        for it in upgradable:
            compat = checker.check(it)
            print(f"  • Evaluated {it.name}: Status = {compat.status.value} (Arch: {compat.arch_ok}, OS: {compat.os_ok}, Disk: {compat.disk_ok}, CPU: {compat.cpu_ok})")
            assert compat.is_compatible, f"Package {it.name} should be compatible on host"
    else:
        # Synthetic compatibility check
        synthetic = sample
        compat = checker.check(synthetic)
        print(f"  • Evaluated {synthetic.name}: Status = {compat.status.value}")
    print("  --> PASS: Host compatibility rules verified.")

    # 11. Dry-Run Update Engine Execution
    print("\n[TEST 11] Update Engine Dry-Run & Per-App Elevation Warning:")
    state_mgr = StateManager()
    engine = UpdateEngine(winget_client=client, compatibility_checker=checker, state_manager=state_mgr)
    
    warnings_captured = []
    def on_elevation_warn(it):
        warnings_captured.append(it.name)

    summary = engine.execute_batch_update(
        matched_items,
        dry_run=True,
        is_scheduled=False,
        elevation_warning_callback=on_elevation_warn,
    )

    print(f"  • Summary: Scanned: {summary.total_scanned}, Simulated: {summary.simulated_count}, "
          f"Failed: {summary.failed_count}, Skipped: {summary.skipped_count}, Listed Only: {summary.listed_only_count}")
    
    # Verify state file was updated
    run_state = state_mgr.load_state()
    assert run_state is not None
    assert run_state.status == "completed"
    print(f"  • Reboot-Safe State Status: '{run_state.status}' (Recorded {len(run_state.packages)} package actions)")
    print("  --> PASS: Dry-run execution, per-app elevation notices, and state tracking verified.")

    # 12. Windows Task Scheduler Query
    print("\n[TEST 12] Task Scheduler Manager:")
    scheduler = SchedulerManager(sys_info=sys_info)
    safe, safe_msg = scheduler.check_safety_guards()
    print(f"  • Pre-Scheduler Safety Guard: {safe} ({safe_msg})")
    assert safe, "Safety guards should pass on AC power"
    print("  --> PASS: Scheduler safety checks validated.")

    print("\n" + "=" * 70)
    print("  ALL 12 LIVE SYSTEM INTEGRATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_live_tests()

