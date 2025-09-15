# Файл: ui/main_window.py
import logging
from datetime import datetime

from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QKeySequence, QFont
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QStackedWidget, QPushButton, QListWidget, QCheckBox,
                             QInputDialog, QComboBox, QSlider,
                             QColorDialog, QTableWidget, QFormLayout, QLabel,
                             QLineEdit, QListWidgetItem, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QMessageBox, QFrame,
                             QRadioButton, QButtonGroup, QFileDialog, QFontDialog, QSizePolicy,
                             QSpinBox)

from core.snapshot_manager import SnapshotManager
from core.utils import save_config
from ui.rules_dialog import RulesDialog


class HotkeyLineEdit(QLineEdit):
    hotkey_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Нажмите комбинацию клавиш...")
        self.setReadOnly(True)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta): return
        modifiers = event.modifiers()
        mod_str = ""
        if modifiers & Qt.ControlModifier: mod_str += "ctrl+"
        if modifiers & Qt.AltModifier: mod_str += "alt+"
        if modifiers & Qt.ShiftModifier: mod_str += "shift+"
        key_text = QKeySequence(key).toString().lower()
        if key_text not in ('ctrl', 'alt', 'shift'):
            full_sequence = mod_str + key_text
            self.setText(full_sequence)
            self.hotkey_changed.emit(full_sequence)
        event.accept()


