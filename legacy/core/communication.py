# app_v2/core/communication.py
"""
System komunikacji między bytami z rozpoznawaniem intencji
"""

from typing import Dict, Any, Optional
from datetime import datetime
import uuid

class Communication:
    """System komunikacji między bytami"""
    
    @staticmethod
    def create_message(sender_uid: str, content: Any, message_type: str = "execute", 
                      metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Tworzy wiadomość między bytami"""
        return {
            "id": str(uuid.uuid4()),
            "sender_uid": sender_uid,
            "content": content,
            "type": message_type,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

class IntentRecognizer:
    """Rozpoznaje intencje na podstawie wiadomości"""
    
    INTENT_PATTERNS = {
        "create_entity": ["create", "spawn", "new", "make", "generate"],
        "load_entity": ["load", "get", "find", "retrieve", "fetch"],
        "execute_function": ["execute", "run", "call", "invoke", "perform"],
        "query_data": ["query", "search", "list", "show", "display"],
        "update_data": ["update", "modify", "change", "edit", "set"],
        "delete_data": ["delete", "remove", "destroy", "kill"],
        "communicate": ["send", "tell", "message", "notify", "inform"]
    }
    
    @classmethod
    def recognize_intent(cls, content: Any) -> str:
        """Rozpoznaje intencję na podstawie treści wiadomości"""
        if isinstance(content, str):
            content_lower = content.lower()
            for intent, patterns in cls.INTENT_PATTERNS.items():
                if any(pattern in content_lower for pattern in patterns):
                    return intent
        elif isinstance(content, dict):
            # Sprawdź klucze w słowniku
            if "action" in content:
                return content["action"]
            if "intent" in content:
                return content["intent"]
            if "command" in content:
                command = content["command"].lower()
                for intent, patterns in cls.INTENT_PATTERNS.items():
                    if any(pattern in command for pattern in patterns):
                        return intent
        
        return "unknown"
