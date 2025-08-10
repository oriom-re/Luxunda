
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

# Singleton instance
function_registry = FunctionRegistry()
