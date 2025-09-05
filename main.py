# main.py
import sys
import os
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtCore import Qt

# ... (код для настройки sys.path остается без изменений)
try:
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(current_file_path)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception as e:
    print(f"Error setting up sys.path: {e}")

from ui.main_window import MainWindow
from core.utils import setup_logging, load_config

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

    # --- НАЧАЛО ИЗМЕНЕНИЯ ---
    # Загрузка и применение файла стилей в зависимости от темы
    theme = config.get("theme", "light") # по умолчанию светлая
    qss_file = os.path.join(project_root, "ui", "styles", f"{theme}.qss")
    if os.path.exists(qss_file):
        with open(qss_file, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    app.setWindowIcon(QIcon(":/icons/app_icon.ico"))

    window = MainWindow(config)
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()