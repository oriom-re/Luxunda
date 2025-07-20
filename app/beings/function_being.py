import asyncpg
import aiosqlite
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from app.beings.base import BaseBeing
from app.safety.executor import SafeCodeExecutor

@dataclass
class FunctionBeing(BaseBeing):
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
    
    def get_function_signature(self) -> str:
        """Zwraca sygnaturę funkcji"""
        return self.genesis.get('signature', f"{self.genesis.get('name', 'unknown')}()")



