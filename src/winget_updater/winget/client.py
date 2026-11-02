"""Winget client providing batched package queries, metadata lookup, and execution."""

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()


@dataclass
class WingetPackageEntry:
    """Represents a row parsed from winget list or winget upgrade."""
    name: str
    id: str
    version: str
    available_version: Optional[str] = None
    source: Optional[str] = None
    publisher: Optional[str] = None


@dataclass
class WingetPackageDetails:
    """Detailed metadata retrieved from winget show."""
    id: str
    version: str
    publisher: Optional[str] = None
    architecture: Optional[str] = None
    installer_type: Optional[str] = None
    installer_url: Optional[str] = None
    installer_sha256: Optional[str] = None
    min_os_version: Optional[str] = None


class WingetClient:
    """Interface to the Windows Package Manager (winget) CLI."""

    def __init__(self, winget_path: Optional[str] = None, timeout_sec: int = 60):
        self.winget_path = winget_path or shutil.which("winget") or "winget"
        self.timeout_sec = timeout_sec

    def is_available(self) -> bool:
        """Verifies if winget executable is present and responsive."""
        try:
            res = silent_run(
                [self.winget_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return res.returncode == 0
        except Exception:
            return False

    def get_version(self) -> str:
        """Returns the installed winget version string."""
        try:
            res = silent_run(
                [self.winget_path, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return res.stdout.strip()
        except Exception as e:
            return f"Unavailable ({e})"

    def get_available_upgrades(self) -> Dict[str, WingetPackageEntry]:
        """Executes winget upgrade in batch mode and returns dictionary mapped by Package ID."""
        cmd = [
            self.winget_path,
            "upgrade",
            "--include-unknown",
            "--accept-source-agreements",
        ]
        logger.info("Executing batched winget upgrade query for all available updates...")
        entries: Dict[str, WingetPackageEntry] = {}

        try:
            res = silent_run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_sec,
            )
            # winget returns 0 on success or 0x8a15002b (-1978236885) if no upgrades available
            entries = self._parse_table_output(res.stdout, is_upgrade_table=True)
            logger.info(f"Batched winget upgrade check found {len(entries)} pending upgrades.")
        except subprocess.TimeoutExpired:
            logger.error(f"winget upgrade batch query timed out after {self.timeout_sec}s")
        except Exception as e:
            logger.error(f"Error querying winget upgrade: {e}")

        return entries

    def get_installed_packages(self) -> Dict[str, WingetPackageEntry]:
        """Executes winget list in batch mode and returns all recognized packages."""
        cmd = [
            self.winget_path,
            "list",
            "--accept-source-agreements",
        ]
        logger.info("Executing batched winget list query for installed package registry...")
        entries: Dict[str, WingetPackageEntry] = {}

        try:
            res = silent_run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_sec,
            )
            entries = self._parse_table_output(res.stdout, is_upgrade_table=False)
            logger.info(f"Batched winget list returned {len(entries)} registered packages.")
        except subprocess.TimeoutExpired:
            logger.error(f"winget list batch query timed out after {self.timeout_sec}s")
        except Exception as e:
            logger.error(f"Error querying winget list: {e}")

        return entries

    def _parse_table_output(self, output: str, is_upgrade_table: bool = False) -> Dict[str, WingetPackageEntry]:
        """Parses fixed-width column table output from winget list or winget upgrade."""
        results: Dict[str, WingetPackageEntry] = {}
        lines = output.splitlines()

        header_idx = -1
        col_name = -1
        col_id = -1
        col_ver = -1
        col_avail = -1
        col_source = -1

        for i, line in enumerate(lines):
            line_str = line.strip()
            if "Name" in line and "Id" in line and "Version" in line:
                header_idx = i
                col_name = line.find("Name")
                col_id = line.find("Id")
                col_ver = line.find("Version")
                col_avail = line.find("Available") if "Available" in line else -1
                col_source = line.find("Source") if "Source" in line else -1
                break

        if header_idx == -1 or col_name == -1 or col_id == -1 or col_ver == -1:
            return results

        # Skip separator line (dashes)
        start_row = header_idx + 1
        if start_row < len(lines) and lines[start_row].strip().startswith("-"):
            start_row += 1

        for row in lines[start_row:]:
            if not row.strip():
                continue
            # End of table summary line (e.g. "5 upgrades available.")
            if "upgrades available" in row.lower() or "upgrade available" in row.lower():
                break

            try:
                name_val = row[col_name:col_id].strip() if col_id > col_name else ""
                if col_avail != -1:
                    id_val = row[col_id:col_ver].strip()
                    ver_val = row[col_ver:col_avail].strip()
                    if col_source != -1:
                        avail_val = row[col_avail:col_source].strip()
                        source_val = row[col_source:].strip()
                    else:
                        avail_val = row[col_avail:].strip()
                        source_val = ""
                elif col_source != -1:
                    id_val = row[col_id:col_ver].strip()
                    ver_val = row[col_ver:col_source].strip()
                    avail_val = None
                    source_val = row[col_source:].strip()
                else:
                    id_val = row[col_id:col_ver].strip()
                    ver_val = row[col_ver:].strip()
                    avail_val = None
                    source_val = ""

                if id_val and name_val:
                    entry = WingetPackageEntry(
                        name=name_val,
                        id=id_val,
                        version=ver_val,
                        available_version=avail_val if avail_val else None,
                        source=source_val if source_val else None,
                    )
                    # Key by lowercased ID
                    results[id_val.lower()] = entry
            except Exception:
                continue

        return results

    def show_package(self, package_id: str) -> Optional[WingetPackageDetails]:
        """Retrieves detailed manifest metadata for a package using winget show."""
        cmd = [
            self.winget_path,
            "show",
            "--id", package_id,
            "--exact",
            "--accept-source-agreements",
        ]
        try:
            res = silent_run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=25,
            )
            if res.returncode != 0:
                logger.debug(f"winget show for {package_id} returned code {res.returncode}")
                return None

            return self._parse_show_output(package_id, res.stdout)
        except Exception as e:
            logger.debug(f"Failed to fetch winget details for {package_id}: {e}")
            return None

    def _parse_show_output(self, package_id: str, output: str) -> WingetPackageDetails:
        """Parses YAML-like output from winget show."""
        version = ""
        publisher = None
        arch = None
        inst_type = None
        inst_url = None
        inst_sha = None
        min_os = None

        for line in output.splitlines():
            line_str = line.strip()
            if line_str.startswith("Version:"):
                version = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("Publisher:"):
                publisher = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("Installer SHA256:"):
                inst_sha = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("Installer Url:"):
                inst_url = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("Installer Type:"):
                inst_type = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("Architecture:"):
                arch = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("Minimum OS Version:"):
                min_os = line_str.split(":", 1)[1].strip()

        return WingetPackageDetails(
            id=package_id,
            version=version,
            publisher=publisher,
            architecture=arch,
            installer_type=inst_type,
            installer_url=inst_url,
            installer_sha256=inst_sha,
            min_os_version=min_os,
        )

    def upgrade_package(self, package_id: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Upgrades a single verified package via winget upgrade --id <id>."""
        if dry_run:
            logger.info(f"[DRY-RUN] Would execute: winget upgrade --id '{package_id}' --exact")
            return True, "Simulated successful upgrade (dry run)"

        cmd = [
            self.winget_path,
            "upgrade",
            "--id", package_id,
            "--exact",
            "--accept-source-agreements",
            "--accept-package-agreements",
            "--disable-interactivity",
        ]
        logger.info(f"Executing winget upgrade for package: {package_id}")

        try:
            res = silent_run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,  # Allow up to 10 minutes for large downloads/installs
            )
            if res.returncode == 0:
                logger.info(f"Successfully upgraded {package_id}")
                return True, "Update completed successfully"
            else:
                err_msg = res.stderr.strip() or res.stdout.strip() or f"Exit code {res.returncode}"
                logger.error(f"Failed to upgrade {package_id}: {err_msg}")
                return False, err_msg
        except subprocess.TimeoutExpired:
            logger.error(f"winget upgrade for {package_id} timed out")
            return False, "Upgrade timed out after 600 seconds"
        except Exception as e:
            logger.error(f"Exception during winget upgrade of {package_id}: {e}")
            return False, str(e)

    def uninstall_package(self, package_id: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Uninstalls a package cleanly via winget uninstall --id <id>."""
        if dry_run:
            logger.info(f"[DRY-RUN] Would execute: winget uninstall --id '{package_id}'")
            return True, "Simulated successful uninstallation (dry run)"

        cmd = [
            self.winget_path,
            "uninstall",
            "--id", package_id,
            "--exact",
            "--accept-source-agreements",
            "--disable-interactivity",
        ]
        logger.info(f"Executing winget uninstall for package: {package_id}")

        try:
            res = silent_run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
            )
            if res.returncode == 0:
                logger.info(f"Successfully uninstalled {package_id}")
                return True, "Uninstallation completed successfully"
            else:
                err_msg = res.stderr.strip() or res.stdout.strip() or f"Exit code {res.returncode}"
                logger.error(f"Failed to uninstall {package_id}: {err_msg}")
                return False, err_msg
        except Exception as e:
            logger.error(f"Exception during uninstallation of {package_id}: {e}")
            return False, str(e)

    def install_package(self, package_id: str, dry_run: bool = False) -> Tuple[bool, str]:
        """Installs a new package from the winget repository."""
        if dry_run:
            logger.info(f"[DRY-RUN] Would execute: winget install --id '{package_id}'")
            return True, "Simulated successful installation (dry run)"

        cmd = [
            self.winget_path,
            "install",
            "--id", package_id,
            "--exact",
            "--accept-package-agreements",
            "--accept-source-agreements",
            "--disable-interactivity",
        ]
        logger.info(f"Executing winget install for package: {package_id}")

        try:
            res = silent_run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
            )
            if res.returncode == 0:
                logger.info(f"Successfully installed {package_id}")
                return True, "Installation completed successfully"
            else:
                err_msg = res.stderr.strip() or res.stdout.strip() or f"Exit code {res.returncode}"
                logger.error(f"Failed to install {package_id}: {err_msg}")
                return False, err_msg
        except Exception as e:
            logger.error(f"Exception during installation of {package_id}: {e}")
            return False, str(e)

    def search_packages(self, query: str, count: int = 30) -> List[WingetPackageEntry]:
        """Searches the winget repository catalog for available packages."""
        if not query or len(query.strip()) < 2:
            return []

        cmd = [
            self.winget_path,
            "search",
            query.strip(),
            "--count", str(count),
            "--accept-source-agreements",
        ]
        logger.info(f"Searching winget catalog for '{query}'...")

        try:
            res = silent_run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            parsed_dict = self._parse_table_output(res.stdout, is_upgrade_table=False)
            return list(parsed_dict.values())
        except Exception as e:
            logger.error(f"Error searching winget catalog: {e}")
            return []

    def update_sources(self) -> Tuple[bool, str]:
        """Synchronizes all configured package sources with their upstream repositories."""
        cmd = [self.winget_path, "source", "update"]
        logger.info("Synchronizing and updating package manager sources...")

        try:
            res = silent_run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            if res.returncode == 0:
                logger.info("Successfully updated package sources.")
                return True, "Package sources synchronized successfully"
            else:
                msg = res.stderr.strip() or res.stdout.strip() or f"Exit code {res.returncode}"
                logger.warning(f"Failed to update sources: {msg}")
                return False, msg
        except Exception as e:
            logger.error(f"Error updating sources: {e}")
            return False, str(e)

    def get_configured_sources(self) -> List[Dict[str, str]]:
        """Returns the list of configured winget sources (e.g. winget, msstore)."""
        cmd = [self.winget_path, "source", "list"]
        sources = []
        try:
            res = silent_run(cmd, capture_output=True, text=True, timeout=15)
            if res.returncode == 0:
                lines = res.stdout.splitlines()
                # Find separator line
                start_parsing = False
                for line in lines:
                    if "---" in line:
                        start_parsing = True
                        continue
                    if start_parsing and line.strip():
                        parts = line.split(None, 1)
                        if len(parts) >= 2:
                            sources.append({"name": parts[0].strip(), "argument": parts[1].strip()})
                        elif len(parts) == 1:
                            sources.append({"name": parts[0].strip(), "argument": ""})
        except Exception as e:
            logger.debug(f"Error listing sources: {e}")
        return sources

    def export_software_manifest(
        self,
        output_path: str,
        include_versions: bool = False,
    ) -> Tuple[bool, str]:
        """Exports installed software packages to a Winget-compatible JSON manifest for machine backup/provisioning."""
        cmd = [
            self.winget_path,
            "export",
            "-o", output_path,
            "--accept-source-agreements",
        ]
        if include_versions:
            cmd.append("--include-versions")

        logger.info(f"Exporting software backup manifest to: {output_path}")
        try:
            res = silent_run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
            if res.returncode == 0 and os.path.exists(output_path):
                return True, f"Software stack successfully exported to {os.path.basename(output_path)}"
            msg = res.stderr.strip() or res.stdout.strip() or f"Exit code {res.returncode}"
            return False, f"Export failed: {msg}"
        except Exception as e:
            logger.error(f"Error exporting software manifest: {e}")
            return False, str(e)

    def import_software_manifest(
        self,
        input_path: str,
        ignore_unavailable: bool = True,
    ) -> Tuple[bool, str]:
        """Imports and installs software packages from a backup manifest (1-click machine restoration)."""
        if not os.path.exists(input_path):
            return False, f"Manifest file does not exist: {input_path}"

        cmd = [
            self.winget_path,
            "import",
            "-i", input_path,
            "--accept-package-agreements",
            "--accept-source-agreements",
        ]
        if ignore_unavailable:
            cmd.append("--ignore-unavailable")

        logger.info(f"Importing and provisioning software stack from: {input_path}")
        try:
            res = silent_run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
            )
            if res.returncode == 0:
                return True, "Software stack successfully restored from backup manifest."
            msg = res.stderr.strip() or res.stdout.strip() or f"Exit code {res.returncode}"
            return False, f"Import error: {msg}"
        except Exception as e:
            logger.error(f"Error importing software manifest: {e}")
            return False, str(e)

