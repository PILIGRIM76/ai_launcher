# core/wallpaper_manager.py
import logging
import ctypes
from pathlib import Path

class WallpaperManager:
    """
    Управляет установкой обоев рабочего стола Windows.
    """
    SPI_SETDESKWALLPAPER = 20

    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config

    def set_wallpaper(self, file_path: str):
        """
        Устанавливает статичное изображение в качестве обоев.
        """
        try:
            path = str(Path(file_path).resolve())
            ctypes.windll.user32.SystemParametersInfoW(self.SPI_SETDESKWALLPAPER, 0, path, 3)
            self.config['wallpapers'] = {
                "current_type": "static",
                "current_path": path
            }
            self.logger.info(f"Установлены обои: {path}")
            return True, "Обои успешно установлены."
        except Exception as e:
            self.logger.error(f"Ошибка установки обоев: {e}", exc_info=True)
            return False, f"Ошибка: {e}"

    def set_solid_color(self, color_hex: str):
        """
        Устанавливает сплошной цвет в качестве фона.
        Примечание: В Windows это реализуется через установку цвета и удаление пути к изображению.
        """
        try:
            # Преобразуем HEX в BGR int
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)

            # 1. Устанавливаем цвет фона в реестре
            # (Для простоты опустим, т.к. требует прямого редактирования реестра)

            # 2. Убираем текущие обои, чтобы отобразился цвет
            ctypes.windll.user32.SystemParametersInfoW(self.SPI_SETDESKWALLPAPER, 0, "", 3)
            self.config['wallpapers'] = {
                "current_type": "color",
                "current_path": color_hex
            }
            self.logger.info(f"Установлен сплошной цвет: {color_hex}. Для отображения может потребоваться перезагрузка.")
            return True, "Цвет установлен. Может потребоваться перезагрузка."
        except Exception as e:
            self.logger.error(f"Ошибка установки цвета: {e}", exc_info=True)
            return False, f"Ошибка: {e}"

    def set_live_wallpaper(self, video_path: str):
        """
        Заглушка для установки живых обоев.
        Это сложная функция, требующая отрисовки видео на корневом окне рабочего стола.
        """
        self.logger.warning("Функция живых обоев не реализована в этой версии.")
        return False, "Функция живых обоев не реализована."