# app_v2/services/genotype_service.py
"""
Serwis do zarządzania genotypami
"""

from typing import Dict, Any, Optional
import importlib.util
import sys
import asyncio

class GenotypeService:
    """Serwis do zarządzania genotypami"""
    
    _loaded_modules = {}  # Cache załadowanych modułów
    
    @staticmethod
    async def load_and_execute(genotype_name: str, context: Dict[str, Any] = None, call_init: bool = True):
        """Ładuje i wykonuje genotyp"""

        # Sprawdź cache
        if genotype_name in GenotypeService._loaded_modules:
            return GenotypeService._loaded_modules[genotype_name]
        
        # Pobierz soul z bazy
        from app_v2.database.soul_repository import SoulRepository
        soul = await SoulRepository.get_by_name(genotype_name)
        if not soul:
            print(f"❌ Nie znaleziono genotypu: {genotype_name}")
            return None
        
        print(f"🔍 Ładowanie genotypu {genotype_name}")
        
        try:
            # 1. Rozwiąż zależności
            from app_v2.services.dependency_service import DependencyService
            dependencies = soul.get("genesis", {}).get("dependencies", [])
            resolved_deps = await DependencyService.resolve_dependencies(dependencies)
            
            # 2. Stwórz moduł
            spec = importlib.util.spec_from_loader(genotype_name, loader=None, origin="virtual")
            if not spec:
                return None
            
            genotype_module = importlib.util.module_from_spec(spec)
            
            # 3. Przygotuj kontekst wykonania
            execution_context = {
                '__name__': genotype_name,
                '__doc__': soul.get("genesis", {}).get("doc", ""),
                
            }
            if context:
                execution_context.update(context)
            
            # Dodaj zależności do kontekstu
            for dep_name, dep_info in resolved_deps.items():
                if dep_info["type"] == "lux":
                    # Rekurencyjnie załaduj moduł Lux
                    dep_module = await GenotypeService.load_and_execute(dep_name, context, False)
                    execution_context[dep_name] = dep_module
                else:
                    execution_context[dep_name] = dep_info["module"]
            
            # 4. Wykonaj kod (mock - w rzeczywistości exec z soul['genesis']['code'])
            print(f"🚀 Wykonywanie kodu genotypu {genotype_name}")
            # exec(soul['genesis']['code'], execution_context)
            
            # Skopiuj wyniki do modułu
            for key, value in execution_context.items():
                if not key.startswith('__'):
                    setattr(genotype_module, key, value)
            
            # 5. Inicjalizacja
            if call_init and hasattr(genotype_module, 'init'):
                init_func = getattr(genotype_module, 'init')
                if asyncio.iscoroutinefunction(init_func):
                    await init_func()
                else:
                    init_func()
            
            # Cache wynik
            GenotypeService._loaded_modules[genotype_name] = genotype_module
            
            return genotype_module
            
        except Exception as e:
            print(f"❌ Błąd podczas ładowania genotypu {genotype_name}: {e}")
            return None
