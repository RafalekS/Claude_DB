"""
Theme management - Dynamic theme system with config file support
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Path to themes config
THEMES_FILE = Path(__file__).parent.parent.parent / "config" / "themes" / "themes.json"

# Meta-keys stored at the top level of themes.json that are NOT theme entries
_META_KEYS = {"active_theme"}

_FALLBACK_THEMES = {
    "Gruvbox Dark": {
        "background": "#282828",
        "foreground": "#EBDBB2",
        "brightBlue": "#83A598",
        "brightGreen": "#B8BB26",
        "brightRed": "#FB4934",
        "brightYellow": "#FABD2F",
        "selection": "#504945",
        "font_size": 14,
        "font_family": "Segoe UI",
        "font_mono": "Consolas",
        "custom_colors": {},
        "custom_numbers": {},
    }
}


def _load_raw_themes() -> dict:
    """Load the raw themes.json dict (including meta-keys like active_theme)."""
    try:
        with open(THEMES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error("Error loading themes: %s", e)
        return {"active_theme": "Gruvbox Dark", **_FALLBACK_THEMES}


def load_themes() -> dict:
    """Return only theme entries (excludes meta-keys like active_theme)."""
    raw = _load_raw_themes()
    return {k: v for k, v in raw.items() if k not in _META_KEYS}


def get_active_theme_name() -> str:
    """Return the name of the active theme stored in themes.json."""
    raw = _load_raw_themes()
    return raw.get("active_theme", "Gruvbox Dark")


def set_active_theme_name(name: str) -> None:
    """Persist the active theme name to themes.json."""
    try:
        raw = _load_raw_themes()
        raw["active_theme"] = name
        with open(THEMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(raw, f, indent=2)
    except Exception as e:
        logger.error("Failed to set active theme '%s': %s", name, e)


# Load themes once
AVAILABLE_THEMES = load_themes()

# Current theme data (mutable - can be changed at runtime)
_current_theme = AVAILABLE_THEMES.get("Gruvbox Dark", {})

# Mutable global variables for current theme
GRUVBOX = _current_theme.copy()
BG_DARK = _current_theme.get("background", "#282828")
BG_MEDIUM = "#3c3836"  # calculated
BG_LIGHT = "#504945"   # calculated
FG_PRIMARY = _current_theme.get("foreground", "#EBDBB2")
FG_SECONDARY = _current_theme.get("white", "#A89984")
FG_DIM = _current_theme.get("brightBlack", "#928374")
ACCENT_PRIMARY = _current_theme.get("brightBlue", "#83A598")
ACCENT_SECONDARY = _current_theme.get("brightGreen", "#B8BB26")
ERROR_COLOR = _current_theme.get("brightRed", "#FB4934")
WARNING_COLOR = _current_theme.get("brightYellow", "#FABD2F")
SUCCESS_COLOR = _current_theme.get("brightGreen", "#B8BB26")

# Font sizes - READABLE! (mutable)
FONT_SIZE_LARGE = 16
FONT_SIZE_NORMAL = 14
FONT_SIZE_SMALL = 12
FONT_SIZE_TINY = 11
FONT_SIZE_TAB = 13

# Font constants
FONT_MONOSPACE = "Consolas"
FONT_FAMILY_MONO = "'Consolas', 'Monaco', 'Courier New', monospace"
FONT_FAMILY = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
# Current UI font family (mutable — updated by apply_theme)
FONT_FAMILY_UI = "Segoe UI"

# UI spacing constants (consistent across all widgets)
MARGIN_SM = 3
MARGIN_MD = 6
MARGIN_LG = 10
PADDING_SM = 4
PADDING_MD = 8
BORDER_RADIUS = 4


def apply_theme(theme_name, font_size=14, font_family=None):
    """
    Apply a new theme dynamically by updating all global variables.

    Args:
        theme_name:   Name of theme from AVAILABLE_THEMES
        font_size:    Base font size in pixels
        font_family:  UI font family name (e.g. "Segoe UI", "Calibri")
    """
    global GRUVBOX, BG_DARK, BG_MEDIUM, BG_LIGHT, FG_PRIMARY, FG_SECONDARY, FG_DIM
    global ACCENT_PRIMARY, ACCENT_SECONDARY, ERROR_COLOR, WARNING_COLOR, SUCCESS_COLOR
    global FONT_SIZE_LARGE, FONT_SIZE_NORMAL, FONT_SIZE_SMALL, FONT_SIZE_TINY, FONT_SIZE_TAB
    global FONT_FAMILY, FONT_FAMILY_UI, _current_theme

    if theme_name not in AVAILABLE_THEMES:
        logger.warning("Theme '%s' not found, using Gruvbox Dark", theme_name)
        theme_name = "Gruvbox Dark"

    _current_theme = AVAILABLE_THEMES[theme_name]
    GRUVBOX = _current_theme.copy()

    # Update all color variables
    BG_DARK = _current_theme.get("background", "#282828")
    # For light themes, surfaces must go DARKER (not lighter) to stay visible
    if is_light_color(BG_DARK):
        BG_MEDIUM = darken_color(BG_DARK, 0.08)   # subtle surface: #f3f3f3 → #e1e1e1
        BG_LIGHT  = darken_color(BG_DARK, 0.17)   # border/divider:  #f3f3f3 → #cacacc
    else:
        BG_MEDIUM = lighten_color(BG_DARK, 0.1)
        BG_LIGHT  = lighten_color(BG_DARK, 0.2)

    FG_PRIMARY = _current_theme.get("foreground", "#EBDBB2")
    FG_SECONDARY = _current_theme.get("white", "#A89984")
    FG_DIM = _current_theme.get("brightBlack", "#928374")
    ACCENT_PRIMARY = _current_theme.get("brightBlue", "#83A598")
    ACCENT_SECONDARY = _current_theme.get("brightGreen", "#B8BB26")
    ERROR_COLOR = _current_theme.get("brightRed", "#FB4934")
    WARNING_COLOR = _current_theme.get("brightYellow", "#FABD2F")
    SUCCESS_COLOR = _current_theme.get("brightGreen", "#B8BB26")

    # Update font sizes
    FONT_SIZE_NORMAL = font_size
    FONT_SIZE_LARGE = font_size + 2
    FONT_SIZE_SMALL = max(10, font_size - 2)
    FONT_SIZE_TINY = max(9, font_size - 3)
    FONT_SIZE_TAB = max(11, font_size - 1)

    # Update UI font family if provided
    if font_family:
        FONT_FAMILY_UI = font_family
        FONT_FAMILY = f"'{font_family}', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"


def is_light_color(hex_color: str) -> bool:
    """Return True if the colour is perceptually light (luminance > 60%)."""
    try:
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        # Standard perceived-luminance formula (WCAG)
        return (r * 299 + g * 587 + b * 114) / 1000 > 155
    except Exception:
        return False


def lighten_color(hex_color, factor=0.1):
    """Move a colour towards white by factor (0.0–1.0)."""
    try:
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


def darken_color(hex_color, factor=0.1):
    """Move a colour towards black by factor (0.0–1.0)."""
    try:
        h = hex_color.lstrip('#')
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        r = max(0, int(r * (1 - factor)))
        g = max(0, int(g * (1 - factor)))
        b = max(0, int(b * (1 - factor)))
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return hex_color


# Stylesheet templates (these read current global variables)
def get_main_window_style():
    """Get main window stylesheet"""
    return f"""
        QMainWindow, QWidget {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            font-size: {FONT_SIZE_NORMAL}px;
        }}
    """

def get_button_style():
    """Get button stylesheet"""
    return f"""
        QPushButton {{
            padding: 4px 10px;
            background-color: {ACCENT_PRIMARY};
            color: {BG_DARK};
            border-radius: 4px;
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: bold;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_SECONDARY};
        }}
        QPushButton:pressed {{
            background-color: {BG_LIGHT};
        }}
    """

def get_monospace_font(size=None):
    """Return a QFont for monospace display (Consolas stack)."""
    from PyQt6.QtGui import QFont
    return QFont(FONT_MONOSPACE, size if size is not None else FONT_SIZE_SMALL)


def get_warning_button_style():
    """Warning action button style (yellow background, dark text)."""
    return f"""
        QPushButton {{
            padding: 4px 10px;
            background-color: {WARNING_COLOR};
            color: {BG_DARK};
            border-radius: {BORDER_RADIUS}px;
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: bold;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_SECONDARY};
            color: {BG_DARK};
        }}
        QPushButton:disabled {{
            background-color: {BG_MEDIUM};
            color: {FG_DIM};
        }}
    """


def get_success_button_style():
    """Success/positive action button style (green background, dark text)."""
    return f"""
        QPushButton {{
            padding: 4px 10px;
            background-color: {SUCCESS_COLOR};
            color: {BG_DARK};
            border-radius: {BORDER_RADIUS}px;
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: bold;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_PRIMARY};
            color: {BG_DARK};
        }}
        QPushButton:disabled {{
            background-color: {BG_MEDIUM};
            color: {FG_DIM};
        }}
    """


def get_button_danger_style():
    """Destructive button style (Delete, Remove, Reset — red accent)."""
    return f"""
        QPushButton {{
            padding: 4px 10px;
            background-color: {ERROR_COLOR};
            color: {BG_DARK};
            border-radius: {BORDER_RADIUS}px;
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: bold;
            border: none;
        }}
        QPushButton:hover {{
            background-color: #cc241d;
        }}
        QPushButton:pressed {{
            background-color: {BG_LIGHT};
        }}
        QPushButton:disabled {{
            background-color: {BG_MEDIUM};
            color: {FG_DIM};
        }}
    """


def get_button_neutral_style():
    """Neutral / secondary button style (Cancel, Refresh — muted)."""
    return f"""
        QPushButton {{
            padding: 4px 10px;
            background-color: {BG_MEDIUM};
            color: {FG_PRIMARY};
            border-radius: {BORDER_RADIUS}px;
            font-size: {FONT_SIZE_NORMAL}px;
            border: 1px solid {BG_LIGHT};
        }}
        QPushButton:hover {{
            background-color: {BG_LIGHT};
        }}
        QPushButton:pressed {{
            background-color: {BG_DARK};
        }}
        QPushButton:disabled {{
            color: {FG_DIM};
        }}
    """


def get_text_edit_style():
    """Get text editor stylesheet"""
    return f"""
        QTextEdit, QPlainTextEdit {{
            font-family: {FONT_FAMILY_MONO};
            font-size: {FONT_SIZE_NORMAL}px;
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            padding: 8px;
            selection-background-color: {GRUVBOX.get("selection", "#504945")};
        }}
    """

def get_list_widget_style():
    """Get list widget stylesheet"""
    return f"""
        QListWidget {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            font-size: {FONT_SIZE_NORMAL}px;
        }}
        QListWidget::item:selected {{
            background-color: {GRUVBOX.get("selection", "#504945")};
            color: {FG_PRIMARY};
        }}
        QListWidget::item:hover {{
            background-color: {BG_MEDIUM};
        }}
    """

def get_line_edit_style():
    """Get line edit stylesheet"""
    return f"""
        QLineEdit {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            padding: 6px;
            font-size: {FONT_SIZE_NORMAL}px;
            selection-background-color: {GRUVBOX.get("selection", "#504945")};
        }}
        QLineEdit:focus {{
            border: 1px solid {ACCENT_PRIMARY};
        }}
    """

def get_combo_style():
    """Get combo box stylesheet"""
    return f"""
        QComboBox {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            padding: 6px;
            font-size: {FONT_SIZE_NORMAL}px;
        }}
        QComboBox:hover {{
            border: 1px solid {ACCENT_PRIMARY};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {FG_PRIMARY};
            width: 0px;
            height: 0px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            selection-background-color: {ACCENT_PRIMARY};
            selection-color: {BG_DARK};
            border: 1px solid {BG_LIGHT};
            max-height: 300px;
        }}
    """

def get_text_browser_style():
    """Get text browser stylesheet"""
    return f"""
        QTextBrowser {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            padding: 10px;
            font-size: {FONT_SIZE_NORMAL}px;
            selection-background-color: {GRUVBOX.get("selection", "#504945")};
        }}
    """

def get_label_style(size="normal", color="primary"):
    """Get label stylesheet"""
    font_size = {
        "large": FONT_SIZE_LARGE,
        "normal": FONT_SIZE_NORMAL,
        "small": FONT_SIZE_SMALL
    }.get(size, FONT_SIZE_NORMAL)

    text_color = {
        "primary": FG_PRIMARY,
        "secondary": FG_SECONDARY,
        "dim": FG_DIM,
        "accent": ACCENT_PRIMARY
    }.get(color, FG_PRIMARY)

    return f"color: {text_color}; font-size: {font_size}px;"

def get_tab_widget_style():
    """Get tab widget stylesheet — accent-colour underline on selected tab."""
    return f"""
        QTabWidget::pane {{
            border: 1px solid {BG_LIGHT};
            background: {BG_DARK};
        }}
        QTabBar::tab {{
            background: {BG_MEDIUM};
            color: {FG_SECONDARY};
            padding: 6px 14px;
            margin-right: 2px;
            border: 1px solid {BG_LIGHT};
            border-bottom: none;
            font-size: {FONT_SIZE_TAB}px;
        }}
        QTabBar::tab:selected {{
            background: {BG_DARK};
            color: {FG_PRIMARY};
            border-bottom: 2px solid {ACCENT_PRIMARY};
            font-weight: bold;
        }}
        QTabBar::tab:hover:!selected {{
            background: {BG_LIGHT};
            color: {FG_PRIMARY};
        }}
    """

def get_groupbox_style():
    """Get group box stylesheet"""
    return f"""
        QGroupBox {{
            font-weight: bold;
            border: 1px solid {BG_LIGHT};
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
            color: {FG_PRIMARY};
            background-color: {BG_MEDIUM};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            background-color: {BG_MEDIUM};
        }}
    """

def get_table_style():
    """Get table widget stylesheet"""
    return f"""
        QTableWidget {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            font-size: {FONT_SIZE_NORMAL}px;
            gridline-color: {BG_LIGHT};
        }}
        QTableWidget::item {{
            padding: 3px 5px;
        }}
        QTableWidget::item:selected {{
            background-color: {GRUVBOX.get("selection", "#504945")};
            color: {FG_PRIMARY};
        }}
        QTableWidget::item:hover {{
            background-color: {BG_MEDIUM};
        }}
        QHeaderView::section {{
            background-color: {BG_MEDIUM};
            color: {FG_PRIMARY};
            padding: 5px;
            border: 1px solid {BG_LIGHT};
            font-weight: bold;
            font-size: {FONT_SIZE_NORMAL}px;
        }}
    """


def generate_app_stylesheet():
    """
    Generate complete application stylesheet for dynamic theme switching.
    This applies the theme to the entire QApplication instantly.
    """
    return f"""
        /* Main Window and Widgets */
        QMainWindow, QWidget {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            font-size: {FONT_SIZE_NORMAL}px;
            font-family: {FONT_FAMILY_UI};
        }}

        /* Labels */
        QLabel {{
            color: {FG_PRIMARY};
            background-color: transparent;
        }}

        /* Buttons */
        QPushButton {{
            padding: 4px 10px;
            background-color: {ACCENT_PRIMARY};
            color: {BG_DARK};
            border-radius: 4px;
            font-size: {FONT_SIZE_NORMAL}px;
            font-weight: bold;
            border: none;
        }}
        QPushButton:hover {{
            background-color: {ACCENT_SECONDARY};
        }}
        QPushButton:pressed {{
            background-color: {BG_LIGHT};
        }}
        QPushButton:disabled {{
            background-color: {BG_MEDIUM};
            color: {FG_DIM};
        }}

        /* Text Editors */
        QTextEdit, QPlainTextEdit {{
            font-family: {FONT_FAMILY_MONO};
            font-size: {FONT_SIZE_SMALL}px;
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            padding: 4px;
            selection-background-color: {GRUVBOX.get("selection", "#504945")};
        }}

        /* Text Browser */
        QTextBrowser {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            padding: 6px;
            font-size: {FONT_SIZE_SMALL}px;
            selection-background-color: {GRUVBOX.get("selection", "#504945")};
        }}

        /* Line Edit */
        QLineEdit {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            padding: 4px;
            font-size: {FONT_SIZE_NORMAL}px;
            selection-background-color: {GRUVBOX.get("selection", "#504945")};
        }}
        QLineEdit:focus {{
            border: 1px solid {ACCENT_PRIMARY};
        }}

        /* Combo Box */
        QComboBox {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            padding: 4px;
            font-size: {FONT_SIZE_NORMAL}px;
            combobox-popup: 0;
        }}
        QComboBox:hover {{
            border: 1px solid {ACCENT_PRIMARY};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {FG_PRIMARY};
            width: 0px;
            height: 0px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            selection-background-color: {ACCENT_PRIMARY};
            selection-color: {BG_DARK};
            border: 1px solid {BG_LIGHT};
            max-height: 300px;
        }}

        /* Spin Box */
        QSpinBox {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            border-radius: 3px;
            padding: 2px 4px;
            font-size: {FONT_SIZE_NORMAL}px;
            min-height: 26px;
        }}
        QSpinBox::up-button {{
            background-color: {BG_MEDIUM};
            border: none;
            border-left: 1px solid {BG_LIGHT};
            border-bottom: 1px solid {BG_LIGHT};
            width: 22px;
            height: 13px;
            subcontrol-origin: border;
            subcontrol-position: top right;
        }}
        QSpinBox::down-button {{
            background-color: {BG_MEDIUM};
            border: none;
            border-left: 1px solid {BG_LIGHT};
            width: 22px;
            height: 13px;
            subcontrol-origin: border;
            subcontrol-position: bottom right;
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background-color: {ACCENT_PRIMARY};
        }}
        QSpinBox::up-arrow {{
            width: 8px;
            height: 8px;
        }}
        QSpinBox::down-arrow {{
            width: 8px;
            height: 8px;
        }}

        /* List Widget */
        QListWidget {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            font-size: {FONT_SIZE_NORMAL}px;
        }}
        QListWidget::item:selected {{
            background-color: {GRUVBOX.get("selection", "#504945")};
            color: {FG_PRIMARY};
        }}
        QListWidget::item:hover {{
            background-color: {BG_MEDIUM};
        }}

        /* Table Widget */
        QTableWidget {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            font-size: {FONT_SIZE_NORMAL}px;
            gridline-color: {BG_LIGHT};
        }}
        QTableWidget::item {{
            padding: 3px 5px;
        }}
        QTableWidget::item:selected {{
            background-color: {GRUVBOX.get("selection", "#504945")};
            color: {FG_PRIMARY};
        }}
        QTableWidget::item:hover {{
            background-color: {BG_MEDIUM};
        }}
        QHeaderView::section {{
            background-color: {BG_MEDIUM};
            color: {FG_PRIMARY};
            padding: 5px;
            border: 1px solid {BG_LIGHT};
            font-weight: bold;
            font-size: {FONT_SIZE_NORMAL}px;
        }}

        /* Tab Widget — accent-colour underline on selected tab */
        QTabWidget::pane {{
            border: 1px solid {BG_LIGHT};
            background: {BG_DARK};
        }}
        QTabBar::tab {{
            background: {BG_MEDIUM};
            color: {FG_SECONDARY};
            padding: 6px 14px;
            margin-right: 2px;
            border: 1px solid {BG_LIGHT};
            border-bottom: none;
            font-size: {FONT_SIZE_TAB}px;
        }}
        QTabBar::tab:selected {{
            background: {BG_DARK};
            color: {FG_PRIMARY};
            border-bottom: 2px solid {ACCENT_PRIMARY};
            font-weight: bold;
        }}
        QTabBar::tab:hover:!selected {{
            background: {BG_LIGHT};
            color: {FG_PRIMARY};
        }}

        /* Group Box */
        QGroupBox {{
            font-weight: bold;
            border: 1px solid {BG_LIGHT};
            border-radius: 4px;
            margin-top: 10px;
            padding-top: 10px;
            color: {FG_PRIMARY};
            background-color: {BG_MEDIUM};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            background-color: {BG_MEDIUM};
            color: {FG_PRIMARY};
        }}

        /* Scroll Bars */
        QScrollBar:vertical {{
            background-color: {BG_DARK};
            width: 12px;
            border: none;
        }}
        QScrollBar::handle:vertical {{
            background-color: {BG_LIGHT};
            border-radius: 6px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{
            background-color: {ACCENT_PRIMARY};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}

        QScrollBar:horizontal {{
            background-color: {BG_DARK};
            height: 12px;
            border: none;
        }}
        QScrollBar::handle:horizontal {{
            background-color: {BG_LIGHT};
            border-radius: 6px;
            min-width: 20px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background-color: {ACCENT_PRIMARY};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}

        /* Splitter */
        QSplitter::handle {{
            background-color: {BG_LIGHT};
        }}
        QSplitter::handle:horizontal {{
            width: 2px;
        }}
        QSplitter::handle:vertical {{
            height: 2px;
        }}

        /* Status Bar */
        QStatusBar {{
            background-color: {BG_MEDIUM};
            color: {FG_PRIMARY};
            border-top: 1px solid {BG_LIGHT};
        }}

        /* Stacked Widget */
        QStackedWidget {{
            border: 1px solid {BG_LIGHT};
            background: {BG_DARK};
        }}
    """


def apply_color_overrides(overrides: dict):
    """Apply custom per-variable color overrides on top of the current theme.
    Keys are theme module variable names (e.g. 'BG_DARK', 'ACCENT_PRIMARY').
    Call generate_app_stylesheet() afterwards to propagate changes.
    """
    g = globals()
    for var_name, hex_value in overrides.items():
        if var_name in g and isinstance(hex_value, str) and hex_value.startswith("#"):
            g[var_name] = hex_value


def apply_number_overrides(overrides: dict):
    """Apply custom numeric overrides for font sizes and spacing constants.
    Keys are theme module variable names (e.g. 'FONT_SIZE_NORMAL', 'BORDER_RADIUS').
    Call generate_app_stylesheet() afterwards to propagate changes.
    """
    g = globals()
    for var_name, val in overrides.items():
        if var_name in g and isinstance(val, (int, float)):
            g[var_name] = int(val)


def get_current_colors_dict() -> dict:
    """Return current color globals in themes.json-compatible format."""
    return {
        "background":   BG_DARK,
        "foreground":   FG_PRIMARY,
        "white":        FG_SECONDARY,
        "brightBlack":  FG_DIM,
        "brightBlue":   ACCENT_PRIMARY,
        "brightGreen":  ACCENT_SECONDARY,
        "brightRed":    ERROR_COLOR,
        "brightYellow": WARNING_COLOR,
        "selection":    BG_LIGHT,
    }


def save_theme_to_file(
    name: str,
    widgets: dict | None = None,
    font_size: int | None = None,
    font_family: str | None = None,
    font_mono: str | None = None,
    custom_colors: dict | None = None,
    custom_numbers: dict | None = None,
    set_active: bool = False,
) -> bool:
    """Snapshot current color globals and save as a named entry in themes.json.

    All per-theme data (fonts, overrides, widget styles) is stored under the
    theme entry so themes.json is the single source of truth.

    Returns True on success.
    """
    global AVAILABLE_THEMES
    try:
        raw = _load_raw_themes()
        existing = {k: v for k, v in raw.items() if k not in _META_KEYS}
        entry = get_current_colors_dict()

        # Persist per-theme font settings
        entry["font_size"] = font_size if font_size is not None else FONT_SIZE_NORMAL
        entry["font_family"] = font_family if font_family is not None else FONT_FAMILY_UI
        entry["font_mono"] = font_mono if font_mono is not None else FONT_MONOSPACE

        # Persist per-theme color/number overrides
        entry["custom_colors"] = custom_colors if custom_colors is not None else {}
        entry["custom_numbers"] = custom_numbers if custom_numbers is not None else {}

        # Persist widget overrides
        if widgets is not None:
            entry["widgets"] = widgets
        elif name in existing:
            for key in ("widgets", "__widget_overrides"):
                if key in existing[name]:
                    entry["widgets"] = existing[name][key]
                    break

        raw[name] = entry
        if set_active:
            raw["active_theme"] = name
        with open(THEMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(raw, f, indent=2)
        AVAILABLE_THEMES = load_themes()
        return True
    except Exception as e:
        logger.error("Failed to save theme '%s': %s", name, e)
        return False


def get_theme_widgets(name: str) -> dict:
    """Return the full widget definitions stored in the named theme, or {}.
    Falls back to the legacy ``__widget_overrides`` key for backward compat.
    """
    themes = load_themes()
    entry = themes.get(name, {})
    return entry.get("widgets", entry.get("__widget_overrides", {}))


def delete_theme_from_file(name: str) -> bool:
    """Remove a named theme from themes.json. Returns True on success."""
    global AVAILABLE_THEMES
    try:
        raw = _load_raw_themes()
        if name not in raw:
            return False
        del raw[name]
        # If deleted theme was active, reset to first available theme
        if raw.get("active_theme") == name:
            remaining = [k for k in raw if k not in _META_KEYS]
            raw["active_theme"] = remaining[0] if remaining else "Gruvbox Dark"
        with open(THEMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(raw, f, indent=2)
        AVAILABLE_THEMES = load_themes()
        return True
    except Exception as e:
        logger.error("Failed to delete theme '%s': %s", name, e)
        return False
