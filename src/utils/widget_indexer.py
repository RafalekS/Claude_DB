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


# ── Navigation tree ──────────────────────────────────────────────────────────
# Scans main.py for top-level tabs and tabs/*.py for .addTab() calls to build
# the full parent→child hierarchy with real display labels.

_MAIN_PY_PATH  = Path(__file__).parent.parent / "main.py"
_NAV_TREE_PATH = Path(__file__).parent.parent.parent / "config" / "nav_tree.json"


def _strip_label(class_name: str) -> str:
    """'MemoryTab' → 'Memory', 'UserPermissionsSubTab' → 'User Permissions'"""
    for suffix in ("SubTab", "Subtab", "Dialog", "Window", "Tab"):
        if class_name.endswith(suffix):
            raw = class_name[: -len(suffix)]
            return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", raw).strip()
    return class_name


def _split_class_chunks(src: str) -> list[tuple[str, str]]:
    """Return [(class_name, class_body_text)] for every class in src."""
    starts = [
        (m.start(), m.group(1))
        for m in re.finditer(r"^class\s+([A-Za-z_]\w*)", src, re.MULTILINE)
    ]
    if not starts:
        return []
    return [
        (name, src[pos: starts[i + 1][0] if i + 1 < len(starts) else len(src)])
        for i, (pos, name) in enumerate(starts)
    ]


def _extract_method_body(src: str, method_name: str) -> str:
    """Return the source text of a named method, or '' if not found."""
    m = re.search(r"\bdef\s+" + re.escape(method_name) + r"\s*\(", src)
    if not m:
        return ""
    line_start = src.rfind("\n", 0, m.start()) + 1
    base_indent = m.start() - line_start
    lines = src[m.start():].split("\n")
    body = [lines[0]]
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped and not stripped.startswith("#"):
            if (len(line) - len(stripped)) <= base_indent:
                break
        body.append(line)
    return "\n".join(body)


