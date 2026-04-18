"""
Widget Theme Editor
===================
Right panel : real Qt widgets – click any to select it.
Left panel  : full property editor for the selected widget type
              (all CSS-like properties: color, radius, padding, font, hover, pressed …).

All changes apply LIVE to the running app via the global QSS override.
"""

import re

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QScrollArea, QFrame, QLineEdit,
    QSplitter, QApplication, QGridLayout, QSizePolicy
)
from PyQt6.QtGui import QIntValidator
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from utils import theme
from utils.widget_indexer import load_visible_ui_index, build_entries_by_qt_class

# ── Property type tokens ──────────────────────────────────────────────────────
COLOR  = 'color'
PX     = 'px'
BOOL   = 'bool'

# ── Pixel-valued CSS properties (need "px" suffix in QSS) ────────────────────
_PX_PROPS = {
    'border-radius', 'border-width', 'border-top-width', 'border-bottom-width',
    'border-left-width', 'border-right-width',
    'padding', 'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
    'margin', 'margin-top', 'margin-right', 'margin-bottom', 'margin-left',
    'font-size', 'spacing', 'width', 'height', 'max-height', 'min-height',
    'max-width', 'min-width', 'subcontrol-height',
}


def _fmt(qss_key, value) -> str:
    """Format one QSS property: value → declaration string."""
    if qss_key == 'font-weight':
        return f"font-weight: {'bold' if value else 'normal'}"
    if qss_key in _PX_PROPS and isinstance(value, int):
        return f"{qss_key}: {value}px"
    return f"{qss_key}: {value}"


def _c(key: str) -> str:
    return getattr(theme, key, '#888888')


def _n(key: str, fallback: int = 4) -> int:
    return getattr(theme, key, fallback)


# ── Widget definitions ────────────────────────────────────────────────────────
#
# Each entry:
#   selector  : the QSS base selector used when generating overrides
#   icon      : short emoji shown in the preview list header
#   props     : list of dicts:
#       {'section': 'Title'}          →  section separator label
#       {'label': ..., 'qss': ..., 'type': COLOR|PX|BOOL, 'state': ..., 'val': ...}
#                                     →  editable property
#       state is appended to selector verbatim (e.g. ':hover', '::chunk')

