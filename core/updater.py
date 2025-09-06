# core/updater.py
import requests
import logging
from packaging import version
from PyQt5.QtCore import QObject, pyqtSignal

# --- ИЗМЕНЕНИЕ: Указываем правильный URL на ваш репозиторий ---
VERSION_URL = "https://raw.githubusercontent.com/PILIGRIM76/ai_launcher/master/version.json"


class Updater(QObject):
    update_available = pyqtSignal(str, str)  # (новая версия, ссылка на скачивание)

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
        self.logger = logging.getLogger(__name__)

    def check_for_updates(self):
        self.logger.info(f"Проверка обновлений... Текущая версия: {self.current_version}")
        try:
            # Добавляем headers, чтобы избежать кэширования
            headers = {'Cache-Control': 'no-cache'}
            response = requests.get(VERSION_URL, timeout=5, headers=headers)
            response.raise_for_status()

            data = response.json()
            latest_ver_str = data.get("latest_version")
            download_url = data.get("download_url")

            if not latest_ver_str or not download_url:
                self.logger.warning("В файле версии отсутствуют необходимые поля.")
                return

            latest_ver = version.parse(latest_ver_str)
            current_ver = version.parse(self.current_version)

            if latest_ver > current_ver:
                self.logger.info(f"Доступна новая версия: {latest_ver_str}")
                self.update_available.emit(latest_ver_str, download_url)
            else:
                self.logger.info("У вас установлена последняя версия.")

        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Не удалось проверить обновления: {e}")
        except Exception as e:
            self.logger.error(f"Произошла ошибка при проверке обновлений: {e}")