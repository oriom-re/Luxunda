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
    genes: Dict[str, Callable] = field(default_factory=dict)

    @classmethod
    async def create(cls, soul: 'Soul', data: Dict[str, Any], limit: int) -> 'Being':
        """Tworzy nowy byt na podstawie genotypu i wartości"""

        being = cls(
            ulid=str(_ulid.ulid()),
            soul_hash=soul.soul_hash,
            genotype=soul.genotype
        )

        being._apply_genotype(soul.genotype)

        for key, value in data.items():
            setattr(being, key, value)
        beings = await BeingRepository.load_all_by_soul_hash(soul.soul_hash)
        if limit and len(beings) >= limit:
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

    def get_attributes(self) -> Dict[str, Any]:
        return asdict(self)

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



    # === RELATION METHODS ===
    
    async def add_tag(self, target_uid: str, tag_name: str, context: Dict[str, Any] = None):
        """Dodaje relację tagową do innego bytu"""
        from services.relation_manager import relation_manager
        return await relation_manager.create_smart_tag(self.uid, target_uid, tag_name, context)
    
    async def create_relation(self, target_uid: str, relation_name: str, 
                            perspective: str, bidirectional: bool = False,
                            context: Dict[str, Any] = None):
        """Tworzy relację kierunkową z innym bytem"""
        from services.relation_manager import relation_manager
        return await relation_manager.create_smart_directional(
            self.uid, target_uid, relation_name, perspective, context, bidirectional
        )
    
    async def get_relations(self, relation_type: str = None) -> List['Relationship']:
        """Pobiera wszystkie relacje bytu"""
        from database.models.relationship import Relationship
        # TODO: Implementacja pobierania z bazy
        return []
    
    async def learn_from_interaction(self, other_uid: str, interaction_type: str, 
                                   success: bool, context: Dict[str, Any] = None):
        """Uczy się z interakcji z innym bytem"""
        from services.relation_manager import relation_manager
        await relation_manager.learn_from_interaction(
            self.uid, other_uid, interaction_type, success, context
        )
    
    async def get_relation_suggestions(self, target_uid: str, 
                                     context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Otrzymuje sugestie relacji z innym bytem"""
        from services.relation_manager import relation_manager
        return await relation_manager.suggest_relations(self.uid, target_uid, context)
    
    async def optimize_relations(self) -> Dict[str, Any]:
        """Optymalizuje relacje bytu"""
        from services.relation_manager import relation_manager
        return await relation_manager.optimize_relations(self.uid)

    @classmethod
    async def load_all(cls) -> list['Being']:
        """Ładuje wszystkie byty z bazy danych"""
        result = await BeingRepository.load_all()
        if result:
            return result.get('beings', [])
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