# Файл: core/box_widget.py
import logging
import os
from pathlib import Path

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QListView,
                             QListWidgetItem, QSizePolicy, QFrame,
                             QMenu, QAction, QPushButton, QHBoxLayout, QActionGroup,
                             QFileIconProvider)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QFileInfo, QTimer
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap

try:
    import win32api
    import win32gui
    import win32con
    import win32com.client
    from win32com.shell import shell, shellcon
    from PyQt5 import QtWinExtras

    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

from ui.custom_widgets import DraggableListWidget


class BoxWidget(QWidget):
    widget_moved = pyqtSignal(str, dict)
    configure_requested = pyqtSignal(str, str)
    rename_requested = pyqtSignal(str, str)
    delete_requested = pyqtSignal(str)
    refresh_requested = pyqtSignal(str)
    create_new_box_requested = pyqtSignal()
    state_changed = pyqtSignal(str, dict)
    file_dropped = pyqtSignal(str, str)
    request_unhide_original = pyqtSignal(str)

    def __init__(self, box_id: str, name: str, config: dict, global_border_settings: dict,
                 global_appearance_settings: dict, parent=None):
        super().__init__(parent)
        self.box_id = box_id
        self.name = name
        self.config = config
        self.global_border_settings = global_border_settings
        self.global_appearance_settings = global_appearance_settings
        self.logger = logging.getLogger(__name__)
        self.old_pos = self.pos()

        self.is_locked = self.config.get("is_locked", False)
        self.is_collapsed = True

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnBottomHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAcceptDrops(True)

        self.container_widget = QFrame(self)
        self.container_widget.setObjectName("ContainerWidget")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container_widget)

        self.layout = QVBoxLayout(self.container_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.header_widget = QWidget()
        header_layout = QHBoxLayout(self.header_widget)
        header_layout.setContentsMargins(8, 2, 2, 2)
        header_layout.setSpacing(0)
        self.title_label = QLabel(self.name)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.menu_button = QPushButton("...")
        self.menu_button.setFixedSize(24, 24)
        self.menu_button.setStyleSheet("border: none; font-size: 14pt; color: white;")
        self.menu_button.clicked.connect(self._show_context_menu)
        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.menu_button)
        self.layout.addWidget(self.header_widget)

        self.separator_line = QFrame()
        self.separator_line.setFrameShape(QFrame.HLine)
        self.separator_line.setFrameShadow(QFrame.Sunken)
        self.layout.addWidget(self.separator_line)

        self.file_list = DraggableListWidget()
        self.file_list.item_dragged_out.connect(self.request_unhide_original)

        self.file_list.setViewMode(
            QListView.IconMode if self.config.get("view_mode", "icon") == "icon" else QListView.ListMode)
        self.file_list.setMovement(QListView.Static)
        self.file_list.setResizeMode(QListView.Adjust)
        self.file_list.setWordWrap(True)
        self.file_list.setIconSize(QSize(48, 48))
        self.file_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.file_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.layout.addWidget(self.file_list)

        self.placeholder_widget = QWidget(self.file_list)
        placeholder_layout = QVBoxLayout(self.placeholder_widget)
        placeholder_layout.setAlignment(Qt.AlignCenter)
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(":/icons/box.png").pixmap(48, 48))
        icon_label.setAlignment(Qt.AlignCenter)
        text_label = QLabel("Перетащите значки файлов или\nпапок, чтобы поместить их в ящик.")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setWordWrap(True)
        placeholder_layout.addWidget(icon_label)
        placeholder_layout.addWidget(text_label)

        self.apply_styles()
        self._setup_animation()
        QTimer.singleShot(10, self._apply_state)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        shortcut_path = item.data(Qt.UserRole)
        if not shortcut_path or not WIN32_AVAILABLE: return

        try:
            shell_dispatch = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell_dispatch.CreateShortCut(shortcut_path)
            target_path = shortcut.TargetPath
            self.logger.info(f"Попытка запустить цель '{target_path}' из ярлыка '{shortcut_path}'")
            os.startfile(target_path)
        except Exception as e:
            self.logger.error(f"Не удалось запустить файл из ящика: {e}")

    def _remove_dragged_item(self, item: QListWidgetItem):
        self.file_list.takeItem(self.file_list.row(item))
        self._update_placeholder_visibility()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            self.logger.info(f"Файл '{file_path}' был перетащен на ящик {self.box_id}")
            self.file_dropped.emit(self.box_id, file_path)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _setup_animation(self):
        self.animation = QPropertyAnimation(self, b"size")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def _animate_to_state(self, collapsed: bool):
        self.animation.stop()
        start_size = self.size()

        header_height = self.header_widget.sizeHint().height() + 4

        full_height = self.config.get("size", [250, 300])[1]
        end_height = header_height if collapsed else full_height
        end_size = QSize(start_size.width(), end_height)

        if start_size == end_size: return

        if not collapsed:
            self.file_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            self.file_list.setVisible(True)
            self.separator_line.setVisible(True)

        self.animation.setStartValue(start_size)
        self.animation.setEndValue(end_size)

        try:
            self.animation.finished.disconnect()
        except TypeError:
            pass

        if collapsed:
            self.animation.finished.connect(self._on_collapse_animation_finished)

        self.animation.start()

    def _on_collapse_animation_finished(self):
        self.file_list.setVisible(False)
        self.separator_line.setVisible(False)
        self.file_list.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

    def _update_placeholder_visibility(self):
        is_empty = (self.file_list.count() == 0)
        self.placeholder_widget.setVisible(is_empty)
        if is_empty:
            self.placeholder_widget.resize(self.file_list.size())

    def _show_context_menu(self):
        menu = QMenu(self)
        appearance = self.config.get("appearance", {})
        bg_color_hex = appearance.get("color", "#2D2D2D")
        menu_color = QColor(bg_color_hex).darker(110)
        menu_color_rgba = f"rgba({menu_color.red()}, {menu_color.green()}, {menu_color.blue()}, 240)"
        hover_color = menu_color.lighter(130)
        menu_stylesheet = f"""
            QMenu {{ background-color: {menu_color_rgba}; color: white; border: 1px solid {hover_color.name()}; }}
            QMenu::item:selected {{ background-color: {hover_color.name()}; }}
        """
        menu.setStyleSheet(menu_stylesheet)
        create_menu = menu.addMenu("Создать ящик")
        create_new_action = create_menu.addAction("Создать новый ящик")
        create_new_action.triggered.connect(self.create_new_box_requested)
        view_menu = menu.addMenu("Вид")
        list_mode_action = view_menu.addAction("Режим списка")
        list_mode_action.setCheckable(True)
        list_mode_action.setChecked(self.config.get("view_mode", "icon") == "list")
        list_mode_action.triggered.connect(lambda checked: self.set_view_mode("list" if checked else "icon"))
        view_menu.addSeparator()
        view_menu.addAction("Изменить внешний вид...").triggered.connect(
            lambda: self.configure_requested.emit(self.box_id))
        sort_menu = menu.addMenu("Сортировать по")
        sort_group = QActionGroup(self)
        sort_group.setExclusive(True)
        sort_actions = {
            "none": sort_group.addAction(QAction("Отсутствует", self, checkable=True)),
            "name": sort_group.addAction(QAction("Имя", self, checkable=True))
        }
        current_sort = self.config.get("sort_by", "none")
        sort_actions[current_sort].setChecked(True)
        for key, action in sort_actions.items():
            action.triggered.connect(lambda checked, k=key: self.set_sort_by(k))
        sort_menu.addActions(sort_group.actions())
        menu.addSeparator()
        menu.addAction("Настройки...").triggered.connect(lambda: self.configure_requested.emit(self.box_id))
        menu.addAction("Обновить значки").triggered.connect(lambda: self.refresh_requested.emit(self.box_id))
        menu.addAction("Переименовать ящик").triggered.connect(
            lambda: self.rename_requested.emit(self.box_id, self.name))
        lock_action = menu.addAction("Замороженный ящик")
        lock_action.setCheckable(True)
        lock_action.setChecked(self.is_locked)
        lock_action.triggered.connect(self.toggle_lock)
        menu.addAction("Удалить ящик").triggered.connect(lambda: self.delete_requested.emit(self.box_id))
        menu.exec_(self.menu_button.mapToGlobal(QPoint(0, self.menu_button.height())))

    def _apply_state(self):
        is_visible = not self.is_collapsed
        self.file_list.setVisible(is_visible)
        self.separator_line.setVisible(is_visible)

        if self.is_collapsed:
            self.file_list.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        else:
            self.file_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        header_height = self.header_widget.sizeHint().height() + 4
        full_height = self.config.get("size", [250, 300])[1]
        initial_height = header_height if self.is_collapsed else full_height

        # Убираем setFixedHeight, чтобы анимация могла работать
        self.setMinimumHeight(header_height)
        if not self.is_collapsed:
            self.setMaximumHeight(full_height)

        self.resize(self.size().width(), initial_height)
        self._update_placeholder_visibility()

    def toggle_lock(self, checked):
        self.is_locked = checked
        self.state_changed.emit(self.box_id, {"is_locked": self.is_locked})
        self.logger.info(f"Ящик {self.box_id} заморожен: {self.is_locked}")

    def set_view_mode(self, mode):
        self.file_list.setViewMode(QListView.ListMode if mode == "list" else QListView.IconMode)
        self.state_changed.emit(self.box_id, {"view_mode": mode})
        self.logger.info(f"Ящик {self.box_id} сменил режим вида на: {mode}")

    def set_sort_by(self, criterion):
        self.state_changed.emit(self.box_id, {"sort_by": criterion})
        self.logger.info(f"Ящик {self.box_id} отсортирован по: {criterion}")
        self._apply_sorting()

    def update_styles(self, new_config: dict, global_border_settings: dict, global_appearance_settings: dict):
        self.logger.info(f"Виджет {self.box_id} получил команду на обновление стилей.")
        self.config = new_config
        self.global_border_settings = global_border_settings
        self.global_appearance_settings = global_appearance_settings
        self.name = new_config.get("name", self.name)
        self.title_label.setText(self.name)
        self.apply_styles()
        self._apply_state()

    def apply_styles(self):
        appearance = self.config.get("appearance", {})
        bg_color_hex = appearance.get("color", "#2D2D2D")
        transparency_bg = self.global_appearance_settings.get("transparency_bg", 85)
        header_visibility = self.global_appearance_settings.get("header_visibility", "always")
        font_str = appearance.get("font", "Segoe UI,10")
        rounded_corners = "8px"
        border_enabled = self.global_border_settings.get("enabled", False)
        border_width = self.global_border_settings.get("width", 1)
        border_color = self.global_border_settings.get("color", "#000000")
        border_style = f"{border_width}px solid {border_color}" if border_enabled else "none"
        self.logger.info(f"Применение стиля для {self.box_id}: Цвет={bg_color_hex}, Граница={border_style}")
        try:
            font_parts = font_str.split(',')
            font_family = font_parts[0].strip()
            font_size = int(font_parts[1].strip())
        except (ValueError, IndexError):
            font_family = "Segoe UI";
            font_size = 10
        color = QColor(bg_color_hex)
        alpha = int(255 * (transparency_bg / 100.0))
        bg_rgba = f"rgba({color.red()}, {color.green()}, {color.blue()}, {alpha / 255.0})"
        header_color = color.darker(130)
        header_rgba = f"rgba({header_color.red()}, {header_color.green()}, {header_color.blue()}, {alpha / 255.0})"
        self.container_widget.setStyleSheet(f"""
            #ContainerWidget {{
                background-color: {bg_rgba};
                border-radius: {rounded_corners};
                border: {border_style};
            }}
        """)
        self.title_label.setFont(QFont(font_family, font_size, QFont.Bold))
        self.header_widget.setStyleSheet(f"background-color: transparent; border: none;")
        self.file_list.setStyleSheet(
            f"background-color: transparent; border: none; padding: 4px; padding-bottom: 10px;")
        self.placeholder_widget.setStyleSheet("color: #dddddd;")
        self.separator_line.setStyleSheet(f"background-color: {border_color};")
        if header_visibility == "never":
            self.header_widget.hide()
        elif header_visibility == "on_hover":
            self.header_widget.hide()
        else:
            self.header_widget.show()

    def enterEvent(self, event):
        if self.global_appearance_settings.get("header_visibility") == "on_hover":
            self.header_widget.show()

        self.is_collapsed = False
        self._animate_to_state(collapsed=False)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.global_appearance_settings.get("header_visibility") == "on_hover":
            self.header_widget.hide()

        self.is_collapsed = True
        self._animate_to_state(collapsed=True)
        super().leaveEvent(event)

    def _get_file_icon(self, path_str: str) -> QIcon:
        if not WIN32_AVAILABLE:
            return QFileIconProvider().icon(QFileInfo(path_str))
        try:
            flags = shellcon.SHGFI_ICON | shellcon.SHGFI_USEFILEATTRIBUTES | shellcon.SHGFI_LARGEICON
            ret, info = shell.SHGetFileInfo(path_str, 0, flags)
            h_icon = info[0]
            if h_icon == 0:
                return QFileIconProvider().icon(QFileInfo(path_str))
            pixmap = QtWinExtras.QtWin.fromHICON(h_icon)
            win32gui.DestroyIcon(h_icon)
            return QIcon(pixmap)
        except Exception as e:
            self.logger.warning(f"Не удалось извлечь Win32 иконку для {path_str}: {e}")
            return QFileIconProvider().icon(QFileInfo(path_str))

    def add_item_from_path(self, file_path_str: str):
        file_path = Path(file_path_str)
        if not file_path.exists(): return

        icon = self._get_file_icon(file_path_str)
        item = QListWidgetItem(icon, file_path.stem)
        item.setData(Qt.UserRole, str(file_path))
        self.file_list.addItem(item)
        self._update_placeholder_visibility()

    def refresh_items(self, file_paths: list):
        self.file_list.clear()
        self.logger.info(f"Обновление значков для ящика {self.box_id}. Найдено {len(file_paths)} файлов.")
        for path in file_paths:
            self.add_item_from_path(path)
        self._apply_sorting()
        self._apply_state()

    def _apply_sorting(self):
        sort_by = self.config.get("sort_by", "none")
        if sort_by == "name":
            self.file_list.sortItems(Qt.AscendingOrder)

    def mousePressEvent(self, event):
        if not self.is_locked and event.button() == Qt.LeftButton and self.header_widget.geometry().contains(
                event.pos()):
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if not self.is_locked and event.buttons() == Qt.LeftButton and self.header_widget.geometry().contains(
                event.pos()):
            delta = QPoint(event.globalPos() - self.old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = self.pos()
            self.widget_moved.emit(self.box_id, {"position": [pos.x(), pos.y()]})

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_placeholder_visibility()