def _make_defs() -> dict:
    def _cp(label, qss, state, val_key):
        """Color prop with palette_key set."""
        return {'label': label, 'qss': qss, 'type': COLOR, 'state': state,
                'val': _c(val_key), 'palette_key': val_key}

    return {
        'Button': {
            'selector': 'QPushButton', 'qt_class': 'QPushButton',
            'icon': '⬜ Button',
            'props': [
                {'section': 'Normal'},
                _cp('Background',    'background-color', '',          'ACCENT_PRIMARY'),
                _cp('Text Color',    'color',            '',          'BG_DARK'),
                {'label': 'Border Radius', 'qss': 'border-radius', 'type': PX, 'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding V',     'qss': 'padding-top',   'type': PX, 'state': '', 'val': 4},
                {'label': 'Padding H',     'qss': 'padding-left',  'type': PX, 'state': '', 'val': 10},
                {'label': 'Font Size',     'qss': 'font-size',     'type': PX, 'state': '', 'val': _n('FONT_SIZE_NORMAL')},
                {'label': 'Bold',          'qss': 'font-weight',   'type': BOOL,'state': '', 'val': True},
                {'section': 'Hover'},
                _cp('Background',    'background-color', ':hover',    'ACCENT_SECONDARY'),
                _cp('Text Color',    'color',            ':hover',    'BG_DARK'),
                {'section': 'Pressed'},
                _cp('Background',    'background-color', ':pressed',  'BG_LIGHT'),
                {'section': 'Disabled'},
                _cp('Background',    'background-color', ':disabled', 'BG_MEDIUM'),
                _cp('Text Color',    'color',            ':disabled', 'FG_DIM'),
            ],
        },
        'Label': {
            'selector': 'QLabel', 'qt_class': 'QLabel',
            'icon': '🔤 Label',
            'props': [
                {'section': 'Normal'},
                _cp('Text Color',    'color',            '',          'FG_PRIMARY'),
                {'label': 'Font Size', 'qss': 'font-size', 'type': PX, 'state': '', 'val': _n('FONT_SIZE_NORMAL')},
                {'label': 'Bold',      'qss': 'font-weight','type': BOOL,'state': '', 'val': False},
                {'label': 'Padding',   'qss': 'padding',   'type': PX, 'state': '', 'val': 0},
                {'label': 'Background','qss': 'background-color','type': COLOR,'state': '', 'val': 'transparent'},
            ],
        },
        'Input': {
            'selector': 'QLineEdit', 'qt_class': 'QLineEdit',
            'icon': '📝 Input',
            'props': [
                {'section': 'Normal'},
                _cp('Background',    'background-color', '',       'BG_DARK'),
                _cp('Text Color',    'color',            '',       'FG_PRIMARY'),
                _cp('Border Color',  'border-color',     '',       'BG_LIGHT'),
                {'label': 'Border Width',  'qss': 'border-width',  'type': PX, 'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius', 'type': PX, 'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding',       'qss': 'padding',       'type': PX, 'state': '', 'val': 4},
                {'label': 'Font Size',     'qss': 'font-size',     'type': PX, 'state': '', 'val': _n('FONT_SIZE_NORMAL')},
                {'section': 'Focus'},
                _cp('Border Color',  'border-color',     ':focus', 'ACCENT_PRIMARY'),
            ],
        },
        'TextEdit': {
            'selector': 'QTextEdit', 'qt_class': 'QTextEdit',
            'icon': '📄 Text Editor',
            'props': [
                {'section': 'Normal'},
                _cp('Background',    'background-color', '',       'BG_DARK'),
                _cp('Text Color',    'color',            '',       'FG_PRIMARY'),
                _cp('Border Color',  'border-color',     '',       'BG_LIGHT'),
                {'label': 'Border Width',  'qss': 'border-width',  'type': PX, 'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius', 'type': PX, 'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding',       'qss': 'padding',       'type': PX, 'state': '', 'val': 4},
                {'label': 'Font Size',     'qss': 'font-size',     'type': PX, 'state': '', 'val': _n('FONT_SIZE_SMALL')},
            ],
        },
        'TextBrowser': {
            'selector': 'QTextBrowser', 'qt_class': 'QTextBrowser',
            'icon': '📰 Text Browser',
            'props': [
                {'section': 'Normal'},
                _cp('Background',    'background-color', '',       'BG_DARK'),
                _cp('Text Color',    'color',            '',       'FG_PRIMARY'),
                _cp('Border Color',  'border-color',     '',       'BG_LIGHT'),
                {'label': 'Border Width',  'qss': 'border-width',  'type': PX, 'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius', 'type': PX, 'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding',       'qss': 'padding',       'type': PX, 'state': '', 'val': 6},
                {'label': 'Font Size',     'qss': 'font-size',     'type': PX, 'state': '', 'val': _n('FONT_SIZE_SMALL')},
            ],
        },
        'ComboBox': {
            'selector': 'QComboBox', 'qt_class': 'QComboBox',
            'icon': '▼ ComboBox',
            'props': [
                {'section': 'Normal'},
                _cp('Background',    'background-color',  '',                    'BG_DARK'),
                _cp('Text Color',    'color',             '',                    'FG_PRIMARY'),
                _cp('Border Color',  'border-color',      '',                    'BG_LIGHT'),
                {'label': 'Border Width',  'qss': 'border-width',  'type': PX, 'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius', 'type': PX, 'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding',       'qss': 'padding',       'type': PX, 'state': '', 'val': 4},
                {'section': 'Hover'},
                _cp('Background',    'background-color',  ':hover',              'BG_MEDIUM'),
                {'section': 'Dropdown'},
                _cp('Drop BG',       'background-color',  ' QAbstractItemView',  'BG_DARK'),
                _cp('Drop Text',     'color',             ' QAbstractItemView',  'FG_PRIMARY'),
            ],
        },
        'CheckBox': {
            'selector': 'QCheckBox', 'qt_class': 'QCheckBox',
            'icon': '☑ CheckBox',
            'props': [
                {'section': 'Normal'},
                _cp('Text Color',    'color',             '',                    'FG_PRIMARY'),
                {'label': 'Font Size', 'qss': 'font-size', 'type': PX, 'state': '', 'val': _n('FONT_SIZE_NORMAL')},
                {'label': 'Spacing',   'qss': 'spacing',   'type': PX, 'state': '', 'val': 6},
                {'section': 'Checked Indicator'},
                _cp('Indicator BG',  'background-color',  '::indicator:checked', 'ACCENT_PRIMARY'),
                {'label': 'Indicator Size', 'qss': 'width', 'type': PX, 'state': '::indicator', 'val': 14},
            ],
        },
        'RadioButton': {
            'selector': 'QRadioButton', 'qt_class': 'QRadioButton',
            'icon': '○ RadioButton',
            'props': [
                {'section': 'Normal'},
                _cp('Text Color',    'color',             '',                    'FG_PRIMARY'),
                {'label': 'Font Size', 'qss': 'font-size', 'type': PX, 'state': '', 'val': _n('FONT_SIZE_NORMAL')},
                {'section': 'Checked Indicator'},
                _cp('Indicator BG',  'background-color',  '::indicator:checked', 'ACCENT_PRIMARY'),
                {'label': 'Indicator Size', 'qss': 'width', 'type': PX, 'state': '::indicator', 'val': 14},
            ],
        },
        'Table': {
            'selector': 'QTableWidget', 'qt_class': 'QTableWidget',
            'icon': '⊞ Table',
            'props': [
                {'section': 'Table'},
                _cp('Background',    'background-color',           '',               'BG_DARK'),
                _cp('Alt Row Color', 'alternate-background-color', '',               'BG_MEDIUM'),
                _cp('Grid Color',    'gridline-color',             '',               'BG_LIGHT'),
                {'label': 'Font Size', 'qss': 'font-size', 'type': PX, 'state': '', 'val': _n('FONT_SIZE_SMALL')},
                {'section': 'Header (QHeaderView)'},
                _cp('Header BG',     'background-color',           '::section',      'BG_MEDIUM'),
                _cp('Header Text',   'color',                      '::section',      'FG_PRIMARY'),
                {'section': 'Selection'},
                _cp('Selected BG',   'background-color',           '::item:selected','ACCENT_PRIMARY'),
                _cp('Selected Text', 'color',                      '::item:selected','BG_DARK'),
            ],
        },
        'List': {
            'selector': 'QListWidget', 'qt_class': 'QListWidget',
            'icon': '≡ List',
            'props': [
                {'section': 'List'},
                _cp('Background',    'background-color', '',              'BG_DARK'),
                _cp('Text Color',    'color',            '',              'FG_PRIMARY'),
                {'label': 'Font Size', 'qss': 'font-size', 'type': PX, 'state': '', 'val': _n('FONT_SIZE_SMALL')},
                {'section': 'Item Hover'},
                _cp('Hover BG',      'background-color', '::item:hover',  'BG_MEDIUM'),
                _cp('Hover Text',    'color',            '::item:hover',  'FG_PRIMARY'),
                {'section': 'Selected Item'},
                _cp('Selected BG',   'background-color', '::item:selected','ACCENT_PRIMARY'),
                _cp('Selected Text', 'color',            '::item:selected','BG_DARK'),
            ],
        },
        'TreeWidget': {
            'selector': 'QTreeWidget', 'qt_class': 'QTreeWidget',
            'icon': '🌲 Tree',
            'props': [
                {'section': 'Tree'},
                _cp('Background',    'background-color', '',               'BG_DARK'),
                _cp('Text Color',    'color',            '',               'FG_PRIMARY'),
                {'label': 'Font Size', 'qss': 'font-size', 'type': PX, 'state': '', 'val': _n('FONT_SIZE_SMALL')},
                {'section': 'Item Hover'},
                _cp('Hover BG',      'background-color', '::item:hover',   'BG_MEDIUM'),
                {'section': 'Selected Item'},
                _cp('Selected BG',   'background-color', '::item:selected','ACCENT_PRIMARY'),
                _cp('Selected Text', 'color',            '::item:selected','BG_DARK'),
                {'section': 'Branch indicator'},
                _cp('Branch BG',     'background-color', '::branch',       'BG_DARK'),
            ],
        },
        'GroupBox': {
            'selector': 'QGroupBox', 'qt_class': 'QGroupBox',
            'icon': '▣ GroupBox',
            'props': [
                {'section': 'Normal'},
                _cp('Title Color',   'color',            '',               'FG_PRIMARY'),
                _cp('Background',    'background-color', '',               'BG_MEDIUM'),
                _cp('Border Color',  'border-color',     '',               'BG_LIGHT'),
                {'label': 'Border Width',  'qss': 'border-width',  'type': PX,   'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius', 'type': PX,   'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding Top',   'qss': 'padding-top',   'type': PX,   'state': '', 'val': 14},
                {'label': 'Font Bold',     'qss': 'font-weight',   'type': BOOL, 'state': '', 'val': True},
            ],
        },
        'TabPane': {
            'selector': 'QTabWidget::pane', 'qt_class': 'QTabWidget',
            'icon': '🗂 Tab Pane',
            'props': [
                {'section': 'Pane'},
                _cp('Background',    'background-color', '',               'BG_DARK'),
                _cp('Border Color',  'border-color',     '',               'BG_LIGHT'),
                {'label': 'Border Width',  'qss': 'border-width',  'type': PX, 'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius', 'type': PX, 'state': '', 'val': _n('BORDER_RADIUS')},
            ],
        },
        'ProgressBar': {
            'selector': 'QProgressBar', 'qt_class': 'QProgressBar',
            'icon': '░ ProgressBar',
            'props': [
                {'section': 'Track'},
                _cp('Background',    'background-color', '',        'BG_MEDIUM'),
                {'label': 'Border Radius', 'qss': 'border-radius', 'type': PX, 'state': '', 'val': 4},
                _cp('Text Color',    'color',            '',        'FG_PRIMARY'),
                {'label': 'Max Height',    'qss': 'max-height',    'type': PX, 'state': '', 'val': 12},
                {'section': 'Fill (::chunk)'},
                _cp('Fill Color',    'background-color', '::chunk', 'ACCENT_PRIMARY'),
                {'label': 'Fill Radius',   'qss': 'border-radius', 'type': PX, 'state': '::chunk', 'val': 4},
            ],
        },
        'Slider': {
            'selector': 'QSlider', 'qt_class': 'QSlider',
            'icon': '▬ Slider',
            'props': [
                {'section': 'Handle'},
                _cp('Handle Color',  'background-color', '::handle:horizontal', 'ACCENT_PRIMARY'),
                {'label': 'Handle Width',  'qss': 'width',        'type': PX, 'state': '::handle:horizontal', 'val': 14},
                {'label': 'Handle Height', 'qss': 'height',       'type': PX, 'state': '::handle:horizontal', 'val': 14},
                {'label': 'Handle Radius', 'qss': 'border-radius','type': PX, 'state': '::handle:horizontal', 'val': 7},
                {'section': 'Groove'},
                _cp('Groove Color',  'background-color', '::groove:horizontal', 'BG_MEDIUM'),
                {'label': 'Groove Height', 'qss': 'height',       'type': PX, 'state': '::groove:horizontal', 'val': 6},
                {'label': 'Groove Radius', 'qss': 'border-radius','type': PX, 'state': '::groove:horizontal', 'val': 3},
            ],
        },
        'SpinBox': {
            'selector': 'QSpinBox', 'qt_class': 'QSpinBox',
            'icon': '123 SpinBox',
            'props': [
                {'section': 'Normal'},
                _cp('Background',    'background-color', '',       'BG_DARK'),
                _cp('Text Color',    'color',            '',       'FG_PRIMARY'),
                _cp('Border Color',  'border-color',     '',       'BG_LIGHT'),
                {'label': 'Border Width',  'qss': 'border-width',  'type': PX, 'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius', 'type': PX, 'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding',       'qss': 'padding',       'type': PX, 'state': '', 'val': 3},
                {'section': 'Focus'},
                _cp('Border Color',  'border-color',     ':focus', 'ACCENT_PRIMARY'),
            ],
        },
        'Tabs': {
            'selector': 'QTabBar::tab', 'qt_class': 'QTabBar',
            'icon': '📑 Tab Bar',
            'props': [
                {'section': 'Normal Tab'},
                _cp('Background',    'background-color', '',          'BG_MEDIUM'),
                _cp('Text Color',    'color',            '',          'FG_SECONDARY'),
                {'label': 'Padding',       'qss': 'padding',       'type': PX, 'state': '', 'val': 6},
                {'label': 'Border Radius', 'qss': 'border-radius', 'type': PX, 'state': '', 'val': 4},
                {'label': 'Font Size',     'qss': 'font-size',     'type': PX, 'state': '', 'val': _n('FONT_SIZE_TAB', 11)},
                {'section': 'Selected'},
                _cp('Background',    'background-color', ':selected', 'BG_DARK'),
                _cp('Text Color',    'color',            ':selected', 'FG_PRIMARY'),
                {'section': 'Hover'},
                _cp('Background',    'background-color', ':hover',    'BG_LIGHT'),
                _cp('Text Color',    'color',            ':hover',    'FG_PRIMARY'),
            ],
        },
        'Splitter': {
            'selector': 'QSplitter::handle', 'qt_class': 'QSplitter',
            'icon': '┃ Splitter',
            'props': [
                {'section': 'Handle'},
                _cp('Color',         'background-color', '',          'BG_LIGHT'),
                {'label': 'Width',  'qss': 'width',  'type': PX, 'state': ':horizontal', 'val': 4},
                {'label': 'Height', 'qss': 'height', 'type': PX, 'state': ':vertical',   'val': 4},
            ],
        },
        'Divider': {
            'selector': 'QFrame[frameShape="4"]', 'qt_class': 'QFrame',
            'icon': '─── Divider',
            'props': [
                {'section': 'Line'},
                _cp('Color',         'color',            '',          'BG_LIGHT'),
                {'label': 'Max Height', 'qss': 'max-height', 'type': PX, 'state': '', 'val': 1},
            ],
        },
        'ScrollBar': {
            'selector': 'QScrollBar', 'qt_class': 'QScrollBar',
            'icon': '│ ScrollBar',
            'props': [
                {'section': 'Track'},
                _cp('Track Color',   'background-color', '',                    'BG_DARK'),
                {'label': 'Width',  'qss': 'width',  'type': PX, 'state': ':vertical',   'val': 8},
                {'label': 'Height', 'qss': 'height', 'type': PX, 'state': ':horizontal', 'val': 8},
                {'section': 'Handle'},
                _cp('Handle Color',  'background-color', '::handle:vertical',        'BG_LIGHT'),
                {'label': 'Handle Radius', 'qss': 'border-radius', 'type': PX, 'state': '::handle:vertical', 'val': 4},
                {'label': 'Min Length',    'qss': 'min-height',    'type': PX, 'state': '::handle:vertical', 'val': 20},
                {'section': 'Handle Hover'},
                _cp('Hover Color',   'background-color', '::handle:vertical:hover', 'ACCENT_PRIMARY'),
            ],
        },
        'Dialog': {
            'selector': 'QDialog', 'qt_class': 'QDialog',
            'icon': '🪟 Dialog',
            'props': [
                {'section': 'Normal'},
                _cp('Background',    'background-color', '',          'BG_DARK'),
                _cp('Text Color',    'color',            '',          'FG_PRIMARY'),
                {'label': 'Font Size', 'qss': 'font-size', 'type': PX, 'state': '', 'val': _n('FONT_SIZE_NORMAL')},
            ],
        },
        'ToolTip': {
            'selector': 'QToolTip', 'qt_class': 'QToolTip',
            'icon': '💬 ToolTip',
            'props': [
                {'section': 'Normal'},
                _cp('Background',    'background-color', '',          'BG_MEDIUM'),
                _cp('Text Color',    'color',            '',          'FG_PRIMARY'),
                _cp('Border Color',  'border-color',     '',          'BG_LIGHT'),
                {'label': 'Border Width',  'qss': 'border-width',  'type': PX, 'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius', 'type': PX, 'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding',       'qss': 'padding',       'type': PX, 'state': '', 'val': 4},
                {'label': 'Font Size',     'qss': 'font-size',     'type': PX, 'state': '', 'val': _n('FONT_SIZE_SMALL')},
            ],
        },
    }