class MainWindow(QMainWindow):
    def __init__(self, config, box_manager, hotkey_manager, wallpaper_manager, version, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.box_manager = box_manager
        self.hotkey_manager = hotkey_manager
        self.wallpaper_manager = wallpaper_manager
        self.version = version
        self.snapshot_manager = SnapshotManager(self.box_manager)

        self.setWindowTitle(f"iTop Easy Desktop v{self.version}")
        self.setMinimumSize(850, 650)
        self.setWindowIcon(QIcon(":/icons/app_icon.png"))

        self._init_ui()
        self._connect_signals()
        self._load_initial_state()
        self.logger.info("Главное окно успешно инициализировано.")

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.side_menu = self._create_side_menu()
        main_layout.addWidget(self.side_menu)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.pages = {
            "boxes": self._create_boxes_page(),
            "organization": self._create_organization_page(),
            "snapshots": self._create_snapshots_page(),
            "wallpapers": self._create_wallpapers_page(),
            "widgets": self._create_widgets_page(),
            "search": self._create_search_page(),
            "hotkeys": self._create_hotkeys_page(),
        }
        for page in self.pages.values():
            self.stacked_widget.addWidget(page)

    def _create_side_menu(self):
        menu_list = QListWidget()
        menu_list.setObjectName("SideMenu")
        menu_list.setFixedWidth(180)
        menu_list.setIconSize(QSize(24, 24))

        self.nav_items = {
            "boxes": QListWidgetItem(QIcon(":/icons/box.png"), "Ящики"),
            "organization": QListWidgetItem(QIcon(":/icons/rules.png"), "Организация"),
            "snapshots": QListWidgetItem(QIcon(":/icons/snapshot.png"), "Макет и Снимок"),
            "wallpapers": QListWidgetItem(QIcon(":/icons/wallpaper.png"), "Обои"),
            "widgets": QListWidgetItem(QIcon(":/icons/widgets.png"), "Виджеты"),
            "search": QListWidgetItem(QIcon(":/icons/search.png"), "Поиск"),
            "hotkeys": QListWidgetItem(QIcon(":/icons/hotkey.png"), "Быстрые действия"),
        }
        for item in self.nav_items.values():
            item.setSizeHint(QSize(-1, 40))
            menu_list.addItem(item)
        return menu_list

    def _create_boxes_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignTop)
        self.enable_boxes_switch = QCheckBox("Включить Ящики на рабочем столе")
        layout.addWidget(self.enable_boxes_switch)
        self.boxes_list_widget = QListWidget()
        self.boxes_list_widget.setFixedHeight(100)
        layout.addWidget(self.boxes_list_widget)
        buttons_layout = QHBoxLayout()
        self.add_box_btn = QPushButton(QIcon(":/icons/add.png"), "Добавить")
        self.delete_box_btn = QPushButton(QIcon(":/icons/delete.png"), "Удалить")
        buttons_layout.addWidget(self.add_box_btn)
        buttons_layout.addWidget(self.delete_box_btn)
        layout.addLayout(buttons_layout)
        layout.addWidget(QFrame(self))

        form_layout = QFormLayout()

        form_layout.addRow(QLabel("<b>Индивидуальные настройки ящика:</b>"))
        self.appearance_box_selector = QComboBox()
        form_layout.addRow("Настроить ящик:", self.appearance_box_selector)

        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 2000)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 2000)
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Ширина:"))
        size_layout.addWidget(self.width_spin)
        size_layout.addWidget(QLabel("Высота:"))
        size_layout.addWidget(self.height_spin)
        form_layout.addRow("Размер:", size_layout)

        self.color_btn = QPushButton("Выбрать цвет...")
        form_layout.addRow("Цвет фона:", self.color_btn)
        self.font_btn = QPushButton("Настроить шрифт")
        self.font_label = QLabel("Segoe UI, 16")
        font_layout = QHBoxLayout()
        font_layout.addWidget(self.font_label)
        font_layout.addWidget(self.font_btn)
        form_layout.addRow("Шрифт заголовка:", font_layout)

        form_layout.addRow(QLabel("<b>Глобальные настройки для всех ящиков:</b>"))
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setRange(0, 100)
        form_layout.addRow("Прозрачность фона:", self.transparency_slider)

        # --- НАЧАЛО ИЗМЕНЕНИЯ: Переносим управление заголовком в глобальные настройки ---
        self.header_visibility_group = QButtonGroup(self)
        rb_always = QRadioButton("Всегда")
        rb_hover = QRadioButton("При наведении")
        rb_never = QRadioButton("Никогда")
        self.header_visibility_group.addButton(rb_always, 0)
        self.header_visibility_group.addButton(rb_hover, 1)
        self.header_visibility_group.addButton(rb_never, 2)
        header_layout = QHBoxLayout()
        header_layout.addWidget(rb_always)
        header_layout.addWidget(rb_hover)
        header_layout.addWidget(rb_never)
        form_layout.addRow("Показывать заголовок:", header_layout)
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---

        self.border_check = QCheckBox("Включить границу")
        form_layout.addRow(self.border_check)
        self.border_color_btn = QPushButton("Выбрать цвет границы...")
        form_layout.addRow("Цвет границы:", self.border_color_btn)
        self.border_width_spin = QSpinBox()
        self.border_width_spin.setRange(1, 10)
        self.border_width_spin.setSuffix(" px")
        form_layout.addRow("Толщина границы:", self.border_width_spin)

        layout.addLayout(form_layout)
        return page

    def _create_organization_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Продвинутые правила автоматической сортировки."))
        self.add_rule_btn = QPushButton(QIcon(":/icons/add.png"), "Добавить правило")
        self.edit_rule_btn = QPushButton(QIcon(":/icons/edit.png"), "Редактировать")
        self.delete_rule_btn = QPushButton(QIcon(":/icons/delete.png"), "Удалить")
        self.rules_list_widget = QListWidget()
        layout.addWidget(self.rules_list_widget)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.add_rule_btn)
        btn_layout.addWidget(self.edit_rule_btn)
        btn_layout.addWidget(self.delete_rule_btn)
        layout.addLayout(btn_layout)
        return page

    def _create_snapshots_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.create_snapshot_btn = QPushButton(QIcon(":/icons/add.png"), "Создать новый снимок")
        layout.addWidget(self.create_snapshot_btn)
        self.snapshots_table = QTableWidget()
        self.snapshots_table.setColumnCount(3)
        self.snapshots_table.setHorizontalHeaderLabels(["Имя", "Дата создания", "Действия"])
        self.snapshots_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.snapshots_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.snapshots_table)
        return page

    def _create_wallpapers_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Управление обоями рабочего стола."))
        self.static_wallpaper_btn = QPushButton("Выбрать статичные обои (картинку)")
        self.solid_color_btn = QPushButton("Выбрать сплошной цвет")
        layout.addWidget(self.static_wallpaper_btn)
        layout.addWidget(self.solid_color_btn)
        return page

    def _create_widgets_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Галерея виджетов (функционал в разработке)."))
        return page

    def _create_search_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel("Настройки поиска (функционал в разработке)."))
        return page

    def _create_hotkeys_page(self):
        page = QWidget()
        layout = QFormLayout(page)
        self.toggle_boxes_hotkey_edit = HotkeyLineEdit()
        layout.addRow("Скрыть/показать все ящики:", self.toggle_boxes_hotkey_edit)
        self.open_search_hotkey_edit = HotkeyLineEdit()
        layout.addRow("Открыть поиск (будущая функция):", self.open_search_hotkey_edit)
        return page

    def _connect_signals(self):
        self.side_menu.currentItemChanged.connect(self._on_nav_item_changed)
        self.enable_boxes_switch.stateChanged.connect(self._toggle_boxes_visibility)
        self.add_box_btn.clicked.connect(self._add_new_box)
        self.delete_box_btn.clicked.connect(self._delete_selected_box)
        self.box_manager.boxes_updated.connect(self.update_boxes_list)
        self.appearance_box_selector.currentIndexChanged.connect(self._load_box_appearance_settings)
        self.color_btn.clicked.connect(self._select_box_color)
        self.font_btn.clicked.connect(self._select_box_font)
        self.box_manager.boxes_updated.connect(self._update_appearance_box_selector)
        self.add_rule_btn.clicked.connect(self._add_rule)
        self.edit_rule_btn.clicked.connect(self._edit_rule)
        self.delete_rule_btn.clicked.connect(self._delete_rule)
        self.create_snapshot_btn.clicked.connect(self._create_new_snapshot)
        self.static_wallpaper_btn.clicked.connect(self._select_static_wallpaper)
        self.solid_color_btn.clicked.connect(self._select_solid_color)
        self.toggle_boxes_hotkey_edit.hotkey_changed.connect(lambda seq: self._save_hotkey("show_hide_boxes", seq))
        self.open_search_hotkey_edit.hotkey_changed.connect(lambda seq: self._save_hotkey("open_search", seq))

        self.box_manager.request_open_settings.connect(self.open_settings_for_box)
        self.box_manager.request_rename_box.connect(self.rename_box)
        self.box_manager.request_delete_box.connect(self.delete_box_from_menu)
        self.box_manager.request_create_new_box.connect(self._add_new_box)
        self.box_manager.state_changed.connect(self.box_manager.update_box_properties)

        self.border_check.stateChanged.connect(self._on_global_border_setting_changed)
        self.border_color_btn.clicked.connect(self._select_border_color)
        self.border_width_spin.valueChanged.connect(self._on_global_border_setting_changed)

        self.width_spin.valueChanged.connect(self._on_appearance_setting_changed)
        self.height_spin.valueChanged.connect(self._on_appearance_setting_changed)

        self.transparency_slider.valueChanged.connect(self._on_global_appearance_setting_changed)
        self.header_visibility_group.buttonClicked.connect(self._on_global_appearance_setting_changed)

    def _load_initial_state(self):
        self.enable_boxes_switch.setChecked(self.config.get("boxes_enabled", True))
        self.update_boxes_list()
        self._update_appearance_box_selector()
        self._populate_rules_list()
        self._load_hotkeys()
        self._load_global_settings()
        self.box_manager.load_boxes()
        self.side_menu.setCurrentRow(0)

    def open_settings_for_box(self, box_id: str):
        self.logger.info(f"Получен запрос на открытие настроек для ящика {box_id}")
        self.show()
        self.raise_()
        self.activateWindow()
        boxes_item = self.nav_items["boxes"]
        self.side_menu.setCurrentItem(boxes_item)
        index = self.appearance_box_selector.findData(box_id)
        if index != -1:
            self.appearance_box_selector.setCurrentIndex(index)
        else:
            self.logger.warning(f"Не удалось найти ящик с ID {box_id} в списке настроек.")

    def rename_box(self, box_id: str, current_name: str):
        new_name, ok = QInputDialog.getText(self, "Переименовать ящик", "Новое имя:", text=current_name)
        if ok and new_name and new_name != current_name:
            self.box_manager.update_box_properties(box_id, {"name": new_name})
            self.box_manager.update_box_visuals(box_id)
            self.update_boxes_list()
            self._update_appearance_box_selector()

    def delete_box_from_menu(self, box_id: str):
        reply = QMessageBox.question(self, "Подтверждение", "Вы уверены, что хотите удалить этот ящик?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.box_manager.delete_box(box_id)

    def _on_nav_item_changed(self, current, previous):
        page_name = list(self.nav_items.keys())[self.side_menu.row(current)]
        self.stacked_widget.setCurrentWidget(self.pages[page_name])
        if page_name == "snapshots":
            self.populate_snapshots_table()
        elif page_name == "organization":
            self._populate_rules_list()

    def _toggle_boxes_visibility(self, state):
        self.config["boxes_enabled"] = (state == Qt.Checked)
        if self.config["boxes_enabled"]:
            self.box_manager.show_all_boxes()
        else:
            self.box_manager.hide_all_boxes()

    def update_boxes_list(self):
        self.boxes_list_widget.clear()
        for box in self.config.get("desktop_boxes", []):
            item = QListWidgetItem(box["name"])
            item.setData(Qt.UserRole, box["id"])
            self.boxes_list_widget.addItem(item)

    def _add_new_box(self):
        name, ok = QInputDialog.getText(self, "Создать ящик", "Введите имя нового ящика:")
        if ok and name: self.box_manager.create_box(name)

    def _delete_selected_box(self):
        selected = self.boxes_list_widget.currentItem()
        if not selected: return
        self.delete_box_from_menu(selected.data(Qt.UserRole))

    def _update_appearance_box_selector(self):
        current_id = self.appearance_box_selector.currentData()
        self.appearance_box_selector.blockSignals(True)
        self.appearance_box_selector.clear()
        for box in self.config.get("desktop_boxes", []):
            self.appearance_box_selector.addItem(box["name"], box["id"])
        index = self.appearance_box_selector.findData(current_id)
        self.appearance_box_selector.setCurrentIndex(index if index != -1 else 0)
        self.appearance_box_selector.blockSignals(False)
        if self.appearance_box_selector.count() > 0: self._load_box_appearance_settings()

    def _load_box_appearance_settings(self):
        box_id = self.appearance_box_selector.currentData()
        if not box_id: return
        box_conf = next((b for b in self.config["desktop_boxes"] if b["id"] == box_id), None)
        if not box_conf: return

        appearance = box_conf.get("appearance", {})
        self.width_spin.blockSignals(True)
        self.height_spin.blockSignals(True)

        color = QColor(appearance.get("color", "#2D2D2D"))
        self.color_btn.setStyleSheet(f"background-color: {color.name()};")
        font_str = appearance.get("font", "Segoe UI,16")
        self.font_label.setText(font_str)
        try:
            font_parts = font_str.split(',')
            font_family = font_parts[0].strip()
            font_size = int(font_parts[1].strip())
            self.font_label.setFont(QFont(font_family, font_size))
        except (IndexError, ValueError) as e:
            self.logger.warning(f"Не удалось разобрать строку шрифта '{font_str}': {e}.")
            self.font_label.setFont(QFont("Segoe UI", 16))

        size = box_conf.get("size", [250, 300])
        self.width_spin.setValue(size[0])
        self.height_spin.setValue(size[1])

        self.width_spin.blockSignals(False)
        self.height_spin.blockSignals(False)

    def _load_global_settings(self):
        border_settings = self.config.get("global_border_settings", {})
        appearance_settings = self.config.get("global_appearance_settings", {})

        self.border_check.blockSignals(True)
        self.border_width_spin.blockSignals(True)
        self.transparency_slider.blockSignals(True)
        self.header_visibility_group.blockSignals(True)

        self.border_check.setChecked(border_settings.get("enabled", False))
        border_color = QColor(border_settings.get("color", "#000000"))
        self.border_color_btn.setStyleSheet(f"background-color: {border_color.name()};")
        self.border_width_spin.setValue(border_settings.get("width", 1))
        self.transparency_slider.setValue(appearance_settings.get("transparency_bg", 85))

        vis_map = {"always": 0, "on_hover": 1, "never": 2}
        vis_id = vis_map.get(appearance_settings.get("header_visibility", "always"), 0)
        self.header_visibility_group.button(vis_id).setChecked(True)

        self.border_check.blockSignals(False)
        self.border_width_spin.blockSignals(False)
        self.transparency_slider.blockSignals(False)
        self.header_visibility_group.blockSignals(False)

    def _select_border_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.border_color_btn.setStyleSheet(f"background-color: {color.name()};")
            self._on_global_border_setting_changed()

    def _on_global_border_setting_changed(self):
        border_color_str = self.border_color_btn.styleSheet().split(":")[1].strip().rstrip(';')
        new_settings = {
            "enabled": self.border_check.isChecked(),
            "color": QColor(border_color_str).name(),
            "width": self.border_width_spin.value()
        }
        self.config["global_border_settings"] = new_settings
        save_config(self.config)
        self.box_manager.refresh_all_visuals()

    def _on_global_appearance_setting_changed(self):
        vis_map = {0: "always", 1: "on_hover", 2: "never"}
        header_vis = vis_map.get(self.header_visibility_group.checkedId(), "always")

        new_settings = {
            "transparency_bg": self.transparency_slider.value(),
            "header_visibility": header_vis
        }
        if "global_appearance_settings" not in self.config:
            self.config["global_appearance_settings"] = {}
        self.config["global_appearance_settings"].update(new_settings)
        save_config(self.config)
        self.box_manager.refresh_all_visuals()

    def _select_box_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_btn.setStyleSheet(f"background-color: {color.name()};")
            self._on_appearance_setting_changed()

    def _select_box_font(self):
        try:
            font_str = self.font_label.text().split(',')
            current_font = QFont(font_str[0], int(font_str[1]))
        except (IndexError, ValueError):
            current_font = QFont("Segoe UI", 16)
        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            self.font_label.setText(f"{font.family()},{font.pointSize()}")
            self.font_label.setFont(font)
            self._on_appearance_setting_changed()

    def _on_appearance_setting_changed(self):
        box_id = self.appearance_box_selector.currentData()
        if not box_id: return

        color_str_from_style = self.color_btn.styleSheet().split(":")[1].strip().rstrip(';')

        new_appearance = {
            "color": QColor(color_str_from_style).name(),
            "font": self.font_label.text()
        }

        new_size = [self.width_spin.value(), self.height_spin.value()]
        self.logger.info(f"UI инициировал изменение настроек для ящика {box_id}: {new_appearance}, Размер: {new_size}")

        self.box_manager.update_box_properties(box_id, {"appearance": new_appearance, "size": new_size})
        self.box_manager.update_box_visuals(box_id)

    def _populate_rules_list(self):
        self.rules_list_widget.clear()
        for index, rule in enumerate(self.config.get("advanced_rules", [])):
            item = QListWidgetItem(rule["name"])
            item.setData(Qt.UserRole, index)
            self.rules_list_widget.addItem(item)

    def _add_rule(self):
        new_rule, ok = RulesDialog.edit_rule(self.config, parent=self)
        if ok and new_rule:
            if "advanced_rules" not in self.config: self.config["advanced_rules"] = []
            self.config["advanced_rules"].append(new_rule)
            save_config(self.config)
            self._populate_rules_list()

    def _edit_rule(self):
        selected = self.rules_list_widget.currentItem()
        if not selected: return
        rule_index = selected.data(Qt.UserRole)
        rule = self.config["advanced_rules"][rule_index]
        updated_rule, ok = RulesDialog.edit_rule(self.config, rule=rule, parent=self)
        if ok and updated_rule:
            self.config["advanced_rules"][rule_index] = updated_rule
            save_config(self.config)
            self._populate_rules_list()

    def _delete_rule(self):
        selected = self.rules_list_widget.currentItem()
        if not selected: return
        if QMessageBox.question(self, "Подтверждение", "Удалить правило?") == QMessageBox.Yes:
            self.config["advanced_rules"].pop(selected.data(Qt.UserRole))
            save_config(self.config)
            self._populate_rules_list()

    def populate_snapshots_table(self):
        self.snapshots_table.setRowCount(0)
        for row, snap in enumerate(self.snapshot_manager.list_snapshots()):
            self.snapshots_table.insertRow(row)
            self.snapshots_table.setItem(row, 0, QTableWidgetItem(snap["name"]))
            date = datetime.fromisoformat(snap["date"]).strftime('%Y-%m-%d %H:%M')
            self.snapshots_table.setItem(row, 1, QTableWidgetItem(date))
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            restore_btn = QPushButton("Восстановить")
            delete_btn = QPushButton("Удалить")
            restore_btn.clicked.connect(lambda ch, fn=snap['filename']: self._restore_snapshot(fn))
            delete_btn.clicked.connect(lambda ch, fn=snap['filename']: self._delete_snapshot(fn))
            actions_layout.addWidget(restore_btn)
            actions_layout.addWidget(delete_btn)
            self.snapshots_table.setCellWidget(row, 2, actions_widget)

    def _create_new_snapshot(self):
        name, ok = QInputDialog.getText(self, "Создать снимок", "Имя снимка:")
        if ok and name:
            success, msg = self.snapshot_manager.create_snapshot(name)
            if success:
                self.populate_snapshots_table()
            else:
                QMessageBox.critical(self, "Ошибка", msg)

    def _restore_snapshot(self, fn):
        if QMessageBox.question(self, "Подтверждение", "Восстановить?") == QMessageBox.Yes:
            success, msg = self.snapshot_manager.restore_snapshot(fn)
            if not success: QMessageBox.critical(self, "Ошибка", msg)

    def _delete_snapshot(self, fn):
        if QMessageBox.question(self, "Подтверждение", "Удалить?") == QMessageBox.Yes:
            if self.snapshot_manager.delete_snapshot(fn): self.populate_snapshots_table()

    def _select_static_wallpaper(self):
        file, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", "", "Images (*.png *.jpg *.bmp)")
        if file:
            success, msg = self.wallpaper_manager.set_wallpaper(file)
            if not success: QMessageBox.critical(self, "Ошибка", msg)

    def _select_solid_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            success, msg = self.wallpaper_manager.set_solid_color(color.name())
            if not success: QMessageBox.critical(self, "Ошибка", msg)

    def _load_hotkeys(self):
        hotkeys = self.config.get("hotkeys", {})
        self.toggle_boxes_hotkey_edit.setText(hotkeys.get("show_hide_boxes", ""))
        self.open_search_hotkey_edit.setText(hotkeys.get("open_search", ""))

    def _save_hotkey(self, action, sequence):
        self.config["hotkeys"][action] = sequence
        self.hotkey_manager.stop()
        self.hotkey_manager.listener = type(self.hotkey_manager.listener)(self.config.get("hotkeys", {}))
        self.hotkey_manager.thread.started.connect(self.hotkey_manager.listener.run)
        self.hotkey_manager.listener.toggle_boxes_visibility.connect(self.box_manager.toggle_visibility)
        self.hotkey_manager.start()

    def closeEvent(self, event):
        save_config(self.config)
        self.logger.info("Конфигурация сохранена. Приложение закрывается.")
        super().closeEvent(event)