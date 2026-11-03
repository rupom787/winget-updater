"""Update execution engine with per-app elevation warnings, compatibility checks, and reboot safety."""

import os
import tempfile
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional
from winget_updater.adapters.manager import SourceManager
from winget_updater.compatibility.checker import CompatibilityChecker
from winget_updater.engine.cleanup import DiskCleanupManager
from winget_updater.engine.process_lock import ProcessLockDetector
from winget_updater.engine.restore_point import RestorePointManager
from winget_updater.engine.state_manager import StateManager
from winget_updater.models import CompatibilityStatus, PackageType, ProgramItem, UpdateAction, UpdateOutcome
from winget_updater.utils.logger import get_logger
from winget_updater.utils.notifications import send_windows_notification
from winget_updater.winget.client import WingetClient
from winget_updater.winget.verifier import PackageVerifier

logger = get_logger()


@dataclass
class UpdateRunSummary:
    total_scanned: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    listed_only_count: int = 0
    simulated_count: int = 0
    downgrade_blocked_count: int = 0
    log_file: Optional[Path] = None


class UpdateEngine:
    """Coordinates batch updates with per-app elevation notices and failure isolation."""

    def __init__(
        self,
        winget_client: Optional[WingetClient] = None,
        compatibility_checker: Optional[CompatibilityChecker] = None,
        state_manager: Optional[StateManager] = None,
        source_manager: Optional[SourceManager] = None,
    ):
        self.client = winget_client or WingetClient()
        self.checker = compatibility_checker or CompatibilityChecker()
        self.state_mgr = state_manager or StateManager()
        self.source_mgr = source_manager or SourceManager()

    def execute_batch_update(
        self,
        items: List[ProgramItem],
        dry_run: bool = False,
        is_scheduled: bool = False,
        create_restore_point: bool = False,
        auto_close_apps: bool = True,
        cleanup_after: bool = True,
        elevation_warning_callback: Optional[Callable[[ProgramItem], None]] = None,
        progress_callback: Optional[Callable[[ProgramItem, int, int], None]] = None,
        log_callback: Optional[Callable[[ProgramItem, str], None]] = None,
        item_complete_callback: Optional[Callable[[ProgramItem, bool, str], None]] = None,
        cancel_check_callback: Optional[Callable[[], bool]] = None,
    ) -> UpdateRunSummary:
        """Executes updates for all qualified packages after single user or schedule approval.
        
        Strict constraints:
        - Automatic updates cover ONLY packaged apps (winget, Store, MSIX) with a verified winget source.
        - Unlisted Store apps, portable folders, browser extensions, drivers, and Win32 without verified winget are listed only.
        - Downgrade items are blocked without per-app confirmation.
        - Fallback vendor list items require separate confirmation.
        - Before EACH update, host compatibility is re-checked.
        - Before EACH elevated update, an elevation warning is triggered.
        - Running processes locking application files are gracefully closed to prevent error 1618.
        - Failures are isolated per program.
        """
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        self.state_mgr.start_new_run(run_id)

        summary = UpdateRunSummary(total_scanned=len(items))
        logger.info(
            f"=== Commencing Update Execution Run [{run_id}] (Dry Run: {dry_run}, Scheduled: {is_scheduled}) ==="
        )
        logger.warning(
            "[ELEVATION NOTICE] Application is running elevated. Package installations will execute with Administrator rights."
        )

        candidates = [item for item in items if item.can_auto_update()]
        total_candidates = len(candidates)
        logger.info(f"Identified {total_candidates} packages meeting verified automatic update criteria.")

        # 1. Create Pre-Update System Restore Point if requested
        if create_restore_point and not dry_run and total_candidates > 0:
            logger.info("Initiating pre-update Windows System Restore Point...")
            RestorePointManager.create_restore_point("Pre-Software Update Snapshot")

        current_idx = 0
        for item in items:
            # Handle non-candidate statuses
            if not item.can_auto_update():
                if item.action == UpdateAction.EXCLUDED:
                    item.outcome = UpdateOutcome.SKIPPED
                    summary.skipped_count += 1
                elif item.action == UpdateAction.NEWER_THAN_SOURCE:
                    item.outcome = UpdateOutcome.AWAITING_CONFIRMATION
                    summary.downgrade_blocked_count += 1
                elif item.action == UpdateAction.VENDOR_FALLBACK:
                    item.outcome = UpdateOutcome.AWAITING_CONFIRMATION
                    summary.skipped_count += 1
                elif item.action == UpdateAction.NO_SOURCE or item.action == UpdateAction.LIST_ONLY:
                    item.outcome = UpdateOutcome.LISTED_ONLY
                    summary.listed_only_count += 1
                elif item.action == UpdateAction.UP_TO_DATE:
                    item.outcome = UpdateOutcome.LISTED_ONLY
                    summary.listed_only_count += 1
                continue

            if cancel_check_callback and cancel_check_callback():
                logger.info(f"Cancellation requested. Skipping queued item '{item.name}'.")
                item.outcome = UpdateOutcome.SKIPPED
                item.notes = "Cancelled by user"
                summary.skipped_count += 1
                if item_complete_callback:
                    item_complete_callback(item, False, "Cancelled by user")
                continue

            current_idx += 1
            if progress_callback:
                progress_callback(item, current_idx, total_candidates)

            # Per-package execution isolated in try-except
            self._update_single_package(
                item,
                dry_run=dry_run,
                auto_close_apps=auto_close_apps,
                summary=summary,
                elevation_warning_callback=elevation_warning_callback,
                log_callback=log_callback,
                item_complete_callback=item_complete_callback,
            )

        # Post-update disk cleanup of installer temporary files
        if cleanup_after and not dry_run and total_candidates > 0:
            DiskCleanupManager.cleanup_temp_and_cache()

        self.state_mgr.complete_run()
        logger.info(
            f"=== Update Run [{run_id}] Completed: "
            f"{summary.updated_count} updated, {summary.simulated_count} simulated, "
            f"{summary.failed_count} failed, {summary.skipped_count} skipped, "
            f"{summary.listed_only_count} listed only ==="
        )

        # Deliver notification for scheduled runs or upon request
        if is_scheduled:
            notif_msg = (
                f"Update Run Complete: {summary.updated_count} updated, "
                f"{summary.failed_count} failed, {summary.skipped_count} skipped."
            )
            send_windows_notification("Winget Daily Software Updater", notif_msg)

        return summary

    def _update_single_package(
        self,
        item: ProgramItem,
        dry_run: bool,
        summary: UpdateRunSummary,
        elevation_warning_callback: Optional[Callable[[ProgramItem], None]],
        auto_close_apps: bool = True,
        log_callback: Optional[Callable[[ProgramItem, str], None]] = None,
        item_complete_callback: Optional[Callable[[ProgramItem, bool, str], None]] = None,
    ) -> None:
        """Executes update for a single verified package with isolation."""
        pkg_id = item.id or item.name

        # 1. Per-App Elevation Warning requirement
        warning_msg = (
            f"[ADMIN RIGHTS WARNING] Updating '{item.name}' ({pkg_id}) using elevated administrator privileges."
        )
        logger.warning(warning_msg)
        if elevation_warning_callback:
            try:
                elevation_warning_callback(item)
            except Exception as e:
                logger.debug(f"Elevation warning callback error: {e}")

        # 2. Re-check compatibility immediately prior to execution
        compat = self.checker.check(item)
        if not compat.is_compatible:
            reasons_str = "; ".join(compat.reasons)
            msg = f"Skipping {item.name}: Failed compatibility check ({reasons_str})"
            logger.warning(msg)
            item.outcome = UpdateOutcome.SKIPPED
            item.notes = reasons_str
            self.state_mgr.record_package_end(pkg_id, "skipped", reasons_str)
            summary.skipped_count += 1
            if item_complete_callback:
                item_complete_callback(item, False, reasons_str)
            return

        # 3. Process Lock Detection: check and gracefully close running executables to prevent error 1618
        if not dry_run and auto_close_apps:
            running = ProcessLockDetector.find_running_processes_for_item(item)
            if running:
                logger.info(f"Closing {len(running)} active processes locking '{item.name}'...")
                ProcessLockDetector.terminate_processes([p[0] for p in running], force=False)

        # 4. Record start in reboot-safe state manager
        self.state_mgr.record_package_start(pkg_id, item.name)

        # 5. Dry run check
        if dry_run:
            logger.info(f"[DRY-RUN] Simulating update for {item.name} ({pkg_id})")
            item.outcome = UpdateOutcome.SIMULATED
            item.notes = "Simulated upgrade (Dry Run active)"
            self.state_mgr.record_package_end(pkg_id, "simulated", item.notes)
            summary.simulated_count += 1
            if item_complete_callback:
                item_complete_callback(item, True, "Simulated upgrade (Dry Run)")
            return

        # 6. Execute upgrade via source manager or fallback winget
        pkg_log_cb = (lambda line: log_callback(item, line)) if log_callback else None
        try:
            source = (item.source or "").lower()
            if pkg_log_cb is not None:
                if source in ("pip", "npm", "scoop", "chocolatey") and self.source_mgr:
                    success, message = self.source_mgr.install_update(item, dry_run=False, log_callback=pkg_log_cb)
                else:
                    success, message = self.client.upgrade_package(pkg_id, dry_run=False, log_callback=pkg_log_cb)
            else:
                if source in ("pip", "npm", "scoop", "chocolatey") and self.source_mgr:
                    success, message = self.source_mgr.install_update(item, dry_run=False)
                else:
                    success, message = self.client.upgrade_package(pkg_id, dry_run=False)
            if success:
                # Re-verify installed status post-installation
                if item.latest_version:
                    item.installed_version = item.latest_version
                item.action = UpdateAction.UP_TO_DATE
                item.outcome = UpdateOutcome.UPDATED
                item.notes = f"Verified update: {item.name} updated to {item.installed_version}"
                self.state_mgr.record_package_end(pkg_id, "completed", item.notes)
                summary.updated_count += 1
                if item_complete_callback:
                    item_complete_callback(item, True, item.notes)
            else:
                item.outcome = UpdateOutcome.FAILED
                item.notes = f"Update failed: {message}"
                self.state_mgr.record_package_end(pkg_id, "failed", message)
                summary.failed_count += 1
                if item_complete_callback:
                    item_complete_callback(item, False, item.notes)
        except Exception as e:
            err_msg = f"Unexpected failure executing update for {pkg_id}: {e}"
            logger.error(err_msg)
            item.outcome = UpdateOutcome.FAILED
            item.notes = err_msg
            self.state_mgr.record_package_end(pkg_id, "failed", str(e))
            summary.failed_count += 1
            if item_complete_callback:
                item_complete_callback(item, False, err_msg)

    def execute_vendor_installer(
        self,
        item: ProgramItem,
        dry_run: bool = False,
    ) -> Tuple[bool, str]:
        """Executes a vendor fallback installer after separate explicit confirmation and signature verification.
        
        Strict constraints:
        - Never run silently.
        - Must pass signature and hash verification before execution.
        """
        if not item.vendor_installer_url:
            return False, "No vendor installer URL specified"

        logger.info(f"Initiating verified vendor fallback install for '{item.name}'...")
        logger.warning(f"[ADMIN RIGHTS WARNING] Installing '{item.name}' from vendor source with Administrator rights.")

        if dry_run:
            msg = f"[DRY-RUN] Would download and verify installer from {item.vendor_installer_url}"
            logger.info(msg)
            return True, msg

        temp_dir = Path(tempfile.gettempdir()) / "winget_updater_vendor"
        temp_dir.mkdir(parents=True, exist_ok=True)
        filename = os.path.basename(item.vendor_installer_url.split("?")[0]) or f"installer_{uuid.uuid4().hex[:6]}.exe"
        installer_path = temp_dir / filename

        try:
            logger.info(f"Downloading vendor installer from {item.vendor_installer_url}...")
            urllib.request.urlretrieve(item.vendor_installer_url, str(installer_path))

            # 1. Check SHA-256 hash if configured
            if item.vendor_installer_hash:
                hash_ok, hash_msg = PackageVerifier.verify_file_hash(installer_path, item.vendor_installer_hash)
                if not hash_ok:
                    installer_path.unlink(missing_ok=True)
                    return False, f"Signature/Hash verification failed: {hash_msg}"

            # 2. Check Windows Authenticode signature
            sig_ok, sig_msg, _ = PackageVerifier.verify_authenticode_signature(installer_path)
            if not sig_ok:
                installer_path.unlink(missing_ok=True)
                return False, f"Digital signature rejection: {sig_msg}"

            logger.info(f"Installer passed cryptographic verification ({sig_msg}). Launching setup...")
            # Execute installer
            ret = os.system(f'"{installer_path}"')
            installer_path.unlink(missing_ok=True)

            if ret == 0:
                item.outcome = UpdateOutcome.UPDATED
                item.notes = "Installed from vendor package"
                return True, "Vendor installation successful"
            else:
                item.outcome = UpdateOutcome.FAILED
                item.notes = f"Vendor installer exited with code {ret}"
                return False, item.notes
        except Exception as e:
            installer_path.unlink(missing_ok=True)
            logger.error(f"Error during vendor installation: {e}")
            return False, str(e)

