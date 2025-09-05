#installer/update_manager
class UndoManager:
    def __init__(self, max_history=10):
        self.history_stack = []
        self.max_history = max_history

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