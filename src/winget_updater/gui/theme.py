"""Theme definitions and color palettes for Software & Package Updater.
Provides Burgundy Light (Clean White & Wine Red) and High-Contrast Dark.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ThemeColors:
    name: str  # "light" or "dark"

    # Surfaces & Backgrounds
    bg_root: str
    bg_canvas: str
    bg_panel: str
    bg_card: str
    bg_card_hover: str
    bg_card_selected: str
    bg_input: str
    bg_table: str
    bg_table_alt: str
    bg_header: str
    bg_button: str
    bg_button_hover: str
    bg_button_active: str
    bg_sidebar: str

    # Borders & Grids
    border: str
    border_subtle: str
    border_accent: str
    grid_line: str

    # Typography & Foregrounds
    fg_primary: str
    fg_secondary: str
    fg_muted: str
    fg_accent: str
    fg_laser: str

    # Semantic Status Accents
    accent_burgundy: str
    accent_burgundy_hover: str
    accent_cyan: str
    accent_emerald: str
    accent_amber: str
    accent_crimson: str
    accent_purple: str

    # Table Tag Colors
    tag_available_bg: str
    tag_available_fg: str
    tag_uptodate_bg: str
    tag_uptodate_fg: str
    tag_uptodate_alt_bg: str
    tag_uptodate_alt_fg: str
    tag_downgrade_bg: str
    tag_downgrade_fg: str
    tag_fallback_bg: str
    tag_fallback_fg: str
    tag_incompat_bg: str
    tag_incompat_fg: str
    tag_listed_bg: str
    tag_listed_fg: str
    tag_unverified_bg: str
    tag_unverified_fg: str
    tag_ignored_bg: str
    tag_ignored_fg: str


# Clean White background with Deep Red-Wine / Burgundy accents
LIGHT_THEME = ThemeColors(
    name="light",
    bg_root="#faf8f8",
    bg_canvas="#ffffff",
    bg_panel="#ffffff",
    bg_card="#ffffff",
    bg_card_hover="#fff1f2",
    bg_card_selected="#ffe4e6",
    bg_input="#ffffff",
    bg_table="#ffffff",
    bg_table_alt="#fdfafa",
    bg_header="#ffffff",
    bg_button="#ffffff",
    bg_button_hover="#fff1f2",
    bg_button_active="#fecdd3",
    bg_sidebar="#faf5f5",
    border="#f3d5d9",
    border_subtle="#fce7e9",
    border_accent="#800020",
    grid_line="#fceef0",
    fg_primary="#111827",
    fg_secondary="#374151",
    fg_muted="#6b7280",
    fg_accent="#800020",
    fg_laser="#800020",
    accent_burgundy="#800020",
    accent_burgundy_hover="#991b1b",
    accent_cyan="#800020",
    accent_emerald="#166534",
    accent_amber="#b45309",
    accent_crimson="#991b1b",
    accent_purple="#6b21a8",
    tag_available_bg="#fef2f2",
    tag_available_fg="#991b1b",
    tag_uptodate_bg="#f0fdf4",
    tag_uptodate_fg="#166534",
    tag_uptodate_alt_bg="#f0fdf4",
    tag_uptodate_alt_fg="#166534",
    tag_downgrade_bg="#fffbeb",
    tag_downgrade_fg="#92400e",
    tag_fallback_bg="#eff6ff",
    tag_fallback_fg="#1e40af",
    tag_incompat_bg="#fef2f2",
    tag_incompat_fg="#991b1b",
    tag_listed_bg="#f3f4f6",
    tag_listed_fg="#4b5563",
    tag_unverified_bg="#fffbeb",
    tag_unverified_fg="#92400e",
    tag_ignored_bg="#f5f3ff",
    tag_ignored_fg="#5b21b6",
)

DARK_THEME = ThemeColors(
    name="dark",
    bg_root="#0c1222",
    bg_canvas="#0f172a",
    bg_panel="#111827",
    bg_card="#162036",
    bg_card_hover="#1e293b",
    bg_card_selected="#241424",
    bg_input="#1e293b",
    bg_table="#111827",
    bg_table_alt="#141d2e",
    bg_header="#0f172a",
    bg_button="#1e293b",
    bg_button_hover="#334155",
    bg_button_active="#475569",
    bg_sidebar="#111827",
    border="#1e293b",
    border_subtle="#1a2336",
    border_accent="#be123c",
    grid_line="#172033",
    fg_primary="#f8fafc",
    fg_secondary="#94a3b8",
    fg_muted="#64748b",
    fg_accent="#f43f5e",
    fg_laser="#f43f5e",
    accent_burgundy="#881337",
    accent_burgundy_hover="#9f1239",
    accent_cyan="#38bdf8",
    accent_emerald="#10b981",
    accent_amber="#fbbf24",
    accent_crimson="#be123c",
    accent_purple="#a855f7",
    tag_available_bg="#4c0519",
    tag_available_fg="#fda4af",
    tag_uptodate_bg="#065f46",
    tag_uptodate_fg="#34d399",
    tag_uptodate_alt_bg="#065f46",
    tag_uptodate_alt_fg="#34d399",
    tag_downgrade_bg="#451a03",
    tag_downgrade_fg="#fbbf24",
    tag_fallback_bg="#1e1b4b",
    tag_fallback_fg="#818cf8",
    tag_incompat_bg="#450a0a",
    tag_incompat_fg="#f87171",
    tag_listed_bg="#1e293b",
    tag_listed_fg="#94a3b8",
    tag_unverified_bg="#451a03",
    tag_unverified_fg="#fbbf24",
    tag_ignored_bg="#2e1065",
    tag_ignored_fg="#c084fc",
)

THEMES: Dict[str, ThemeColors] = {
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
}


def get_theme(name: str) -> ThemeColors:
    """Returns the ThemeColors corresponding to the given theme name (defaults to light)."""
    if not name:
        return LIGHT_THEME
    return THEMES.get(name.lower(), LIGHT_THEME)


@dataclass
class Typography:
    """Scalable typography bundle for high-DPI displays and user font scale preferences."""
    preset: str
    font_family: str
    code_family: str
    title: tuple
    subtitle: tuple
    section: tuple
    body: tuple
    body_bold: tuple
    table: tuple
    table_bold: tuple
    button: tuple
    caption: tuple
    caption_bold: tuple
    mono: tuple
    mono_bold: tuple
    row_height: int


TYPOGRAPHY_PRESETS: Dict[str, Typography] = {
    "compact": Typography(
        preset="compact",
        font_family="Segoe UI",
        code_family="Cascadia Code",
        title=("Segoe UI", 12, "bold"),
        subtitle=("Segoe UI", 9),
        section=("Segoe UI", 8, "bold"),
        body=("Segoe UI", 9),
        body_bold=("Segoe UI", 9, "bold"),
        table=("Segoe UI", 9),
        table_bold=("Segoe UI", 9, "bold"),
        button=("Segoe UI", 8, "bold"),
        caption=("Segoe UI", 8),
        caption_bold=("Segoe UI", 8, "bold"),
        mono=("Cascadia Code", 8),
        mono_bold=("Cascadia Code", 8, "bold"),
        row_height=30,
    ),
    "normal": Typography(
        preset="normal",
        font_family="Segoe UI",
        code_family="Cascadia Code",
        title=("Segoe UI", 13, "bold"),
        subtitle=("Segoe UI", 10),
        section=("Segoe UI", 9, "bold"),
        body=("Segoe UI", 10),
        body_bold=("Segoe UI", 10, "bold"),
        table=("Segoe UI", 10),
        table_bold=("Segoe UI", 10, "bold"),
        button=("Segoe UI", 9, "bold"),
        caption=("Segoe UI", 9),
        caption_bold=("Segoe UI", 9, "bold"),
        mono=("Cascadia Code", 9),
        mono_bold=("Cascadia Code", 9, "bold"),
        row_height=36,
    ),
    "large": Typography(
        preset="large",
        font_family="Segoe UI",
        code_family="Cascadia Code",
        title=("Segoe UI", 15, "bold"),
        subtitle=("Segoe UI", 11),
        section=("Segoe UI", 10, "bold"),
        body=("Segoe UI", 11),
        body_bold=("Segoe UI", 11, "bold"),
        table=("Segoe UI", 11),
        table_bold=("Segoe UI", 11, "bold"),
        button=("Segoe UI", 10, "bold"),
        caption=("Segoe UI", 10),
        caption_bold=("Segoe UI", 10, "bold"),
        mono=("Cascadia Code", 10),
        mono_bold=("Cascadia Code", 10, "bold"),
        row_height=42,
    ),
    "extra_large": Typography(
        preset="extra_large",
        font_family="Segoe UI",
        code_family="Cascadia Code",
        title=("Segoe UI", 17, "bold"),
        subtitle=("Segoe UI", 13),
        section=("Segoe UI", 12, "bold"),
        body=("Segoe UI", 12),
        body_bold=("Segoe UI", 12, "bold"),
        table=("Segoe UI", 12),
        table_bold=("Segoe UI", 12, "bold"),
        button=("Segoe UI", 11, "bold"),
        caption=("Segoe UI", 11),
        caption_bold=("Segoe UI", 11, "bold"),
        mono=("Cascadia Code", 11),
        mono_bold=("Cascadia Code", 11, "bold"),
        row_height=48,
    ),
}


def get_typography(preset: str = "normal") -> Typography:
    """Returns the Typography bundle corresponding to the given preset name."""
    if not preset:
        return TYPOGRAPHY_PRESETS["normal"]
    return TYPOGRAPHY_PRESETS.get(preset.lower(), TYPOGRAPHY_PRESETS["normal"])
