# Файл: ui/rules_dialog.py
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QCheckBox, QDialogButtonBox, QListWidget,
                             QHBoxLayout, QPushButton, QComboBox, QFileDialog,
                             QInputDialog, QMessageBox, QListWidgetItem, QWidget)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt


class RulesDialog(QDialog):
    def __init__(self, config, rule=None, parent=None):
        super().__init__(parent)
        self.config = config
        self.rule_data = rule if rule else {}

        self.setWindowTitle("Редактор правил")
        self.setMinimumWidth(500)

        self._init_ui()
        if self.rule_data:
            self._load_rule_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        # --- НАЧАЛО ИЗМЕНЕНИЯ: Сохраняем ссылку на QFormLayout ---
        self.form_layout = QFormLayout()
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---

        self.name_edit = QLineEdit()
        self.enabled_check = QCheckBox("Правило включено")
        self.form_layout.addRow("Название правила:", self.name_edit)
        self.form_layout.addRow(self.enabled_check)

        conditions_layout = QVBoxLayout()
        self.conditions_list = QListWidget()
        conditions_layout.addWidget(self.conditions_list)
        cond_btn_layout = QHBoxLayout()
        add_cond_btn = QPushButton(QIcon(":/icons/add.png"), "Добавить условие")
        del_cond_btn = QPushButton(QIcon(":/icons/delete.png"), "Удалить условие")
        cond_btn_layout.addWidget(add_cond_btn)
        cond_btn_layout.addWidget(del_cond_btn)
        conditions_layout.addLayout(cond_btn_layout)
        self.form_layout.addRow("Условия (должны выполняться все):", conditions_layout)

        self.action_type_combo = QComboBox()
        self.action_type_combo.addItems(["Назначить в ящик", "Переместить в папку"])
        self.form_layout.addRow("Действие:", self.action_type_combo)

        self.box_selector_combo = QComboBox()
        self.path_selector_widget = QWidget()
        path_layout = QHBoxLayout(self.path_selector_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        self.path_edit = QLineEdit()
        browse_btn = QPushButton("...")
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_btn)

        self.populate_box_selector()
        self.form_layout.addRow("Ящик:", self.box_selector_combo)
        self.form_layout.addRow("Папка:", self.path_selector_widget)

        main_layout.addLayout(self.form_layout)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        main_layout.addWidget(self.button_box)

        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        add_cond_btn.clicked.connect(self._add_condition)
        del_cond_btn.clicked.connect(self._delete_condition)
        self.action_type_combo.currentIndexChanged.connect(self._on_action_type_changed)
        browse_btn.clicked.connect(self._browse_folder)

        self._on_action_type_changed(0)

    def populate_box_selector(self):
        self.box_selector_combo.clear()
        for box in self.config.get("desktop_boxes", []):
            self.box_selector_combo.addItem(box["name"], box["id"])

    def _load_rule_data(self):
        self.name_edit.setText(self.rule_data.get("name", ""))
        self.enabled_check.setChecked(self.rule_data.get("enabled", True))

        for cond in self.rule_data.get("conditions", []):
            self._add_condition_item(cond)

        action = self.rule_data.get("action", {})
        if action.get("type") == "assign_to_box":
            self.action_type_combo.setCurrentIndex(0)
            box_id = action.get("box_id")
            index = self.box_selector_combo.findData(box_id)
            if index != -1: self.box_selector_combo.setCurrentIndex(index)
        elif action.get("type") == "move_to":
            self.action_type_combo.setCurrentIndex(1)
            self.path_edit.setText(action.get("path", ""))

    # --- НАЧАЛО ИЗМЕНЕНИЯ: Обращаемся к QFormLayout напрямую ---
    def _on_action_type_changed(self, index):
        is_assign = (index == 0)
        # Получаем виджеты для каждой строки и управляем их видимостью
        self.form_layout.labelForField(self.box_selector_combo).setVisible(is_assign)
        self.box_selector_combo.setVisible(is_assign)

        self.form_layout.labelForField(self.path_selector_widget).setVisible(not is_assign)
        self.path_selector_widget.setVisible(not is_assign)

    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    def _add_condition(self):
        cond_type, ok = QInputDialog.getItem(self, "Добавить условие", "Выберите тип условия:",
                                             ["Имя содержит", "Расширение файла"], 0, False)
        if not ok: return

        text, ok = QInputDialog.getText(self, "Значение", "Введите значение для условия:")
        if not ok or not text: return

        condition_map = {"Имя содержит": "name_contains", "Расширение файла": "extension_is"}
        condition = {"type": condition_map[cond_type], "value": text}
        self._add_condition_item(condition)

    def _add_condition_item(self, condition):
        display_map = {"name_contains": "Имя содержит", "extension_is": "Расширение"}
        display_text = f"{display_map.get(condition['type'], '???')} '{condition['value']}'"
        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, condition)
        self.conditions_list.addItem(item)

    def _delete_condition(self):
        selected_item = self.conditions_list.currentItem()
        if selected_item:
            self.conditions_list.takeItem(self.conditions_list.row(selected_item))

    def _browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку", os.path.expanduser("~"))
        if folder:
            self.path_edit.setText(folder)

    def get_rule_data(self):
        if not self.name_edit.text():
            QMessageBox.warning(self, "Ошибка", "Название правила не может быть пустым.")
            return None

        conditions = []
        for i in range(self.conditions_list.count()):
            item = self.conditions_list.item(i)
            conditions.append(item.data(Qt.UserRole))

        if not conditions:
            QMessageBox.warning(self, "Ошибка", "Нужно добавить хотя бы одно условие.")
            return None

        action = {}
        if self.action_type_combo.currentIndex() == 0:
            action["type"] = "assign_to_box"
            action["box_id"] = self.box_selector_combo.currentData()
        else:
            action["type"] = "move_to"
            action["path"] = self.path_edit.text()
            if not action["path"]:
                QMessageBox.warning(self, "Ошибка", "Необходимо указать путь к папке.")
                return None

        return {
            "name": self.name_edit.text(),
            "enabled": self.enabled_check.isChecked(),
            "conditions": conditions,
            "action": action
        }

    @staticmethod
    def edit_rule(config, rule=None, parent=None):
        dialog = RulesDialog(config, rule, parent)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            return dialog.get_rule_data(), True
        return None, False