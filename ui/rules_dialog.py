# ui/rules_dialog.py
import copy
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QListWidgetItem,
    QGroupBox, QLabel, QLineEdit, QComboBox, QCheckBox, QFrame, QMessageBox,
    QFileDialog
)
from PyQt5.QtCore import Qt


#
# ОШИБОЧНАЯ СТРОКА ИМПОРТА БЫЛА ЗДЕСЬ И ТЕПЕРЬ УДАЛЕНА
#

class RulesDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = copy.deepcopy(config)
        self.rules = self.config.get('advanced_rules', [])
        self.current_rule_index = -1

        self.setWindowTitle("Редактор Продвинутых Правил")
        self.setGeometry(150, 150, 800, 600)
        self._init_ui()
        self._connect_signals()
        self._load_rules_list()

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        main_layout = QHBoxLayout()

        # Левая панель
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("Список правил:"))
        self.rules_list = QListWidget()
        left_panel.addWidget(self.rules_list)
        rules_btn_layout = QHBoxLayout()
        self.add_rule_btn = QPushButton("Добавить")
        self.remove_rule_btn = QPushButton("Удалить")
        rules_btn_layout.addWidget(self.add_rule_btn)
        rules_btn_layout.addWidget(self.remove_rule_btn)
        left_panel.addLayout(rules_btn_layout)

        # Правая панель
        right_panel = QVBoxLayout()
        self.editor_group = QGroupBox("Редактор правила")
        self.editor_group.setEnabled(False)
        editor_layout = QVBoxLayout(self.editor_group)
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Имя правила:"))
        self.rule_name_edit = QLineEdit()
        name_layout.addWidget(self.rule_name_edit)
        self.rule_enabled_check = QCheckBox("Включено")
        name_layout.addWidget(self.rule_enabled_check)
        editor_layout.addLayout(name_layout)
        line1 = QFrame();
        line1.setFrameShape(QFrame.HLine)
        editor_layout.addWidget(line1)
        conditions_group = QGroupBox("Условия (должны выполняться ВСЕ)")
        self.conditions_layout = QVBoxLayout(conditions_group)
        editor_layout.addWidget(conditions_group)
        self.add_condition_btn = QPushButton("Добавить условие")
        self.conditions_layout.addWidget(self.add_condition_btn, 0, Qt.AlignRight)
        line2 = QFrame();
        line2.setFrameShape(QFrame.HLine)
        editor_layout.addWidget(line2)
        action_group = QGroupBox("Действие")
        action_layout = QHBoxLayout(action_group)
        action_layout.addWidget(QLabel("Переместить в папку:"))
        self.action_path_edit = QLineEdit()
        self.browse_path_btn = QPushButton("...")
        action_layout.addWidget(self.action_path_edit)
        action_layout.addWidget(self.browse_path_btn)
        editor_layout.addWidget(action_group)
        right_panel.addWidget(self.editor_group)
        right_panel.addStretch()

        # Нижняя панель
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.save_button = QPushButton("Сохранить и закрыть")
        self.cancel_button = QPushButton("Отмена")
        bottom_layout.addWidget(self.save_button)
        bottom_layout.addWidget(self.cancel_button)

        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 2)
        outer_layout.addLayout(main_layout)
        outer_layout.addLayout(bottom_layout)

    def _connect_signals(self):
        self.rules_list.currentRowChanged.connect(self._on_rule_selected)
        self.add_rule_btn.clicked.connect(self._add_rule)
        self.remove_rule_btn.clicked.connect(self._remove_rule)
        self.save_button.clicked.connect(self._save_and_accept)
        self.cancel_button.clicked.connect(self.reject)
        self.browse_path_btn.clicked.connect(self._browse_folder)
        self.add_condition_btn.clicked.connect(self._add_condition_widget)

    def _load_rules_list(self):
        self.rules_list.clear()
        for rule in self.rules:
            item = QListWidgetItem(rule.get("name", "Новое правило"))
            self.rules_list.addItem(item)
        if self.rules:
            self.rules_list.setCurrentRow(0)
        else:
            self._on_rule_selected(-1)

    def _on_rule_selected(self, index):
        self._save_editor_to_rule(self.current_rule_index)

        self.current_rule_index = index
        if index == -1:
            self.editor_group.setEnabled(False)
            self.rule_name_edit.clear()
            self._display_conditions([])
            return

        self.editor_group.setEnabled(True)
        rule = self.rules[index]

        self.rule_name_edit.blockSignals(True)
        self.rule_enabled_check.blockSignals(True)
        self.action_path_edit.blockSignals(True)

        self.rule_name_edit.setText(rule.get("name", ""))
        self.rule_enabled_check.setChecked(rule.get("enabled", True))
        self.action_path_edit.setText(rule.get("action", {}).get("path", ""))
        self._display_conditions(rule.get("conditions", []))

        self.rule_name_edit.blockSignals(False)
        self.rule_enabled_check.blockSignals(False)
        self.action_path_edit.blockSignals(False)

    def _display_conditions(self, conditions):
        while self.conditions_layout.count() > 1:
            widget = self.conditions_layout.itemAt(0).widget()
            widget.deleteLater()

        for cond in conditions:
            self._add_condition_widget(cond)

    def _add_condition_widget(self, condition_data=None):
        if self.current_rule_index == -1: return

        widget = QFrame()
        layout = QHBoxLayout(widget)

        type_combo = QComboBox()
        type_combo.addItems(["Имя файла содержит", "Расширение файла"])

        value_edit = QLineEdit()

        remove_btn = QPushButton("X")
        remove_btn.setFixedSize(24, 24)
        remove_btn.clicked.connect(widget.deleteLater)

        layout.addWidget(type_combo)
        layout.addWidget(value_edit)
        layout.addWidget(remove_btn)

        if isinstance(condition_data, dict):
            cond_type = condition_data.get("type", "name_contains")
            index = 1 if cond_type == "extension_is" else 0
            type_combo.setCurrentIndex(index)
            value_edit.setText(condition_data.get("value", ""))

        self.conditions_layout.insertWidget(self.conditions_layout.count() - 1, widget)

    def _save_editor_to_rule(self, index):
        if index == -1: return

        rule = self.rules[index]
        rule["name"] = self.rule_name_edit.text()
        rule["enabled"] = self.rule_enabled_check.isChecked()

        if "action" not in rule: rule["action"] = {}
        rule["action"]["type"] = "move_to"
        rule["action"]["path"] = self.action_path_edit.text()

        conditions = []
        for i in range(self.conditions_layout.count() - 1):
            widget = self.conditions_layout.itemAt(i).widget()
            type_combo = widget.findChild(QComboBox)
            value_edit = widget.findChild(QLineEdit)

            if type_combo and value_edit:
                cond_type = "extension_is" if type_combo.currentIndex() == 1 else "name_contains"
                conditions.append({"type": cond_type, "value": value_edit.text()})
        rule["conditions"] = conditions

        self.rules_list.item(index).setText(rule["name"])

    def _add_rule(self):
        self._save_editor_to_rule(self.current_rule_index)
        new_rule = {"name": "Новое правило", "enabled": True, "conditions": [],
                    "action": {"type": "move_to", "path": ""}}
        self.rules.append(new_rule)
        self._load_rules_list()
        self.rules_list.setCurrentRow(len(self.rules) - 1)

    def _remove_rule(self):
        if self.current_rule_index == -1: return
        reply = QMessageBox.question(self, "Подтверждение", "Удалить выбранное правило?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.rules[self.current_rule_index]
            self._load_rules_list()

    def _browse_folder(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите папку назначения")
        if directory:
            self.action_path_edit.setText(directory)

    def _save_and_accept(self):
        self._save_editor_to_rule(self.current_rule_index)
        self.config['advanced_rules'] = self.rules
        self.accept()