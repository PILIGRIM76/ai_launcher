#core/scheduler.py
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

class AutoOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.scheduler = BackgroundScheduler(daemon=True)
        try:
            self.scheduler.start()
            self.logger.info("Планировщик задач запущен")
        except Exception as e:
            self.logger.error(f"Не удалось запустить планировщик: {e}")

    def schedule_task(self, task_fn, interval_hours=24):
        """Планирование регулярной задачи"""
        try:
            self.scheduler.add_job(
                task_fn,
                'interval',
                hours=interval_hours,
                next_run_time=datetime.now() + timedelta(seconds=10) # Небольшая задержка перед первым запуском
            )
            self.logger.info(f"Задача '{task_fn.__name__}' запланирована с интервалом {interval_hours} ч.")
        except Exception as e:
            self.logger.error(f"Ошибка планирования задачи: {e}")

    def shutdown(self):
        """Корректное завершение работы планировщика."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Планировщик задач остановлен.")