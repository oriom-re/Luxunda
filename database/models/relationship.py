
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import ulid as _ulid
import hashlib
import json
from core.globals import Globals

@dataclass
class Relationship:
    """Zaawansowany system relacji w LuxDB - byty z genotypami"""
    
    ulid: str = field(default_factory=lambda: str(_ulid.ulid()))
    hash_code: str = ""  # Unikalny hash dla relacji
    
    # Podstawowe właściwości relacji
    source_ulid: str = ""
    target_ulid: str = ""
    relation_type: str = ""  # "tag", "directional", "bidirectional"
    
    # Genotyp relacji - każda relacja jest bytem
    genesis: Dict[str, Any] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    # Specjalne właściwości
    description: str = ""
    embedding: List[float] = field(default_factory=list)
    perspective: Optional[str] = None  # Dla relacji kierunkowych
    tags: List[str] = field(default_factory=list)
    
    # Metadane
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    usage_count: int = 0  # System śledzi jak często używana
    success_rate: float = 0.0  # Skuteczność relacji
    
    def __post_init__(self):
        """Automatycznie generuje hash i ustawia daty"""
        if not self.created_at:
            self.created_at = datetime.now()
        
        if not self.hash_code:
            self.hash_code = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generuje unikalny hash dla relacji"""
        hash_data = {
            "source": self.source_ulid,
            "target": self.target_ulid,
            "type": self.relation_type,
            "description": self.description,
            "perspective": self.perspective,
            "genesis": self.genesis
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()[:16]
    
    @classmethod
    async def create_tag_relation(cls, source_uid: str, target_uid: str, 
                                 tag_name: str, description: str = "", 
                                 embedding: List[float] = None) -> 'Relationship':
        """Tworzy relację jednokierunkową typu tag"""
        genesis = {
            "name": f"tag_{tag_name}",
            "type": "tag_relation",
            "doc": f"Relacja tagowa: {tag_name}",
            "persistent": True
        }
        
        attributes = {
            "tag_name": tag_name,
            "searchable": True,
            "weight": 1.0
        }
        
        relationship = cls(
            source_ulid=source_uid,
            target_ulid=target_uid,
            relation_type="tag",
            genesis=genesis,
            attributes=attributes,
            description=description,
            embedding=embedding or [],
            tags=[tag_name]
        )
        
        await relationship.save()
        return relationship
    
    @classmethod
    async def create_directional_relation(cls, source_uid: str, target_uid: str,
                                         relation_name: str, perspective: str,
                                         description: str = "",
                                         bidirectional: bool = False) -> 'Relationship':
        """Tworzy relację kierunkową z perspektywą"""
        genesis = {
            "name": f"relation_{relation_name}",
            "type": "directional_relation",
            "doc": f"Relacja kierunkowa: {relation_name} z perspektywą {perspective}",
            "bidirectional": bidirectional
        }
        
        attributes = {
            "relation_name": relation_name,
            "strength": 1.0,
            "context_dependent": True,
            "learning_enabled": True
        }
        
        relationship = cls(
            source_ulid=source_uid,
            target_ulid=target_uid,
            relation_type="bidirectional" if bidirectional else "directional",
            genesis=genesis,
            attributes=attributes,
            description=description,
            perspective=perspective
        )
        
        await relationship.save()
        
        # Jeśli obustronna, utwórz również odwrotną relację
        if bidirectional:
            reverse_relationship = cls(
                source_ulid=target_uid,
                target_ulid=source_uid,
                relation_type="directional",
                genesis={**genesis, "name": f"relation_{relation_name}_reverse"},
                attributes={**attributes, "is_reverse": True},
                description=f"Odwrotna: {description}",
                perspective=f"reverse_{perspective}"
            )
            await reverse_relationship.save()
        
        return relationship
    
    async def save(self):
        """Zapisuje relację do bazy jako byt z genotypem"""
        # W LuxDB relacje są bytami, więc używamy systemu Soul/Being
        from database.models.base import Soul, Being
        
        # Utwórz duszę dla relacji jeśli nie istnieje
        soul_data = {
            "genesis": {
                **self.genesis,
                "hash_code": self.hash_code,
                "relation_metadata": {
                    "source_ulid": self.source_ulid,
                    "target_ulid": self.target_ulid,
                    "relation_type": self.relation_type,
                    "perspective": self.perspective
                }
            },
            "attributes": self.attributes,
            "memories": [{
                "type": "relation_creation",
                "description": self.description,
                "embedding": self.embedding,
                "created_at": self.created_at.isoformat() if self.created_at else None
            }],
            "self_awareness": {
                "purpose": f"Relacja {self.relation_type}",
                "usage_count": self.usage_count,
                "success_rate": self.success_rate
            }
        }
        
        # Utwórz lub zaktualizuj duszę relacji
        soul = await Soul.create(soul_data, alias=f"relation_{self.hash_code}")
        
        # Utwórz byt relacji
        being_data = {
            "description": self.description,
            "embedding": self.embedding,
            "perspective": self.perspective,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "hash_code": self.hash_code
        }
        
        being = await Being.create(soul, being_data)
        
        print(f"✅ Relacja {self.relation_type} zapisana jako byt: {self.hash_code}")
        return being
    
    @classmethod
    async def find_by_tag(cls, tag_name: str) -> List['Relationship']:
        """Znajduje wszystkie relacje z danym tagiem"""
        # TODO: Implementacja wyszukiwania w bazie bytów
        return []
    
    @classmethod
    async def find_by_perspective(cls, perspective: str) -> List['Relationship']:
        """Znajduje relacje z daną perspektywą"""
        # TODO: Implementacja wyszukiwania
        return []
    
    async def update_usage_stats(self, success: bool):
        """Aktualizuje statystyki użycia relacji"""
        self.usage_count += 1
        
        if success:
            # Wzór uczenia - zwiększ success_rate
            self.success_rate = (self.success_rate * (self.usage_count - 1) + 1.0) / self.usage_count
        else:
            # Zmniejsz success_rate
            self.success_rate = (self.success_rate * (self.usage_count - 1)) / self.usage_count
        
        self.updated_at = datetime.now()
        await self.save()
    
    def is_similar_to(self, other: 'Relationship', threshold: float = 0.8) -> bool:
        """Sprawdza podobieństwo relacji na podstawie embeddingu"""
        if not self.embedding or not other.embedding:
            return False
        
        # Prosta kalkulacja podobieństwa cosinusowego
        import numpy as np
        
        vec_a = np.array(self.embedding)
        vec_b = np.array(other.embedding)
        
        similarity = np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
        return similarity >= threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje relację do słownika"""
        return {
            "ulid": self.ulid,
            "hash_code": self.hash_code,
            "source_ulid": self.source_ulid,
            "target_ulid": self.target_ulid,
            "relation_type": self.relation_type,
            "genesis": self.genesis,
            "attributes": self.attributes,
            "description": self.description,
            "embedding": self.embedding,
            "perspective": self.perspective,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Relationship':
        """Tworzy relację ze słownika"""
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
        
        return cls(
            ulid=data.get("ulid", ""),
            hash_code=data.get("hash_code", ""),
            source_ulid=data.get("source_ulid", ""),
            target_ulid=data.get("target_ulid", ""),
            relation_type=data.get("relation_type", ""),
            genesis=data.get("genesis", {}),
            attributes=data.get("attributes", {}),
            description=data.get("description", ""),
            embedding=data.get("embedding", []),
            perspective=data.get("perspective"),
            tags=data.get("tags", []),
            created_at=created_at,
            updated_at=updated_at,
            usage_count=data.get("usage_count", 0),
            success_rate=data.get("success_rate", 0.0)
        )

# Factory functions for easy relation creation
async def create_tag(source_uid: str, target_uid: str, tag: str, description: str = "") -> Relationship:
    """Szybkie tworzenie relacji tagowej"""
    return await Relationship.create_tag_relation(source_uid, target_uid, tag, description)

async def create_directional(source_uid: str, target_uid: str, relation: str, 
                           perspective: str, description: str = "") -> Relationship:
    """Szybkie tworzenie relacji kierunkowej"""
    return await Relationship.create_directional_relation(
        source_uid, target_uid, relation, perspective, description
    )

async def create_bidirectional(source_uid: str, target_uid: str, relation: str,
                             perspective: str, description: str = "") -> Relationship:
    """Szybkie tworzenie relacji obustronnej"""
    return await Relationship.create_directional_relation(
        source_uid, target_uid, relation, perspective, description, bidirectional=True
    )
