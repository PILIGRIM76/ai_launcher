# ui/themes.py

# --- ИЗМЕНЕНИЕ: Добавляем недостающие константы с цветами ---
DARK_ICON_COLOR = "#f8f8f2"  # Светлые иконки для темной темы
LIGHT_ICON_COLOR = "#282a36"  # Темные иконки для светлой темы

# Простая темная тема, основанная на популярном стиле "Dracula"
DARK_THEME_QSS = """
    /* Общий стиль окна */
    #MainWindow, #MainWidget, QDialog {
        background-color: #282a36;
        color: #f8f8f2;
        font-family: Segoe UI;
        font-size: 10pt;
    }

    /* Боковая панель */
    #Sidebar {
        background-color: #44475a;
    }

    /* Кнопки боковой панели */
    QPushButton#SidebarButton {
        background-color: transparent;
        color: #f8f8f2;
        border: none;
        padding: 10px;
        text-align: left;
        font-size: 11pt;
    }
    QPushButton#SidebarButton:hover {
        background-color: #6272a4;
    }
    QPushButton#SidebarButton:checked {
        background-color: #bd93f9;
        color: #282a36;
    }

    /* Группы */
    QGroupBox {
        background-color: #282a36;
        border: 1px solid #44475a;
        border-radius: 5px;
        margin-top: 1ex;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        margin-left: 10px;
    }

    /* Обычные кнопки */
    QPushButton {
        background-color: #6272a4;
        border: none;
        padding: 8px;
        border-radius: 3px;
        min-width: 120px;
    }
    QPushButton:hover {
        background-color: #7082b6;
    }
    QPushButton:pressed {
        background-color: #506090;
    }

    /* Поля ввода и списки */
    QLineEdit, QComboBox, QTextEdit {
        background-color: #44475a;
        border: 1px solid #6272a4;
        padding: 5px;
        border-radius: 3px;
    }
    QListWidget {
        border: 1px solid #44475a;
        background-color: #44475a;
    }

    /* Прогресс-бар */
    QProgressBar {
        border: 1px solid #6272a4;
        border-radius: 5px;
        text-align: center;
        color: #f8f8f2;
    }
    QProgressBar::chunk {
        background-color: #bd93f9;
    }

    /* Меню */
    QMenuBar { background-color: #44475a; }
    QMenuBar::item:selected { background-color: #6272a4; }
    QMenu { background-color: #44475a; border: 1px solid #6272a4; }
    QMenu::item:selected { background-color: #6272a4; }
"""

# Светлая тема - это просто пустая строка, чтобы сбросить стили к системным
LIGHT_THEME_QSS = ""