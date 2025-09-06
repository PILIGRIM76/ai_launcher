# core/classifier.py
import logging
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal


class FileClassifier(QObject):
    file_classified = pyqtSignal(str, str)

    def __init__(self, config):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.categories = self.config.get('categories', {})
        self.exceptions = self.config.get('exceptions', [])
        self.advanced_rules = self.config.get('advanced_rules', [])

    def check_advanced_rules(self, file_path: Path):
        """
        Проверяет файл по списку продвинутых правил.
        Возвращает действие (например, путь для перемещения), если правило сработало.
        """
        for rule in self.advanced_rules:
            if not rule.get("enabled", False):
                continue

            conditions = rule.get("conditions", [])
            if not conditions:
                continue

            # Проверяем, выполняются ли ВСЕ условия для данного правила
            is_match = all(self._check_condition(file_path, cond) for cond in conditions)

            if is_match:
                self.logger.info(f"Файл '{file_path.name}' соответствует продвинутому правилу '{rule.get('name')}'.")
                return rule.get("action")

        return None

    def _check_condition(self, file_path: Path, condition: dict):
        """Проверяет одно конкретное условие для файла."""
        cond_type = condition.get("type")
        cond_value = condition.get("value")

        if cond_type == "name_contains":
            return cond_value.lower() in file_path.name.lower()
        if cond_type == "extension_is":
            return file_path.suffix.lower() == cond_value.lower()
        # Здесь в будущем можно добавить другие типы условий:
        # if cond_type == "size_greater_than": ...
        # if cond_type == "older_than": ...

        return False

    def classify_by_category(self, file_path: Path):
        """
        Определяет категорию для файла по старой логике (расширениям).
        """
        if not file_path.exists():
            return None

        if file_path.is_dir():
            return "Папки"  # Папки не обрабатываются

        if file_path.name in self.exceptions:
            return None  # Исключение - не трогать

        ext = file_path.suffix.lower()

        for category, extensions in self.categories.items():
            if ext in extensions:
                return category

        return "Другое"