# core/watcher.py
import time
import logging
from PyQt5.QtCore import QThread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class DesktopHandler(FileSystemEventHandler):
    """
    Обработчик событий файловой системы.
    Когда watchdog замечает событие, он передает его сюда.
    """

    def __init__(self, organizer):
        super().__init__()
        self.organizer = organizer
        self.logger = logging.getLogger(__name__)
        # Защита от дублирующихся событий, которые иногда генерирует ОС
        self.last_event_time = 0
        self.last_event_path = ""

    def on_created(self, event):
        """Вызывается, когда в отслеживаемой папке создается новый файл или папка."""
        try:
            # Нас интересуют только файлы
            if not event.is_directory:
                current_time = time.time()
                if (current_time - self.last_event_time < 1) and (event.src_path == self.last_event_path):
                    return  # Игнорируем дублирующееся событие

                self.last_event_time = current_time
                self.last_event_path = event.src_path

                # Даем файлу время на завершение записи (например, при скачивании)
                time.sleep(1)

                self.logger.info(f"Наблюдатель обнаружил новый файл: {event.src_path}")
                # Передаем файл на обработку в органайзер
                self.organizer.handle_new_file(event.src_path)
        except Exception as e:
            self.logger.error(f"Ошибка в обработчике файловых событий: {e}", exc_info=True)


class DesktopWatcher(QThread):
    """
    Наблюдатель, работающий в отдельном потоке, чтобы не блокировать основной интерфейс.
    """

    def __init__(self, organizer, path_to_watch):
        super().__init__()
        self.organizer = organizer
        self.path_to_watch = path_to_watch
        self.logger = logging.getLogger(__name__)
        self.observer = Observer()
        self._is_running = True

    def run(self):
        """Этот метод выполняется при запуске потока (`.start()`)."""
        event_handler = DesktopHandler(self.organizer)
        self.observer.schedule(event_handler, self.path_to_watch, recursive=False)
        self.observer.start()
        self.logger.info(f"Наблюдение за папкой '{self.path_to_watch}' запущено.")

        try:
            while self._is_running:
                time.sleep(1)
        except Exception as e:
            self.logger.error(f"Ошибка в потоке наблюдателя: {e}")
        finally:
            self.observer.stop()
            self.observer.join()
            self.logger.info("Наблюдение остановлено.")

    def stop(self):
        """Сигнализирует потоку о необходимости завершения."""
        self._is_running = False