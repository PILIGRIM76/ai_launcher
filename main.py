# Файл: main.py
import sys
import os
import logging
from pathlib import Path

__version__ = "3.2.0"

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QStyleFactory
from PyQt5.QtCore import Qt

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from ui.main_window import MainWindow
from core.utils import setup_logging, load_config, save_config, get_all_desktop_paths
from core.box_manager import BoxManager
from core.hotkey_manager import HotkeyManager
from core.organizer import DesktopOrganizer
from core.watcher import DesktopWatcher
from core.wallpaper_manager import WallpaperManager
from ui.themes import DARK_THEME_QSS, LIGHT_THEME_QSS

try:
    import resources_rc
except ImportError:
    print("Внимание: файл ресурсов 'resources_rc.py' не найден. Иконки могут не отображаться.")
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
    logger = logging.getLogger(__name__)
    config = load_config()

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setWindowIcon(QIcon(":/icons/app_icon.png"))

    apply_theme(app, config.get("theme", "light"))

    box_manager = BoxManager(config)
    hotkey_manager = HotkeyManager(config)
    organizer = DesktopOrganizer(config)
    wallpaper_manager = WallpaperManager(config)

    desktop_paths = get_all_desktop_paths()
    watcher = None
    if desktop_paths:
        watcher = DesktopWatcher(organizer, desktop_paths[0])
        if config.get("auto_organize_enabled", True):
            watcher.start()

    hotkey_manager.listener.toggle_boxes_visibility.connect(box_manager.toggle_visibility)
    organizer.shortcut_assigned_to_box.connect(box_manager.add_shortcut_to_box)
    hotkey_manager.start()

    # --- НАЧАЛО ИЗМЕНЕНИЯ: Добавляем обработку ручного перетаскивания ---
    def handle_file_drop(box_id, file_path):
        logger.info(f"Обработка перетаскивания файла '{file_path}' в ящик {box_id}")
        # Создаем временное "действие" для органайзера
        action = {"type": "assign_to_box", "box_id": box_id}
        organizer._execute_action(Path(file_path), action)

    box_manager.file_dropped.connect(handle_file_drop)
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    window = MainWindow(
        config=config,
        box_manager=box_manager,
        hotkey_manager=hotkey_manager,
        wallpaper_manager=wallpaper_manager,
        version=__version__
    )
    window.show()

    if config.get("run_initial_organization", True):
        logger.info("Запуск первоначальной организации рабочего стола...")
        organizer.organize_all_desktops()

    def on_quit():
        hotkey_manager.stop()
        if watcher and watcher.isRunning():
            watcher.stop()
            watcher.wait()
        save_config(config)

    app.aboutToQuit.connect(on_quit)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()