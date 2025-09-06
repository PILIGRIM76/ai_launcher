#installer/update_manager

import logging
import json
import shutil
from datetime import datetime
from pathlib import Path
from .utils import DATA_DIR

class UndoManager:
    def __init__(self, max_history=10):
        self.logger = logging.getLogger(__name__)
        self.history_stack = []
        self.max_history = max_history
        # --- ИЗМЕНЕНИЕ: История отмены теперь в AppData ---
        self.UNDO_DIR = DATA_DIR / "undo_history"
        self.UNDO_DIR.mkdir(exist_ok=True)
        self.logger.info("Менеджер отмены инициализирован.")

    def add_operation(self, operation_type, original_state):
        """Добавление операции в историю"""
        if len(self.history_stack) >= self.max_history:
            self.history_stack.pop(0)
        self.history_stack.append({
            'type': operation_type,
            'state': original_state,
            'timestamp': datetime.now()
        })

    def undo_last(self):
        """Отмена последней операции"""
        if not self.history_stack:
            return False
        last_op = self.history_stack.pop()
        # Восстановление предыдущего состояния
        self.restore_state(last_op['state'])
        return True