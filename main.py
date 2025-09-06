# main.py
import sys
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtCore import Qt

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ui.main_window import MainWindow
from core.utils import setup_logging, load_config
from core.box_manager import BoxManager
# --- ИЗМЕНЕНИЕ: Импортируем темы ---
from ui.themes import DARK_THEME_QSS, LIGHT_THEME_QSS

__version__ = "1.0.0"
try:
    import resources_rc
except ImportError:
    print("Внимание: файл ресурсов 'resources_rc.py' не найден.")
    pass


# --- ИЗМЕНЕНИЕ: Новая функция для применения темы ---
def apply_theme(app, theme_name):
    if theme_name == 'dark':
        app.setStyleSheet(DARK_THEME_QSS)
    else:
        app.setStyleSheet(LIGHT_THEME_QSS)


def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    setup_logging()
    config = load_config()

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setWindowIcon(QIcon(":/icons/app_icon.png"))

    # --- ИЗМЕНЕНИЕ: Применяем тему при запуске ---
    apply_theme(app, config.get("theme", "light"))

    box_manager = BoxManager(config)
    window = MainWindow(config, box_manager)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()