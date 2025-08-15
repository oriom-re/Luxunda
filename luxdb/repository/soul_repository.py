#!/usr/bin/env python3
"""
🗄️ Soul Repository - Tylko nowoczesny JSONB, bez legacy
"""

from typing import Dict, Any, Optional, List
import json
from luxdb.core.postgre_db import Postgre_db
from luxdb.core.globals import Globals
from typing import TYPE_CHECKING
from datetime import datetime
if TYPE_CHECKING:
    from luxdb.models.soul import Soul
    from luxdb.models.being import Being

def get_soul_class():
    from luxdb.models.soul import Soul
    return Soul

def get_being_class():
    from luxdb.models.being import Being
    return Being

class SoulRepository:
    """Repository for Soul operations"""

    @staticmethod
    async def get_soul_by_hash(soul_hash: str) -> dict:
        """Get soul by hash - primary method"""
        return await SoulRepository.get_by_hash(soul_hash)

    @staticmethod
    async def get_by_hash(soul_hash: str) -> dict:
        """Ładuje soul z bazy danych na podstawie jego unikalnego global_ulid"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM souls
                    WHERE soul_hash = $1
                """
                row = await conn.fetchrow(query, soul_hash)
                if row:
                    Soul = get_soul_class()
                    soul = Soul(
                        genotype=row['genotype'],
                        alias=row['alias'],
                        soul_hash=row['soul_hash'],
                        global_ulid=row['global_ulid']
                    )
                    soul.created_at = row['created_at']
                    soul.updated_at = row.get('updated_at')
                    return {"success": True, "soul": soul}
            return {"success": False}
        except Exception as e:
            print(f"❌ Error loading soul by hash: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def get_all(limit: int = 100) -> Dict[str, Any]:
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
                    soul.updated_at = row.get('updated_at')
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

    @staticmethod
    async def get_all_souls(limit: int = 100) -> Dict[str, Any]:
        """Legacy compatibility - delegates to get_all"""
        return await SoulRepository.get_all(limit)

    @staticmethod
    async def get_by_alias(alias: str) -> dict:
        """Ładuje soul z bazy danych na podstawie aliasu"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM souls
                    WHERE alias = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                row = await conn.fetchrow(query, alias)
                if row:
                    Soul = get_soul_class()
                    soul = Soul(
                        genotype=row['genotype'],
                        alias=row['alias'],
                        soul_hash=row['soul_hash'],
                        global_ulid=row['global_ulid']
                    )
                    soul.created_at = row['created_at']
                    soul.updated_at = row.get('updated_at')
                    return {"success": True, "soul": soul}
                else:
                    return {"success": False, "error": "Soul not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def set(soul: 'Soul') -> dict:
        """Zapisuje soul do bazy danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    INSERT INTO souls (soul_hash, global_ulid, alias, genotype)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (soul_hash) DO UPDATE SET
                        alias = EXCLUDED.alias,
                        genotype = EXCLUDED.genotype,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING created_at, updated_at
                """
                result = await conn.fetchrow(query,
                    soul.soul_hash,
                    soul.global_ulid,
                    soul.alias,
                    json.dumps(soul.genotype)
                )

                if result:
                    soul.created_at = result['created_at']
                    soul.updated_at = result['updated_at']

                return {"success": True}
        except Exception as e:
            error_msg = f"Database error while saving soul: {str(e)}"
            print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg, "error_type": "database_error"}

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
    async def get_all_beings() -> Dict[str, Any]:
        """
        Pobiera wszystkie Being z bazy danych.

        Returns:
            Dict z listą wszystkich Being
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                query = "SELECT ulid, soul_hash, data, created_at, updated_at FROM beings ORDER BY created_at DESC"
                rows = await conn.fetch(query)

                beings = []
                for row in rows:
                    being_data = dict(row)
                    being = Being.from_dict(being_data)
                    beings.append(being)

                return {
                    "success": True,
                    "beings": beings,
                    "count": len(beings)
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "beings": []
            }

    @staticmethod
    async def get_by_ulid(ulid: str) -> Optional['Being']:
        """Get being by ULID"""
        Being = get_being_class()
        return await Being.get_by_ulid(ulid)

    @staticmethod
    async def get_by_ulid(ulid: str) -> dict:
        """Pobiera being z bazy danych na podstawie ULID"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT ulid, soul_hash, data, created_at, updated_at
                    FROM beings
                    WHERE ulid = $1
                """
                row = await conn.fetchrow(query, ulid)

                if not row:
                    return {"success": False, "error": "Being not found"}

                # Pobierz Soul dla deserializacji
                Soul = get_soul_class()
                soul = None
                if row['soul_hash']:
                    soul_result = await SoulRepository.get_by_hash(row['soul_hash'])
                    if soul_result.get('success'):
                        soul = soul_result.get('soul')

                # Deserializuj dane według schematu Soul
                from ..utils.serializer import JSONBSerializer
                data = row['data'] or {}
                if soul:
                    data = JSONBSerializer.deserialize_being_data(data, soul)

                # Deserializuj Being z bazy
                being_dict = {
                    'ulid': row['ulid'],
                    'soul_hash': row['soul_hash'],
                    'data': data,  # Teraz z deserializacją typów
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }

                Being = get_being_class()
                being = Being.from_dict(being_dict)

                return {
                    "success": True,
                    "being": being
                }
        except Exception as e:
            print(f"❌ Error getting being by ULID: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def get_by_alias(alias: str) -> dict:
        """Pobiera wszystkie beings o danym aliasie"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT ulid, soul_hash, data, created_at, updated_at FROM beings
                    WHERE data::jsonb->>'alias' = $1
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, alias)

                Being = get_being_class()
                beings = []
                for row in rows:
                    being = Being()
                    being.ulid = row['ulid']
                    being.soul_hash = row['soul_hash']
                    being.data = row['data'] or {}
                    being.created_at = row['created_at']
                    being.updated_at = row['updated_at']

                    # Alias z danych JSONB jeśli istnieje
                    being.alias = being.data.get('alias')
                    beings.append(being)

                return {"success": True, "beings": beings}
        except Exception as e:
            print(f"❌ Error getting beings by alias: {e}")
            return {"success": False, "error": str(e), "beings": []}

    @staticmethod
    async def set(being: 'Being') -> dict:
        """Alias for save_jsonb method"""
        return await BeingRepository.save_jsonb(being)

    @staticmethod
    async def save_jsonb(being: 'Being') -> dict:
        """Zapisuje being do bazy danych w podejściu JSONB"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:

                query = """
                    INSERT INTO beings (ulid, soul_hash, data, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (ulid) DO UPDATE SET
                        soul_hash = EXCLUDED.soul_hash,
                        data = EXCLUDED.data,
                        updated_at = EXCLUDED.updated_at
                    RETURNING created_at
                """

                # Ensure ULID is generated if missing
                if not being.ulid:
                    import ulid
                    being.ulid = str(ulid.ulid())

                result = await conn.fetchrow(query,
                    being.ulid,
                    being.soul_hash,
                    json.dumps(being.data),
                    being.created_at,
                    being.updated_at
                )

                if result:
                    # Baza danych automatycznie ustawia created_at i updated_at
                    being.created_at = result['created_at']
                    being.updated_at = result['updated_at']

                return {"success": True}
        except Exception as e:
            print(f"❌ Error saving being: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def count_beings() -> int:
        """Zwraca liczbę wszystkich beings w bazie danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return 0

            async with pool.acquire() as conn:
                query = "SELECT COUNT(*) FROM beings"
                result = await conn.fetchval(query)
                return result if result is not None else 0
        except Exception as e:
            print(f"❌ Error counting beings: {e}")
            return 0

    @staticmethod
    async def get_all(limit: int = 100) -> Dict[str, Any]:
        """Get all beings"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT ulid, soul_hash, data, created_at, updated_at FROM beings ORDER BY created_at DESC LIMIT $1",
                    limit
                )

                Being = get_being_class()
                beings = []
                for row in rows:
                    being = Being(
                        soul_hash=row['soul_hash'],
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
            print(f"❌ Error getting all beings: {e}")
            return {
                'success': False,
                'error': str(e),
                'beings': [],
                'count': 0
            }

    @staticmethod
    async def get_all_beings(limit: int = 100) -> Dict[str, Any]:
        """Legacy compatibility - delegates to get_all"""
        return await BeingRepository.get_all(limit)

    @staticmethod
    async def search_beings(query: str, limit: int = 50) -> Dict[str, Any]:
        """Search beings by alias or data content"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT ulid, soul_hash, data, created_at, updated_at FROM beings
                    WHERE data::jsonb->>'alias' ILIKE $1
                    OR data::text ILIKE $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, f"%{query}%", limit)

                Being = get_being_class()
                beings = []
                for row in rows:
                    being = Being(
                        soul_hash=row['soul_hash'],
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
    async def get_by_soul_hash(soul_hash: str) -> dict:
        """Ładuje beings na podstawie soul_hash"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT ulid, soul_hash, data, created_at, updated_at FROM beings WHERE soul_hash = $1 ORDER BY created_at DESC",
                    soul_hash
                )

                Being = get_being_class()
                beings = []
                for row in rows:
                    being_data = dict(row)
                    being = Being.from_dict(being_data)
                    beings.append(being)

                return {"success": True, "beings": beings}
        except Exception as e:
            return {"success": False, "error": str(e), "beings": []}

    @staticmethod
    async def get_all_by_alias(alias: str) -> dict:
        """Pobiera wszystkie beings o danym aliasie"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT ulid, soul_hash, data, created_at, updated_at FROM beings
                    WHERE data::jsonb->>'alias' = $1
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, alias)

                Being = get_being_class()
                beings = []
                for row in rows:
                    being = Being()
                    being.ulid = row['ulid']
                    being.soul_hash = row['soul_hash']
                    being.data = row['data'] or {}
                    being.created_at = row['created_at']
                    being.updated_at = row['updated_at']

                    # Alias z danych JSONB jeśli istnieje
                    being.alias = being.data.get('alias')
                    beings.append(being)

                return {"success": True, "beings": beings}
        except Exception as e:
            print(f"❌ Error getting beings by alias: {e}")
            return {"success": False, "error": str(e), "beings": []}

    @staticmethod
    async def update_being(being) -> Dict[str, Any]:
        """
        Aktualizuje Being w bazie danych.

        Args:
            being: Obiekt Being do aktualizacji

        Returns:
            Dict z wynikiem operacji
        """
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:

                query = """
                    UPDATE beings
                    SET data = $1, updated_at = $2
                    WHERE ulid = $3
                """
                await conn.execute(query, being.data, being.updated_at, being.ulid)

                return {"success": True, "updated_being": being.ulid}

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    async def insert_data_transaction(being_data, genotype_data) -> Dict[str, Any]:
        pass

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