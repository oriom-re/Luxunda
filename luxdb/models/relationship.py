
"""
Model Relationship (Relacja) dla LuxDB.
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class Relationship:
    """
    Relationship reprezentuje relację między dwoma Being.
    
    W przyszłości relacje będą również Being, ale na razie używamy tradycyjnego modelu.
    """
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_ulid: str = None
    target_ulid: str = None
    relation_type: str = "connection"
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    async def create(
        cls, 
        source_ulid: str, 
        target_ulid: str, 
        relation_type: str = "connection",
        strength: float = 1.0, 
        metadata: Dict[str, Any] = None
    ) -> 'Relationship':
        """
        Tworzy nową relację między dwoma Being.
        
        Args:
            source_ulid: ULID źródłowego Being
            target_ulid: ULID docelowego Being
            relation_type: Typ relacji (np. "friendship", "parent_child")
            strength: Siła relacji (0.0 - 1.0)
            metadata: Dodatkowe metadane relacji
            
        Returns:
            Nowy obiekt Relationship
            
        Example:
            ```python
            friendship = await Relationship.create(
                source_ulid=user1.ulid,
                target_ulid=user2.ulid,
                relation_type="friendship",
                strength=0.8,
                metadata={"since": "2025-01-01"}
            )
            ```
        """
        from ..core.connection import ConnectionManager
        # Tutaj używamy uproszczonej implementacji
        # W pełnej bibliotece należy zaimplementować ConnectionManager
        
        relationship = cls(
            source_ulid=source_ulid,
            target_ulid=target_ulid,
            relation_type=relation_type,
            strength=strength,
            metadata=metadata or {}
        )
        
        # Zapis do bazy danych - implementacja docelowa
        # await RelationshipRepository.save(relationship)
        
        return relationship

    @classmethod
    async def get_all(cls) -> List['Relationship']:
        """
        Pobiera wszystkie relacje z bazy danych.
        
        Returns:
            Lista wszystkich relacji
        """
        relationships = []
        
        # Implementacja docelowa z ConnectionManager
        # pool = await connection_manager.get_pool()
        # async with pool.acquire() as conn:
        #     query = "SELECT * FROM relationships ORDER BY created_at DESC"
        #     rows = await conn.fetch(query)
        #     for row in rows:
        #         relationship = cls.from_row(row)
        #         relationships.append(relationship)
        
        return relationships

    @classmethod
    async def get_by_being(cls, being_ulid: str) -> List['Relationship']:
        """
        Pobiera wszystkie relacje dla danego Being.
        
        Args:
            being_ulid: ULID Being dla którego szukamy relacji
            
        Returns:
            Lista relacji w których Being uczestniczy
        """
        relationships = []
        
        # Implementacja docelowa
        # pool = await connection_manager.get_pool()
        # async with pool.acquire() as conn:
        #     query = """
        #         SELECT * FROM relationships 
        #         WHERE source_ulid = $1 OR target_ulid = $1 
        #         ORDER BY created_at DESC
        #     """
        #     rows = await conn.fetch(query, being_ulid)
        #     for row in rows:
        #         relationship = cls.from_row(row)
        #         relationships.append(relationship)
        
        return relationships

    @classmethod
    async def delete(cls, relationship_id: str) -> bool:
        """
        Usuwa relację z bazy danych.
        
        Args:
            relationship_id: ID relacji do usunięcia
            
        Returns:
            True jeśli usunięcie się powiodło
        """
        # Implementacja docelowa
        # pool = await connection_manager.get_pool()
        # async with pool.acquire() as conn:
        #     query = "DELETE FROM relationships WHERE id = $1"
        #     result = await conn.execute(query, relationship_id)
        #     return result == "DELETE 1"
        
        return False

    @classmethod
    def from_row(cls, row: Dict[str, Any]) -> 'Relationship':
        """
        Tworzy Relationship z wiersza bazy danych.
        
        Args:
            row: Wiersz z bazy danych
            
        Returns:
            Obiekt Relationship
        """
        return cls(
            id=row['id'],
            source_ulid=row['source_ulid'],
            target_ulid=row['target_ulid'],
            relation_type=row['relation_type'],
            strength=row['strength'],
            metadata=json.loads(row['metadata']) if row['metadata'] else {},
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Konwertuje Relationship do słownika.
        
        Returns:
            Słownik reprezentujący Relationship
        """
        return {
            'id': self.id,
            'source_ulid': self.source_ulid,
            'target_ulid': self.target_ulid,
            'relation_type': self.relation_type,
            'strength': self.strength,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f"Relationship({self.relation_type}: {self.source_ulid[:8]}... -> {self.target_ulid[:8]}...)"
