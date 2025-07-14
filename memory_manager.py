import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import logging
from pathlib import Path
import uuid
import hashlib

class MemoryManager:
    """Enhanced memory manager for conversation history and user profiles"""
    
    def __init__(self, user_id: str, data_dir: str = "user_data", max_conversation_length: int = 100):
        self.user_id = self._sanitize_user_id(user_id)
        self.data_dir = Path(data_dir)
        self.max_conversation_length = max_conversation_length
        
        self._access_count = 0          
        self._last_error = None        
        self._setup_logging()
        
        self.conversation_file = self.data_dir / f"{self.user_id}_conversation.json"
        self.profile_file = self.data_dir / f"{self.user_id}_profile.json"
        self.backup_dir = self.data_dir / "backups"
        
        self._initialize_directories()
        self._initialize_files()

    
    def _sanitize_user_id(self, user_id: str) -> str:
        return hashlib.sha256(user_id.encode()).hexdigest()[:32]
    
    def _setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f"MemoryManager_{self.user_id[:8]}")
    
    def _initialize_directories(self):
        try:
            self.data_dir.mkdir(exist_ok=True, parents=True)
            self.backup_dir.mkdir(exist_ok=True, parents=True)
        except Exception as e:
            self.logger.error(f"Directory creation failed: {e}")
            self.data_dir = Path(".")
            self.backup_dir = self.data_dir / "backups"
            self.backup_dir.mkdir(exist_ok=True)
            self.conversation_file = self.data_dir / f"{self.user_id}_conversation.json"
            self.profile_file = self.data_dir / f"{self.user_id}_profile.json"
    
    def _initialize_files(self):
        default_files = {
            self.conversation_file: [],
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
                except Exception as e:
                    self.logger.error(f"Failed to initialize {file_path.name}: {e}")
    
    def _load_json(self, file_path: Path) -> Union[dict, list]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._access_count += 1
                return data
        except FileNotFoundError:
            self._initialize_files()
            return self._load_json(file_path)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in {file_path}: {e}")
            corrupted_backup = file_path.with_name(f"{file_path.stem}_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            try:
                os.replace(file_path, corrupted_backup)
            except Exception:
                pass
            self._initialize_files()
            return self._load_json(file_path)
        except Exception as e:
            self.logger.error(f"Unexpected error loading {file_path}: {e}")
            return [] if "conversation" in file_path.name else {}
    
    def _save_json(self, file_path: Path, data: Any, backup: bool = True):
        try:
            if backup and file_path.exists():
                backup_path = self.backup_dir / f"{file_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                try:
                    file_path.replace(backup_path)
                except Exception:
                    pass
            
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            temp_path.replace(file_path)
            self._access_count += 1
        except Exception as e:
            self.logger.error(f"Error saving {file_path}: {e}")
            raise
    
    # Conversation methods
    def add_to_conversation(self, role: str, message: str, metadata: Optional[dict] = None):
        try:
            conversation = self.get_conversation_history()
            conversation.append({
                "id": str(uuid.uuid4()),
                "role": role,
                "message": message,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            })
            if len(conversation) > self.max_conversation_length:
                conversation = conversation[-self.max_conversation_length:]
            self._save_json(self.conversation_file, conversation)
            self._update_last_active()
        except Exception as e:
            self.logger.error(f"Error adding to conversation: {e}")
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            conversation = self._load_json(self.conversation_file)
            if not isinstance(conversation, list):
                conversation = []
                self._save_json(self.conversation_file, conversation)
            return conversation[-limit:] if limit else conversation
        except Exception as e:
            self.logger.error(f"Error getting conversation history: {e}")
            return []
    
    def search_conversation(self, keyword: str, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            conversation = self.get_conversation_history()
            results = [msg for msg in conversation if keyword.lower() in msg.get('message', '').lower()]
            return results[-limit:] if limit else results
        except Exception as e:
            self.logger.error(f"Error searching conversation: {e}")
            return []
    
    def clear_conversation(self):
        try:
            self._save_json(self.conversation_file, [])
        except Exception as e:
            self.logger.error(f"Error clearing conversation: {e}")
    
    # Profile methods
    def set_user_profile(self, **kwargs):
        try:
            profile = self.get_user_profile()
            profile.update(kwargs)
            profile["last_updated"] = datetime.now().isoformat()
            self._save_json(self.profile_file, profile)
        except Exception as e:
            self.logger.error(f"Error updating profile: {e}")
    
    def set_user_name(self, name: str):
        self.set_user_profile(user_name=name)
    
    def get_user_profile(self) -> Dict[str, Any]:
        try:
            profile = self._load_json(self.profile_file)
            return profile if isinstance(profile, dict) else {}
        except Exception as e:
            self.logger.error(f"Error getting profile: {e}")
            return {}
    
    def get_user_name(self) -> str:
        return self.get_user_profile().get("user_name", "")
    
    def _update_last_active(self):
        self.set_user_profile(last_active=datetime.now().isoformat())
    
    # Utility methods
    def get_stats(self) -> Dict[str, Any]:
        try:
            conversation = self.get_conversation_history()
            return {
                "total_messages": len(conversation),
                "user_messages": sum(1 for msg in conversation if msg.get("role") == "user"),
                "assistant_messages": sum(1 for msg in conversation if msg.get("role") == "assistant"),
                "created_at": self.get_user_profile().get("created_at"),
                "last_active": self.get_user_profile().get("last_active"),
                "data_access_count": self._access_count
            }
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
    
    def get_last_error(self) -> Optional[str]:
        return self._last_error
    
    def __repr__(self):
        return f"MemoryManager(user_id='{self.user_id[:8]}...', data_dir='{self.data_dir}')"