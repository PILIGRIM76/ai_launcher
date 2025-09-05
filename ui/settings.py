# ui/settings.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QCheckBox, QMessageBox
)
# --- ИМПОРТИРУЕМ НАШ НОВЫЙ МОДУЛЬ ---
from core import startup_manager


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(400)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        theme_group = QGroupBox("Внешний вид")
        theme_layout = QHBoxLayout(theme_group)
        theme_layout.addWidget(QLabel("Тема оформления:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        theme_layout.addWidget(self.theme_combo)

        general_group = QGroupBox("Общие")
        general_layout = QVBoxLayout(general_group)
        # --- АКТИВИРУЕМ ЧЕКБОКС ---
        self.run_on_startup_cb = QCheckBox("Запускать при старте Windows")
        self.run_initial_org_cb = QCheckBox("Выполнять организацию при запуске программы")
        general_layout.addWidget(self.run_on_startup_cb)
        general_layout.addWidget(self.run_initial_org_cb)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addWidget(theme_group)
        layout.addWidget(general_group)
        layout.addStretch(1)
        layout.addLayout(button_layout)

        self._load_settings()

        self.save_btn.clicked.connect(self._save_and_accept)
        self.cancel_btn.clicked.connect(self.reject)

    def _load_settings(self):
        """Загружает настройки из конфига и реестра в UI."""
        current_theme = self.config.get("theme", "light")
        self.theme_combo.setCurrentText(current_theme)

        self.run_initial_org_cb.setChecked(self.config.get("run_initial_organization", True))

        # --- ЗАГРУЖАЕМ СТАТУС АВТОЗАПУСКА ИЗ РЕЕСТРА ---
        self.run_on_startup_cb.setChecked(startup_manager.is_enabled())

    def _save_and_accept(self):
        """Сохраняет настройки в конфиг и реестр."""
        self.config["theme"] = self.theme_combo.currentText()
        self.config["run_initial_organization"] = self.run_initial_org_cb.isChecked()

        # --- СОХРАНЯЕМ СТАТУС АВТОЗАПУСКА В РЕЕСТР ---
        try:
            if self.run_on_startup_cb.isChecked():
                startup_manager.enable()
            else:
                startup_manager.disable()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось изменить настройки автозапуска:\n{e}")

        self.accept()

    def get_config(self):
        """Возвращает обновленную конфигурацию."""
        return self.config