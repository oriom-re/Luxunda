# app_v2/beings/base.py
"""
Base classes for beings in the system
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import json

@dataclass
class Soul:
    """Podstawowa klasa dla wszystkich bytów w systemie"""
    alias: str = None # Alias dla bytu
    genotype_hex: str = None # unikalna reprezentacja genotypu bytu
    genotype: Dict[str, Any] = field(default_factory=dict) # Genotyp bytu
    created_at: Optional[datetime] = None # Data zapisu bytu w bazie danych

    def _apply_genotype(self, genotype: dict, values: dict):
        attributes = genotype.get("attributes", {})
        for attr, table in attributes.items():
            default = values.get(attr)
            self.fields[attr] = {
                "table": table,
                "value": default
            }

    def get_values_for_table(self, table_name: str):
        return {
            attr: details["value"]
            for attr, details in self.fields.items()
            if details["table"] == table_name
        }

    def serialize(self):
        return {
            "uid": self.uid,
            "soul_uid": self.soul_uid,
            "created_at": self.created_at.isoformat(),
            "fields": self.fields
        }

    def __repr__(self):
        return f"<Being {self.uid[:8]} fields={list(self.fields.keys())}>"
        
    @classmethod
    async def create(cls) -> 'Being':
        """Zapisuje byt do bazy danych"""
        from app_v2.database.soul_repository import SoulRepository
        soul_data = {
            "uid": cls.uid,
            "genesis": cls.genesis,
            "attributes": cls.attributes,
            "memories": cls.memories,
            "self_awareness": cls.self_awareness
        }
        return await SoulRepository.save(soul_data)

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
    async def load(cls, uid: str) -> 'Being':
        """Ładuje byt z bazy danych na podstawie UID"""
        from app_v2.database.soul_repository import SoulRepository
        soul_data = await SoulRepository.load(uid)
        if not soul_data:
            return None
        
        return cls(
            uid=soul_data.get('uid'),
            genesis=soul_data.get('genesis'),
            attributes=soul_data.get('attributes'),
            memories=soul_data.get('memories', []),
            self_awareness=soul_data.get('self_awareness', {})
        )
        

    def to_dict(self) -> Dict[str, Any]:
        """Zwraca reprezentację bytu jako słownik"""
        return {
            "uid": self.uid,
            "genesis": self.genesis,
            "attributes": self.attributes,
            "memories": self.memories,
            "self_awareness": self.self_awareness,
            "created_at": self.created_at.isoformat()
        }
    
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