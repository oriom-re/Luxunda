# app_v2/database/soul_repository.py
__name__ = 'soul_repository'
__doc__ = 'Repository pattern dla operacji na souls w bazie danych'
__version__ = '1.0.0'
__static__ = ['get_db_pool', 'set_db_pool', 'get_by_name', 'get_by_field', 'save', 'get_dependencies']


import asyncio
from typing import Dict, Any, Optional, List
import json
import uuid
import aiosqlite
from app_v2.database.postgre_db import Postgre_db
from app_v2.core.globals import Globals


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
    async def get_by_field(field: str, value: Any, column: str = "genesis", limit: int = 1) -> Optional[Dict[str, Any]]:
        """Pobiera soul po dowolnym polu w genesis"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return None

        async with pool.acquire() as conn:
            query = f"""
                SELECT * FROM souls
                WHERE {column}->>'{field}' = $1
                ORDER BY created_at DESC
            """
            if limit is not None:
                query += f" LIMIT {limit}"
            row = await conn.fetchrow(query, value)
            if row:
                return SoulRepository._row_to_dict(row, 'postgres')
        return None

    @staticmethod
    async def get_by_attributes(attributes: Dict[str, Any], limit: int = 1) -> Optional[Dict[str, Any]]:
        """Pobiera soul po atrybutach"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return None

        async with pool.acquire() as conn:
            query = """
                SELECT * FROM souls
                WHERE attributes @> $1
                ORDER BY created_at DESC
            """
            if limit is not None:
                query += f" LIMIT {limit}"
            row = await conn.fetchrow(query, json.dumps(attributes))
            if row:
                return SoulRepository._row_to_dict(row, 'postgres')
        return None
    
    @staticmethod
    async def load(uid: str) -> Optional[Dict[str, Any]]:
        """Ładuje soul z bazy danych na podstawie UID"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return None

        async with pool.acquire() as conn:
            query = """
                SELECT * FROM souls
                WHERE uid = $1
            """
            row = await conn.fetchrow(query, uid)
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

            async with db_pool.acquire() as conn:
                # PostgreSQL implementation
                await conn.execute("""
                    INSERT INTO relationships (uid, source_uid, target_uid, attributes)
                    VALUES ($1, $2, $3, $4)
                """, 
                    relationship_uid,
                    relationship.get('source_uid'),
                    relationship.get('target_uid'),
                    json.dumps(relationship.get('attributes', {}))
                )
                print("✅ Relacja zapisana")
                return True
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania relacji: {e}")
            return False

    @staticmethod
    async def get_thread_view(thread_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Pobiera widok wątku"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return []

        async with pool.acquire() as conn:
            query = "SELECT * FROM thread_view WHERE thread_id = $1"
            if limit is not None:
                query += " LIMIT $2"
                rows = await conn.fetch(query, thread_id, limit)
            else:
                rows = await conn.fetch(query, thread_id)
            relationships = []
            if not rows:
                return []
            for row in rows:
                print(f"🔗 Pobieranie relacji: {row}")
                relationships.append({
                    "uid": str(row['uid']),
                    "genesis": json.loads(row['genesis']),
                    "attributes": json.loads(row['attributes']),
                    "memories": json.loads(row['memories']),
                    "self_awareness": json.loads(row['self_awareness']),
                    "created_at": row['created_at']
                })


            return [dict(row) for row in rows]

    @staticmethod
    async def get_thread_context(thread_id: str, limit: int = None) -> List[Dict[str, Any]]:
        """Zwraca kontekst wątku"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return []
        async with pool.acquire() as conn:
            query = """
                SELECT m.*, r.attributes->>'type' AS type, r.source_uid AS thread_id
                FROM souls m
                JOIN relationships r ON m.uid = r.target_uid
                WHERE r.source_uid = $1
            """
            if limit is not None:
                query += " LIMIT $2"
                rows = await conn.fetch(query, thread_id, limit)
            else:
                rows = await conn.fetch(query, thread_id)

            relationships = []
            for row in rows:
                relationships.append(row)
            return relationships

