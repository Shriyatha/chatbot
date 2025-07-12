import json
import os
from typing import Dict, List

class MemoryManager:
    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.memory_file = f"user_{user_id}_memory.json"
        self._initialize_memory()

    def _initialize_memory(self):
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w') as f:
                json.dump({
                    "conversation_history": [],
                    "todo_list": []
                }, f)

    def _load_memory(self) -> Dict:
        with open(self.memory_file, 'r') as f:
            return json.load(f)

    def _save_memory(self, data: Dict):
        with open(self.memory_file, 'w') as f:
            json.dump(data, f)

    def add_to_conversation(self, role: str, message: str):
        memory = self._load_memory()
        memory["conversation_history"].append({
            "role": role,
            "message": message
        })
        self._save_memory(memory)

    def get_conversation_history(self) -> List[Dict]:
        memory = self._load_memory()
        return memory["conversation_history"]

    def add_todo(self, task: str):
        memory = self._load_memory()
        memory["todo_list"].append(task)
        self._save_memory(memory)

    def remove_todo(self, task: str):
        memory = self._load_memory()
        if task in memory["todo_list"]:
            memory["todo_list"].remove(task)
            self._save_memory(memory)
            return True
        return False

    def get_todo_list(self) -> List[str]:
        memory = self._load_memory()
        return memory["todo_list"]