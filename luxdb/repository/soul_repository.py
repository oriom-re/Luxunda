#!/usr/bin/env python3
"""
🗄️ Soul Repository - Tylko nowoczesny JSONB, bez legacy
"""

from typing import Dict, Any, Optional, List
import json
from database.postgre_db import Postgre_db
from core.globals import Globals
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from database.models.base import Being
    from database.models.base import Soul

def get_soul_class():
    from database.models.base import Soul
    return Soul

def get_being_class():
    from database.models.base import Being
    return Being

class SoulRepository:
    """Repository for Soul operations"""

    @staticmethod
    async def create_soul(genotype: Dict[str, Any], alias: str = None) -> 'Soul':
        """Create a new soul"""
        Soul = get_soul_class()
        soul = Soul(genotype=genotype, alias=alias)
        await soul.save()
        return soul

    @staticmethod
    async def get_soul_by_hash(soul_hash: str) -> Optional['Soul']:
        """Get soul by hash"""
        Soul = get_soul_class()
        return await Soul.load_by_hash(soul_hash)

    @staticmethod
    async def get_all_souls(limit: int = 100) -> Dict[str, Any]:
        """Get all souls"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM souls ORDER BY created_at DESC LIMIT $1",
                    limit
                )

                Soul = get_soul_class()
                souls = []
                for row in rows:
                    soul = Soul(
                        genotype=row['genotype'],
                        alias=row['alias'],
                        soul_hash=row['soul_hash'],
                        global_ulid=row['global_ulid']
                    )
                    soul.created_at = row['created_at']
                    souls.append(soul)

                return {
                    'success': True,
                    'souls': souls,
                    'count': len(souls)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'souls': [],
                'count': 0
            }

class BeingRepository:
    """Repository for Being operations"""

    @staticmethod
    async def create_being(soul_hash: str, alias: str = None, data: Dict[str, Any] = None) -> 'Being':
        """Create a new being"""
        Being = get_being_class()
        being = Being(soul_hash=soul_hash, alias=alias, data=data or {})
        await being.save()
        return being

    @staticmethod
    async def get_being_by_ulid(ulid: str) -> Optional['Being']:
        """Get being by ULID"""
        Being = get_being_class()
        return await Being.load_by_ulid(ulid)

    @staticmethod
    async def get_all_beings(limit: int = 100) -> Dict[str, Any]:
        """Get all beings"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM beings ORDER BY created_at DESC LIMIT $1",
                    limit
                )

                Being = get_being_class()
                beings = []
                for row in rows:
                    being = Being(
                        soul_hash=row['soul_hash'],
                        alias=row['alias'],
                        data=row['data'] or {},
                        ulid=row['ulid']
                    )
                    being.created_at = row['created_at']
                    being.updated_at = row['updated_at']
                    beings.append(being)

                return {
                    'success': True,
                    'beings': beings,
                    'count': len(beings)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'beings': [],
                'count': 0
            }

    @staticmethod
    async def count_beings() -> int:
        """Count total beings"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT COUNT(*) FROM beings")
                return result or 0
        except Exception as e:
            print(f"Error counting beings: {e}")
            return 0

    @staticmethod
    async def search_beings(query: str, limit: int = 50) -> Dict[str, Any]:
        """Search beings by alias or data content"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM beings 
                    WHERE alias ILIKE $1 
                    OR data::text ILIKE $1
                    ORDER BY created_at DESC 
                    LIMIT $2
                """, f"%{query}%", limit)

                Being = get_being_class()
                beings = []
                for row in rows:
                    being = Being(
                        soul_hash=row['soul_hash'],
                        alias=row['alias'],
                        data=row['data'] or {},
                        ulid=row['ulid']
                    )
                    being.created_at = row['created_at']
                    being.updated_at = row['updated_at']
                    beings.append(being)

                return {
                    'success': True,
                    'beings': beings,
                    'count': len(beings)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'beings': [],
                'count': 0
            }

class RelationshipRepository:
    """Repository for Relationship operations"""

    @staticmethod
    async def create_relationship(source_ulid: str, target_ulid: str, 
                                relation_type: str = 'connection', 
                                strength: float = 1.0,
                                metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a relationship between beings"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                relationship_id = await conn.fetchval("""
                    INSERT INTO relationships 
                    (source_ulid, target_ulid, source_id, target_id, relation_type, strength, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id
                """, source_ulid, target_ulid, source_ulid, target_ulid, 
                    relation_type, strength, json.dumps(metadata or {}))

                return {
                    'success': True,
                    'relationship_id': str(relationship_id)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    async def get_relationships_for_being(ulid: str) -> Dict[str, Any]:
        """Get all relationships for a being"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM relationships 
                    WHERE source_ulid = $1 OR target_ulid = $1
                    ORDER BY created_at DESC
                """, ulid)

                relationships = []
                for row in rows:
                    relationships.append({
                        'id': str(row['id']),
                        'source_ulid': row['source_ulid'],
                        'target_ulid': row['target_ulid'],
                        'relation_type': row['relation_type'],
                        'strength': row['strength'],
                        'metadata': row['metadata'],
                        'created_at': row['created_at'].isoformat() if row['created_at'] else None
                    })

                return {
                    'success': True,
                    'relationships': relationships,
                    'count': len(relationships)
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'relationships': [],
                'count': 0
            }