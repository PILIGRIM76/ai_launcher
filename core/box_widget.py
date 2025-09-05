# core/box_widget.py
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QListView, QSizeGrip
from PyQt5.QtCore import Qt, QPoint, pyqtSignal
from PyQt5.QtGui import QFont

class BoxWidget(QWidget):
    widget_moved = pyqtSignal(str, QPoint)
    widget_resized = pyqtSignal(str, object)

    def __init__(self, category_name, parent=None):
        super().__init__(parent)
        self.category_name = category_name
        self.logger = logging.getLogger(__name__)
        self.old_pos = self.pos()

        # --- НАСТРОЙКА ОКНА ---
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(45, 45, 45, 0.85);
                border-radius: 8px;
                color: white;
            }
        """)

        # --- МАКЕТ ---
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(1, 1, 1, 1)

        # --- ЗАГОЛОВОК ---
        self.header = QLabel(self.category_name)
        self.header.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.header.setAlignment(Qt.AlignCenter)
        self.header.setStyleSheet("background-color: rgba(60, 60, 60, 0.9); border-top-left-radius: 8px; border-top-right-radius: 8px; padding: 5px;")
        self.layout.addWidget(self.header)

        # --- СПИСОК ФАЙЛОВ ---
        self.file_list = QListWidget()
        self.file_list.setViewMode(QListView.IconMode)
        self.file_list.setMovement(QListView.Static)
        self.file_list.setResizeMode(QListView.Adjust)
        self.file_list.setWordWrap(True)
        self.file_list.setStyleSheet("QListWidget { border: none; }")
        self.layout.addWidget(self.file_list)

        # --- ИЗМЕНЕНИЕ РАЗМЕРА ---
        size_grip = QSizeGrip(self)
        self.layout.addWidget(size_grip, 0, Qt.AlignBottom | Qt.AlignRight)

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
            self.widget_moved.emit(self.category_name, self.pos())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.widget_resized.emit(self.category_name, self.size())

    def add_item(self, file_name, file_path):
        # TODO: Добавить реальные иконки файлов
        item = self.file_list.addItem(file_name)
        # item.setData(Qt.UserRole, file_path) # Сохраняем путь для будущего использования

    def filter_items(self, query):
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            is_visible = query.lower() in item.text().lower()
            item.setHidden(not is_visible)