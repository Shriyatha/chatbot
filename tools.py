"""
Todo Tools for the Personal Todo Assistant
"""

from typing import List, Optional
from memory_manager import MemoryManager

class TodoTools:
    """Tools for managing todo items"""
    
    def __init__(self, memory_manager: MemoryManager):
        """Initialize with memory manager"""
        self.memory = memory_manager
    
    def add_todo(self, task: str) -> str:
        """Add a new todo item"""
        try:
            if not task.strip():
                return "❌ Cannot add empty task"
            
            # Get current todos
            todos = self.memory.get_todos()
            
            # Check if task already exists
            if task in todos:
                return f"⚠️ Task '{task}' already exists"
            
            # Add new task
            todos.append(task)
            self.memory.save_todos(todos)
            
            return f"✅ Task '{task}' added successfully"
            
        except Exception as e:
            return f"❌ Error adding task: {str(e)}"
    
    def remove_todo(self, task: str) -> str:
        """Remove a todo item"""
        try:
            if not task.strip():
                return "❌ Cannot remove empty task"
            
            # Get current todos
            todos = self.memory.get_todos()
            
            # Check if task exists
            if task not in todos:
                return f"⚠️ Task '{task}' not found"
            
            # Remove task
            todos.remove(task)
            self.memory.save_todos(todos)
            
            return f"✅ Task '{task}' removed successfully"
            
        except Exception as e:
            return f"❌ Error removing task: {str(e)}"
    
    def list_todos(self) -> str:
        """List all todo items"""
        try:
            todos = self.memory.get_todos()
            
            if not todos:
                return "📝 Your todo list is empty"
            
            # Format the list
            result = "📝 Your Todo List:\n"
            for i, task in enumerate(todos, 1):
                result += f"{i}. {task}\n"
            
            return result.strip()
            
        except Exception as e:
            return f"❌ Error listing tasks: {str(e)}"
    
    def clear_todos(self) -> str:
        """Clear all todo items"""
        try:
            self.memory.clear_todos()
            return "✅ All tasks cleared successfully"
            
        except Exception as e:
            return f"❌ Error clearing tasks: {str(e)}"
    
    def update_todo(self, old_task: str, new_task: str) -> str:
        """Update an existing todo item"""
        try:
            if not old_task.strip() or not new_task.strip():
                return "❌ Cannot update with empty task"
            
            # Get current todos
            todos = self.memory.get_todos()
            
            # Check if old task exists
            if old_task not in todos:
                return f"⚠️ Task '{old_task}' not found"
            
            # Check if new task already exists
            if new_task in todos:
                return f"⚠️ Task '{new_task}' already exists"
            
            # Update task
            index = todos.index(old_task)
            todos[index] = new_task
            self.memory.save_todos(todos)
            
            return f"✅ Task updated from '{old_task}' to '{new_task}'"
            
        except Exception as e:
            return f"❌ Error updating task: {str(e)}"
    
    def search_todos(self, query: str) -> str:
        """Search for todos containing the query"""
        try:
            if not query.strip():
                return "❌ Cannot search with empty query"
            
            todos = self.memory.get_todos()
            
            if not todos:
                return "📝 Your todo list is empty"
            
            # Find matching tasks
            matching_tasks = [task for task in todos if query.lower() in task.lower()]
            
            if not matching_tasks:
                return f"🔍 No tasks found containing '{query}'"
            
            # Format results
            result = f"🔍 Tasks containing '{query}':\n"
            for i, task in enumerate(matching_tasks, 1):
                result += f"{i}. {task}\n"
            
            return result.strip()
            
        except Exception as e:
            return f"❌ Error searching tasks: {str(e)}"
    
    def get_todo_count(self) -> str:
        """Get the count of todo items"""
        try:
            todos = self.memory.get_todos()
            count = len(todos)
            
            if count == 0:
                return "📝 You have no tasks in your todo list"
            elif count == 1:
                return "📝 You have 1 task in your todo list"
            else:
                return f"📝 You have {count} tasks in your todo list"
                
        except Exception as e:
            return f"❌ Error getting task count: {str(e)}"
    
    def get_todo_by_number(self, number: int) -> str:
        """Get a specific todo by its number"""
        try:
            todos = self.memory.get_todos()
            
            if not todos:
                return "📝 Your todo list is empty"
            
            if number < 1 or number > len(todos):
                return f"❌ Invalid task number. Please choose between 1 and {len(todos)}"
            
            task = todos[number - 1]
            return f"📝 Task {number}: {task}"
            
        except Exception as e:
            return f"❌ Error getting task: {str(e)}"
    
    def remove_todo_by_number(self, number: int) -> str:
        """Remove a todo by its number"""
        try:
            todos = self.memory.get_todos()
            
            if not todos:
                return "📝 Your todo list is empty"
            
            if number < 1 or number > len(todos):
                return f"❌ Invalid task number. Please choose between 1 and {len(todos)}"
            
            task = todos[number - 1]
            todos.pop(number - 1)
            self.memory.save_todos(todos)
            
            return f"✅ Task {number} ('{task}') removed successfully"
            
        except Exception as e:
            return f"❌ Error removing task: {str(e)}"

# Test the class if run directly
if __name__ == "__main__":
    print("Testing TodoTools...")
    try:
        from memory_manager import MemoryManager
        
        # Test setup
        memory = MemoryManager("test_user")
        tools = TodoTools(memory)
        
        # Test add
        result = tools.add_todo("Test task")
        print(f"Add result: {result}")
        assert "added" in result.lower()
        
        # Test list
        result = tools.list_todos()
        print(f"List result: {result}")
        assert "Test task" in result
        
        # Test remove
        result = tools.remove_todo("Test task")
        print(f"Remove result: {result}")
        assert "removed" in result.lower()
        
        # Test empty list
        result = tools.list_todos()
        print(f"Empty list result: {result}")
        assert "empty" in result.lower()
        
        print("✅ All TodoTools tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()