def build_navigation_tree() -> list[dict]:
    """
    Build a full navigation hierarchy by scanning main.py (top-level tabs)
    and all tabs/*.py (addTab calls).

    Each entry: {"id", "label", "type", "parent_id", "parent_label",
                 "source_class", "builder"}
      - id:           class name OR "ParentClass::Label" for anonymous subtabs
      - source_class: class whose file contains the widget code
      - builder:      method name to scan for widgets (anonymous subtabs only)
    """
    nav: dict[str, dict] = {}

    # ── Step 1: top-level tabs from main.py ──────────────────────────────────
    if _MAIN_PY_PATH.exists():
        src = _MAIN_PY_PATH.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(
            r'"[^"]+"\s*:\s*\(\s*"([^"]+)"\s*,\s*([A-Za-z]\w+)\s*\(',
            src,
        ):
            label, cls = m.group(1).strip(), m.group(2)
            nav[cls] = {
                "id": cls, "label": label, "type": "Tab",
                "parent_id": None, "parent_label": None,
                "source_class": cls, "builder": None,
            }

    # ── Step 2: scan tabs/*.py for addTab calls ───────────────────────────────
    for py_file in sorted(_TABS_DIR.glob("*.py")):
        if "__pycache__" in str(py_file):
            continue
        try:
            src = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for cls_name, cls_body in _split_class_chunks(src):
            parent_entry = nav.get(cls_name)
            parent_label = parent_entry["label"] if parent_entry else _strip_label(cls_name)

            # Map: self.attr → {"class": ClassName|None, "builder": method|None}
            attr_map: dict[str, dict] = {}
            for am in re.finditer(
                r"self\.(\w+)\s*=\s*(?:self\.(\w+)\s*\(|([A-Z][A-Za-z]\w*)\s*\()",
                cls_body,
            ):
                attr = am.group(1)
                if am.group(2):
                    attr_map[attr] = {"builder": am.group(2), "class": None}
                else:
                    attr_map[attr] = {"builder": None, "class": am.group(3)}

            # Map: local_var → ClassName  (e.g. claude_md_tab = ProjectClaudeMDSubTab(...))
            local_var_map: dict[str, str] = {}
            for lm in re.finditer(
                r"^\s+(\w+)\s*=\s*([A-Z][A-Za-z]\w*)\s*\(",
                cls_body,
                re.MULTILINE,
            ):
                local_var_map[lm.group(1)] = lm.group(2)

            # Find every .addTab(widget_expr, "Label")
            for tab_m in re.finditer(
                r"\.addTab\s*\(\s*([^,]+?)\s*,\s*['\"]([^'\"]+)['\"]",
                cls_body,
            ):
                widget_expr = tab_m.group(1).strip()
                tab_label   = tab_m.group(2).strip()
                if not tab_label:
                    continue

                child_id   = None
                source_cls = cls_name
                builder    = None

                # Case A: ClassName(...)  ← direct instantiation inside addTab
                ma = re.match(r"([A-Z][A-Za-z]\w*)\s*\(", widget_expr)
                if ma:
                    child_id   = ma.group(1)
                    source_cls = ma.group(1)

                # Case B: self.method(...)  ← anonymous builder
                elif re.match(r"self\.(\w+)\s*\(", widget_expr):
                    mb = re.match(r"self\.(\w+)\s*\(", widget_expr)
                    builder  = mb.group(1)
                    child_id = f"{cls_name}::{tab_label}"

                # Case C: self.attr  ← previously stored instance attribute
                elif re.match(r"self\.(\w+)$", widget_expr):
                    mc   = re.match(r"self\.(\w+)$", widget_expr)
                    info = attr_map.get(mc.group(1))
                    if info and info["class"]:
                        child_id   = info["class"]
                        source_cls = info["class"]
                    elif info and info["builder"]:
                        builder  = info["builder"]
                        child_id = f"{cls_name}::{tab_label}"
                    else:
                        child_id = f"{cls_name}::{tab_label}"

                # Case D: local variable  ← local_var = ClassName(...)
                elif re.match(r"^\w+$", widget_expr):
                    named = local_var_map.get(widget_expr)
                    if named:
                        child_id   = named
                        source_cls = named
                    else:
                        child_id = f"{cls_name}::{tab_label}"

                else:
                    continue   # dynamic / unresolvable

                if child_id not in nav:
                    nav[child_id] = {
                        "id":           child_id,
                        "label":        tab_label,
                        "type":         "SubTab",
                        "parent_id":    cls_name,
                        "parent_label": parent_label,
                        "source_class": source_cls,
                        "builder":      builder,
                    }
                elif nav[child_id].get("parent_id") is None:
                    nav[child_id]["parent_id"]    = cls_name
                    nav[child_id]["parent_label"] = parent_label

            # ── Special: scan (fn, "https://...", "label") page-def tuples ──
            # Handles DocumentationTab-style dynamic addTab loops where labels
            # are in a list of (callable, url, "Label") tuples.
            for lm in re.finditer(
                r"\(\s*\w+\s*,\s*\"https?://[^\"]*\"\s*,\s*\"([^\"]+)\"\s*\)",
                cls_body,
            ):
                tab_label = lm.group(1).strip()
                if not tab_label:
                    continue
                child_id = f"{cls_name}::{tab_label}"
                if child_id not in nav:
                    nav[child_id] = {
                        "id":           child_id,
                        "label":        tab_label,
                        "type":         "SubTab",
                        "parent_id":    cls_name,
                        "parent_label": parent_label,
                        "source_class": cls_name,
                        "builder":      None,
                    }

    return list(nav.values())


