# ui/category_manager_dialog.py
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton,
    QInputDialog, QMessageBox, QLabel, QFileDialog
)

class CategoryManagerDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Управление категориями и иконками")
        self.setGeometry(300, 300, 550, 400)
        self._init_ui()
        self._load_categories()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)

        # Левая панель: Категории
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Категории:"))
        self.categories_list = QListWidget()
        self.categories_list.currentItemChanged.connect(self._on_category_selected)
        left_panel.addWidget(self.categories_list)

        cat_btn_layout = QVBoxLayout()
        add_edit_layout = QHBoxLayout()
        self.add_cat_btn = QPushButton("Добавить")
        self.edit_cat_btn = QPushButton("Изменить")
        add_edit_layout.addWidget(self.add_cat_btn)
        add_edit_layout.addWidget(self.edit_cat_btn)

        self.remove_cat_btn = QPushButton("Удалить категорию")
        self.change_icon_btn = QPushButton("Сменить иконку")
        self.change_icon_btn.setEnabled(False) # Изначально неактивна

        cat_btn_layout.addLayout(add_edit_layout)
        cat_btn_layout.addWidget(self.change_icon_btn)
        cat_btn_layout.addWidget(self.remove_cat_btn)
        left_panel.addLayout(cat_btn_layout)

        # Правая панель: Расширения
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("Расширения (напр., .txt .docx):"))
        self.extensions_list = QListWidget()
        right_panel.addWidget(self.extensions_list)

        ext_btn_layout = QHBoxLayout()
        self.add_ext_btn = QPushButton("Добавить")
        self.remove_ext_btn = QPushButton("Удалить")
        ext_btn_layout.addWidget(self.add_ext_btn)
        ext_btn_layout.addWidget(self.remove_ext_btn)
        right_panel.addLayout(ext_btn_layout)

        # Кнопки OK/Отмена
        dialog_buttons = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Отмена")
        dialog_buttons.addStretch()
        dialog_buttons.addWidget(self.ok_button)
        dialog_buttons.addWidget(self.cancel_button)

        outer_layout = QVBoxLayout()
        outer_layout.addLayout(main_layout)
        outer_layout.addLayout(dialog_buttons)
        self.setLayout(outer_layout)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)

        # Подключения
        self.add_cat_btn.clicked.connect(self._add_category)
        self.edit_cat_btn.clicked.connect(self._edit_category)
        self.remove_cat_btn.clicked.connect(self._remove_category)
        self.change_icon_btn.clicked.connect(self._change_icon)
        self.add_ext_btn.clicked.connect(self._add_extension)
        self.remove_ext_btn.clicked.connect(self._remove_extension)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def _load_categories(self):
        self.categories_list.clear()
        categories = self.config.get('categories', {})
        self.categories_list.addItems(sorted(categories.keys()))
        if self.categories_list.count() > 0:
            self.categories_list.setCurrentRow(0)

    def _on_category_selected(self, current_item):
        if not current_item:
            self.extensions_list.clear()
            self.change_icon_btn.setEnabled(False)
            return

        self.change_icon_btn.setEnabled(True)
        category_name = current_item.text()
        categories = self.config.get('categories', {})
        extensions = categories.get(category_name, [])

        self.extensions_list.clear()
        self.extensions_list.addItems(extensions)

    def _change_icon(self):
        selected_item = self.categories_list.currentItem()
        if not selected_item: return

        category_name = selected_item.text()
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите иконку", "", "Icon Files (*.ico)")

        if file_path:
            if 'category_icons' not in self.config:
                self.config['category_icons'] = {}
            self.config['category_icons'][category_name] = file_path
            QMessageBox.information(self, "Успех",
                                    f"Иконка для '{category_name}' установлена.\nИзменения будут применены при следующей организации.")

    def _add_category(self):
        name, ok = QInputDialog.getText(self, "Новая категория", "Введите название:")
        if ok and name:
            categories = self.config.get('categories', {})
            if name in categories:
                QMessageBox.warning(self, "Ошибка", "Такая категория уже существует.")
                return
            categories[name] = []
            self.config['categories'] = categories
            self._load_categories()
            # Находим и выбираем новый элемент
            items = self.categories_list.findItems(name, Qt.MatchExactly)
            if items:
                self.categories_list.setCurrentItem(items[0])

    def _edit_category(self):
        selected_item = self.categories_list.currentItem()
        if not selected_item: return

        old_name = selected_item.text()
        new_name, ok = QInputDialog.getText(self, "Редактирование", "Новое название:", text=old_name)
        if ok and new_name and new_name != old_name:
            categories = self.config.get('categories', {})
            if new_name in categories:
                QMessageBox.warning(self, "Ошибка", "Такая категория уже существует.")
                return
            categories[new_name] = categories.pop(old_name)
            self.config['categories'] = categories
            selected_item.setText(new_name)

    def _remove_category(self):
        selected_item = self.categories_list.currentItem()
        if not selected_item: return

        name = selected_item.text()
        if name == "Другое":
            QMessageBox.warning(self, "Запрещено", "Категорию 'Другое' нельзя удалить.")
            return

        reply = QMessageBox.question(self, "Подтверждение", f"Удалить категорию '{name}'?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            categories = self.config.get('categories', {})
            if name in categories:
                del categories[name]
                self.config['categories'] = categories
                self.categories_list.takeItem(self.categories_list.row(selected_item))

    def _add_extension(self):
        selected_cat = self.categories_list.currentItem()
        if not selected_cat: return

        category_name = selected_cat.text()
        ext, ok = QInputDialog.getText(self, "Новое расширение", "Введите расширение (напр., .zip):")
        if ok and ext:
            if not ext.startswith('.'): ext = '.' + ext
            ext = ext.lower()

            categories = self.config.get('categories', {})
            if ext not in categories[category_name]:
                categories[category_name].append(ext)
                self.extensions_list.addItem(ext)
            else:
                QMessageBox.warning(self, "Дубликат", "Это расширение уже есть в списке.")

    def _remove_extension(self):
        selected_cat = self.categories_list.currentItem()
        selected_ext = self.extensions_list.currentItem()
        if not selected_cat or not selected_ext: return

        category_name = selected_cat.text()
        ext_to_remove = selected_ext.text()

        categories = self.config.get('categories', {})
        if ext_to_remove in categories[category_name]:
            categories[category_name].remove(ext_to_remove)
            self.extensions_list.takeItem(self.extensions_list.row(selected_ext))

    def get_updated_config(self):
        return self.config