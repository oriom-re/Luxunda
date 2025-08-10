"""
Database Models Base Module
===========================

Base classes and utilities for database models.
"""

import json
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

# Import unified serializer
from luxdb.utils.serializer import JSONBSerializer, JsonbSerializer

# Import globals
try:
    from core.globals import Globals
except ImportError:
    class Globals:
        GLOBAL_ULID = "01K29SYSTEM"

# Re-export for compatibility
__all__ = ['JSONBSerializer', 'JsonbSerializer', 'Soul']


@dataclass
class Soul:
    """Podstawowa klasa dla wszystkich genotypów w systemie JSONB"""
    soul_hash: str = None
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    alias: str = None
    genotype: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    # Dodanie metody do pobierania Soul z bazy danych (załóżmy, że taka istnieje)
    @classmethod
    async def get_soul_by_hash(cls, soul_hash: str) -> 'Soul':
        """Ładuje definicję Soul z bazy danych na podstawie jego unikalnego hasha"""
        # To jest placeholder, w rzeczywistości tutaj byłoby zapytanie do repozytorium
        # Zwracamy przykładowy obiekt Soul dla demonstracji
        if soul_hash == "example_hash_123":
             return Soul(
                soul_hash="example_hash_123",
                alias="user_profile",
                genotype={
                    "attributes": {
                        "name": {"py_type": "str", "required": True},
                        "age": {"py_type": "int", "required": False},
                        "registered_at": {"py_type": "datetime", "required": False}
                    }
                }
            )
        return None


    @classmethod
    async def create(cls, genotype: Dict[str, Any], alias: str = None) -> 'Soul':
        """Tworzy nowy genotyp na podstawie definicji"""
        from luxdb.repository.soul_repository import SoulRepository
        soul = cls()
        soul.alias = alias
        soul.genotype = genotype
        soul.soul_hash = hashlib.sha256(json.dumps(genotype, sort_keys=True).encode()).hexdigest()
        result = await SoulRepository.save(soul)
        if result and result.get('success'):
            return soul
        else:
            raise Exception("Failed to create soul")

    @classmethod
    async def load_by_hash(cls, hash: str) -> 'Soul':
        """Ładuje genotyp z bazy danych na podstawie jego unikalnego hasha"""
        from luxdb.repository.soul_repository import SoulRepository
        result = await SoulRepository.get_soul_by_hash(hash)
        return result

    @classmethod
    async def load_by_alias(cls, alias: str) -> 'Soul':
        """Ładuje genotyp z bazy danych na podstawie jego aliasu"""
        from luxdb.repository.soul_repository import SoulRepository
        result = await SoulRepository.load_by_alias(alias)
        if result:
            return result.get('soul', None)

    @classmethod
    async def load_all_by_alias(cls, alias: str) -> list['Soul']:
        """Ładuje wszystkie genotypy z bazy danych na podstawie aliasu"""
        from luxdb.repository.soul_repository import SoulRepository
        result = await SoulRepository.get_all_souls()
        if result and result.get('success'):
            souls = result.get('souls', [])
            return [soul for soul in souls if soul.alias == alias]
        return []

    @classmethod
    async def load_all(cls) -> list['Soul']:
        """Ładuje wszystkie genotypy z bazy danych"""
        from luxdb.repository.soul_repository import SoulRepository
        result = await SoulRepository.get_all_souls()
        if result and result.get('success'):
            return result.get('souls', [])
        return []

    def validate_data(self, data: Dict[str, Any]) -> List[str]:
        """Waliduje dane względem genotypu"""
        errors = []
        attributes = self.genotype.get("attributes", {})

        for attr_name, attr_meta in attributes.items():
            required = attr_meta.get("required", False)
            py_type = attr_meta.get("py_type", "str")

            if required and attr_name not in data:
                errors.append(f"Required attribute '{attr_name}' is missing")

            if attr_name in data:
                value = data[attr_name]
                # Podstawowa walidacja typów
                type_map = {
                    "str": str, "int": int, "bool": bool, "float": float,
                    "dict": dict, "list": list, "List[str]": list, "List[float]": list, "datetime": datetime
                }
                expected_type = type_map.get(py_type, str)
                if value is not None and not isinstance(value, expected_type):
                    # Specjalna obsługa dla typów listowych, jeśli py_type to np. List[str]
                    if py_type.startswith("List[") and isinstance(value, list):
                        # Tutaj można dodać walidację elementów listy, jeśli jest potrzebna
                        pass # Na razie tylko sprawdzamy, czy to lista
                    else:
                        errors.append(f"Attribute '{attr_name}' should be of type {py_type}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje Soul do słownika"""
        return {
            'soul_hash': self.soul_hash,
            'global_ulid': self.global_ulid,
            'alias': self.alias,
            'genotype': self.genotype,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def parser(cls, soul_data: Dict[str, Any]) -> 'Soul':
        """Parser dla danych genotypu"""
        if not soul_data:
            return None
        soul = cls()
        for key, value in soul_data.items():
            setattr(soul, key, value)
        return soul


class Being:
    def __init__(self, data: Dict[str, Any] = None, _soul_cache: Soul = None):
        self.data = data or {}
        self._soul_cache = _soul_cache # Cache dla Soul powiązanego z tym Being

    async def get_soul(self) -> Optional[Soul]:
        """Pobiera powiązany obiekt Soul, jeśli jest dostępny w cache lub przez soul_hash"""
        if self._soul_cache:
            return self._soul_cache
        # W tym miejscu można by pobrać Soul z bazy danych na podstawie np. soul_hash z self.data
        # Załóżmy, że self.data zawiera 'soul_hash'
        if 'soul_hash' in self.data:
            self._soul_cache = await Soul.get_soul_by_hash(self.data['soul_hash'])
        return self._soul_cache

    def serialize_data(self) -> Dict[str, Any]:
        """Serializuje dane Being zgodnie ze schematem Soul"""
        if hasattr(self, '_soul_cache') and self._soul_cache:
            return JSONBSerializer.serialize_being_data(self.data, self._soul_cache)
        return self.data

    def deserialize_data(self) -> Dict[str, Any]:
        """Deserializuje dane Being zgodnie ze schematem Soul"""
        if hasattr(self, '_soul_cache') and self._soul_cache:
            return JSONBSerializer.deserialize_being_data(self.data, self._soul_cache)
        return self.data

    async def validate_and_serialize_data(self, new_data: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
        """Waliduje i serializuje nowe dane"""
        soul = await self.get_soul()
        if soul:
            return JSONBSerializer.validate_and_serialize(new_data, soul)
        return new_data, []

    @classmethod
    async def create(cls, soul_hash: str, alias: str = None, data: Dict[str, Any] = None, force_new: bool = False) -> 'Being':
        """Tworzy nowy obiekt Being, walidując i serializując dane"""
        being = cls()
        # Walidacja i serializacja danych względem soul
        soul = await Soul.get_soul_by_hash(soul_hash) # Używamy metody z klasy Soul
        if soul and data:
            serialized_data, validation_errors = JSONBSerializer.validate_and_serialize(data, soul)
            if validation_errors:
                print(f"⚠️ Błędy walidacji danych: {validation_errors}")
                # Możemy zdecydować czy kontynuować czy przerwać
            being.data = serialized_data
            being._soul_cache = soul  # Cache dla późniejszego użycia
        else:
            being.data = data or {}

        # Ustawienie aliasu, jeśli podano
        if alias:
            being.alias = alias # Zakładając, że Being ma atrybuty alias

        return being

    async def update_data(self, new_data: Dict[str, Any]) -> bool:
        """Aktualizuje dane Being w bazie danych"""
        try:
            # Walidacja i serializacja danych względem soul
            soul = await self.get_soul()
            if soul:
                # Połącz istniejące dane z nowymi
                combined_data = {**self.data, **new_data}
                serialized_data, validation_errors = JSONBSerializer.validate_and_serialize(combined_data, soul)

                if validation_errors:
                    print(f"⚠️ Błędy walidacji danych: {validation_errors}")
                    return False

                self.data = serialized_data
            else:
                self.data.update(new_data)

            # Tutaj powinien być kod do zapisania zaktualizowanych danych being w bazie danych
            # Np. await BeingRepository.save(self)
            print("Dane Being zaktualizowane.")
            return True
        except Exception as e:
            print(f"Błąd podczas aktualizacji danych Being: {e}")
            return False

    # Dodajemy inne metody związane z Being, jeśli są potrzebne, np. do zapisywania w bazie
    # async def save(self):
    #     pass