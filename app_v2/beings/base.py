# app_v2/beings/base.py
"""
Base classes for beings in the system
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
import json

class Being:
    """Podstawowa klasa dla wszystkich bytów w systemie"""
    
    def __init__(self, uid: str = None, genesis: Dict[str, Any] = None, 
                 attributes: Dict[str, Any] = None, memories: List[Any] = None,
                 self_awareness: Dict[str, Any] = None):
        self.uid = uid or str(uuid.uuid4())
        self.genesis = genesis or {}
        self.attributes = attributes or {}
        self.memories = memories or []
        self.self_awareness = self_awareness or {}
        self.created_at = datetime.now()
    
    def remember(self, key: str, value: Any):
        """Zapisuje informację w pamięci bytu"""
        if not isinstance(self.memories, list):
            self.memories = []
        
        # Znajdź istniejący wpis lub dodaj nowy
        for memory in self.memories:
            if isinstance(memory, dict) and memory.get('key') == key:
                memory['value'] = value
                memory['updated_at'] = datetime.now().isoformat()
                return
        
        # Dodaj nowy wpis
        self.memories.append({
            'key': key,
            'value': value,
            'created_at': datetime.now().isoformat()
        })
    
    def recall(self, key: str) -> Any:
        """Odzyskuje informację z pamięci bytu"""
        if not isinstance(self.memories, list):
            return None
        
        for memory in self.memories:
            if isinstance(memory, dict) and memory.get('key') == key:
                return memory.get('value')
        return None
    
    def log(self, message: str, level: str = "INFO"):
        """Metoda logowania specyficzna dla bytu"""
        entity_name = self.genesis.get('name', self.uid[:8])
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] [{level}] [Entity:{entity_name}] {message}")
        
        # Zapisz do memories
        self.remember('last_log', {
            'message': message,
            'level': level,
            'timestamp': timestamp
        })
    
    async def save(self):
        """Zapisuje byt do bazy danych"""
        from app_v2.database.soul_repository import SoulRepository
        soul_data = {
            "uid": self.uid,
            "genesis": self.genesis,
            "attributes": self.attributes,
            "memories": self.memories,
            "self_awareness": self.self_awareness
        }
        return await SoulRepository.save(soul_data)
    
    @classmethod
    async def create(cls, soul_data: Dict[str, Any]):
        """Tworzy nowy byt i zapisuje do bazy danych"""
        from app_v2.database.soul_repository import SoulRepository
        return await SoulRepository.save(soul_data)

class Relationship:
    """Klasa reprezentująca relacje między bytami"""
    
    def __init__(self, source_uid: str, target_uid: str, attributes: Dict[str, Any] = None):
        self.source_uid = source_uid
        self.target_uid = target_uid
        self.attributes = attributes or {}
        self.created_at = datetime.now()
    
    @classmethod
    async def create(cls, source_uid: str, target_uid: str, attributes: Dict[str, Any] = None):
        """Tworzy nową relację między bytami"""
        from app_v2.database.soul_repository import SoulRepository
        relationship_data = {
            "source_uid": source_uid,
            "target_uid": target_uid,
            "attributes": attributes or {},
            "created_at": datetime.now().isoformat()
        }
        return await SoulRepository.save_relationship(relationship_data)
