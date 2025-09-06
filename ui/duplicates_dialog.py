# ui/duplicates_dialog.py
import os
from pathlib import Path
from send2trash import send2trash
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QTreeWidget, QTreeWidgetItem, QLabel, QHeaderView, QTreeWidgetItemIterator
)
from PyQt5.QtCore import Qt



class DuplicatesDialog(QDialog):
    def __init__(self, duplicates_data: dict, parent=None):
        super().__init__(parent)
        self.duplicates_data = duplicates_data
        self.setWindowTitle("Найденные дубликаты файлов")
        self.setGeometry(150, 150, 700, 500)
        self._init_ui()
        self._populate_tree()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        info_label = QLabel(
            "Ниже представлены группы дубликатов. В каждой группе оставьте хотя бы один файл.\n"
            "Отметьте файлы, которые вы хотите удалить."
        )
        layout.addWidget(info_label)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Файл", "Путь"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        layout.addWidget(self.tree)

        button_layout = QHBoxLayout()
        self.delete_button = QPushButton("Переместить в корзину")
        self.close_button = QPushButton("Закрыть")
        button_layout.addStretch()
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.delete_button.clicked.connect(self._delete_selected)
        self.close_button.clicked.connect(self.accept)

    def _populate_tree(self):
        """Заполняет дерево данными о дубликатах."""
        for i, (file_hash, files) in enumerate(self.duplicates_data.items()):
            # Родительский элемент для группы
            group_item = QTreeWidgetItem(self.tree, [f"Группа {i + 1} ({len(files)} файла)"])
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsSelectable)  # Нельзя выбрать саму группу

            # Дочерние элементы - файлы
            for filepath_str in files:
                filepath = Path(filepath_str)
                file_item = QTreeWidgetItem(group_item, [filepath.name, str(filepath.parent)])
                file_item.setFlags(file_item.flags() | Qt.ItemIsUserCheckable)
                # Первый файл в группе оставляем неотмеченным по умолчанию
                if files.index(filepath_str) == 0:
                    file_item.setCheckState(0, Qt.Unchecked)
                else:
                    file_item.setCheckState(0, Qt.Checked)  # Остальные отмечаем для удаления

                file_item.setData(0, Qt.UserRole, filepath_str)  # Сохраняем полный путь

        self.tree.expandAll()

    def _delete_selected(self):
        """Собирает отмеченные файлы и предлагает их удалить."""
        files_to_delete = []
        iterator = QTreeWidgetItemIterator(self.tree)
        while iterator.value():
            item = iterator.value()
            if item.checkState(0) == Qt.Checked:
                full_path = item.data(0, Qt.UserRole)
                if full_path:
                    files_to_delete.append(full_path)
            iterator += 1

        if not files_to_delete:
            QMessageBox.warning(self, "Ничего не выбрано", "Пожалуйста, отметьте файлы для удаления.")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Вы уверены, что хотите переместить {len(files_to_delete)} файлов в Корзину?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted_count = 0
            errors = []
            for f in files_to_delete:
                try:
                    send2trash(f)
                    deleted_count += 1
                except Exception as e:  # send2trash может вызвать разные ошибки
                    errors.append(f"{Path(f).name}: {e}")

            summary_message = f"Перемещено в корзину {deleted_count} из {len(files_to_delete)} файлов."
            if errors:
                summary_message += "\n\nПроизошли следующие ошибки:\n" + "\n".join(errors)

            QMessageBox.information(self, "Результат", summary_message)
            self.accept()