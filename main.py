# main.py
import sys
import os

# Устанавливаем версию в одном-единственном месте
__version__ = "2.0.0"  # --- ИЗМЕНЕНИЕ: Версия обновлена до 2.0.0 ---

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtCore import Qt

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ui.main_window import MainWindow
from core.utils import setup_logging, load_config
from core.box_manager import BoxManager
# --- НАЧАЛО ИЗМЕНЕНИЯ: Импортируем новый менеджер ---
from core.hotkey_manager import HotkeyManager
# --- КОНЕЦ ИЗМЕНЕНИЯ ---
from ui.themes import DARK_THEME_QSS, LIGHT_THEME_QSS

try:
    import resources_rc
except ImportError:
    print("Внимание: файл ресурсов 'resources_rc.py' не найден.")
    pass


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

    apply_theme(app, config.get("theme", "light"))

    # --- НАЧАЛО ИЗМЕНЕНИЯ: Инициализация и запуск новых компонентов ---
    box_manager = BoxManager(config)

    hotkey_manager = HotkeyManager(config)
    hotkey_manager.start()

    # Связываем сигналы от хоткеев с действиями
    hotkey_manager.listener.toggle_boxes_visibility.connect(box_manager.toggle_visibility)
    # hotkey_manager.listener.open_search.connect(...) # Связать с будущим окном поиска

    # Передаем __version__ и новые менеджеры как аргументы
    window = MainWindow(config, box_manager, hotkey_manager, __version__)
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    window.show()

    # --- НАЧАЛО ИЗМЕНЕНИЯ: Корректное завершение работы потока хоткеев ---
    app.aboutToQuit.connect(hotkey_manager.stop)
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()