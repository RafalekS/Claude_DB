"""
User Settings sub-tab — the master/detail settings.json editor for
~/.claude/settings.json (see tabs/settings_editor.py).
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout

from tabs.settings_editor import SettingsEditor, user_scope


class UserSettingsSubTab(QWidget):
    def __init__(self, config_manager, backup_manager, settings_manager):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.editor = SettingsEditor(user_scope(config_manager), backup_manager)
        layout.addWidget(self.editor)

    def load_settings(self):
        self.editor.reload()

    def apply_theme(self):
        self.editor.apply_theme()
