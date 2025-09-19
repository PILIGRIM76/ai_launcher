# Файл: ui/custom_widgets.py
import os
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QUrl, QPoint
from PyQt5.QtGui import QDrag


class DraggableListWidget(QListWidget):
    # --- НАЧАЛО ИЗМЕНЕНИЯ: Сигнал теперь передает путь к ярлыку ---
    item_dragged_out = pyqtSignal(str)  # shortcut_path

    # --- КОНЕЦ ИЗМЕНЕНИЯ ---

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(self.DragOnly)
        self.setSelectionMode(self.SingleSelection)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return

        shortcut_path = item.data(Qt.UserRole)
        if not shortcut_path or not os.path.exists(shortcut_path):
            return

        mimeData = QMimeData()
        mimeData.setUrls([QUrl.fromLocalFile(shortcut_path)])

        drag = QDrag(self)
        drag.setMimeData(mimeData)

        pixmap = item.icon().pixmap(48, 48)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(24, 24))

        # --- НАЧАЛО ИЗМЕНЕНИЯ: Используем MoveAction, так как мы хотим "переместить" файл из ящика ---
        result = drag.exec_(Qt.MoveAction)

        if result == Qt.MoveAction:
            # Сообщаем системе, что нужно сделать оригинал видимым и удалить ярлык
            self.item_dragged_out.emit(shortcut_path)
            # Удаляем сам элемент из списка в UI
            self.takeItem(self.row(item))
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---