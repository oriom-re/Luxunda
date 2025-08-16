# app_v2/database/soul_repository.py
__name__ = 'soul_repository'
__doc__ = 'Repository pattern dla operacji na souls w bazie danych'
__version__ = '1.0.0'
__static__ = ['get_db_pool', 'set_db_pool', 'get_by_name', 'get_by_field', 'save', 'get_dependencies']


from typing import Dict, Any, Optional, List
import json
import uuid
import aiosqlite
from datetime import datetime
from app_v2.database.postgre_db import Postgre_db


"""Repository pattern dla operacji na souls w bazie danych"""


class SoulRepository:
    """Repository dla operacji na souls w bazie danych"""
    
    @staticmethod
    async def get_by_name(name: str) -> Optional[Dict[str, Any]]:
        """Pobiera soul po nazwie"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            print("Database pool is not initialized.")
            return None

        async with pool.acquire() as conn:
            query = """
                SELECT * FROM souls
                WHERE genesis->>'name' = $1
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await conn.fetchrow(query, name)
            if row:
                return SoulRepository._row_to_dict(row, 'postgres')
        return None

    @staticmethod
    async def get_by_field(field: str, value: Any, column: str = "genesis") -> Optional[Dict[str, Any]]:
        """Pobiera soul po dowolnym polu w genesis"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return None

        async with pool.acquire() as conn:
            query = f"""
                SELECT * FROM souls
                WHERE {column}->>'{field}' = $1
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await conn.fetchrow(query, value)
            if row:
                return SoulRepository._row_to_dict(row, 'postgres')
        return None

    @staticmethod
    async def save(soul: Dict[str, Any]) -> bool:
        """Zapisuje soul do bazy danych"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return False
            async with pool.acquire() as conn:
                query = """
                    INSERT INTO souls (uid, genesis, attributes, memories, self_awareness)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (uid) DO UPDATE SET
                        genesis = EXCLUDED.genesis,
                        attributes = EXCLUDED.attributes,
                        memories = EXCLUDED.memories,
                        self_awareness = EXCLUDED.self_awareness,
                        created_at = NOW()
                """
                await conn.execute(query,
                    soul["uid"],
                    json.dumps(soul["genesis"]),
                    json.dumps(soul["attributes"]),
                    json.dumps(soul["memories"]),
                    json.dumps(soul["self_awareness"])
                )

    @staticmethod
    async def get_dependencies(soul_uid: str) -> List[Dict[str, Any]]:
        """Pobiera zależności dla danego soul"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return []

        dependencies = []
        if hasattr(pool, 'acquire'):  # PostgreSQL
            async with pool.acquire() as conn:
                query = """
                    SELECT s.* FROM relationships r
                    JOIN souls s ON r.target_uid = s.uid
                    WHERE r.source_uid = $1 AND r.attributes->>'type' = 'dependency'
                """
                rows = await conn.fetch(query, soul_uid)
                for row in rows:
                    dependencies.append(SoulRepository._row_to_dict(row, 'postgres'))
        else:  # SQLite
            pool.row_factory = aiosqlite.Row
            query = """
                SELECT s.* FROM relationships r
                JOIN souls s ON r.target_uid = s.uid
                WHERE r.source_uid = ? AND json_extract(r.attributes, '$.type') = 'dependency'
            """
            async with pool.execute(query, (soul_uid,)) as cursor:
                async for row in cursor:
                    dependencies.append(SoulRepository._row_to_dict(row, 'sqlite'))
        
        return dependencies

    @staticmethod
    def _row_to_dict(row, db_type: str) -> Dict[str, Any]:
        """Konwertuje wiersz z bazy danych na słownik"""
        if db_type == 'postgres':
            return {
                "uid": str(row['uid']),
                "genesis": json.loads(row['genesis']),
                "attributes": json.loads(row['attributes']),
                "memories": json.loads(row['memories']),
                "self_awareness": json.loads(row['self_awareness']),
                "created_at": row['created_at']
            }
        else:  # sqlite
            return {
                "uid": row["uid"],
                "genesis": json.loads(row["genesis"]) if row["genesis"] else {},
                "attributes": json.loads(row["attributes"]) if row["attributes"] else {},
                "memories": json.loads(row["memories"]) if row["memories"] else [],
                "self_awareness": json.loads(row["self_awareness"]) if row["self_awareness"] else [],
                "created_at": row["created_at"]
            }
        