WIDGET_DEFS = _make_defs()


# ── QSS generation ────────────────────────────────────────────────────────────

def build_overrides_qss(overrides: dict) -> str:
    """Convert the overrides dict into a QSS string.

    overrides structure:
        { widget_name: { (state, qss_key): value, ... }, ... }
    """
    # group declarations by full selector
    by_sel: dict[str, dict] = {}
    for wname, state_map in overrides.items():
        if wname not in WIDGET_DEFS:
            continue
        base_sel = WIDGET_DEFS[wname]['selector']
        for (state, qss_key), value in state_map.items():
            full_sel = base_sel + state
            by_sel.setdefault(full_sel, {})[qss_key] = value

    parts = []
    for sel, decls in by_sel.items():
        decl_str = '; '.join(_fmt(k, v) for k, v in decls.items())
        parts.append(f"{sel} {{ {decl_str} }}")
    return '\n'.join(parts)


# ── ColorSwatch ───────────────────────────────────────────────────────────────

class ColorSwatch(QFrame):
    """Clickable color swatch. Custom-painted so it is never overridden by the
    global app QSS (which can stomp QPushButton backgrounds)."""

    clicked = pyqtSignal()

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = color if color and color.startswith('#') else '#888888'
        self.setFixedSize(40, 26)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Click to pick colour")

    def set_color(self, color: str):
        self._color = color if color and color.startswith('#') else '#888888'
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        try:
            p.fillRect(self.rect().adjusted(1, 1, -1, -1), QColor(self._color))
        except Exception:
            p.fillRect(self.rect().adjusted(1, 1, -1, -1), QColor('#888888'))
        pen_color = QColor(theme.FG_DIM)
        p.setPen(pen_color)
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _location_display_name(class_name: str) -> tuple[str, str]:
    """Return (human_name, type_badge) for a navigable UI class."""
    for suffix, badge in (("SubTab", "subtab"), ("Dialog", "dialog"), ("Tab", "tab")):
        if class_name.endswith(suffix):
            raw = class_name[:-len(suffix)]
            # Insert spaces before capitals: "UserHooks" → "User Hooks"
            name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', raw)
            return name, badge
    return class_name, ""


