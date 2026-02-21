 Before you remove any functionality or change any functionality - YOU HAVE TO ASK USER for Permission FIRST

## PyQt6 QComboBox Dropdown Height Fix
Fusion style ignores `setMaxVisibleItems()` - use `combobox-popup: 0;` in stylesheet + `max-height: 300px;` on view's stylesheet to limit dropdown height.