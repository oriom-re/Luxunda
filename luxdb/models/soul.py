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
        result = await SoulRepository.save(soul)
        if not result.get('success'):
            raise Exception("Failed to create soul")

        return soul

    @classmethod
    async def load_by_hash(cls, hash: str) -> Optional['Soul']:
        """
        Ładuje Soul po global_ulid.

        Args:
            hash: Global ULID soul

        Returns:
            Soul lub None jeśli nie znaleziono
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.load_by_hash(hash)
        return result.get('soul') if result.get('success') else None

    @classmethod
    async def load_by_alias(cls, alias: str) -> Optional['Soul']:
        """
        Ładuje Soul po aliasie.

        Args:
            alias: Alias soul

        Returns:
            Soul lub None jeśli nie znaleziono
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.load_by_alias(alias)
        return result.get('soul') if result.get('success') else None

    @classmethod
    async def load_all(cls) -> List['Soul']:
        """
        Ładuje wszystkie Soul z bazy danych.

        Returns:
            Lista wszystkich Soul
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.load_all()
        souls = result.get('souls', [])
        return [soul for soul in souls if soul is not None]

    @classmethod
    async def load_all_by_alias(cls, alias: str) -> List['Soul']:
        """
        Ładuje wszystkie Soul o danym aliasie.

        Args:
            alias: Alias do wyszukania

        Returns:
            Lista Soul o podanym aliasie
        """
        from ..repository.soul_repository import SoulRepository

        result = await SoulRepository.load_all_by_alias(alias)
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

    def __repr__(self):
        return f"Soul(hash={self.soul_hash[:8]}..., alias={self.alias})"