# ── WidgetPreviewPanel ────────────────────────────────────────────────────────

class WidgetPreviewPanel(QScrollArea):
    """Left panel — a clean scrollable list of widget-type buttons.
    Click one to load its properties in the right panel.
    Only shows widgets that are actually used somewhere in the app's tabs."""

    widget_selected    = pyqtSignal(str)       # name of selected widget
    usage_panel_toggled = pyqtSignal(bool)      # checkbox state changed

    _BTN_H = 38

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumWidth(190)
        self.setMaximumWidth(220)
        self._buttons: dict[str, QPushButton] = {}
        self._selected: str | None = None

        # Load visible UI index — only navigable locations, smarter detection
        try:
            self._vis_idx = load_visible_ui_index()
        except Exception:
            self._vis_idx = {}

        # Build {qt_class: [nav_entries]} with accurate per-method-body detection.
        # Each anonymous subtab (e.g. MemoryTab::Overview) is scanned against
        # only its builder method body, not the whole file.
        try:
            self._entries_by_qt_class = build_entries_by_qt_class()
        except Exception:
            self._entries_by_qt_class = {}

        content = QWidget()
        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(6, 6, 6, 8)
        vbox.setSpacing(3)

        # ── "Show usage panel" checkbox ───────────────────────────────────────
        usage_chk = QCheckBox("Show usage panel")
        usage_chk.setStyleSheet(
            f"QCheckBox {{ color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; }}"
        )
        usage_chk.setToolTip(
            "Opens a panel to the right showing which tabs/dialogs use the selected widget.\n"
            "Click any entry to navigate there."
        )
        usage_chk.stateChanged.connect(
            lambda s: self.usage_panel_toggled.emit(s == 2)
        )
        self._usage_chk = usage_chk
        vbox.addWidget(usage_chk)

        # ── Buttons — only widgets with ≥ 1 visible location ─────────────────
        for wname, wdef in WIDGET_DEFS.items():
            qt_class = wdef.get('qt_class', wdef['selector'].split('::')[0].split(' ')[0])
            locations = self._vis_idx.get(qt_class, [])
            if not locations:
                continue   # not used anywhere in the app — skip

            btn = QPushButton(wdef['icon'])
            btn.setCheckable(True)
            btn.setFixedHeight(self._BTN_H)
            btn.setStyleSheet(self._btn_style(False))
            btn.setToolTip(f"Used in {len(locations)} location(s)")
            btn.clicked.connect(lambda _checked, n=wname: self._select(n))
            self._buttons[wname] = btn
            vbox.addWidget(btn)

        vbox.addStretch()
        self.setWidget(content)

    @staticmethod
    def _btn_style(active: bool) -> str:
        if active:
            return (
                f"QPushButton {{ background-color: {theme.ACCENT_PRIMARY}; color: {theme.BG_DARK}; "
                f"border: none; border-radius: 4px; padding: 0 10px; "
                f"font-weight: bold; text-align: left; }}"
            )
        return (
            f"QPushButton {{ background-color: {theme.BG_MEDIUM}; color: {theme.FG_PRIMARY}; "
            f"border: 1px solid {theme.BG_LIGHT}; border-radius: 4px; padding: 0 10px; "
            f"text-align: left; }}"
            f"QPushButton:hover {{ background-color: {theme.BG_LIGHT}; }}"
        )

    def apply_theme(self):
        """Refresh colours after a theme change."""
        for n, btn in self._buttons.items():
            btn.setStyleSheet(self._btn_style(n == self._selected))
        self._usage_chk.setStyleSheet(
            f"QCheckBox {{ color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; }}"
        )

    def _select(self, name: str):
        for n, btn in self._buttons.items():
            active = (n == name)
            btn.setChecked(active)
            btn.setStyleSheet(self._btn_style(active))
        self._selected = name
        self.widget_selected.emit(name)


