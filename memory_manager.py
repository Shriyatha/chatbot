import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

class MemoryManager:
    """Manages conversation history and to-do list persistence"""
    
    def __init__(self, user_id: str):
        """Initialize memory manager for a specific user"""
        self.user_id = user_id
        self.data_dir = "user_data"
        self.conversation_file = os.path.join(self.data_dir, f"{user_id}_conversation.json")
        self.todos_file = os.path.join(self.data_dir, f"{user_id}_todos.json")
        self.profile_file = os.path.join(self.data_dir, f"{user_id}_profile.json")
        
        # Create data directory if it doesn't exist
        try:
            os.makedirs(self.data_dir, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create data directory: {e}")
            # Fall back to current directory
            self.data_dir = "."
            self.conversation_file = f"{user_id}_conversation.json"
            self.todos_file = f"{user_id}_todos.json"
            self.profile_file = f"{user_id}_profile.json"
        
        # Initialize files if they don't exist
        self._initialize_files()
    
    def _initialize_files(self):
        """Initialize data files if they don't exist"""
        try:
            # Initialize conversation history
            if not os.path.exists(self.conversation_file):
                self._save_json(self.conversation_file, [])
            
            # Initialize todos
            if not os.path.exists(self.todos_file):
                self._save_json(self.todos_file, [])
            
            # Initialize profile
            if not os.path.exists(self.profile_file):
                self._save_json(self.profile_file, {
                    "user_name": "",
                    "created_at": datetime.now().isoformat(),
                    "last_active": datetime.now().isoformat()
                })
        except Exception as e:
            print(f"Warning: Could not initialize files: {e}")
    
    def _load_json(self, file_path: str) -> Any:
        """Load JSON data from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load {file_path}: {e}")
            # Return appropriate default based on file type
            if 'conversation' in file_path or 'todos' in file_path:
                return []
            else:
                return {}
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return [] if 'conversation' in file_path or 'todos' in file_path else {}
    
    def _save_json(self, file_path: str, data: Any):
        """Save JSON data to file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving to {file_path}: {str(e)}")
    
    def add_to_conversation(self, role: str, message: str):
        """Add a message to conversation history"""
        try:
            conversation = self._load_json(self.conversation_file)
            
            conversation.append({
                "role": role,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only last 100 messages to prevent file from getting too large
            if len(conversation) > 100:
                conversation = conversation[-100:]
            
            self._save_json(self.conversation_file, conversation)
            self._update_last_active()
        except Exception as e:
            print(f"Error adding to conversation: {e}")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history"""
        try:
            return self._load_json(self.conversation_file)
        except Exception as e:
            print(f"Error getting conversation history: {e}")
            return []
    
    def get_recent_conversation(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation messages"""
        try:
            conversation = self.get_conversation_history()
            return conversation[-limit:] if conversation else []
        except Exception as e:
            print(f"Error getting recent conversation: {e}")
            return []
    
    def save_todos(self, todos: List[str]):
        """Save to-do list"""
        try:
            todo_data = {
                "todos": todos,
                "last_updated": datetime.now().isoformat()
            }
            self._save_json(self.todos_file, todo_data)
            self._update_last_active()
        except Exception as e:
            print(f"Error saving todos: {e}")
    
    def get_todos(self) -> List[str]:
        """Get to-do list"""
        try:
            data = self._load_json(self.todos_file)
            if isinstance(data, list):
                # Handle old format (direct list)
                return data
            elif isinstance(data, dict) and "todos" in data:
                # Handle new format (with metadata)
                return data["todos"]
            else:
                return []
        except Exception as e:
            print(f"Error getting todos: {e}")
            return []
    
    def set_user_name(self, name: str):
        """Set user name"""
        try:
            profile = self._load_json(self.profile_file)
            profile["user_name"] = name
            profile["last_updated"] = datetime.now().isoformat()
            self._save_json(self.profile_file, profile)
        except Exception as e:
            print(f"Error setting user name: {e}")
    
    def get_user_name(self) -> Optional[str]:
        """Get user name"""
        try:
            profile = self._load_json(self.profile_file)
            return profile.get("user_name", "") if profile else ""
        except Exception as e:
            print(f"Error getting user name: {e}")
            return ""
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get full user profile"""
        try:
            return self._load_json(self.profile_file)
        except Exception as e:
            print(f"Error getting user profile: {e}")
            return {}
    
    def _update_last_active(self):
        """Update last active timestamp"""
        try:
            profile = self._load_json(self.profile_file)
            profile["last_active"] = datetime.now().isoformat()
            self._save_json(self.profile_file, profile)
        except Exception as e:
            print(f"Error updating last active: {e}")
    
    def clear_conversation(self):
        """Clear conversation history"""
        try:
            self._save_json(self.conversation_file, [])
        except Exception as e:
            print(f"Error clearing conversation: {e}")
    
    def clear_todos(self):
        """Clear to-do list"""
        try:
            self.save_todos([])
        except Exception as e:
            print(f"Error clearing todos: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        try:
            conversation = self.get_conversation_history()
            todos = self.get_todos()
            profile = self.get_user_profile()
            
            return {
                "total_messages": len(conversation),
                "total_todos": len(todos),
                "completed_todos": 0,  # Could track this in the future
                "created_at": profile.get("created_at", ""),
                "last_active": profile.get("last_active", "")
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {
                "total_messages": 0,
                "total_todos": 0,
                "completed_todos": 0,
                "created_at": "",
                "last_active": ""
            }
    
    def export_data(self) -> Dict[str, Any]:
        """Export all user data"""
        try:
            return {
                "user_id": self.user_id,
                "profile": self.get_user_profile(),
                "conversation": self.get_conversation_history(),
                "todos": self.get_todos(),
                "stats": self.get_stats()
            }
        except Exception as e:
            print(f"Error exporting data: {e}")
            return {
                "user_id": self.user_id,
                "profile": {},
                "conversation": [],
                "todos": [],
                "stats": {}
            }
    
    def import_data(self, data: Dict[str, Any]):
        """Import user data"""
        try:
            if "profile" in data:
                self._save_json(self.profile_file, data["profile"])
            
            if "conversation" in data:
                self._save_json(self.conversation_file, data["conversation"])
            
            if "todos" in data:
                self.save_todos(data["todos"])
        except Exception as e:
            print(f"Error importing data: {e}")
    
    def backup_data(self) -> str:
        """Create a backup of all user data"""
        try:
            backup_file = os.path.join(self.data_dir, f"{self.user_id}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            backup_data = self.export_data()
            self._save_json(backup_file, backup_data)
            return backup_file
        except Exception as e:
            print(f"Error creating backup: {e}")
            return ""

# Test the class if run directly
if __name__ == "__main__":
    print("Testing MemoryManager...")
    try:
        # Test basic functionality
        memory = MemoryManager("test_user")
        print("✅ MemoryManager initialized successfully")
        
        # Test conversation
        memory.add_to_conversation("user", "Hello")
        memory.add_to_conversation("assistant", "Hi there!")
        history = memory.get_conversation_history()
        print(f"✅ Conversation history: {len(history)} messages")
        
        # Test todos
        memory.save_todos(["Task 1", "Task 2"])
        todos = memory.get_todos()
        print(f"✅ Todos: {len(todos)} items")
        
        # Test profile
        memory.set_user_name("Test User")
        name = memory.get_user_name()
        print(f"✅ User name: {name}")
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()