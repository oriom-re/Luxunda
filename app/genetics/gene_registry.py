
import asyncio
import inspect
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import uuid

class GeneRegistry:
    """Globalny rejestr genów dostępny w kontekście bytów"""
    
    def __init__(self):
        self._genes: Dict[str, Dict[str, Any]] = {}
        self._active_context: Optional[str] = None
        self._context_stack: List[str] = []
        
    def register_gene(self, gene_name: str, gene_function: Callable, metadata: Dict[str, Any] = None):
        """Rejestruje gen w globalnym rejestrze"""
        self._genes[gene_name] = {
            'function': gene_function,
            'metadata': metadata or {},
            'registered_at': datetime.now().isoformat(),
            'call_count': 0,
            'is_async': asyncio.iscoroutinefunction(gene_function)
        }
        print(f"🧬 Zarejestrowano gen: {gene_name}")
    
    def enter_context(self, context_id: str):
        """Wchodzi w kontekst bytu"""
        self._context_stack.append(self._active_context)
        self._active_context = context_id
    
    def exit_context(self):
        """Wychodzi z kontekstu bytu"""
        if self._context_stack:
            self._active_context = self._context_stack.pop()
        else:
            self._active_context = None
    
    async def call_gene(self, gene_name: str, *args, **kwargs):
        """Wywołuje gen z aktualnego kontekstu"""
        if gene_name not in self._genes:
            return {
                'error': f'Gen "{gene_name}" nie został zainicjowany',
                'available_genes': list(self._genes.keys()),
                'context': self._active_context
            }
        
        gene_info = self._genes[gene_name]
        gene_info['call_count'] += 1
        
        try:
            if gene_info['is_async']:
                result = await gene_info['function'](*args, **kwargs)
            else:
                result = gene_info['function'](*args, **kwargs)
            
            return {
                'success': True,
                'result': result,
                'gene': gene_name,
                'context': self._active_context,
                'call_count': gene_info['call_count']
            }
        except Exception as e:
            return {
                'error': f'Błąd wywołania genu "{gene_name}": {str(e)}',
                'context': self._active_context
            }
    
    def get_available_genes(self) -> List[str]:
        """Zwraca listę dostępnych genów"""
        return list(self._genes.keys())
    
    def get_gene_info(self, gene_name: str) -> Optional[Dict[str, Any]]:
        """Zwraca informacje o genie"""
        return self._genes.get(gene_name)

# Globalny singleton rejestru genów
gene_registry = GeneRegistry()

# Dekorator dla automatycznej rejestracji genów
def gene(name: str = None, **metadata):
    """Dekorator do automatycznej rejestracji genów"""
    def decorator(func):
        gene_name = name or func.__name__
        gene_registry.register_gene(gene_name, func, metadata)
        return func
    return decorator

# Kontekst manager dla pracy z genami
class GeneContext:
    """Kontekst manager dla genów"""
    
    def __init__(self, context_id: str):
        self.context_id = context_id
    
    def __enter__(self):
        gene_registry.enter_context(self.context_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        gene_registry.exit_context()
    
    async def __call__(self, gene_name: str, *args, **kwargs):
        """Pozwala wywoływać geny jak funkcje: context('debug', message)"""
        return await gene_registry.call_gene(gene_name, *args, **kwargs)
    
    def available_genes(self) -> List[str]:
        """Zwraca dostępne geny"""
        return gene_registry.get_available_genes()

# Funkcja pomocnicza do tworzenia kontekstu
def create_gene_context(being_soul: str) -> GeneContext:
    """Tworzy kontekst genowy dla bytu"""
    return GeneContext(being_soul)
