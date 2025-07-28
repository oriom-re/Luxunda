# app_v2/services/dependency_service.py
"""
Serwis do zarządzania zależnościami
"""

from typing import List, Dict, Any
import importlib
import subprocess
import sys
from app_v2.database.soul_repository import SoulRepository

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
                
                # 3. Spróbuj zainstalować przez pip
                print(f"📦 Instalowanie {dep} przez pip...")
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", dep
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    module = importlib.import_module(dep)
                    resolved[dep] = {"type": "installed", "module": module}
                    print(f"✅ Zainstalowano i załadowano: {dep}")
                else:
                    print(f"❌ Nie udało się zainstalować {dep}: {result.stderr}")
                    failed.append(dep)
                    
            except Exception as e:
                print(f"❌ Błąd podczas rozwiązywania {dep}: {e}")
                failed.append(dep)
        
        return resolved
