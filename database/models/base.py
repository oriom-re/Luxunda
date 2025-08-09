from dataclasses import dataclass, field
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
from core.globals import Globals

@dataclass
class Soul:
    """Podstawowa klasa dla wszystkich genotypów w systemie JSONB"""
    soul_hash: str = None
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    alias: str = None
    genotype: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

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
                    "dict": dict, "List[str]": list, "List[float]": list
                }
                expected_type = type_map.get(py_type, str)
                if value is not None and not isinstance(value, expected_type):
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