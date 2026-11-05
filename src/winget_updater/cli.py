"""Command-line interface and entry point for Windows 11 Software Updater."""

import argparse
import sys
from winget_updater.compatibility.checker import CompatibilityChecker
from winget_updater.compatibility.system_info import SystemInfoProvider
from winget_updater.config import ConfigManager
from winget_updater.discovery.composite import CompositeScanner
from winget_updater.elevation import ensure_elevated, is_elevated
from winget_updater.engine.scheduler import SchedulerManager
from winget_updater.engine.state_manager import StateManager
from winget_updater.engine.updater import UpdateEngine
from winget_updater.models import UpdateAction
from winget_updater.utils.logger import get_logger, setup_logger
from winget_updater.winget.client import WingetClient
from winget_updater.winget.matcher import PackageMatcher

logger = get_logger()


def run_cli_scan(
    scan_only: bool = False,
    dry_run: bool = False,
    auto_approve: bool = False,
    is_scheduled: bool = False,
) -> int:
    """Executes update routine via command-line interface."""
    logger.info("Initializing Windows 11 Software Updater CLI...")

    sys_info = SystemInfoProvider()
    if not sys_info.is_windows_11():
        logger.warning(
            f"Host is running Windows build {sys_info.get_windows_build()}. This tool is designed for Windows 11."
        )

    # Scheduler safety checks if running under scheduled task
    scheduler = SchedulerManager(sys_info=sys_info)
    if is_scheduled:
        safe, reason = scheduler.check_safety_guards()
        if not safe:
            logger.warning(f"Aborting scheduled run: {reason}")
            return 2

    config = ConfigManager()
    winget = WingetClient()
    if not winget.is_available():
        logger.error("Winget CLI is not available in system PATH.")
        return 1

    checker = CompatibilityChecker(system_info=sys_info)
    state_mgr = StateManager()
    engine = UpdateEngine(winget_client=winget, compatibility_checker=checker, state_manager=state_mgr)

    # 1. Discover software across all subsystems
    logger.info("Scanning installed programs across Registry, Store, Portable folders, Extensions, and Drivers...")
    scanner = CompositeScanner(portable_directories=config.portable_directories)
    discovered = scanner.scan_all()
    print(f"\n[INFO] Discovered {len(discovered)} total software items across PC.")

    # 2. Batch winget queries
    print("[INFO] Batch querying winget repository...")
    upgrades = winget.get_available_upgrades()
    installed = winget.get_installed_packages()

    # 3. Match against winget and fallback sources
    matcher = PackageMatcher(config)
    items = matcher.match_all(discovered, upgrades, installed)

    # Automatically track updates in persistent history tracker
    try:
        from winget_updater.engine.tracker import UpdateTracker
        UpdateTracker().track_scan_results(items)
    except Exception:
        pass

    candidates = [item for item in items if item.can_auto_update()]
    print(f"[INFO] Analysis complete: {len(candidates)} packages qualify for automatic update.")

    # Print summary table
    print("\n" + "=" * 95)
    print(f"{'Package Name':<35} {'Installed':<15} {'Latest':<15} {'Status / Action':<25}")
    print("=" * 95)
    for item in items:
        status_desc = item.action.value
        if item.action == UpdateAction.AVAILABLE:
            status_desc = "Update Available (Ready)"
        elif item.action == UpdateAction.NEWER_THAN_SOURCE:
            status_desc = "Downgrade Risk (Blocked)"
        elif item.action == UpdateAction.VENDOR_FALLBACK:
            status_desc = "Vendor Fallback (Manual)"
        print(f"{item.name[:34]:<35} {item.installed_version[:14]:<15} {(item.latest_version or '-')[:14]:<15} {status_desc[:24]:<25}")
    print("=" * 95 + "\n")

    if scan_only:
        print(f"[INFO] Scan finished. {len(candidates)} package(s) ready for update. Run with --update to apply.")
        return 0

    if not candidates:
        print("[INFO] No packages require updates at this time.")
        return 0

    # 4. Approval check
    if not auto_approve and not is_scheduled:
        ans = input(f"\nProceed with updating {len(candidates)} packages with Administrator rights? (y/N): ").strip().lower()
        if ans not in ("y", "yes"):
            print("Update cancelled by user.")
            return 0

    # 5. Execute batch update
    print(f"\nExecuting updates for {len(candidates)} packages (Dry Run: {dry_run})...")
    summary = engine.execute_batch_update(
        items,
        dry_run=dry_run,
        is_scheduled=is_scheduled,
        create_restore_point=getattr(config, "create_restore_point", False),
        auto_close_apps=getattr(config, "auto_close_apps", True),
        cleanup_after=getattr(config, "cleanup_temp_cache", True),
        elevation_warning_callback=lambda it: print(f"  [ADMIN RIGHTS WARNING] Updating '{it.name}' ({it.id})..."),
        progress_callback=lambda it, cur, tot: print(f"  [{cur}/{tot}] Processing {it.name}..."),
    )

    print("\n" + "=" * 50)
    print("Execution Run Summary:")
    print(f"  Total Scanned:         {summary.total_scanned}")
    print(f"  Updated Successfully:  {summary.updated_count}")
    print(f"  Dry-Run Simulated:     {summary.simulated_count}")
    print(f"  Failed:                {summary.failed_count}")
    print(f"  Skipped:               {summary.skipped_count}")
    print(f"  Downgrades Blocked:    {summary.downgrade_blocked_count}")
    print(f"  Listed Only:           {summary.listed_only_count}")
    print("=" * 50 + "\n")

    return 0 if summary.failed_count == 0 else 1