class SoulRepository:
    """Repository dla operacji na souls w bazie danych"""

    @staticmethod
    async def save(alias: str, genotype: Dict[str, Any], soul_hash: str) -> dict:
        """Zapisuje soul do bazy danych"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return {"success": False}
        global_ulid = Globals.GLOBAL_ULID

        async with pool.acquire() as conn:
  
            query = """
                INSERT INTO souls (global_ulid, alias, genotype, soul_hash)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (soul_hash) DO NOTHING
            """

            await conn.execute(query,
                global_ulid,
                alias,
                json.dumps(genotype),
                soul_hash
            )
            row = await conn.fetchrow("SELECT * FROM souls WHERE soul_hash = $1", soul_hash)
            if not row:
                print("❌ Failed to save soul, no row returned.")
                return {"success": False}
            print(f"✅ Soul saved with hash: {soul_hash}")
            dict = {
                "soul_hash": row['soul_hash'],
                "alias": row['alias'],
                "genotype": json.loads(row['genotype']),
                "created_at": row['created_at'],
                "global_ulid": row['global_ulid']
            }
            return {"success": True, "soul_dict": dict}

    @staticmethod
    async def load(soul_hash: str) -> Optional[Dict[str, Any]]:
        """Ładuje soul z bazy danych na podstawie jego unikalnego hasha"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return None

        async with pool.acquire() as conn:
            query = """
                SELECT * FROM souls
                WHERE soul_hash = $1
            """
            row = await conn.fetchrow(query, soul_hash)
            if row:
                return {
                    "soul_hash": row['soul_hash'],
                    "alias": row['alias'],
                    "genotype": json.loads(row['genotype']),
                    "created_at": row['created_at']
                }
        return None
    
    @staticmethod
    async def load_by_alias(alias: str) -> Optional[Dict[str, Any]]:
        """Ładuje soul z bazy danych na podstawie jego aliasu"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return None

        async with pool.acquire() as conn:
            query = """
                SELECT * FROM souls
                WHERE alias = $1
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await conn.fetchrow(query, alias)
            if row:
                return {
                    "soul_hash": row['soul_hash'],
                    "alias": row['alias'],
                    "genotype": json.loads(row['genotype']),
                    "created_at": row['created_at']
                }
        return None
    
    @staticmethod
    async def load_all() -> List[Dict[str, Any]]:
        """Ładuje wszystkie souls z bazy danych"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return []

        async with pool.acquire() as conn:
            query = """
                SELECT * FROM souls
                ORDER BY created_at DESC
            """
            rows = await conn.fetch(query)
            return [
                {
                    "soul_hash": row['soul_hash'],
                    "alias": row['alias'],
                    "genotype": json.loads(row['genotype']),
                    "created_at": row['created_at']
                } for row in rows
            ] if rows else []
    
    @staticmethod
    async def load_all_by_alias(alias: str) -> List[Dict[str, Any]]:
        """Ładuje wszystkie souls z bazy danych na podstawie aliasu"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return []

        async with pool.acquire() as conn:
            query = """
                SELECT * FROM souls
                WHERE alias = $1
                ORDER BY created_at DESC
            """
            rows = await conn.fetch(query, alias)
            return [
                {
                    "soul_hash": row['soul_hash'],
                    "alias": row['alias'],
                    "genotype": json.loads(row['genotype']),
                    "created_at": row['created_at']
                } for row in rows
            ] if rows else []
        
