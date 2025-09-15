# ui/icon_utils.py
from PyQt5.QtGui import QPixmap, QPainter, QColor, QIcon
from PyQt5.QtCore import Qt


def create_themed_icon(icon_path: str, color_str: str) -> QIcon:
    """
    Загружает иконку из ресурсов и перекрашивает ее в указанный цвет.

    :param icon_path: Путь к иконке в ресурсах (например, ':/icons/icons/home.png')
    :param color_str: Цвет в формате HEX (например, '#f8f8f2')
    :return: Новый объект QIcon
    """
    # 1. Загружаем исходную иконку (предполагается, что она белая или черная)
    pixmap = QPixmap(icon_path)

    # 2. Создаем QPainter для рисования прямо на этой иконке
    painter = QPainter(pixmap)

    # 3. Устанавливаем "магический" режим наложения: CompositionMode_SourceIn
    # Этот режим говорит: "Рисуй источник (наш цвет) только там, где уже есть
    # непрозрачные пиксели в назначении (нашей иконке)".
    painter.setCompositionMode(QPainter.CompositionMode_SourceIn)

    # 4. "Заливаем" всю область иконки нужным нам цветом
    painter.fillRect(pixmap.rect(), QColor(color_str))

    # 5. Завершаем рисование
    painter.end()

    # 6. Возвращаем новую, перекрашенную иконку
    return QIcon(pixmap)