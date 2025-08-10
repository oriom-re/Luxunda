
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import json

@dataclass
class Relationship:
    """Enhanced relationship class supporting mixed ID types (hash/ULID) and soul-being relationships"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Flexible source/target fields that can handle both hash and ULID
    source_id: str = None  # Can be soul_hash or being_ulid
    target_id: str = None  # Can be soul_hash or being_ulid
    source_type: str = "being"  # "soul" or "being"
    target_type: str = "being"  # "soul" or "being"
    
    relation_type: str = "connection"
    strength: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Legacy compatibility
    @property
    def source_ulid(self):
        """Legacy compatibility - returns source_id if source is being"""
        return self.source_id if self.source_type == "being" else None
    
    @property
    def target_ulid(self):
        """Legacy compatibility - returns target_id if target is being"""
        return self.target_id if self.target_type == "being" else None

    @classmethod
    async def create(cls, source_id: str, target_id: str, source_type: str = "being", 
                     target_type: str = "being", relation_type: str = "connection", 
                     strength: float = 1.0, metadata: Dict[str, Any] = None) -> 'Relationship':
        """Tworzy nową relację obsługującą zarówno souls (hash) jak i beings (ULID)"""
        from database.postgre_db import Postgre_db
        
        relationship = cls(
            source_id=source_id,
            target_id=target_id,
            source_type=source_type,
            target_type=target_type,
            relation_type=relation_type,
            strength=strength,
            metadata=metadata or {}
        )
        
        db_pool = await Postgre_db.get_db_pool()
        if db_pool:
            async with db_pool.acquire() as conn:
                query = """
                    INSERT INTO relationships (id, source_id, target_id, source_type, target_type, relation_type, strength, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (source_id, target_id, relation_type) 
                    DO UPDATE SET 
                        strength = EXCLUDED.strength,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING created_at, updated_at
                """
                result = await conn.fetchrow(query, relationship.id, source_id, target_id, 
                                           source_type, target_type, relation_type, strength, 
                                           json.dumps(metadata or {}))
                if result:
                    relationship.created_at = result['created_at']
                    relationship.updated_at = result['updated_at']
        
        return relationship
    
    @classmethod
    async def create_soul_being_relationship(cls, soul_hash: str, being_ulid: str, 
                                           relation_type: str = "instantiates", 
                                           strength: float = 1.0) -> 'Relationship':
        """Helper method to create soul-being relationships"""
        return await cls.create(
            source_id=soul_hash,
            target_id=being_ulid,
            source_type="soul",
            target_type="being",
            relation_type=relation_type,
            strength=strength,
            metadata={"description": f"Soul {soul_hash[:8]}... instantiates being {being_ulid}"}
        )

    @classmethod
    async def get_all(cls) -> List['Relationship']:
        """Pobiera wszystkie relacje"""
        from database.postgre_db import Postgre_db
        
        relationships = []
        db_pool = await Postgre_db.get_db_pool()
        if db_pool:
            async with db_pool.acquire() as conn:
                # Try new schema first, fall back to legacy
                try:
                    query = """
                        SELECT id, source_id, target_id, source_type, target_type, relation_type, strength, metadata, created_at, updated_at
                        FROM relationships
                        ORDER BY created_at DESC
                    """
                    rows = await conn.fetch(query)
                    for row in rows:
                        relationship = cls(
                            id=row['id'],
                            source_id=row['source_id'],
                            target_id=row['target_id'],
                            source_type=row['source_type'],
                            target_type=row['target_type'],
                            relation_type=row['relation_type'],
                            strength=row['strength'],
                            metadata=json.loads(row['metadata']) if row['metadata'] else {},
                            created_at=row['created_at'],
                            updated_at=row['updated_at']
                        )
                        relationships.append(relationship)
                except:
                    # Fallback to legacy schema
                    query = """
                        SELECT id, source_ulid as source_id, target_ulid as target_id, relation_type, strength, metadata, created_at, updated_at
                        FROM relationships
                        ORDER BY created_at DESC
                    """
                    rows = await conn.fetch(query)
                    for row in rows:
                        relationship = cls(
                            id=row['id'],
                            source_id=row['source_id'],
                            target_id=row['target_id'],
                            source_type="being",
                            target_type="being",
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
            'source_id': self.source_id,
            'target_id': self.target_id,
            'source_type': self.source_type,
            'target_type': self.target_type,
            'relation_type': self.relation_type,
            'strength': self.strength,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Legacy compatibility
            'source_ulid': self.source_ulid,
            'target_ulid': self.target_ulid
        }
