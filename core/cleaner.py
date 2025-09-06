# core/cleaner.py
import logging
from pathlib import Path
from .security import FileRecycleBin
from PyQt5.QtCore import QObject, pyqtSignal

class DesktopCleaner(QObject):
    progress_updated = pyqtSignal(int)
    cleaning_completed = pyqtSignal(str)
    operation_logged = pyqtSignal(dict)

    def __init__(self, config):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.recycle_bin = FileRecycleBin()

    # --- ИЗМЕНЕНИЕ: Добавляем desktop_path в аргументы ---
    def clean_desktop(self, desktop_path: str, options: dict):
        try:
            desktop = Path(desktop_path)
            if not desktop.exists():
                raise FileNotFoundError(f"Путь к рабочему столу не найден: {desktop_path}")

            entries = [e for e in desktop.iterdir() if e.is_file()]
            total_files = len(entries)
            removed_count = 0
            operation_details = {'type': 'clean', 'removed_files': []}

            for i, entry in enumerate(entries):
                if self._should_remove(entry, options):
                    try:
                        original_path = str(entry)
                        backup_path = self.recycle_bin.safe_delete(original_path)
                        operation_details['removed_files'].append({'original': original_path, 'backup': backup_path})
                        removed_count += 1
                    except Exception as e:
                        self.logger.warning(f"Не удалось удалить {entry.name}: {e}")
                if total_files > 0:
                    self.progress_updated.emit((i + 1) * 100 // total_files)

            msg = f"Очистка завершена. Удалено элементов: {removed_count}."
            self.cleaning_completed.emit(msg)
            if removed_count > 0:
                self.operation_logged.emit(operation_details)
        except Exception as e:
            self.logger.error(f"Критическая ошибка при очистке: {e}", exc_info=True)
            self.cleaning_completed.emit(f"Ошибка очистки: {e}")

    def _should_remove(self, file_entry: Path, options: dict) -> bool:
        ext = file_entry.suffix.lower()
        if options.get("remove_broken_shortcuts") and ext == ".lnk":
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(file_entry))
                return not Path(shortcut.Targetpath).exists()
            except Exception:
                return True
        if options.get("remove_temp_files") and (file_entry.name.startswith("~$") or file_entry.name.startswith("~")):
            return True
        return False