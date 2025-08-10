"""
Model Soul (Dusza/Genotyp) dla LuxDB.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import ulid

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

        # Zapis do bazy danych
        result = await SoulRepository.set(soul)
        if not result.get('success'):
            raise Exception("Failed to create soul")

        # Zwróć zgodnie z formatem genetycznym
        return await cls.set(genotype, alias)

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

    def __repr__(self):
        return f"Soul(hash={self.soul_hash[:8]}..., alias={self.alias})"