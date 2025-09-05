# core/updater.py
import logging
import requests
from PyQt5.QtCore import QObject, pyqtSignal


class Updater(QObject):
    # Сигналы для отправки результатов в основной поток GUI
    # (новая_версия, ссылка_на_скачивание)
    update_available = pyqtSignal(str, str)
    up_to_date = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, current_version, github_repo):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.current_version = current_version
        # Формируем URL для API GitHub
        self.api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"

    def check_for_updates(self):
        """
        Выполняет проверку обновлений. Этот метод предназначен для запуска в отдельном потоке.
        """
        self.logger.info(f"Проверка обновлений по адресу: {self.api_url}")
        try:
            response = requests.get(self.api_url, timeout=10)
            # Проверяем, что запрос успешен (код 200)
            response.raise_for_status()

            data = response.json()
            latest_version = data['tag_name'].lstrip('v')  # Убираем 'v' из 'v1.1.0'
            download_url = data['html_url']

            self.logger.info(f"Текущая версия: {self.current_version}, Последняя версия на GitHub: {latest_version}")

            # Сравниваем версии. Для простоты сравниваем как строки.
            # Для сложных версий (1.10.0 vs 1.9.0) лучше использовать библиотеку 'semver'.
            if latest_version > self.current_version:
                self.update_available.emit(latest_version, download_url)
            else:
                self.up_to_date.emit("У вас установлена последняя версия.")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка сети при проверке обновлений: {e}")
            self.error.emit("Ошибка сети. Не удалось проверить обновления.")
        except KeyError:
            self.logger.error("Ошибка парсинга ответа от GitHub. Возможно, нет релизов.")
            self.error.emit("Не удалось получить информацию о версии с GitHub.")
        except Exception as e:
            self.logger.error(f"Неизвестная ошибка при проверке обновлений: {e}")
            self.error.emit("Произошла неизвестная ошибка.")