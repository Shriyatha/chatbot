from typing import List, Optional, Tuple, Union, Dict, Any
from memory_manager import MemoryManager
import logging
from datetime import datetime

class TodoTools:
    """Tools for managing todo items with completion tracking"""
    
    def __init__(self, memory_manager: MemoryManager):
        self.memory = memory_manager
        self.logger = logging.getLogger(__name__)
        self.todos_file = self.memory.data_dir / f"{self.memory.user_id}_todos.json"
        self._initialize_todos_file()
    
    def _initialize_todos_file(self):
        if not self.todos_file.exists():
            try:
                initial_data = {
                    "todos": [],
                    "completed": [],
                    "last_updated": datetime.now().isoformat()
                }
                self.memory._save_json(self.todos_file, initial_data, backup=False)
            except Exception as e:
                self.logger.error(f"Failed to initialize todos file: {e}")
    
    def _get_current_todos(self) -> Tuple[List[dict], List[dict]]:
        try:
            data = self.memory._load_json(self.todos_file)
            if isinstance(data, list):  # Backward compatibility
                return [{"task": t} for t in data], []
            
            active = data.get("todos", [])
            completed = data.get("completed", [])
            
            # Ensure proper format
            if active and isinstance(active[0], str):
                active = [{"task": t} for t in active]
            if completed and isinstance(completed[0], str):
                completed = [{"task": t} for t in completed]
                
            return active, completed
        except Exception as e:
            self.logger.error(f"Error getting todos: {e}")
            return [], []
    
    def _save_todos(self, active: List[dict], completed: List[dict]) -> bool:
        try:
            todo_data = {
                "todos": active,
                "completed": completed,
                "last_updated": datetime.now().isoformat()
            }
            self.memory._save_json(self.todos_file, todo_data)
            self.memory._update_last_active()
            return True
        except Exception as e:
            self.logger.error(f"Error saving todos: {e}")
            return False
    
    def add_todo(self, task: str, priority: str = "medium", tags: List[str] = None) -> str:
        try:
            if not task.strip():
                return "❌ Cannot add empty task"
            
            active, completed = self._get_current_todos()
            
            # Check for duplicate
            if any(t["task"].lower() == task.lower() for t in active):
                return f"⚠️ Task '{task}' already exists"
            
            new_task = {
                "task": task,
                "priority": priority.lower(),
                "tags": tags or [],
                "created": datetime.now().isoformat()
            }
            
            active.append(new_task)
            if self._save_todos(active, completed):
                return f"✅ Added: {task}"
            return "❌ Failed to save task"
        except Exception as e:
            self.logger.error(f"Error adding todo: {e}")
            return f"❌ Error adding task: {str(e)}"
    
    def remove_todo(self, task_ref: Union[str, int]) -> str:
        try:
            if not task_ref:
                return "❌ Cannot remove empty task reference"
            
            active, completed = self._get_current_todos()
            
            # Handle index reference
            if isinstance(task_ref, int) or (isinstance(task_ref, str) and task_ref.isdigit()):
                index = int(task_ref) - 1
                if 0 <= index < len(active):
                    removed = active.pop(index)
                    if self._save_todos(active, completed):
                        return f"✅ Removed: {removed['task']}"
                    return "❌ Failed to save changes"
                return f"⚠️ Invalid task number (1-{len(active)})"
            
            # Handle text reference
            task_lower = str(task_ref).lower()
            matches = [i for i, t in enumerate(active) if task_lower in t["task"].lower()]
            
            if not matches:
                return f"⚠️ Task '{task_ref}' not found"
            if len(matches) > 1:
                return "⚠️ Multiple matches found - please specify by number"
            
            removed = active.pop(matches[0])
            if self._save_todos(active, completed):
                return f"✅ Removed: {removed['task']}"
            return "❌ Failed to save changes"
        except Exception as e:
            self.logger.error(f"Error removing todo: {e}")
            return f"❌ Error removing task: {str(e)}"
    
    def complete_todo(self, task_ref: Union[str, int]) -> str:
        try:
            active, completed = self._get_current_todos()
            
            # Handle index reference
            if isinstance(task_ref, int) or (isinstance(task_ref, str) and task_ref.isdigit()):
                index = int(task_ref) - 1
                if 0 <= index < len(active):
                    task = active.pop(index)
                    task["completed"] = datetime.now().isoformat()
                    completed.append(task)
                    if self._save_todos(active, completed):
                        return f"✅ Completed: {task['task']}"
                    return "❌ Failed to save changes"
                return f"⚠️ Invalid task number (1-{len(active)})"
            
            # Handle text reference
            task_lower = str(task_ref).lower()
            matches = [i for i, t in enumerate(active) if task_lower in t["task"].lower()]
            
            if not matches:
                return f"⚠️ Task '{task_ref}' not found"
            if len(matches) > 1:
                return "⚠️ Multiple matches found - please specify by number"
            
            task = active.pop(matches[0])
            task["completed"] = datetime.now().isoformat()
            completed.append(task)
            if self._save_todos(active, completed):
                return f"✅ Completed: {task['task']}"
            return "❌ Failed to save changes"
        except Exception as e:
            self.logger.error(f"Error completing todo: {e}")
            return f"❌ Error completing task: {str(e)}"
    
    def list_todos(self, show_completed: bool = False) -> str:
        try:
            active, completed = self._get_current_todos()
            
            if not active and (not show_completed or not completed):
                return "📝 Your todo list is empty"
            
            result = ["📝 Active Tasks:"]
            for i, task in enumerate(active, 1):
                task_str = f"{i}. {task['task']}"
                if "priority" in task:
                    task_str += f" (Priority: {task['priority']})"
                if "tags" in task and task["tags"]:
                    task_str += f" [Tags: {', '.join(task['tags'])}]"
                result.append(task_str)
            
            if show_completed and completed:
                result.append("\n✅ Completed Tasks:")
                for i, task in enumerate(completed, 1):
                    task_str = f"{i}. {task['task']}"
                    if "completed" in task:
                        task_str += f" - Done on {task['completed'][:10]}"
                    result.append(task_str)
            
            return "\n".join(result)
        except Exception as e:
            self.logger.error(f"Error listing todos: {e}")
            return f"❌ Error listing tasks: {str(e)}"
    
    def clear_todos(self, include_completed: bool = False) -> str:
        try:
            if include_completed:
                if self._save_todos([], []):
                    return "✅ Cleared all tasks (including completed)"
                return "❌ Failed to clear tasks"
            
            _, completed = self._get_current_todos()
            if self._save_todos([], completed):
                return "✅ Cleared active tasks (kept completed)"
            return "❌ Failed to clear tasks"
        except Exception as e:
            self.logger.error(f"Error clearing todos: {e}")
            return f"❌ Error clearing tasks: {str(e)}"
    
    def get_stats(self) -> Dict[str, Any]:
        try:
            active, completed = self._get_current_todos()
            return {
                "active_count": len(active),
                "completed_count": len(completed),
                "completion_ratio": len(completed) / max(1, len(active) + len(completed))
            }
        except Exception as e:
            self.logger.error(f"Error getting todo stats: {e}")
            return {"error": str(e)}