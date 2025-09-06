# core/organizer.py
import shutil
import logging
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal
from .classifier import FileClassifier
from .utils import get_all_desktop_paths

# ... (try/except для win32api без изменений) ...
try:
    import win32api, win32con

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class DesktopOrganizer(QObject):
    # ... (сигналы без изменений) ...
    progress_updated = pyqtSignal(int)
    organization_completed = pyqtSignal(str)
    operation_logged = pyqtSignal(dict)

    def __init__(self, config):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.classifier = FileClassifier(self.config)
        # --- ИЗМЕНЕНИЕ: Берем только первый, основной рабочий стол ---
        all_desktops = get_all_desktop_paths()
        self.desktop_path = Path(all_desktops[0]) if all_desktops else None
        self.auto_organize = True

    def organize_all_desktops(self):
        """Теперь организует только основной рабочий стол пользователя."""
        if not self.desktop_path:
            msg = "Рабочий стол не найден. Организация отменена."
            self.logger.warning(msg)
            self.organization_completed.emit(msg)
            return
        self.organize_single_desktop(self.desktop_path)

    # ... (остальной код класса остается без изменений, я его скрыл для краткости) ...
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

                moved_info = None
                action = self.classifier.check_advanced_rules(entry)
                if action:
                    moved_info = self._execute_action(entry, action)
                else:
                    if entry.name not in self.classifier.categories:
                        category = self.classifier.classify_by_category(entry)
                        if category and category != "Папки":
                            moved_info = self._move_to_category(entry, category, desktop_path)

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
        desktop_path = file_path.parent
        action = self.classifier.check_advanced_rules(file_path)
        if action:
            self._execute_action(file_path, action)
        else:
            category = self.classifier.classify_by_category(file_path)
            if category and category != "Папки":
                self._move_to_category(file_path, category, desktop_path)

    def _execute_action(self, src_path: Path, action: dict):
        action_type = action.get("type")
        if action_type == "move_to":
            dest_dir = Path(action.get("path"))
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest_path = dest_dir / src_path.name
            counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f"{src_path.stem}_{counter}{src_path.suffix}"
                counter += 1
            try:
                shutil.move(str(src_path), str(dest_path))
                self.logger.info(f"Правило сработало: '{src_path.name}' -> '{dest_path}'")
                return {'original': str(src_path), 'new': str(dest_path)}
            except Exception as e:
                self.logger.error(f"Ошибка выполнения действия для '{src_path.name}': {e}")
        return None

    def _move_to_category(self, src_path: Path, category: str, desktop_path: Path):
        dest_dir = desktop_path / category
        dest_dir.mkdir(exist_ok=True)
        dest_path = dest_dir / src_path.name
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{src_path.stem}_{counter}{src_path.suffix}"
            counter += 1
        try:
            shutil.move(str(src_path), str(dest_path))
            self.logger.info(f"Файл отсортирован по категории: '{src_path.name}' -> '{category}'")
            self._set_category_icon(dest_dir, category)
            return {'original': str(src_path), 'new': str(dest_path)}
        except Exception as e:
            self.logger.error(f"Ошибка перемещения в категорию '{src_path.name}': {e}")
            return None

    def _set_category_icon(self, folder_path: Path, category: str):
        if not WIN32_AVAILABLE: return
        icon_map = {"Программы": "shell32.dll,3", "Документы": "shell32.dll,4", "Изображения": "imageres.dll,11",
                    "Медиа": "imageres.dll,10", "Архивы": "imageres.dll,56", "Код": "shell32.dll,74"}
        icon_path = icon_map.get(category)
        if icon_path:
            try:
                ini_path = folder_path / "desktop.ini"
                with open(ini_path, "w", encoding="utf-8") as f:
                    f.write("[.ShellClassInfo]\n")
                    f.write(f"IconResource={icon_path}\n")
                win32api.SetFileAttributes(str(ini_path), win32con.FILE_ATTRIBUTE_HIDDEN)
                win32api.SetFileAttributes(str(folder_path), win32con.FILE_ATTRIBUTE_SYSTEM)
            except Exception as e:
                self.logger.error(f"Ошибка установки иконки для {folder_path.name}: {e}")

    def restore_file(self, src_path_str: str, dest_path_str: str):
        src_path = Path(src_path_str)
        dest_path = Path(dest_path_str)
        try:
            dest_path.parent.mkdir(exist_ok=True, parents=True)
            shutil.move(str(src_path), str(dest_path))
            self.logger.info(f"Файл восстановлен: '{src_path.name}' -> '{dest_path.parent.name}'")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка восстановления файла '{src_path.name}': {e}")
            return False