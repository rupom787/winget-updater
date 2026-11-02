"""Hardware device driver discovery using Windows PnP Utility (pnputil)."""

import subprocess
from typing import Dict, List
from winget_updater.models import PackageType, ProgramItem
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()


class DriverScanner:
    """Discovers installed third-party/OEM device drivers via pnputil."""

    def __init__(self, timeout_sec: int = 20):
        self.timeout_sec = timeout_sec

    def scan(self) -> List[ProgramItem]:
        """Runs pnputil /enum-drivers and extracts driver metadata."""
        items: List[ProgramItem] = []
        try:
            res = silent_run(
                ["pnputil", "/enum-drivers"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout_sec,
            )

            if res.returncode != 0:
                logger.warning(f"pnputil returned code {res.returncode}")
                return items

            items = self.parse_pnputil_output(res.stdout)
            logger.info(f"Driver scanner found {len(items)} OEM device drivers.")
        except subprocess.TimeoutExpired:
            logger.error("pnputil /enum-drivers timed out.")
        except Exception as e:
            logger.error(f"Error enumerating device drivers: {e}")

        return items

    def parse_pnputil_output(self, output: str) -> List[ProgramItem]:
        """Parses stdout blocks from pnputil /enum-drivers."""
        items: List[ProgramItem] = []
        current_entry: Dict[str, str] = {}

        for line in output.splitlines():
            line_str = line.strip()
            if not line_str:
                if current_entry and "Published Name" in current_entry:
                    item = self._create_item_from_entry(current_entry)
                    if item:
                        items.append(item)
                    current_entry = {}
                continue

            if ":" in line_str:
                key, val = line_str.split(":", 1)
                current_entry[key.strip()] = val.strip()

        # Final block if trailing output without empty line
        if current_entry and "Published Name" in current_entry:
            item = self._create_item_from_entry(current_entry)
            if item:
                items.append(item)

        return items

    def _create_item_from_entry(self, entry: Dict[str, str]) -> ProgramItem:
        pub_name = entry.get("Published Name", "oem.inf")
        orig_name = entry.get("Original Name", pub_name)
        provider = entry.get("Provider Name", "Unknown Provider")
        class_name = entry.get("Class Name", "Device")
        raw_version = entry.get("Driver Version", "Unknown")
        signer = entry.get("Signer Name", "Unknown")

        # Driver version often contains date + version e.g. "12/23/2025 6.0.2.118"
        version_part = raw_version
        parts = raw_version.split()
        if len(parts) >= 2:
            version_part = parts[1]

        display_name = f"{provider} {orig_name} ({class_name})"

        return ProgramItem(
            name=display_name,
            installed_version=version_part,
            id=f"Driver\\{pub_name}",
            publisher=provider,
            package_type=PackageType.DRIVER,
            notes=f"Driver {pub_name} (Signer: {signer}; listed only)",
        )

