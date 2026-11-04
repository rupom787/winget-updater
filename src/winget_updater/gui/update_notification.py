"""Non-intrusive update notification banner for the main application window.
Displays a themed toast-style bar at the top of the content area when a newer
version of WingetUpdater is available on GitHub.
"""

import tkinter as tk
import webbrowser
from typing import Optional

from winget_updater.engine.auto_updater import UpdateInfo, dismiss_version
from winget_updater.gui.rounded_widgets import RoundedButton
from winget_updater.gui.theme import LIGHT_THEME, ThemeColors


class UpdateNotificationBanner(tk.Frame):
    """A slim notification banner that slides into view when an update is available.

    Designed to sit at the top of the center content column, between the
    action header and the progress frame.
    """

    def __init__(
        self,
        parent: tk.Widget,
        theme: Optional[ThemeColors] = None,
    ):
        self.theme = theme or LIGHT_THEME
        super().__init__(
            parent,
            bg=self.theme.accent_burgundy,
            padx=16,
            pady=6,
        )

        self._update_info: Optional[UpdateInfo] = None
        self._build_ui()

    def _build_ui(self) -> None:
        t = self.theme

        # Left: icon + message text
        self.lbl_icon = tk.Label(
            self,
            text="🔄",
            bg=t.accent_burgundy,
            fg="#ffffff",
            font=("Segoe UI", 10),
        )
        self.lbl_icon.pack(side=tk.LEFT, padx=(0, 6))

        self.lbl_message = tk.Label(
            self,
            text="Update Available",
            bg=t.accent_burgundy,
            fg="#ffffff",
            font=("Segoe UI", 9, "bold"),
            anchor="w",
        )
        self.lbl_message.pack(side=tk.LEFT, padx=(0, 8))

        # Right: Dismiss button
        self.btn_dismiss = RoundedButton(
            self,
            text="✕ Dismiss",
            command=self._on_dismiss,
            bg_color=t.accent_burgundy_hover,
            fg_color="#ffffff",
            hover_bg="#b91c1c",
            radius=6,
            height=24,
            font=("Segoe UI", 8),
            padding=(8, 2),
        )
        self.btn_dismiss.pack(side=tk.RIGHT, padx=(4, 0))

        # Right: Download button
        self.btn_download = RoundedButton(
            self,
            text="⬇ Download",
            command=self._on_download,
            bg_color="#ffffff",
            fg_color=t.accent_burgundy,
            hover_bg="#fff1f2",
            radius=6,
            height=24,
            font=("Segoe UI", 8, "bold"),
            padding=(10, 2),
        )
        self.btn_download.pack(side=tk.RIGHT, padx=(4, 0))

    def show_update(self, info: UpdateInfo) -> None:
        """Displays the banner with the provided update information."""
        self._update_info = info
        self.lbl_message.config(
            text=f"Update Available: v{info.latest_version}"
        )
        self.pack(fill=tk.X, pady=(0, 0))

    def _on_download(self) -> None:
        """Opens the GitHub release page in the default browser."""
        if self._update_info and self._update_info.download_url:
            webbrowser.open(self._update_info.download_url)

    def _on_dismiss(self) -> None:
        """Hides the banner and records the version as dismissed."""
        if self._update_info and self._update_info.latest_version:
            dismiss_version(self._update_info.latest_version)
        self.pack_forget()

    def apply_theme(self, theme: ThemeColors) -> None:
        """Reapplies colors when the global theme changes."""
        self.theme = theme
        t = theme
        self.config(bg=t.accent_burgundy)
        self.lbl_icon.config(bg=t.accent_burgundy, fg="#ffffff")
        self.lbl_message.config(bg=t.accent_burgundy, fg="#ffffff")
        self.btn_download.config(bg="#ffffff", fg=t.accent_burgundy)
        self.btn_dismiss.config(bg=t.accent_burgundy_hover, fg="#ffffff")
