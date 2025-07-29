
# from app_v2.beings.new_being import Soul
from dataclasses import dataclass, field, make_dataclass, asdict
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from app_v2.database.soul_repository import DynamicRepository, BeingRepository, SoulRepository
import ulid as _ulid
import hashlib
from app_v2.core.globals import Globals

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

    @staticmethod
    def parser(soul_data: Dict[str, Any]) -> 'Soul':
        """Parser dla danych duszy"""
        if not soul_data:
            return None
        soul = Soul()
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

    @classmethod
    async def create(cls, soul: 'Soul', data: Dict[str, Any]) -> 'Being':
        """Tworzy nowy byt na podstawie genotypu i wartości"""

        being = cls(
            ulid=str(_ulid.ulid()),
            soul_hash=soul.soul_hash,
            genotype=soul.genotype
        )

        being._apply_genotype(soul.genotype)

        for key, value in data.items():
            setattr(being, key, value)

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

    @classmethod
    async def from_row(cls, row: Dict[str, Any], genotype: Dict[str, Any]) -> 'Being':
        from app_v2.core.parser_table import parse_py_type
        """Tworzy instancję Being z danych wiersza"""
        being = cls()

        if genotype:
            being._apply_genotype(genotype)

        # Przypisz wszystkie dodatkowe pola dynamicznie
        attributes = genotype.get("attributes", {})
        for key, value in row.items():
            parsed = parse_py_type(key, attributes.get(key, {}))
            _value = parsed["decoder"](value)
            if hasattr(being, key):  # jeśli już istnieje (np. ulid)
                continue
            setattr(being, key, _value)

        return being



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
        
    def get_attributes(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    async def load_by_ulid(cls, ulid: str) -> 'Being':
        """Ładuje byt z bazy danych na podstawie jego unikalnego ulid"""
        result = await BeingRepository.load_by_ulid(ulid)
        return result.get('being', None)

    @classmethod
    async def load_all_by_soul_hash(cls, soul_hash: str) -> list['Being']:
        """Ładuje byt z bazy danych na podstawie jego unikalnego hasha"""
        result = await BeingRepository.load_all_by_soul_hash(soul_hash)
        return [cls.parse(being_data) for being_data in result.get('rows', [])]

    @classmethod
    async def load_all(cls) -> list['Being']:
        """Ładuje wszystkie byty z bazy danych"""
        result = await BeingRepository.load_all()
        return [cls.parse(being_data) for being_data in result.get('rows', [])]

    @classmethod
    async def load_last_by_soul_hash(cls, soul_hash: str) -> 'Being':
        """Ładuje ostatni byt z bazy danych na podstawie jego unikalnego hasha"""
        being_data = await BeingRepository.load_last_by_soul_hash(soul_hash)
        return cls.parse(being_data)

    
    

    @classmethod
    def parse(cls, data: Dict[str, Any]) -> 'Being':
        """Parser dla danych bytu"""
        if not data:
            return None
        being = cls()
        for key, value in data.items():
            setattr(being, key, value)
        return being
    
    def to_dict(self) -> Dict[str, Any] :
        return asdict(self)
    
    def __repr__(self):
        return f"<Being {self.ulid} fields={self.to_dict()}>"

@dataclass
class Message(Being):
    """Klasa reprezentująca wiadomość w systemie"""
    source_uid: str = None  # UID źródła wiadomości
    thread_uid: str = None  # UID wątku wiadomości
    message: Dict[str, Any] = field(default_factory=dict)  # Treść wiadomości

    @classmethod
    async def create(cls, soul:Soul, source_uid: str, thread_uid: str, message: Dict[str, Any]) -> 'Message':
        """Tworzy nową wiadomość"""
        instance = cls()
        instance.source_uid = source_uid
        instance.thread_uid = thread_uid
        instance.message = message
        instance._apply_genotype(soul.genotype)
        instance.soul_hash = soul.soul_hash
        instance.ulid = str(_ulid.ulid())
        await instance.save(soul)
        return instance
    
