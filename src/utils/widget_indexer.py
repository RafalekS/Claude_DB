"""
Widget Indexer
==============
Scans all Python source files and builds:
  1. Full index  (config/widget_index.json)  — every class that mentions the widget
  2. Visible UI index (config/widget_visible_index.json) — only navigable UI
     locations (Tab, SubTab, Dialog) found in the tabs/ directory, using smarter
     detection patterns for implicitly-used widgets.

Run as a script to regenerate both files:
    python src/utils/widget_indexer.py
"""

from __future__ import annotations

import json
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Canonical PyQt6 widget types we care about ────────────────────────────────
INDEXED_WIDGETS: list[str] = [
    "QPushButton",
    "QLabel",
    "QLineEdit",
    "QTextEdit",
    "QTextBrowser",
    "QComboBox",
    "QCheckBox",
    "QRadioButton",
    "QListWidget",
    "QTableWidget",
    "QTreeWidget",
    "QGroupBox",
    "QSpinBox",
    "QTabWidget",
    "QTabBar",
    "QSplitter",
    "QScrollArea",
    "QScrollBar",
    "QProgressBar",
    "QSlider",
    "QFrame",
    "QDialog",
    "QStatusBar",
    "QToolTip",
]

# Where we write the cached indexes
_INDEX_PATH         = Path(__file__).parent.parent.parent / "config" / "widget_index.json"
_VISIBLE_INDEX_PATH = Path(__file__).parent.parent.parent / "config" / "widget_visible_index.json"

# Directories to scan for the FULL index
_SCAN_DIRS = [
    Path(__file__).parent.parent / "tabs",
    Path(__file__).parent.parent / "utils",
    Path(__file__).parent.parent,  # src/ root (main.py etc.)
]

# Only the tabs/ directory is used for the VISIBLE UI index
_TABS_DIR = Path(__file__).parent.parent / "tabs"

# Class name suffixes that indicate a user-visible, navigable UI component
_NAVIGABLE_SUFFIXES = ("Tab", "SubTab", "Subtab", "Dialog", "Window")

# ── Detection overrides for implicitly-used widgets ───────────────────────────
# Some widgets are used without being named directly:
#   QToolTip  → used via .setToolTip()
#   QScrollBar → auto-created inside QScrollArea
#   QTabBar    → auto-created inside QTabWidget
#
# For these we match a broader pattern so they actually show up.
_DETECTION_OVERRIDES: dict[str, str] = {
    "QToolTip":   r"\.setToolTip\s*\(",
    "QScrollBar": r"\b(QScrollArea|QScrollBar)\b",
    "QTabBar":    r"\b(QTabWidget|QTabBar)\b",
}


# ── Full widget index ─────────────────────────────────────────────────────────

def build_widget_index(src_dir: Path | None = None) -> dict[str, list[str]]:
    """Scan Python files and return {WidgetType: sorted unique list of class names}.

    Each class name is the first class defined in the file that imports/uses the
    widget type — good enough for "used in X" display purposes.
    """
    index: dict[str, set[str]] = {w: set() for w in INDEXED_WIDGETS}

    scan_roots: list[Path] = [src_dir] if src_dir else _SCAN_DIRS

    for root in scan_roots:
        if not root.exists():
            continue
        for py_file in sorted(root.rglob("*.py")):
            if "__pycache__" in py_file.parts:
                continue
            try:
                source = py_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            class_names = re.findall(r"^class\s+([A-Za-z_]\w*)", source, re.MULTILINE)
            if not class_names:
                class_names = [py_file.stem]

            for widget in INDEXED_WIDGETS:
                if re.search(r"\b" + re.escape(widget) + r"\b", source):
                    for cn in class_names:
                        index[widget].add(cn)

    return {w: sorted(v) for w, v in index.items()}


def save_widget_index(index: dict[str, list[str]]) -> None:
    """Persist the full index to config/widget_index.json."""
    _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    logger.info("Widget index saved to %s", _INDEX_PATH)


def load_widget_index() -> dict[str, list[str]]:
    """Load cached full index; rebuild if missing or empty."""
    if _INDEX_PATH.exists():
        try:
            data = json.loads(_INDEX_PATH.read_text(encoding="utf-8"))
            if data:
                return data
        except Exception:
            pass
    index = build_widget_index()
    save_widget_index(index)
    return index


# ── Visible UI index ──────────────────────────────────────────────────────────

def build_visible_ui_index() -> dict[str, list[str]]:
    """Scan only the tabs/ directory and return only *navigable* UI class names.

    Navigable = ends with Tab, SubTab, Dialog, or Window.
    Uses detection overrides for widgets that are used implicitly
    (QToolTip via setToolTip, QScrollBar via QScrollArea, QTabBar via QTabWidget).
    """
    index: dict[str, set[str]] = {w: set() for w in INDEXED_WIDGETS}

    if not _TABS_DIR.exists():
        return {w: [] for w in INDEXED_WIDGETS}

    for py_file in sorted(_TABS_DIR.glob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # Only keep class names that represent navigable UI locations
        all_classes = re.findall(r"^class\s+([A-Za-z_]\w*)", source, re.MULTILINE)
        nav_classes = [
            c for c in all_classes
            if any(c.endswith(s) for s in _NAVIGABLE_SUFFIXES)
        ]
        if not nav_classes:
            continue

        for widget in INDEXED_WIDGETS:
            pattern = _DETECTION_OVERRIDES.get(
                widget, r"\b" + re.escape(widget) + r"\b"
            )
            if re.search(pattern, source):
                for cn in nav_classes:
                    index[widget].add(cn)

    return {w: sorted(v) for w, v in index.items()}


def save_visible_ui_index(index: dict[str, list[str]]) -> None:
    """Persist the visible UI index to config/widget_visible_index.json."""
    _VISIBLE_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_VISIBLE_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    logger.info("Visible UI index saved to %s", _VISIBLE_INDEX_PATH)


def load_visible_ui_index() -> dict[str, list[str]]:
    """Load cached visible UI index; rebuild if missing or empty."""
    if _VISIBLE_INDEX_PATH.exists():
        try:
            data = json.loads(_VISIBLE_INDEX_PATH.read_text(encoding="utf-8"))
            if data:
                return data
        except Exception:
            pass
    index = build_visible_ui_index()
    save_visible_ui_index(index)
    return index


# ── Human-readable "used in" label ───────────────────────────────────────────

def used_in_label(widget_type: str, index: dict[str, list[str]]) -> str:
    """Return a compact comma-separated list of class names for the tooltip."""
    classes = index.get(widget_type, [])
    if not classes:
        return "not used"
    _SKIP = {"QApplication", "ClaudeDBApp"}
    filtered = [c for c in classes if c not in _SKIP]
    if not filtered:
        return "not used"
    return ", ".join(filtered)


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Scanning source files (full index)…")
    idx = build_widget_index()
    save_widget_index(idx)
    print(f"Full index → {_INDEX_PATH}")

    print("Scanning tabs/ (visible UI index)…")
    vis = build_visible_ui_index()
    save_visible_ui_index(vis)
    print(f"Visible index → {_VISIBLE_INDEX_PATH}")

    print()
    for widget in INDEXED_WIDGETS:
        full_n = len(idx.get(widget, []))
        vis_locs = vis.get(widget, [])
        vis_n = len(vis_locs)
        print(f"  {widget:20s}  full={full_n:3d}  visible={vis_n:2d} — "
              f"{', '.join(vis_locs[:4])}{'…' if vis_n > 4 else ''}")
