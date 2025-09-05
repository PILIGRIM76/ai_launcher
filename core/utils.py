# core/utils.py
import os
import json
import logging
from pathlib import Path

# --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ---
# Мы будем использовать pywin32 для надежного определения пути к рабочему столу
try:
    from win32com.shell import shell, shellcon
    PYWIN32_AVAILABLE = True
except ImportError:
    PYWIN32_AVAILABLE = False
# --- КОНЕЦ ИСПРАВЛЕНИЯ ---


# Определяем путь к конфигу относительно папки проекта
CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

def setup_logging():
    """Настройка системы логирования."""
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app_logs.txt"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler() # Вывод в консоль для отладки
        ]
    )
    # Отключаем слишком "шумные" логгеры
    logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)
    return logging.getLogger(__name__)

logger = setup_logging()

def load_config() -> dict:
    """Загрузка конфигурации приложения."""
    default_config = {
        "language": "ru",
        "auto_organize": True,
        "run_initial_organization": True,
        "categories": {
            "Программы": [".exe", ".lnk", ".msi", ".bat"],
            "Документы": [".doc", ".docx", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
            "Изображения": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
            "Медиа": [".mp3", ".mp4", ".avi", ".mkv", ".mov", ".wav"],
            "Архивы": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Код": [".py", ".js", ".html", ".css", ".java", ".cpp", ".cs"],
            "Другое": []
        },
        "exceptions": [],
        "sort_options": {"by_type": True, "by_name": False, "by_date": False, "by_size": False},
        "clean_options": {"remove_broken_shortcuts": True, "remove_temp_files": True, "remove_by_ext": True},
        "security": {"use_recycle_bin": True, "backup_before_operations": True}
    }

    if not CONFIG_PATH.exists():
        logger.info("Файл конфигурации не найден. Создается новый config.json со значениями по умолчанию.")
        save_config(default_config)
        return default_config

    try:
        with open(CONFIG_PATH, "r", encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Ошибка загрузки config.json: {e}. Будут использованы значения по умолчанию.")
        return default_config

def save_config(config: dict) -> None:
    """Сохранение конфигурации."""
    try:
        with open(CONFIG_PATH, "w", encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info("Конфигурация успешно сохранена.")
    except IOError as e:
        logger.error(f"Ошибка сохранения конфигурации: {e}")

# --- КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ ---
def get_desktop_path() -> str:
    """
    Надежно возвращает путь к рабочему столу текущего пользователя,
    независимо от языка системы.
    """
    if PYWIN32_AVAILABLE:
        try:
            # Спрашиваем у Windows, где находится рабочий стол
            path = shell.SHGetFolderPath(0, shellcon.CSIDL_DESKTOP, None, 0)
            logger.info(f"Обнаружен рабочий стол через pywin32: {path}")
            return path
        except Exception as e:
            logger.warning(f"Не удалось получить путь через pywin32: {e}. Используется запасной метод.")

    # Запасной метод, если pywin32 не сработал
    path = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
    logger.info(f"Используется запасной метод для определения рабочего стола: {path}")
    return path

def get_all_desktop_paths() -> list:
    """
    Возвращает список, содержащий путь к рабочему столу текущего пользователя.
    """
    desktop_path = get_desktop_path()
    if os.path.isdir(desktop_path):
        return [desktop_path]
    return []