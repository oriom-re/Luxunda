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
        Tworzy Soul na podstawie genotypu. 
        Jeśli Soul o tym samym hash już istnieje - zwraca istniejący.
        To zapewnia unikalność i bezpieczeństwo.

        Args:
            genotype: Definicja struktury danych (słownik)
            alias: Opcjonalny alias dla łatwego odszukiwania

        Returns:
            Soul (nowy lub istniejący)
        """
        from ..utils.validators import validate_genotype
        from ..repository.soul_repository import SoulRepository

        # Walidacja genotypu
        validate_genotype(genotype)

        # Generuj hash z genotypu - to jest unikalny kod genetyczny
        soul_hash = hashlib.sha256(
            json.dumps(genotype, sort_keys=True).encode()
        ).hexdigest()

        # Sprawdź czy Soul o tym hash już istnieje
        existing_soul = await cls.get_by_hash(soul_hash)
        if existing_soul:
            # Aktualizuj alias jeśli podano nowy
            if alias and existing_soul.alias != alias:
                existing_soul.alias = alias
                await SoulRepository.set(existing_soul)
            return existing_soul

        # Utwórz nową Soul
        soul = cls()
        soul.alias = alias
        soul.genotype = genotype
        soul.soul_hash = soul_hash
        soul.created_at = datetime.now()

        # Zapis do bazy danych
        result = await SoulRepository.set(soul)
        if not result.get('success'):
            raise Exception("Failed to create soul")

        return soul

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
    async def get_by_hash(cls, soul_hash: str) -> Optional['Soul']:
        """
        Ładuje Soul po jego hash (kodzie genetycznym).

        Args:
            soul_hash: Hash wygenerowany z genotypu - unikalny kod genetyczny

        Returns:
            Soul lub None jeśli nie znaleziono
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.get_soul_by_hash(soul_hash)
        return result.get('soul') if result.get('success') else None

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
        return result.get('soul') if result.get('success') else None

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
            value = data.get(attr_name)

            # Sprawdź wymagane pola
            if value is None and not attr_config.get("default"):
                errors.append(f"Missing required attribute: {attr_name}")
                continue

            # Sprawdź typ
            if value is not None:
                if py_type == "str" and not isinstance(value, str):
                    errors.append(f"Attribute {attr_name} must be string")
                elif py_type == "int" and not isinstance(value, int):
                    errors.append(f"Attribute {attr_name} must be integer")
                elif py_type == "float" and not isinstance(value, (int, float)):
                    errors.append(f"Attribute {attr_name} must be float")
                elif py_type == "bool" and not isinstance(value, bool):
                    errors.append(f"Attribute {attr_name} must be boolean")
                elif py_type == "dict" and not isinstance(value, dict):
                    errors.append(f"Attribute {attr_name} must be dict")
                elif py_type.startswith("List[") and not isinstance(value, list):
                    errors.append(f"Attribute {attr_name} must be list")

        return errors

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

    def get_functions_count(self) -> int:
        """Zwraca liczbę zarejestrowanych funkcji"""
        return len(self._function_registry)

    def get_function_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Pobiera informacje o funkcji"""
        if name in self.genotype.get("functions", {}):
            return self.genotype["functions"][name]
        return None

    def has_module_source(self) -> bool:
        """Sprawdza czy Soul zawiera kod źródłowy modułu"""
        return "module_source" in self.genotype and self.genotype["module_source"] is not None

    def get_module_source(self) -> Optional[str]:
        """Zwraca kod źródłowy modułu"""
        return self.genotype.get("module_source")

    def load_module_dynamically(self) -> Optional[Any]:
        """Ładuje moduł dynamicznie z kodu źródłowego"""
        if not self.has_module_source():
            return None
        
        try:
            import types
            import sys
            
            # Utwórz nowy moduł
            module_name = f"dynamic_soul_{self.soul_hash[:8]}"
            module = types.ModuleType(module_name)
            
            # Wykonaj kod w kontekście modułu
            exec(self.get_module_source(), module.__dict__)
            
            # Dodaj do sys.modules dla możliwości importu
            sys.modules[module_name] = module
            
            return module
            
        except Exception as e:
            print(f"Error loading dynamic module: {e}")
            return None

    def extract_functions_from_module(self, module: Any) -> Dict[str, Callable]:
        """Wyciąga funkcje z załadowanego modułu"""
        functions = {}
        
        if not module:
            return functions
            
        # Znajdź wszystkie callable obiekty w module
        for attr_name in dir(module):
            if not attr_name.startswith('_'):  # Pomijaj prywatne
                attr = getattr(module, attr_name)
                if callable(attr):
                    functions[attr_name] = attr
                    
        return functions

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
        Tworzy specjalizowany Soul dla pojedynczej funkcji z niezmiennym genotypem.

        Args:
            name: Nazwa funkcji
            func: Funkcja
            description: Opis funkcji
            alias: Alias dla soul
            version: Wersja genotypu

        Returns:
            Nowy Soul z funkcją
        """
        # Genotyp dla funkcji - KOMPLETNY i NIEZMIENNY
        function_genotype = {
            "genesis": {
                "name": alias or f"function_{name}",
                "type": "function_soul", 
                "version": version,
                "description": description or f"Soul for function {name}",
                "immutable": True,
                "created_at": datetime.now().isoformat()
            },
            "attributes": {
                "function_name": {"py_type": "str", "default": name},
                "last_execution": {"py_type": "str"},
                "execution_count": {"py_type": "int", "default": 0}
            },
            "functions": {
                name: {
                    "py_type": "function",
                    "description": description or f"Main function {name}",
                    "is_primary": True,
                    "signature": cls._get_function_signature_static(func),
                    "is_async": asyncio.iscoroutinefunction(func)
                }
            }
        }

        # Utwórz Soul
        soul = await cls.create(function_genotype, alias or f"function_{name}")
        
        # Załaduj funkcję do rejestru (bez modyfikacji genotypu)
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