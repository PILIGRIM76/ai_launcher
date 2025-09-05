# core/undo_manager.py
import logging
import json
import shutil
from datetime import datetime
from pathlib import Path


class UndoManager:
    def __init__(self, max_history=10):
        self.logger = logging.getLogger(__name__)
        self.history_stack = []
        self.max_history = max_history
        self.UNDO_DIR = Path("undo_history")
        self.UNDO_DIR.mkdir(exist_ok=True)
        self.logger.info("Менеджер отмены инициализирован.")

    def add_operation(self, operation_data: dict) -> None:
        """Добавление операции в историю."""
        try:
            operation_type = operation_data.get('type', 'unknown')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"{timestamp}_{operation_type}.json"
            filepath = self.UNDO_DIR / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(operation_data, f, indent=4, ensure_ascii=False)

            self.history_stack.append({
                'type': operation_type,
                'file': str(filepath),
                'timestamp': timestamp
            })
            self.logger.info(f"Операция '{operation_type}' добавлена в историю отмены.")

            # Ограничиваем размер истории
            if len(self.history_stack) > self.max_history:
                oldest = self.history_stack.pop(0)
                try:
                    Path(oldest['file']).unlink()
                except OSError as e:
                    self.logger.warning(f"Не удалось удалить старый файл истории: {e}")

        except Exception as e:
            self.logger.error(f"Ошибка добавления операции в историю: {e}", exc_info=True)

    def undo_last(self) -> (bool, str):
        """Отмена последней операции. Возвращает кортеж (успех, сообщение)."""
        if not self.history_stack:
            self.logger.warning("История операций пуста, отмена невозможна.")
            return False, "История операций пуста."

        last_op = self.history_stack.pop()
        op_type = last_op['type']
        op_file = Path(last_op['file'])

        try:
            with open(op_file, 'r', encoding='utf-8') as f:
                operation_data = json.load(f)

            if op_type == 'clean':
                self._undo_clean(operation_data)
            elif op_type in ['organize', 'sort']:
                self._undo_move(operation_data)
            else:
                raise NotImplementedError(f"Отмена для операции типа '{op_type}' не реализована.")

            op_file.unlink()  # Удаляем файл истории после успешной отмены
            msg = f"Операция '{op_type}' успешно отменена."
            self.logger.info(msg)
            return True, msg
        except Exception as e:
            self.logger.error(f"Ошибка отмены операции '{op_type}': {e}", exc_info=True)
            # Возвращаем операцию в стек, если отмена не удалась
            self.history_stack.append(last_op)
            return False, f"Ошибка отмены: {e}"

    def _undo_clean(self, operation_data: dict):
        """Отмена операции очистки (восстановление из корзины приложения)."""
        # ИСПРАВЛЕНИЕ: Абсолютный импорт
        from core.security import FileRecycleBin
        recycle_bin = FileRecycleBin()
        restored_count = 0
        for file_info in reversed(operation_data.get('removed_files', [])):
            try:
                recycle_bin.restore_file(file_info['backup'], file_info['original'])
                restored_count += 1
            except Exception as e:
                self.logger.warning(f"Не удалось восстановить файл {file_info['original']}: {e}")
        self.logger.info(f"Восстановлено {restored_count} файлов после очистки.")

    def _undo_move(self, operation_data: dict):
        """Отмена операций организации или сортировки (перемещение обратно)."""
        moved_count = 0
        for file_info in reversed(operation_data.get('moved_files', [])):
            try:
                src = Path(file_info['new'])
                dest = Path(file_info['original'])
                if src.exists():
                    dest.parent.mkdir(exist_ok=True, parents=True)
                    shutil.move(str(src), str(dest))
                    moved_count += 1
                else:
                    self.logger.warning(f"Файл для отмены перемещения не найден: {src}")
            except Exception as e:
                self.logger.warning(f"Не удалось отменить перемещение для {file_info['new']}: {e}")
        self.logger.info(f"Возвращено на место {moved_count} файлов.")