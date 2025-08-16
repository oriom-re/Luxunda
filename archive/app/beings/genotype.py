
import asyncio
from typing import List

import aiosqlite
from app.beings.base import Being, Relationship
from typing import Dict, Any, Optional
from datetime import datetime
from app.database import get_db_pool
import json
import importlib.util
import sys

class Genotype(Being):
    """
    Genotype class that extends the Being class.
    This class is used to represent a genotype in the system.
    """
    loaded_genes: Optional[List[str]] = []
    cxt: Dict[str, Any] = {}
    local_cxt: Dict[str, Any] = {}

    
    async def load_and_run_genotype(self, genotype_name, call_init: bool = True):
        db_pool = await get_db_pool()
        soul = await self.get_soul_by_name(genotype_name)
        if not soul:
            print(f"❌ Nie znaleziono duszy dla nazwy: {genotype_name}")
            return None
        print(f"🔍 Ładowanie modułu {genotype_name} {soul['genesis'].get('name')}")
        if genotype_name in self.cxt:
            return self.cxt[genotype_name]

        # 1. 🔌 Wczytaj zależności
        await self.load_dependencies(soul)

        # 2. 📦 Załaduj jako moduł dynamicznie z kodu
        try:
            # Tworzymy specyfikację modułu z kodu źródłowego
            spec = importlib.util.spec_from_loader(
                genotype_name, 
                loader=None, 
                origin="virtual"
            )
            if not spec:
                print(f"❌ Nie udało się utworzyć specyfikacji dla modułu: {genotype_name}")
                return None
            
            # Tworzymy moduł z specyfikacji
            genotype = importlib.util.module_from_spec(spec)
            
            # Dodajemy moduł do sys.modules przed wykonaniem kodu
            sys.modules[genotype_name] = genotype
            
            # Wykonujemy kod źródłowy w kontekście modułu
            exec(soul['genesis']['code'], genotype.__dict__)
            
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia modułu {genotype_name}: {e}")
            # Usuń moduł z sys.modules jeśli wystąpił błąd
            if genotype_name in sys.modules:
                del sys.modules[genotype_name]
            return None

        self.cxt[genotype_name] = genotype

        # 3. ⚙️ Inicjalizacja, jeśli funkcja lub klasa dostępna
        if call_init:
            if hasattr(genotype, "init"):
                await self.maybe_async(genotype.init)
                print(f"✅ Inicjalizacja modułu {genotype_name} zakończona.")
            elif hasattr(genotype, "__call__"):
                await self.maybe_async(genotype())
                print(f"✅ Wywołanie modułu {genotype_name} zakończone.")
        
        return genotype

    @staticmethod
    async def get_soul_by_name(name: str) -> Optional[Dict[str, Any]]:
        pool = await get_db_pool()
        # get all tables
        if not pool:
            print("Database pool is not initialized.")
            return None

        if hasattr(pool, 'acquire'):  # PostgreSQL (np. asyncpg)
            async with pool.acquire() as conn:
                tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                print(f"Available tables: {[table['table_name'] for table in tables]}")
                query = """
                    SELECT * FROM souls
                    WHERE genesis->>'name' = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                row = await conn.fetchrow(query, name)
                print(f"🔍 Searching for soul with name: {name}")
                if row:
                    return {
                        "uid": str(row['uid']),
                        "genesis": json.loads(row['genesis']),
                        "attributes": json.loads(row['attributes']),
                        "memories": json.loads(row['memories']),
                        "self_awareness": json.loads(row['self_awareness']),
                        "created_at": row['created_at']
                    }
                print(f"No soul found for name: {name}")
        else:  # SQLite (np. aiosqlite)
            pool.row_factory = aiosqlite.Row
            query = """
                SELECT * FROM souls
                WHERE json_extract(genesis, '$.name') = ?
                ORDER BY created_at DESC
                LIMIT 1
            """
            async with pool.execute(query, (name,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "uid": row["uid"],
                        "genesis": json.loads(row["genesis"]) if row["genesis"] else {},
                        "attributes": json.loads(row["attributes"]) if row["attributes"] else {},
                        "memories": json.loads(row["memories"]) if row["memories"] else [],
                        "self_awareness": json.loads(row["self_awareness"]) if row["self_awareness"] else [],
                        "created_at": row["created_at"]
                    }
        return None

    @staticmethod
    async def maybe_async(func):
        """Wykonuje funkcję niezależnie od tego, czy jest async."""
        if asyncio.iscoroutinefunction(func):
            await func()
        else:
            func()

    async def load_dependencies(self, soul: Dict[str, Any]):
        """Wczytuje zależności z bazy i ładuje je rekurencyjnie."""
        db_pool = await get_db_pool()
        dependencies = soul.get("genesis", {}).get("dependencies", [])
        if not dependencies:
            print(f"🔍 Brak zależności dla {soul['genesis'].get('name')}")
            return
        print(f"context: {self.cxt}")
        for depend in dependencies:
            if depend in self.cxt:
                print("🔍 Zależność już załadowana:", depend)
            else:
                print(f"🔍 Wczytywanie zależności dla: {depend}")
        return 
        if hasattr(db_pool, 'acquire'):  # PostgreSQL (np. asyncpg)
            async with db_pool.acquire() as conn:
                query = """
                SELECT target_uid, genesis FROM relationships
                JOIN souls ON relationships.target_uid = souls.uid
                WHERE source_uid = ? AND relationships.attributes LIKE '%depends_on%'
                """
                print(f"🔍 Wczytywanie zależności dla {soul['genesis'].get('name')}")
                
                async with conn.execute(query, (soul.get("uid"),)) as cursor:
                    async for row in cursor:
                        target_uid, target_genesis = row
                        target_uid_dict = {
                            "soul": target_uid,
                            "genesis": json.loads(target_genesis),
                            "attributes": {},
                            "memories": [],
                            "self_awareness": {}
                        }
                        await self.load_and_run_genotype(target_uid_dict, call_init=True)
        

    @classmethod
    async def send_genotype_to_db(cls, soul: Dict):
        """Zapisuje moduł jako soul w bazie danych."""
        existing_soul = await cls.get_soul_by_name(soul["genesis"]["name"])
        if existing_soul:
            print(f"🔍 Soul with name {soul['genesis']['name']} already exists. Updating existing soul.")
            if await cls.get_soul_by('hash_hex', soul["genesis"]["hash_hex"]):
                # Jeśli istnieje już taki soul, nie zapisuj ponownie
                print(f"🔍 Soul with name {soul['genesis']['name']} already exists. Skipping save.")
                return
            else:
                print(f"🔍 Soul with name {soul['genesis']['name']} already exists. Replacing with new soul.")
                await Relationship.create(
                    source_uid=existing_soul["uid"],
                    target_uid=soul["uid"],
                    attributes={"replaces": soul["uid"]}
                )
        await cls.create(soul)
    
    @staticmethod
    async def get_soul_by(element: str, value: Any):
        """Zwraca duszę na podstawie elementu i wartości."""
        pool = await get_db_pool()
        if not pool:
            print("Database pool is not initialized.")
            return None
        if hasattr(pool, 'acquire'):  # PostgreSQL (np. asyncpg)
            async with pool.acquire() as conn:
                query = f"""
                    SELECT * FROM souls
                    WHERE genesis->>'{element}' = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                row = await conn.fetchrow(query, value)
                if row:
                    return {
                        "uid": str(row['uid']),
                        "genesis": json.loads(row['genesis']),
                        "attributes": json.loads(row['attributes']),
                        "memories": json.loads(row['memories']),
                        "self_awareness": json.loads(row['self_awareness']),
                        "created_at": row['created_at']
                    }
        else:  # SQLite (np. aiosqlite)
            pool.row_factory = aiosqlite.Row
            query = f"""
                SELECT * FROM souls
                WHERE json_extract(genesis, '$.{element}') = ?
                ORDER BY created_at DESC
                LIMIT 1
            """
            async with pool.execute(query, (value,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "uid": row["uid"],
                        "genesis": json.loads(row["genesis"]) if row["genesis"] else {},
                        "attributes": json.loads(row["attributes"]) if row["attributes"] else {},
                        "memories": json.loads(row["memories"]) if row["memories"] else [],
                        "self_awareness": json.loads(row["self_awareness"]) if row["self_awareness"] else [],
                        "created_at": row["created_at"]
                    }
        return None