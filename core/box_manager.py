# core/box_manager.py
import logging
import uuid
from PyQt5.QtCore import QObject, pyqtSignal, QPoint, QSize
from PyQt5.QtWidgets import QApplication
from .box_widget import BoxWidget
from .utils import save_config


class BoxManager(QObject):
    """
    Управляет созданием, отображением и жизненным циклом виджетов-"ящиков".
    """
    # Сигнал для уведомления UI о необходимости обновить список ящиков
    boxes_updated = pyqtSignal()

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.boxes = {}  # Словарь для хранения экземпляров BoxWidget, ключ - id ящика
        self.are_visible = True

    def load_boxes(self):
        """Загружает и отображает все ящики из конфигурации."""
        self.hide_all_boxes()  # Сначала скроем старые, если они есть
        self.boxes.clear()

        box_definitions = self.config.get("desktop_boxes", [])
        for box_def in box_definitions:
            box_id = box_def.get("id")
            if not box_id:
                self.logger.warning(f"Найден ящик без ID в конфиге: {box_def.get('name')}. Пропускаем.")
                continue

            box_widget = BoxWidget(
                box_id=box_id,
                name=box_def.get("name", "Без имени"),
                config=box_def
            )

            # Устанавливаем геометрию
            pos = QPoint(*box_def.get("position", [100, 100]))
            size = QSize(*box_def.get("size", [250, 300]))
            box_widget.move(pos)
            box_widget.resize(size)

            # Подключаем сигналы для сохранения изменений
            box_widget.widget_moved.connect(self.update_box_properties)
            box_widget.widget_resized.connect(self.update_box_properties)

            self.boxes[box_id] = box_widget

        self.logger.info(f"Загружено {len(self.boxes)} ящиков.")
        self.show_all_boxes()

    def create_box(self, name: str, position: list = [150, 150]):
        """Создает новый ящик с настройками по умолчанию и сохраняет его в конфиг."""
        new_box_id = f"box_{uuid.uuid4().hex[:8]}"
        new_box_config = {
            "id": new_box_id,
            "name": name,
            "position": position,
            "size": [250, 300],
            "color": "#2D2D2D",
            "transparency": 85,
            "font_size": 10
        }
        self.config["desktop_boxes"].append(new_box_config)
        save_config(self.config)
        self.load_boxes()  # Перезагружаем все ящики, чтобы отобразить новый
        self.boxes_updated.emit()
        self.logger.info(f"Создан новый ящик '{name}' с ID {new_box_id}.")

    def delete_box(self, box_id: str):
        """Удаляет ящик из конфига и с экрана."""
        if box_id in self.boxes:
            self.boxes[box_id].close()
            del self.boxes[box_id]

        self.config["desktop_boxes"] = [
            box for box in self.config["desktop_boxes"] if box.get("id") != box_id
        ]
        save_config(self.config)
        self.boxes_updated.emit()
        self.logger.info(f"Ящик с ID {box_id} удален.")

    def update_box_properties(self, box_id: str, new_properties: dict):
        """Обновляет свойства ящика в конфиге и сохраняет."""
        for box_def in self.config.get("desktop_boxes", []):
            if box_def.get("id") == box_id:
                box_def.update(new_properties)
                self.logger.debug(f"Обновлены свойства для ящика {box_id}: {new_properties}")
                break
        save_config(self.config)
        # Можно добавить сигнал для UI, если нужно обновлять настройки в реальном времени

    def add_shortcut_to_box(self, box_id: str, shortcut_path: str):
        """Добавляет ярлык в указанный ящик."""
        if box_id in self.boxes:
            self.boxes[box_id].add_item_from_path(shortcut_path)
        else:
            self.logger.warning(f"Попытка добавить ярлык в несуществующий ящик с ID: {box_id}")

    def hide_all_boxes(self):
        for box in self.boxes.values():
            box.hide()
        self.are_visible = False

    def show_all_boxes(self):
        for box in self.boxes.values():
            box.show()
        self.are_visible = True

    def toggle_visibility(self):
        """Переключает видимость всех ящиков."""
        if self.are_visible:
            self.hide_all_boxes()
        else:
            self.show_all_boxes()
        self.logger.info(f"Видимость ящиков переключена на: {self.are_visible}")