from typing import List
from memory_manager import MemoryManager

class TodoTools:
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager

    def add_todo(self, task: str) -> str:
        """Add a task to the user's to-do list"""
        self.memory.add_todo(task)
        return f"Added '{task}' to your to-do list."

    def remove_todo(self, task: str) -> str:
        """Remove a task from the user's to-do list"""
        if self.memory.remove_todo(task):
            return f"Removed '{task}' from your to-do list."
        return f"Task '{task}' not found in your to-do list."

    def list_todos(self) -> str:
        """List all tasks in the user's to-do list"""
        todos = self.memory.get_todo_list()
        if not todos:
            return "Your to-do list is empty."
        return "Your to-do list:\n" + "\n".join(f"{i+1}. {task}" for i, task in enumerate(todos))