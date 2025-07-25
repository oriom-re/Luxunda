# app_v2/database/soul_repository.py
__name__ = 'soul_repository'
__doc__ = 'Repository pattern dla operacji na souls w bazie danych'
__version__ = '1.0.0'


from typing import Dict, Any, Optional, List
import json
import aiosqlite
from datetime import datetime


"""Repository pattern dla operacji na souls w bazie danych"""
db_pool: Optional[aiosqlite.Connection] = None
class SoulRepository:
    """Repository dla operacji na souls w bazie danych"""

    async def get_db_pool() -> Optional[aiosqlite.Connection]:
        """Zwraca połączenie z bazą danych - na razie mock"""
        global db_pool
        return db_pool


    async def set_db_pool(pool: aiosqlite.Connection):
        """Ustawia połączenie z bazą danych - na razie mock"""
        global db_pool
        db_pool = pool
        print("Database pool has been set.")


    async def get_by_name(name: str) -> Optional[Dict[str, Any]]:
        """Pobiera soul po nazwie"""
        db_pool = await SoulRepository.get_db_pool()
        if not db_pool:
            print("Database pool is not initialized.")
            return None

        # SQLite implementation
        print(f"🔍 Szukanie soul o nazwie: {name}")
        db_pool.row_factory = aiosqlite.Row
        async with db_pool.execute("""
            SELECT * FROM souls 
            WHERE json_extract(genesis, '$.name') = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (name,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return SoulRepository.row_to_dict(row, 'sqlite')
        return None


    async def get_by_field(field: str, value: Any) -> Optional[Dict[str, Any]]:
        """Pobiera soul po dowolnym polu w genesis"""
        db_pool = await SoulRepository.get_db_pool()
        if not db_pool:
            return None

        print(f"🔍 Szukanie soul po polu {field} = {value}")
        db_pool.row_factory = aiosqlite.Row
        async with db_pool.execute(f"""
            SELECT * FROM souls 
            WHERE json_extract(genesis, '$.{field}') = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (value,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return SoulRepository.row_to_dict(row, 'sqlite')
        return None


    async def save(soul: Dict[str, Any]) -> bool:
        """Zapisuje soul do bazy danych"""
        try:
            print(f"💾 Zapisywanie soul: {soul.get('uid', 'unknown')}")
            db_pool = await SoulRepository.get_db_pool()
            if not db_pool:
                return False

            # SQLite implementation
            await db_pool.execute("""
                INSERT OR REPLACE INTO souls (uid, genesis, attributes, memories, self_awareness)
                VALUES (?, ?, ?, ?, ?)
            """, (
                soul.get('uid'), 
                json.dumps(soul.get('genesis', {})), 
                json.dumps(soul.get('attributes', {})),
                json.dumps(soul.get('memories', [])), 
                json.dumps(soul.get('self_awareness', {}))
            ))
            await db_pool.commit()
            print(f"✅ Soul {soul.get('uid')} zapisany")
            return True
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania soul: {e}")
            return False


    async def save_relationship(relationship: Dict[str, Any]) -> bool:
        """Zapisuje relację do bazy danych"""
        try:
            print(f"🔗 Zapisywanie relacji: {relationship.get('source_uid')} -> {relationship.get('target_uid')}")
            db_pool = await SoulRepository.get_db_pool()
            if not db_pool:
                return False
            
            # SQLite implementation
            import uuid
            relationship_uid = relationship.get('uid', str(uuid.uuid4()))
            
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


    async def get_dependencies(soul_uid: str) -> List[Dict[str, Any]]:
        """Pobiera zależności dla danego soul"""
        print(f"🔍 Pobieranie zależności dla soul: {soul_uid}")
        return []


    def row_to_dict(row, db_type: str) -> Dict[str, Any]:
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
