"""
Model Soul (Dusza/Genotyp) dla LuxDB.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
import ulid
import inspect
import asyncio

from ..core.globals import Globals

@dataclass
class Soul:
    """
    Soul reprezentuje genotyp - szablon dla bytów.

    Każdy Soul ma unikalny hash wygenerowany z genotypu
    i może być używany do tworzenia wielu Being (bytów).
    """

    soul_hash: str = None
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    alias: str = None
    genotype: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    # Function registry for this soul
    _function_registry: Dict[str, Callable] = field(default_factory=dict, init=False, repr=False)

    @classmethod
    async def create(cls, genotype: Dict[str, Any], alias: str = None) -> 'Soul':
        """
        Tworzy nowy Soul na podstawie genotypu.

        Args:
            genotype: Definicja struktury danych
            alias: Opcjonalny alias dla łatwego odszukiwania

        Returns:
            Nowy obiekt Soul

        Example:
            ```python
            genotype = {
                "genesis": {"name": "user", "version": "1.0"},
                "attributes": {
                    "name": {"py_type": "str"},
                    "email": {"py_type": "str", "unique": True}
                }
            }
            soul = await Soul.create(genotype, alias="user_profile")
            ```
        """
        try:
            from ..utils.validators import validate_genotype
            from ..repository.soul_repository import SoulRepository

            # Walidacja genotypu
            validate_genotype(genotype)

            # Tworzenie Soul
            soul = cls()
            soul.alias = alias
            soul.genotype = genotype
            soul.soul_hash = hashlib.sha256(
                json.dumps(genotype, sort_keys=True).encode()
            ).hexdigest()
            soul.created_at = datetime.now()

            # Zapis do bazy danych
            result = await SoulRepository.set(soul)
            if not result.get('success'):
                raise Exception(f"Failed to create soul: {result.get('error', 'Unknown error')}")

            return soul

        except Exception as e:
            print(f"❌ Błąd tworzenia Soul: {e}")
            raise Exception(f"Failed to create soul: {str(e)}")

    @classmethod
    async def get(cls, **kwargs) -> Optional['Soul']:
        """
        Uniwersalna metoda get dla Soul.

        Args:
            **kwargs: Parametry wyszukiwania (alias, hash, itp.)

        Returns:
            Soul lub None jeśli nie znaleziono
        """
        if 'alias' in kwargs:
            return await cls.get_by_alias(kwargs['alias'])
        elif 'hash' in kwargs:
            return await cls.get_by_hash(kwargs['hash'])
        elif 'soul_hash' in kwargs:
            return await cls.get_by_hash(kwargs['soul_hash'])
        else:
            # Jeśli podano tylko alias jako pierwszy argument
            for value in kwargs.values():
                if isinstance(value, str):
                    # Próbuj najpierw alias, potem hash
                    soul = await cls.get_by_alias(value)
                    if soul:
                        return soul
                    return await cls.get_by_hash(value)
        return None

    @classmethod
    async def set(cls, genotype: Dict[str, Any], alias: str = None) -> 'Soul':
        """
        Metoda set dla Soul (alias dla create).

        Args:
            genotype: Definicja struktury danych
            alias: Opcjonalny alias

        Returns:
            Nowy obiekt Soul
        """
        return await cls.create(genotype, alias)

    @classmethod
    async def get_by_hash(cls, hash: str) -> Optional['Soul']:
        """
        Ładuje Soul po global_ulid.

        Args:
            hash: Global ULID soul

        Returns:
            Soul lub None jeśli nie znaleziono
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.get_by_hash(hash)
        soul = result.get('soul') if result.get('success') else None
        
        if soul:
            # Załaduj funkcje z genotypu
            await soul.load_functions_from_genotype()
        
        return soul

    @classmethod
    async def get_by_alias(cls, alias: str) -> Optional['Soul']:
        """
        Ładuje Soul po aliasie.

        Args:
            alias: Alias soul

        Returns:
            Soul lub None jeśli nie znaleziono
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.get_by_alias(alias)
        soul = result.get('soul') if result.get('success') else None
        
        if soul:
            # Załaduj funkcje z genotypu
            await soul.load_functions_from_genotype()
        
        return soul

    @classmethod
    async def get_all(cls) -> List['Soul']:
        """
        Ładuje wszystkie Soul z bazy danych.

        Returns:
            Lista wszystkich Soul
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.get_all_souls()
        souls = result.get('souls', [])
        return [soul for soul in souls if soul is not None]

    @classmethod
    async def get_all_by_alias(cls, alias: str) -> List['Soul']:
        """
        Ładuje wszystkie Soul o danym aliasie.

        Args:
            alias: Alias do wyszukania

        Returns:
            Lista Soul o podanym aliasie
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.get_all_by_alias(alias)
        souls = result.get('souls', [])
        return [soul for soul in souls if soul is not None]

    async def save(self) -> bool:
        """
        Zapisuje zmiany w Soul do bazy danych.

        Returns:
            True jeśli zapis się powiódł
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.save(self)
        return result.get('success', False)

    def get_attribute_types(self) -> Dict[str, str]:
        """
        Zwraca mapowanie nazw atrybutów na ich typy.

        Returns:
            Słownik {nazwa_atrybutu: typ_py}
        """
        attributes = self.genotype.get("attributes", {})
        return {
            name: attr.get("py_type", "str")
            for name, attr in attributes.items()
        }

    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Waliduje dane względem genotypu.

        Args:
            data: Dane do walidacji

        Returns:
            Lista błędów walidacji (pusta jeśli brak błędów)
        """
        errors = []
        attributes = self.genotype.get("attributes", {})

        for attr_name, attr_config in attributes.items():
            py_type = attr_config.get("py_type", "str")
            required = attr_config.get("required", False)
            value = data.get(attr_name)

            # Sprawdź wymagane pola
            if required and value is None and "default" not in attr_config:
                errors.append(f"Missing required attribute: {attr_name}")
                continue

            # Użyj domyślnej wartości jeśli nie podano
            if value is None and "default" in attr_config:
                data[attr_name] = attr_config["default"]
                value = data[attr_name]

            # Sprawdź typ
            if value is not None:
                if py_type == "str" and not isinstance(value, str):
                    errors.append(f"Attribute {attr_name} must be string, got {type(value).__name__}")
                elif py_type == "int" and not isinstance(value, int):
                    errors.append(f"Attribute {attr_name} must be integer, got {type(value).__name__}")
                elif py_type == "float" and not isinstance(value, (int, float)):
                    errors.append(f"Attribute {attr_name} must be float, got {type(value).__name__}")
                elif py_type == "bool" and not isinstance(value, bool):
                    errors.append(f"Attribute {attr_name} must be boolean, got {type(value).__name__}")
                elif py_type == "dict" and not isinstance(value, dict):
                    errors.append(f"Attribute {attr_name} must be dict, got {type(value).__name__}")
                elif py_type.startswith("List[") and not isinstance(value, list):
                    errors.append(f"Attribute {attr_name} must be list, got {type(value).__name__}")

        return errors

    def get_default_data(self) -> Dict[str, Any]:
        """
        Zwraca domyślne dane na podstawie definicji atrybutów w genotypie.

        Returns:
            Słownik z domyślnymi wartościami
        """
        default_data = {}
        attributes = self.genotype.get("attributes", {})

        for attr_name, attr_config in attributes.items():
            if "default" in attr_config:
                default_data[attr_name] = attr_config["default"]
            elif not attr_config.get("required", False):
                # Ustaw domyślne wartości na podstawie typu
                py_type = attr_config.get("py_type", "str")
                if py_type == "str":
                    default_data[attr_name] = ""
                elif py_type == "int":
                    default_data[attr_name] = 0
                elif py_type == "float":
                    default_data[attr_name] = 0.0
                elif py_type == "bool":
                    default_data[attr_name] = False
                elif py_type == "dict":
                    default_data[attr_name] = {}
                elif py_type.startswith("List["):
                    default_data[attr_name] = []

        return default_data

    async def get_hash(self) -> str:
        """Zwraca hash Soul"""
        return self.soul_hash

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje Soul do słownika dla serializacji"""
        return {
            'soul_hash': self.soul_hash,
            'global_ulid': self.global_ulid,
            'alias': self.alias,
            'genotype': self.genotype,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def to_json_serializable(self) -> Dict[str, Any]:
        """Automatycznie wykrywa i konwertuje strukturę do JSON-serializable"""
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Soul':
        """Tworzy Soul z słownika"""
        soul = cls()
        soul.soul_hash = data.get('soul_hash')
        soul.global_ulid = data.get('global_ulid', Globals.GLOBAL_ULID)
        soul.alias = data.get('alias')
        soul.genotype = data.get('genotype', {})
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                soul.created_at = datetime.fromisoformat(data['created_at'])
            else:
                soul.created_at = data['created_at']
        return soul

    def __json__(self):
        """Protokół dla automatycznej serializacji JSON"""
        return self.to_dict()

    def _register_immutable_function(self, name: str, func: Callable):
        """
        Rejestruje funkcję w niezmiennym rejestrze (tylko wewnętrznie).
        Ta metoda nie modyfikuje genotypu - funkcje muszą być zdefiniowane przy tworzeniu.
        """
        self._function_registry[name] = func

    def register_function(self, name: str, func: Callable, description: str = None):
        """
        Rejestruje funkcję w genotypie i w lokalnym rejestrze.
        
        Args:
            name: Nazwa funkcji
            func: Funkcja do zarejestrowania
            description: Opis funkcji
        """
        from ..core.function_registry import function_registry
        
        # Zarejestruj w globalnym rejestrze
        func_hash = function_registry.register_function(func, name)
        
        # Dodaj do genotypu
        if "functions" not in self.genotype:
            self.genotype["functions"] = {}
        
        self.genotype["functions"][name] = {
            "py_type": "function",
            "description": description or f"Function {name}",
            "signature": self._get_function_signature(func),
            "is_async": asyncio.iscoroutinefunction(func),
            "function_hash": func_hash
        }
        
        # Dodaj do lokalnego rejestru
        self._function_registry[name] = func

    async def register_function_and_save(self, name: str, func: Callable, description: str = None):
        """
        Rejestruje funkcję i zapisuje zmiany w bazie danych.
        
        Args:
            name: Nazwa funkcji
            func: Funkcja do zarejestrowania
            description: Opis funkcji
        """
        self.register_function(name, func, description)
        await self.save()

    def _calculate_function_hash(self, func: Callable) -> str:
        """Oblicza hash funkcji na podstawie jej kodu"""
        import inspect
        import hashlib
        
        try:
            source = inspect.getsource(func)
            return hashlib.sha256(source.encode()).hexdigest()[:16]
        except:
            # Fallback dla built-in functions
            return hashlib.sha256(str(func).encode()).hexdigest()[:16]

    async def load_functions_from_genotype(self):
        """
        Ładuje funkcje z genotypu do lokalnego rejestru.
        Ta metoda musi być wywołana po załadowaniu Soul z bazy danych.
        """
        functions_def = self.genotype.get("functions", {})
        
        for func_name, func_info in functions_def.items():
            if func_name not in self._function_registry:
                # Funkcja nie jest załadowana - próbuj znaleźć ją w globalnym rejestrze
                loaded_func = await self._load_function_by_hash(func_info.get("function_hash"))
                if loaded_func:
                    self._function_registry[func_name] = loaded_func
                else:
                    print(f"⚠️ Warning: Function '{func_name}' from genotype not found in registry")

    async def _load_function_by_hash(self, function_hash: str) -> Optional[Callable]:
        """
        Ładuje funkcję na podstawie jej hash z globalnego rejestru funkcji.
        
        Args:
            function_hash: Hash funkcji
            
        Returns:
            Funkcja lub None jeśli nie znaleziono
        """
        from ..core.function_registry import function_registry
        return function_registry.get_function(function_hash)

    def _get_function_signature(self, func: Callable) -> Dict[str, Any]:
        """Pobiera sygnaturę funkcji"""
        try:
            sig = inspect.signature(func)
            return {
                "parameters": {
                    param.name: {
                        "type": str(param.annotation) if param.annotation != param.empty else "Any",
                        "default": str(param.default) if param.default != param.empty else None
                    }
                    for param in sig.parameters.values()
                },
                "return_type": str(sig.return_annotation) if sig.return_annotation != sig.empty else "Any"
            }
        except Exception as e:
            return {"error": str(e)}

    def get_function(self, name: str) -> Optional[Callable]:
        """Pobiera funkcję z rejestru"""
        return self._function_registry.get(name)

    def list_functions(self) -> List[str]:
        """Lista dostępnych funkcji"""
        return list(self._function_registry.keys())

    def get_function_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Pobiera informacje o funkcji"""
        if name in self.genotype.get("functions", {}):
            return self.genotype["functions"][name]
        return None

    async def execute_function(self, name: str, *args, **kwargs) -> Dict[str, Any]:
        """
        Wykonuje funkcję zarejestrowaną w Soul.

        Args:
            name: Nazwa funkcji
            *args: Argumenty pozycyjne
            **kwargs: Argumenty nazwane

        Returns:
            Wynik wykonania funkcji w standardowym formacie genetycznym
        """
        from luxdb.utils.serializer import GeneticResponseFormat
        
        try:
            func = self.get_function(name)
            if not func:
                return GeneticResponseFormat.error_response(
                    error=f"Function '{name}' not found in soul '{self.alias}'",
                    error_code="FUNCTION_NOT_FOUND"
                )

            # Wykonaj funkcję
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            return GeneticResponseFormat.success_response(
                data={
                    "function_name": name,
                    "result": result,
                    "executed_at": datetime.now().isoformat()
                },
                soul_context={
                    "soul_hash": self.soul_hash,
                    "function_info": self.get_function_info(name)
                }
            )

        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Function execution error: {str(e)}",
                error_code="FUNCTION_EXECUTION_ERROR",
                soul_context={"soul_hash": self.soul_hash, "function_name": name}
            )

    @classmethod
    async def create_function_soul(cls, name: str, func: Callable, description: str = None, alias: str = None, version: str = "1.0.0") -> 'Soul':
        """
        Tworzy Soul dla funkcji - funkcja to zwykła Soul z typem "function".

        Args:
            name: Nazwa funkcji
            func: Funkcja
            description: Opis funkcji
            alias: Alias dla soul
            version: Wersja genotypu

        Returns:
            Nowy Soul z funkcją
        """
        import inspect
        
        try:
            source_code = inspect.getsource(func)
        except:
            source_code = str(func)
        
        # Genotyp dla funkcji - zwykła Soul z typem "function"
        function_genotype = {
            "genesis": {
                "name": alias or f"function_{name}",
                "type": "function",
                "version": version,
                "description": description or f"Function {name}",
                "created_at": datetime.now().isoformat()
            },
            "attributes": {
                "function_name": {"py_type": "str", "default": name},
                "source_code": {"py_type": "str", "default": source_code},
                "language": {"py_type": "str", "default": "python"},
                "signature": {"py_type": "dict", "default": cls._get_function_signature_static(func)},
                "is_async": {"py_type": "bool", "default": asyncio.iscoroutinefunction(func)},
                "usage_count": {"py_type": "int", "default": 0},
                "last_used": {"py_type": "str", "default": ""}
            }
        }

        # Utwórz zwykłą Soul
        soul = await cls.create(function_genotype, alias or f"function_{name}")
        
        # Zarejestruj w globalnym rejestrze
        from ..core.function_registry import function_registry
        function_registry.register_function(func, name)
        
        # Załaduj funkcję do lokalnego rejestru
        soul._register_immutable_function(name, func)
        
        return soul

    @classmethod 
    async def create_evolved_version(cls, original_soul: 'Soul', changes: Dict[str, Any], new_version: str = None) -> 'Soul':
        """
        Tworzy nową wersję Soul z ewolucją genotypu.
        
        Args:
            original_soul: Oryginalna Soul
            changes: Zmiany do wprowadzenia
            new_version: Nowa wersja (automatyczna jeśli None)
            
        Returns:
            Nowy Soul z nowym hashem
        """
        # Skopiuj oryginalny genotyp
        evolved_genotype = original_soul.genotype.copy()
        
        # Automatyczne wersjonowanie
        if new_version is None:
            old_version = evolved_genotype.get("genesis", {}).get("version", "1.0.0")
            parts = old_version.split(".")
            major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0
            new_version = f"{major}.{minor}.{patch + 1}"
        
        # Aktualizuj genesis
        if "genesis" not in evolved_genotype:
            evolved_genotype["genesis"] = {}
        evolved_genotype["genesis"]["version"] = new_version
        evolved_genotype["genesis"]["parent_hash"] = original_soul.soul_hash
        evolved_genotype["genesis"]["evolution_timestamp"] = datetime.now().isoformat()
        
        # Zastosuj zmiany
        for key, value in changes.items():
            if "." in key:  # Nested path like "attributes.new_field"
                keys = key.split(".")
                current = evolved_genotype
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                evolved_genotype[key] = value
        
        # Utwórz nową Soul
        return await cls.create(evolved_genotype, original_soul.alias)

    @classmethod
    def _get_function_signature_static(cls, func: Callable) -> Dict[str, Any]:
        """Statyczna wersja pobierania sygnatury funkcji"""
        try:
            sig = inspect.signature(func)
            return {
                "parameters": {
                    param.name: {
                        "type": str(param.annotation) if param.annotation != param.empty else "Any",
                        "default": str(param.default) if param.default != param.empty else None
                    }
                    for param in sig.parameters.values()
                },
                "return_type": str(sig.return_annotation) if sig.return_annotation != sig.empty else "Any"
            }
        except Exception as e:
            return {"error": str(e)}
    
    @classmethod
    async def find_function_by_hash(cls, func_hash: str) -> Optional['Soul']:
        """
        Znajdź funkcję po hash - używa zwykłej metody get().
        """
        return await cls.get_by_hash(func_hash)
    
    @classmethod
    async def find_function_by_alias(cls, alias: str) -> Optional['Soul']:
        """
        Znajdź funkcję po alias - używa zwykłej metody get().
        """
        return await cls.get_by_alias(alias)
    
    @classmethod
    async def get_function_souls(cls) -> List['Soul']:
        """
        Zwraca wszystkie Soul typu "function".
        """
        all_souls = await cls.get_all()
        return [soul for soul in all_souls 
                if soul.genotype.get("genesis", {}).get("type") == "function"]
    
    async def execute_function_from_soul(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Wykonuje funkcję z Soul typu "function".
        """
        from luxdb.utils.serializer import GeneticResponseFormat
        
        try:
            # Sprawdź czy to funkcja
            if self.genotype.get("genesis", {}).get("type") != "function":
                return GeneticResponseFormat.error_response(
                    error="Soul is not a function type",
                    error_code="NOT_FUNCTION_SOUL"
                )
            
            # Pobierz informacje o funkcji
            default_data = self.get_default_data()
            source_code = default_data.get("source_code", "")
            function_name = default_data.get("function_name", "")
            
            if not source_code:
                return GeneticResponseFormat.error_response(
                    error="No source code in function soul",
                    error_code="NO_SOURCE_CODE"
                )
            
            # Wykonaj kod funkcji
            exec_globals = {}
            exec(source_code, exec_globals)
            
            if function_name not in exec_globals:
                return GeneticResponseFormat.error_response(
                    error=f"Function '{function_name}' not found",
                    error_code="FUNCTION_NOT_FOUND"
                )
            
            func = exec_globals[function_name]
            
            # Wywołaj funkcję
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            return GeneticResponseFormat.success_response(
                data={
                    "function_name": function_name,
                    "result": result,
                    "executed_at": datetime.now().isoformat()
                },
                soul_context={"soul_hash": self.soul_hash}
            )
            
        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=f"Function execution error: {str(e)}",
                error_code="FUNCTION_EXECUTION_ERROR",
                soul_context={"soul_hash": self.soul_hash}
            )
    
    async def _update_usage_stats(self):
        """Aktualizuje statystyki użycia funkcji"""
        try:
            # Tworzy being i aktualizuje statystyki
            from ..models.being import Being
            
            # Uzyskaj dostęp do danych duszy
            current_data = self.get_default_data()
            current_data["usage_count"] = current_data.get("usage_count", 0) + 1
            current_data["last_used"] = datetime.now().isoformat()
            
            # Utwórz tymczasowe being dla aktualizacji
            being_result = await Being.set(
                soul=self,
                data=current_data,
                alias=f"temp_stats_{self.soul_hash[:8]}"
            )
            
            if being_result.get("success"):
                # Zaktualizuj being
                being = being_result["data"]["being"]
                await being.save()
        except Exception as e:
            print(f"⚠️ Warning: Failed to update function usage stats: {e}")

    def validate_function_call(self, name: str, *args, **kwargs) -> List[str]:
        """
        Waliduje wywołanie funkcji.

        Args:
            name: Nazwa funkcji
            *args: Argumenty pozycyjne
            **kwargs: Argumenty nazwane

        Returns:
            Lista błędów walidacji
        """
        errors = []
        
        if name not in self._function_registry:
            errors.append(f"Function '{name}' not found")
            return errors

        func = self._function_registry[name]
        func_info = self.get_function_info(name)
        
        if not func_info:
            return errors

        try:
            # Sprawdź sygnaturę funkcji
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()
        except TypeError as e:
            errors.append(f"Function signature error: {str(e)}")

        return errors

    def get_version(self) -> str:
        """Zwraca wersję Soul"""
        return self.genotype.get("genesis", {}).get("version", "1.0.0")
    
    def get_parent_hash(self) -> Optional[str]:
        """Zwraca hash rodzica (jeśli Soul jest ewolucją)"""
        return self.genotype.get("genesis", {}).get("parent_hash")
    
    def is_evolution_of(self, other_soul: 'Soul') -> bool:
        """Sprawdza czy ta Soul jest ewolucją innej"""
        return self.get_parent_hash() == other_soul.soul_hash
    
    async def get_lineage(self) -> List['Soul']:
        """Zwraca pełną linię ewolucji Soul"""
        lineage = [self]
        current = self
        
        while current.get_parent_hash():
            parent = await Soul.get_by_hash(current.get_parent_hash())
            if parent:
                lineage.append(parent)
                current = parent
            else:
                break
                
        return lineage
    
    @classmethod
    async def get_all_versions(cls, base_name: str) -> List['Soul']:
        """Zwraca wszystkie wersje Soul o danej nazwie"""
        all_souls = await cls.get_all()
        versions = []
        
        for soul in all_souls:
            genesis_name = soul.genotype.get("genesis", {}).get("name")
            if genesis_name and genesis_name.startswith(base_name):
                versions.append(soul)
        
        # Sortuj po wersji
        versions.sort(key=lambda s: s.get_version())
        return versions
    
    def is_compatible_with(self, other_soul: 'Soul') -> bool:
        """Sprawdza kompatybilność między wersjami Soul"""
        # Podstawowa kompatybilność - ten sam typ genesis
        self_genesis = self.genotype.get("genesis", {})
        other_genesis = other_soul.genotype.get("genesis", {})
        
        if self_genesis.get("name") != other_genesis.get("name"):
            return False
            
        # Sprawdź kompatybilność wersji (uproszczona)
        self_version = self.get_version().split(".")
        other_version = other_soul.get_version().split(".")
        
        # Kompatybilne jeśli major version jest taka sama
        return self_version[0] == other_version[0]

    def __repr__(self):
        functions_count = len(self._function_registry)
        version = self.get_version()
        parent = self.get_parent_hash()
        parent_info = f", parent={parent[:8]}..." if parent else ""
        return f"Soul(hash={self.soul_hash[:8] if self.soul_hash else 'None'}..., alias={self.alias}, v={version}, functions={functions_count}{parent_info})"