# ── UsagePanel ────────────────────────────────────────────────────────────────

class UsagePanel(QWidget):
    """Third pane — shows where the currently selected widget is used.
    Each location is a clickable button; clicking emits navigate_to(class_name)
    so the main window can switch to that tab/subtab/dialog."""

    navigate_to = pyqtSignal(str)   # emits the class name to navigate to

    _COLS_THRESHOLD_2 = 7    # use 2 cols when locations > this
    _COLS_THRESHOLD_3 = 18   # use 3 cols when locations > this

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        # Title label
        self._title_lbl = QLabel("Select a widget to see where it is used")
        self._title_lbl.setWordWrap(True)
        self._title_lbl.setStyleSheet(
            f"font-weight: bold; color: {theme.ACCENT_PRIMARY}; padding-bottom: 4px;"
        )
        outer.addWidget(self._title_lbl)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {theme.BG_LIGHT};")
        sep.setFixedHeight(1)
        outer.addWidget(sep)

        # Scrollable grid of location buttons
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        outer.addWidget(scroll, 1)

        self._grid_widget = QWidget()
        self._grid = QGridLayout(self._grid_widget)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(4)
        scroll.setWidget(self._grid_widget)

        # Hint at the bottom
        self._hint_lbl = QLabel("Click any location to navigate there")
        self._hint_lbl.setStyleSheet(
            f"color: {theme.FG_DIM}; font-style: italic; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        outer.addWidget(self._hint_lbl)

        self._loc_btns: list[QPushButton] = []

    def update_locations(self, widget_display_name: str, entries: list[dict]):
        """Rebuild the grid with nav entries, grouped Tab → SubTab → Dialog."""
        # Clear grid
        for w in self._loc_btns:
            w.deleteLater()
        self._loc_btns.clear()
        while self._grid.count():
            item = self._grid.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        n = len(entries)
        if n == 0:
            self._title_lbl.setText(f"{widget_display_name} — not used in any tab/dialog")
            self._hint_lbl.hide()
            return

        self._title_lbl.setText(f"{widget_display_name}  —  {n} location{'s' if n != 1 else ''}")
        self._hint_lbl.show()

        # Group by type
        groups: dict[str, tuple[str, list]] = {
            "Tab":    ("🗂  Tabs",     []),
            "SubTab": ("📑  SubTabs",  []),
            "Dialog": ("💬  Dialogs",  []),
            "other":  ("▸  Other",    []),
        }
        for entry in entries:
            t = entry.get("type", "other")
            groups.get(t, groups["other"])[1].append(entry)

        cols = 1
        if n > self._COLS_THRESHOLD_3:
            cols = 3
        elif n > self._COLS_THRESHOLD_2:
            cols = 2

        grid_row = 0
        for grp_key, (section_title, entry_list) in groups.items():
            if not entry_list:
                continue

            hdr = QLabel(section_title)
            hdr.setStyleSheet(
                f"color: {theme.ACCENT_SECONDARY}; font-weight: bold; "
                f"font-size: {theme.FONT_SIZE_SMALL}px; letter-spacing: 1px; "
                f"padding: 6px 0 2px 0; background: transparent;"
            )
            self._grid.addWidget(hdr, grid_row, 0, 1, cols)
            grid_row += 1

            for col_idx, entry in enumerate(
                sorted(entry_list, key=lambda e: e["label"])
            ):
                label       = entry["label"]
                parent_lbl  = entry.get("parent_label")
                # Button text: label on first line, "↳ Parent" on second if subtab
                btn_text    = f"{label}\n↳ {parent_lbl}" if parent_lbl else label
                tooltip     = (f"sub of {parent_lbl}" if parent_lbl else entry.get("type", ""))

                btn = QPushButton(btn_text)
                btn.setToolTip(tooltip)
                btn.setStyleSheet(self._loc_btn_style())
                btn.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Expanding,
                )
                # Navigate to parent class for anonymous/named subtabs;
                # the main window's navigate_to_class handles Tab/SubTab lookup.
                nav_target = entry.get("parent_id") or entry["id"]
                btn.clicked.connect(
                    lambda _c, cn=nav_target: self.navigate_to.emit(cn)
                )

                row = grid_row + col_idx // cols
                col = col_idx % cols
                self._grid.addWidget(btn, row, col)
                self._loc_btns.append(btn)

            grid_row += (len(entry_list) + cols - 1) // cols

        if n < 45:
            for r in range(grid_row):
                self._grid.setRowStretch(r, 1)

    @staticmethod
    def _loc_btn_style() -> str:
        return (
            f"QPushButton {{ background-color: {theme.BG_MEDIUM}; color: {theme.FG_PRIMARY}; "
            f"border: 1px solid {theme.BG_LIGHT}; border-radius: 4px; "
            f"padding: 5px 8px; text-align: left; font-size: {theme.FONT_SIZE_SMALL}px; }}"
            f"QPushButton:hover {{ background-color: {theme.ACCENT_PRIMARY}; "
            f"color: {theme.BG_DARK}; border-color: {theme.ACCENT_PRIMARY}; }}"
        )

    def apply_theme(self):
        self._title_lbl.setStyleSheet(
            f"font-weight: bold; color: {theme.ACCENT_PRIMARY}; padding-bottom: 4px;"
        )
        self._hint_lbl.setStyleSheet(
            f"color: {theme.FG_DIM}; font-style: italic; font-size: {theme.FONT_SIZE_SMALL}px;"
        )
        for btn in self._loc_btns:
            btn.setStyleSheet(self._loc_btn_style())
        # Restyle section header labels in the grid
        hdr_style = (
            f"color: {theme.ACCENT_SECONDARY}; font-weight: bold; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; letter-spacing: 1px; "
            f"padding: 6px 0 2px 0; background: transparent;"
        )
        for i in range(self._grid.count()):
            w = self._grid.itemAt(i).widget()
            if isinstance(w, QLabel):
                w.setStyleSheet(hdr_style)


