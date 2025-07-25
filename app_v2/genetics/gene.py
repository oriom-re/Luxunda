# app_v2/genetics/gene.py
"""
Klasa reprezentująca pojedynczy gen w systemie
"""

import uuid
from datetime import datetime
from typing import Dict, Any, List, Callable, Optional

class Gene:
    """Pojedynczy gen - atomowa jednostka funkcjonalności"""
    
    def __init__(self, 
                 name: str,
                 function: Callable,
                 description: str = "",
                 version: str = "1.0.0",
                 requires: List[str] = None,
                 provides: List[str] = None,
                 metadata: Dict[str, Any] = None):
        
        self.uid = str(uuid.uuid4())
        self.name = name
        self.function = function
        self.description = description
        self.version = version
        self.requires = requires or []  # Jakie geny/capabilities wymaga
        self.provides = provides or []  # Jakie capabilities dostarcza
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        
        # Metadata automatyczne z funkcji
        if hasattr(function, '__doc__'):
            self.description = self.description or function.__doc__ or ""
        if hasattr(function, '__name__'):
            self.function_name = function.__name__
        if hasattr(function, '__module__'):
            self.module_name = function.__module__
    
    def to_soul_format(self) -> Dict[str, Any]:
        """Konwertuje gen do formatu soul dla bazy danych"""
        return {
            "uid": self.uid,
            "genesis": {
                "name": self.name,
                "type": "gene",
                "function_name": getattr(self, 'function_name', ''),
                "module_name": getattr(self, 'module_name', ''),
                "description": self.description,
                "version": self.version,
                "requires": self.requires,
                "provides": self.provides,
                "created_at": self.created_at.isoformat(),
                "hash_hex": self._compute_hash()
            },
            "attributes": self.metadata,
            "memories": [],
            "self_awareness": {
                "is_gene": True,
                "function_signature": str(self.function.__annotations__) if hasattr(self.function, '__annotations__') else {}
            }
        }
    
    def _compute_hash(self) -> str:
        """Oblicza hash genu na podstawie jego właściwości"""
        import hashlib
        
        # Combine key properties for hashing
        content = f"{self.name}_{self.version}_{self.description}_{str(self.requires)}_{str(self.provides)}"
        
        # Add function source if available
        try:
            import inspect
            source = inspect.getsource(self.function)
            content += source
        except:
            content += str(self.function)
        
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def execute(self, *args, **kwargs):
        """Wykonuje funkcję genu"""
        import asyncio
        
        if asyncio.iscoroutinefunction(self.function):
            return await self.function(*args, **kwargs)
        else:
            return self.function(*args, **kwargs)
    
    def __repr__(self):
        return f"Gene(name='{self.name}', version='{self.version}', requires={self.requires}, provides={self.provides})"
