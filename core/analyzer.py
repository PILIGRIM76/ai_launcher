# core/analyzer.py
import logging
from pathlib import Path
from collections import defaultdict
from PyQt5.QtCore import QObject, pyqtSignal
from .utils import get_all_desktop_paths

class DesktopAnalyzer(QObject):
    suggestion_found = pyqtSignal(str, list) # (anomaly_type, extensions)

    def __init__(self, config):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.desktop_paths = get_all_desktop_paths()
        self.update_config(config) # Используем метод для начальной установки

    # --- НАЧАЛО ИЗМЕНЕНИЯ: ДОБАВЛЕН НЕДОСТАЮЩИЙ МЕТОД ---
    def update_config(self, config):
        """
        Обновляет конфигурацию, используемую анализатором.
        Это нужно, чтобы анализатор знал о новых категориях, созданных пользователем.
        """
        self.config = config
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    def analyze_desktop(self):
        """Анализирует рабочий стол на предмет аномалий."""
        if not self.desktop_paths:
            self.logger.warning("Рабочий стол для анализа не найден.")
            return

        desktop_path = Path(self.desktop_paths[0]) # Анализируем основной рабочий стол
        try:
            self._find_unclassified_extensions(desktop_path)
        except Exception as e:
            self.logger.error(f"Ошибка при анализе рабочего стола: {e}", exc_info=True)

    def _find_unclassified_extensions(self, desktop_path: Path):
        """Ищет расширения, для которых нет категорий."""
        known_extensions = set()
        # Берем актуальный список категорий из self.config
        for exts in self.config.get('categories', {}).values():
            known_extensions.update(exts)

        extension_counts = defaultdict(int)
        for entry in desktop_path.iterdir():
            if entry.is_file():
                ext = entry.suffix.lower()
                if ext and ext not in known_extensions:
                    extension_counts[ext] += 1

        # Ищем аномалии: > 10 файлов с одним неклассифицированным расширением
        anomalies = [ext for ext, count in extension_counts.items() if count > 10]

        if anomalies:
            self.logger.info(f"Найдена аномалия: неклассифицированные расширения {anomalies}")
            self.suggestion_found.emit("unclassified_extensions", anomalies)
        else:
            self.logger.info("Анализ завершен, аномалий не найдено.")