from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QCheckBox
)


class SettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config.copy()
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(400)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # --- ИЗМЕНЕНИЕ: Добавляем группу для темы ---
        display_group = QGroupBox("Оформление")
        display_layout = QHBoxLayout(display_group)
        display_layout.addWidget(QLabel("Тема:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Светлая", "Темная"])
        display_layout.addWidget(self.theme_combo)

        general_group = QGroupBox("Общие")
        general_layout = QVBoxLayout(general_group)
        self.run_on_startup_cb = QCheckBox("Запускать при старте Windows (не реализовано)")
        self.run_initial_org_cb = QCheckBox("Выполнять организацию при запуске программы")
        general_layout.addWidget(self.run_on_startup_cb)
        general_layout.addWidget(self.run_initial_org_cb)

        security_group = QGroupBox("Безопасность")
        security_layout = QVBoxLayout(security_group)
        self.use_recycle_cb = QCheckBox("Использовать внутреннюю корзину для удаленных файлов")
        self.backup_cb = QCheckBox("Создавать резервные копии (не реализовано)")
        security_layout.addWidget(self.use_recycle_cb)
        security_layout.addWidget(self.backup_cb)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addWidget(display_group)  # Добавили группу в layout
        layout.addWidget(general_group)
        layout.addWidget(security_group)
        layout.addStretch(1)
        layout.addLayout(button_layout)

        self._load_settings()

        self.save_btn.clicked.connect(self._save_and_accept)
        self.cancel_btn.clicked.connect(self.reject)

    def _load_settings(self):
        # --- ИЗМЕНЕНИЕ: Загружаем тему ---
        current_theme = self.config.get("theme", "light")
        self.theme_combo.setCurrentIndex(1 if current_theme == "dark" else 0)

        self.run_initial_org_cb.setChecked(self.config.get("run_initial_organization", True))
        security = self.config.get("security", {})
        self.use_recycle_cb.setChecked(security.get("use_recycle_bin", True))
        self.backup_cb.setChecked(security.get("backup_before_operations", True))

    def _save_and_accept(self):
        # --- ИЗМЕНЕНИЕ: Сохраняем тему ---
        self.config["theme"] = "dark" if self.theme_combo.currentIndex() == 1 else "light"

        self.config["run_initial_organization"] = self.run_initial_org_cb.isChecked()
        if "security" not in self.config:
            self.config["security"] = {}
        self.config["security"]["use_recycle_bin"] = self.use_recycle_cb.isChecked()
        self.config["security"]["backup_before_operations"] = self.backup_cb.isChecked()

        self.accept()

    def get_config(self):
        return self.config