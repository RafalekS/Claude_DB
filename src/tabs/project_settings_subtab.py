"""
Project Settings sub-tab — the master/detail settings.json editor for a project's
.claude/settings.json (Shared) and .claude/settings.local.json (Local).
See tabs/settings_editor.py.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout

from tabs.settings_editor import SettingsEditor, project_scopes


class ProjectSettingsSubTab(QWidget):
    def __init__(self, config_manager, backup_manager, settings_manager, project_context):
        super().__init__()
        self.config_manager = config_manager
        self.backup_manager = backup_manager
        self.settings_manager = settings_manager
        self.project_context = project_context

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.editor = SettingsEditor(
            project_scopes(settings_manager, project_context), backup_manager
        )
        layout.addWidget(self.editor)

        if project_context is not None:
            project_context.project_changed.connect(lambda *_: self.editor.reload())

    def load_settings(self, *_):
        self.editor.reload()

    def load_all_settings(self):
        self.editor.reload()

    def apply_theme(self):
        self.editor.apply_theme()
