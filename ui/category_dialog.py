#ui/category_dialog.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QLabel, QInputDialog, QMessageBox
)


class CategoryDialog(QDialog):
    def __init__(self, classifier, parent=None):
        super().__init__(parent)
        self.classifier = classifier
        self.setWindowTitle("Управление категориями")
        self.resize(600, 400)

        self._init_ui()
        self._load_categories()

    def _init_ui(self):
        main_layout = QHBoxLayout()

        # Левая панель: список категорий
        left_layout = QVBoxLayout()
        self.categories_list = QListWidget()
        self.categories_list.currentItemChanged.connect(self._category_selected)
        left_layout.addWidget(QLabel("Категории:"))
        left_layout.addWidget(self.categories_list)

        # Кнопки управления категориями
        btn_layout = QHBoxLayout()
        self.add_category_btn = QPushButton("Добавить")
        self.remove_category_btn = QPushButton("Удалить")
        self.rename_category_btn = QPushButton("Переименовать")

        btn_layout.addWidget(self.add_category_btn)
        btn_layout.addWidget(self.remove_category_btn)
        btn_layout.addWidget(self.rename_category_btn)
        left_layout.addLayout(btn_layout)

        # Правая панель: расширения категории
        right_layout = QVBoxLayout()
        self.extensions_list = QListWidget()
        right_layout.addWidget(QLabel("Расширения:"))
        right_layout.addWidget(self.extensions_list)

        # Кнопки управления расширениями
        ext_btn_layout = QHBoxLayout()
        self.add_extension_btn = QPushButton("Добавить")
        self.remove_extension_btn = QPushButton("Удалить")

        ext_btn_layout.addWidget(self.add_extension_btn)
        ext_btn_layout.addWidget(self.remove_extension_btn)
        right_layout.addLayout(ext_btn_layout)

        # Исключения
        self.exceptions_list = QListWidget()
        right_layout.addWidget(QLabel("Исключения:"))
        right_layout.addWidget(self.exceptions_list)

        # Кнопки управления исключениями
        exc_btn_layout = QHBoxLayout()
        self.add_exception_btn = QPushButton("Добавить")
        self.remove_exception_btn = QPushButton("Удалить")

        exc_btn_layout.addWidget(self.add_exception_btn)
        exc_btn_layout.addWidget(self.remove_exception_btn)
        right_layout.addLayout(exc_btn_layout)

        # Кнопки диалога
        dialog_btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Отмена")

        dialog_btn_layout.addWidget(self.ok_btn)
        dialog_btn_layout.addWidget(self.cancel_btn)
        right_layout.addLayout(dialog_btn_layout)

        # Компоновка
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)
        self.setLayout(main_layout)

        # Подключим сигналы
        self.add_category_btn.clicked.connect(self._add_category)
        self.remove_category_btn.clicked.connect(self._remove_category)
        self.rename_category_btn.clicked.connect(self._rename_category)
        self.add_extension_btn.clicked.connect(self._add_extension)
        self.remove_extension_btn.clicked.connect(self._remove_extension)
        self.add_exception_btn.clicked.connect(self._add_exception)
        self.remove_exception_btn.clicked.connect(self._remove_exception)
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

    def _load_categories(self):
        self.categories_list.clear()
        for category in self.classifier.categories:
            self.categories_list.addItem(category)

        if self.categories_list.count() > 0:
            self.categories_list.setCurrentRow(0)

    def _category_selected(self, current, previous):
        if current:
            category = current.text()
            self._update_extensions_list(category)
            self._update_exceptions_list()

    def _update_extensions_list(self, category):
        self.extensions_list.clear()
        if category in self.classifier.categories:
            for ext in self.classifier.categories[category]:
                self.extensions_list.addItem(ext)

    def _update_exceptions_list(self):
        self.exceptions_list.clear()
        for exc in self.classifier.exceptions:
            self.exceptions_list.addItem(exc)

    def _add_category(self):
        name, ok = QInputDialog.getText(self, "Новая категория", "Введите название категории:")
        if ok and name:
            if name not in self.classifier.categories:
                self.classifier.add_category(name, [])
                self.categories_list.addItem(name)
                self.categories_list.setCurrentRow(self.categories_list.count() - 1)
            else:
                QMessageBox.warning(self, "Ошибка", "Категория с таким именем уже существует")

    def _remove_category(self):
        current = self.categories_list.currentItem()
        if current:
            category = current.text()
            if self.classifier.remove_category(category):
                self.categories_list.takeItem(self.categories_list.row(current))

    def _rename_category(self):
        current = self.categories_list.currentItem()
        if current:
            old_name = current.text()
            new_name, ok = QInputDialog.getText(self, "Переименование", "Новое название:", text=old_name)
            if ok and new_name and new_name != old_name:
                if new_name not in self.classifier.categories:
                    # Сохраняем расширения
                    extensions = self.classifier.categories[old_name]
                    self.classifier.remove_category(old_name)
                    self.classifier.add_category(new_name, extensions)
                    current.setText(new_name)
                else:
                    QMessageBox.warning(self, "Ошибка", "Категория с таким именем уже существует")

    def _add_extension(self):
        current = self.categories_list.currentItem()
        if current:
            category = current.text()
            ext, ok = QInputDialog.getText(self, "Добавить расширение", "Введите расширение (например, .txt):")
            if ok and ext:
                if not ext.startswith("."):
                    ext = "." + ext
                if self.classifier.add_extension(category, ext.lower()):
                    self._update_extensions_list(category)

    def _remove_extension(self):
        current_ext = self.extensions_list.currentItem()
        current_cat = self.categories_list.currentItem()
        if current_ext and current_cat:
            ext = current_ext.text()
            category = current_cat.text()
            if category in self.classifier.categories and ext in self.classifier.categories[category]:
                self.classifier.categories[category].remove(ext)
                self._update_extensions_list(category)

    def _add_exception(self):
        file_name, ok = QInputDialog.getText(self, "Добавить исключение", "Имя файла:")
        if ok and file_name:
            if self.classifier.add_exception(file_name):
                self._update_exceptions_list()

    def _remove_exception(self):
        current = self.exceptions_list.currentItem()
        if current:
            file_name = current.text()
            if self.classifier.remove_exception(file_name):
                self.exceptions_list.takeItem(self.exceptions_list.row(current))