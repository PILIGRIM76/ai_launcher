# core/snapshot_manager.py
import json
import logging
from datetime import datetime
from pathlib import Path
from .utils import DATA_DIR

try:
    import win32gui
    import win32con
    import win32api
    import commctrl

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class SnapshotManager:
    def __init__(self, box_manager):
        self.logger = logging.getLogger(__name__)
        self.box_manager = box_manager
        self.snapshots_dir = DATA_DIR / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)

    def _get_desktop_listview_hwnd(self):
        """Находит хендл (HWND) элемента SysListView32 на рабочем столе."""
        if not WIN32_AVAILABLE: return None
        h_progman = win32gui.FindWindow("Progman", None)
        h_shelldll = win32gui.FindWindowEx(h_progman, 0, "SHELLDLL_DefView", None)
        h_listview = win32gui.FindWindowEx(h_shelldll, 0, "SysListView32", "FolderView")
        return h_listview

    def create_snapshot(self, name: str):
        """Создает снимок текущего расположения иконок и ящиков."""
        if not WIN32_AVAILABLE:
            self.logger.error("Невозможно создать снимок: библиотека pywin32 не доступна.")
            return False, "pywin32 не установлена"

        hwnd = self._get_desktop_listview_hwnd()
        if not hwnd:
            self.logger.error("Не удалось найти SysListView32 на рабочем столе.")
            return False, "Не найден компонент рабочего стола"

        icon_count = win32gui.SendMessage(hwnd, win32con.LVM_GETITEMCOUNT, 0, 0)
        icons_data = []
        for i in range(icon_count):
            # Получение позиции иконки
            point = win32gui.SendMessage(hwnd, win32con.LVM_GETITEMPOSITION, i, 0)
            x, y = win32api.LOWORD(point), win32api.HIWORD(point)

            # Получение имени иконки (это более сложная часть, требующая работы с памятью)
            # Для простоты пока оставим заглушку, но в реальном проекте это нужно реализовать
            # через VirtualAllocEx, WriteProcessMemory, ReadProcessMemory.
            # Здесь мы просто сохраним индекс и позицию.
            icons_data.append({"index": i, "position": [x, y]})

        # Получение данных о ящиках
        boxes_data = self.box_manager.config.get("desktop_boxes", [])

        snapshot_data = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "icons": icons_data,
            "boxes": boxes_data
        }

        try:
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name}.json"
            filepath = self.snapshots_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=4)
            self.logger.info(f"Снимок '{name}' успешно создан: {filename}")
            return True, "Снимок создан"
        except Exception as e:
            self.logger.error(f"Ошибка сохранения снимка: {e}", exc_info=True)
            return False, str(e)

    def restore_snapshot(self, filename: str):
        """Восстанавливает расположение из файла снимка."""
        if not WIN32_AVAILABLE:
            self.logger.error("Невозможно восстановить снимок: pywin32 не доступна.")
            return False, "pywin32 не установлена"

        filepath = self.snapshots_dir / filename
        if not filepath.exists():
            return False, "Файл снимка не найден"

        hwnd = self._get_desktop_listview_hwnd()
        if not hwnd:
            return False, "Не найден компонент рабочего стола"

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                snapshot_data = json.load(f)

            # Восстановление иконок
            for icon in snapshot_data.get("icons", []):
                index = icon.get("index")
                pos = icon.get("position")
                lparam = win32api.MAKELONG(pos[0], pos[1])
                win32gui.SendMessage(hwnd, win32con.LVM_SETITEMPOSITION, index, lparam)

            # Восстановление ящиков
            self.box_manager.config["desktop_boxes"] = snapshot_data.get("boxes", [])
            self.box_manager.load_boxes()  # Перезагружаем ящики с новыми позициями

            self.logger.info(f"Снимок '{filename}' восстановлен.")
            return True, "Снимок восстановлен"
        except Exception as e:
            self.logger.error(f"Ошибка восстановления снимка: {e}", exc_info=True)
            return False, str(e)

    def list_snapshots(self) -> list:
        """Возвращает список всех сохраненных снимков."""
        snapshots = []
        for file in self.snapshots_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    snapshots.append({
                        "filename": file.name,
                        "name": data.get("name", "Без имени"),
                        "date": data.get("timestamp", "")
                    })
            except Exception:
                continue
        return sorted(snapshots, key=lambda x: x['date'], reverse=True)

    def delete_snapshot(self, filename: str):
        """Удаляет файл снимка."""
        try:
            (self.snapshots_dir / filename).unlink()
            return True
        except OSError:
            return False