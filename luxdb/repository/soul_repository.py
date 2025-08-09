#!/usr/bin/env python3
"""
🗄️ Soul Repository - Tylko nowoczesny JSONB, bez legacy
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from database.postgre_db import Postgre_db

# Eksportuj tylko BeingRepository
__all__ = ['BeingRepository']

def get_being_class():
    """Importuje klasę Being aby uniknąć circular imports"""
    from ..models.being import Being
    return Being

class BeingRepository:
    """
    Nowoczesne repozytorium używające tylko JSONB
    Bez dynamicznych tabel i legacy systemów
    """

    @staticmethod
    async def save_jsonb(being: 'Being') -> dict:
        """Zapisuje being używając podejścia JSONB"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False, "error": "No database connection"}

            async with pool.acquire() as conn:
                if being.ulid:
                    # Update istniejącego
                    query = """
                        UPDATE beings 
                        SET 
                            soul_hash = $2,
                            alias = $3,
                            data = $4,
                            vector_embedding = $5,
                            table_type = $6,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE ulid = $1
                        RETURNING ulid, created_at, updated_at
                    """
                    row = await conn.fetchrow(
                        query,
                        being.ulid,
                        being.soul_hash,
                        being.alias,
                        json.dumps(being.data) if being.data else '{}',
                        being.vector_embedding,
                        being.table_type or 'being'
                    )
                else:
                    # Insert nowego
                    query = """
                        INSERT INTO beings (soul_hash, alias, data, vector_embedding, table_type)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING ulid, created_at, updated_at
                    """
                    row = await conn.fetchrow(
                        query,
                        being.soul_hash,
                        being.alias,
                        json.dumps(being.data) if being.data else '{}',
                        being.vector_embedding,
                        being.table_type or 'being'
                    )

                if row:
                    return {
                        "success": True,
                        "ulid": row['ulid'],
                        "created_at": row['created_at'],
                        "updated_at": row['updated_at']
                    }
                else:
                    return {"success": False, "error": "Failed to save being"}

        except Exception as e:
            print(f"❌ Error saving being: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_by_ulid(ulid: str) -> dict:
        """Ładuje being z bazy danych na podstawie ULID"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False, "error": "No database connection"}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM beings WHERE ulid = $1
                """
                row = await conn.fetchrow(query, ulid)

                if row:
                    Being = get_being_class()
                    being = Being()
                    being.ulid = row['ulid']
                    being.soul_hash = row['soul_hash']
                    being.alias = row['alias']
                    being.data = json.loads(row['data']) if row['data'] else {}
                    being.vector_embedding = list(row['vector_embedding']) if row['vector_embedding'] else None
                    being.table_type = row['table_type']
                    being.created_at = row['created_at']
                    being.updated_at = row['updated_at']

                    return {"success": True, "beings": [being]}
                else:
                    return {"success": False, "beings": []}

        except Exception as e:
            print(f"❌ Error loading being by ULID: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_all_by_soul_hash(soul_hash: str) -> dict:
        """Ładuje wszystkie beings z danym soul_hash"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False, "error": "No database connection"}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM beings
                    WHERE soul_hash = $1
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, soul_hash)

                Being = get_being_class()
                beings: List['Being'] = []

                for row in rows:
                    being = Being()
                    being.ulid = row['ulid']
                    being.soul_hash = row['soul_hash']
                    being.alias = row['alias']
                    being.data = json.loads(row['data']) if row['data'] else {}
                    being.vector_embedding = list(row['vector_embedding']) if row['vector_embedding'] else None
                    being.table_type = row['table_type']
                    being.created_at = row['created_at']
                    being.updated_at = row['updated_at']
                    beings.append(being)

                return {"success": True, "beings": beings}

        except Exception as e:
            print(f"❌ Error loading beings by soul_hash: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_all_by_alias(alias: str) -> dict:
        """Ładuje beings z bazy danych na podstawie aliasu"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False, "error": "No database connection"}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM beings
                    WHERE alias = $1
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, alias)
                Being = get_being_class()
                beings: List['Being'] = []
                for row in rows:
                    being = Being()
                    being.ulid = row['ulid']
                    being.soul_hash = row['soul_hash']
                    being.alias = row['alias']
                    being.data = json.loads(row['data']) if row['data'] else {}
                    being.vector_embedding = list(row['vector_embedding']) if row['vector_embedding'] else None
                    being.created_at = row['created_at']
                    being.updated_at = row['updated_at']
                    beings.append(being)
            return {"success": True, "beings": beings}
        except Exception as e:
            print(f"❌ Error loading beings by alias: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def find_similar_beings(embedding: List[float], threshold: float = 0.8, limit: int = 10) -> List['Being']:
        """Znajduje podobne beings na podstawie embedingu wektorowego"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                print("❌ No database connection")
                return []

            async with pool.acquire() as conn:
                query = """
                    SELECT *, vector_embedding <-> $1 as distance
                    FROM beings 
                    WHERE vector_embedding IS NOT NULL 
                    AND vector_embedding <-> $1 < $2
                    ORDER BY vector_embedding <-> $1
                    LIMIT $3
                """

                rows = await conn.fetch(query, embedding, 1 - threshold, limit)
                Being = get_being_class()
                beings = []

                for row in rows:
                    being = Being()
                    being.ulid = row['ulid']
                    being.soul_hash = row['soul_hash']
                    being.alias = row['alias']
                    being.data = json.loads(row['data']) if row['data'] else {}
                    being.vector_embedding = list(row['vector_embedding']) if row['vector_embedding'] else None
                    being.created_at = row['created_at']
                    being.updated_at = row['updated_at']
                    beings.append(being)

                return beings

        except Exception as e:
            print(f"❌ Error finding similar beings: {e}")
            return []

    @staticmethod
    async def delete_being(ulid: str) -> dict:
        """Usuwa being z bazy danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False, "error": "No database connection"}

            async with pool.acquire() as conn:
                query = "DELETE FROM beings WHERE ulid = $1"
                result = await conn.execute(query, ulid)

                return {
                    "success": True,
                    "deleted": result == "DELETE 1"
                }

        except Exception as e:
            print(f"❌ Error deleting being: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def get_all_beings(limit: int = 100, offset: int = 0) -> dict:
        """Pobiera wszystkie beings z paginacją"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False, "error": "No database connection"}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM beings
                    ORDER BY created_at DESC
                    LIMIT $1 OFFSET $2
                """
                rows = await conn.fetch(query, limit, offset)

                Being = get_being_class()
                beings: List['Being'] = []

                for row in rows:
                    being = Being()
                    being.ulid = row['ulid']
                    being.soul_hash = row['soul_hash']
                    being.alias = row['alias']
                    being.data = json.loads(row['data']) if row['data'] else {}
                    being.vector_embedding = list(row['vector_embedding']) if row['vector_embedding'] else None
                    being.table_type = row['table_type']
                    being.created_at = row['created_at']
                    being.updated_at = row['updated_at']
                    beings.append(being)

                return {"success": True, "beings": beings}

        except Exception as e:
            print(f"❌ Error getting all beings: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def count_beings() -> int:
        """Zlicza wszystkie beings w bazie"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return 0

            async with pool.acquire() as conn:
                count = await conn.fetchval("SELECT COUNT(*) FROM beings")
                return count or 0

        except Exception as e:
            print(f"❌ Error counting beings: {e}")
            return 0