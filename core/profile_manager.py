# core/profile_manager.py
import os
import json
import logging
from pathlib import Path


class ProfileManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.PROFILES_DIR = Path("profiles")
        self.PROFILES_DIR.mkdir(exist_ok=True)
        self.current_profile = "default"

    def save_profile(self, name: str, settings: dict) -> bool:
        """Сохранение профиля настроек"""
        try:
            if not name.strip():
                self.logger.error("Имя профиля не может быть пустым.")
                return False
            profile_path = self.PROFILES_DIR / f"{name}.json"
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Профиль '{name}' успешно сохранен.")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения профиля {name}: {e}")
            return False

    def load_profile(self, name: str) -> dict:
        """
        Загрузка профиля настроек.
        Исправлена ошибка при чтении пустого файла.
        """
        profile_path = self.PROFILES_DIR / f"{name}.json"
        if not profile_path.exists() or profile_path.stat().st_size == 0:
            self.logger.warning(f"Файл профиля '{name}' не найден или пуст.")
            return None

        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка декодирования JSON в профиле {name}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Не удалось загрузить профиль {name}: {e}")
            return None

    def list_profiles(self) -> list:
        """Получение списка доступных профилей"""
        return [p.stem for p in self.PROFILES_DIR.glob("*.json")]

    def delete_profile(self, name: str) -> bool:
        """Удаление файла профиля."""
        try:
            profile_path = self.PROFILES_DIR / f"{name}.json"
            if profile_path.exists():
                profile_path.unlink()
                self.logger.info(f"Профиль '{name}' удален.")
                return True
            else:
                self.logger.warning(f"Профиль '{name}' для удаления не найден.")
                return False
        except Exception as e:
            self.logger.error(f"Ошибка при удалении профиля '{name}': {e}")
            return False