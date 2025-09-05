# ui/rules_dialog.py
from PyQt5.QtWidgets import QDialog, QListWidgetItem, QWidget, QHBoxLayout, QComboBox, QLineEdit, QPushButton
from .rules_dialog_ui import Ui_RulesDialog


class RulesDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.ui = Ui_RulesDialog()
        self.ui.setupUi(self)

        self.config = config
        self.current_rule_name = None
        self.condition_widgets = []

        self._populate_boxes_combo()
        self._load_rules_to_list()
        self._setup_connections()

    def _setup_connections(self):
        self.ui.rulesListWidget.currentItemChanged.connect(self._on_rule_selected)
        self.ui.addRuleButton.clicked.connect(self._add_new_rule)
        self.ui.deleteRuleButton.clicked.connect(self._delete_rule)
        self.ui.addConditionButton.clicked.connect(self._add_new_condition_widget)
        self.ui.buttonBox.accepted.connect(self._save_all_changes_and_accept)

    def _populate_boxes_combo(self):
        box_names = [box['name'] for box in self.config.get('boxes', [])]
        self.ui.targetBoxCombo.addItems(box_names)

    def _load_rules_to_list(self):
        self.ui.rulesListWidget.clear()
        for rule in self.config.get('rules', []):
            item = QListWidgetItem(rule['name'])
            self.ui.rulesListWidget.addItem(item)

    def _on_rule_selected(self, current, previous):
        # Перед выбором нового правила, сохраняем изменения в предыдущем
        if previous:
            self._save_current_rule_changes(previous.text())

        if not current:
            self.ui.editorGroupBox.setEnabled(False)
            self.current_rule_name = None
            return

        self.ui.editorGroupBox.setEnabled(True)
        rule_name = current.text()
        self.current_rule_name = rule_name
        rule_data = next((r for r in self.config['rules'] if r['name'] == rule_name), None)

        if not rule_data:
            return

        # Заполняем поля редактора
        self.ui.ruleNameEdit.setText(rule_data.get('name', ''))
        self.ui.targetBoxCombo.setCurrentText(rule_data.get('target_box', ''))

        self._clear_condition_widgets()
        for condition in rule_data.get('conditions', []):
            self._add_new_condition_widget(condition)

    def _add_new_condition_widget(self, condition_data=None):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        field_combo = QComboBox()
        field_combo.addItems(['extension', 'name', 'full_name'])

        operator_combo = QComboBox()
        operator_combo.addItems(['is', 'is_not', 'contains', 'not_contains', 'starts_with', 'ends_with', 'in'])

        value_edit = QLineEdit()

        delete_btn = QPushButton("X")
        delete_btn.setFixedSize(24, 24)

        layout.addWidget(field_combo)
        layout.addWidget(operator_combo)
        layout.addWidget(value_edit, 1)
        layout.addWidget(delete_btn)

        if condition_data:
            field_combo.setCurrentText(condition_data.get('field', ''))
            operator_combo.setCurrentText(condition_data.get('operator', ''))
            value_edit.setText(condition_data.get('value', ''))

        self.ui.conditionsVLayout.addWidget(widget)
        self.condition_widgets.append(widget)

        delete_btn.clicked.connect(lambda: self._remove_condition_widget(widget))

    def _remove_condition_widget(self, widget):
        self.condition_widgets.remove(widget)
        widget.deleteLater()

    def _clear_condition_widgets(self):
        for widget in self.condition_widgets:
            widget.deleteLater()
        self.condition_widgets.clear()

    def _add_new_rule(self):
        # Генерируем уникальное имя
        i = 1
        while any(r['name'] == f"Новое правило {i}" for r in self.config['rules']):
            i += 1
        new_name = f"Новое правило {i}"

        new_rule = {
            "name": new_name,
            "target_box": self.config['boxes'][0]['name'] if self.config['boxes'] else "",
            "conditions": [{"field": "extension", "operator": "is", "value": ".docx"}],
            "enabled": True
        }
        self.config['rules'].append(new_rule)
        self._load_rules_to_list()
        self.ui.rulesListWidget.setCurrentRow(self.ui.rulesListWidget.count() - 1)

    def _delete_rule(self):
        current_item = self.ui.rulesListWidget.currentItem()
        if not current_item: return

        rule_name = current_item.text()
        self.config['rules'] = [r for r in self.config['rules'] if r['name'] != rule_name]
        self._load_rules_to_list()
        self.ui.editorGroupBox.setEnabled(False)

    def _save_current_rule_changes(self, rule_name_to_save):
        if not rule_name_to_save: return

        rule_data = next((r for r in self.config['rules'] if r['name'] == rule_name_to_save), None)
        if not rule_data: return

        new_name = self.ui.ruleNameEdit.text()
        if new_name != rule_name_to_save:
            # Обновляем имя в списке
            for i in range(self.ui.rulesListWidget.count()):
                if self.ui.rulesListWidget.item(i).text() == rule_name_to_save:
                    self.ui.rulesListWidget.item(i).setText(new_name)
                    break
            self.current_rule_name = new_name

        rule_data['name'] = new_name
        rule_data['target_box'] = self.ui.targetBoxCombo.currentText()

        new_conditions = []
        for widget in self.condition_widgets:
            layout = widget.layout()
            field = layout.itemAt(0).widget().currentText()
            operator = layout.itemAt(1).widget().currentText()
            value = layout.itemAt(2).widget().text()
            new_conditions.append({"field": field, "operator": operator, "value": value})

        rule_data['conditions'] = new_conditions

    def _save_all_changes_and_accept(self):
        # Сохраняем изменения для последнего активного правила перед закрытием
        self._save_current_rule_changes(self.current_rule_name)
        self.accept()  # Закрываем окно с результатом "Accepted"

    def get_updated_config(self):
        return self.config