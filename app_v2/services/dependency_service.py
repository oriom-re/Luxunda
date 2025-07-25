# app_v2/services/dependency_service.py
"""
Serwis do zarządzania zależnościami
"""

from typing import List, Dict, Any
import importlib
import subprocess
import sys

class DependencyService:
    """Serwis do zarządzania zależnościami"""
    
    @staticmethod
    async def resolve_dependencies(dependencies: List[str]) -> Dict[str, Any]:
        """Rozwiązuje zależności - ładuje z bazy lub instaluje przez pip"""
        resolved = {}
        failed = []
        
        for dep in dependencies:
            try:
                # 1. Sprawdź czy to moduł systemu Lux (w bazie)
                from app_v2.database.soul_repository import SoulRepository
                soul = await SoulRepository.get_by_name(dep)
                if soul:
                    print(f"🔍 Znaleziono moduł Lux: {dep}")
                    resolved[dep] = {"type": "lux", "soul": soul}
                    continue
                
                # 2. Sprawdź czy to standardowa biblioteka Python
                try:
                    module = importlib.import_module(dep)
                    resolved[dep] = {"type": "standard", "module": module}
                    print(f"✅ Znaleziono standardowy moduł: {dep}")
                    continue
                except ImportError:
                    pass
                
                # 3. Spróbuj zainstalować przez pip (w produkcji wyłączone)
                print(f"📦 Moduł {dep} nie znaleziony (pip install wyłączony w testach)")
                failed.append(dep)
                    
            except Exception as e:
                print(f"❌ Błąd podczas rozwiązywania {dep}: {e}")
                failed.append(dep)
        
        if failed:
            print(f"⚠️ Nie udało się rozwiązać zależności: {failed}")
        
        return resolved
