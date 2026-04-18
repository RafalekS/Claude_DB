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


# ── Palette definitions ───────────────────────────────────────────────────────
# Maps theme variable name → display info.
# Order determines display order in the palette list.

PALETTE_DEFS = {
    'BG_DARK':          {'label': '🌑 Background',    'usage': 'main window bg, code blocks, text editors'},
    'BG_MEDIUM':        {'label': '⬛ Surface',        'usage': 'panels, footers, inputs, header bg'},
    'BG_LIGHT':         {'label': '▫ Surface Light',  'usage': 'borders, dividers, scrollbars'},
    'FG_PRIMARY':       {'label': '📝 Text Primary',   'usage': 'headings, labels, primary text'},
    'FG_SECONDARY':     {'label': '📃 Text Secondary', 'usage': 'descriptions, subtitles, dim labels'},
    'FG_DIM':           {'label': '🔅 Text Dim',       'usage': 'disabled text, placeholders'},
    'ACCENT_PRIMARY':   {'label': '🔵 Accent',         'usage': 'buttons, active tabs, links, key actions'},
    'ACCENT_SECONDARY': {'label': '🟢 Accent Alt',     'usage': 'footer borders, section markers, hover state'},
    'ERROR_COLOR':      {'label': '🔴 Error',          'usage': 'error messages, destructive actions'},
    'WARNING_COLOR':    {'label': '🟡 Warning',        'usage': 'warnings, caution indicators'},
    'SUCCESS_COLOR':    {'label': '✅ Success',        'usage': 'success messages, OK states'},
}

_PALETTE_PREFIX  = 'PALETTE/'

# ── Typography and Spacing definitions ────────────────────────────────────────

TYPO_DEFS = {
    'FONT_FAMILY_UI':   {
        'label': '🔤 UI Font',    'type': 'font_ui',
        'choices': ["Segoe UI", "Arial", "Calibri", "Tahoma", "Verdana",
                    "Trebuchet MS", "Georgia", "Helvetica", "Ubuntu", "Noto Sans", "Open Sans"],
        'usage': 'All text in the app — labels, buttons, inputs, menus',
    },
    'FONT_MONOSPACE':   {
        'label': '💻 Mono Font',  'type': 'font_mono',
        'choices': ["Consolas", "Courier New", "DejaVu Sans Mono", "Liberation Mono",
                    "Monaco", "Menlo", "SF Mono", "Cascadia Code", "Fira Code",
                    "JetBrains Mono", "Source Code Pro"],
        'usage': 'Code blocks, hex inputs, terminal-style text',
    },
    'FONT_SIZE_NORMAL': {'label': '🔡 Size Normal', 'type': 'px', 'lo': 8,  'hi': 24, 'default': 14,
                         'usage': 'Default font size everywhere (labels, inputs, buttons)'},
    'FONT_SIZE_LARGE':  {'label': '🔡 Size Large',  'type': 'px', 'lo': 10, 'hi': 28, 'default': 16,
                         'usage': 'Section headers and large titles'},
    'FONT_SIZE_SMALL':  {'label': '🔡 Size Small',  'type': 'px', 'lo': 7,  'hi': 20, 'default': 12,
                         'usage': 'Descriptions, sub-labels, table cell text'},
    'FONT_SIZE_TINY':   {'label': '🔡 Size Tiny',   'type': 'px', 'lo': 6,  'hi': 18, 'default': 11,
                         'usage': 'Status bar, footnotes, very small hints'},
    'FONT_SIZE_TAB':    {'label': '🔡 Size Tab',    'type': 'px', 'lo': 8,  'hi': 20, 'default': 13,
                         'usage': 'Tab bar labels on QTabBar'},
}

SPACING_DEFS = {
    'BORDER_RADIUS': {'label': '◻ Border Radius', 'type': 'px', 'lo': 0, 'hi': 20, 'default': 4,
                      'usage': 'Widget corner radius (buttons, inputs, cards)'},
    'MARGIN_SM':     {'label': '↔ Margin SM',     'type': 'px', 'lo': 0, 'hi': 20, 'default': 3,
                      'usage': 'Smallest outer margin between elements'},
    'MARGIN_MD':     {'label': '↔ Margin MD',     'type': 'px', 'lo': 0, 'hi': 30, 'default': 6,
                      'usage': 'Medium outer margin between sections'},
    'MARGIN_LG':     {'label': '↔ Margin LG',     'type': 'px', 'lo': 0, 'hi': 40, 'default': 10,
                      'usage': 'Large outer margin for major sections'},
    'PADDING_SM':    {'label': '⬜ Padding SM',    'type': 'px', 'lo': 0, 'hi': 20, 'default': 4,
                      'usage': 'Small inner padding inside widgets'},
    'PADDING_MD':    {'label': '⬜ Padding MD',    'type': 'px', 'lo': 0, 'hi': 30, 'default': 8,
                      'usage': 'Standard inner padding for inputs and panels'},
}

