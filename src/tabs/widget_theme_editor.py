"""
Widget Theme Editor
===================
Right panel : real Qt widgets – click any to select it.
Left panel  : full property editor for the selected widget type
              (all CSS-like properties: color, radius, padding, font, hover, pressed …).

All changes apply LIVE to the running app via the global QSS override.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QCheckBox, QScrollArea, QFrame, QLineEdit, QTextEdit,
    QComboBox, QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem,
    QGroupBox, QProgressBar, QSlider, QTabWidget, QRadioButton,
    QSplitter, QHeaderView, QSizePolicy, QApplication, QStackedWidget
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QSize
from PyQt6.QtGui import QColor, QFont
from utils import theme

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
    return {
        'Button': {
            'selector': 'QPushButton',
            'icon': '⬜ Button',
            'props': [
                {'section': 'Normal'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': '', 'val': _c('ACCENT_PRIMARY')},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('BG_DARK')},
                {'label': 'Border Radius', 'qss': 'border-radius',    'type': PX,    'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding V',     'qss': 'padding-top',      'type': PX,    'state': '', 'val': 4},
                {'label': 'Padding H',     'qss': 'padding-left',     'type': PX,    'state': '', 'val': 10},
                {'label': 'Font Size',     'qss': 'font-size',        'type': PX,    'state': '', 'val': _n('FONT_SIZE_NORMAL')},
                {'label': 'Bold',          'qss': 'font-weight',      'type': BOOL,  'state': '', 'val': True},
                {'section': 'Hover'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': ':hover', 'val': _c('ACCENT_SECONDARY')},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': ':hover', 'val': _c('BG_DARK')},
                {'section': 'Pressed'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': ':pressed', 'val': _c('BG_LIGHT')},
                {'section': 'Disabled'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': ':disabled', 'val': _c('BG_MEDIUM')},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': ':disabled', 'val': _c('FG_DIM')},
            ],
        },
        'Label': {
            'selector': 'QLabel',
            'icon': '🔤 Label',
            'props': [
                {'section': 'Normal'},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('FG_PRIMARY')},
                {'label': 'Font Size',     'qss': 'font-size',        'type': PX,    'state': '', 'val': _n('FONT_SIZE_NORMAL')},
                {'label': 'Bold',          'qss': 'font-weight',      'type': BOOL,  'state': '', 'val': False},
                {'label': 'Padding',       'qss': 'padding',          'type': PX,    'state': '', 'val': 0},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': '', 'val': 'transparent'},
            ],
        },
        'Input': {
            'selector': 'QLineEdit',
            'icon': '📝 Input',
            'props': [
                {'section': 'Normal'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': '', 'val': _c('BG_DARK')},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('FG_PRIMARY')},
                {'label': 'Border Color',  'qss': 'border-color',     'type': COLOR, 'state': '', 'val': _c('BG_LIGHT')},
                {'label': 'Border Width',  'qss': 'border-width',     'type': PX,    'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius',    'type': PX,    'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding',       'qss': 'padding',          'type': PX,    'state': '', 'val': 4},
                {'label': 'Font Size',     'qss': 'font-size',        'type': PX,    'state': '', 'val': _n('FONT_SIZE_NORMAL')},
                {'section': 'Focus'},
                {'label': 'Border Color',  'qss': 'border-color',     'type': COLOR, 'state': ':focus', 'val': _c('ACCENT_PRIMARY')},
            ],
        },
        'TextEdit': {
            'selector': 'QTextEdit',
            'icon': '📄 Text Area',
            'props': [
                {'section': 'Normal'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': '', 'val': _c('BG_DARK')},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('FG_PRIMARY')},
                {'label': 'Border Color',  'qss': 'border-color',     'type': COLOR, 'state': '', 'val': _c('BG_LIGHT')},
                {'label': 'Border Width',  'qss': 'border-width',     'type': PX,    'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius',    'type': PX,    'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding',       'qss': 'padding',          'type': PX,    'state': '', 'val': 4},
                {'label': 'Font Size',     'qss': 'font-size',        'type': PX,    'state': '', 'val': _n('FONT_SIZE_SMALL')},
            ],
        },
        'ComboBox': {
            'selector': 'QComboBox',
            'icon': '▼ ComboBox',
            'props': [
                {'section': 'Normal'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': '', 'val': _c('BG_DARK')},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('FG_PRIMARY')},
                {'label': 'Border Color',  'qss': 'border-color',     'type': COLOR, 'state': '', 'val': _c('BG_LIGHT')},
                {'label': 'Border Width',  'qss': 'border-width',     'type': PX,    'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius',    'type': PX,    'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding',       'qss': 'padding',          'type': PX,    'state': '', 'val': 4},
                {'section': 'Hover'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': ':hover', 'val': _c('BG_MEDIUM')},
                {'section': 'Dropdown'},
                {'label': 'Drop BG',       'qss': 'background-color', 'type': COLOR, 'state': ' QAbstractItemView', 'val': _c('BG_DARK')},
                {'label': 'Drop Text',     'qss': 'color',            'type': COLOR, 'state': ' QAbstractItemView', 'val': _c('FG_PRIMARY')},
            ],
        },
        'CheckBox': {
            'selector': 'QCheckBox',
            'icon': '☑ CheckBox',
            'props': [
                {'section': 'Normal'},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('FG_PRIMARY')},
                {'label': 'Font Size',     'qss': 'font-size',        'type': PX,    'state': '', 'val': _n('FONT_SIZE_NORMAL')},
                {'label': 'Spacing',       'qss': 'spacing',          'type': PX,    'state': '', 'val': 6},
                {'section': 'Checked Indicator'},
                {'label': 'Indicator BG',  'qss': 'background-color', 'type': COLOR, 'state': '::indicator:checked', 'val': _c('ACCENT_PRIMARY')},
                {'label': 'Indicator Size','qss': 'width',            'type': PX,    'state': '::indicator', 'val': 14},
            ],
        },
        'RadioButton': {
            'selector': 'QRadioButton',
            'icon': '○ RadioButton',
            'props': [
                {'section': 'Normal'},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('FG_PRIMARY')},
                {'label': 'Font Size',     'qss': 'font-size',        'type': PX,    'state': '', 'val': _n('FONT_SIZE_NORMAL')},
                {'section': 'Checked Indicator'},
                {'label': 'Indicator BG',  'qss': 'background-color', 'type': COLOR, 'state': '::indicator:checked', 'val': _c('ACCENT_PRIMARY')},
                {'label': 'Indicator Size','qss': 'width',            'type': PX,    'state': '::indicator', 'val': 14},
            ],
        },
        'Table': {
            'selector': 'QTableWidget',
            'icon': '⊞ Table',
            'props': [
                {'section': 'Table'},
                {'label': 'Background',    'qss': 'background-color',          'type': COLOR, 'state': '', 'val': _c('BG_DARK')},
                {'label': 'Alt Row Color', 'qss': 'alternate-background-color','type': COLOR, 'state': '', 'val': _c('BG_MEDIUM')},
                {'label': 'Grid Color',    'qss': 'gridline-color',            'type': COLOR, 'state': '', 'val': _c('BG_LIGHT')},
                {'label': 'Font Size',     'qss': 'font-size',                 'type': PX,    'state': '', 'val': _n('FONT_SIZE_SMALL')},
                {'section': 'Header'},
                {'label': 'Header BG',     'qss': 'background-color',          'type': COLOR, 'state': '::section', 'val': _c('BG_MEDIUM')},
                {'label': 'Header Text',   'qss': 'color',                     'type': COLOR, 'state': '::section', 'val': _c('FG_PRIMARY')},
                {'section': 'Selection'},
                {'label': 'Selected BG',   'qss': 'background-color',          'type': COLOR, 'state': '::item:selected', 'val': _c('ACCENT_PRIMARY')},
                {'label': 'Selected Text', 'qss': 'color',                     'type': COLOR, 'state': '::item:selected', 'val': _c('BG_DARK')},
            ],
        },
        'List': {
            'selector': 'QListWidget',
            'icon': '≡ List',
            'props': [
                {'section': 'List'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': '', 'val': _c('BG_DARK')},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('FG_PRIMARY')},
                {'label': 'Font Size',     'qss': 'font-size',        'type': PX,    'state': '', 'val': _n('FONT_SIZE_SMALL')},
                {'section': 'Item Hover'},
                {'label': 'Hover BG',      'qss': 'background-color', 'type': COLOR, 'state': '::item:hover', 'val': _c('BG_MEDIUM')},
                {'label': 'Hover Text',    'qss': 'color',            'type': COLOR, 'state': '::item:hover', 'val': _c('FG_PRIMARY')},
                {'section': 'Selected Item'},
                {'label': 'Selected BG',   'qss': 'background-color', 'type': COLOR, 'state': '::item:selected', 'val': _c('ACCENT_PRIMARY')},
                {'label': 'Selected Text', 'qss': 'color',            'type': COLOR, 'state': '::item:selected', 'val': _c('BG_DARK')},
            ],
        },
        'GroupBox': {
            'selector': 'QGroupBox',
            'icon': '▣ GroupBox',
            'props': [
                {'section': 'Normal'},
                {'label': 'Title Color',   'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('ACCENT_PRIMARY')},
                {'label': 'Border Color',  'qss': 'border-color',     'type': COLOR, 'state': '', 'val': _c('BG_LIGHT')},
                {'label': 'Border Width',  'qss': 'border-width',     'type': PX,    'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius',    'type': PX,    'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding Top',   'qss': 'padding-top',      'type': PX,    'state': '', 'val': 14},
                {'label': 'Font Bold',     'qss': 'font-weight',      'type': BOOL,  'state': '', 'val': True},
            ],
        },
        'ProgressBar': {
            'selector': 'QProgressBar',
            'icon': '░ ProgressBar',
            'props': [
                {'section': 'Track'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': '', 'val': _c('BG_MEDIUM')},
                {'label': 'Border Radius', 'qss': 'border-radius',    'type': PX,    'state': '', 'val': 4},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('FG_PRIMARY')},
                {'label': 'Max Height',    'qss': 'max-height',       'type': PX,    'state': '', 'val': 12},
                {'section': 'Fill (::chunk)'},
                {'label': 'Fill Color',    'qss': 'background-color', 'type': COLOR, 'state': '::chunk', 'val': _c('ACCENT_PRIMARY')},
                {'label': 'Fill Radius',   'qss': 'border-radius',    'type': PX,    'state': '::chunk', 'val': 4},
            ],
        },
        'Slider': {
            'selector': 'QSlider',
            'icon': '▬ Slider',
            'props': [
                {'section': 'Handle'},
                {'label': 'Handle Color',  'qss': 'background-color', 'type': COLOR, 'state': '::handle:horizontal', 'val': _c('ACCENT_PRIMARY')},
                {'label': 'Handle Width',  'qss': 'width',            'type': PX,    'state': '::handle:horizontal', 'val': 14},
                {'label': 'Handle Height', 'qss': 'height',           'type': PX,    'state': '::handle:horizontal', 'val': 14},
                {'label': 'Handle Radius', 'qss': 'border-radius',    'type': PX,    'state': '::handle:horizontal', 'val': 7},
                {'section': 'Groove'},
                {'label': 'Groove Color',  'qss': 'background-color', 'type': COLOR, 'state': '::groove:horizontal', 'val': _c('BG_MEDIUM')},
                {'label': 'Groove Height', 'qss': 'height',           'type': PX,    'state': '::groove:horizontal', 'val': 6},
                {'label': 'Groove Radius', 'qss': 'border-radius',    'type': PX,    'state': '::groove:horizontal', 'val': 3},
            ],
        },
        'SpinBox': {
            'selector': 'QSpinBox',
            'icon': '123 SpinBox',
            'props': [
                {'section': 'Normal'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': '', 'val': _c('BG_DARK')},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('FG_PRIMARY')},
                {'label': 'Border Color',  'qss': 'border-color',     'type': COLOR, 'state': '', 'val': _c('BG_LIGHT')},
                {'label': 'Border Width',  'qss': 'border-width',     'type': PX,    'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius',    'type': PX,    'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding',       'qss': 'padding',          'type': PX,    'state': '', 'val': 3},
                {'section': 'Focus'},
                {'label': 'Border Color',  'qss': 'border-color',     'type': COLOR, 'state': ':focus', 'val': _c('ACCENT_PRIMARY')},
            ],
        },
        'Tabs': {
            'selector': 'QTabBar::tab',
            'icon': '🗂 Tabs',
            'props': [
                {'section': 'Normal Tab'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': '', 'val': _c('BG_MEDIUM')},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('FG_SECONDARY')},
                {'label': 'Padding',       'qss': 'padding',          'type': PX,    'state': '', 'val': 6},
                {'label': 'Border Radius', 'qss': 'border-radius',    'type': PX,    'state': '', 'val': 4},
                {'label': 'Font Size',     'qss': 'font-size',        'type': PX,    'state': '', 'val': _n('FONT_SIZE_TAB', 11)},
                {'section': 'Selected'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': ':selected', 'val': _c('BG_DARK')},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': ':selected', 'val': _c('FG_PRIMARY')},
                {'section': 'Hover'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': ':hover', 'val': _c('BG_LIGHT')},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': ':hover', 'val': _c('FG_PRIMARY')},
            ],
        },
        'Divider': {
            'selector': 'QFrame[frameShape="4"]',
            'icon': '─── Divider',
            'props': [
                {'section': 'Line'},
                {'label': 'Color',         'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('BG_LIGHT')},
                {'label': 'Max Height',    'qss': 'max-height',       'type': PX,    'state': '', 'val': 1},
            ],
        },
        'ScrollBar': {
            'selector': 'QScrollBar',
            'icon': '│ ScrollBar',
            'props': [
                {'section': 'Track'},
                {'label': 'Track Color',   'qss': 'background-color', 'type': COLOR, 'state': '', 'val': _c('BG_DARK')},
                {'label': 'Width',         'qss': 'width',            'type': PX,    'state': ':vertical', 'val': 8},
                {'label': 'Height',        'qss': 'height',           'type': PX,    'state': ':horizontal', 'val': 8},
                {'section': 'Handle'},
                {'label': 'Handle Color',  'qss': 'background-color', 'type': COLOR, 'state': '::handle:vertical', 'val': _c('BG_LIGHT')},
                {'label': 'Handle Radius', 'qss': 'border-radius',    'type': PX,    'state': '::handle:vertical', 'val': 4},
                {'label': 'Min Length',    'qss': 'min-height',       'type': PX,    'state': '::handle:vertical', 'val': 20},
                {'section': 'Handle Hover'},
                {'label': 'Hover Color',   'qss': 'background-color', 'type': COLOR, 'state': '::handle:vertical:hover', 'val': _c('ACCENT_PRIMARY')},
            ],
        },
        'ToolTip': {
            'selector': 'QToolTip',
            'icon': '💬 ToolTip',
            'props': [
                {'section': 'Normal'},
                {'label': 'Background',    'qss': 'background-color', 'type': COLOR, 'state': '', 'val': _c('BG_MEDIUM')},
                {'label': 'Text Color',    'qss': 'color',            'type': COLOR, 'state': '', 'val': _c('FG_PRIMARY')},
                {'label': 'Border Color',  'qss': 'border-color',     'type': COLOR, 'state': '', 'val': _c('BG_LIGHT')},
                {'label': 'Border Width',  'qss': 'border-width',     'type': PX,    'state': '', 'val': 1},
                {'label': 'Border Radius', 'qss': 'border-radius',    'type': PX,    'state': '', 'val': _n('BORDER_RADIUS')},
                {'label': 'Padding',       'qss': 'padding',          'type': PX,    'state': '', 'val': 4},
                {'label': 'Font Size',     'qss': 'font-size',        'type': PX,    'state': '', 'val': _n('FONT_SIZE_SMALL')},
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


# ── ClickableSection ──────────────────────────────────────────────────────────

class ClickableSection(QFrame):
    """A row in the preview panel.  Click anywhere (including child widgets)
    to select this widget type."""

    selected = pyqtSignal(str)   # emits widget_name

    _NORMAL_STYLE = f"QFrame {{ background: {theme.BG_DARK}; border: 2px solid transparent; border-radius: 4px; }}"
    _ACTIVE_STYLE = f"QFrame {{ background: {theme.BG_MEDIUM}; border: 2px solid {theme.ACCENT_PRIMARY}; border-radius: 4px; }}"

    def __init__(self, widget_name: str, parent=None):
        super().__init__(parent)
        self._name = widget_name
        self._active = False
        self.setStyleSheet(self._NORMAL_STYLE)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_active(self, active: bool):
        self._active = active
        self.setStyleSheet(self._ACTIVE_STYLE if active else self._NORMAL_STYLE)

    def mousePressEvent(self, event):
        self.selected.emit(self._name)
        super().mousePressEvent(event)

    # Forward clicks from ALL descendant widgets
    def childEvent(self, event):
        if event.type() == event.Type.ChildAdded:
            obj = event.child()
            if isinstance(obj, QWidget):
                obj.installEventFilter(self)
        super().childEvent(event)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            self.selected.emit(self._name)
        return False   # let the original event still be processed


# ── WidgetPreviewPanel ────────────────────────────────────────────────────────

class WidgetPreviewPanel(QScrollArea):
    """Right panel — all widgets shown as real Qt instances; clicking any
    emits widget_selected(name)."""

    widget_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._sections: dict[str, ClickableSection] = {}

        content = QWidget()
        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        title = QLabel("Click any widget to edit its properties")
        title.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px; font-style: italic;")
        vbox.addWidget(title)

        for wname in WIDGET_DEFS:
            section = ClickableSection(wname)
            section.selected.connect(self._on_section_clicked)
            self._sections[wname] = section

            row = QHBoxLayout(section)
            row.setContentsMargins(8, 8, 8, 8)
            row.setSpacing(12)

            # Type label
            icon_lbl = QLabel(WIDGET_DEFS[wname]['icon'])
            icon_lbl.setFixedWidth(130)
            icon_lbl.setStyleSheet(f"color: {theme.FG_SECONDARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
            row.addWidget(icon_lbl)

            # Actual widget(s)
            preview_widget = self._make_preview(wname)
            row.addWidget(preview_widget, 1)

            vbox.addWidget(section)

        vbox.addStretch()
        self.setWidget(content)

    def _make_preview(self, name: str) -> QWidget:
        """Create a small live preview for the widget type."""
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(8)

        if name == 'Button':
            h.addWidget(QPushButton("Primary"))
            h.addWidget(QPushButton("Secondary"))
            d = QPushButton("Disabled")
            d.setDisabled(True)
            h.addWidget(d)

        elif name == 'Label':
            h.addWidget(QLabel("Normal text"))
            lbl2 = QLabel("Secondary")
            lbl2.setStyleSheet(f"color: {theme.FG_SECONDARY};")
            h.addWidget(lbl2)

        elif name == 'Input':
            le = QLineEdit()
            le.setPlaceholderText("Type here…")
            le.setFixedWidth(200)
            h.addWidget(le)

        elif name == 'TextEdit':
            te = QTextEdit()
            te.setPlainText("Sample text\nLine two")
            te.setFixedHeight(60)
            te.setFixedWidth(240)
            h.addWidget(te)

        elif name == 'ComboBox':
            cb = QComboBox()
            cb.addItems(["Option A", "Option B", "Option C"])
            cb.setFixedWidth(150)
            h.addWidget(cb)

        elif name == 'CheckBox':
            c1 = QCheckBox("Checked")
            c1.setChecked(True)
            h.addWidget(c1)
            h.addWidget(QCheckBox("Unchecked"))

        elif name == 'RadioButton':
            r1 = QRadioButton("Option A")
            r1.setChecked(True)
            h.addWidget(r1)
            h.addWidget(QRadioButton("Option B"))

        elif name == 'Table':
            t = QTableWidget(3, 3)
            t.setFixedHeight(90)
            t.setFixedWidth(280)
            t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            t.verticalHeader().setVisible(False)
            t.horizontalHeader().setVisible(True)
            t.setHorizontalHeaderLabels(["Name", "Value", "Type"])
            for r in range(3):
                for c in range(3):
                    t.setItem(r, c, QTableWidgetItem(f"R{r+1}C{c+1}"))
            h.addWidget(t)

        elif name == 'List':
            lw = QListWidget()
            lw.setFixedHeight(80)
            lw.setFixedWidth(160)
            for item in ("Item Alpha", "Item Beta", "Item Gamma"):
                lw.addItem(QListWidgetItem(item))
            h.addWidget(lw)

        elif name == 'GroupBox':
            gb = QGroupBox("Group Title")
            gb_inner = QHBoxLayout(gb)
            gb_inner.addWidget(QLabel("Content inside"))
            h.addWidget(gb)

        elif name == 'ProgressBar':
            pb = QProgressBar()
            pb.setValue(65)
            pb.setFixedWidth(200)
            h.addWidget(pb)
            pb2 = QProgressBar()
            pb2.setValue(30)
            pb2.setFixedWidth(120)
            h.addWidget(pb2)

        elif name == 'Slider':
            sl = QSlider(Qt.Orientation.Horizontal)
            sl.setValue(60)
            sl.setFixedWidth(200)
            h.addWidget(sl)

        elif name == 'SpinBox':
            sb = QSpinBox()
            sb.setValue(42)
            sb.setFixedWidth(90)
            h.addWidget(sb)
            sb2 = QSpinBox()
            sb2.setValue(7)
            sb2.setFixedWidth(90)
            h.addWidget(sb2)

        elif name == 'Tabs':
            tw = QTabWidget()
            tw.addTab(QLabel("Tab A content"), "Tab A")
            tw.addTab(QLabel("Tab B content"), "Tab B")
            tw.addTab(QLabel("Tab C content"), "Tab C")
            tw.setFixedHeight(80)
            tw.setFixedWidth(300)
            h.addWidget(tw)

        elif name == 'Divider':
            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFixedWidth(300)
            h.addWidget(line)

        elif name == 'ScrollBar':
            sa = QScrollArea()
            inner = QWidget()
            inner.setFixedHeight(400)
            sa.setWidget(inner)
            sa.setFixedHeight(60)
            sa.setFixedWidth(200)
            h.addWidget(sa)

        elif name == 'ToolTip':
            btn = QPushButton("Hover for tooltip")
            btn.setToolTip("This is how tooltips look")
            h.addWidget(btn)

        else:
            h.addWidget(QLabel(f"({name})"))

        h.addStretch()
        return w

    def _on_section_clicked(self, name: str):
        for n, sec in self._sections.items():
            sec.set_active(n == name)
        self.widget_selected.emit(name)


# ── WidgetPropertyPanel ───────────────────────────────────────────────────────

class WidgetPropertyPanel(QScrollArea):
    """Left panel — shows all editable properties for the selected widget type.
    Emits property_changed(widget_name, state, qss_key, value) on any edit."""

    property_changed = pyqtSignal(str, str, str, object)

    def __init__(self, overrides: dict, parent=None):
        super().__init__(parent)
        self._overrides = overrides
        self._current = None

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content = QWidget()
        self._vbox = QVBoxLayout(self._content)
        self._vbox.setContentsMargins(8, 8, 8, 8)
        self._vbox.setSpacing(4)

        self._placeholder = QLabel("← Click any widget on the right\nto edit its properties here")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(f"color: {theme.FG_DIM}; font-size: {theme.FONT_SIZE_NORMAL}px; font-style: italic;")
        self._vbox.addWidget(self._placeholder)
        self._vbox.addStretch()
        self.setWidget(self._content)

    def load_widget(self, widget_name: str):
        """Rebuild the property editor for the given widget type."""
        if widget_name not in WIDGET_DEFS:
            return
        self._current = widget_name
        self._clear()

        wdef = WIDGET_DEFS[widget_name]
        title = QLabel(wdef['icon'])
        title.setStyleSheet(
            f"font-size: {theme.FONT_SIZE_LARGE}px; font-weight: bold; "
            f"color: {theme.ACCENT_PRIMARY}; padding-bottom: 4px;"
        )
        self._vbox.addWidget(title)

        overrides_for = self._overrides.get(widget_name, {})

        for prop in wdef['props']:
            if 'section' in prop:
                self._add_section_header(prop['section'])
            else:
                self._add_prop_row(widget_name, prop, overrides_for)

        self._vbox.addStretch()

    def _clear(self):
        while self._vbox.count():
            item = self._vbox.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_section_header(self, title: str):
        lbl = QLabel(title)
        lbl.setStyleSheet(
            f"color: {theme.ACCENT_SECONDARY}; font-weight: bold; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; "
            f"border-bottom: 1px solid {theme.BG_LIGHT}; "
            f"padding: 4px 0 2px 0; margin-top: 6px;"
        )
        self._vbox.addWidget(lbl)

    def _add_prop_row(self, widget_name: str, prop: dict, overrides_for: dict):
        state = prop['state']
        qss_key = prop['qss']
        key = (state, qss_key)
        current_val = overrides_for.get(key, prop['val'])

        row = QHBoxLayout()
        row.setSpacing(6)

        lbl = QLabel(prop['label'])
        lbl.setFixedWidth(110)
        lbl.setStyleSheet(f"color: {theme.FG_PRIMARY}; font-size: {theme.FONT_SIZE_SMALL}px;")
        row.addWidget(lbl)

        prop_type = prop['type']

        if prop_type == COLOR:
            editor = self._make_color_editor(widget_name, state, qss_key, current_val)
        elif prop_type == PX:
            editor = self._make_px_editor(widget_name, state, qss_key, current_val)
        elif prop_type == BOOL:
            editor = self._make_bool_editor(widget_name, state, qss_key, current_val)
        else:
            editor = QLabel(f"({prop_type}?)")

        row.addWidget(editor, 1)

        # Reset-to-default button
        rst = QPushButton("↺")
        rst.setFixedSize(22, 22)
        rst.setToolTip("Reset to theme default")
        rst.setStyleSheet(
            f"QPushButton {{ background: {theme.BG_MEDIUM}; color: {theme.FG_SECONDARY}; "
            f"border: none; border-radius: 3px; font-size: 11px; }}"
            f"QPushButton:hover {{ background: {theme.BG_LIGHT}; }}"
        )
        rst.clicked.connect(lambda _, wn=widget_name, st=state, qk=qss_key, dv=prop['val']:
                            self._reset_prop(wn, st, qk, dv))
        row.addWidget(rst)

        self._vbox.addLayout(row)

    def _make_color_editor(self, wn, state, qss_key, current_val) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)

        swatch = QPushButton()
        swatch.setFixedSize(28, 22)
        hex_val = current_val if isinstance(current_val, str) and current_val.startswith('#') else '#888888'
        swatch.setStyleSheet(
            f"QPushButton {{ background-color: {hex_val}; border: 1px solid {theme.BG_LIGHT}; border-radius: 3px; }}"
        )
        swatch.setToolTip("Click to pick color")

        hex_edit = QLineEdit(current_val if isinstance(current_val, str) else '#888888')
        hex_edit.setFixedWidth(80)
        hex_edit.setStyleSheet(f"font-family: {theme.FONT_MONOSPACE}; font-size: {theme.FONT_SIZE_SMALL}px;")

        def _pick():
            from PyQt6.QtWidgets import QColorDialog
            c = QColorDialog.getColor(QColor(hex_edit.text()), w, f"Pick — {qss_key}")
            if c.isValid():
                hex_edit.setText(c.name())
                swatch.setStyleSheet(
                    f"QPushButton {{ background-color: {c.name()}; border: 1px solid {theme.BG_LIGHT}; border-radius: 3px; }}"
                )
                self._emit_change(wn, state, qss_key, c.name())

        def _hex_changed(text: str):
            if len(text) == 7 and text.startswith('#'):
                try:
                    QColor(text)
                    swatch.setStyleSheet(
                        f"QPushButton {{ background-color: {text}; border: 1px solid {theme.BG_LIGHT}; border-radius: 3px; }}"
                    )
                    self._emit_change(wn, state, qss_key, text)
                except Exception:
                    pass

        swatch.clicked.connect(_pick)
        hex_edit.textChanged.connect(_hex_changed)

        h.addWidget(swatch)
        h.addWidget(hex_edit)
        return w

    def _make_px_editor(self, wn, state, qss_key, current_val) -> QWidget:
        spin = QSpinBox()
        spin.setRange(0, 200)
        try:
            spin.setValue(int(current_val))
        except (TypeError, ValueError):
            spin.setValue(0)
        spin.setSuffix(" px")
        spin.setMaximumWidth(80)
        spin.valueChanged.connect(lambda v, _wn=wn, _st=state, _qk=qss_key:
                                  self._emit_change(_wn, _st, _qk, v))
        return spin

    def _make_bool_editor(self, wn, state, qss_key, current_val) -> QWidget:
        cb = QCheckBox()
        cb.setChecked(bool(current_val))
        cb.stateChanged.connect(lambda s, _wn=wn, _st=state, _qk=qss_key:
                                self._emit_change(_wn, _st, _qk, s == 2))
        return cb

    def _emit_change(self, wn: str, state: str, qss_key: str, value):
        key = (state, qss_key)
        self._overrides.setdefault(wn, {})[key] = value
        self.property_changed.emit(wn, state, qss_key, value)

    def _reset_prop(self, wn: str, state: str, qss_key: str, default_val):
        key = (state, qss_key)
        if wn in self._overrides and key in self._overrides[wn]:
            del self._overrides[wn][key]
        # Reload the panel to refresh displayed values
        if self._current == wn:
            self.load_widget(wn)
        self.property_changed.emit(wn, state, qss_key, default_val)


# ── WidgetThemeEditor (top-level widget) ──────────────────────────────────────

class WidgetThemeEditor(QSplitter):
    """The full interactive widget theme editor.

    Left  : property panel (shows props for the selected widget type)
    Right : preview panel (all real widgets, click to select)

    Usage:
        editor = WidgetThemeEditor()
        # call editor.get_overrides_qss() to get current QSS string
        # call editor.load_overrides(dict) to restore saved overrides
    """

    def __init__(self, on_change_callback=None, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        self._overrides: dict = {}
        self._on_change = on_change_callback   # called whenever any property changes

        self._prop_panel = WidgetPropertyPanel(self._overrides)
        self._prop_panel.setMinimumWidth(280)
        self._preview_panel = WidgetPreviewPanel()
        self._preview_panel.setMinimumWidth(400)

        self.addWidget(self._prop_panel)
        self.addWidget(self._preview_panel)
        self.setSizes([380, 700])

        self._preview_panel.widget_selected.connect(self._prop_panel.load_widget)
        self._prop_panel.property_changed.connect(self._on_property_changed)

    def _on_property_changed(self, wn: str, state: str, qss_key: str, value):
        if self._on_change:
            self._on_change()

    def get_overrides_qss(self) -> str:
        """Return the current per-widget overrides as a QSS string."""
        return build_overrides_qss(self._overrides)

    def get_overrides_dict(self) -> dict:
        """Return a JSON-serializable copy of the overrides."""
        result = {}
        for wname, state_map in self._overrides.items():
            result[wname] = {f"{st}|{qk}": v for (st, qk), v in state_map.items()}
        return result

    def load_overrides(self, data: dict):
        """Restore overrides from a JSON-serializable dict (as returned by get_overrides_dict)."""
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
