# core/duplicates.py
import os
import hashlib
import logging
from collections import defaultdict
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal


class DuplicateFinder(QObject):
    # --- ДОБАВЛЕН НОВЫЙ СИГНАЛ ---
    status_updated = pyqtSignal(str)
    duplicates_found = pyqtSignal(dict)
    progress_updated = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def find_duplicates(self, folder_path: str) -> None:
        try:
            duplicates = defaultdict(list)
            files_by_size = defaultdict(list)
            start_path = Path(folder_path)

            if not start_path.is_dir():
                self.logger.error(f"Путь для поиска дубликатов не является директорией: {folder_path}")
                self.duplicates_found.emit({})
                return

            all_files = [p for p in start_path.rglob('*') if p.is_file()]
            total_files = len(all_files)
            if total_files == 0:
                self.duplicates_found.emit({})
                return

            # Этап 1: Группировка по размеру
            for i, filepath in enumerate(all_files):
                # --- ОТПРАВКА СИГНАЛА ---
                self.status_updated.emit(f"Анализ размера: {filepath.name}")
                try:
                    file_size = filepath.stat().st_size
                    files_by_size[file_size].append(filepath)
                except OSError as e:
                    self.logger.warning(f"Не удалось получить размер файла {filepath.name}: {e}")
                self.progress_updated.emit(int((i + 1) / total_files * 50))

            # Этап 2: Проверка хешей
            size_groups = [files for files in files_by_size.values() if len(files) > 1]
            total_groups = len(size_groups)
            if total_groups == 0:
                self.duplicates_found.emit({})
                return

            processed_files_in_groups = 0
            for group_idx, files in enumerate(size_groups):
                hashes = defaultdict(list)
                for filepath in files:
                    # --- ОТПРАВКА СИГНАЛА ---
                    self.status_updated.emit(f"Вычисление хеша: {filepath.name}")
                    try:
                        file_hash = self._calculate_hash(filepath)
                        if file_hash:
                            hashes[file_hash].append(str(filepath))
                    except OSError as e:
                        self.logger.warning(f"Не удалось вычислить хеш для {filepath.name}: {e}")

                for hash_value, hash_files in hashes.items():
                    if len(hash_files) > 1:
                        duplicates[hash_value] = hash_files

                self.progress_updated.emit(50 + int((group_idx + 1) / total_groups * 50))

            self.duplicates_found.emit(dict(duplicates))
        except Exception as e:
            self.logger.error(f"Ошибка при поиске дубликатов: {e}", exc_info=True)
            self.duplicates_found.emit({})

    def _calculate_hash(self, filepath: Path, block_size=65536) -> str:
        hasher = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                buf = f.read(block_size)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(block_size)
            return hasher.hexdigest()
        except (IOError, OSError) as e:
            self.logger.warning(f"Не удалось прочитать файл для хеширования {filepath.name}: {e}")
            return None