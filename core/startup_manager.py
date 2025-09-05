# core/startup_manager.py
import winreg
import sys
import os
import logging

# --- ИЗМЕНЕНИЕ: Получаем именованный логгер ---
logger = logging.getLogger(__name__)

APP_NAME = "DesktopManager"
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"

def get_run_command():
    python_exe = sys.executable
    script_path = os.path.abspath(sys.argv[0])
    return f'"{python_exe}" "{script_path}"'

def is_enabled():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        # --- ИЗМЕНЕНИЕ: Используем logger ---
        logger.error(f"Ошибка при проверке статуса автозапуска: {e}")
        return False

def enable():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
        command = get_run_command()
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        # --- ИЗМЕНЕНИЕ: Используем logger ---
        logger.info(f"Автозапуск включен. Команда: {command}")
        return True
    except Exception as e:
        logger.error(f"Не удалось включить автозапуск: {e}")
        return False

def disable():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        # --- ИЗМЕНЕНИЕ: Используем logger ---
        logger.info("Автозапуск отключен.")
        return True
    except FileNotFoundError:
        return True
    except Exception as e:
        logger.error(f"Не удалось отключить автозапуск: {e}")
        return False