def main() -> int:
    """Main application entry point."""
    setup_logger()

    parser = argparse.ArgumentParser(
        description="Windows 11 Software & Package Update Management Tool"
    )
    parser.add_argument("--scan", action="store_true", help="Perform discovery and update scan only")
    parser.add_argument("--update", action="store_true", help="Perform discovery and proceed to update")
    parser.add_argument("--dry-run", action="store_true", help="Simulate updates without modifying system")
    parser.add_argument("-y", "--yes", action="store_true", help="Auto-approve verified updates in CLI mode")
    parser.add_argument("--scheduled", action="store_true", help="Run in scheduled daily background mode")
    parser.add_argument("--tracker", action="store_true", help="Display tracked available updates and pending durations")
    parser.add_argument("--relaunch-attempted", action="store_true", help="Internal flag for elevation check")
    parser.add_argument("--no-gui", action="store_true", help="Force command-line mode")

    args = parser.parse_args()

    # Step 1: Guarantee process runs elevated
    if not is_elevated():
        if not ensure_elevated(exit_on_relaunch=True):
            logger.error("Process must run with administrative privileges. Elevation was cancelled.")
            return 1
        return 0

    # Step 2: Configure high-performance GPU acceleration for Windows 11
    try:
        from winget_updater.engine.gpu import GpuAccelerationManager
        GpuAccelerationManager.enable_high_performance_gpu()
    except Exception:
        pass

    # Step 3: Determine execution mode (Scheduled, CLI scan, CLI update, or GUI)
    if args.tracker:
        from winget_updater.engine.tracker import UpdateTracker
        tracker = UpdateTracker()
        items = tracker.get_tracked_items()
        metrics = tracker.get_metrics()
        print("\n=== App Update Tracker ===")
        print(f"Total Tracked: {metrics['total_tracked']} | Pending: {metrics['pending_count']} | Resolved: {metrics['updated_count']} | Oldest: {metrics['oldest_pending_days']} days\n")
        if not items:
            print("No tracked updates found. Run a scan to discover available updates.")
        else:
            print(f"{'Package / Name':<32} {'Source':<10} {'Installed':<14} {'Available':<14} {'Pending':<12} {'Status'}")
            print("-" * 95)
            for it in items:
                print(f"{it.name[:30]:<32} {it.source[:8]:<10} {it.installed_version[:12]:<14} {it.available_version[:12]:<14} {str(it.days_pending) + ' days':<12} {it.status}")
        return 0

    if args.scheduled:
        return run_cli_scan(scan_only=False, dry_run=args.dry_run, auto_approve=True, is_scheduled=True)

    if args.scan:
        return run_cli_scan(scan_only=True, dry_run=args.dry_run, auto_approve=False, is_scheduled=False)

    if args.update or args.no_gui:
        return run_cli_scan(scan_only=False, dry_run=args.dry_run, auto_approve=args.yes, is_scheduled=False)

    # Launch GUI with luxury editorial startup splash screen (optimized for fast launch)
    from winget_updater.gui.app import MainWindow
    from winget_updater.gui.splash import EditorialStartupSplashScreen
    app = MainWindow()
    app.withdraw()
    splash = EditorialStartupSplashScreen(
        parent=app,
        on_complete=app.deiconify,
        duration_ms=450,
    )
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