def get_widgets_for_nav_entry(entry: dict) -> list[str]:
    """Return Qt widget class names used in a specific navigation entry.

    For anonymous subtabs (builder method given), scans only that method body.
    For named-class entries, scans the whole class file.
    """
    source_cls = entry.get("source_class")
    builder    = entry.get("builder")

    if not source_cls:
        return []

    src_text = ""
    for py_file in _TABS_DIR.glob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            txt = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if re.search(r"^class\s+" + re.escape(source_cls) + r"\b", txt, re.MULTILINE):
            src_text = txt
            break

    if not src_text:
        return []

    scan_src = _extract_method_body(src_text, builder) if builder else src_text
    if not scan_src:
        scan_src = src_text

    found = []
    for widget in INDEXED_WIDGETS:
        pattern = _DETECTION_OVERRIDES.get(widget, r"\b" + re.escape(widget) + r"\b")
        if re.search(pattern, scan_src):
            found.append(widget)
    return found


def build_entries_by_qt_class() -> dict[str, list[dict]]:
    """Build {qt_class: [nav_entries]} with accurate per-method-body detection.

    Unlike using vis_idx (whole-file), this scans only the specific builder
    method body for anonymous subtabs, so e.g. MemoryTab::Overview only lists
    widgets actually present in _build_overview(), not the entire memory_tab.py.
    """
    nav_tree = load_navigation_tree()

    # Preload all tab source files keyed by class name (read each file once)
    _file_cache: dict[str, str] = {}
    for py_file in _TABS_DIR.glob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            txt = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for cls in re.findall(r"^class\s+([A-Za-z_]\w*)", txt, re.MULTILINE):
            _file_cache[cls] = txt

    result: dict[str, list[dict]] = {}
    seen: set[tuple] = set()

    for entry in nav_tree:
        source_cls = entry.get("source_class")
        builder    = entry.get("builder")
        if not source_cls:
            continue
        src_text = _file_cache.get(source_cls, "")
        if not src_text:
            continue
        scan_src = _extract_method_body(src_text, builder) if builder else src_text
        if not scan_src:
            scan_src = src_text

        for widget in INDEXED_WIDGETS:
            pattern = _DETECTION_OVERRIDES.get(widget, r"\b" + re.escape(widget) + r"\b")
            if re.search(pattern, scan_src):
                key = (widget, entry["id"])
                if key not in seen:
                    seen.add(key)
                    result.setdefault(widget, []).append(entry)

    return result


def save_navigation_tree(tree: list[dict]) -> None:
    """Persist the navigation tree to config/nav_tree.json."""
    _NAV_TREE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_NAV_TREE_PATH, "w", encoding="utf-8") as f:
        json.dump(tree, f, indent=2)
    logger.info("Navigation tree saved to %s", _NAV_TREE_PATH)


def load_navigation_tree() -> list[dict]:
    """Load cached navigation tree; rebuild if missing."""
    if _NAV_TREE_PATH.exists():
        try:
            data = json.loads(_NAV_TREE_PATH.read_text(encoding="utf-8"))
            if data:
                return data
        except Exception:
            pass
    tree = build_navigation_tree()
    save_navigation_tree(tree)
    return tree


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

    print("Building navigation tree…")
    tree = build_navigation_tree()
    save_navigation_tree(tree)
    print(f"Nav tree → {_NAV_TREE_PATH}  ({len(tree)} entries)")
    print()
    for e in sorted(tree, key=lambda x: (x.get("parent_id") or "", x["label"])):
        indent = "  " if e.get("parent_id") else ""
        parent = f"  ← {e['parent_label']}" if e.get("parent_label") else ""
        print(f"  {indent}{e['type']:8s}  {e['label']}{parent}")

    print()
    for widget in INDEXED_WIDGETS:
        full_n = len(idx.get(widget, []))
        vis_locs = vis.get(widget, [])
        vis_n = len(vis_locs)
        print(f"  {widget:20s}  full={full_n:3d}  visible={vis_n:2d} — "
              f"{', '.join(vis_locs[:4])}{'…' if vis_n > 4 else ''}")
