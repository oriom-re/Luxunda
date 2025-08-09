
from dataclasses import dataclass, field, make_dataclass, asdict
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from database.soul_repository import DynamicRepository, BeingRepository, SoulRepository
import ulid as _ulid
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
        result = await SoulRepository.load_by_hash(hash)
        if result:
            return result.get('soul', None)
        return None

    @classmethod
    async def from_row(cls, row: Dict[str, Any]) -> 'Soul':
        """Tworzy instancję Soul z danych wiersza"""
        soul = cls()
        soul.alias = row.get('alias')
        soul.soul_hash = row.get('soul_hash')
        soul.genotype = json.loads(row.get('genotype', '{}'))
        soul.created_at = row.get('created_at')
        soul.global_ulid = row.get('global_ulid')
        return soul

    async def load(self) -> list['Soul']:
        """Ładuje wszystkie genotypy z bazy danych"""
        await SoulRepository.load(self)

    @classmethod
    async def load_by_alias(cls, alias: str) -> 'Soul':
        """Ładuje genotyp z bazy danych na podstawie jego aliasu"""
        result = await SoulRepository.load_by_alias(alias)
        if result:
            return result.get('soul', None)

    @classmethod
    async def load_all_by_alias(cls, alias: str) -> list['Soul']:
        """Ładuje wszystkie genotypy z bazy danych na podstawie aliasu"""
        result = await SoulRepository.load_all_by_alias(alias)
        if result:
            return result.get('souls', [])

    @classmethod
    async def load_all(cls) -> list['Soul']:
        """Ładuje wszystkie genotypy z bazy danych"""
        result = await SoulRepository.load_all()
        if result:
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

