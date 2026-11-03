"""Windows Update, Reboot Required detection, and OEM Companion Firmware integration.
Provides 4-stage Complete System Update orchestration natively on Windows 11.
"""

import json
import os
import re
import subprocess
import winreg
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()


@dataclass
class WindowsUpdateItem:
    """Represents a pending Windows Update or OS patch."""
    title: str
    kb_id: Optional[str] = None
    size_mb: float = 0.0
    severity: Optional[str] = None
    is_driver: bool = False
    is_mandatory: bool = True


@dataclass
class OemCompanionInfo:
    """Represents detected OEM hardware manufacturer and recommended companion app."""
    manufacturer: str
    model: str
    companion_name: str
    store_uri: str
    app_id: Optional[str] = None
    description: str = ""


class WindowsUpdateManager:
    """Manages Windows Update query/install, reboot detection, and OEM companion tools."""

    @staticmethod
    def get_oem_info() -> OemCompanionInfo:
        """Detects host PC manufacturer, product model, and matches official companion app."""
        mfg = "Unknown"
        model = "Standard PC"

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\BIOS") as key:
                mfg_val, _ = winreg.QueryValueEx(key, "SystemManufacturer")
                model_val, _ = winreg.QueryValueEx(key, "SystemProductName")
                mfg = str(mfg_val).strip()
                model = str(model_val).strip()
        except OSError:
            pass

        norm_mfg = mfg.upper()

        if "ASUS" in norm_mfg:
            return OemCompanionInfo(
                manufacturer=mfg,
                model=model,
                companion_name="MyASUS / Armoury Crate",
                store_uri="ms-windows-store://pdp/?productid=9NBLGGH51628",
                app_id="ASUS.MyASUS",
                description="Official ASUS utility for BIOS, firmware, and motherboard driver updates.",
            )
        elif "LENOVO" in norm_mfg:
            return OemCompanionInfo(
                manufacturer=mfg,
                model=model,
                companion_name="Lenovo Vantage",
                store_uri="ms-windows-store://pdp/?productid=9WZDNCRFJ4MV",
                app_id="Lenovo.Vantage",
                description="Official Lenovo utility for BIOS, ThinkPad firmware, and system maintenance.",
            )
        elif "DELL" in norm_mfg or "ALIENWARE" in norm_mfg:
            return OemCompanionInfo(
                manufacturer=mfg,
                model=model,
                companion_name="Dell SupportAssist",
                store_uri="ms-windows-store://pdp/?productid=9NM7CT8SSB5Q",
                app_id="Dell.SupportAssist",
                description="Official Dell utility for BIOS flashing, hardware diagnostics, and chipset drivers.",
            )
        elif "HP" in norm_mfg or "HEWLETT" in norm_mfg:
            return OemCompanionInfo(
                manufacturer=mfg,
                model=model,
                companion_name="HP Support Assistant",
                store_uri="ms-windows-store://pdp/?productid=9P94T4591F4Q",
                app_id="HP.SupportAssistant",
                description="Official HP utility for BIOS updates, docking station firmware, and audio drivers.",
            )
        elif "MSI" in norm_mfg or "MICRO-STAR" in norm_mfg:
            return OemCompanionInfo(
                manufacturer=mfg,
                model=model,
                companion_name="MSI Center",
                store_uri="ms-windows-store://pdp/?productid=9NVM8F83PK04",
                app_id="MSI.Center",
                description="Official MSI utility for Dragon Center, BIOS updates, and cooling controls.",
            )
        elif "ACER" in norm_mfg:
            return OemCompanionInfo(
                manufacturer=mfg,
                model=model,
                companion_name="Acer Care Center",
                store_uri="ms-settings:windowsupdate-optionalupdates",
                app_id="Acer.CareCenter",
                description="Acer utility for system diagnostics and firmware.",
            )
        elif "SURFACE" in norm_mfg or "MICROSOFT" in norm_mfg:
            return OemCompanionInfo(
                manufacturer=mfg,
                model=model,
                companion_name="Surface App",
                store_uri="ms-windows-store://pdp/?productid=9WZDNCRFJB89",
                app_id="Microsoft.Surface",
                description="Official Microsoft Surface companion for firmware, pen, and audio drivers.",
            )

        return OemCompanionInfo(
            manufacturer=mfg,
            model=model,
            companion_name="Windows Update Optional Drivers",
            store_uri="ms-settings:windowsupdate-optionalupdates",
            description="Access optional hardware firmware, BIOS, and vendor drivers via Windows Settings.",
        )

    @staticmethod
    def is_reboot_pending() -> Tuple[bool, str]:
        """Checks if a system reboot is required to finish installing OS or driver updates.
        
        Evaluates 3 authoritative Windows registry indicators:
        1. WindowsUpdate Auto Update RebootRequired
        2. Component Based Servicing (CBS) RebootPending
        3. Session Manager PendingFileRenameOperations
        """
        # 1. Windows Update Reboot Required
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired",
            ):
                return True, "Windows Update requires restart to finalize OS patches"
        except OSError:
            pass

        # 2. Component Based Servicing (CBS)
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
            ):
                return True, "Windows Component Store (CBS) requires restart"
        except OSError:
            pass

        # 3. Pending file rename operations
        try:
            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager",
            ) as key:
                val, _ = winreg.QueryValueEx(key, "PendingFileRenameOperations")
                if val:
                    return True, "Pending file renames/driver replacements require restart"
        except OSError:
            pass

        return False, "No restart required"

    @staticmethod
    def get_pending_windows_updates(timeout_sec: int = 15) -> List[WindowsUpdateItem]:
        """Queries pending Windows Updates via native Windows Update Agent COM API."""
        ps_code = (
            "$ErrorActionPreference = 'SilentlyContinue'; "
            "$Session = New-Object -ComObject Microsoft.Update.Session; "
            "$Searcher = $Session.CreateUpdateSearcher(); "
            "$Searcher.ServerSelection = 1; "
            "$SearchCriteria = \"IsInstalled=0 and IsHidden=0\"; "
            "$Result = $Searcher.Search($SearchCriteria); "
            "$list = @(); "
            "foreach ($u in $Result.Updates) { "
            "  $list += @{ "
            "    title = $u.Title; "
            "    kb = ($u.KBArticleIDs -join ', '); "
            "    size = [math]::Round($u.MaxDownloadSize / (1024 * 1024), 1); "
            "    severity = $u.MsrcSeverity; "
            "    is_driver = ($u.Type -eq 2); "
            "  }; "
            "}; "
            "$list | ConvertTo-Json -Compress"
        )
        try:
            stdout, stderr, code = silent_run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_code],
                timeout=timeout_sec,
            )
            if code != 0 or not stdout.strip():
                return []

            data = json.loads(stdout)
            if isinstance(data, dict):
                data = [data]

            results = []
            for item in data:
                title = item.get("title", "Windows Update")
                kb = item.get("kb") or None
                size = float(item.get("size") or 0.0)
                sev = item.get("severity") or None
                is_drv = bool(item.get("is_driver", False))
                results.append(WindowsUpdateItem(
                    title=title,
                    kb_id=kb,
                    size_mb=size,
                    severity=sev,
                    is_driver=is_drv,
                ))
            return results
        except Exception as e:
            logger.debug(f"Failed to query pending Windows Updates: {e}")
            return []

    @staticmethod
    def trigger_windows_update_scan_and_install() -> Tuple[bool, str]:
        """Triggers native Windows Update scan & download via UsoClient or Windows Settings."""
        try:
            # UsoClient StartScan triggers native background check
            uso_path = os.path.expandvars(r"%SystemRoot%\System32\UsoClient.exe")
            if os.path.isfile(uso_path):
                silent_run([uso_path, "StartInteractiveScan"])
                return True, "Triggered native Windows Update scan via UsoClient."
        except Exception:
            pass

        # Fallback: Launch Windows Update settings page
        try:
            os.system("start ms-settings:windowsupdate-action")
            return True, "Opened Windows Update settings."
        except Exception as e:
            return False, f"Error launching Windows Update: {e}"

    @staticmethod
    def open_oem_companion(store_uri: Optional[str] = None) -> bool:
        """Launches the detected OEM companion app (e.g. MyASUS, Lenovo Vantage, Dell SupportAssist)."""
        uri = store_uri or WindowsUpdateManager.get_oem_info().store_uri
        try:
            os.system(f"start {uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to open OEM companion '{uri}': {e}")
            return False
