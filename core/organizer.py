# core/organizer.py
import os
import shutil
import logging
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal
from .classifier import FileClassifier
from .utils import get_all_desktop_paths

try:
    import win32api
    import win32con

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    logging.getLogger(__name__).warning("Модуль pywin32 не найден. Настройка иконок будет отключена.")


class DesktopOrganizer(QObject):
    # --- ДОБАВЛЕН НОВЫЙ СИГНАЛ ---
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    organization_completed = pyqtSignal(str)
    operation_logged = pyqtSignal(dict)

    def __init__(self, config):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.classifier = FileClassifier()
        self.desktop_paths = get_all_desktop_paths()
        self.update_config(config)

    def update_config(self, config):
        self.config = config
        self.classifier.categories = self.config.get('categories', {})
        self.auto_organize = self.config.get('auto_organize_enabled', True)

    def organize_all_desktops(self):
        if not self.desktop_paths:
            self.organization_completed.emit("Рабочие столы для организации не найдены.")
            return
        for path_str in self.desktop_paths:
            self.organize_single_desktop(Path(path_str))

    def organize_single_desktop(self, desktop_path: Path):
        try:
            entries = list(desktop_path.iterdir())
            total_items = len(entries)
            moved_count = 0
            operation_details = {'type': 'organize', 'moved_files': []}

            for i, entry in enumerate(entries):
                # --- ОТПРАВКА СИГНАЛА О ТЕКУЩЕМ СТАТУСЕ ---
                self.status_updated.emit(f"Проверка: {entry.name}")

                if entry.name.startswith(
                        ".") or entry.name == "desktop.ini" or entry.name in self.classifier.categories:
                    continue

                category = self.classifier.classify_file(entry)
                if category and category != "Папки":
                    moved_info = self._move_to_category(entry, category, desktop_path)
                    if moved_info:
                        operation_details['moved_files'].append(moved_info)
                        moved_count += 1

                if total_items > 0:
                    self.progress_updated.emit(int((i + 1) / total_items * 100))

            msg = f"Организация завершена. Перемещено: {moved_count}."
            self.organization_completed.emit(msg)
            if moved_count > 0:
                self.operation_logged.emit(operation_details)
        except Exception as e:
            self.logger.error(f"Ошибка при организации {desktop_path}: {e}", exc_info=True)
            self.organization_completed.emit(f"Ошибка организации: {e}")

    def handle_new_file(self, file_path_str: str):
        if not self.auto_organize:
            return

        file_path = Path(file_path_str)
        category = self.classifier.classify_file(file_path)
        if category and category != "Папки":
            for desktop_path_str in self.desktop_paths:
                desktop_path = Path(desktop_path_str)
                if file_path.parent == desktop_path:
                    self._move_to_category(file_path, category, desktop_path)
                    break

    def _move_to_category(self, src_path: Path, category: str, desktop_path: Path) -> dict:
        dest_dir = desktop_path / category

        try:
            dest_dir.mkdir(exist_ok=True)
        except PermissionError:
            self.logger.error(f"Отказано в доступе при создании папки: {dest_dir}")
            return None
        except Exception as e:
            self.logger.error(f"Неизвестная ошибка при создании папки {dest_dir}: {e}")
            return None

        dest_path = dest_dir / src_path.name
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{src_path.stem}_{counter}{src_path.suffix}"
            counter += 1

        try:
            shutil.move(str(src_path), str(dest_path))
            self.logger.info(f"Файл перемещен: '{src_path.name}' -> '{dest_path.parent.name}'")
            self._set_category_icon(dest_dir, category)
            return {'original': str(src_path), 'new': str(dest_path)}
        except Exception as e:
            self.logger.error(f"Ошибка перемещения файла '{src_path.name}': {e}")
            return None

    def _set_category_icon(self, folder_path: Path, category: str):
        if not WIN32_AVAILABLE:
            return

        try:
            icon_path = None
            custom_icons = self.config.get('category_icons', {})
            if category in custom_icons and Path(custom_icons[category]).exists():
                icon_path = custom_icons[category]
            else:
                icon_map = {
                    "Программы": "shell32.dll,3",
                    "Документы": "shell32.dll,4",
                    "Изображения": "imageres.dll,11",
                    "Медиа": "imageres.dll,10",
                    "Архивы": "imageres.dll,56",
                    "Код": "shell32.dll,74",
                }
                icon_path = icon_map.get(category)

            if icon_path:
                ini_path = folder_path / "desktop.ini"

                if ini_path.exists():
                    return

                with open(ini_path, "w", encoding="utf-8") as f:
                    f.write("[.ShellClassInfo]\n")
                    if icon_path.lower().endswith('.ico'):
                        f.write(f"IconResource={icon_path},0\n")
                    else:
                        f.write(f"IconResource={icon_path}\n")

                win32api.SetFileAttributes(str(ini_path), win32con.FILE_ATTRIBUTE_HIDDEN)
                win32api.SetFileAttributes(str(folder_path), win32con.FILE_ATTRIBUTE_SYSTEM)
        except Exception as e:
            self.logger.warning(f"Не удалось установить иконку для '{folder_path.name}': {e}")

    def restore_file(self, src_path_str: str, dest_path_str: str) -> bool:
        src_path = Path(src_path_str)
        dest_path = Path(dest_path_str)
        try:
            dest_path.parent.mkdir(exist_ok=True, parents=True)
            shutil.move(str(src_path), str(dest_path))
            self.logger.info(f"Файл восстановлен: '{src_path.name}' -> '{dest_path.parent.name}'")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка восстановления файла '{src_path.name}': {e}")
            return False