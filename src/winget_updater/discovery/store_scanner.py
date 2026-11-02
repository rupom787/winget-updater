"""Microsoft Store and MSIX package discovery via PowerShell Get-AppxPackage."""

import json
import subprocess
from typing import List
from winget_updater.models import PackageType, ProgramItem
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()


class StoreScanner:
    """Discovers installed Microsoft Store and MSIX packages."""

    def __init__(self, timeout_sec: int = 25):
        self.timeout_sec = timeout_sec

    def scan(self) -> List[ProgramItem]:
        """Runs PowerShell Get-AppxPackage and parses JSON output."""
        items: List[ProgramItem] = []
        ps_cmd = (
            "Get-AppxPackage | Where-Object { -not $_.IsFramework } | "
            "Select-Object Name, PackageFullName, Version, Publisher, InstallLocation | "
            "ConvertTo-Json -Compress"
        )

        try:
            res = silent_run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_sec,
            )

            if res.returncode != 0:
                logger.warning(f"Get-AppxPackage returned code {res.returncode}: {res.stderr.strip()}")
                return items

            raw_out = res.stdout.strip()
            if not raw_out:
                return items

            data = json.loads(raw_out)
            if isinstance(data, dict):
                data = [data]

            for pkg in data:
                name = pkg.get("Name")
                if not name:
                    continue

                # Filter out pure internal/staged Windows packages that aren't user apps
                if name.startswith("Microsoft.Windows.") and "Cortana" not in name:
                    # Windows internal system stubs
                    continue

                version = pkg.get("Version") or "Unknown"
                publisher = pkg.get("Publisher")
                install_loc = pkg.get("InstallLocation")
                full_name = pkg.get("PackageFullName")

                items.append(
                    ProgramItem(
                        name=name,
                        installed_version=version,
                        id=f"MSIX\\{full_name}" if full_name else name,
                        publisher=publisher,
                        install_location=install_loc,
                        package_type=PackageType.STORE_MSIX,
                        notes="Discovered via Get-AppxPackage",
                    )
                )

            logger.info(f"Store/MSIX scanner found {len(items)} packages.")
        except subprocess.TimeoutExpired:
            logger.error(f"Get-AppxPackage timed out after {self.timeout_sec} seconds.")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Get-AppxPackage JSON output: {e}")
        except Exception as e:
            logger.error(f"Unexpected error scanning Store packages: {e}")

        return items