# ── WidgetPropertyPanel ───────────────────────────────────────────────────────

_ROW_H   = 30   # every editor row same height
_LBL_W   = 130  # label column width
_SWATCH_W = 40  # colour swatch width
_HEX_W   = 90   # hex input width
_SPIN_W  = 90   # spinbox width


class WidgetPropertyPanel(QScrollArea):
    """Right panel — all editable QSS properties for the selected widget type,
    plus palette color entries that edit global theme variables directly."""

    property_changed = pyqtSignal(str, str, str, object)

    def __init__(self, overrides: dict, parent=None):
        super().__init__(parent)
        self._overrides = overrides
        self._current: str | None = None

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._vbox = QVBoxLayout(self._content)
        self._vbox.setContentsMargins(10, 10, 10, 10)
        self._vbox.setSpacing(0)
        self._vbox.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._show_placeholder()
        self.setWidget(self._content)

    # ── public ────────────────────────────────────────────────────────────────

    def load_widget(self, widget_name: str):
        if widget_name not in WIDGET_DEFS:
            return
        self._current = widget_name
        self._clear()

        wdef = WIDGET_DEFS[widget_name]

        # Title row
        title = QLabel(wdef['icon'])
        title.setStyleSheet(
            f"font-weight: bold; color: {theme.ACCENT_PRIMARY}; padding: 0 0 8px 0;"
        )
        self._vbox.addWidget(title)

        overrides_for = self._overrides.get(widget_name, {})
        for prop in wdef['props']:
            if 'section' in prop:
                self._add_section_header(prop['section'])
            else:
                self._add_prop_row(widget_name, prop, overrides_for)

    # ── private ───────────────────────────────────────────────────────────────

    def _show_placeholder(self):
        ph = QLabel("← Select a widget type to edit")
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.setStyleSheet(f"color: {theme.FG_DIM}; font-style: italic;")
        self._vbox.addWidget(ph)

    def _clear(self):
        while self._vbox.count():
            item = self._vbox.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _add_section_header(self, title: str):
        lbl = QLabel(title.upper())
        lbl.setFixedHeight(28)
        lbl.setStyleSheet(
            f"color: {theme.ACCENT_SECONDARY}; font-weight: bold; letter-spacing: 1px; "
            f"border-bottom: 1px solid {theme.BG_LIGHT}; "
            f"padding: 8px 0 2px 0; background: transparent;"
        )
        self._vbox.addWidget(lbl)

    def _add_prop_row(self, widget_name: str, prop: dict, overrides_for: dict):
        state    = prop['state']
        qss_key  = prop['qss']
        key      = (state, qss_key)
        cur_val  = overrides_for.get(key, prop['val'])

        row = QWidget()
        row.setFixedHeight(_ROW_H)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Label — fixed width, left-aligned, vertically centred
        lbl = QLabel(prop['label'])
        lbl.setFixedWidth(_LBL_W)
        lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        lbl.setStyleSheet(f"color: {theme.FG_PRIMARY}; background: transparent;")
        h.addWidget(lbl)

        # Editor — fixed width per type so it never expands
        ptype = prop['type']
        if ptype == COLOR:
            editor = self._make_color_editor(widget_name, state, qss_key, cur_val)
            editor.setFixedWidth(_SWATCH_W + 6 + _HEX_W)
        elif ptype == PX:
            editor = self._make_px_editor(widget_name, state, qss_key, cur_val)
            editor.setFixedWidth(_SPIN_W)
        elif ptype == BOOL:
            editor = self._make_bool_editor(widget_name, state, qss_key, cur_val)
            editor.setFixedWidth(24)
        else:
            editor = QLabel(f"({ptype}?)")
            editor.setFixedWidth(60)

        editor.setFixedHeight(_ROW_H - 4)
        h.addWidget(editor)
        h.addStretch(1)   # absorbs remaining space — keeps everything left-aligned

        self._vbox.addWidget(row)

    def _make_color_editor(self, wn, state, qss_key, cur_val) -> QWidget:
        hex_val = cur_val if isinstance(cur_val, str) and cur_val.startswith('#') else '#888888'

        container = QWidget()
        container.setFixedHeight(_ROW_H - 4)
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        swatch = ColorSwatch(hex_val)
        hex_edit = QLineEdit(hex_val)
        hex_edit.setFixedWidth(_HEX_W)
        hex_edit.setFixedHeight(_ROW_H - 6)
        hex_edit.setStyleSheet(
            f"QLineEdit {{ font-family: {theme.FONT_MONOSPACE}; font-size: {theme.FONT_SIZE_SMALL}px; "
            f"background: {theme.BG_DARK}; color: {theme.FG_PRIMARY}; "
            f"border: 1px solid {theme.BG_LIGHT}; border-radius: 3px; padding: 0 4px; }}"
        )

        def _pick():
            from PyQt6.QtWidgets import QColorDialog
            c = QColorDialog.getColor(QColor(hex_edit.text()), container, f"Pick — {qss_key}")
            if c.isValid():
                hex_edit.blockSignals(True)
                hex_edit.setText(c.name())
                hex_edit.blockSignals(False)
                swatch.set_color(c.name())
                self._emit_change(wn, state, qss_key, c.name())

        def _hex_typed(text: str):
            if len(text) == 7 and text.startswith('#'):
                try:
                    QColor(text)
                    swatch.set_color(text)
                    self._emit_change(wn, state, qss_key, text)
                except Exception:
                    pass

        swatch.clicked.connect(_pick)
        hex_edit.textChanged.connect(_hex_typed)

        h.addWidget(swatch)
        h.addWidget(hex_edit)
        return container

    def _make_px_editor(self, wn, state, qss_key, cur_val) -> QWidget:
        le = QLineEdit()
        le.setValidator(QIntValidator(0, 200, le))
        le.setFixedWidth(_SPIN_W)
        le.setFixedHeight(_ROW_H - 4)
        le.setAlignment(Qt.AlignmentFlag.AlignRight)
        le.setPlaceholderText("px")
        le.setStyleSheet(
            f"QLineEdit {{ background: {theme.BG_DARK}; color: {theme.FG_PRIMARY}; "
            f"border: 1px solid {theme.BG_LIGHT}; border-radius: 3px; padding: 0 4px; }}"
        )
        try:
            le.setText(str(int(cur_val)))
        except (TypeError, ValueError):
            le.setText("0")

        def _on_change(text, _wn=wn, _st=state, _qk=qss_key):
            try:
                self._emit_change(_wn, _st, _qk, int(text))
            except ValueError:
                pass

        le.textChanged.connect(_on_change)
        return le

    def _make_bool_editor(self, wn, state, qss_key, cur_val) -> QWidget:
        container = QWidget()
        container.setFixedHeight(_ROW_H - 4)
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0)
        h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        cb = QCheckBox()
        cb.setChecked(bool(cur_val))
        cb.setStyleSheet(f"QCheckBox {{ color: {theme.FG_PRIMARY}; }}")
        cb.stateChanged.connect(
            lambda s, _wn=wn, _st=state, _qk=qss_key: self._emit_change(_wn, _st, _qk, s == 2)
        )
        h.addWidget(cb)
        return container

    def _emit_change(self, wn: str, state: str, qss_key: str, value):
        self._overrides.setdefault(wn, {})[(state, qss_key)] = value
        self.property_changed.emit(wn, state, qss_key, value)


