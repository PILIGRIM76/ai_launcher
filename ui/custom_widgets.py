# Файл: ui/custom_widgets.py
import os
from PyQt5.QtWidgets import QListWidget, QListWidgetItem
from PyQt5.QtCore import Qt, pyqtSignal, QMimeData, QUrl, QPoint
from PyQt5.QtGui import QDrag


class DraggableListWidget(QListWidget):
    item_dragged_out = pyqtSignal(QListWidgetItem)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(self.DragOnly)
        self.setSelectionMode(self.SingleSelection)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return

        file_path = item.data(Qt.UserRole)
        if not file_path or not os.path.exists(file_path):
            return

        mimeData = QMimeData()
        mimeData.setUrls([QUrl.fromLocalFile(file_path)])

        drag = QDrag(self)
        drag.setMimeData(mimeData)

        pixmap = item.icon().pixmap(48, 48)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(24, 24))

        # --- НАЧАЛО ИЗМЕНЕНИЯ: Используем CopyAction, так как Windows предпочитает его ---
        result = drag.exec_(Qt.CopyAction | Qt.MoveAction)

        # Проверяем, была ли операция успешной (не отменена)
        if result != Qt.IgnoreAction:
            # Поскольку мы не можем надежно отследить, была ли это копия или перемещение,
            # мы просто удаляем наш ярлык. Пользователь всегда может его восстановить,
            # перетащив обратно или через "Обновить значки".
            try:
                os.remove(file_path)
                self.item_dragged_out.emit(item)
            except OSError as e:
                print(f"Не удалось удалить ярлык после перетаскивания: {e}")
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---