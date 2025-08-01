
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import json

@dataclass
class Relationship:
    """Tradycyjna klasa relacji dla MVP"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_ulid: str = None
    target_ulid: str = None
    relation_type: str = "connection"
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    async def create(cls, source_ulid: str, target_ulid: str, relation_type: str = "connection", 
                     strength: float = 1.0, metadata: Dict[str, Any] = None) -> 'Relationship':
        """Tworzy nową relację"""
        from database.postgre_db import Postgre_db
        
        relationship = cls(
            source_ulid=source_ulid,
            target_ulid=target_ulid,
            relation_type=relation_type,
            strength=strength,
            metadata=metadata or {}
        )
        
        db_pool = await Postgre_db.get_db_pool()
        if db_pool:
            async with db_pool.acquire() as conn:
                query = """
                    INSERT INTO relationships (id, source_ulid, target_ulid, relation_type, strength, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (source_ulid, target_ulid, relation_type) 
                    DO UPDATE SET 
                        strength = EXCLUDED.strength,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING created_at, updated_at
                """
                result = await conn.fetchrow(query, relationship.id, source_ulid, target_ulid, 
                                           relation_type, strength, json.dumps(metadata or {}))
                if result:
                    relationship.created_at = result['created_at']
                    relationship.updated_at = result['updated_at']
        
        return relationship

    @classmethod
    async def get_all(cls) -> List['Relationship']:
        """Pobiera wszystkie relacje"""
        from database.postgre_db import Postgre_db
        
        relationships = []
        db_pool = await Postgre_db.get_db_pool()
        if db_pool:
            async with db_pool.acquire() as conn:
                query = """
                    SELECT id, source_ulid, target_ulid, relation_type, strength, metadata, created_at, updated_at
                    FROM relationships
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query)
                for row in rows:
                    relationship = cls(
                        id=row['id'],
                        source_ulid=row['source_ulid'],
                        target_ulid=row['target_ulid'],
                        relation_type=row['relation_type'],
                        strength=row['strength'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    relationships.append(relationship)
        
        return relationships

    @classmethod
    async def get_by_being(cls, being_ulid: str) -> List['Relationship']:
        """Pobiera wszystkie relacje dla danego being'a"""
        from database.postgre_db import Postgre_db
        
        relationships = []
        db_pool = await Postgre_db.get_db_pool()
        if db_pool:
            async with db_pool.acquire() as conn:
                query = """
                    SELECT id, source_ulid, target_ulid, relation_type, strength, metadata, created_at, updated_at
                    FROM relationships
                    WHERE source_ulid = $1 OR target_ulid = $1
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, being_ulid)
                for row in rows:
                    relationship = cls(
                        id=row['id'],
                        source_ulid=row['source_ulid'],
                        target_ulid=row['target_ulid'],
                        relation_type=row['relation_type'],
                        strength=row['strength'],
                        metadata=json.loads(row['metadata']) if row['metadata'] else {},
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    relationships.append(relationship)
        
        return relationships

    @classmethod
    async def delete(cls, relationship_id: str) -> bool:
        """Usuwa relację"""
        from database.postgre_db import Postgre_db
        
        db_pool = await Postgre_db.get_db_pool()
        if db_pool:
            async with db_pool.acquire() as conn:
                query = "DELETE FROM relationships WHERE id = $1"
                result = await conn.execute(query, relationship_id)
                return result == "DELETE 1"
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje do słownika"""
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