class RelationshipRepository:
    """Repository dla operacji na relacjach między souls"""

    @staticmethod
    async def load_by_source(source_uid: str, attributes: Dict[str, Any]=None) -> List[Dict[str, Any]]:
        """Pobiera relacje dla danego źródłowego UID"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return []

        relationships = []
        async with pool.acquire() as conn:
            if attributes:
                query = """
                    SELECT * FROM relationships
                    WHERE source_uid = $1 AND attributes @> $2
                """
                rows = await conn.fetch(query, source_uid, json.dumps(attributes))
            else:
                query = """
                    SELECT * FROM relationships
                    WHERE source_uid = $1
                """
            rows = await conn.fetch(query, source_uid)
            for row in rows:
                relationships.append({
                    "uid": str(row['uid']),
                    "source_uid": str(row['source_uid']),
                    "target_uid": str(row['target_uid']),
                    "attributes": json.loads(row['attributes']),
                    "created_at": row['created_at']
                })
        return relationships
    
    @staticmethod
    async def load_by_target(target_uid: str, attributes: Dict[str, Any]=None) -> List[Dict[str, Any]]:
        """Pobiera relacje dla danego docelowego UID"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return []
        relationships = []
        async with pool.acquire() as conn:
            if attributes:
                query = """
                    SELECT * FROM relationships
                    WHERE target_uid = $1 AND attributes @> $2
                """
                rows = await conn.fetch(query, target_uid, json.dumps(attributes))
            else:
                query = """
                    SELECT * FROM relationships
                    WHERE target_uid = $1
                """
            rows = await conn.fetch(query, target_uid)
            for row in rows:
                relationships.append({
                    "uid": str(row['uid']),
                    "source_uid": str(row['source_uid']),
                    "target_uid": str(row['target_uid']),
                    "attributes": json.loads(row['attributes']),
                    "created_at": row['created_at']
                })
        return relationships
    
    @staticmethod
    async def load_by_attributes(attributes: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Pobiera relacje na podstawie atrybutów"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return []
        
        relationships = []
        async with pool.acquire() as conn:
            query = """
                SELECT * FROM relationships
                WHERE attributes @> $1
            """
            rows = await conn.fetch(query, json.dumps(attributes))
            for row in rows:
                relationships.append({
                    "uid": str(row['uid']),
                    "source_uid": str(row['source_uid']),
                    "target_uid": str(row['target_uid']),
                    "attributes": json.loads(row['attributes']),
                    "created_at": row['created_at']
                })
        return relationships
    
    @staticmethod
    async def save(relationship: Dict[str, Any]) -> bool:
        """Zapisuje relację do bazy danych"""
        try:
            print(f"🔗 Zapisywanie relacji: {relationship.get('source_uid')} -> {relationship.get('target_uid')}")
            db_pool = await Postgre_db.get_db_pool()
            if not db_pool:
                return False

            # Sprawdź, czy uid jest ustawione, jeśli nie, wygeneruj nowe
            relationship_uid = relationship.get('uid', str(uuid.uuid4()))

            if hasattr(db_pool, 'acquire'):  # PostgreSQL (np. asyncpg)
                async with db_pool.acquire() as conn:
                    # PostgreSQL implementation
                    await conn.execute("""
                        INSERT INTO relationships (uid, source_uid, target_uid, attributes)
                        VALUES ($1, $2, $3, $4)
                    """, (
                        relationship_uid,
                        relationship.get('source_uid'),
                        relationship.get('target_uid'),
                        json.dumps(relationship.get('attributes', {}))
                    ))
                    print("✅ Relacja zapisana")
                    return True
            else:  # SQLite (np. aiosqlite)
                # SQLite implementation
                await db_pool.execute("""
                    INSERT OR REPLACE INTO relationships (uid, source_uid, target_uid, attributes)
                    VALUES (?, ?, ?, ?)
                """, (
                    relationship_uid,
                    relationship.get('source_uid'),
                    relationship.get('target_uid'),
                    json.dumps(relationship.get('attributes', {}))
                ))
                await db_pool.commit()
                print("✅ Relacja zapisana")
                return True
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania relacji: {e}")
            return False

