# core/classifier.py
import logging
from pathlib import Path
from datetime import datetime

class FileClassifier:
    def __init__(self, config):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.update_config(config)

    def update_config(self, config):
        self.rules = config.get("rules", [])
        self.exceptions = config.get("exceptions", [])
        self.logger.info("Конфигурация классификатора обновлена.")

    def classify_file(self, file_path: Path) -> str:
        """
        Определяет целевую "коробку" для файла на основе набора правил.
        Возвращает имя "коробки" или None, если правило не найдено.
        """
        if not file_path.exists() or file_path.is_dir():
            return None

        if file_path.name in self.exceptions:
            self.logger.info(f"Файл '{file_path.name}' находится в исключениях, пропущен.")
            return None

        for rule in self.rules:
            if rule.get("enabled", False) and self._check_conditions(file_path, rule.get("conditions", [])):
                target_box = rule.get("target_box")
                self.logger.info(f"Файл '{file_path.name}' соответствует правилу '{rule.get('name')}'. Цель: '{target_box}'.")
                return target_box

        self.logger.info(f"Для файла '{file_path.name}' не найдено подходящих правил. Цель: 'Другое'.")
        return "Другое" # Категория по умолчанию

    def _check_conditions(self, file_path: Path, conditions: list) -> bool:
        """Проверяет, соответствует ли файл всем условиям правила."""
        if not conditions:
            return False

        for cond in conditions:
            field = cond.get("field")
            operator = cond.get("operator")
            value = cond.get("value")

            # Получаем фактическое значение поля из файла
            file_value = self._get_file_field_value(file_path, field)
            if file_value is None:
                return False # Если не удалось получить значение, условие не выполнено

            # Проверяем условие
            if not self._evaluate_operator(file_value, operator, value):
                return False # Если хотя бы одно условие неверно, все правило неверно

        return True # Все условия выполнены

    def _get_file_field_value(self, file_path: Path, field: str):
        """Возвращает значение указанного поля для файла."""
        if field == "extension":
            return file_path.suffix.lower()
        if field == "name":
            return file_path.stem.lower()
        if field == "full_name":
            return file_path.name.lower()
        if field == "date_created":
            return datetime.fromtimestamp(file_path.stat().st_ctime)
        # Добавьте другие поля по необходимости (date_modified, size и т.д.)
        return None

    def _evaluate_operator(self, file_value, operator: str, rule_value) -> bool:
        """Сравнивает значение файла со значением из правила с помощью оператора."""
        rule_value_lower = str(rule_value).lower()
        file_value_str_lower = str(file_value).lower()

        if operator == "is":
            return file_value_str_lower == rule_value_lower
        if operator == "is_not":
            return file_value_str_lower != rule_value_lower
        if operator == "contains":
            return rule_value_lower in file_value_str_lower
        if operator == "not_contains":
            return rule_value_lower not in file_value_str_lower
        if operator == "starts_with":
            return file_value_str_lower.startswith(rule_value_lower)
        if operator == "ends_with":
            return file_value_str_lower.endswith(rule_value_lower)
        if operator == "in":
            # Для оператора 'in' значением является строка расширений через запятую
            extensions = [ext.strip().lower() for ext in rule_value.split(',')]
            return file_value_str_lower in extensions
        # Добавьте другие операторы (>, < для дат и размеров)
        return False