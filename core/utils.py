# Файл: core/utils.py
import os
import json
import logging
from pathlib import Path

from PyQt5.QtWidgets import QMessageBox

APP_NAME = "DesktopManager"
DATA_DIR = Path(os.getenv('LOCALAPPDATA', Path.home())) / APP_NAME
CONFIG_PATH = DATA_DIR / "config.json"


def setup_logging():
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
    # --- НАЧАЛО ИЗМЕНЕНИЯ: Убираем видимость заголовка из индивидуальных настроек ---
    default_box_appearance = {
        "color": "#3A3A3A", "font": "Segoe UI,16"
    }
    # --- КОНЕЦ ИЗМЕНЕНИЯ ---
    default_box_state = {
        "is_collapsed": False, "is_locked": False, "view_mode": "icon",
        "sort_by": "none", "sort_order": "asc"
    }

    default_config = {
        "language": "ru", "theme": "light", "auto_organize": True,
        "run_initial_organization": True, "boxes_enabled": True,
        "global_border_settings": {
            "enabled": True, "color": "#000000", "width": 1
        },
        # --- НАЧАЛО ИЗМЕНЕНИЯ: Добавляем видимость заголовка в глобальные настройки ---
        "global_appearance_settings": {
            "transparency_bg": 85,
            "header_visibility": "always"
        },
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---
        "desktop_boxes": [
            {**{"id": "default_programs", "name": "Программы", "position": [50, 50], "size": [250, 300]},
             **default_box_state, "appearance": default_box_appearance},
            {**{"id": "default_images", "name": "Изображения", "position": [320, 50], "size": [250, 300]},
             **default_box_state, "appearance": default_box_appearance},
            {**{"id": "default_screenshots", "name": "Скриншоты", "position": [590, 50], "size": [250, 300]},
             **default_box_state, "appearance": default_box_appearance},
            {**{"id": "default_archives", "name": "Архивы", "position": [50, 370], "size": [250, 300]},
             **default_box_state, "appearance": default_box_appearance}
        ],
        "hotkeys": {"show_hide_boxes": "alt+d", "open_search": "alt+space"},
        "advanced_rules": [
            {"name": "Ярлыки", "enabled": True, "conditions": [{"type": "extension_is", "value": ".lnk"}],
             "action": {"type": "assign_to_box", "box_id": "default_programs"}},
            {"name": "Приложения", "enabled": True, "conditions": [{"type": "extension_is", "value": ".exe"}],
             "action": {"type": "assign_to_box", "box_id": "default_programs"}},
            {"name": "Установщики", "enabled": True, "conditions": [{"type": "extension_is", "value": ".msi"}],
             "action": {"type": "assign_to_box", "box_id": "default_programs"}},
            {"name": "PNG Изображения", "enabled": True, "conditions": [{"type": "extension_is", "value": ".png"}],
             "action": {"type": "assign_to_box", "box_id": "default_images"}},
            {"name": "JPG Изображения", "enabled": True, "conditions": [{"type": "extension_is", "value": ".jpg"}],
             "action": {"type": "assign_to_box", "box_id": "default_images"}},
            {"name": "JPEG Изображения", "enabled": True, "conditions": [{"type": "extension_is", "value": ".jpeg"}],
             "action": {"type": "assign_to_box", "box_id": "default_images"}},
            {"name": "Скриншоты (Снимок)", "enabled": True,
             "conditions": [{"type": "name_contains", "value": "Снимок"}],
             "action": {"type": "assign_to_box", "box_id": "default_screenshots"}},
            {"name": "Скриншоты (Screenshot)", "enabled": True,
             "conditions": [{"type": "name_contains", "value": "Screenshot"}],
             "action": {"type": "assign_to_box", "box_id": "default_screenshots"}},
            {"name": "ZIP Архивы", "enabled": True, "conditions": [{"type": "extension_is", "value": ".zip"}],
             "action": {"type": "assign_to_box", "box_id": "default_archives"}},
            {"name": "RAR Архивы", "enabled": True, "conditions": [{"type": "extension_is", "value": ".rar"}],
             "action": {"type": "assign_to_box", "box_id": "default_archives"}},
            {"name": "7Z Архивы", "enabled": True, "conditions": [{"type": "extension_is", "value": ".7z"}],
             "action": {"type": "assign_to_box", "box_id": "default_archives"}}
        ],
        "categories": {"Программы": [".exe", ".lnk", ".msi", ".bat"],
                       "Документы": [".doc", ".docx", ".pdf", ".xls", ".xlsx", ".ppt", ".pptx", ".txt"],
                       "Изображения": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
                       "Медиа": [".mp3", ".mp4", ".avi", ".mkv", ".mov", ".wav"],
                       "Архивы": [".zip", ".rar", ".7z", ".tar", ".gz"],
                       "Код": [".py", ".js", ".html", ".css", ".java", ".cpp", ".cs"], "Другое": []},
        "exceptions": [], "sort_options": {"by_type": True, "by_name": False, "by_date": False, "by_size": False},
        "clean_options": {"remove_broken_shortcuts": True, "remove_temp_files": True, "remove_by_ext": True},
        "security": {"use_recycle_bin": True, "backup_before_operations": True},
        "wallpapers": {}, "widgets": {}
    }

    if not CONFIG_PATH.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Файл конфигурации не найден. Создается новый config.json с ящиками и правилами по умолчанию.")
        save_config(default_config)
        return default_config
    try:
        with open(CONFIG_PATH, "r", encoding='utf-8') as f:
            user_config = json.load(f)
            for key, value in default_config.items():
                user_config.setdefault(key, value)
            return user_config
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Ошибка загрузки config.json: {e}. Будут использованы значения по умолчанию.")
        return default_config


def save_config(config: dict) -> None:
    try:
        with open(CONFIG_PATH, "w", encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info("Конфигурация успешно сохранена.")
    except IOError as e:
        logger.error(f"Ошибка сохранения конфигурации: {e}")


def get_all_desktop_paths() -> list:
    user_profile = os.environ.get('USERPROFILE', '')
    public_profile = os.environ.get('PUBLIC', '')
    paths = []
    if user_profile: paths.append(os.path.join(user_profile, 'Desktop'))
    if public_profile: paths.append(os.path.join(public_profile, 'Desktop'))
    return [p for p in paths if os.path.isdir(p)]