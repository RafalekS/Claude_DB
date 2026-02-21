"""
Theme management - Dynamic theme system with config file support
"""

import json
from pathlib import Path

# Path to themes config
THEMES_FILE = Path(__file__).parent.parent.parent / "config" / "themes.json"

# Load all available themes from config
def load_themes():
    """Load themes from config/themes.json"""
    try:
        with open(THEMES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading themes: {e}")
        # Return default Gruvbox Dark if file can't be loaded
        return {
            "Gruvbox Dark": {
                "background": "#282828",
                "foreground": "#EBDBB2",
                "brightBlue": "#83A598",
                "brightGreen": "#B8BB26",
                "brightRed": "#FB4934",
                "brightYellow": "#FABD2F",
                "selection": "#504945"
            }
        }

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


def apply_theme(theme_name, font_size=14):
    """
    Apply a new theme dynamically by updating all global variables

    Args:
        theme_name: Name of theme from AVAILABLE_THEMES
        font_size: Base font size in pixels
    """
    global GRUVBOX, BG_DARK, BG_MEDIUM, BG_LIGHT, FG_PRIMARY, FG_SECONDARY, FG_DIM
    global ACCENT_PRIMARY, ACCENT_SECONDARY, ERROR_COLOR, WARNING_COLOR, SUCCESS_COLOR
    global FONT_SIZE_LARGE, FONT_SIZE_NORMAL, FONT_SIZE_SMALL, FONT_SIZE_TINY
    global _current_theme

    if theme_name not in AVAILABLE_THEMES:
        print(f"Theme '{theme_name}' not found, using Gruvbox Dark")
        theme_name = "Gruvbox Dark"

    _current_theme = AVAILABLE_THEMES[theme_name]
    GRUVBOX = _current_theme.copy()

    # Update all color variables
    BG_DARK = _current_theme.get("background", "#282828")
    # Calculate medium and light variants
    BG_MEDIUM = lighten_color(BG_DARK, 0.1)
    BG_LIGHT = lighten_color(BG_DARK, 0.2)

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


def lighten_color(hex_color, factor=0.1):
    """Lighten a hex color by a factor (0.0 to 1.0)"""
    try:
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        # Convert to RGB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        # Lighten
        r = min(255, int(r + (255 - r) * factor))
        g = min(255, int(g + (255 - g) * factor))
        b = min(255, int(b + (255 - b) * factor))
        # Convert back to hex
        return f"#{r:02x}{g:02x}{b:02x}"
    except:
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
            padding: 6px 12px;
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

def get_text_edit_style():
    """Get text editor stylesheet"""
    return f"""
        QTextEdit, QPlainTextEdit {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
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
    """Get tab widget stylesheet"""
    return f"""
        QTabWidget::pane {{
            border: 1px solid {BG_LIGHT};
            background: {BG_DARK};
        }}
        QTabBar::tab {{
            background: {BG_MEDIUM};
            color: {FG_PRIMARY};
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid {BG_LIGHT};
            font-size: {FONT_SIZE_NORMAL}px;
        }}
        QTabBar::tab:selected {{
            background: {ACCENT_PRIMARY};
            color: {BG_DARK};
            font-weight: bold;
        }}
        QTabBar::tab:hover {{
            background: {BG_LIGHT};
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
            padding: 5px;
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
        }}

        /* Labels */
        QLabel {{
            color: {FG_PRIMARY};
            background-color: transparent;
        }}

        /* Buttons */
        QPushButton {{
            padding: 6px 12px;
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
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: {FONT_SIZE_NORMAL}px;
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            padding: 8px;
            selection-background-color: {GRUVBOX.get("selection", "#504945")};
        }}

        /* Text Browser */
        QTextBrowser {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            padding: 10px;
            font-size: {FONT_SIZE_NORMAL}px;
            selection-background-color: {GRUVBOX.get("selection", "#504945")};
        }}

        /* Line Edit */
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

        /* Combo Box */
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

        /* Spin Box */
        QSpinBox {{
            background-color: {BG_DARK};
            color: {FG_PRIMARY};
            border: 1px solid {BG_LIGHT};
            padding: 6px;
            font-size: {FONT_SIZE_NORMAL}px;
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            background-color: {ACCENT_PRIMARY};
            border: none;
            width: 20px;
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
            padding: 5px;
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

        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {BG_LIGHT};
            background: {BG_DARK};
        }}
        QTabBar::tab {{
            background: {BG_MEDIUM};
            color: {FG_PRIMARY};
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid {BG_LIGHT};
            font-size: {FONT_SIZE_NORMAL}px;
        }}
        QTabBar::tab:selected {{
            background: {ACCENT_PRIMARY};
            color: {BG_DARK};
            font-weight: bold;
        }}
        QTabBar::tab:hover {{
            background: {BG_LIGHT};
        }}

        /* Group Box */
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
