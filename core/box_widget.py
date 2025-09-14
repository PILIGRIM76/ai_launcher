# core/box_widget.py
import logging
from pathlib import Path
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListView, QSizeGrip, QListWidgetItem
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon, QColor


class BoxWidget(QWidget):
    # --- НАЧАЛО ИЗМЕНЕНИЯ: Сигнал теперь передает ID и словарь свойств ---
    widget_moved = pyqtSignal(str, dict)
    widget_resized = pyqtSignal(str, dict)

    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    def __init__(self, box_id: str, name: str, config: dict, parent=None):
        super().__init__(parent)
        self.box_id = box_id
        self.name = name
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.old_pos = self.pos()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self._apply_styles()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)

        self.header = QLabel(self.name)
        self.header.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.header)

        self.file_list = QListWidget()
        self.file_list.setViewMode(QListView.IconMode)
        self.file_list.setMovement(QListView.Static)
        self.file_list.setResizeMode(QListView.Adjust)
        self.file_list.setWordWrap(True)
        self.file_list.setIconSize(QSize(48, 48))
        self.layout.addWidget(self.file_list)

        size_grip = QSizeGrip(self)
        self.layout.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)

        self._apply_styles()  # Применяем стили после создания всех элементов

    def _apply_styles(self):
        """Применяет визуальные стили на основе конфига."""
        bg_color_hex = self.config.get("color", "#2D2D2D")
        transparency = self.config.get("transparency", 85)
        font_size = self.config.get("font_size", 10)

        # Преобразуем HEX в RGBA
        color = QColor(bg_color_hex)
        alpha = int(255 * (transparency / 100.0))
        bg_rgba = f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha / 255.0})"

        # Создаем цвет заголовка чуть темнее
        header_color = color.darker(120)
        header_rgba = f"rgba({header_color.red()}, {header_color.green()}, {header_color.blue()}, {alpha / 255.0})"

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_rgba};
                border-radius: 8px;
                color: white;
            }}
            QListWidget {{ 
                border: none; 
                background-color: transparent;
            }}
            QSizeGrip {{
                width: 10px; height: 10px;
                background-color: transparent;
            }}
        """)

        if hasattr(self, 'header'):
            self.header.setFont(QFont("Segoe UI", font_size, QFont.Bold))
            self.header.setStyleSheet(
                f"background-color: {header_rgba}; "
                "border-top-left-radius: 8px; "
                "border-top-right-radius: 8px; "
                "padding: 5px;"
            )

    def add_item_from_path(self, file_path_str: str):
        """Добавляет элемент в список, извлекая иконку и имя."""
        file_path = Path(file_path_str)
        if not file_path.exists():
            self.logger.warning(f"Файл для добавления в ящик не найден: {file_path_str}")
            return

        # TODO: Реализовать асинхронное извлечение иконок для производительности
        # Пока используем стандартную иконку файла
        icon = QIcon.fromTheme("document-new", QIcon(":/icons/file.png"))
        item = QListWidgetItem(icon, file_path.stem)
        item.setData(Qt.UserRole, str(file_path))  # Сохраняем полный путь
        self.file_list.addItem(item)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.header.geometry().contains(event.pos()):
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.header.geometry().contains(event.pos()):
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.pos()
            self.widget_moved.emit(self.box_id, {"position": [pos.x(), pos.y()]})

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self.size()
        self.widget_resized.emit(self.box_id, {"size": [size.width(), size.height()]})