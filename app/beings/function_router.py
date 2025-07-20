from datetime import datetime
import uuid
import json
from typing import Optional
from app.beings.base import BaseBeing
from app.safety.executor import SafeCodeExecutor

class FunctionRouter:
    """Router dla funkcji z bytów"""

    def __init__(self):
        self.registered_functions = {}

    async def register_function_from_being(self, soul: str) -> dict:
        """Rejestruje funkcję z bytu"""
        being = await BaseBeing.load(soul)
        if not being:
            return {'success': False, 'error': 'Byt nie znaleziony'}

        if being.genesis.get('type') != 'function':
            return {'success': False, 'error': 'Byt nie jest funkcją'}

        source = being.genesis.get('source', '')
        name = being.genesis.get('name', 'unknown_function')

        if not source:
            return {'success': False, 'error': 'Brak kodu źródłowego w bycie'}

        # Waliduj kod
        is_valid, validation_msg = SafeCodeExecutor.validate_code(source)
        if not is_valid:
            return {'success': False, 'error': validation_msg}

        self.registered_functions[soul] = {
            'name': name,
            'source': source,
            'being': being
        }

        return {'success': True, 'message': f'Funkcja {name} została zarejestrowana'}

    async def execute_function(self, soul: str, *args, **kwargs) -> dict:
        """Wykonuje funkcję z zarejestrowanego bytu"""
        if soul not in self.registered_functions:
            return {'success': False, 'error': 'Funkcja nie jest zarejestrowana'}

        func_info = self.registered_functions[soul]
        result = await SafeCodeExecutor.execute_function(
            func_info['source'], 
            func_info['name'], 
            *args, **kwargs
        )

        # Zapisz wykonanie w pamięci bytu
        if result['success']:
            being = func_info['being']
            memory_entry = {
                'type': 'execution',
                'timestamp': datetime.now().isoformat(),
                'args': str(args),
                'kwargs': str(kwargs),
                'result': str(result['result']),
                'output': result['output']
            }
            being.memories.append(memory_entry)
            await being.save()

        return result

    def get_registered_functions(self) -> dict:
        """Zwraca listę zarejestrowanych funkcji"""
        return {
            soul: {
                'name': info['name'],
                'source_preview': info['source'][:200] + '...' if len(info['source']) > 200 else info['source']
            }
            for soul, info in self.registered_functions.items()
        }