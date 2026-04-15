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
    QSpinBox, QCheckBox, QScrollArea, QFrame, QLineEdit,
    QSplitter, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
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


# ── WidgetPreviewPanel ────────────────────────────────────────────────────────

class WidgetPreviewPanel(QScrollArea):
    """Left panel — a clean scrollable list of widget-type buttons.
    Click one to load its properties in the right panel."""

    widget_selected = pyqtSignal(str)

    _BTN_H = 38

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMinimumWidth(180)
        self.setMaximumWidth(220)
        self._buttons: dict[str, QPushButton] = {}
        self._selected: str | None = None

        content = QWidget()
        vbox = QVBoxLayout(content)
        vbox.setContentsMargins(6, 8, 6, 8)
        vbox.setSpacing(3)

        title = QLabel("Select widget:")
        title.setStyleSheet(
            f"color: {theme.FG_DIM}; font-style: italic; padding-bottom: 4px;"
        )
        vbox.addWidget(title)

        for wname, wdef in WIDGET_DEFS.items():
            btn = QPushButton(wdef['icon'])
            btn.setCheckable(True)
            btn.setFixedHeight(self._BTN_H)
            btn.setStyleSheet(self._btn_style(False))
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

    def _select(self, name: str):
        for n, btn in self._buttons.items():
            active = (n == name)
            btn.setChecked(active)
            btn.setStyleSheet(self._btn_style(active))
        self._selected = name
        self.widget_selected.emit(name)


# ── WidgetPropertyPanel ───────────────────────────────────────────────────────

_ROW_H   = 30   # every editor row same height
_LBL_W   = 130  # label column width
_SWATCH_W = 40  # colour swatch width
_HEX_W   = 90   # hex input width
_SPIN_W  = 90   # spinbox width


class WidgetPropertyPanel(QScrollArea):
    """Right panel — all editable QSS properties for the selected widget type."""

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
        ph = QLabel("← Select a widget type\nto edit its properties")
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

        # Reset button
        rst = QPushButton("↺")
        rst.setFixedSize(22, 22)
        rst.setToolTip("Reset to default")
        rst.setStyleSheet(
            f"QPushButton {{ background: {theme.BG_MEDIUM}; color: {theme.FG_SECONDARY}; "
            f"border: 1px solid {theme.BG_LIGHT}; border-radius: 3px; font-size: 11px; padding: 0; }}"
            f"QPushButton:hover {{ background: {theme.BG_LIGHT}; color: {theme.FG_PRIMARY}; }}"
        )
        rst.clicked.connect(
            lambda _, wn=widget_name, st=state, qk=qss_key, dv=prop['val']:
            self._reset_prop(wn, st, qk, dv)
        )
        h.addWidget(rst)
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
        spin = QSpinBox()
        spin.setRange(0, 200)
        spin.setFixedWidth(_SPIN_W)
        spin.setFixedHeight(_ROW_H - 4)
        spin.setSuffix(" px")
        spin.setStyleSheet(
            f"QSpinBox {{ background: {theme.BG_DARK}; color: {theme.FG_PRIMARY}; "
            f"border: 1px solid {theme.BG_LIGHT}; border-radius: 3px; padding: 0 4px; "
            f"font-size: {theme.FONT_SIZE_SMALL}px; }}"
        )
        try:
            spin.setValue(int(cur_val))
        except (TypeError, ValueError):
            spin.setValue(0)
        spin.valueChanged.connect(
            lambda v, _wn=wn, _st=state, _qk=qss_key: self._emit_change(_wn, _st, _qk, v)
        )
        return spin

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

    def _reset_prop(self, wn: str, state: str, qss_key: str, default_val):
        key = (state, qss_key)
        if wn in self._overrides and key in self._overrides[wn]:
            del self._overrides[wn][key]
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

        self._preview_panel = WidgetPreviewPanel()
        self._prop_panel = WidgetPropertyPanel(self._overrides)
        self._prop_panel.setMinimumWidth(300)

        self.addWidget(self._preview_panel)
        self.addWidget(self._prop_panel)
        self.setSizes([200, 800])

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