_TYPO_PREFIX    = 'TYPO/'
_SPACING_PREFIX = 'SPACING/'


def _build_palette_usage() -> dict:
    """Return {palette_var_name: [(widget_name, icon, prop_label, state), ...]}
    Built by scanning WIDGET_DEFS for palette_key fields."""
    usage: dict = {}
    for wname, wdef in WIDGET_DEFS.items():
        for prop in wdef.get('props', []):
            pk = prop.get('palette_key')
            if pk:
                usage.setdefault(pk, []).append(
                    (wname, wdef['icon'], prop['label'], prop.get('state', ''))
                )
    return usage


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

        # ── Palette section ───────────────────────────────────────────────────
        palette_hdr = QLabel("PALETTE COLORS")
        palette_hdr.setStyleSheet(
            f"color: {theme.ACCENT_SECONDARY}; font-weight: bold; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; letter-spacing: 1px; padding: 4px 0 2px 0;"
        )
        vbox.addWidget(palette_hdr)

        for var_name, pdef in PALETTE_DEFS.items():
            key = _PALETTE_PREFIX + var_name
            btn = QPushButton(pdef['label'])
            btn.setCheckable(True)
            btn.setFixedHeight(self._BTN_H)
            btn.setStyleSheet(self._btn_style(False))
            btn.setToolTip(pdef['usage'])
            btn.clicked.connect(lambda _checked, n=key: self._select(n))
            self._buttons[key] = btn
            vbox.addWidget(btn)

        # ── Separator ─────────────────────────────────────────────────────────
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet(f"color: {theme.BG_LIGHT};")
        sep1.setFixedHeight(1)
        vbox.addWidget(sep1)

        # ── Typography section ────────────────────────────────────────────────
        typo_hdr = QLabel("TYPOGRAPHY")
        typo_hdr.setStyleSheet(
            f"color: {theme.ACCENT_SECONDARY}; font-weight: bold; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; letter-spacing: 1px; padding: 4px 0 2px 0;"
        )
        vbox.addWidget(typo_hdr)

        for var_name, tdef in TYPO_DEFS.items():
            key = _TYPO_PREFIX + var_name
            btn = QPushButton(tdef['label'])
            btn.setCheckable(True)
            btn.setFixedHeight(self._BTN_H)
            btn.setStyleSheet(self._btn_style(False))
            btn.setToolTip(tdef['usage'])
            btn.clicked.connect(lambda _checked, n=key: self._select(n))
            self._buttons[key] = btn
            vbox.addWidget(btn)

        # ── Spacing section ───────────────────────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {theme.BG_LIGHT};")
        sep2.setFixedHeight(1)
        vbox.addWidget(sep2)

        spacing_hdr = QLabel("SPACING & LAYOUT")
        spacing_hdr.setStyleSheet(
            f"color: {theme.ACCENT_SECONDARY}; font-weight: bold; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; letter-spacing: 1px; padding: 4px 0 2px 0;"
        )
        vbox.addWidget(spacing_hdr)

        for var_name, sdef in SPACING_DEFS.items():
            key = _SPACING_PREFIX + var_name
            btn = QPushButton(sdef['label'])
            btn.setCheckable(True)
            btn.setFixedHeight(self._BTN_H)
            btn.setStyleSheet(self._btn_style(False))
            btn.setToolTip(sdef['usage'])
            btn.clicked.connect(lambda _checked, n=key: self._select(n))
            self._buttons[key] = btn
            vbox.addWidget(btn)

        # ── Separator ─────────────────────────────────────────────────────────
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setStyleSheet(f"color: {theme.BG_LIGHT};")
        sep3.setFixedHeight(1)
        vbox.addWidget(sep3)

        # ── Widget list title ─────────────────────────────────────────────────
        widget_hdr = QLabel("WIDGET STYLES")
        widget_hdr.setStyleSheet(
            f"color: {theme.ACCENT_SECONDARY}; font-weight: bold; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; letter-spacing: 1px; padding: 4px 0 2px 0;"
        )
        vbox.addWidget(widget_hdr)

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

    property_changed   = pyqtSignal(str, str, str, object)
    palette_changed    = pyqtSignal(str, str)   # (var_name, new_hex)
    typo_changed       = pyqtSignal(str, object) # (var_name, value)
    navigate_to_widget = pyqtSignal(str)          # wname — navigate to widget in left panel

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
        if widget_name.startswith(_PALETTE_PREFIX):
            self._load_palette_entry(widget_name[len(_PALETTE_PREFIX):])
            return
        if widget_name.startswith(_TYPO_PREFIX):
            self._load_typo_entry(widget_name[len(_TYPO_PREFIX):])
            return
        if widget_name.startswith(_SPACING_PREFIX):
            self._load_spacing_entry(widget_name[len(_SPACING_PREFIX):])
            return
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
        ph = QLabel("← Select a palette color\nor widget type to edit")
        ph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph.setStyleSheet(f"color: {theme.FG_DIM}; font-style: italic;")
        self._vbox.addWidget(ph)

    def _load_palette_entry(self, var_name: str):
        """Render a color picker + affected-widgets list for a global palette variable."""
        if var_name not in PALETTE_DEFS:
            return
        self._current = _PALETTE_PREFIX + var_name
        self._clear()

        pdef = PALETTE_DEFS[var_name]

        title = QLabel(pdef['label'])
        title.setStyleSheet(
            f"font-weight: bold; color: {theme.ACCENT_PRIMARY}; padding: 0 0 4px 0;"
        )
        self._vbox.addWidget(title)

        usage = QLabel(pdef['usage'])
        usage.setWordWrap(True)
        usage.setStyleSheet(
            f"color: {theme.FG_DIM}; font-style: italic; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; padding: 0 0 8px 0;"
        )
        self._vbox.addWidget(usage)

        # Color picker row
        cur_hex = getattr(theme, var_name, '#888888')
        row = QWidget()
        row.setFixedHeight(_ROW_H)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        lbl = QLabel("Color")
        lbl.setFixedWidth(_LBL_W)
        lbl.setStyleSheet(f"color: {theme.FG_PRIMARY}; background: transparent;")
        h.addWidget(lbl)

        editor = self._make_palette_color_editor(var_name, cur_hex)
        editor.setFixedHeight(_ROW_H - 4)
        editor.setFixedWidth(_SWATCH_W + 6 + _HEX_W)
        h.addWidget(editor)
        h.addStretch(1)
        self._vbox.addWidget(row)

        # ── Affected widget properties ─────────────────────────────────────
        usage_map = _build_palette_usage()
        affected = usage_map.get(var_name, [])
        if affected:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"color: {theme.BG_LIGHT};")
            sep.setFixedHeight(1)
            self._vbox.addWidget(sep)

            hdr = QLabel("AFFECTS THESE WIDGET PROPERTIES")
            hdr.setStyleSheet(
                f"color: {theme.ACCENT_SECONDARY}; font-weight: bold; letter-spacing: 1px; "
                f"font-size: {theme.FONT_SIZE_SMALL}px; padding: 6px 0 4px 0;"
            )
            self._vbox.addWidget(hdr)

            hint = QLabel("Click any entry to open it in the Widget Editor →")
            hint.setStyleSheet(
                f"color: {theme.FG_DIM}; font-style: italic; font-size: {theme.FONT_SIZE_SMALL}px; padding: 0 0 4px 0;"
            )
            self._vbox.addWidget(hint)

            for wname, icon, prop_label, state in sorted(affected, key=lambda x: x[0]):
                state_txt = f"  {state}" if state else ""
                btn = QPushButton(f"{icon}  ›  {prop_label}{state_txt}")
                btn.setStyleSheet(
                    f"QPushButton {{ text-align: left; background: {theme.BG_MEDIUM}; "
                    f"color: {theme.FG_PRIMARY}; border: 1px solid {theme.BG_LIGHT}; "
                    f"border-radius: 3px; padding: 3px 8px; "
                    f"font-size: {theme.FONT_SIZE_SMALL}px; }}"
                    f"QPushButton:hover {{ background: {theme.ACCENT_PRIMARY}; color: {theme.BG_DARK}; }}"
                )
                btn.clicked.connect(lambda _c, n=wname: self.navigate_to_widget.emit(n))
                self._vbox.addWidget(btn)

        self._vbox.addStretch()

    def _load_typo_entry(self, var_name: str):
        """Render a font-family combo or px spinbox for a typography variable."""
        if var_name not in TYPO_DEFS:
            return
        self._current = _TYPO_PREFIX + var_name
        self._clear()

        tdef = TYPO_DEFS[var_name]

        title = QLabel(tdef['label'])
        title.setStyleSheet(
            f"font-weight: bold; color: {theme.ACCENT_PRIMARY}; padding: 0 0 4px 0;"
        )
        self._vbox.addWidget(title)

        desc = QLabel(tdef['usage'])
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {theme.FG_DIM}; font-style: italic; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; padding: 0 0 10px 0;"
        )
        self._vbox.addWidget(desc)

        row = QWidget()
        row.setFixedHeight(_ROW_H)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        lbl = QLabel("Value")
        lbl.setFixedWidth(_LBL_W)
        lbl.setStyleSheet(f"color: {theme.FG_PRIMARY}; background: transparent;")
        h.addWidget(lbl)

        typ = tdef['type']
        if typ in ('font_ui', 'font_mono'):
            from PyQt6.QtWidgets import QComboBox as _QCB
            combo = _QCB()
            combo.addItems(tdef['choices'])
            combo.setStyleSheet("combobox-popup: 0;")
            # current value: FONT_FAMILY_UI for font_ui, FONT_MONOSPACE for font_mono
            cur_val = getattr(theme, var_name, tdef['choices'][0])
            idx = combo.findText(cur_val)
            if idx >= 0:
                combo.setCurrentIndex(idx)
            combo.currentTextChanged.connect(
                lambda val, vn=var_name: self.typo_changed.emit(vn, val)
            )
            h.addWidget(combo)
        else:  # 'px'
            spin = IntLineEdit(tdef['lo'], tdef['hi'], getattr(theme, var_name, tdef['default']))
            spin.setFixedWidth(_SPIN_W)
            spin.setFixedHeight(_ROW_H - 6)
            spin.valueChanged.connect(
                lambda val, vn=var_name: self.typo_changed.emit(vn, val)
            )
            h.addWidget(spin)

        h.addStretch(1)
        self._vbox.addWidget(row)
        self._vbox.addStretch()

    def _load_spacing_entry(self, var_name: str):
        """Render a px spinbox for a spacing/layout variable."""
        if var_name not in SPACING_DEFS:
            return
        self._current = _SPACING_PREFIX + var_name
        self._clear()

        sdef = SPACING_DEFS[var_name]

        title = QLabel(sdef['label'])
        title.setStyleSheet(
            f"font-weight: bold; color: {theme.ACCENT_PRIMARY}; padding: 0 0 4px 0;"
        )
        self._vbox.addWidget(title)

        desc = QLabel(sdef['usage'])
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"color: {theme.FG_DIM}; font-style: italic; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; padding: 0 0 10px 0;"
        )
        self._vbox.addWidget(desc)

        row = QWidget()
        row.setFixedHeight(_ROW_H)
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        lbl = QLabel("Value (px)")
        lbl.setFixedWidth(_LBL_W)
        lbl.setStyleSheet(f"color: {theme.FG_PRIMARY}; background: transparent;")
        h.addWidget(lbl)

        spin = IntLineEdit(sdef['lo'], sdef['hi'], getattr(theme, var_name, sdef['default']))
        spin.setFixedWidth(_SPIN_W)
        spin.setFixedHeight(_ROW_H - 6)
        spin.valueChanged.connect(
            lambda val, vn=var_name: self.typo_changed.emit(vn, val)
        )
        h.addWidget(spin)
        h.addStretch(1)
        self._vbox.addWidget(row)
        self._vbox.addStretch()

    def _make_palette_color_editor(self, var_name: str, cur_hex: str) -> QWidget:
        """Color swatch + hex field that updates theme.VAR_NAME directly."""
        container = QWidget()
        container.setFixedHeight(_ROW_H - 4)
        h = QHBoxLayout(container)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(6)
        h.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        swatch = ColorSwatch(cur_hex)
        hex_edit = QLineEdit(cur_hex)
        hex_edit.setFixedWidth(_HEX_W)
        hex_edit.setFixedHeight(_ROW_H - 6)
        hex_edit.setStyleSheet(
            f"QLineEdit {{ font-family: {theme.FONT_MONOSPACE}; font-size: {theme.FONT_SIZE_SMALL}px; "
            f"background: {theme.BG_DARK}; color: {theme.FG_PRIMARY}; "
            f"border: 1px solid {theme.BG_LIGHT}; border-radius: 3px; padding: 0 4px; }}"
        )

        def _emit(hex_val: str):
            self.palette_changed.emit(var_name, hex_val)

        def _pick():
            from PyQt6.QtWidgets import QColorDialog
            c = QColorDialog.getColor(QColor(hex_edit.text()), container, f"Pick — {var_name}")
            if c.isValid():
                hex_edit.blockSignals(True)
                hex_edit.setText(c.name())
                hex_edit.blockSignals(False)
                swatch.set_color(c.name())
                _emit(c.name())

        def _hex_typed(text: str):
            if len(text) == 7 and text.startswith('#'):
                try:
                    QColor(text)
                    swatch.set_color(text)
                    _emit(text)
                except Exception:
                    pass

        swatch.clicked.connect(_pick)
        hex_edit.textChanged.connect(_hex_typed)
        h.addWidget(swatch)
        h.addWidget(hex_edit)
        return container

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
        self._prop_panel.palette_changed.connect(self._on_palette_changed)
        self._prop_panel.typo_changed.connect(self._on_typo_changed)

        # Wire: "Affected in:" buttons in palette panel → navigate to that widget
        self._prop_panel.navigate_to_widget.connect(self._navigate_to_widget)

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

    def _navigate_to_widget(self, wname: str):
        """Navigate left panel to wname and load its properties."""
        self._preview_panel._select(wname)
        self._prop_panel.load_widget(wname)

    def _on_property_changed(self, wn: str, state: str, qss_key: str, value):
        if self._on_change:
            self._on_change()

    def _on_typo_changed(self, var_name: str, value):
        """User changed a typography or spacing value — apply live."""
        setattr(theme, var_name, value)
        if var_name == 'FONT_FAMILY_UI':
            theme.FONT_FAMILY = f"'{value}', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
            app = QApplication.instance()
            if app:
                from PyQt6.QtGui import QFont
                app.setFont(QFont(value, theme.FONT_SIZE_NORMAL))
        elif var_name == 'FONT_MONOSPACE':
            theme.FONT_FAMILY_MONO = f"'{value}', 'Courier New', monospace"
        if self._on_change:
            self._on_change()

    def reset_typo_spacing(self):
        """Reset all typography and spacing variables to their built-in defaults."""
        defaults = {
            'FONT_SIZE_NORMAL': 14, 'FONT_SIZE_LARGE': 16, 'FONT_SIZE_SMALL': 12,
            'FONT_SIZE_TINY': 11, 'FONT_SIZE_TAB': 13,
            'BORDER_RADIUS': 4, 'MARGIN_SM': 3, 'MARGIN_MD': 6,
            'MARGIN_LG': 10, 'PADDING_SM': 4, 'PADDING_MD': 8,
        }
        for var_name, val in defaults.items():
            setattr(theme, var_name, val)
        theme.FONT_FAMILY_UI = 'Segoe UI'
        theme.FONT_FAMILY = "'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
        theme.FONT_MONOSPACE = 'Consolas'
        theme.FONT_FAMILY_MONO = "'Consolas', 'Courier New', monospace"
        # Refresh property panel if currently showing a typo/spacing entry
        cur = self._prop_panel._current
        if cur and (cur.startswith(_TYPO_PREFIX) or cur.startswith(_SPACING_PREFIX)):
            self._prop_panel.load_widget(cur)
        if self._on_change:
            self._on_change()

    def _on_palette_changed(self, var_name: str, new_hex: str):
        """User edited a palette color — update theme globals and refresh the app."""
        setattr(theme, var_name, new_hex)
        # BG_MEDIUM and BG_LIGHT are derived from BG_DARK
        if var_name == 'BG_DARK':
            if theme.is_light_color(new_hex):
                theme.BG_MEDIUM = theme.darken_color(new_hex, 0.08)
                theme.BG_LIGHT  = theme.darken_color(new_hex, 0.17)
            else:
                theme.BG_MEDIUM = theme.lighten_color(new_hex, 0.1)
                theme.BG_LIGHT  = theme.lighten_color(new_hex, 0.2)
        # Rebuild widget defaults so they reflect the updated palette
        new_defs = _make_defs()
        WIDGET_DEFS.clear()
        WIDGET_DEFS.update(new_defs)
        # Push the new app stylesheet
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
