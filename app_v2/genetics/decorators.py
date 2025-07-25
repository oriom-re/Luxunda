# app_v2/genetics/decorators.py
"""
Dekoratory do definiowania genów
"""

from typing import List, Dict, Any, Callable
from functools import wraps
from .gene import Gene
from .gene_registry import GeneRegistry

def gene(name: str = None, 
         description: str = "", 
         version: str = "1.0.0",
         provides: List[str] = None,
         metadata: Dict[str, Any] = None):
    """
    Dekorator do definiowania genu
    
    @gene(name="logger", provides=["logging"], description="Basic logging capability")
    def log_message(message, level="INFO"):
        print(f"[{level}] {message}")
    """
    def decorator(func: Callable):
        gene_name = name or func.__name__
        
        # Wyciągnij requires z dekoratora @requires jeśli istnieje
        requires_list = getattr(func, '_gene_requires', [])
        
        # Stwórz gen
        new_gene = Gene(
            name=gene_name,
            function=func,
            description=description,
            version=version,
            requires=requires_list,
            provides=provides or [],
            metadata=metadata or {}
        )
        
        # Zarejestruj gen
        GeneRegistry.register_gene(new_gene)
        
        # Dodaj metadata do funkcji
        func._gene = new_gene
        func._gene_name = gene_name
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Loguj wykonanie genu
            print(f"🧬 Wykonywanie genu: {gene_name}")
            return await new_gene.execute(*args, **kwargs)
        
        return wrapper
    
    return decorator

def requires(*gene_names: str):
    """
    Dekorator do definiowania zależności genu
    
    @requires("logging", "database")
    @gene(name="audit_logger")
    def audit_log(action, user_id):
        pass
    """
    def decorator(func: Callable):
        # Zapisz wymagania w funkcji
        func._gene_requires = list(gene_names)
        return func
    
    return decorator

def capability(name: str):
    """
    Dekorator do oznaczania funkcji jako dostarczającej określoną capability
    
    @capability("file_storage")
    def save_file(path, content):
        pass
    """
    def decorator(func: Callable):
        if not hasattr(func, '_gene_provides'):
            func._gene_provides = []
        func._gene_provides.append(name)
        return func
    
    return decorator
