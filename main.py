# main.py
import sys
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtCore import Qt

# ... (блок для исправления пути PyInstaller остается без изменений) ...

from ui.main_window import MainWindow
from core.utils import setup_logging, load_config
# --- НОВЫЙ ИМПОРТ ---
from core.box_manager import BoxManager

try:
    import resources_rc
except ImportError:
    print("Внимание: файл ресурсов 'resources_rc.py' не найден.")
    pass

def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    setup_logging()
    config = load_config()

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))

    theme = config.get("theme", "light")
    qss_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui", "styles", f"{theme}.qss")
    if os.path.exists(qss_file):
        with open(qss_file, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    app.setWindowIcon(QIcon(":/icons/app_icon.ico"))

    # --- ИНТЕГРАЦИЯ СИСТЕМЫ "КОРОБОК" ---
    # 1. Создаем менеджер "коробок"
    box_manager = BoxManager(config)

    # 2. Создаем главное окно и передаем в него менеджер
    window = MainWindow(config, box_manager)
    window.show()

    # 3. Создаем все "коробки" после того, как основное приложение готово
    box_manager.create_all_boxes()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()