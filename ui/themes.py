# ui/themes.py

# Простая темная тема, основанная на популярном стиле "Dracula"
DARK_THEME_QSS = """
    QWidget {
        background-color: #282a36;
        color: #f8f8f2;
        font-family: Segoe UI;
        font-size: 10pt;
    }
    QMainWindow, QDialog {
        background-color: #282a36;
    }
    QGroupBox {
        background-color: #44475a;
        border: 1px solid #6272a4;
        border-radius: 5px;
        margin-top: 1ex;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 3px;
    }
    QPushButton {
        background-color: #6272a4;
        border: 1px solid #bd93f9;
        padding: 5px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background-color: #7082b6;
    }
    QPushButton:pressed {
        background-color: #506090;
    }
    QCheckBox, QLabel {
        background-color: transparent;
    }
    QComboBox {
        background-color: #44475a;
        border: 1px solid #bd93f9;
        padding: 3px;
        border-radius: 3px;
    }
    QTextEdit {
        background-color: #282a36;
        border: 1px solid #6272a4;
        color: #f8f8f2;
    }
    QProgressBar {
        border: 1px solid #6272a4;
        border-radius: 5px;
        text-align: center;
        color: #f8f8f2;
    }
    QProgressBar::chunk {
        background-color: #bd93f9;
        width: 10px;
        margin: 0.5px;
    }
    QMenuBar {
        background-color: #44475a;
    }
    QMenuBar::item:selected {
        background-color: #6272a4;
    }
    QMenu {
        background-color: #44475a;
        border: 1px solid #6272a4;
    }
    QMenu::item:selected {
        background-color: #6272a4;
    }
"""

# Светлая тема - это просто пустая строка, чтобы сбросить стили к системным
LIGHT_THEME_QSS = ""