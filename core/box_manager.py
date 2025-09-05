# core/box_manager.py
import json
import logging
from pathlib import Path
from PyQt5.QtCore import QObject, QPoint, QSize
# Важное исправление: импортируем BoxWidget из того же пакета 'core'
from .box_widget import BoxWidget


class BoxManager(QObject):
    LAYOUT_FILE = Path("layout.json")

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.boxes = {}
        self.layout_data = self._load_layout()
        self.are_visible = True  # Изначально считаем, что коробки видны

    def create_all_boxes(self):
        box_definitions = self.config.get("boxes", [])
        for box_def in box_definitions:
            name = box_def.get("name")
            if name:
                self.create_box(name)
        self.logger.info(f"Создано {len(self.boxes)} контейнеров.")

    def create_box(self, category_name):
        if category_name in self.boxes:
            return

        box_widget = BoxWidget(category_name)

        # Восстанавливаем позицию и размер
        box_layout = self.layout_data.get(category_name)
        if box_layout:
            pos = QPoint(*box_layout.get("pos", [100, 100]))
            size = QSize(*box_layout.get("size", [250, 300]))
            box_widget.move(pos)
            box_widget.resize(size)

        box_widget.widget_moved.connect(self.on_box_moved)
        box_widget.widget_resized.connect(self.on_box_resized)

        self.boxes[category_name] = box_widget
        box_widget.show()

    def on_box_moved(self, name, pos):
        if name in self.layout_data:
            self.layout_data[name]['pos'] = [pos.x(), pos.y()]
        else:
            self.layout_data[name] = {'pos': [pos.x(), pos.y()], 'size': [250, 300]}
        self._save_layout()

    def on_box_resized(self, name, size):
        if name in self.layout_data:
            self.layout_data[name]['size'] = [size.width(), size.height()]
        else:
            self.layout_data[name] = {'pos': [100, 100], 'size': [size.width(), size.height()]}
        self._save_layout()

    def add_file_to_box(self, category, file_path):
        if category in self.boxes:
            p = Path(file_path)
            self.boxes[category].add_item(p.name, str(p))
            self.logger.info(f"Файл '{p.name}' добавлен в контейнер '{category}'.")
        else:
            self.logger.warning(f"Контейнер '{category}' не найден для файла '{file_path}'.")

    def remove_file_from_box(self, category, file_path):
        # TODO: Реализовать логику удаления элемента из QListWidget
        pass

    def _load_layout(self):
        if not self.LAYOUT_FILE.exists():
            return {}
        try:
            with open(self.LAYOUT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            self.logger.error(f"Ошибка загрузки layout.json: {e}")
            return {}

    def _save_layout(self):
        try:
            with open(self.LAYOUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.layout_data, f, indent=4)
        except IOError as e:
            self.logger.error(f"Ошибка сохранения layout.json: {e}")

    def hide_all_boxes(self):
        for box in self.boxes.values():
            box.hide()

    def show_all_boxes(self):
        for box in self.boxes.values():
            box.show()

    def toggle_visibility(self) -> bool:
        """
        Переключает видимость всех коробок и возвращает их новое состояние.
        True - видны, False - скрыты.
        """
        if self.are_visible:
            self.hide_all_boxes()
            self.are_visible = False
        else:
            self.show_all_boxes()
            self.are_visible = True

        self.logger.info(f"Видимость 'коробок' переключена на: {self.are_visible}")
        return self.are_visible