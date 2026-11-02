"""Desktop notifications for scheduled and background update runs on Windows 11."""

import os
import subprocess
from typing import Optional
from winget_updater.utils.logger import get_logger
from winget_updater.utils.process import silent_run

logger = get_logger()


def send_windows_notification(title: str, message: str) -> bool:
    """Delivers a Windows 11 native desktop toast notification via PowerShell."""
    clean_title = title.replace('"', '`"').replace("'", "''")
    clean_message = message.replace('"', '`"').replace("'", "''")

    ps_script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; "
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null; "
        f"$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
        f"$xml.LoadXml('<toast><visual><binding template=\"ToastGeneric\"><text>{clean_title}</text><text>{clean_message}</text></binding></visual></toast>'); "
        f"$toast = New-Object Windows.UI.Notifications.ToastNotification $xml; "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\cmd.exe').Show($toast);"
    )

    try:
        res = silent_run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if res.returncode == 0:
            logger.info(f"Delivered desktop notification: {title} - {message}")
            return True
        else:
            logger.debug(f"PowerShell toast notification returned {res.returncode}: {res.stderr}")
            return False
    except Exception as e:
        logger.debug(f"Could not deliver toast notification: {e}")
        return False

