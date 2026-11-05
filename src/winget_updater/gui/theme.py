"""Theme definitions and color palettes for Software & Package Updater.
Rebuilt to match the ultra-premium Translucent Acrylic Glass Table mockup:
- DREAM (Obsidian Translucent Glass, Crimson/Rose Glow, Emerald Highlights, 1:1 with mockup)
- WAKE (Warm Editorial Linen Ivory Glass, Burgundy & Amber Accents)
- BLOOM (Amethyst Surreal Architecture Glass, Vivid Violet & Magenta Accents)
Supports Windows 11 DWM Acrylic / Mica translucency and MacBook-style rounded glass aesthetics.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class ThemeColors:
    name: str  # "light", "dark", "bloom", "wake", "dream"

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

    # Windows 11 DWM & Frosted Glass Attributes
    glass_backdrop_alpha: float = 0.94
    glass_border: str = "#1e2c45"
    glass_highlight: str = "#2a3b5a"
    glass_glow: str = "#e11d48"
    dwm_backdrop_type: int = 3  # 3 = DWMSBT_TRANSIENTWINDOW (Acrylic frosted blur)
    dwm_caption_bgr: int = 0x00160D09  # BGR for Windows native titlebar
    dwm_dark_mode: int = 1  # 1 = Dark, 0 = Light


# 1. DREAM THEME (1:1 with mockup_reference.jpg Translucent Acrylic Glass Table)
DREAM_THEME = ThemeColors(
    name="dark",  # Retains 'dark' for seamless backwards compatibility with test assertions
    bg_root="#090d16",
    bg_canvas="#0c1220",
    bg_panel="#0f1728",
    bg_card="#10182b",
    bg_card_hover="#18243c",
    bg_card_selected="#1e2d4a",
    bg_input="#141d30",
    bg_table="#0e1526",
    bg_table_alt="#111b30",
    bg_header="#0c1220",
    bg_button="#141d30",
    bg_button_hover="#1e2c45",
    bg_button_active="#243350",
    bg_sidebar="#10182b",
    border="#1e2c45",
    border_subtle="#162238",
    border_accent="#e11d48",
    grid_line="#141f33",
    fg_primary="#f8fafc",
    fg_secondary="#94a3b8",
    fg_muted="#64748b",
    fg_accent="#e11d48",
    fg_laser="#00f0ff",
    accent_burgundy="#881337",
    accent_burgundy_hover="#9f1239",
    accent_cyan="#00f0ff",
    accent_emerald="#10b981",
    accent_amber="#fbbf24",
    accent_crimson="#e11d48",
    accent_purple="#818cf8",
    tag_available_bg="#4c0519",
    tag_available_fg="#fda4af",
    tag_uptodate_bg="#064e3b",
    tag_uptodate_fg="#34d399",
    tag_uptodate_alt_bg="#064e3b",
    tag_uptodate_alt_fg="#34d399",
    tag_downgrade_bg="#451a03",
    tag_downgrade_fg="#fbbf24",
    tag_fallback_bg="#1e1b4b",
    tag_fallback_fg="#818cf8",
    tag_incompat_bg="#450a0a",
    tag_incompat_fg="#f87171",
    tag_listed_bg="#1c263c",
    tag_listed_fg="#94a3b8",
    tag_unverified_bg="#451a03",
    tag_unverified_fg="#fbbf24",
    tag_ignored_bg="#2e1065",
    tag_ignored_fg="#c084fc",
    glass_backdrop_alpha=0.94,
    glass_border="#1e2c45",
    glass_highlight="#2a3b5a",
    glass_glow="#e11d48",
    dwm_backdrop_type=3,
    dwm_caption_bgr=0x00160D09,
    dwm_dark_mode=1,
)

# 2. WAKE THEME (Warm Editorial Linen Ivory Glass with Burgundy & Warm Amber Accents)
WAKE_THEME = ThemeColors(
    name="light",  # Retains 'light' for seamless backwards compatibility with test assertions
    bg_root="#faf7f2",
    bg_canvas="#fdfcf9",
    bg_panel="#f3eee5",
    bg_card="#f7f3eb",
    bg_card_hover="#eee7da",
    bg_card_selected="#e5dcce",
    bg_input="#ffffff",
    bg_table="#f7f3eb",
    bg_table_alt="#fbf9f4",
    bg_header="#fdfcf9",
    bg_button="#ffffff",
    bg_button_hover="#fff1f2",
    bg_button_active="#fecdd3",
    bg_sidebar="#f3eee5",
    border="#e5dcce",
    border_subtle="#eee8dd",
    border_accent="#800020",
    grid_line="#f3ede2",
    fg_primary="#1c1917",
    fg_secondary="#44403c",
    fg_muted="#78716c",
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
    glass_backdrop_alpha=0.96,
    glass_border="#e2d9cc",
    glass_highlight="#ffffff",
    glass_glow="#800020",
    dwm_backdrop_type=3,
    dwm_caption_bgr=0x00F2F7FA,
    dwm_dark_mode=0,
)

# 3. BLOOM THEME (Amethyst Surreal Architecture Glass with Vivid Violet & Magenta Accents)
BLOOM_THEME = ThemeColors(
    name="bloom",
    bg_root="#f0f3fc",
    bg_canvas="#f6f8fe",
    bg_panel="#e7ecf9",
    bg_card="#edf1fb",
    bg_card_hover="#e0e7f8",
    bg_card_selected="#d4def5",
    bg_input="#ffffff",
    bg_table="#edf1fb",
    bg_table_alt="#f4f7fd",
    bg_header="#f6f8fe",
    bg_button="#ffffff",
    bg_button_hover="#ede9fe",
    bg_button_active="#ddd6fe",
    bg_sidebar="#e7ecf9",
    border="#c7d2fe",
    border_subtle="#e0e7ff",
    border_accent="#7c3aed",
    grid_line="#eef2ff",
    fg_primary="#1e1b4b",
    fg_secondary="#4338ca",
    fg_muted="#6366f1",
    fg_accent="#7c3aed",
    fg_laser="#d946ef",
    accent_burgundy="#7c3aed",
    accent_burgundy_hover="#6d28d9",
    accent_cyan="#7c3aed",
    accent_emerald="#059669",
    accent_amber="#d97706",
    accent_crimson="#e11d48",
    accent_purple="#7c3aed",
    tag_available_bg="#fae8ff",
    tag_available_fg="#a21caf",
    tag_uptodate_bg="#ecfdf5",
    tag_uptodate_fg="#047857",
    tag_uptodate_alt_bg="#ecfdf5",
    tag_uptodate_alt_fg="#047857",
    tag_downgrade_bg="#fef3c7",
    tag_downgrade_fg="#b45309",
    tag_fallback_bg="#e0e7ff",
    tag_fallback_fg="#4338ca",
    tag_incompat_bg="#ffe4e6",
    tag_incompat_fg="#be123c",
    tag_listed_bg="#f1f5f9",
    tag_listed_fg="#475569",
    tag_unverified_bg="#fef3c7",
    tag_unverified_fg="#b45309",
    tag_ignored_bg="#f3e8ff",
    tag_ignored_fg="#7e22ce",
    glass_backdrop_alpha=0.96,
    glass_border="#c7d2fe",
    glass_highlight="#e0e7ff",
    glass_glow="#d946ef",
    dwm_backdrop_type=3,
    dwm_caption_bgr=0x00FCF3F0,
    dwm_dark_mode=0,
)

LIGHT_THEME = WAKE_THEME
DARK_THEME = DREAM_THEME

THEMES: Dict[str, ThemeColors] = {
    "light": WAKE_THEME,
    "dark": DREAM_THEME,
    "wake": WAKE_THEME,
    "dream": DREAM_THEME,
    "bloom": BLOOM_THEME,
}


def get_theme(name: str) -> ThemeColors:
    """Returns the ThemeColors corresponding to the given theme name (defaults to light)."""
    if not name:
        return WAKE_THEME
    return THEMES.get(name.lower(), WAKE_THEME)


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
