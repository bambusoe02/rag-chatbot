"""File handling utilities for chat history and preferences."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger


class ChatHistoryHandler:
    """Handle chat history persistence."""
    
    def __init__(self, history_dir: str = "./data/chat_history"):
        """Initialize chat history handler.
        
        Args:
            history_dir: Directory to store chat history files
        """
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)
    
    def save_chat(self, session_id: str, messages: List[Dict[str, Any]]):
        """Save chat messages to file.
        
        Args:
            session_id: Unique session identifier
            messages: List of message dictionaries
        """
        try:
            history_file = self.history_dir / f"{session_id}.json"
            chat_data = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "messages": messages,
            }
            
            with open(history_file, "w") as f:
                json.dump(chat_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving chat history: {e}")
    
    def load_chat(self, session_id: str) -> List[Dict[str, Any]]:
        """Load chat messages from file.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of message dictionaries
        """
        try:
            history_file = self.history_dir / f"{session_id}.json"
            if history_file.exists():
                with open(history_file, "r") as f:
                    chat_data = json.load(f)
                    return chat_data.get("messages", [])
        except Exception as e:
            logger.error(f"Error loading chat history: {e}")
        return []
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all chat sessions.
        
        Returns:
            List of session metadata dictionaries
        """
        sessions = []
        try:
            for file in self.history_dir.glob("*.json"):
                with open(file, "r") as f:
                    chat_data = json.load(f)
                    sessions.append({
                        "session_id": chat_data.get("session_id"),
                        "created_at": chat_data.get("created_at"),
                        "updated_at": chat_data.get("updated_at"),
                        "message_count": len(chat_data.get("messages", [])),
                    })
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
        return sorted(sessions, key=lambda x: x.get("updated_at", ""), reverse=True)
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if successful
        """
        try:
            history_file = self.history_dir / f"{session_id}.json"
            if history_file.exists():
                history_file.unlink()
                return True
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
        return False


class UserPreferencesHandler:
    """Handle user preferences storage."""
    
    def __init__(self, prefs_file: str = "./data/user_preferences.json"):
        """Initialize preferences handler.
        
        Args:
            prefs_file: Path to preferences file
        """
        self.prefs_file = Path(prefs_file)
        self.prefs_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_preferences(self) -> Dict[str, Any]:
        """Load user preferences.
        
        Returns:
            Dictionary of preferences
        """
        default_prefs = {
            "temperature": 0.1,
            "top_k": 5,
            "chunk_size": 1000,
            "chunk_overlap": 200,
            "model": "qwen2.5:14b-instruct",
            "language": "auto",
            "theme": "light",
        }
        
        try:
            if self.prefs_file.exists():
                with open(self.prefs_file, "r") as f:
                    prefs = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**default_prefs, **prefs}
        except Exception as e:
            logger.error(f"Error loading preferences: {e}")
        
        return default_prefs
    
    def save_preferences(self, preferences: Dict[str, Any]):
        """Save user preferences.
        
        Args:
            preferences: Dictionary of preferences to save
        """
        try:
            with open(self.prefs_file, "w") as f:
                json.dump(preferences, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")


# Global handlers
chat_history = ChatHistoryHandler()
user_preferences = UserPreferencesHandler()

