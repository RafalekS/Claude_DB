"""
Widget Indexer
==============
Scans all Python source files in the project and builds a map of
{PyQt6WidgetType: [list_of_classes_that_use_it]}.

Run as a script to regenerate config/widget_index.json:
    python src/utils/widget_indexer.py

Or import and call build_widget_index() / load_widget_index() at runtime.
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

# Where we write the cached index
_INDEX_PATH = Path(__file__).parent.parent.parent / "config" / "widget_index.json"

# Directories to scan (relative to project root)
_SCAN_DIRS = [
    Path(__file__).parent.parent / "tabs",
    Path(__file__).parent.parent / "utils",
    Path(__file__).parent,               # this file's dir = utils
]
_SCAN_DIRS.append(Path(__file__).parent.parent)  # src/ root for main.py


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

            # Collect class names defined in this file
            class_names = re.findall(r"^class\s+([A-Za-z_]\w*)", source, re.MULTILINE)
            if not class_names:
                # Use the stem as a fallback label
                class_names = [py_file.stem]

            for widget in INDEXED_WIDGETS:
                # Match: WidgetType( or WidgetType) or "import WidgetType"
                if re.search(r"\b" + re.escape(widget) + r"\b", source):
                    for cn in class_names:
                        index[widget].add(cn)

    return {w: sorted(v) for w, v in index.items()}


def save_widget_index(index: dict[str, list[str]]) -> None:
    """Persist the index to config/widget_index.json."""
    _INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
    logger.info("Widget index saved to %s", _INDEX_PATH)


def load_widget_index() -> dict[str, list[str]]:
    """Load cached index; rebuild if missing or empty."""
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


# ── Human-readable "used in" label ───────────────────────────────────────────

def used_in_label(widget_type: str, index: dict[str, list[str]]) -> str:
    """Return a compact comma-separated list of class names for the tooltip."""
    classes = index.get(widget_type, [])
    if not classes:
        return "not used"
    # Omit pure-utility classes (layouts, managers, etc.)
    _SKIP = {"QApplication", "ClaudeDBApp"}
    filtered = [c for c in classes if c not in _SKIP]
    if not filtered:
        return "not used"
    return ", ".join(filtered)


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    print("Scanning source files…")
    idx = build_widget_index()
    save_widget_index(idx)
    print(f"Saved to {_INDEX_PATH}")
    for widget, classes in idx.items():
        print(f"  {widget:20s} ({len(classes):2d}) — {', '.join(classes[:5])}{'…' if len(classes)>5 else ''}")