class BeingRepository:
    """Repository dla operacji na bytach w bazie danych"""

    @staticmethod
    async def save(ulid: str, soul_hash: str) -> bool:
        """Zapisuje byt do bazy danych"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return False
        
        async with pool.acquire() as conn:
            query = """
                INSERT INTO beings (ulid, soul_hash)
                VALUES ($1, $2)
            """
            await conn.execute(query,
                ulid,
                soul_hash,
            )
            return True

    @staticmethod
    async def load(ulid: str) -> Optional[Dict[str, Any]]:
        """Ładuje byt z bazy danych na podstawie UID"""

        pool = await Postgre_db.get_db_pool()
        if not pool:
            return None

        async with pool.acquire() as conn:
            query = """
                SELECT * FROM beings
                WHERE ulid = $1
            """
            row = await conn.fetchrow(query, ulid)
            if row:
                return {
                    "ulid": str(row['ulid']),
                    "soul_ulid": str(row['soul_ulid']),
                    "created_at": row['created_at']
                }
        return None
    
    @staticmethod
    async def load_all_by_hash(soul_hash: str) -> List[Dict[str, Any]]:
        """Ładuje wszystkie byty z bazy danych na podstawie unikalnego hasha duszy"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return []

        async with pool.acquire() as conn:
            query = """
                SELECT * FROM beings
                WHERE soul_hash = $1
                ORDER BY created_at DESC
            """
            rows = await conn.fetch(query, soul_hash)
            return [
                {
                    "ulid": str(row['ulid']),
                    "soul_hash": str(row['soul_hash']),
                    "created_at": row['created_at']
                } for row in rows
            ] if rows else []   

    @staticmethod
    async def load_all() -> List[Dict[str, Any]]:
        """Ładuje wszystkie byty z bazy danych"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return []

        async with pool.acquire() as conn:
            query = """
                SELECT * FROM beings
                ORDER BY created_at DESC
            """
            rows = await conn.fetch(query)
            return [
                {
                    "ulid": str(row['ulid']),
                    "soul_hash": str(row['soul_hash']),
                    "created_at": row['created_at']
                } for row in rows
            ] if rows else []
    
    @staticmethod
    async def load_last_by_soul_hash(soul_hash: str) -> Optional[Dict[str, Any]]:
        """Ładuje ostatni byt z bazy danych na podstawie unikalnego hasha duszy"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return None

        async with pool.acquire() as conn:
            query = """
                SELECT * FROM beings
                WHERE soul_hash = $1
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await conn.fetchrow(query, soul_hash)
            if row:
                return {
                    "ulid": str(row['ulid']),
                    "soul_hash": str(row['soul_hash']),
                    "created_at": row['created_at']
                }
        return None
    
class DynamicRepository:
    """Repository dla dynamicznych pól w souls"""

    @staticmethod
    async def save(ulid: str, table_name:str, value: Any) -> bool:
        """Zapisuje dynamiczne pola dla danego soul"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return False

            async with pool.acquire() as conn:
                await conn.execute(f"""
                        INSERT INTO {table_name} (ulid, value)
                        VALUES ($1, $2)
                    """, 
                        ulid, value
                    )
            print(f"✅ Dynamiczna tabela {table_name} zapisana dla ulid {ulid}")
            return True
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania dynamicznej tabeli {table_name}: {e}")
            return False
    
    @staticmethod
    async def load(ulid: str, table_name: str) -> Optional[Dict[str, Any]]:
        """Ładuje dynamiczne pola dla danego soul"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return None

            async with pool.acquire() as conn:
                query = f"""
                    SELECT * FROM {table_name}
                    WHERE ulid = $1
                """
                row = await conn.fetchrow(query, ulid)
                if row:
                    print(f"✅ Dynamiczna tabela {table_name} załadowana dla ulid {ulid}")
                    return {"value": row['value'], "data_type": row['data_type']}
                print(f"🔍 Brak danych w dynamicznej tabeli {table_name} dla ulid {ulid}")
            return None
        except Exception as e:
            print(f"❌ Błąd podczas ładowania dynamicznej tabeli {table_name}: {e}")
            return None
    
    @staticmethod
    def generate_dynamic_query(row: dict) -> str:
        """Tworzy dynamiczne SQL na podstawie genotypu i ULID bytu."""
        genotype_config = json.loads(row["genotype"])
        attributes = genotype_config['attributes']
        select_columns = []
        join_clauses = []

        for attr_name, attr_data in attributes.items():
            table = attr_data['type']
            alias = f"{table}_{attr_name}"  # Dodajemy nazwę atrybutu do aliasu
            select_columns.append(f"{alias}.value AS {attr_name}")
            # jako że każdy atrybut jest w osobnej tabeli, tworzymy JOIN
            join_clause = f"LEFT JOIN {table} {alias} ON {alias}.ulid = b.ulid"
            join_clauses.append(join_clause)

        select_stmt = ", ".join(select_columns)
        join_stmt = "\n".join(join_clauses)

        query = f"""
        SELECT {select_stmt}
        FROM beings b
        {join_stmt}
        WHERE b.ulid = $1;
        """
        # print(f"🔍 Generowanie dynamicznego zapytania: {query}")
        return query.strip()

    async def load_dynamic_data(ulid: str) -> Optional[dict]:
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return None

        async with pool.acquire() as conn:
            query = """
                SELECT s.*, b.ulid AS being_ulid 
                FROM souls s
                JOIN beings b ON s.soul_hash = b.soul_hash
                WHERE b.ulid = $1
            """
            row = await conn.fetchrow(query, ulid)
            if not row:
                return None


            query = DynamicRepository.generate_dynamic_query(row)
            data_row = await conn.fetchrow(query, ulid)
            # print(f"🔍 Pobieranie danych dynamicznych dla bytu {ulid}: {data_row}")
            return dict(data_row) if data_row else None

    @staticmethod
    async def save_dynamic_data(ulid: str, data: Dict[str, Any]) -> bool:
        """Zapisuje dynamiczne dane dla bytu na podstawie genotypu"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return False

        async with pool.acquire() as conn:
            for key, value in data.items():
                table_name = key
                try:
                    await DynamicRepository.save(ulid, table_name, value)
                except Exception as e:
                    print(f"❌ Błąd podczas zapisywania dynamicznej tabeli {table_name} dla ulid {ulid}: {e}")
                    return False
        print(f"✅ Dynamiczne dane zapisane dla bytu {ulid}")
        return True