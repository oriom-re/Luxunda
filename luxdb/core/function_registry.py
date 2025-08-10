
"""
Globalny rejestr funkcji dla LuxDB.
Pozwala na przechowywanie i odzyskiwanie funkcji na podstawie ich hash.
"""

from typing import Dict, Callable, Optional
import hashlib
import inspect
import asyncio

class FunctionRegistry:
    """Globalny rejestr funkcji"""
    
    _instance = None
    _functions: Dict[str, Callable] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_function(self, func: Callable, name: str = None) -> str:
        """
        Rejestruje funkcję w globalnym rejestrze.
        
        Args:
            func: Funkcja do zarejestrowania
            name: Opcjonalna nazwa funkcji
            
        Returns:
            Hash funkcji
        """
        func_hash = self._calculate_function_hash(func)
        self._functions[func_hash] = func
        
        if name:
            # Możemy też przechowywać funkcje po nazwie
            self._functions[f"name:{name}"] = func
        
        return func_hash
    
    def get_function(self, function_hash: str) -> Optional[Callable]:
        """
        Pobiera funkcję na podstawie hash.
        
        Args:
            function_hash: Hash funkcji
            
        Returns:
            Funkcja lub None jeśli nie znaleziono
        """
        return self._functions.get(function_hash)
    
    def get_function_by_name(self, name: str) -> Optional[Callable]:
        """
        Pobiera funkcję na podstawie nazwy.
        
        Args:
            name: Nazwa funkcji
            
        Returns:
            Funkcja lub None jeśli nie znaleziono
        """
        return self._functions.get(f"name:{name}")
    
    def _calculate_function_hash(self, func: Callable) -> str:
        """Oblicza hash funkcji na podstawie jej kodu"""
        try:
            source = inspect.getsource(func)
            return hashlib.sha256(source.encode()).hexdigest()[:16]
        except:
            # Fallback dla built-in functions
            return hashlib.sha256(str(func).encode()).hexdigest()[:16]
    
    def list_functions(self) -> Dict[str, str]:
        """
        Lista wszystkich zarejestrowanych funkcji.
        
        Returns:
            Słownik {hash: nazwa_funkcji}
        """
        result = {}
        for key, func in self._functions.items():
            if not key.startswith("name:"):
                result[key] = getattr(func, '__name__', str(func))
        return result
    
    async def find_function_soul(self, identifier: str, search_type: str = "auto"):
        """
        Znajduje Soul funkcji - używa zwykłych metod Soul.get().
        
        Args:
            identifier: Hash lub alias funkcji  
            search_type: "hash", "alias" lub "auto"
            
        Returns:
            Soul funkcji lub None
        """
        from ..models.soul import Soul
        
        if search_type == "hash":
            return await Soul.get_by_hash(identifier)
        elif search_type == "alias":
            return await Soul.get_by_alias(identifier)
        else:  # auto
            # Spróbuj najpierw po hash, potem po alias
            soul = await Soul.get_by_hash(identifier)
            if not soul:
                soul = await Soul.get_by_alias(identifier)
            return soul
    
    async def exec_function_by_soul(self, identifier: str, *args, **kwargs):
        """
        Wykonuje funkcję przez duszę po hash lub alias.
        
        Args:
            identifier: Hash lub alias funkcji
            *args: Argumenty pozycyjne
            **kwargs: Argumenty nazwane
            
        Returns:
            Wynik wykonania funkcji
        """
        soul = await self.find_function_soul(identifier)
        if soul:
            return await soul.execute_function_from_soul(*args, **kwargs)
        
        from luxdb.utils.serializer import GeneticResponseFormat
        return GeneticResponseFormat.error_response(
            error=f"Function soul not found: {identifier}",
            error_code="FUNCTION_SOUL_NOT_FOUND"
        )

# Singleton instance
function_registry = FunctionRegistry()
