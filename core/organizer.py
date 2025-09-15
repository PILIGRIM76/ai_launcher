# Файл: core/organizer.py
import shutil
import logging
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSignal
from .classifier import FileClassifier
from .utils import get_all_desktop_paths, DATA_DIR

try:
    import win32com.client
    import win32api, win32con

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class DesktopOrganizer(QObject):
    progress_updated = pyqtSignal(int)
    organization_completed = pyqtSignal(str)
    operation_logged = pyqtSignal(dict)
    shortcut_assigned_to_box = pyqtSignal(str, str)

    def __init__(self, config):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.classifier = FileClassifier(self.config)
        all_desktops = get_all_desktop_paths()
        self.desktop_path = Path(all_desktops[0]) if all_desktops else None
        self.auto_organize = True
        # --- НАЧАЛО ИЗМЕНЕНИЯ: Создаем папку для хранения оригиналов ---
        self.storage_dir = DATA_DIR / "Storage"
        self.storage_dir.mkdir(exist_ok=True)
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    def organize_all_desktops(self):
        if not self.desktop_path:
            msg = "Рабочий стол не найден. Организация отменена."
            self.logger.warning(msg)
            self.organization_completed.emit(msg)
            return
        self.organize_single_desktop(self.desktop_path)

    def organize_single_desktop(self, desktop_path: Path):
        try:
            if not desktop_path.is_dir():
                self.logger.error(f"Директория рабочего стола не найдена: {desktop_path}")
                return

            entries = list(desktop_path.iterdir())
            total_items = len(entries)
            moved_count = 0
            operation_details = {'type': 'organize', 'moved_files': []}

            for i, entry in enumerate(entries):
                if entry.name.startswith(".") or entry.name == "desktop.ini":
                    continue

                action = self.classifier.check_advanced_rules(entry)
                if action:
                    moved_info = self._execute_action(entry, action)
                    if moved_info:
                        operation_details['moved_files'].append(moved_info)
                        moved_count += 1

                if total_items > 0:
                    self.progress_updated.emit(int((i + 1) / total_items * 100))

            msg = f"Организация для '{desktop_path.name}' завершена. Перемещено: {moved_count}."
            self.organization_completed.emit(msg)
            if moved_count > 0:
                self.operation_logged.emit(operation_details)

        except Exception as e:
            self.logger.error(f"Ошибка при организации {desktop_path}: {e}", exc_info=True)
            self.organization_completed.emit(f"Ошибка организации: {e}")

    def handle_new_file(self, file_path_str: str):
        if not self.auto_organize: return
        file_path = Path(file_path_str)
        action = self.classifier.check_advanced_rules(file_path)
        if action:
            self._execute_action(file_path, action)

    # --- НАЧАЛО ИЗМЕНЕНИЯ: Полностью переписанная логика обработки ---
    def _execute_action(self, src_path: Path, action: dict):
        action_type = action.get("type")
        stored_path = None  # Для отката в случае ошибки

        if action_type == "assign_to_box":
            if not WIN32_AVAILABLE:
                self.logger.warning("Невозможно создать ярлык: библиотека pywin32 не найдена.")
                return None

            box_id = action.get("box_id")
            if not box_id:
                self.logger.warning(f"Действие 'assign_to_box' для файла '{src_path.name}' не содержит box_id.")
                return None

            try:
                # 1. Перемещаем ОРИГИНАЛ с рабочего стола в наше хранилище
                stored_path = self.storage_dir / src_path.name
                counter = 1
                while stored_path.exists():
                    stored_path = self.storage_dir / f"{src_path.stem}_{counter}{src_path.suffix}"
                    counter += 1
                shutil.move(str(src_path), str(stored_path))
                self.logger.info(f"Файл '{src_path.name}' перемещен в хранилище: {stored_path}")

                # 2. Создаем папку для ярлыков этого ящика
                shortcuts_dir = DATA_DIR / "Shortcuts" / box_id
                shortcuts_dir.mkdir(parents=True, exist_ok=True)

                # 3. Создаем ярлык, который указывает на файл в хранилище
                shortcut_path = shortcuts_dir / f"{stored_path.stem}.lnk"
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(shortcut_path))
                shortcut.TargetPath = str(stored_path.resolve())
                shortcut.WorkingDirectory = str(self.storage_dir.resolve())
                shortcut.save()

                # 4. Сообщаем BoxManager о новом ярлыке для отображения
                self.shortcut_assigned_to_box.emit(box_id, str(shortcut_path))

                self.logger.info(f"Правило сработало: '{src_path.name}' назначен в ящик ID '{box_id}'.")
                return {'original': str(src_path), 'new_shortcut': str(shortcut_path), 'type': 'assign'}

            except Exception as e:
                self.logger.error(f"Ошибка при назначении файла в ящик '{src_path.name}': {e}", exc_info=True)
                # Если что-то пошло не так, пытаемся вернуть файл на рабочий стол
                if stored_path and stored_path.exists():
                    shutil.move(str(stored_path), str(src_path))
                    self.logger.warning(f"Файл '{src_path.name}' возвращен на рабочий стол из-за ошибки.")
                return None

        elif action_type == "move_to":
            # Эта логика остается прежней
            # ...
            pass

        return None
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---