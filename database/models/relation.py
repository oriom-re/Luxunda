
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime
import ulid as _ulid
from database.models.base import Soul

@dataclass
class Relation:
    """
    Dedykowana klasa Relation - podobna do Being ale z własną tabelą relations
    Dziedziczy zachowanie Being ale ma dodatkowe pola dla relacji
    """
    
    ulid: str = field(default_factory=lambda: str(_ulid.ulid()))
    soul_hash: Optional[str] = None
    alias: Optional[str] = None
    source_ulid: Optional[str] = None  # ULID źródłowego being
    target_ulid: Optional[str] = None  # ULID docelowego being
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    genotype: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    async def create(cls, soul: Soul, source_ulid: str, target_ulid: str, 
                     data: Dict[str, Any] = None, alias: str = None) -> 'Relation':
        """
        Tworzy nową relację na podstawie Soul i danych połączenia
        
        Args:
            soul: Soul (genotyp) relacji
            source_ulid: ULID źródłowego being
            target_ulid: ULID docelowego being
            data: Dodatkowe dane relacji
            alias: Opcjonalny alias
        
        Returns:
            Nowy obiekt Relation
        """
        from database.soul_repository import RelationRepository
        
        # Walidacja danych względem genotypu
        if data:
            errors = soul.validate_data(data)
            if errors:
                raise ValueError(f"Data validation errors: {', '.join(errors)}")
        
        # Tworzenie Relation
        relation = cls(
            ulid=str(_ulid.ulid()),
            soul_hash=soul.soul_hash,
            genotype=soul.genotype,
            source_ulid=source_ulid,
            target_ulid=target_ulid,
            alias=alias
        )
        
        # Zastosowanie genotypu (dynamiczne pola)
        relation._apply_genotype(soul.genotype)
        
        # Ustawienie danych
        if data:
            for key, value in data.items():
                setattr(relation, key, value)
        
        # Zapis do bazy danych
        await RelationRepository.save(relation)
        
        return relation

    def _apply_genotype(self, genotype: dict):
        """
        Dynamicznie dodaje pola z genotypu do obiektu Relation
        Identyczna funkcjonalność jak w Being
        """
        from dataclasses import make_dataclass, field
        
        fields = []
        type_map = {
            "str": str, 
            "int": int, 
            "bool": bool, 
            "float": float, 
            "dict": dict, 
            "List[str]": list, 
            "List[float]": list
        }

        attributes = genotype.get("attributes", {})
        for name, meta in attributes.items():
            type_name = meta.get("py_type", "str")
            py_type = type_map.get(type_name, str)
            fields.append((name, py_type, field(default=None)))

        if fields:
            DynamicRelation = make_dataclass(
                cls_name="DynamicRelation",
                fields=fields,
                bases=(self.__class__,),
                frozen=False
            )
            self.__class__ = DynamicRelation

    @classmethod
    async def load_by_ulid(cls, ulid: str) -> Optional['Relation']:
        """Ładuje relację po ULID"""
        from database.soul_repository import RelationRepository
        
        result = await RelationRepository.load_by_ulid(ulid)
        return result.get('relation') if result.get('success') else None

    @classmethod
    async def load_all_by_soul_hash(cls, soul_hash: str) -> list['Relation']:
        """Ładuje wszystkie relacje dla danego Soul"""
        from database.soul_repository import RelationRepository
        
        result = await RelationRepository.load_all_by_soul_hash(soul_hash)
        relations = result.get('relations', [])
        return [relation for relation in relations if relation is not None]

    @classmethod
    async def load_all(cls) -> list['Relation']:
        """Ładuje wszystkie relacje z bazy danych"""
        from database.soul_repository import RelationRepository
        
        result = await RelationRepository.load_all()
        relations = result.get('relations', [])
        return [relation for relation in relations if relation is not None]

    @classmethod
    async def load_by_being(cls, being_ulid: str) -> list['Relation']:
        """Ładuje wszystkie relacje dla danego being (jako source lub target)"""
        from database.soul_repository import RelationRepository
        
        result = await RelationRepository.load_by_being(being_ulid)
        relations = result.get('relations', [])
        return [relation for relation in relations if relation is not None]

    async def save(self) -> bool:
        """Zapisuje zmiany w Relation do bazy danych"""
        from database.soul_repository import RelationRepository, DynamicRepository
        
        # Zapisz podstawowe informacje Relation
        result = await RelationRepository.save(self)
        if not result.get('success'):
            return False
            
        # Zapisz dynamiczne atrybuty do tabel attr_*
        if self.genotype:
            await DynamicRepository.insert_data_transaction(self, self.genotype, table_prefix="relation_")
            
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje Relation do słownika"""
        from dataclasses import asdict
        return asdict(self)

    def __repr__(self):
        return f"Relation(ulid={self.ulid[:8]}..., {self.source_ulid[:8] if self.source_ulid else 'None'}... -> {self.target_ulid[:8] if self.target_ulid else 'None'}...)"
