# core/sorter.py:
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal


class FileSorter(QObject):
    progress_updated = pyqtSignal(int)
    sorting_completed = pyqtSignal(str)
    operation_logged = pyqtSignal(dict)  # Для системы отмены

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def sort_desktop(self, desktop_path: str, criteria: dict):
        """
        Сортирует файлы на рабочем столе.
        Принимает путь к рабочему столу как аргумент.
        """
        try:
            desktop = Path(desktop_path)
            if not desktop.is_dir():
                raise FileNotFoundError(f"Директория рабочего стола не найдена: {desktop_path}")

            entries = [e for e in desktop.iterdir() if e.is_file()]
            total_files = len(entries)
            if total_files == 0:
                self.sorting_completed.emit("Сортировка завершена: файлы не найдены.")
                return

            operation_details = {
                'type': 'sort',
                'moved_files': []
            }

            for i, entry in enumerate(entries):
                moved_info = self._sort_file(entry, desktop, criteria)
                if moved_info:
                    operation_details['moved_files'].append(moved_info)
                self.progress_updated.emit(int((i + 1) / total_files * 100))

            self.sorting_completed.emit("Сортировка успешно завершена.")
            if operation_details['moved_files']:
                self.operation_logged.emit(operation_details)

        except Exception as e:
            self.logger.error(f"Ошибка при сортировке: {e}", exc_info=True)
            self.sorting_completed.emit(f"Ошибка сортировки: {e}")

    def _sort_file(self, file_path: Path, desktop_path: Path, criteria: dict) -> dict:
        """Сортирует один файл и возвращает информацию для отмены."""
        target_dir = None
        original_path_str = str(file_path)

        try:
            if criteria.get("by_type"):
                ext = file_path.suffix[1:].lower() if file_path.suffix else "NoExtension"
                target_dir = desktop_path / ext
            elif criteria.get("by_date"):
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                month_year = mod_time.strftime("%Y-%m")
                target_dir = desktop_path / month_year
            elif criteria.get("by_size"):
                size = file_path.stat().st_size
                if size < 1024 * 1024:
                    size_group = "Маленькие"
                elif size < 10 * 1024 * 1024:
                    size_group = "Средние"
                else:
                    size_group = "Большие"
                target_dir = desktop_path / size_group

            if target_dir:
                target_dir.mkdir(exist_ok=True)
                dest_path = target_dir / file_path.name
                shutil.move(original_path_str, str(dest_path))
                return {'original': original_path_str, 'new': str(dest_path)}

        except Exception as e:
            self.logger.warning(f"Не удалось отсортировать файл {file_path.name}: {e}")

        return None