@dataclass
class Being:
    """Podstawowa klasa dla wszystkich bytów w systemie JSONB"""

    ulid: str = field(default_factory=lambda: str(_ulid.ulid()))
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    soul_hash: Optional[str] = None
    alias: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)  # JSONB data
    vector_embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    genotype: Dict[str, Any] = field(default_factory=dict)
    genes: Dict[str, Callable] = field(default_factory=dict)

    @classmethod
    async def create(cls, soul: 'Soul', data: Dict[str, Any], limit: int = None) -> 'Being':
        """Tworzy nowy byt na podstawie genotypu i danych w podejściu JSONB"""
        
        # Walidacja danych względem genotypu
        errors = soul.validate_data(data)
        if errors:
            raise ValueError(f"Data validation errors: {', '.join(errors)}")

        being = cls(
            ulid=str(_ulid.ulid()),
            soul_hash=soul.soul_hash,
            genotype=soul.genotype,
            data=data  # Wszystkie dane w JSONB
        )

        # Sprawdź limit tylko jeśli został podany
        if limit is not None:
            beings = await BeingRepository.load_all_by_soul_hash(soul.soul_hash)
            if len(beings) >= limit:
                raise ValueError(f"Limit of {limit} beings reached for soul {soul.soul_hash}")

        # Load genes from genotype
        being.genes = soul.genotype.get("genes", {})

        await being.save()
        return being

    async def save(self) -> 'Being':
        """Zapisuje byt do bazy danych w podejściu JSONB"""
        await BeingRepository.save_jsonb(self)
        return self

    async def update_data(self, new_data: Dict[str, Any]) -> None:
        """Aktualizuje dane JSONB"""
        self.data.update(new_data)
        await self.save()

    async def get_data(self, key: str = None) -> Any:
        """Pobiera dane z JSONB"""
        if key:
            return self.data.get(key)
        return self.data

    async def set_vector_embedding(self, embedding: List[float]) -> None:
        """Ustawia embedding wektorowy"""
        self.vector_embedding = embedding
        await BeingRepository.update_vector(self.ulid, embedding)

    async def find_similar(self, limit: int = 10, threshold: float = 0.8) -> List['Being']:
        """Znajdź podobne byty na podstawie embeddingu wektorowego"""
        if not self.vector_embedding:
            return []
        return await BeingRepository.find_similar_beings(self.vector_embedding, limit, threshold)

    @classmethod
    async def load_by_ulid(cls, ulid: str) -> 'Being':
        """Ładuje byt z bazy danych na podstawie jego unikalnego ulid"""
        result = await BeingRepository.load_by_ulid(ulid)
        if result and result.get('success'):
            return result.get('being')
        return None

    @classmethod
    async def load_all_by_soul_hash(cls, soul_hash: str) -> list['Being']:
        """Ładuje wszystkie byty dla danego genotypu"""
        result = await BeingRepository.load_all_by_soul_hash(soul_hash)
        beings = result.get('beings', [])
        return [being for being in beings if being is not None]

    @classmethod
    async def load_all(cls) -> List['Being']:
        """Ładuje wszystkie byty z bazy danych"""
        result = await BeingRepository.load_all()
        beings = result.get('beings', [])
        return [being for being in beings if being is not None]

    @classmethod
    async def search_by_data(cls, query: Dict[str, Any], soul_hash: str = None) -> List['Being']:
        """Wyszukuje byty na podstawie danych JSONB"""
        return await BeingRepository.search_by_jsonb_data(query, soul_hash)

    async def execute(self, gene_name: str, *args, **kwargs):
        """Wykonuje gen na bycie"""
        if gene_name not in self.genes:
            raise ValueError(f"Gene {gene_name} not found in being")

        gene_path = self.genes[gene_name]
        try:
            module_name, function_name = gene_path.rsplit(".", 1)
            module = __import__(module_name, fromlist=[function_name])
            gene_function = getattr(module, function_name)
            return await gene_function(self, *args, **kwargs)
        except Exception as e:
            raise Exception(f"Failed to execute gene {gene_name}: {e}")

    @classmethod
    def parse(cls, data: Dict[str, Any]) -> 'Being':
        """Parser dla danych bytu"""
        if not data:
            return None
        being = cls()
        for key, value in data.items():
            setattr(being, key, value)
        return being

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje Being do słownika z uwzględnieniem _soul dla frontend"""
        result = asdict(self)
        
        # Dodaj pole _soul dla kompatybilności z frontendem
        if hasattr(self, 'soul_hash') and self.soul_hash:
            result['_soul'] = {
                'soul_hash': self.soul_hash,
                'genesis': self.genotype.get('genesis', {}),
                'alias': self.alias,
                'genotype': self.genotype
            }
        
        return result

    # Discord integration methods
    async def discord_report_error(self, error_message: str):
        """Zgłasza błąd przez Discord"""
        from luxdb.core.discord_being import being_discord_report_error
        return await being_discord_report_error(self, error_message)
    
    async def discord_suggest(self, suggestion: str):
        """Wysyła sugestię przez Discord"""
        from luxdb.core.discord_being import being_discord_suggest
        return await being_discord_suggest(self, suggestion)
    
    async def discord_revolution_talk(self, message_content: str):
        """Rozmawia o rewolucji przez Discord"""
        from luxdb.core.discord_being import being_discord_revolution_talk
        return await being_discord_revolution_talk(self, message_content)
    
    async def discord_status(self, status_message: str):
        """Wysyła status przez Discord"""
        from luxdb.core.discord_being import being_discord_status
        return await being_discord_status(self, status_message)

    def __repr__(self):
        return f"<Being {self.ulid} data_keys={list(self.data.keys()) if self.data else []}>"

@dataclass
class Message(Being):
    """Klasa reprezentująca wiadomość w systemie JSONB"""
    source_uid: str = None
    thread_uid: str = None
    message: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    async def create(cls, soul: Soul, source_uid: str, thread_uid: str, message: Dict[str, Any], limit: int = None) -> 'Message':
        """Tworzy nową wiadomość w systemie JSONB"""
        message_data = {
            "source_uid": source_uid,
            "thread_uid": thread_uid,
            "message": message
        }
        
        instance = await super().create(soul, message_data, limit)
        instance.source_uid = source_uid
        instance.thread_uid = thread_uid
        instance.message = message
        return instance
