# core/cleaner.py
import os
import logging
import shutil
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal
# ИСПРАВЛЕНИЕ: Абсолютный импорт
from core.security import FileRecycleBin


class DesktopCleaner(QObject):
    progress_updated = pyqtSignal(int)
    cleaning_completed = pyqtSignal(str)
    operation_logged = pyqtSignal(dict)  # Для системы отмены

    # --- НАЧАЛО ИЗМЕНЕНИЯ ---
    def __init__(self, config):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.recycle_bin = FileRecycleBin()
        self.update_config(config)  # Используем метод для начальной установки конфига

    def update_config(self, config):
        """Обновляет конфигурацию для применения настроек 'на лету'."""
        self.config = config

    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    # --- ИЗМЕНЕНИЕ: Метод больше не принимает 'options', а берет их из self.config ---
    def clean_desktop(self, desktop_path: str):
        """
        Очищает рабочий стол на основе настроек из конфигурации.
        """
        try:
            # Получаем настройки очистки напрямую из сохраненного конфига
            options = self.config.get("clean_options", {})

            desktop = Path(desktop_path)
            if not desktop.exists():
                raise FileNotFoundError(f"Путь к рабочему столу не найден: {desktop_path}")

            entries = list(desktop.iterdir())
            total_files = len(entries)
            removed_count = 0
            operation_details = {
                'type': 'clean',
                'removed_files': []
            }

            for i, entry in enumerate(entries):
                if entry.is_file():
                    # Передаем 'options' во внутренний метод
                    if self._should_remove(entry, options):
                        try:
                            original_path = str(entry)
                            backup_path = self.recycle_bin.safe_delete(original_path)

                            operation_details['removed_files'].append({
                                'original': original_path,
                                'backup': backup_path
                            })
                            removed_count += 1
                        except Exception as e:
                            self.logger.warning(f"Не удалось удалить {entry.name}: {e}")

                self.progress_updated.emit((i + 1) * 100 // total_files if total_files > 0 else 100)

            msg = f"Очистка завершена. Удалено элементов: {removed_count}."
            self.cleaning_completed.emit(msg)
            self.operation_logged.emit(operation_details)
        except Exception as e:
            self.logger.error(f"Критическая ошибка при очистке рабочего стола {desktop_path}: {e}", exc_info=True)
            self.cleaning_completed.emit(f"Ошибка очистки: {e}")

    def _should_remove(self, file_entry: Path, options: dict) -> bool:
        """Определяет, следует ли удалять файл."""
        ext = file_entry.suffix.lower()

        if options.get("remove_broken_shortcuts") and ext == ".lnk":
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(file_entry))
                return not Path(shortcut.Targetpath).exists()
            except ImportError:
                self.logger.warning("Модуль win32com не найден. Проверка битых ярлыков отключена.")
                return False
            except Exception:
                return True

        if options.get("remove_temp_files") and (file_entry.name.startswith("~$") or file_entry.name.startswith("~")):
            return True

        if options.get("remove_by_ext") and ext in [".tmp", ".bak", ".old"]:
            return True

        return False