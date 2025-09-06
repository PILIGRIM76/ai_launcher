#core/security.py
import os
import shutil
import logging
from datetime import datetime
from pathlib import Path
from .utils import DATA_DIR # --- ИЗМЕНЕНИЕ: Импортируем DATA_DIR

class FileRecycleBin:
    def __init__(self): # Убрали аргумент bin_dir
        self.logger = logging.getLogger(__name__)
        # --- ИЗМЕНЕНИЕ: Корзина теперь в AppData ---
        self.bin_dir = DATA_DIR / "recycle_bin"
        self.bin_dir.mkdir(exist_ok=True)
        self.logger.info(f"Корзина приложения инициализирована в: {self.bin_dir.resolve()}")

    def safe_delete(self, file_path_str: str) -> str:
        """Безопасное удаление с перемещением в корзину приложения."""
        try:
            file_path = Path(file_path_str)
            if not file_path.exists():
                raise FileNotFoundError(f"Файл для удаления не найден: {file_path}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            dest = self.bin_dir / f"{timestamp}_{file_path.name}"

            shutil.move(str(file_path), str(dest))
            self.logger.info(f"Файл '{file_path.name}' перемещен в корзину приложения.")
            return str(dest)
        except Exception as e:
            self.logger.error(f"Ошибка безопасного удаления файла {file_path_str}: {e}")
            raise

    def restore_file(self, backup_path_str: str, original_path_str: str) -> str:
        """Восстановление файла из корзины по оригинальному пути."""
        try:
            backup_path = Path(backup_path_str)
            if not backup_path.exists():
                raise FileNotFoundError(f"Резервная копия не найдена: {backup_path}")

            dest_path = Path(original_path_str)
            # Создаем родительские директории, если их нет
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(backup_path), str(dest_path))
            self.logger.info(f"Файл '{backup_path.name}' восстановлен в '{dest_path}'.")
            return str(dest_path)
        except Exception as e:
            self.logger.error(f"Ошибка восстановления файла {backup_path_str}: {e}")
            raise