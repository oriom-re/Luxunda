import asyncpg
import aiosqlite
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from app.beings.base import Being

@dataclass
class DataBeing(Being):
    """Byt danych z operacjami CRUD"""
    
    def __post_init__(self):
        if self.genesis.get('type') != 'data':
            self.genesis['type'] = 'data'
        if 'data_schema' not in self.attributes:
            self.attributes['data_schema'] = {}
        if 'data_values' not in self.attributes:
            self.attributes['data_values'] = {}
    
    def set_data(self, key: str, value: Any):
        """Ustawia wartość danych"""
        self.attributes['data_values'][key] = value
        
        # Zapisz w pamięci
        self.memories.append({
            'type': 'data_update',
            'key': key,
            'value': str(value),
            'timestamp': datetime.now().isoformat()
        })
    
    def get_data(self, key: str) -> Any:
        """Pobiera wartość danych"""
        return self.attributes['data_values'].get(key)
    
    def define_schema(self, schema: Dict[str, Any]):
        """Definiuje schemat danych"""
        self.attributes['data_schema'] = schema