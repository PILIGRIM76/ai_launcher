# core/organizer.py
import os
import shutil
import logging
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal
from .classifier import FileClassifier
from .utils import get_all_desktop_paths

class DesktopOrganizer(QObject):
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    organization_completed = pyqtSignal(str)
    operation_logged = pyqtSignal(dict)
    # --- НОВЫЙ СИГНАЛ ДЛЯ ИНТЕГРАЦИИ С BoxManager ---
    file_classified_for_box = pyqtSignal(str, str) # (category, file_path)

    def __init__(self, config):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.desktop_paths = get_all_desktop_paths()
        # --- ИЗМЕНЕНИЕ: Инициализация нового классификатора ---
        self.classifier = FileClassifier(config)
        self.update_config(config)
        # --- НОВОЕ: Путь к скрытому хранилищу ---
        if self.desktop_paths:
            self.storage_path = Path(self.desktop_paths[0]).parent / ".DesktopManagerStorage"
            self.storage_path.mkdir(exist_ok=True)
            self.logger.info(f"Хранилище файлов: {self.storage_path}")

    def update_config(self, config):
        self.config = config
        self.classifier.update_config(config)
        self.auto_organize = self.config.get('auto_organize_enabled', True)

    def organize_all_desktops(self):
        if not self.desktop_paths:
            self.organization_completed.emit("Рабочие столы для организации не найдены.")
            return
        for path_str in self.desktop_paths:
            self.organize_single_desktop(Path(path_str))

    def organize_single_desktop(self, desktop_path: Path):
        try:
            entries = [e for e in desktop_path.iterdir() if e.is_file()]
            total_items = len(entries)
            moved_count = 0
            operation_details = {'type': 'organize', 'moved_files': []}

            for i, entry in enumerate(entries):
                self.status_updated.emit(f"Проверка: {entry.name}")

                if entry.name.startswith(".") or entry.name == "desktop.ini":
                    continue

                # --- ИЗМЕНЕНИЕ: Используем новый классификатор ---
                target_box = self.classifier.classify_file(entry)
                if target_box:
                    moved_info = self._move_to_storage(entry, target_box)
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
        target_box = self.classifier.classify_file(file_path)
        if target_box:
            # Убедимся, что файл находится на одном из отслеживаемых рабочих столов
            if any(file_path.parent == Path(p) for p in self.desktop_paths):
                 self._move_to_storage(file_path, target_box)

    def _move_to_storage(self, src_path: Path, target_box: str) -> dict:
        """Перемещает файл в центральное хранилище и сообщает UI."""
        if not self.storage_path:
            self.logger.error("Путь к хранилищу не определен.")
            return None

        dest_path = self.storage_path / src_path.name
        counter = 1
        while dest_path.exists():
            dest_path = self.storage_path / f"{src_path.stem}_{counter}{src_path.suffix}"
            counter += 1

        try:
            shutil.move(str(src_path), str(dest_path))
            self.logger.info(f"Файл перемещен в хранилище: '{src_path.name}' -> '{dest_path}'")
            # --- КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: Отправляем сигнал для BoxManager ---
            self.file_classified_for_box.emit(target_box, str(dest_path))
            return {'original': str(src_path), 'new': str(dest_path)}
        except Exception as e:
            self.logger.error(f"Ошибка перемещения файла '{src_path.name}' в хранилище: {e}")
            return None