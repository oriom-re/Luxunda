import asyncpg
import aiosqlite
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from app.beings.base import Being
from app.safety.executor import SafeCodeExecutor
import json

@dataclass
class FunctionBeing(Being):
    """Byt funkcyjny z możliwością wykonania"""
    
    def __post_init__(self):
        if self.genesis.get('type') != 'function':
            self.genesis['type'] = 'function'
    
    async def __call__(self, *args, **kwargs):
        """Wykonuje funkcję z kodu źródłowego"""
        source = self.genesis.get('source', '')
        function_name = self.genesis.get('name', 'unknown_function')
        
        if not source:
            return {'success': False, 'error': 'Brak kodu źródłowego'}
        
        result = await SafeCodeExecutor.execute_function(source, function_name, *args, **kwargs)
        
        # Zapisz wykonanie w pamięci
        memory_entry = {
            'type': 'execution',
            'timestamp': datetime.now().isoformat(),
            'args': str(args),
            'kwargs': str(kwargs),
            'result': str(result.get('result')),
            'success': result.get('success', False)
        }
        self.memories.append(memory_entry)
        await self.save()
        
        return result

    async def create(cls, source: str, name: str, **kwargs) -> 'FunctionBeing':
        """Tworzy nowy byt funkcyjny"""
        soul = str(uuid.uuid4())
        genesis = {
            'source': source,
            'name': name,
            'type': 'function'
        }
        
        attributes = kwargs.get('attributes', {})
        if 'energy_level' not in attributes:
            attributes['energy_level'] = 100
    
    async def save(self):
        """Zapisuje byt do bazy danych"""
        async with aiosqlite.connect('beings.db') as db:
            await db.execute("""
                INSERT OR REPLACE INTO beings (soul, genesis, memories)
                VALUES (?, ?, ?)
            """, (self.soul, json.dumps(self.genesis), json.dumps(self.memories)))
            await db.commit()