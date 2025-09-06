#core/utils.py
import os
import json
import logging
from pathlib import Path

from PyQt5.QtWidgets import QMessageBox

# --- ИЗМЕНЕНИЕ: Определяем правильное место для хранения данных ---
APP_NAME = "DesktopManager"
# C:\Users\<Имя>\AppData\Local\DesktopManager
DATA_DIR = Path(os.getenv('LOCALAPPDATA', Path.home())) / APP_NAME

# --- ИЗМЕНЕНИЕ: Путь к конфигу теперь внутри AppData ---
CONFIG_PATH = DATA_DIR / "config.json"

def setup_logging():
    """Настройка системы логирования."""
    # --- ИЗМЕНЕНИЕ: Логи теперь тоже в AppData ---
    log_dir = DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app_logs.txt"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
    return logging.getLogger(__name__)

logger = setup_logging()

def load_config() -> dict:
    # ... (остальной код функции без изменений) ...
    default_config = {
        "language": "ru", "auto_organize": True, "run_initial_organization": True,
        "categories": {
            "Программы": [".exe", ".lnk", ".msi", ".bat"], "Документы": [".doc", ".docx", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
            "Изображения": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"], "Медиа": [".mp3", ".mp4", ".avi", ".mkv", ".mov", ".wav"],
            "Архивы": [".zip", ".rar", ".7z", ".tar", ".gz"], "Код": [".py", ".js", ".html", ".css", ".java", ".cpp", ".cs"], "Другое": []
        },
        "exceptions": [], "sort_options": {"by_type": True, "by_name": False, "by_date": False, "by_size": False},
        "clean_options": {"remove_broken_shortcuts": True, "remove_temp_files": True, "remove_by_ext": True},
        "security": {"use_recycle_bin": True, "backup_before_operations": True}
    }

    if not CONFIG_PATH.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True) # Создаем папку, если ее нет
        logger.info("Файл конфигурации не найден. Создается новый config.json.")
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_PATH, "r", encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Ошибка загрузки config.json: {e}. Будут использованы значения по умолчанию.")
        return default_config

def save_config(config: dict) -> None:
    # ... (остальной код функции без изменений) ...
    try:
        with open(CONFIG_PATH, "w", encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info("Конфигурация успешно сохранена.")
    except IOError as e:
        logger.error(f"Ошибка сохранения конфигурации: {e}")


def _get_primary_desktop(self):
    """Возвращает путь к основному рабочему столу пользователя."""
    paths = get_all_desktop_paths()
    if not paths:
        QMessageBox.critical(self, "Ошибка", "Не удалось определить путь к рабочему столу.")
        return None
    return paths[0]  # Берем первый (самый главный) путь

def get_all_desktop_paths() -> list:
    # ... (остальной код функции без изменений) ...
    user_profile = os.environ.get('USERPROFILE', '')
    public_profile = os.environ.get('PUBLIC', '')
    paths = []
    if user_profile: paths.append(os.path.join(user_profile, 'Desktop'))
    if public_profile: paths.append(os.path.join(public_profile, 'Desktop'))
    return [p for p in paths if os.path.isdir(p)]