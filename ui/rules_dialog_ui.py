# ui/rules_dialog_ui.py
from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_RulesDialog(object):
    def setupUi(self, RulesDialog):
        RulesDialog.setObjectName("RulesDialog")
        RulesDialog.resize(750, 450)
        self.gridLayout = QtWidgets.QGridLayout(RulesDialog)
        self.gridLayout.setObjectName("gridLayout")

        self.rulesListWidget = QtWidgets.QListWidget(RulesDialog)
        self.rulesListWidget.setObjectName("rulesListWidget")
        self.gridLayout.addWidget(self.rulesListWidget, 0, 0, 1, 1)

        self.buttonsLayout = QtWidgets.QHBoxLayout()
        self.addRuleButton = QtWidgets.QPushButton("Добавить правило", RulesDialog)
        self.addRuleButton.setObjectName("addRuleButton")
        self.deleteRuleButton = QtWidgets.QPushButton("Удалить правило", RulesDialog)
        self.deleteRuleButton.setObjectName("deleteRuleButton")
        self.buttonsLayout.addWidget(self.addRuleButton)
        self.buttonsLayout.addWidget(self.deleteRuleButton)
        self.gridLayout.addLayout(self.buttonsLayout, 1, 0, 1, 1)

        self.editorGroupBox = QtWidgets.QGroupBox("Редактор правила", RulesDialog)
        self.editorGroupBox.setEnabled(False)
        self.editorGroupBox.setObjectName("editorGroupBox")
        self.formLayout = QtWidgets.QFormLayout(self.editorGroupBox)
        self.formLayout.setObjectName("formLayout")

        # --- ИЗМЕНЕНИЯ ЗДЕСЬ ---
        self.ruleNameLabel = QtWidgets.QLabel("Название:", self.editorGroupBox)
        self.ruleNameEdit = QtWidgets.QLineEdit(self.editorGroupBox)
        self.ruleNameEdit.setObjectName("ruleNameEdit")
        self.formLayout.addRow(self.ruleNameLabel, self.ruleNameEdit)

        self.targetBoxLabel = QtWidgets.QLabel("Целевая коробка:", self.editorGroupBox)
        self.targetBoxCombo = QtWidgets.QComboBox(self.editorGroupBox)
        self.targetBoxCombo.setObjectName("targetBoxCombo")
        self.formLayout.addRow(self.targetBoxLabel, self.targetBoxCombo)
        # --- КОНЕЦ ИЗМЕНЕНИЙ ---

        self.conditionsGroupBox = QtWidgets.QGroupBox("Условия (все должны выполняться)", self.editorGroupBox)
        self.conditionsLayout = QtWidgets.QVBoxLayout(self.conditionsGroupBox)
        self.scrollArea = QtWidgets.QScrollArea(self.conditionsGroupBox)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.conditionsVLayout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)
        self.conditionsVLayout.setAlignment(QtCore.Qt.AlignTop)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.conditionsLayout.addWidget(self.scrollArea)

        self.addConditionButton = QtWidgets.QPushButton("Добавить условие", self.editorGroupBox)
        self.addConditionButton.setObjectName("addConditionButton")
        self.conditionsLayout.addWidget(self.addConditionButton)

        self.formLayout.addRow(self.conditionsGroupBox)

        self.gridLayout.addWidget(self.editorGroupBox, 0, 1, 2, 1)
        self.gridLayout.setColumnStretch(1, 2)

        self.buttonBox = QtWidgets.QDialogButtonBox(RulesDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Save)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 2)

        self.retranslateUi(RulesDialog)
        self.buttonBox.accepted.connect(RulesDialog.accept)
        self.buttonBox.rejected.connect(RulesDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(RulesDialog)

    def retranslateUi(self, RulesDialog):
        _translate = QtCore.QCoreApplication.translate
        RulesDialog.setWindowTitle(_translate("RulesDialog", "Редактор правил сортировки"))