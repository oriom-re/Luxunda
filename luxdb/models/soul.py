
#!/usr/bin/env python3
"""
🧬 Soul Model - Kompletny model bez Being
"""

import ulid as _ulid
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
import hashlib
import json
import asyncio
import time
from dataclasses import dataclass, field
from luxdb.core.globals import Globals


@dataclass 
class Soul:
    """
    Soul - KOMPLETNY MODEL systemu LuxDB bez Being
    
    Soul zawiera:
    - Genotyp (niezmienne definicje)
    - Instancje (dane w rejestrze)
    - Funkcje (wykonywalne kod)
    - Zarządzanie stanem
    
    Każda Soul może mieć wiele instancji identyfikowanych przez ULID.
    """
    
    # Rejestr globalny instancji Soul - zawsze aktualny
    _registry: Dict[str, Dict[str, Any]] = field(default_factory=dict, init=False)
    
    # Podstawowe pola Soul
    soul_hash: str = None
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    alias: Optional[str] = None
    genotype: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Cache i wydajność
    _function_registry: Dict[str, Callable] = field(default_factory=dict, init=False, repr=False)
    _module_cache: Optional[Any] = field(default_factory=dict, init=False, repr=False)
    _module_cache_ttl: Optional[float] = field(default=None, init=False, repr=False)
    
    # Tymczasowe pola dla tworzenia instancji
    _temp_ulid: Optional[str] = field(default=None, init=False, repr=False)
    _temp_data: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)
    _temp_alias: Optional[str] = field(default=None, init=False, repr=False)
    _initialized_at: Optional[datetime] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        """Inicjalizacja po utworzeniu obiektu Soul"""
        if not self.soul_hash:
            self.soul_hash = self._generate_soul_hash()
        
        if not self.created_at:
            self.created_at = datetime.now()
        
        self.updated_at = datetime.now()
        
        # Inicjalizuj rejestr dla tego soul_hash jeśli nie istnieje
        if self.soul_hash not in Soul._registry:
            Soul._registry[self.soul_hash] = {}

    @property
    def instances(self) -> Dict[str, Any]:
        """Property zwracające aktualne instancje z rejestru"""
        if self.soul_hash not in Soul._registry:
            Soul._registry[self.soul_hash] = {}
        return Soul._registry[self.soul_hash]

    def _generate_soul_hash(self) -> str:
        """Generuje hash dla genotypu Soul"""
        genotype_str = json.dumps(self.genotype, sort_keys=True)
        return hashlib.sha256(genotype_str.encode()).hexdigest()[:16]

    @classmethod
    async def create(cls, genotype: Dict[str, Any], alias: str = None) -> 'Soul':
        """
        Tworzy nową Soul z genotypem.
        
        Args:
            genotype: Definicja genotypu
            alias: Opcjonalny alias
            
        Returns:
            Nowa Soul
        """
        soul = cls()
        soul.genotype = genotype
        soul.alias = alias
        soul.soul_hash = soul._generate_soul_hash()
        soul.created_at = datetime.now()
        soul.updated_at = datetime.now()
        
        # Inicjalizuj rejestr
        if soul.soul_hash not in Soul._registry:
            Soul._registry[soul.soul_hash] = {}
        
        # Załaduj funkcje z genotypu
        await soul._load_functions_from_genotype()
        
        print(f"🧬 Created Soul: {soul.alias or soul.soul_hash[:8]} with {len(soul._function_registry)} functions")
        
        return soul

    @classmethod 
    async def get_by_hash(cls, soul_hash: str) -> Optional['Soul']:
        """Pobiera Soul po hash"""
        # Implementacja pobierania z bazy danych
        # Na razie zwracamy None - do implementacji z repository
        return None
        
    @classmethod
    async def get_by_alias(cls, alias: str) -> Optional['Soul']:
        """Pobiera Soul po aliasie"""
        # Implementacja pobierania z bazy danych
        # Na razie zwracamy None - do implementacji z repository
        return None

    def init(self, ulid: str = None, data: Dict[str, Any] = None, alias: str = None) -> 'Soul':
        """
        Inicjalizuje Soul z tymczasowymi polami dla tworzenia instancji.
        
        Args:
            ulid: ULID instancji (opcjonalny)
            data: Dane instancji
            alias: Alias instancji
            
        Returns:
            Self dla chain calling
        """
        self._temp_ulid = ulid or str(_ulid.ulid())
        self._temp_data = data if data is not None else {}
        self._temp_alias = alias
        self._initialized_at = datetime.now()
        
        print(f"💭 Soul {self.alias} initialized with temporary instance {self._temp_ulid[:8]}")
        
        return self

    async def set(self) -> Dict[str, Any]:
        """
        Zapisuje instancję do rejestru używając tymczasowych pól z init().
        
        Returns:
            Informacje o utworzonej instancji
        """
        from luxdb.utils.serializer import GeneticResponseFormat
        
        if not self._temp_ulid:
            return GeneticResponseFormat.error_response(
                error="Soul must be initialized with init() before set()",
                error_code="NOT_INITIALIZED"
            )
        
        try:
            # Walidacja danych
            errors = self.validate_data(self._temp_data)
            if errors:
                return GeneticResponseFormat.error_response(
                    error=f"Validation errors: {', '.join(errors)}",
                    error_code="VALIDATION_ERROR"
                )
            
            # Dodaj instancję do rejestru
            instance_data = {
                "ulid": self._temp_ulid,
                "data": self._temp_data.copy(),
                "alias": self._temp_alias,
                "soul_hash": self.soul_hash,
                "created_at": self._initialized_at.isoformat(),
                "updated_at": datetime.now().isoformat(),
                "persistent": True
            }
            
            # Zapisz do rejestru
            self.instances[self._temp_ulid] = instance_data
            
            # Auto-inicjalizacja jeśli Soul ma funkcję init
            if self.has_init_function():
                init_result = await self._auto_initialize_instance(self._temp_ulid)
                if init_result.get('success'):
                    instance_data['initialized'] = True
                    instance_data['function_master'] = True
            
            # Opcjonalnie zapisz do bazy danych
            await self._persist_instance_to_database(instance_data)
            
            print(f"💾 Soul {self.alias} created instance {self._temp_ulid[:8]} (persistent)")
            
            # Wyczyść tymczasowe pola
            self._clear_temp_fields()
            
            return GeneticResponseFormat.success_response(
                data={
                    "instance_created": True,
                    "ulid": instance_data["ulid"],
                    "soul_hash": self.soul_hash,
                    "instance": instance_data
                },
                soul_context={
                    "soul_hash": self.soul_hash,
                    "genotype": self.genotype
                }
            )
            
        except Exception as e:
            self._clear_temp_fields()
            return GeneticResponseFormat.error_response(
                error=f"Failed to create instance: {str(e)}",
                error_code="INSTANCE_CREATION_ERROR"
            )

    async def get_or_create(self, ulid: str = None, data: Dict[str, Any] = None, 
                           unique_by: str = "soul_hash", max_instances: int = None) -> Dict[str, Any]:
        """
        Pobiera istniejącą instancję lub tworzy nową.
        
        Args:
            ulid: ULID instancji
            data: Dane dla nowej instancji
            unique_by: Sposób sprawdzania unikalności
            max_instances: Maksymalna liczba instancji (pooling)
            
        Returns:
            Instancja w formacie dict
        """
        from luxdb.utils.serializer import GeneticResponseFormat
        
        try:
            # Sprawdź istniejące instancje
            if unique_by == "soul_hash" and len(self.instances) > 0:
                # Zwróć pierwszą istniejącą instancję
                existing_ulid = next(iter(self.instances.keys()))
                existing_instance = self.instances[existing_ulid]
                
                # Opcjonalnie aktualizuj dane
                if data:
                    existing_instance["data"].update(data)
                    existing_instance["updated_at"] = datetime.now().isoformat()
                    await self._persist_instance_to_database(existing_instance)
                
                return GeneticResponseFormat.success_response(
                    data={
                        "instance_found": True,
                        "ulid": existing_instance["ulid"],
                        "instance": existing_instance
                    }
                )
            
            # Sprawdź pooling
            if max_instances and len(self.instances) >= max_instances:
                # Reaktywuj nieaktywną instancję lub zwróć pierwszą
                for inst_ulid, instance in self.instances.items():
                    if not instance["data"].get("active", True):
                        instance["data"]["active"] = True
                        instance["updated_at"] = datetime.now().isoformat()
                        if data:
                            instance["data"].update(data)
                        await self._persist_instance_to_database(instance)
                        
                        return GeneticResponseFormat.success_response(
                            data={
                                "instance_reactivated": True,
                                "ulid": instance["ulid"],
                                "instance": instance
                            }
                        )
                
                # Zwróć pierwszą aktywną
                first_ulid = next(iter(self.instances.keys()))
                return GeneticResponseFormat.success_response(
                    data={
                        "instance_pool_limit_reached": True,
                        "ulid": first_ulid,
                        "instance": self.instances[first_ulid]
                    }
                )
            
            # Utwórz nową instancję
            new_ulid = ulid or str(_ulid.ulid())
            return await self.init(ulid=new_ulid, data=data).set()
            
        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"get_or_create failed: {str(e)}",
                error_code="GET_OR_CREATE_ERROR"
            )

    async def get_instance(self, ulid: str) -> Optional[Dict[str, Any]]:
        """Pobiera instancję po ULID"""
        return self.instances.get(ulid)

    async def update_instance(self, ulid: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Aktualizuje dane instancji"""
        from luxdb.utils.serializer import GeneticResponseFormat
        
        if ulid not in self.instances:
            return GeneticResponseFormat.error_response(
                error="Instance not found",
                error_code="INSTANCE_NOT_FOUND"
            )
        
        try:
            instance = self.instances[ulid]
            instance["data"].update(data)
            instance["updated_at"] = datetime.now().isoformat()
            
            await self._persist_instance_to_database(instance)
            
            return GeneticResponseFormat.success_response(
                data={
                    "instance_updated": True,
                    "ulid": ulid,
                    "instance": instance
                }
            )
            
        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Failed to update instance: {str(e)}",
                error_code="INSTANCE_UPDATE_ERROR"
            )

    async def delete_instance(self, ulid: str) -> Dict[str, Any]:
        """Usuwa instancję z rejestru"""
        from luxdb.utils.serializer import GeneticResponseFormat
        
        if ulid not in self.instances:
            return GeneticResponseFormat.error_response(
                error="Instance not found",
                error_code="INSTANCE_NOT_FOUND"
            )
        
        try:
            # Usuń z rejestru
            deleted_instance = self.instances.pop(ulid)
            
            # Usuń z bazy danych
            await self._delete_instance_from_database(ulid)
            
            return GeneticResponseFormat.success_response(
                data={
                    "instance_deleted": True,
                    "ulid": ulid,
                    "deleted_instance": deleted_instance
                }
            )
            
        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Failed to delete instance: {str(e)}",
                error_code="INSTANCE_DELETE_ERROR"
            )

    def list_instances(self) -> List[Dict[str, Any]]:
        """Lista wszystkich instancji"""
        return list(self.instances.values())

    def get_instance_count(self) -> int:
        """Liczba instancji"""
        return len(self.instances)

    async def execute_function(self, function_name: str, ulid: str = None, *args, **kwargs) -> Dict[str, Any]:
        """
        Wykonuje funkcję Soul w kontekście instancji.
        
        Args:
            function_name: Nazwa funkcji
            ulid: ULID instancji (opcjonalny)
            *args: Argumenty pozycyjne
            **kwargs: Argumenty nazwane
            
        Returns:
            Wynik wykonania funkcji
        """
        from luxdb.utils.serializer import GeneticResponseFormat
        
        try:
            # Znajdź funkcję
            if function_name not in self._function_registry:
                return GeneticResponseFormat.error_response(
                    error=f"Function '{function_name}' not found",
                    error_code="FUNCTION_NOT_FOUND"
                )
            
            func = self._function_registry[function_name]
            
            # Przygotuj kontekst
            instance_context = None
            if ulid:
                instance_context = self.instances.get(ulid)
                if not instance_context:
                    return GeneticResponseFormat.error_response(
                        error=f"Instance {ulid} not found",
                        error_code="INSTANCE_NOT_FOUND"
                    )
            
            # Dodaj kontekst do kwargs jeśli funkcja go oczekuje
            if 'instance_context' not in kwargs and instance_context:
                kwargs['instance_context'] = instance_context
            
            # Wykonaj funkcję
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Aktualizuj statystyki instancji
            if ulid and instance_context:
                instance_context["data"]["execution_count"] = instance_context["data"].get("execution_count", 0) + 1
                instance_context["data"]["last_execution"] = datetime.now().isoformat()
                instance_context["updated_at"] = datetime.now().isoformat()
                await self._persist_instance_to_database(instance_context)
            
            return GeneticResponseFormat.success_response(
                data={
                    "function_name": function_name,
                    "result": result,
                    "executed_at": datetime.now().isoformat(),
                    "instance_ulid": ulid
                }
            )
            
        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Function execution failed: {str(e)}",
                error_code="FUNCTION_EXECUTION_ERROR"
            )

    async def execute_on_all_instances(self, function_name: str, *args, **kwargs) -> Dict[str, Any]:
        """Wykonuje funkcję na wszystkich instancjach"""
        from luxdb.utils.serializer import GeneticResponseFormat
        
        results = {}
        errors = {}
        
        for ulid in self.instances.keys():
            try:
                result = await self.execute_function(function_name, ulid, *args, **kwargs)
                results[ulid] = result
            except Exception as e:
                errors[ulid] = str(e)
        
        return GeneticResponseFormat.success_response(
            data={
                "function_name": function_name,
                "instances_executed": len(results),
                "instances_failed": len(errors),
                "results": results,
                "errors": errors if errors else None
            }
        )

    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Waliduje dane zgodnie z genotypem"""
        errors = []
        attributes = self.genotype.get("attributes", {})
        
        for attr_name, attr_def in attributes.items():
            if attr_def.get("required", False) and attr_name not in data:
                errors.append(f"Required attribute '{attr_name}' missing")
            
            if attr_name in data:
                expected_type = attr_def.get("py_type", "str")
                actual_value = data[attr_name]
                
                # Prosta walidacja typów
                if expected_type == "str" and not isinstance(actual_value, str):
                    errors.append(f"Attribute '{attr_name}' should be str, got {type(actual_value).__name__}")
                elif expected_type == "int" and not isinstance(actual_value, int):
                    errors.append(f"Attribute '{attr_name}' should be int, got {type(actual_value).__name__}")
                elif expected_type == "float" and not isinstance(actual_value, (int, float)):
                    errors.append(f"Attribute '{attr_name}' should be float, got {type(actual_value).__name__}")
                elif expected_type == "bool" and not isinstance(actual_value, bool):
                    errors.append(f"Attribute '{attr_name}' should be bool, got {type(actual_value).__name__}")
        
        return errors

    def has_init_function(self) -> bool:
        """Sprawdza czy Soul ma funkcję init"""
        return "init" in self._function_registry

    def has_execute_function(self) -> bool:
        """Sprawdza czy Soul ma funkcję execute"""
        return "execute" in self._function_registry

    def list_functions(self) -> List[str]:
        """Lista dostępnych funkcji"""
        return list(self._function_registry.keys())

    def get_functions_count(self) -> int:
        """Liczba dostępnych funkcji"""
        return len(self._function_registry)

    async def _load_functions_from_genotype(self):
        """Ładuje funkcje z genotypu"""
        if "module_source" in self.genotype:
            await self._load_functions_from_module_source()
        elif "functions" in self.genotype:
            await self._load_functions_from_definitions()

    async def _load_functions_from_module_source(self):
        """Ładuje funkcje z module_source"""
        try:
            module_source = self.genotype["module_source"]
            
            # Kompiluj moduł
            compiled_code = compile(module_source, f"<soul_{self.soul_hash}>", "exec")
            module_globals = {}
            exec(compiled_code, module_globals)
            
            # Wyciągnij funkcje
            for name, obj in module_globals.items():
                if callable(obj) and not name.startswith("_"):
                    self._function_registry[name] = obj
            
            print(f"🔧 Loaded {len(self._function_registry)} functions from module_source")
            
        except Exception as e:
            print(f"❌ Failed to load functions from module_source: {e}")

    async def _load_functions_from_definitions(self):
        """Ładuje funkcje z definicji w genotypie"""
        functions = self.genotype.get("functions", {})
        
        for func_name, func_def in functions.items():
            try:
                # Prosta implementacja - dla bardziej zaawansowanych przypadków
                # można dodać interpretację kodu z func_def
                def simple_func(*args, **kwargs):
                    return f"Function {func_name} executed with args: {args}, kwargs: {kwargs}"
                
                self._function_registry[func_name] = simple_func
                
            except Exception as e:
                print(f"❌ Failed to load function {func_name}: {e}")

    async def _auto_initialize_instance(self, ulid: str) -> Dict[str, Any]:
        """Automatyczna inicjalizacja instancji przez funkcję init"""
        if not self.has_init_function():
            return {"success": False, "error": "No init function"}
        
        try:
            instance = self.instances[ulid]
            
            # Kontekst dla funkcji init
            init_context = {
                "ulid": ulid,
                "data": instance["data"].copy(),
                "soul_hash": self.soul_hash,
                "creation_time": instance["created_at"]
            }
            
            # Wykonaj init
            result = await self.execute_function("init", ulid, instance_context=init_context)
            
            if result.get("success"):
                # Oznacz jako zainicjalizowaną
                instance["data"]["_initialized"] = True
                instance["data"]["_init_time"] = datetime.now().isoformat()
                instance["updated_at"] = datetime.now().isoformat()
                
                print(f"🎯 Instance {ulid[:8]} auto-initialized successfully")
                return {"success": True}
            else:
                return {"success": False, "error": result.get("error")}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _persist_instance_to_database(self, instance_data: Dict[str, Any]):
        """Zapisuje instancję do bazy danych"""
        # Placeholder - implementacja z repository
        # Na razie tylko log
        print(f"💾 Persisting instance {instance_data['ulid'][:8]} to database")

    async def _delete_instance_from_database(self, ulid: str):
        """Usuwa instancję z bazy danych"""
        # Placeholder - implementacja z repository
        print(f"🗑️ Deleting instance {ulid[:8]} from database")

    def _clear_temp_fields(self):
        """Czyści tymczasowe pola po operacji"""
        self._temp_ulid = None
        self._temp_data = {}
        self._temp_alias = None
        self._initialized_at = None

    def get_soul_info(self) -> Dict[str, Any]:
        """Informacje o Soul"""
        return {
            "soul_hash": self.soul_hash,
            "alias": self.alias,
            "genotype": self.genotype,
            "instances_count": self.get_instance_count(),
            "functions_count": self.get_functions_count(),
            "functions": self.list_functions(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje Soul do słownika"""
        return {
            "soul_hash": self.soul_hash,
            "global_ulid": self.global_ulid,
            "alias": self.alias,
            "genotype": self.genotype,
            "instances": self.instances,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def to_json_serializable(self) -> Dict[str, Any]:
        """Wersja JSON-serializable"""
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Soul':
        """Tworzy Soul z słownika"""
        soul = cls()
        soul.soul_hash = data.get("soul_hash")
        soul.global_ulid = data.get("global_ulid", Globals.GLOBAL_ULID)
        soul.alias = data.get("alias")
        soul.genotype = data.get("genotype", {})
        
        # Przywróć instancje do rejestru
        if soul.soul_hash and "instances" in data:
            Soul._registry[soul.soul_hash] = data["instances"]
        
        # Konwersja dat
        if data.get("created_at"):
            soul.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            soul.updated_at = datetime.fromisoformat(data["updated_at"])
        
        return soul

    def __repr__(self):
        instances_count = self.get_instance_count()
        functions_count = self.get_functions_count()
        return f"Soul(hash={self.soul_hash[:8]}..., alias={self.alias}, instances={instances_count}, functions={functions_count})"

    def __json__(self):
        """Protokół dla JSON serializacji"""
        return self.to_dict()
