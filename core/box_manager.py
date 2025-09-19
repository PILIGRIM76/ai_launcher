# Файл: core/box_manager.py
import logging
import uuid
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal, QPoint, QSize
from .box_widget import BoxWidget
from .utils import save_config, DATA_DIR


class BoxManager(QObject):
    boxes_updated = pyqtSignal()
    request_open_settings = pyqtSignal(str)
    request_rename_box = pyqtSignal(str, str)
    request_delete_box = pyqtSignal(str)
    request_create_new_box = pyqtSignal()
    state_changed = pyqtSignal(str, dict)
    file_dropped = pyqtSignal(str, str)
    # --- НАЧАЛО ИЗМЕНЕНИЯ: Добавляем недостающий сигнал ---
    request_unhide_original = pyqtSignal(str)

    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.boxes = {}
        self.are_visible = True

    def load_boxes(self):
        self.hide_all_boxes()
        self.boxes.clear()
        box_definitions = self.config.get("desktop_boxes", [])
        global_border_settings = self.config.get("global_border_settings", {})
        global_appearance_settings = self.config.get("global_appearance_settings", {})

        for box_def in box_definitions:
            box_id = box_def.get("id")
            if not box_id:
                self.logger.warning(f"Найден ящик без ID. Пропускаем.")
                continue

            box_widget = BoxWidget(box_id=box_id, name=box_def.get("name", "Без имени"), config=box_def,
                                   global_border_settings=global_border_settings,
                                   global_appearance_settings=global_appearance_settings)

            pos = QPoint(*box_def.get("position", [100, 100]))
            size = QSize(*box_def.get("size", [250, 300]))
            box_widget.move(pos)
            box_widget.resize(size)
            box_widget.widget_moved.connect(self.update_box_properties)

            box_widget.configure_requested.connect(self.request_open_settings)
            box_widget.rename_requested.connect(self.request_rename_box)
            box_widget.delete_requested.connect(self.request_delete_box)
            box_widget.create_new_box_requested.connect(self.request_create_new_box)
            box_widget.state_changed.connect(self.state_changed)
            box_widget.refresh_requested.connect(self.refresh_box_content)
            box_widget.file_dropped.connect(self.file_dropped)
            # --- НАЧАЛО ИЗМЕНЕНИЯ: Подключаем сигнал от виджета к нашему новому сигналу ---
            box_widget.request_unhide_original.connect(self.request_unhide_original)
            # --- КОНЕЦ ИЗМЕНЕНИЯ ---

            self.boxes[box_id] = box_widget

        self.logger.info(f"Загружено {len(self.boxes)} ящиков.")
        if self.config.get("boxes_enabled", True):
            self.show_all_boxes()

        self.logger.info("Загрузка содержимого для каждого ящика...")
        for box_id in self.boxes.keys():
            self.refresh_box_content(box_id)

    def create_box(self, name: str, position: list = [150, 150]):
        default_box_appearance = {
            "color": "#3A3A3A", "font": "Segoe UI,16"
        }
        default_box_state = {
            "is_collapsed": False, "is_locked": False, "view_mode": "icon",
            "sort_by": "none", "sort_order": "asc"
        }
        new_box_config = {
            **{"id": f"box_{uuid.uuid4().hex[:8]}", "name": name, "position": position, "size": [250, 300]},
            **default_box_state,
            "appearance": default_box_appearance
        }
        self.config["desktop_boxes"].append(new_box_config)
        save_config(self.config)
        self.logger.info(f"Создан новый ящик '{name}'.")
        self.load_boxes()
        self.boxes_updated.emit()

    def delete_box(self, box_id: str):
        if box_id in self.boxes:
            self.boxes[box_id].close()
            del self.boxes[box_id]
        self.config["desktop_boxes"] = [b for b in self.config["desktop_boxes"] if b.get("id") != box_id]
        save_config(self.config)
        self.logger.info(f"Ящик с ID {box_id} удален.")
        self.boxes_updated.emit()

    def update_box_properties(self, box_id: str, new_properties: dict):
        self.logger.info(f"Получены для обновления свойства ящика {box_id}: {new_properties}")
        for box_def in self.config.get("desktop_boxes", []):
            if box_def.get("id") == box_id:
                if 'appearance' in new_properties and 'appearance' in box_def:
                    box_def['appearance'].update(new_properties['appearance'])
                    del new_properties['appearance']
                box_def.update(new_properties)
                self.logger.info(f"Конфигурация для ящика {box_id} успешно обновлена.")
                break
        save_config(self.config)

    def update_box_visuals(self, box_id: str):
        if box_id in self.boxes:
            box_widget = self.boxes[box_id]
            box_config = next((b for b in self.config["desktop_boxes"] if b.get("id") == box_id), None)
            global_border_settings = self.config.get("global_border_settings", {})
            global_appearance_settings = self.config.get("global_appearance_settings", {})
            if box_config:
                self.logger.info(f"Передача команды на обновление стилей виджету {box_id}")
                new_size = QSize(*box_config.get("size", [250, 300]))
                box_widget.resize(new_size)
                box_widget.update_styles(box_config, global_border_settings, global_appearance_settings)
        else:
            self.logger.warning(f"Попытка обновить виджет, который не найден в активных: {box_id}")

    def refresh_all_visuals(self):
        self.logger.info("Получена команда на обновление всех ящиков.")
        for box_id in self.boxes.keys():
            self.update_box_visuals(box_id)

    def add_shortcut_to_box(self, box_id: str, shortcut_path: str):
        if box_id in self.boxes:
            self.boxes[box_id].add_item_from_path(shortcut_path)
        else:
            self.logger.warning(f"Попытка добавить ярлык в несуществующий ящик с ID: {box_id}")

    def refresh_box_content(self, box_id: str):
        self.logger.info(f"Получен запрос на обновление содержимого ящика {box_id}")
        if box_id not in self.boxes:
            self.logger.warning("Ящик для обновления не найден.")
            return

        shortcuts_dir = DATA_DIR / "Shortcuts" / box_id
        if not shortcuts_dir.exists():
            self.logger.info(f"Папка с ярлыками для {box_id} не найдена, обновлять нечего.")
            self.boxes[box_id].refresh_items([])
            return

        file_paths = [str(f) for f in shortcuts_dir.glob("*.lnk")]
        self.boxes[box_id].refresh_items(file_paths)

    def hide_all_boxes(self):
        for box in self.boxes.values(): box.hide()
        self.are_visible = False

    def show_all_boxes(self):
        for box in self.boxes.values(): box.show()
        self.are_visible = True

    def toggle_visibility(self):
        if self.are_visible:
            self.hide_all_boxes()
        else:
            self.show_all_boxes()
        self.logger.info(f"Видимость ящиков переключена на: {self.are_visible}")