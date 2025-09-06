# ui/main_window.py:
import os
import traceback
from pathlib import Path
import webbrowser

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox,
    QTextEdit, QProgressBar, QLabel, QMessageBox, QAction, QMenu,
    QGroupBox, QDialog, QSystemTrayIcon, QComboBox, QInputDialog, QTreeWidgetItemIterator, QApplication
)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QIcon

from ui.category_manager_dialog import CategoryManagerDialog
from ui.settings import SettingsDialog
from ui.duplicates_dialog import DuplicatesDialog
from ui.rules_dialog import RulesDialog

from core.sorter import FileSorter
from core.cleaner import DesktopCleaner
from core.duplicates import DuplicateFinder
from core.organizer import DesktopOrganizer
from core.profile_manager import ProfileManager
from core.utils import save_config, get_all_desktop_paths
from core.threading_pool import ThreadManager
from core.undo_manager import UndoManager
from core.updater import Updater


class MainWindow(QMainWindow):
    def __init__(self, config, box_manager, current_version):
        super().__init__()
        self.config = config
        self.box_manager = box_manager
        self.setWindowTitle(f"Desktop Manager (v{current_version})")
        self.setGeometry(100, 100, 600, 500)

        self.thread_manager = ThreadManager()
        self.undo_manager = UndoManager()
        self.profile_manager = ProfileManager()

        self.organizer = DesktopOrganizer(self.config)
        self.desktop_cleaner = DesktopCleaner(self.config)
        self.file_sorter = FileSorter()
        self.duplicate_finder = DuplicateFinder()

        self._init_ui()
        self._init_tray_icon()
        self._setup_connections()
        self._load_settings_to_ui()
        self._update_profile_list()

        self.updater = Updater(current_version)
        self.updater.update_available.connect(self._show_update_dialog)
        QTimer.singleShot(3000, lambda: self.thread_manager.start_task(self.updater.check_for_updates))

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)

        profile_group = QGroupBox("Управление профилями")
        profile_layout = QHBoxLayout(profile_group)
        self.profile_combo = QComboBox()
        self.load_profile_btn = QPushButton("Загрузить")
        self.new_profile_btn = QPushButton("Создать")
        self.delete_profile_btn = QPushButton("Удалить")
        profile_layout.addWidget(QLabel("Профиль:"))
        profile_layout.addWidget(self.profile_combo, 1)
        profile_layout.addWidget(self.load_profile_btn)
        profile_layout.addWidget(self.new_profile_btn)
        profile_layout.addWidget(self.delete_profile_btn)
        self.main_layout.addWidget(profile_group)

        auto_group = QGroupBox("Автоматическая организация")
        auto_layout = QHBoxLayout(auto_group)
        self.auto_organize_cb = QCheckBox("Сортировать новые файлы")
        self.organize_btn = QPushButton("Организовать сейчас")
        self.manage_categories_btn = QPushButton("Настроить категории")
        self.manage_rules_btn = QPushButton("Продвинутые правила")
        auto_layout.addWidget(self.auto_organize_cb)
        auto_layout.addStretch()
        auto_layout.addWidget(self.manage_rules_btn)
        auto_layout.addWidget(self.manage_categories_btn)
        auto_layout.addWidget(self.organize_btn)
        self.main_layout.addWidget(auto_group)

        manual_ops_group = QGroupBox("Ручные операции")
        manual_layout = QHBoxLayout(manual_ops_group)

        clean_opts_layout = QVBoxLayout()
        self.clean_shortcuts_cb = QCheckBox("Удалить битые ярлыки")
        self.clean_temp_cb = QCheckBox("Удалить временные файлы")
        clean_opts_layout.addWidget(self.clean_shortcuts_cb)
        clean_opts_layout.addWidget(self.clean_temp_cb)

        sort_opts_layout = QVBoxLayout()
        self.sort_date_cb = QCheckBox("Сортировать по дате")
        self.sort_type_cb = QCheckBox("Сортировать по типу")
        sort_opts_layout.addWidget(self.sort_date_cb)
        sort_opts_layout.addWidget(self.sort_type_cb)

        buttons_layout = QVBoxLayout()
        self.clean_btn = QPushButton("Очистить")
        self.sort_btn = QPushButton("Сортировать")
        self.duplicates_btn = QPushButton("Найти дубликаты")
        self.undo_btn = QPushButton("Отменить")
        self.undo_btn.setToolTip("Отменить последнее действие (Ctrl+Z)")

        buttons_layout.addWidget(self.clean_btn)
        buttons_layout.addWidget(self.sort_btn)
        buttons_layout.addWidget(self.duplicates_btn)
        buttons_layout.addWidget(self.undo_btn)

        manual_layout.addLayout(clean_opts_layout)
        manual_layout.addLayout(sort_opts_layout)
        manual_layout.addStretch()
        manual_layout.addLayout(buttons_layout)
        self.main_layout.addWidget(manual_ops_group)

        self.progress_bar = QProgressBar()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.log_output, 1)

        self.statusBar()
        self._create_actions()
        self._create_menus()

    def _init_tray_icon(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self.windowIcon(), self)
            tray_menu = QMenu()
            tray_menu.addAction(self.show_action)
            tray_menu.addAction(self.exit_action)
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            self.tray_icon.setToolTip("Desktop Manager")

    def _show_notification(self, title, message):
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.Information, 3000)

    def _create_actions(self):
        self.undo_action = QAction("Отменить", self, shortcut="Ctrl+Z", triggered=self._undo_last_action)
        self.settings_action = QAction("Настройки", self, triggered=self._open_settings)
        self.show_action = QAction("Показать", self, triggered=self.showNormal)
        self.exit_action = QAction("Выход", self, triggered=self.close)

    def _create_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Файл")
        file_menu.addAction(self.settings_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        edit_menu = menu_bar.addMenu("Правка")
        edit_menu.addAction(self.undo_action)

    def _setup_connections(self):
        self.organize_btn.clicked.connect(self._organize_now)
        self.clean_btn.clicked.connect(self._on_clean_clicked)
        self.sort_btn.clicked.connect(self._on_sort_clicked)
        self.duplicates_btn.clicked.connect(self._on_find_duplicates)
        self.manage_categories_btn.clicked.connect(self._manage_categories)
        self.undo_btn.clicked.connect(self._undo_last_action)
        self.manage_rules_btn.clicked.connect(self._manage_rules)

        self.load_profile_btn.clicked.connect(self._load_selected_profile)
        self.new_profile_btn.clicked.connect(self._create_new_profile)
        self.delete_profile_btn.clicked.connect(self._delete_profile)

        for module in [self.organizer, self.file_sorter, self.desktop_cleaner, self.duplicate_finder]:
            module.progress_updated.connect(self._update_progress)

        self.organizer.organization_completed.connect(self._on_operation_completed)
        self.file_sorter.sorting_completed.connect(self._on_operation_completed)
        self.desktop_cleaner.cleaning_completed.connect(self._on_operation_completed)
        self.duplicate_finder.duplicates_found.connect(self._show_duplicates)

        self.organizer.operation_logged.connect(self.undo_manager.add_operation)
        self.desktop_cleaner.operation_logged.connect(self.undo_manager.add_operation)
        self.file_sorter.operation_logged.connect(self.undo_manager.add_operation)

    def _load_settings_to_ui(self):
        sort_options = self.config.get("sort_options", {})
        self.sort_date_cb.setChecked(sort_options.get("by_date", False))
        self.sort_type_cb.setChecked(sort_options.get("by_type", False))
        clean_options = self.config.get("clean_options", {})
        self.clean_shortcuts_cb.setChecked(clean_options.get("remove_broken_shortcuts", True))
        self.clean_temp_cb.setChecked(clean_options.get("remove_temp_files", True))
        self.auto_organize_cb.setChecked(self.config.get("auto_organize_enabled", True))

    def _save_ui_settings_to_config(self):
        self.config["sort_options"] = {"by_date": self.sort_date_cb.isChecked(),
                                       "by_type": self.sort_type_cb.isChecked()}
        self.config["clean_options"] = {"remove_broken_shortcuts": self.clean_shortcuts_cb.isChecked(),
                                        "remove_temp_files": self.clean_temp_cb.isChecked()}
        self.config["auto_organize_enabled"] = self.auto_organize_cb.isChecked()
        save_config(self.config)

    @pyqtSlot(int)
    def _update_progress(self, value):
        self.progress_bar.setValue(value)

    @pyqtSlot(str)
    def _log_message(self, message):
        self.log_output.append(message)
        self.statusBar().showMessage(message, 5000)

    @pyqtSlot(str)
    def _on_operation_completed(self, message):
        self._log_message(message)
        if "Ошибка" not in message:
            self._show_notification("Операция завершена", message)

    # --- ИЗМЕНЕНИЕ: Восстановленные методы ---
    def _get_primary_desktop(self):
        """Возвращает путь к основному рабочему столу пользователя."""
        paths = get_all_desktop_paths()
        if not paths:
            QMessageBox.critical(self, "Ошибка", "Не удалось определить путь к рабочему столу.")
            return None
        return paths[0]

    def _organize_now(self):
        self._log_message("Запуск организации рабочего стола...")
        self.thread_manager.start_task(self.organizer.organize_all_desktops)

    def _on_clean_clicked(self):
        desktop = self._get_primary_desktop()
        if not desktop: return
        options = {"remove_broken_shortcuts": self.clean_shortcuts_cb.isChecked(),
                   "remove_temp_files": self.clean_temp_cb.isChecked()}
        self._log_message(f"Запуск очистки для '{desktop}'...")
        self.thread_manager.start_task(self.desktop_cleaner.clean_desktop, desktop, options)

    def _on_sort_clicked(self):
        desktop = self._get_primary_desktop()
        if not desktop: return
        criteria = {"by_date": self.sort_date_cb.isChecked(), "by_type": self.sort_type_cb.isChecked()}
        if not any(criteria.values()):
            QMessageBox.warning(self, "Нет критерия", "Выберите хотя бы один критерий для сортировки.")
            return
        self._log_message(f"Запуск сортировки для '{desktop}'...")
        self.thread_manager.start_task(self.file_sorter.sort_desktop, desktop, criteria)

    def _on_find_duplicates(self):
        desktop = self._get_primary_desktop()
        if not desktop: return
        self._log_message(f"Поиск дубликатов в '{desktop}'...")
        self.thread_manager.start_task(self.duplicate_finder.find_duplicates, desktop)

    # --- Конец восстановленных методов ---

    @pyqtSlot(dict)
    def _show_duplicates(self, duplicates):
        if not duplicates:
            self._log_message("Дубликаты файлов не найдены.")
            QMessageBox.information(self, "Результат", "Дубликаты не найдены.")
            return
        self._log_message(f"Найдено {len(duplicates)} групп(ы) дубликатов. Открыто окно управления.")
        dialog = DuplicatesDialog(duplicates, self)
        dialog.exec_()
        self._log_message("Окно управления дубликатами закрыто.")

    def _manage_categories(self):
        dialog = CategoryManagerDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.get_updated_config()
            save_config(self.config)
            self.organizer.classifier.categories = self.config.get('categories', {})
            self._log_message("Настройки категорий обновлены.")

    def _manage_rules(self):
        self._log_message("Открыт редактор продвинутых правил.")
        dialog = RulesDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.config
            save_config(self.config)
            self.organizer.classifier.advanced_rules = self.config.get('advanced_rules', [])
            self._log_message("Продвинутые правила обновлены.")
        else:
            self._log_message("Изменение продвинутых правил отменено.")

    def _open_settings(self):
        self._save_ui_settings_to_config()
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.get_config()
            save_config(self.config)
            self._load_settings_to_ui()
            self._log_message("Настройки сохранены.")
            from main import apply_theme
            apply_theme(QApplication.instance(), self.config.get("theme"))

    @pyqtSlot(str, str)
    def _show_update_dialog(self, new_version, download_url):
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Доступно обновление")
        msg_box.setText(f"Доступна новая версия: <b>{new_version}</b><br>"
                        f"Хотите перейти на страницу загрузки?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)

        yes_button = msg_box.button(QMessageBox.Yes)
        yes_button.setText("Перейти")
        no_button = msg_box.button(QMessageBox.No)
        no_button.setText("Позже")

        if msg_box.exec_() == QMessageBox.Yes:
            webbrowser.open(download_url)

    def _undo_last_action(self):
        success, message = self.undo_manager.undo_last()
        self._log_message(message)
        if success:
            self._show_notification("Действие отменено", message)

    def _update_profile_list(self):
        self.profile_combo.clear()
        profiles = self.profile_manager.list_profiles()
        if profiles:
            self.profile_combo.addItems(profiles)

    def _load_selected_profile(self):
        profile_name = self.profile_combo.currentText()
        if not profile_name: return
        profile_data = self.profile_manager.load_profile(profile_name)
        if profile_data:
            self.config.update(profile_data)
            self._load_settings_to_ui()
            self._log_message(f"Профиль '{profile_name}' загружен.")
        else:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить профиль '{profile_name}'.")

    def _create_new_profile(self):
        name, ok = QInputDialog.getText(self, "Новый профиль", "Введите имя профиля:")
        if ok and name:
            self._save_ui_settings_to_config()
            profile_settings = {"sort_options": self.config.get("sort_options"),
                                "clean_options": self.config.get("clean_options"),
                                "auto_organize_enabled": self.config.get("auto_organize_enabled")}
            if self.profile_manager.save_profile(name, profile_settings):
                self._log_message(f"Профиль '{name}' создан.")
                self._update_profile_list()
                self.profile_combo.setCurrentText(name)
            else:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить профиль '{name}'.")

    def _delete_profile(self):
        profile_name = self.profile_combo.currentText()
        if not profile_name: return
        reply = QMessageBox.question(self, "Подтверждение", f"Удалить профиль '{profile_name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.profile_manager.delete_profile(profile_name):
                self._log_message(f"Профиль '{profile_name}' удален.")
                self._update_profile_list()
            else:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить профиль '{profile_name}'.")

    def closeEvent(self, event):
        self._save_ui_settings_to_config()
        super().closeEvent(event)