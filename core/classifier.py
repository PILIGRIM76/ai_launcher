#core/classifier.py

import os
import logging
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal


class FileClassifier(QObject):
    file_classified = pyqtSignal(str, str)  # (file_path, category)

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.categories = {
            "Программы": [".exe", ".lnk", ".msi", ".bat"],
            "Документы": [".doc", ".docx", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
            "Изображения": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
            "Медиа": [".mp3", ".mp4", ".avi", ".mkv", ".mov", ".wav"],
            "Архивы": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Код": [".py", ".js", ".html", ".css", ".java", ".cpp", ".cs"],
            "Другое": []
        }
        self.exceptions = []

    def classify_file(self, file_path: Path):
        """Определяет категорию для файла"""
        if not file_path.exists():
            self.logger.warning(f"Файл для классификации не найден: {file_path}")
            return None

        if file_path.is_dir():
            return "Папки"

        if file_path.name in self.exceptions:
            return None  # Исключение - не перемещать

        ext = file_path.suffix.lower()

        for category, extensions in self.categories.items():
            if ext in extensions:
                return category

        return "Другое"

    def add_category(self, name, extensions):
        """Добавляет новую категорию"""
        self.categories[name] = extensions

    def remove_category(self, name):
        """Удаляет категорию"""
        if name in self.categories and name not in ["Другое", "Папки"]:
            del self.categories[name]
            return True
        return False

    def add_extension(self, category, extension):
        """Добавляет расширение к категории"""
        if category in self.categories:
            if extension not in self.categories[category]:
                self.categories[category].append(extension)
                return True
        return False

    def add_exception(self, file_name):
        """Добавляет файл в исключения"""
        if file_name not in self.exceptions:
            self.exceptions.append(file_name)
            return True
        return False

    def remove_exception(self, file_name):
        """Удаляет файл из исключений"""
        if file_name in self.exceptions:
            self.exceptions.remove(file_name)
            return True
        return False