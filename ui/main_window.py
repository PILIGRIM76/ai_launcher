# ui/main_window.py
import os
import webbrowser
from pathlib import Path
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QCheckBox, QTextEdit,
                             QProgressBar, QLabel, QMessageBox, QAction, QMenu, QGroupBox, QDialog, QSystemTrayIcon,
                             QComboBox, QInputDialog)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QIcon
from requests import __version__

from core.updater import Updater
from ui.category_manager_dialog import CategoryManagerDialog
from ui.settings import SettingsDialog
from ui.duplicates_dialog import DuplicatesDialog
from core.sorter import FileSorter
from core.cleaner import DesktopCleaner
from core.duplicates import DuplicateFinder
from core.organizer import DesktopOrganizer
from core.profile_manager import ProfileManager
from core.utils import save_config, get_desktop_path
from core.threading_pool import ThreadManager
from core.undo_manager import UndoManager
from core.analyzer import DesktopAnalyzer
from core.watcher import DesktopWatcher


class MainWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Pilgrim Desktop Manager v1.0.0")
        self.setGeometry(100, 100, 600, 500)

        # 1. Инициализация
        self.thread_manager = ThreadManager()
        self.undo_manager = UndoManager()
        self.profile_manager = ProfileManager()
        self.organizer = DesktopOrganizer(self.config)
        self.desktop_cleaner = DesktopCleaner(self.config)
        self.analyzer = DesktopAnalyzer(self.config)
        self.file_sorter = FileSorter()
        self.duplicate_finder = DuplicateFinder()
        self.watcher = DesktopWatcher(self.organizer, get_desktop_path())

        # 2. Создаем UI
        self._init_ui()
        self._create_actions()
        self._init_tray_icon()
        self._create_menus()

        # 3. Подключаем сигналы
        self._setup_connections()

        # 4. Загружаем настройки
        self._load_settings_to_ui()
        self._update_profile_list()

        # 5. Запускаем начальные операции
        if self.config.get("run_initial_organization", False):
            QTimer.singleShot(1000, self.organizer.organize_all_desktops)

        if self.auto_organize_cb.isChecked():
            self.watcher.start()

    def _init_ui(self, GITHUB_REPO=None):
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
        auto_layout.addWidget(self.auto_organize_cb)
        auto_layout.addStretch()
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
        buttons_layout.addWidget(self.clean_btn)
        buttons_layout.addWidget(self.sort_btn)
        buttons_layout.addWidget(self.duplicates_btn)
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

        self.auto_organize_cb.setToolTip("Включить/отключить автоматическую организацию новых файлов")
        self.organize_btn.setToolTip("Запустить организацию всех файлов на рабочем столе сейчас")
        self.manage_categories_btn.setToolTip("Открыть редактор категорий и расширений")
        self.clean_btn.setToolTip("Удалить мусорные файлы согласно выбранным опциям")
        self.sort_btn.setToolTip("Отсортировать файлы в папки по дате или типу")
        self.duplicates_btn.setToolTip("Найти и удалить дубликаты файлов на рабочем столе")

        # 1. Инициализация
        self.thread_manager = ThreadManager()
        self.undo_manager = UndoManager()
        # ... (другие менеджеры)
        # --- ИНИЦИАЛИЗИРУЕМ UPDATER ---
        self.updater = Updater(__version__, GITHUB_REPO)

    def _create_actions(self):
        self.undo_action = QAction("Отменить", self, shortcut="Ctrl+Z", triggered=self._undo_last_action)
        self.settings_action = QAction("Настройки", self, triggered=self._open_settings)
        self.analyze_action = QAction("Анализ рабочего стола", self, triggered=self._analyze_desktop)
        self.show_action = QAction("Показать", self, triggered=self.showNormal)
        self.exit_action = QAction("Выход", self, triggered=self.close)
        self.about_action = QAction("О программе", self, triggered=self._show_about_dialog)
        self.update_action = QAction("Проверить обновления...", self, triggered=self._check_for_updates)

    def _init_tray_icon(self):
        icon = QIcon(":/icons/app_icon.ico")
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(icon, self)
            tray_menu = QMenu()
            tray_menu.addAction(self.show_action)
            tray_menu.addAction(self.exit_action)
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()
            self.tray_icon.setToolTip("Piligrim Desktop Manager v1.0.0")

    def _create_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("Файл")
        file_menu.addAction(self.settings_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        edit_menu = menu_bar.addMenu("Правка")
        edit_menu.addAction(self.undo_action)
        tools_menu = menu_bar.addMenu("Инструменты")
        tools_menu.addAction(self.analyze_action)
        help_menu = menu_bar.addMenu("Справка")
        help_menu.addAction(self.about_action)
        # --- ДОБАВЛЯЕМ НОВЫЙ ПУНКТ В МЕНЮ ---
        help_menu.addAction(self.update_action)
        help_menu.addAction(self.about_action)

    # --- ИСПРАВЛЕННЫЙ МЕТОД ---
    def _setup_connections(self):
        """Подключает все сигналы к слотам."""
        # Чекбокс
        self.auto_organize_cb.stateChanged.connect(self._toggle_watcher)

        # Кнопки
        self.organize_btn.clicked.connect(self._organize_now)
        self.clean_btn.clicked.connect(self._on_clean_clicked)
        self.sort_btn.clicked.connect(self._on_sort_clicked)
        self.duplicates_btn.clicked.connect(self._on_find_duplicates)
        self.manage_categories_btn.clicked.connect(self._manage_categories)

        # Профили
        self.load_profile_btn.clicked.connect(self._load_selected_profile)
        self.new_profile_btn.clicked.connect(self._create_new_profile)
        self.delete_profile_btn.clicked.connect(self._delete_profile)

        # Сигналы от модулей
        self.analyzer.suggestion_found.connect(self._handle_suggestion)
        self.organizer.status_updated.connect(self.statusBar().showMessage)
        self.duplicate_finder.status_updated.connect(self.statusBar().showMessage)

        for module in [self.organizer, self.file_sorter, self.desktop_cleaner, self.duplicate_finder]:
            module.progress_updated.connect(self._update_progress)

        self.organizer.organization_completed.connect(self._log_message)
        self.file_sorter.sorting_completed.connect(self._log_message)
        self.desktop_cleaner.cleaning_completed.connect(self._log_message)
        self.duplicate_finder.duplicates_found.connect(self._show_duplicates)

        # Сигналы для системы отмены
        self.organizer.operation_logged.connect(self.undo_manager.add_operation)
        self.desktop_cleaner.operation_logged.connect(self.undo_manager.add_operation)
        self.file_sorter.operation_logged.connect(self.undo_manager.add_operation)
        # --- ПОДКЛЮЧАЕМ СИГНАЛЫ ОТ UPDATER ---
        self.updater.update_available.connect(self._on_update_available)
        self.updater.up_to_date.connect(self._on_up_to_date)
        self.updater.error.connect(self._on_update_error)

    def _check_for_updates(self):
        """Запускает проверку обновлений в фоновом потоке."""
        self._log_message("Проверка наличия обновлений...")
        self.thread_manager.start_task(self.updater.check_for_updates)

    @pyqtSlot(str, str)
    def _on_update_available(self, new_version, download_url):
        """Вызывается, когда найдено обновление."""
        self._log_message(f"Найдено обновление: v{new_version}")
        reply = QMessageBox.information(
            self,
            "Доступно обновление!",
            f"Новая версия <b>v{new_version}</b> доступна для скачивания.<br><br>"
            "Хотите перейти на страницу загрузки?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            webbrowser.open(download_url)

    @pyqtSlot(str)
    def _on_up_to_date(self, message):
        """Вызывается, когда обновление не найдено."""
        self._log_message(message)
        QMessageBox.information(self, "Проверка обновлений", message)

    @pyqtSlot(str)
    def _on_update_error(self, message):
        """Вызывается при ошибке проверки."""
        self._log_message(f"Ошибка проверки обновлений: {message}")
        QMessageBox.warning(self, "Ошибка", message)

    # --- ИСПРАВЛЕННЫЙ МЕТОД ---
    def _show_about_dialog(self):
        """Показывает диалоговое окно 'О программе'."""
        QMessageBox.about(self, "О программе Piligrim  Desktop Manager v1.0.0",
                          "<b>Piligrim  Desktop Manager v1.0.0</b><br><br>"
                          "Эта программа помогает автоматически организовывать файлы на вашем рабочем столе.<br><br>"
                          "Автор: Зайцев Андрей Юрьевич."
                          )

    def _toggle_watcher(self, state):
        if state == Qt.Checked:
            if not self.watcher.isRunning():
                self.watcher.start()
        else:
            if self.watcher.isRunning():
                self.watcher.stop()

    def closeEvent(self, event):
        self._save_ui_settings_to_config()
        if self.watcher.isRunning():
            self.watcher.stop()
            self.watcher.wait(1000)
        super().closeEvent(event)

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

    def _organize_now(self):
        self._log_message("Запуск организации рабочего стола...")
        self.thread_manager.start_task(self.organizer.organize_all_desktops)

    def _on_clean_clicked(self):
        desktop = get_desktop_path()
        self._log_message(f"Запуск очистки для '{desktop}'...")
        self.thread_manager.start_task(self.desktop_cleaner.clean_desktop, desktop)

    def _on_sort_clicked(self):
        desktop = get_desktop_path()
        criteria = {"by_date": self.sort_date_cb.isChecked(), "by_type": self.sort_type_cb.isChecked()}
        if not any(criteria.values()):
            QMessageBox.warning(self, "Нет критерия", "Выберите хотя бы один критерий для сортировки.")
            return
        self._log_message(f"Запуск сортировки для '{desktop}'...")
        self.thread_manager.start_task(self.file_sorter.sort_desktop, desktop, criteria)

    def _on_find_duplicates(self):
        desktop = get_desktop_path()
        self._log_message(f"Поиск дубликатов в '{desktop}'...")
        self.thread_manager.start_task(self.duplicate_finder.find_duplicates, desktop)

    @pyqtSlot(dict)
    def _show_duplicates(self, duplicates):
        if not duplicates:
            QMessageBox.information(self, "Результат", "Дубликаты не найдены.")
            self._log_message("Поиск дубликатов завершен: ничего не найдено.")
            return
        self._log_message(f"Найдено {len(duplicates)} групп дубликатов. Открытие окна управления...")
        dialog = DuplicatesDialog(duplicates, self)
        dialog.exec_()
        self._log_message("Окно управления дубликатами закрыто.")

    def _manage_categories(self):
        dialog = CategoryManagerDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.get_updated_config()
            save_config(self.config)
            self.organizer.update_config(self.config)
            self.analyzer.update_config(self.config)
            self._log_message("Настройки категорий обновлены.")

    def _open_settings(self):
        old_theme = self.config.get("theme", "light")
        self._save_ui_settings_to_config()
        dialog = SettingsDialog(self.config, self)
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.get_config()
            save_config(self.config)
            self._load_settings_to_ui()
            self.organizer.update_config(self.config)
            self.desktop_cleaner.update_config(self.config)
            self.analyzer.update_config(self.config)
            self._log_message("Настройки сохранены.")
            new_theme = self.config.get("theme", "light")
            if old_theme != new_theme:
                QMessageBox.information(self, "Требуется перезапуск",
                                        "Для полного применения новой темы оформления, пожалуйста, перезапустите приложение.")

    def _undo_last_action(self):
        success, message = self.undo_manager.undo_last()
        self._log_message(message)

    def _analyze_desktop(self):
        self._log_message("Запуск анализа рабочего стола...")
        self.thread_manager.start_task(self.analyzer.analyze_desktop)

    @pyqtSlot(str, list)
    def _handle_suggestion(self, anomaly_type, details):
        if anomaly_type == "unclassified_extensions":
            ext_list = ", ".join(details)
            reply = QMessageBox.question(self, "Найдена аномалия",
                                         f"На рабочем столе найдено много файлов со следующими расширениями:\n{ext_list}\n\n"
                                         "Хотите создать для них новую категорию?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                name, ok = QInputDialog.getText(self, "Новая категория", "Введите название для новой категории:")
                if ok and name:
                    self.config['categories'][name] = details
                    save_config(self.config)
                    self.organizer.update_config(self.config)
                    self.analyzer.update_config(self.config)
                    self._log_message(f"Создана новая категория '{name}' для расширений: {ext_list}")

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
        reply = QMessageBox.question(self, "Подтверждение", f"Вы уверены, что хотите удалить профиль '{profile_name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.profile_manager.delete_profile(profile_name):
                self._log_message(f"Профиль '{profile_name}' удален.")
                self._update_profile_list()
            else:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить профиль '{profile_name}'.")