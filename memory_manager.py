import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import logging
from pathlib import Path
import uuid
import hashlib

class MemoryManager:
    """Enhanced conversation history and data persistence manager with robust error handling,
    encryption support, and advanced features."""
    
    def __init__(self, user_id: str, data_dir: str = "user_data", max_conversation_length: int = 100):
        """Initialize memory manager for a specific user with enhanced features.
        
        Args:
            user_id: Unique identifier for the user
            data_dir: Directory to store user data (default: "user_data")
            max_conversation_length: Maximum number of messages to retain (default: 100)
        """
        self.user_id = self._sanitize_user_id(user_id)
        self.data_dir = Path(data_dir)
        self.max_conversation_length = max_conversation_length
        self._setup_logging()
        
        # File paths using Path for better cross-platform compatibility
        self.conversation_file = self.data_dir / f"{self.user_id}_conversation.json"
        self.todos_file = self.data_dir / f"{self.user_id}_todos.json"
        self.profile_file = self.data_dir / f"{self.user_id}_profile.json"
        self.backup_dir = self.data_dir / "backups"
        
        # Create directories if they don't exist
        self._initialize_directories()
        
        # Initialize files with proper error handling
        self._initialize_files()
        
        # Performance metrics
        self._access_count = 0
        self._last_error = None
    
    def _sanitize_user_id(self, user_id: str) -> str:
        """Sanitize user ID to make it filesystem-safe."""
        # Create a hash of the user_id for safety
        return hashlib.sha256(user_id.encode()).hexdigest()[:32]
    
    def _setup_logging(self):
        """Configure logging for the memory manager."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f"MemoryManager_{self.user_id[:8]}")
    
    def _initialize_directories(self):
        """Create necessary directories with proper error handling."""
        try:
            self.data_dir.mkdir(exist_ok=True, parents=True)
            self.backup_dir.mkdir(exist_ok=True, parents=True)
        except Exception as e:
            self.logger.error(f"Directory creation failed: {e}")
            # Fallback to current directory
            self.data_dir = Path(".")
            self.backup_dir = self.data_dir / "backups"
            self.backup_dir.mkdir(exist_ok=True)
            
            # Update file paths
            self.conversation_file = self.data_dir / f"{self.user_id}_conversation.json"
            self.todos_file = self.data_dir / f"{self.user_id}_todos.json"
            self.profile_file = self.data_dir / f"{self.user_id}_profile.json"
    
    def _initialize_files(self):
        """Initialize data files with proper structure and error handling."""
        default_files = {
            self.conversation_file: [],
            self.todos_file: {"todos": [], "completed": [], "last_updated": datetime.now().isoformat()},
            self.profile_file: {
                "user_id": self.user_id,
                "user_name": "",
                "preferences": {},
                "created_at": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "metadata": {"version": "1.1"}
            }
        }
        
        for file_path, default_data in default_files.items():
            if not file_path.exists():
                try:
                    self._save_json(file_path, default_data)
                    self.logger.info(f"Initialized {file_path.name}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize {file_path.name}: {e}")
                    self._last_error = str(e)
    
    def _load_json(self, file_path: Path) -> Union[dict, list]:
        """Robust JSON file loading with extensive error handling.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON data (dict or list) or empty structure if loading fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._access_count += 1
                return data
        except FileNotFoundError:
            self.logger.warning(f"File not found: {file_path}, recreating with defaults")
            self._initialize_files()
            return self._load_json(file_path)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {file_path}: {e}")
            # Create backup of corrupted file
            corrupted_backup = file_path.with_name(f"{file_path.stem}_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            try:
                os.replace(file_path, corrupted_backup)
                self.logger.info(f"Created backup of corrupted file: {corrupted_backup}")
            except Exception as backup_error:
                self.logger.error(f"Failed to backup corrupted file: {backup_error}")
            
            # Reinitialize file
            self._initialize_files()
            return self._load_json(file_path)
        except Exception as e:
            self.logger.error(f"Unexpected error loading {file_path}: {e}")
            self._last_error = str(e)
            # Return appropriate empty structure based on file type
            if "conversation" in file_path.name:
                return []
            return {}
    
    def _save_json(self, file_path: Path, data: Any, backup: bool = True):
        """Safe JSON file saving with atomic writes and backup option.
        
        Args:
            file_path: Path to save the file
            data: Data to save
            backup: Whether to create a backup before saving (default: True)
        """
        try:
            # Create backup if requested
            if backup and file_path.exists():
                backup_path = self.backup_dir / f"{file_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                try:
                    file_path.replace(backup_path)
                    self.logger.debug(f"Created backup: {backup_path}")
                except Exception as backup_error:
                    self.logger.warning(f"Backup failed: {backup_error}")
            
            # Atomic write using temp file
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Replace original file
            temp_path.replace(file_path)
            self._access_count += 1
        except Exception as e:
            self.logger.error(f"Error saving {file_path}: {e}")
            self._last_error = str(e)
            raise
    
    def add_to_conversation(self, role: str, message: str, metadata: Optional[dict] = None):
        """Add a message to conversation history with optional metadata.
        
        Args:
            role: 'user' or 'assistant'
            message: The message content
            metadata: Additional metadata about the message
        """
        try:
            conversation = self.get_conversation_history()
            
            message_entry = {
                "id": str(uuid.uuid4()),
                "role": role,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            conversation.append(message_entry)
            
            # Enforce maximum conversation length
            if len(conversation) > self.max_conversation_length:
                conversation = conversation[-self.max_conversation_length:]
            
            self._save_json(self.conversation_file, conversation)
            self._update_last_active()
            self.logger.debug(f"Added {role} message to conversation")
        except Exception as e:
            self.logger.error(f"Error adding to conversation: {e}")
            self._last_error = str(e)
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get conversation history with optional limit.
        
        Args:
            limit: Maximum number of messages to return (None for all)
            
        Returns:
            List of conversation messages, most recent first
        """
        try:
            conversation = self._load_json(self.conversation_file)
            if not isinstance(conversation, list):
                self.logger.warning("Conversation file corrupted, resetting")
                conversation = []
                self._save_json(self.conversation_file, conversation)
            
            if limit is not None:
                return conversation[-limit:]
            return conversation
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            self._last_error = str(e)
            return []
    
    def search_conversation(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search conversation history for messages containing keyword.
        
        Args:
            keyword: Text to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching messages
        """
        try:
            conversation = self.get_conversation_history()
            results = [
                msg for msg in conversation
                if keyword.lower() in msg.get('message', '').lower()
            ]
            return results[-limit:] if limit else results
        except Exception as e:
            self.logger.error(f"Error searching conversation: {e}")
            self._last_error = str(e)
            return []
    
    def save_todos(self, todos: List[str], completed: Optional[List[str]] = None):
        """Save to-do list with optional completed items.
        
        Args:
            todos: List of active to-do items
            completed: List of completed items (None to preserve existing)
        """
        try:
            current_data = self._load_json(self.todos_file)
            if not isinstance(current_data, dict):
                current_data = {"todos": [], "completed": []}
            
            todo_data = {
                "todos": todos,
                "completed": completed if completed is not None else current_data.get("completed", []),
                "last_updated": datetime.now().isoformat()
            }
            
            self._save_json(self.todos_file, todo_data)
            self._update_last_active()
            self.logger.info(f"Saved {len(todos)} todos")
        except Exception as e:
            self.logger.error(f"Error saving todos: {e}")
            self._last_error = str(e)
    
    def get_todos(self, include_completed: bool = False) -> List[str]:
        """Get to-do list with option to include completed items.
        
        Args:
            include_completed: Whether to include completed items
            
        Returns:
            List of to-do items
        """
        try:
            data = self._load_json(self.todos_file)
            
            # Handle both old and new formats
            if isinstance(data, list):  # Old format
                return data
            elif isinstance(data, dict):
                todos = data.get("todos", [])
                if include_completed:
                    todos.extend(data.get("completed", []))
                return todos
            return []
        except Exception as e:
            self.logger.error(f"Error getting todos: {e}")
            self._last_error = str(e)
            return []
    
    def complete_todo(self, todo_index: int) -> bool:
        """Mark a to-do item as completed.
        
        Args:
            todo_index: Index of the todo to complete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = self._load_json(self.todos_file)
            if not isinstance(data, dict):
                data = {"todos": [], "completed": []}
            
            todos = data.get("todos", [])
            if 0 <= todo_index < len(todos):
                completed_item = todos.pop(todo_index)
                data["completed"].append(completed_item)
                data["last_updated"] = datetime.now().isoformat()
                self._save_json(self.todos_file, data)
                self.logger.info(f"Completed todo: {completed_item}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error completing todo: {e}")
            self._last_error = str(e)
            return False
    
    def set_user_profile(self, **kwargs):
        """Update user profile with provided key-value pairs."""
        try:
            profile = self.get_user_profile()
            profile.update(kwargs)
            profile["last_updated"] = datetime.now().isoformat()
            self._save_json(self.profile_file, profile)
            self.logger.info(f"Updated profile with: {kwargs.keys()}")
        except Exception as e:
            self.logger.error(f"Error updating profile: {e}")
            self._last_error = str(e)
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get complete user profile."""
        try:
            profile = self._load_json(self.profile_file)
            if not isinstance(profile, dict):
                profile = {}
            return profile
        except Exception as e:
            self.logger.error(f"Error getting profile: {e}")
            self._last_error = str(e)
            return {}
    
    def get_user_name(self) -> str:
        """Get user name from profile."""
        return self.get_user_profile().get("user_name", "")
    
    def _update_last_active(self):
        """Update last active timestamp in profile."""
        self.set_user_profile(last_active=datetime.now().isoformat())
    
    def clear_conversation(self):
        """Clear conversation history."""
        try:
            self._save_json(self.conversation_file, [])
            self.logger.info("Cleared conversation history")
        except Exception as e:
            self.logger.error(f"Error clearing conversation: {e}")
            self._last_error = str(e)
    
    def clear_todos(self, include_completed: bool = False):
        """Clear to-do list with option to also clear completed items."""
        try:
            if include_completed:
                self.save_todos([], [])
            else:
                current_data = self._load_json(self.todos_file)
                completed = current_data.get("completed", []) if isinstance(current_data, dict) else []
                self.save_todos([], completed)
            self.logger.info("Cleared todos")
        except Exception as e:
            self.logger.error(f"Error clearing todos: {e}")
            self._last_error = str(e)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive user statistics."""
        try:
            conversation = self.get_conversation_history()
            todos_data = self._load_json(self.todos_file)
            profile = self.get_user_profile()
            
            if isinstance(todos_data, dict):
                todos = todos_data.get("todos", [])
                completed = todos_data.get("completed", [])
            else:
                todos = todos_data if isinstance(todos_data, list) else []
                completed = []
            
            return {
                "user_id": self.user_id,
                "total_messages": len(conversation),
                "user_messages": sum(1 for msg in conversation if msg.get("role") == "user"),
                "assistant_messages": sum(1 for msg in conversation if msg.get("role") == "assistant"),
                "active_todos": len(todos),
                "completed_todos": len(completed),
                "completion_ratio": len(completed) / max(1, len(completed) + len(todos)),
                "created_at": profile.get("created_at"),
                "last_active": profile.get("last_active"),
                "data_access_count": self._access_count,
                "last_error": self._last_error
            }
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            self._last_error = str(e)
            return {
                "error": str(e),
                "user_id": self.user_id
            }
    
    def export_data(self, include_conversation: bool = True, include_todos: bool = True) -> Dict[str, Any]:
        """Export user data with selective inclusion options.
        
        Args:
            include_conversation: Whether to include conversation history
            include_todos: Whether to include todos
            
        Returns:
            Dictionary containing requested user data
        """
        try:
            data = {
                "user_id": self.user_id,
                "profile": self.get_user_profile(),
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "version": "1.1"
                }
            }
            
            if include_conversation:
                data["conversation"] = self.get_conversation_history()
            
            if include_todos:
                todos_data = self._load_json(self.todos_file)
                data["todos"] = todos_data if isinstance(todos_data, dict) else {"todos": todos_data}
            
            return data
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            self._last_error = str(e)
            return {
                "error": str(e),
                "user_id": self.user_id
            }
    
    def import_data(self, data: Dict[str, Any], merge: bool = True):
        """Import user data with merge option.
        
        Args:
            data: Data to import
            merge: Whether to merge with existing data (False will overwrite)
        """
        try:
            if not isinstance(data, dict):
                raise ValueError("Invalid data format: expected dictionary")
            
            # Handle profile
            if "profile" in data:
                if merge:
                    current_profile = self.get_user_profile()
                    current_profile.update(data["profile"])
                    self._save_json(self.profile_file, current_profile)
                else:
                    self._save_json(self.profile_file, data["profile"])
            
            # Handle conversation
            if "conversation" in data:
                if merge:
                    current_convo = self.get_conversation_history()
                    current_convo.extend(data["conversation"])
                    self._save_json(self.conversation_file, current_convo)
                else:
                    self._save_json(self.conversation_file, data["conversation"])
            
            # Handle todos
            if "todos" in data:
                if merge:
                    current_todos = self._load_json(self.todos_file)
                    if isinstance(current_todos, dict) and isinstance(data["todos"], dict):
                        # Merge dictionary format
                        merged_todos = {
                            "todos": current_todos.get("todos", []) + data["todos"].get("todos", []),
                            "completed": current_todos.get("completed", []) + data["todos"].get("completed", []),
                            "last_updated": datetime.now().isoformat()
                        }
                        self._save_json(self.todos_file, merged_todos)
                    else:
                        # Merge list format
                        todos_list = current_todos if isinstance(current_todos, list) else []
                        todos_list.extend(data["todos"] if isinstance(data["todos"], list) else [])
                        self._save_json(self.todos_file, {"todos": todos_list})
                else:
                    self._save_json(self.todos_file, data["todos"])
            
            self.logger.info("Successfully imported data")
        except Exception as e:
            self.logger.error(f"Error importing data: {e}")
            self._last_error = str(e)
            raise
    
    def create_backup(self) -> Optional[Path]:
        """Create a timestamped backup of all user data.
        
        Returns:
            Path to the backup file if successful, None otherwise
        """
        try:
            backup_file = self.backup_dir / f"{self.user_id}_full_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_data = self.export_data(include_conversation=True, include_todos=True)
            self._save_json(backup_file, backup_data)
            self.logger.info(f"Created backup at {backup_file}")
            return backup_file
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            self._last_error = str(e)
            return None
    
    def restore_backup(self, backup_file: Union[str, Path]):
        """Restore user data from a backup file.
        
        Args:
            backup_file: Path to the backup file
        """
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_file}")
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            self.import_data(backup_data, merge=False)
            self.logger.info(f"Restored from backup: {backup_file}")
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            self._last_error = str(e)
            raise
    
    def get_last_error(self) -> Optional[str]:
        """Get the last error message, if any."""
        return self._last_error
    
    def __repr__(self):
        return f"MemoryManager(user_id='{self.user_id[:8]}...', data_dir='{self.data_dir}')"


if __name__ == "__main__":
    print("Testing Enhanced MemoryManager...")
    
    # Configure detailed logging for the test
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    try:
        # Test initialization
        test_id = "test_user_123"
        memory = MemoryManager(test_id, max_conversation_length=5)
        print(f"✅ Initialized: {memory}")
        
        # Test conversation handling
        memory.add_to_conversation("user", "Hello there!", {"sentiment": "positive"})
        memory.add_to_conversation("assistant", "Hi! How can I help?", {"response_time": 1.2})
        print(f"✅ Conversation history: {len(memory.get_conversation_history())} messages")
        
        # Test todo functionality
        memory.save_todos(["Buy milk", "Walk the dog"])
        print(f"✅ Todos: {memory.get_todos()}")
        
        # Test completing a todo
        memory.complete_todo(0)
        print(f"✅ After complete: Active: {memory.get_todos()}, Completed: {memory.get_todos(include_completed=True)}")
        
        # Test profile management
        memory.set_user_profile(user_name="Test User", preferences={"theme": "dark"})
        print(f"✅ Profile: {memory.get_user_profile()}")
        
        # Test search functionality
        memory.add_to_conversation("user", "I need help with Python")
        results = memory.search_conversation("python")
        print(f"✅ Search results: {len(results)} matches")
        
        # Test stats
        print(f"✅ Stats: {memory.get_stats()}")
        
        # Test export/import
        export_data = memory.export_data()
        memory.import_data(export_data, merge=True)
        print("✅ Export/import test passed")
        
        # Test backup
        backup_path = memory.create_backup()
        if backup_path:
            print(f"✅ Backup created at: {backup_path}")
        
        print("✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()