# ── WidgetThemeEditor (top-level widget) ──────────────────────────────────────

class WidgetThemeEditor(QSplitter):
    """The full interactive widget theme editor.

    Left   : widget selector list (WidgetPreviewPanel)
    Middle : property editor for the selected widget (WidgetPropertyPanel)
    Right  : usage panel — where the widget is used (UsagePanel, shown on demand)

    Usage:
        editor = WidgetThemeEditor()
        # call editor.get_overrides_qss() to get current QSS string
        # call editor.load_overrides(dict) to restore saved overrides
    """

    navigate_to = pyqtSignal(str)   # class name to navigate to (forwarded from UsagePanel)

    def __init__(self, on_change_callback=None, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._overrides: dict = {}
        self._on_change = on_change_callback

        self._preview_panel = WidgetPreviewPanel()
        self._prop_panel    = WidgetPropertyPanel(self._overrides)
        self._prop_panel.setMinimumWidth(300)
        self._usage_panel   = UsagePanel()

        self.addWidget(self._preview_panel)
        self.addWidget(self._prop_panel)
        self.addWidget(self._usage_panel)
        self._usage_panel.hide()
        self.setSizes([200, 700, 300])

        # Prevent any pane from being collapsed to zero by dragging
        self.setCollapsible(0, False)
        self.setCollapsible(1, False)
        self.setCollapsible(2, False)

        # Wire: selecting a widget/palette entry → load props + update usage panel
        self._preview_panel.widget_selected.connect(self._prop_panel.load_widget)
        self._preview_panel.widget_selected.connect(self._on_widget_selected)
        self._prop_panel.property_changed.connect(self._on_property_changed)

        # Wire: checkbox toggle → show/hide usage panel
        self._preview_panel.usage_panel_toggled.connect(self._toggle_usage_panel)

        # Wire: clicking a location → forward navigate signal
        self._usage_panel.navigate_to.connect(self.navigate_to)

    def _toggle_usage_panel(self, visible: bool):
        self._usage_panel.setVisible(visible)
        # If showing and a widget is already selected, populate immediately
        if visible and self._preview_panel._selected:
            self._on_widget_selected(self._preview_panel._selected)

    def _on_widget_selected(self, widget_name: str):
        """When a widget is selected, update the usage panel if visible."""
        if not self._usage_panel.isVisible():
            return
        wdef = WIDGET_DEFS.get(widget_name)
        if not wdef:
            return
        qt_class = wdef.get('qt_class', wdef['selector'].split('::')[0].split(' ')[0])
        entries = self._preview_panel._entries_by_qt_class.get(qt_class, [])
        self._usage_panel.update_locations(wdef['icon'], entries)

    def apply_theme(self):
        """Refresh colours after a global theme change."""
        # Rebuild widget default values in-place so they reflect the new theme palette
        new_defs = _make_defs()
        WIDGET_DEFS.clear()
        WIDGET_DEFS.update(new_defs)

        self._preview_panel.apply_theme()
        self._usage_panel.apply_theme()
        # Re-render property panel so section headers / labels pick up new theme colors
        # (palette entries also re-read their var so the swatch shows the new value)
        if self._prop_panel._current:
            self._prop_panel.load_widget(self._prop_panel._current)

    def _on_property_changed(self, wn: str, state: str, qss_key: str, value):
        if self._on_change:
            self._on_change()

    def get_overrides_qss(self) -> str:
        """Return the current per-widget overrides as a QSS string."""
        return build_overrides_qss(self._overrides)

    # ── Public API: full widget definitions ───────────────────────────────────

    # Properties that Typography (FONT_SIZE_*) controls globally.
    # These are NOT stored in Widget Styles by default so that changing
    # Typography still has effect on all widgets.  Only stored if the user
    # explicitly overrides them per-widget in the property panel.
    _TYPOGRAPHY_PROPS = {'font-size', 'font-weight'}

    def get_widgets_dict(self) -> dict:
        """Return widget properties for ALL widget types as a complete,
        JSON-serializable dict suitable for storing in themes.json.

        Font-size and font-weight are omitted from auto-generated defaults so
        that Typography (Global Theme) still controls them.  They are only
        included when the user has explicitly set an override per widget.

        Structure:
            { "Button": { "|background-color": "#83A598", ":hover|background-color": "#B8BB26", ... }, ... }
        """
        current_defs = _make_defs()   # fresh defaults from current theme globals
        result = {}
        for wname, wdef in current_defs.items():
            props = {}
            overrides_for = self._overrides.get(wname, {})
            for p in wdef['props']:
                if 'qss' not in p:
                    continue   # section header row — skip
                state   = p['state']
                qss_key = p['qss']
                key_str = f"{state}|{qss_key}"
                key     = (state, qss_key)
                if key in overrides_for:
                    # User explicitly set this — always include
                    props[key_str] = overrides_for[key]
                elif qss_key not in self._TYPOGRAPHY_PROPS:
                    # Non-typography default — include
                    props[key_str] = p['val']
                # else: typography prop with no override — skip (Typography column controls it)
            if props:
                result[wname] = props
        return result

    def load_widgets_dict(self, data: dict):
        """Load a full widgets dict (from themes.json 'widgets' key).
        Treats every entry as an override of the computed theme defaults so that
        the property panel reflects the saved values when a widget is selected.
        """
        self._overrides.clear()
        for wname, flat in data.items():
            if wname not in WIDGET_DEFS:
                continue
            inner = {}
            for key_str, val in flat.items():
                if '|' in key_str:
                    st, qk = key_str.split('|', 1)
                    inner[(st, qk)] = val
            if inner:
                self._overrides[wname] = inner
        # Refresh the property panel if a widget is already selected
        if self._prop_panel._current:
            self._prop_panel.load_widget(self._prop_panel._current)

    # ── Backward-compat aliases (used by load_preferences / config.json) ─────

    def get_overrides_dict(self) -> dict:
        """Deprecated — use get_widgets_dict() for themes.json.
        Returns only the user-changed properties (not the full defaults)."""
        result = {}
        for wname, state_map in self._overrides.items():
            result[wname] = {f"{st}|{qk}": v for (st, qk), v in state_map.items()}
        return result

    def load_overrides(self, data: dict):
        """Load a previously-saved overrides dict (also accepts full widgets dict)."""
        self.load_widgets_dict(data)
