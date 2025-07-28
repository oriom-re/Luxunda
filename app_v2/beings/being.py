
# from app_v2.beings.new_being import Soul
from dataclasses import dataclass, field, make_dataclass, asdict
import json
from typing import Dict, Any, Optional
from datetime import datetime
from app_v2.database.soul_repository import DynamicRepository, BeingRepository, SoulRepository
import ulid
import hashlib

@dataclass
class Soul:
    """Podstawowa klasa dla wszystkich bytów w systemie"""
    # generuje testowy hash dla bytu
    soul_hash: str = None
    alias: str = None  # Alias dla bytu
    genotype: Dict[str, Any] = None
    created_at: Optional[datetime] = None  # Data zapisu bytu w bazie danych

    @classmethod
    async def create(cls, genotype: Dict[str, Any], alias: str = None) -> 'Soul':
        """Tworzy nowy byt na podstawie genotypu i wartości"""
        soul = cls()
        soul.alias = alias
        soul.genotype = genotype
        soul.soul_hash = hashlib.sha256(json.dumps(genotype, sort_keys=True).encode()).hexdigest()
        result = await SoulRepository.save(soul.alias, soul.genotype, soul.soul_hash)
        if result and result.get('success'):
            metadata = result.get('soul_dict', {})
            return cls.parser(metadata)
        else:
            raise Exception("Failed to create soul")

        return self
    
    @classmethod
    async def load(cls, soul_hash: str) -> 'Soul':
        """Ładuje byt z bazy danych na podstawie jego unikalnego hasha"""
        soul_data = await SoulRepository.load(soul_hash)
        return cls.parser(soul_data)
    
    @classmethod
    async def load_by_alias(cls, alias: str) -> 'Soul':
        """Ładuje byt z bazy danych na podstawie jego aliasu"""
        soul_data = await SoulRepository.load_by_alias(alias)
        return cls.parser(soul_data)

    @classmethod
    async def load_all_by_alias(cls, alias: str) -> list['Soul']:
        """Ładuje wszystkie byty z bazy danych na podstawie aliasu"""
        souls_data = await SoulRepository.load_all_by_alias(alias)
        return [cls.parser(soul_data) for soul_data in souls_data]
    
    @classmethod
    async def load_all(cls) -> list['Soul']:
        """Ładuje wszystkie dusze z bazy danych"""
        souls_data = await SoulRepository.load_all()
        return [cls.parser(soul_data) for soul_data in souls_data]

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

    ulid: str = str(ulid.ulid())  # Unikalny identyfikator bytu
    soul_hash: str = None  # Unikalna reprezentacja genotypu bytu
    created_at: Optional[datetime] = None  # Data zapisu bytu w bazie danych

    @classmethod
    async def create(cls, soul: Soul, data: Dict[str, Any]) -> 'Being':
        """Tworzy nowy byt na podstawie genotypu i wartości"""
        being = cls()
        being._apply_genotype(soul.genotype)
        being.soul_hash = soul.soul_hash
        being.ulid = str(ulid.ulid())
        await being.save(soul, data)
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
        # przygotowanie tabeli z genotypu
        
        data_to_save = {}
        print(self)
        print(soul.genotype)

        if not soul.genotype or not soul.genotype.get("attributes"):
            raise ValueError("Soul genotype must have attributes defined")
        print(f"===================== genotype: {soul.genotype}")
        for key, metadata in soul.genotype.get("attributes", {}).items():
            if not hasattr(self, key):
                raise ValueError(f"Being instance does not have attribute {key}")
            print(f"Saving attribute {key} with value {getattr(self, key)}")
            data_to_save[metadata.get('table_name')] = getattr(self, key)

        if data:
            for key, value in data.items():
                setattr(self, key, value)

        print(f"Saving soul with hash: {soul.soul_hash} and data: {data_to_save}")
        return self
        # return await DynamicRepository.save(soul.soul_hash, soul.genotype, data_to_save)

    def get_attributes(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    async def load(cls, ulid: str) -> 'Being':
        """Ładuje byt z bazy danych na podstawie jego unikalnego ulid"""
        being = await DynamicRepository.load_dynamic_data(ulid)
        return cls.parse(being)

    @classmethod
    async def load_all_by_soul_hash(cls, soul_hash: str) -> list['Being']:
        """Ładuje byt z bazy danych na podstawie jego unikalnego hasha"""
        being_datas = await BeingRepository.load_all_by_hash(soul_hash)
        return [cls.parse(being_data) for being_data in being_datas]
    
    @classmethod
    async def load_all(cls) -> list['Being']:
        """Ładuje wszystkie byty z bazy danych"""
        beings_data = await BeingRepository.load_all()
        return [cls.parse(being_data) for being_data in beings_data]
    
    @classmethod
    async def load_last_by_soul_hash(cls, soul_hash: str) -> 'Being':
        """Ładuje ostatni byt z bazy danych na podstawie jego unikalnego hasha"""
        being_data = await BeingRepository.load_last_by_soul_hash(soul_hash)
        return cls.parse(being_data)

    
    def _apply_genotype(self, genotype: dict):

        fields = []
        type_map = {"str": str, "int": int, "bool": bool, "float": float}
        for name, meta in genotype.get("attributes", {}).items():
            typ_name = meta.get("py_type", "str")
            typ = type_map.get(typ_name, str)
            fields.append((name, typ, field(default=typ())))
        print(f"Creating dynamic class with fields: {fields}")
        DynamicBeing = make_dataclass(
            cls_name="DynamicBeing",
            fields=fields,
            bases=(self.__class__,),
            frozen=False
        )
        print(DynamicBeing)
        self.__class__ = DynamicBeing
        print(self.get_attributes())

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
        instance.ulid = str(ulid.ulid())
        await instance.save(soul)
        return instance
