# from app_v2.beings.new_being import Soul
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
    """Podstawowa klasa dla wszystkich bytów w systemie"""
    # generuje testowy hash dla bytu
    soul_hash: str = None
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    alias: str = None  # Alias dla bytu
    genotype: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None  # Data zapisu bytu w bazie danych

    @classmethod
    async def create(cls, genotype: Dict[str, Any], alias: str = None) -> 'Soul':
        """Tworzy nowy byt na podstawie genotypu i wartości"""
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
        """Ładuje byt z bazy danych na podstawie jego unikalnego hasha"""
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
        """Ładuje wszystkie byty z bazy danych"""
        await SoulRepository.load(self)


    @classmethod
    async def load_by_alias(cls, alias: str) -> 'Soul':
        """Ładuje byt z bazy danych na podstawie jego aliasu"""
        result = await SoulRepository.load_by_alias(alias)
        if result:
            return result.get('soul', None)

    @classmethod
    async def load_all_by_alias(cls, alias: str) -> list['Soul']:
        """Ładuje wszystkie byty z bazy danych na podstawie aliasu"""
        result = await SoulRepository.load_all_by_alias(alias)
        if result:
            return result.get('souls', [])

    @classmethod
    async def load_all(cls) -> list['Soul']:
        """Ładuje wszystkie dusze z bazy danych"""
        result = await SoulRepository.load_all()
        if result:
            return result.get('souls', [])
        return []

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
        """Parser dla danych duszy"""
        if not soul_data:
            return None
        soul = cls()
        for key, value in soul_data.items():
            setattr(soul, key, value)
        return soul

