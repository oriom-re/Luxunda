
"""
System uruchamiania Kernel z konfiguracji JSON
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .kernel_system import kernel_system
from .module_system import module_watcher
from ..models.being import Being
from ..models.soul import Soul

class JsonKernelRunner:
    """Uruchamia system Kernel na podstawie konfiguracji JSON"""
    
    def __init__(self):
        self.config = {}
        self.loaded_modules = {}
        self.execution_log = []
    
    async def load_config_from_file(self, config_path: str) -> Dict[str, Any]:
        """Ładuje konfigurację z pliku JSON"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            print(f"📋 Załadowano konfigurację: {config_path}")
            return self.config
            
        except Exception as e:
            print(f"❌ Błąd ładowania konfiguracji {config_path}: {e}")
            return {}
    
    async def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Waliduje konfigurację JSON"""
        errors = []
        
        # Sprawdź wymagane pola
        required_fields = ["name", "version", "kernel", "modules"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Brakuje wymaganego pola: {field}")
        
        # Sprawdź konfigurację kernel
        if "kernel" in config:
            kernel_config = config["kernel"]
            if "scenario" not in kernel_config:
                errors.append("Kernel musi mieć określony scenariusz")
        
        # Sprawdź moduły
        if "modules" in config:
            modules_config = config["modules"]
            if not isinstance(modules_config, list):
                errors.append("Moduły muszą być listą")
            else:
                for i, module in enumerate(modules_config):
                    if "path" not in module:
                        errors.append(f"Moduł {i} nie ma ścieżki")
        
        return errors
    
    async def load_module_from_config(self, module_config: Dict[str, Any]) -> Being:
        """Ładuje moduł na podstawie konfiguracji"""
        try:
            module_path = module_config["path"]
            module_alias = module_config.get("alias", Path(module_path).stem)
            
            # Sprawdź czy plik istnieje
            if not Path(module_path).exists():
                raise FileNotFoundError(f"Plik modułu nie istnieje: {module_path}")
            
            # Zarejestruj jako Being
            being = await module_watcher.register_module_as_being(module_path)
            
            if being:
                # Jeśli moduł ma specjalne parametry konfiguracyjne
                if "config" in module_config:
                    config_data = module_config["config"]
                    # Tutaj można dodać kod do aplikowania konfiguracji do modułu
                    print(f"⚙️ Zastosowano konfigurację do modułu {module_alias}: {config_data}")
                
                self.loaded_modules[module_alias] = being
                print(f"🔧 Załadowano moduł: {module_alias} ({module_path})")
                
            return being
            
        except Exception as e:
            print(f"❌ Błąd ładowania modułu {module_config}: {e}")
            return None
    
    async def execute_startup_sequence(self, startup_config: List[Dict[str, Any]]):
        """Wykonuje sekwencję startową"""
        for step in startup_config:
            try:
                action = step.get("action")
                params = step.get("params", {})
                
                if action == "scan_modules":
                    print("🔍 Skanowanie modułów...")
                    await module_watcher.scan_and_register_all()
                
                elif action == "create_relationships":
                    print("🔗 Tworzenie relacji między modułami...")
                    await module_watcher.create_module_relationships()
                
                elif action == "load_scenario":
                    scenario_name = params.get("name", "default")
                    print(f"🎬 Ładowanie scenariusza: {scenario_name}")
                    await kernel_system.initialize(scenario_name)
                
                elif action == "execute_module_function":
                    module_alias = params.get("module")
                    function_name = params.get("function")
                    args = params.get("args", [])
                    
                    if module_alias in self.loaded_modules:
                        being = self.loaded_modules[module_alias]
                        # Tutaj można dodać kod do wykonywania funkcji modułu
                        print(f"⚡ Wykonano: {module_alias}.{function_name}({args})")
                
                elif action == "wait":
                    delay = params.get("seconds", 1)
                    print(f"⏸️ Czekanie {delay}s...")
                    await asyncio.sleep(delay)
                
                else:
                    print(f"⚠️ Nieznana akcja: {action}")
                
                # Zapisz w logu
                self.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": action,
                    "params": params,
                    "status": "success"
                })
                
            except Exception as e:
                print(f"❌ Błąd wykonania akcji {action}: {e}")
                self.execution_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "action": action,
                    "params": params,
                    "status": "error",
                    "error": str(e)
                })
    
    async def run_from_config(self, config_path: str) -> bool:
        """Główna funkcja uruchamiania z konfiguracji JSON"""
        try:
            # Załaduj konfigurację
            config = await self.load_config_from_file(config_path)
            if not config:
                return False
            
            # Waliduj konfigurację  
            errors = await self.validate_config(config)
            if errors:
                print("❌ Błędy walidacji konfiguracji:")
                for error in errors:
                    print(f"  - {error}")
                return False
            
            print(f"🚀 Uruchamiam system: {config.get('name', 'Unknown')} v{config.get('version', '1.0')}")
            
            # Załaduj moduły
            modules_config = config.get("modules", [])
            for module_config in modules_config:
                await self.load_module_from_config(module_config)
            
            # Wykonaj sekwencję startową
            startup_sequence = config.get("startup", [])
            if startup_sequence:
                print("🎯 Wykonywanie sekwencji startowej...")
                await self.execute_startup_sequence(startup_sequence)
            
            # Inicjalizuj kernel z określonym scenariuszem
            kernel_config = config.get("kernel", {})
            scenario_name = kernel_config.get("scenario", "default")
            await kernel_system.initialize(scenario_name)
            
            print("✅ System uruchomiony pomyślnie!")
            return True
            
        except Exception as e:
            print(f"❌ Błąd uruchamiania systemu: {e}")
            return False
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Zwraca log wykonania"""
        return self.execution_log
    
    def get_loaded_modules(self) -> Dict[str, Being]:
        """Zwraca załadowane moduły"""
        return self.loaded_modules

# Globalna instancja
json_kernel_runner = JsonKernelRunner()
