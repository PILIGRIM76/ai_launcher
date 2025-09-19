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
    # --- ИЗМЕНЕНИЕ: Импортируем класс ошибки, чтобы ее можно было "поймать" ---
    import pywintypes

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

            # --- ИЗМЕНЕНИЕ: Добавляем обработку ошибок доступа при чтении атрибутов ---
            entries = []
            for e in desktop_path.iterdir():
                try:
                    # Пропускаем скрытые файлы
                    if not (win32api.GetFileAttributes(str(e)) & win32con.FILE_ATTRIBUTE_HIDDEN):
                        entries.append(e)
                except pywintypes.error:
                    self.logger.warning(f"Нет доступа к файлу '{e.name}', пропускаем.")
                    continue

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

    def _execute_action(self, src_path: Path, action: dict):
        action_type = action.get("type")

        if action_type == "assign_to_box":
            if not WIN32_AVAILABLE:
                self.logger.warning("Невозможно создать ярлык: библиотека pywin32 не найдена.")
                return None

            box_id = action.get("box_id")
            if not box_id:
                self.logger.warning(f"Действие 'assign_to_box' для файла '{src_path.name}' не содержит box_id.")
                return None

            try:
                shortcuts_dir = DATA_DIR / "Shortcuts" / box_id
                shortcuts_dir.mkdir(parents=True, exist_ok=True)

                shortcut_path = shortcuts_dir / f"{src_path.stem}.lnk"
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(str(shortcut_path))
                shortcut.TargetPath = str(src_path.resolve())
                shortcut.WorkingDirectory = str(src_path.parent.resolve())
                shortcut.save()

                # --- ИЗМЕНЕНИЕ: Теперь этот блок будет работать правильно ---
                try:
                    win32api.SetFileAttributes(str(src_path), win32con.FILE_ATTRIBUTE_HIDDEN)
                    self.logger.info(f"Файл '{src_path.name}' на рабочем столе скрыт.")
                except pywintypes.error as e:
                    if e.winerror == 5: # Ошибка 5 - это "Отказано в доступе"
                        self.logger.warning(f"Не удалось скрыть файл '{src_path.name}': Отказано в доступе. "
                                            f"Это может быть системный ярлык. Пропускаем скрытие.")
                    else:
                        # Если это другая ошибка, мы все равно хотим ее видеть
                        self.logger.error(f"Неизвестная ошибка Win32 при скрытии файла '{src_path.name}': {e}")

                self.shortcut_assigned_to_box.emit(box_id, str(shortcut_path))

                self.logger.info(f"Правило сработало: '{src_path.name}' назначен в ящик ID '{box_id}'.")
                return {'original': str(src_path), 'new_shortcut': str(shortcut_path), 'type': 'assign'}

            except Exception as e:
                self.logger.error(f"Ошибка при назначении файла в ящик '{src_path.name}': {e}", exc_info=True)
                return None

        return None

    def unhide_and_cleanup(self, shortcut_path_str: str):
        if not WIN32_AVAILABLE: return

        shortcut_path = Path(shortcut_path_str)
        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            original_path = Path(shortcut.TargetPath)

            if original_path.exists():
                try:
                    current_attrs = win32api.GetFileAttributes(str(original_path))
                    win32api.SetFileAttributes(str(original_path), current_attrs & ~win32con.FILE_ATTRIBUTE_HIDDEN)
                    self.logger.info(f"Файл '{original_path.name}' снова видим на рабочем столе.")
                except pywintypes.error as e:
                     if e.winerror == 5:
                         self.logger.warning(f"Не удалось сделать видимым файл '{original_path.name}': Отказано в доступе.")
                     else:
                         raise e

            shortcut_path.unlink()
            self.logger.info(f"Ярлык '{shortcut_path.name}' удален.")

        except Exception as e:
            self.logger.error(f"Ошибка при восстановлении файла из ящика: {e}")