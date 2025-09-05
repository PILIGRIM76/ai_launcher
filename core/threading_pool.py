#core/threading_pool
from PyQt5.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal
import logging

logger = logging.getLogger(__name__)

class WorkerSignals(QObject):
    """Сигналы для рабочего потока"""
    error = pyqtSignal(tuple)
    finished = pyqtSignal()

class FileTask(QRunnable):
    def __init__(self, task_fn, *args, **kwargs):
        super().__init__()
        self.task_fn = task_fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        try:
            self.task_fn(*self.args, **self.kwargs)
        except Exception as e:
            logger.error(f"Ошибка в фоновой задаче '{self.task_fn.__name__}': {e}", exc_info=True)
            # self.signals.error.emit((type(e), e, traceback.format_exc())) # Для более детальной отладки
        finally:
            self.signals.finished.emit()


class ThreadManager:
    def __init__(self, max_threads=4):
        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(max_threads)
        logger.info(f"Пул потоков инициализирован (макс. потоков: {max_threads})")

    def start_task(self, task_fn, *args, **kwargs):
        task = FileTask(task_fn, *args, **kwargs)
        self.thread_pool.start(task)
        logger.info(f"Задача '{task_fn.__name__}' добавлена в пул потоков.")