@dataclass
class Being:
    """Podstawowa klasa dla wszystkich bytów w systemie"""

    ulid: str = field(default_factory=lambda: str(_ulid.ulid()))
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    soul_hash: Optional[str] = None
    alias: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    genotype: Dict[str, Any] = field(default_factory=dict)
    genes: Dict[str, Callable] = field(default_factory=dict)

    @classmethod
    async def create(cls, soul: 'Soul', data: Dict[str, Any], limit: int = None) -> 'Being':
        """Tworzy nowy byt na podstawie genotypu i wartości"""

        being = cls(
            ulid=str(_ulid.ulid()),
            soul_hash=soul.soul_hash,
            genotype=soul.genotype
        )

        being._apply_genotype(soul.genotype)

        for key, value in data.items():
            setattr(being, key, value)

        # Sprawdź limit tylko jeśli został podany
        if limit is not None:
            beings = await BeingRepository.load_all_by_soul_hash(soul.soul_hash)
            if len(beings) >= limit:
                raise ValueError(f"Limit of {limit} beings reached for soul {soul.soul_hash}")

        # Load genes from genotype
        being.genes = soul.genotype.get("genes", {})

        await being.save(soul, data)
        return being

    def _apply_genotype(self, genotype: dict):
        """Tworzy dynamiczną wersję bytu z polami z genotypu"""
        fields = []
        type_map = {"str": str, "int": int, "bool": bool, "float": float, "dict": dict, "List[str]": list, "List[float]": list}

        attributes = genotype.get("attributes", {})
        for name, meta in attributes.items():
            typ_name = meta.get("py_type", "str")
            typ = type_map.get(typ_name, str)
            fields.append((name, typ, field(default=None)))

        if fields:  # tylko jeśli są jakieś pola do dodania
            DynamicBeing = make_dataclass(
                cls_name="DynamicBeing",
                fields=fields,
                bases=(self.__class__,),
                frozen=False
            )

            self.__class__ = DynamicBeing

    async def save(self, soul: Soul, data: Dict[str, Any]=None) -> 'Being':
        """Zapisuje byt do bazy danych

            przykład genotypu:
            {
                "attributes": {
                    "attribute_name": {
                        "table_name": "_text",
                        "py_type": "str"
                    }
                }
                "genes": {
                    "gene_name": "path.to.gene_function"
                }
            }

        """

        data_to_save = {}
        if not soul.genotype or not soul.genotype.get("attributes"):
            raise ValueError("Soul genotype must have attributes defined")
        for key, metadata in soul.genotype.get("attributes", {}).items():
            if not hasattr(self, key):
                raise ValueError(f"Being instance does not have attribute {key}")
            data_to_save[metadata.get('table_name')] = getattr(self, key)

        if data:
            for key, value in data.items():
                setattr(self, key, value)

        print(f"Saving soul with hash: {soul.soul_hash}")
        await DynamicRepository.insert_data_transaction(self, soul.genotype)
        return self

    async def get_attributes(self):
        """Zwraca wszystkie atrybuty tego bytu z bazy danych"""
        attributes = {}

        try:
            from database.postgre_db import Postgre_db
            db_pool = await Postgre_db.get_db_pool()

            if db_pool:
                async with db_pool.acquire() as conn:
                    # Sprawdź wszystkie tabele z atrybutami - używamy prawidłowych nazw kolumn
                    for table_suffix in ['_text', '_int', '_float', '_boolean', '_jsonb']:
                        table_name = f"attr{table_suffix}"
                        try:
                            query = f"""
                                SELECT key, value
                                FROM {table_name}
                                WHERE being_ulid = $1
                            """
                            rows = await conn.fetch(query, self.ulid)
                            for row in rows:
                                attributes[row['key']] = row['value']
                        except Exception as e:
                            # Tabela może nie istnieć lub mieć inną strukturę
                            print(f"⚠️ Błąd czytania tabeli {table_name}: {e}")
                            continue

        except Exception as e:
            print(f"❌ Błąd pobierania atrybutów dla {self.ulid}: {e}")

        return attributes

    @classmethod
    async def load_by_ulid(cls, ulid: str) -> 'Being':
        """Ładuje byt z bazy danych na podstawie jego unikalnego ulid"""
        result = await BeingRepository.load_by_ulid(ulid)
        if result:
            return result.get('beings', [])
        return []

    @classmethod
    async def load_all_by_soul_hash(cls, soul_hash: str) -> list['Being']:
        """Ładuje byt z bazy danych na podstawie jego unikalnego hasha"""
        result = await BeingRepository.load_all_by_soul_hash(soul_hash)
        if result:
            return result.get('beings', [])

    @classmethod
    async def load_all(cls) -> List['Being']:
        """Ładuje wszystkie beings z bazy danych"""
        result = await BeingRepository.load_all()
        if isinstance(result, dict) and result.get("success") and result.get("beings"):
            return result["beings"]
        return []

    @classmethod
    async def load_last_by_soul_hash(cls, soul_hash: str) -> 'Being':
        """Ładuje ostatni byt z bazy danych na podstawie jego unikalnego hasha"""
        result = await BeingRepository.load_last_by_soul_hash(soul_hash)
        if result:
            return result.get('beings', [])
        return []

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
            # Pobierz soul na podstawie hash
            result['_soul'] = {
                'soul_hash': self.soul_hash,
                'genesis': self.genotype.get('genesis', {}),
                'alias': self.alias,
                'genotype': self.genotype
            }
        
        return result

    def __repr__(self):
        return f"<Being {self.ulid} fields={self.to_dict()}>"

@dataclass
class Message(Being):
    """Klasa reprezentująca wiadomość w systemie"""
    source_uid: str = None  # UID źródła wiadomości
    thread_uid: str = None  # UID wątku wiadomości
    message: Dict[str, Any] = field(default_factory=dict)  # Treść wiadomości

    @classmethod
    async def create(cls, soul:Soul, source_uid: str, thread_uid: str, message: Dict[str, Any], limit: int = None) -> 'Message':
        """Tworzy nową wiadomość"""
        instance = cls()
        instance.source_uid = source_uid
        instance.thread_uid = thread_uid
        instance.message = message
        instance._apply_genotype(soul.genotype)
        instance.soul_hash = soul.soul_hash
        instance.ulid = str(_ulid.ulid())

        # Sprawdź limit tylko jeśli został podany
        if limit is not None:
            beings = await BeingRepository.load_all_by_soul_hash(soul.soul_hash)
            if len(beings) >= limit:
                raise ValueError(f"Limit of {limit} beings reached for soul {soul.soul_hash}")

        await instance.save(soul)
        return instance