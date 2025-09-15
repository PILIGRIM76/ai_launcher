# core/hotkey_manager.py
import logging
from PyQt5.QtCore import QObject, pyqtSignal, QThread
from pynput import keyboard

class HotkeyListener(QObject):
    """
    Слушатель, работающий в отдельном потоке для отслеживания глобальных хоткеев.
    """
    # Сигналы для каждого действия
    toggle_boxes_visibility = pyqtSignal()
    open_search = pyqtSignal()

    def __init__(self, hotkeys_config: dict):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.hotkeys = self._parse_hotkeys(hotkeys_config)
        self.listener = None
        self.current_keys = set()

    def _parse_hotkeys(self, config):
        """Преобразует строки хоткеев в формат, понятный pynput."""
        parsed = {}
        for action, combo_str in config.items():
            keys = set()
            parts = combo_str.lower().split('+')
            for part in parts:
                try:
                    # Для специальных клавиш (alt, ctrl, shift)
                    key = getattr(keyboard.Key, part)
                    keys.add(key)
                except AttributeError:
                    # Для обычных буквенно-цифровых клавиш
                    keys.add(keyboard.KeyCode.from_char(part))
            parsed[action] = keys
        self.logger.info(f"Загружены горячие клавиши: {parsed}")
        return parsed

    def _on_press(self, key):
        self.current_keys.add(key)
        for action, combo in self.hotkeys.items():
            if combo.issubset(self.current_keys):
                self.logger.info(f"Сработала горячая клавиша для действия: '{action}'")
                if action == "show_hide_boxes":
                    self.toggle_boxes_visibility.emit()
                elif action == "open_search":
                    self.open_search.emit()
                # Сбрасываем, чтобы избежать многократного срабатывания при удержании
                self.current_keys.clear()

    def _on_release(self, key):
        if key in self.current_keys:
            self.current_keys.remove(key)

    def run(self):
        """Запускает слушатель в текущем потоке."""
        with keyboard.Listener(on_press=self._on_press, on_release=self._on_release) as listener:
            self.listener = listener
            listener.join()

    def stop(self):
        if self.listener:
            self.listener.stop()
            self.logger.info("Слушатель горячих клавиш остановлен.")


class HotkeyManager(QObject):
    """
    Управляет жизненным циклом слушателя горячих клавиш в отдельном потоке.
    """
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.thread = QThread()
        self.listener = HotkeyListener(self.config.get("hotkeys", {}))
        self.listener.moveToThread(self.thread)

        # Запуск слушателя при старте потока
        self.thread.started.connect(self.listener.run)
        # Остановка слушателя перед завершением потока
        self.thread.finished.connect(self.listener.stop)

    def start(self):
        if not self.thread.isRunning():
            self.thread.start()

    def stop(self):
        if self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()