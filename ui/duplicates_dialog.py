# ui/duplicates_dialog.py
import os
import logging
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QMessageBox, QLabel
)


class DuplicatesDialog(QDialog):
    def __init__(self, duplicates_dict, parent=None):
        super().__init__(parent)
        self.duplicates = duplicates_dict
        self.logger = logging.getLogger(__name__)
        self.setWindowTitle("Найденные дубликаты файлов")
        self.setGeometry(150, 150, 800, 600)
        self._init_ui()
        self._populate_tree()

    def _init_ui(self):
        """Создает элементы интерфейса окна."""
        main_layout = QVBoxLayout(self)

        # Информационная метка
        info_label = QLabel(
            "Ниже представлены группы одинаковых файлов. "
            "Оставьте хотя бы один файл в каждой группе.\n"
            "Отметьте галочками файлы, которые хотите удалить."
        )
        main_layout.addWidget(info_label)

        # Дерево для отображения дубликатов
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Имя файла", "Путь к файлу"])
        self.tree.setColumnWidth(0, 250)  # Устанавливаем ширину колонок
        main_layout.addWidget(self.tree)

        # Кнопки управления
        button_layout = QHBoxLayout()
        button_layout.addStretch()  # Пустое пространство, чтобы кнопки были справа
        self.delete_btn = QPushButton("Удалить выбранные")
        self.close_btn = QPushButton("Закрыть")
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.close_btn)
        main_layout.addLayout(button_layout)

        # Подключение сигналов к методам
        self.delete_btn.clicked.connect(self._delete_selected_files)
        self.close_btn.clicked.connect(self.accept)

    def _populate_tree(self):
        """Заполняет дерево данными о дубликатах."""
        self.tree.clear()

        for group_index, (hash_val, files) in enumerate(self.duplicates.items()):
            # Создаем корневой элемент для группы дубликатов
            group_item = QTreeWidgetItem(self.tree)
            group_item.setText(0, f"Группа {group_index + 1} ({len(files)} файла)")
            group_item.setFlags(group_item.flags() & ~Qt.ItemIsUserCheckable)  # Группу нельзя выбрать

            # Добавляем файлы как дочерние элементы
            for i, filepath in enumerate(files):
                file_item = QTreeWidgetItem(group_item)
                file_item.setText(0, os.path.basename(filepath))
                file_item.setText(1, os.path.dirname(filepath))

                # Сохраняем полный путь к файлу внутри элемента. Это надежнее, чем брать его из текста.
                file_item.setData(0, Qt.UserRole, filepath)

                # Делаем элемент "выбираемым" с помощью чекбокса
                file_item.setFlags(file_item.flags() | Qt.ItemIsUserCheckable)

                # Важная мера предосторожности:
                # Первый файл в группе по умолчанию не выбран и не может быть удален,
                # чтобы пользователь случайно не удалил все копии файла.
                if i == 0:
                    file_item.setCheckState(0, Qt.Unchecked)
                else:
                    file_item.setCheckState(0, Qt.Checked)  # Остальные предлагаем к удалению

    def _delete_selected_files(self):
        """Собирает все отмеченные файлы и удаляет их после подтверждения."""
        files_to_delete = []
        root = self.tree.invisibleRootItem()

        # Проходим по всем группам в дереве
        for i in range(root.childCount()):
            group_item = root.child(i)
            # Проходим по всем файлам в группе
            for j in range(group_item.childCount()):
                file_item = group_item.child(j)
                # Если файл отмечен галочкой
                if file_item.checkState(0) == Qt.Checked:
                    # Получаем сохраненный ранее путь к файлу
                    filepath = file_item.data(0, Qt.UserRole)
                    files_to_delete.append(filepath)

        if not files_to_delete:
            QMessageBox.warning(self, "Ничего не выбрано", "Пожалуйста, отметьте файлы для удаления.")
            return

        # Запрашиваем подтверждение у пользователя
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы уверены, что хотите навсегда удалить {len(files_to_delete)} файлов?\n"
            "Эта операция необратима.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            deleted_count = 0
            errors = []
            for f in files_to_delete:
                try:
                    os.remove(f)
                    deleted_count += 1
                    self.logger.info(f"Дубликат удален: {f}")
                except Exception as e:
                    errors.append(os.path.basename(f))
                    self.logger.error(f"Не удалось удалить дубликат {f}: {e}")

            # Показываем финальный отчет
            if not errors:
                QMessageBox.information(self, "Успех", f"Успешно удалено {deleted_count} файлов.")
            else:
                QMessageBox.warning(self, "Завершено с ошибками",
                                    f"Удалено: {deleted_count} файлов.\n"
                                    f"Не удалось удалить: {', '.join(errors)}")

            # Закрываем диалог после удаления
            self.accept()