
"""
Geny - moduły funkcjonalności dla LuxDB beings
"""

from typing import Dict, Any, Callable
import asyncio
import inspect

class GeneRegistry:
    """Rejestr dostępnych genów"""
    
    _genes: Dict[str, Callable] = {}
    
    @classmethod
    def register(cls, path: str, func: Callable):
        """Rejestruje gen pod określoną ścieżką"""
        cls._genes[path] = func
        print(f"🧬 Zarejestrowano gen: {path}")
    
    @classmethod
    def get_gene(cls, path: str) -> Callable:
        """Pobiera gen po ścieżce"""
        return cls._genes.get(path)
    
    @classmethod
    def list_genes(cls) -> list:
        """Lista wszystkich zarejestrowanych genów"""
        return list(cls._genes.keys())

def gene(path: str):
    """Dekorator do rejestracji genów"""
    def decorator(func):
        GeneRegistry.register(path, func)
        return func
    return decorator

# Auto-import wszystkich genów
from . import communication
from . import analysis  
from . import learning
from . import decision
from . import memory
from . import ingestion
from . import transform
from . import validation
from . import export
from . import monitoring
from . import coordination

__all__ = ["gene", "GeneRegistry"]
