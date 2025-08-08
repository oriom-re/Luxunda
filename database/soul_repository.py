# app_v2/database/soul_repository.py
__name__ = 'soul_repository'
__doc__ = 'Repository pattern dla operacji na souls w bazie danych'
__version__ = '2.0.0'



from typing import Dict, Any, Optional, List
import json
from database.postgre_db import Postgre_db
from core.globals import Globals
from database.parser_table import parse_py_type, build_table_name, process_genotype_for_tables
# pobiera typy
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from database.models.base import Being
    from database.models.base import Soul

# Import dla runtime
def get_soul_class():
    from database.models.base import Soul
    return Soul

def get_being_class():
    from database.models.base import Being
    return Being


"""Repository pattern dla operacji na souls w bazie danych"""

class SoulRepository:
    """Repository dla operacji na souls w bazie danych"""

    @staticmethod
    async def save(soul: 'Soul') -> dict:
        """Zapisuje soul do bazy danych"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return {"success": False}


        async with pool.acquire() as conn:

            query = """
                INSERT INTO souls (soul_hash, global_ulid, alias, genotype)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (soul_hash) DO NOTHING
            """

            result = await conn.execute(query,
                soul.soul_hash,
                soul.global_ulid,
                soul.alias,
                json.dumps(soul.genotype)
            )
            if result.endswith("1"):
                row = await conn.fetchrow("SELECT * FROM souls WHERE soul_hash = $1", soul.soul_hash)
                if not row:
                    print("❌ Failed to save soul, no row returned.")
                    return {"success": False}
                print(f"✅ Soul saved with hash: {soul.soul_hash[:8]}... and alias: {soul.alias}")
                soul.created_at = row['created_at']
            return {"success": True}

    @staticmethod
    async def load(soul: 'Soul') -> dict:
        """Ładuje soul z bazy danych na podstawie jego unikalnego hasha"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM souls
                    WHERE soul_hash = $1
                """
                row = await conn.fetchrow(query, soul.soul_hash)
                if row:
                    soul.alias = row['alias']
                    soul.soul_hash = row['soul_hash']
                    soul.genotype = json.loads(row['genotype'])
                    soul.created_at = row['created_at']
                    soul.global_ulid = row['global_ulid']
            return {"success": True}
        except Exception as e:
            print(f"❌ Error loading soul: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_by_hash(hash: str) -> dict:
        """Ładuje soul z bazy danych na podstawie jego unikalnego global_ulid"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM souls
                    WHERE global_ulid = $1
                """
                row = await conn.fetchrow(query, hash)
                if row:
                    Soul = get_soul_class()
                    soul = Soul()
                    soul.alias = row['alias']
                    soul.soul_hash = row['soul_hash']
                    soul.genotype = json.loads(row['genotype'])
                    soul.created_at = row['created_at']
                    soul.global_ulid = row['global_ulid']
            return {"success": True, "soul": soul}
        except Exception as e:
            print(f"❌ Error loading soul by ulid: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_by_alias(alias: str) -> dict:
        """Ładuje soul z bazy danych na podstawie jego aliasu"""
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
                    soul: 'Soul' = Soul()
                    soul.alias = row['alias']
                    soul.soul_hash = row['soul_hash']
                    soul.genotype = json.loads(row['genotype'])
                    soul.created_at = row['created_at']
                    soul.global_ulid = row['global_ulid']
            return {"success": True, "soul": soul}
        except Exception as e:
            print(f"❌ Error loading soul by alias: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_all() -> dict:
        """Ładuje wszystkie souls z bazy danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False, "error": "No database connection"}


            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM souls
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query)
                Soul = get_soul_class()
                souls: List['Soul'] = []
                for row in rows:
                    soul = Soul()
                    soul.soul_hash = row['soul_hash']
                    soul.alias = row['alias']
                    soul.genotype = json.loads(row['genotype'])
                    soul.created_at = row['created_at']
                    soul.global_ulid = row['global_ulid']
                    souls.append(soul)
                if not souls:
                    souls = [None]
            return {"success": True, "souls": souls}
        except Exception as e:
            print(f"❌ Error loading all souls: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_all_by_alias(alias: str) -> dict:
        """Ładuje wszystkie souls z bazy danych na podstawie aliasu"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM souls
                    WHERE alias = $1
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, alias)
                Soul = get_soul_class()
                souls: List['Soul'] = []
                for row in rows:
                    soul = Soul()
                    soul.soul_hash = row['soul_hash']
                    soul.alias = row['alias']
                    soul.genotype = json.loads(row['genotype'])
                    soul.created_at = row['created_at']
                    soul.global_ulid = row['global_ulid']
                    souls.append(soul)
                if not souls:
                    souls = [None]
            return {"success": True, "souls": souls}
        except Exception as e:
            print(f"❌ Error loading souls by alias: {e}")
            return {"success": False, "error": str(e)}

class BeingRepository:
    """Repository dla operacji na beings w bazie danych"""

    @staticmethod
    async def save(being: 'Being') -> dict:
        """Zapisuje being do bazy danych"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return {"success": False}

        async with pool.acquire() as conn:
            # Determine table_type based on soul alias and genotype
            table_type = 'being'  # default
            if hasattr(being, '_soul') and being._soul:
                soul_alias = getattr(being._soul, 'alias', None)
                genotype = getattr(being._soul, 'genotype', {})
                genesis_type = genotype.get('genesis', {}).get('type', None)

                if soul_alias in ['user_profile', 'ai_agent']:
                    table_type = 'soul'
                elif genesis_type == 'relation' or soul_alias == 'basic_relation':
                    table_type = 'relation'

            query = """
                INSERT INTO beings (ulid, soul_hash, alias, table_type)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (ulid) DO UPDATE SET
                    alias = EXCLUDED.alias,
                    table_type = EXCLUDED.table_type,
                    updated_at = CURRENT_TIMESTAMP
            """
            result = await conn.execute(query,
                being.ulid,
                being.soul_hash,
                being.alias,
                table_type
            )
            if result.endswith("1"):
                if not being.created_at:
                    await BeingRepository.load(being)
                print(f"✅ Being saved with ulid: {being.ulid[:8]}... and soul hash: {being.soul_hash[:8]}...")
            return {"success": True}

    @staticmethod
    async def load_by_ulid(ulid: str) -> dict:
        """Ładuje being z bazy danych na podstawie jego unikalnego ulid"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM beings
                    WHERE ulid = $1
                """
                row = await conn.fetchrow(query, ulid)
                if row:
                    Being = get_being_class()
                    being = Being()
                    being.ulid = row['ulid']
                    being.soul_hash = row['soul_hash']
                    being.alias = row['alias']
                    being.created_at = row['created_at']
                    if 'updated_at' in row:
                        being.updated_at = row['updated_at']
            return {"success": True, "being": being}
        except Exception as e:
            print(f"❌ Error loading being by ulid: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load(being: 'Being') -> dict:
        """Ładuje being z bazy danych na podstawie jego unikalnego ulid"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM beings
                    WHERE ulid = $1
                """
                row = await conn.fetchrow(query, being.ulid)
                if row:
                    being.soul_hash = row['soul_hash']
                    being.alias = row['alias']
                    being.created_at = row['created_at']
            return {"success": True}
        except Exception as e:
            print(f"❌ Error loading being: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_all_by_soul_hash(soul_hash: str) -> dict:
        """Ładuje beings z bazy danych na podstawie unikalnego soul_hash"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

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
                    being.created_at = row['created_at']
                    if 'updated_at' in row:
                        being.updated_at = row['updated_at']
                    beings.append(being)
                if not beings:
                    beings = [None]
            return {"success": True, "beings": beings}
        except Exception as e:
            print(f"❌ Error loading beings by soul hash: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_last_by_soul_hash(soul_hash: str) -> dict:
        """Ładuje beings z bazy danych na podstawie unikalnego soul_hash"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

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
                    being.created_at = row['created_at']
                    beings.append(being)
                if not beings:
                    beings = [None]
            return {"success": True, "beings": beings}
        except Exception as e:
            print(f"❌ Error loading beings by soul hash: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_all() -> dict:
        """Ładuje wszystkie beings z bazy danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                # Force fresh statement plan if cached plan is invalid
                try:
                    query = """
                        SELECT * FROM beings
                        ORDER BY created_at DESC
                    """
                    rows = await conn.fetch(query)
                except Exception as e:
                    if "cached statement plan is invalid" in str(e).lower():
                        print("🔄 Cached statement plan invalid, forcing reset...")
                        # Reset connection and try again
                        await conn.execute("DEALLOCATE ALL")
                        rows = await conn.fetch(query)
                    else:
                        raise e

                Being = get_being_class()
                beings: List['Being'] = []
                for row in rows:
                    being = Being()
                    being.ulid = row['ulid']
                    being.soul_hash = row['soul_hash']
                    being.alias = row['alias']
                    being.created_at = row['created_at']
                    # Add table_type if it exists
                    if 'table_type' in row:
                        being.table_type = row['table_type']
                    beings.append(being)
                if not beings:
                    beings = []  # Return empty list instead of [None]
            print(f"✅ BeingRepository.load_all returning {len(beings)} beings")
            return {"success": True, "beings": beings}
        except Exception as e:
            print(f"❌ Error loading all beings: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_all_by_alias(alias: str) -> dict:
        """Ładuje beings z bazy danych na podstawie aliasu"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

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
                    being.created_at = row['created_at']
                    beings.append(being)
                if not beings:
                    beings = [None]
            return {"success": True, "beings": beings}
        except Exception as e:
            print(f"❌ Error loading beings by alias: {e}")
            return {"success": False, "error": str(e)}

class DynamicRepository:
    """Repository dla dynamicznych pól w souls"""

    @staticmethod
    async def insert_data_transaction(being, genotype: Dict[str, Any]) -> bool:
        """Zapisuje dynamiczne pola w transakcji"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return False

        async with pool.acquire() as conn:
            async with conn.transaction():
                # wpisuje being
                await BeingRepository.save(being)

                attributes = genotype.get("attributes", {})

                # przygotuj tabele
                tables_to_create = process_genotype_for_tables(genotype)
                for table_info in tables_to_create:
                    table_hash = table_info['table_hash']
                    table_name = table_info['table_name']
                    column_def = table_info['column_def']
                    index = table_info['index']
                    foreign_key = table_info['foreign_key']
                    unique = table_info['unique']

                    # Sprawdź, czy tabela istnieje i zbuduj ją, jeśli nie
                    result = await Postgre_db.ensure_table(
                        conn, table_hash=table_hash, table_name=table_name, column_def=column_def, index=index, foreign_key=foreign_key, unique=unique
                    )

                    if result.get("status") == "error":
                        print(f"❌ Error creating table {table_name}: {result.get('error')}")
                        return False
                # iteruje po atrybutach i zapisuje je w odpowiednich tabelach
                for attr_name, attr_meta in attributes.items():

                    # parsuje typ atrybutu
                    parsed = parse_py_type(attr_name, attr_meta)
                    build_result = build_table_name(parsed)
                    if len(build_result) == 5:
                        table_name, column_def, index, foreign_key, unique = build_result
                    else:
                        # Handle case where build_table_name returns different number of values
                        table_name, column_def = build_result[:2]
                        index = False
                        foreign_key = False
                        unique = {}


                    # Sprawdź, czy tabela istnieje i zbuduj ją, jeśli nie
                    result = await Postgre_db.ensure_table(
                        conn, table_name, table_name, column_def, index, foreign_key, unique
                    )

                    import ulid
                    _ulid = ulid.ulid()

                    if result.get("status") != "error":
                        query = f"""
                            INSERT INTO {table_name} (ulid, being_ulid, soul_hash, key, value)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (being_ulid, key) DO UPDATE SET
                                value = EXCLUDED.value,
                                modified_at = CURRENT_TIMESTAMP
                        """
                        # pobiera atrybut z being
                        being_data = getattr(being, attr_name, None)
                        value = json.dumps(being_data) if parsed["requires_serialization"] else being_data

                        # wstawia dane do tabeli
                        if value is None:
                            print(f"🔍 No value for attribute {attr_name} in being data.")
                            continue
                        await conn.execute(query, _ulid, being.ulid, being.soul_hash, attr_name, value)

                return True

    @staticmethod
    async def load_values(being, key_list: List[str], genotype: dict) -> Optional[Dict[str, Any]]:
        """Ładuje dynamiczne pola dla danego being"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return None

        async with pool.acquire() as conn:
            result = {}
            attributes = genotype.get("attributes", {})
            async with conn.transaction():
                for key in key_list:
                    #odszukaj nazwę tabeli na podstawie genotype attributes
                    parsed = parse_py_type(key, attributes.get(key, {}))
                    table_name, column_def, index, foreign_key, unique = build_table_name(parsed)
                    # Ensure the table exists before querying
                    await Postgre_db.ensure_table(
                        conn, table_name=table_name, column_def=column_def, index=index, foreign_key=foreign_key, unique=unique
                    )
                    # Pobiera dane z dynamicznej tabeli
                    query = f"""
                        SELECT value FROM {table_name}
                        WHERE being_ulid = $1 AND key = $2
                    """
                    row = await conn.fetchrow(query, being.ulid, key)


                    result[key] = json.loads(row['value']) if parsed["requires_serialization"] else (row['value'] if row else None)
            if result:
                for key, value in result.items():
                    if value is not None:
                        setattr(being, key, value)

    @staticmethod
    async def load_full_table(being, key_list: List[str], genotype: dict) -> Optional[Dict[str, Any]]:
        """Wczytuje całą tabelę dynamicznych pól dla danego being"""
        pool = await Postgre_db.get_db_pool()
        if not pool:
            return None

        async with pool.acquire() as conn:
            result = {}
            attributes = genotype.get("attributes", {})
            async with conn.transaction():
                for key in key_list:
                    #odszukaj nazwę tabeli na podstawie genotype attributes
                    parsed = parse_py_type(key, attributes.get(key, {}))
                    table_name, column_def, index, foreign_key, unique = build_table_name(parsed)
                    # Ensure the table exists before querying
                    await Postgre_db.ensure_table(
                        conn, table_name=table_name, column_def=column_def, index=index, foreign_key=foreign_key, unique=unique
                    )
                    # Pobiera dane z dynamicznej tabeli
                    query = f"""
                        SELECT * FROM {table_name}
                        WHERE being_ulid = $1 AND key = $2
                    """
                    rows = await conn.fetch(query, being.ulid, key)

                    for row in rows:
                        value = json.loads(row['value']) if parsed["requires_serialization"] else row['value']
                        result[row['key']] = value
            return result if result else None


class RelationRepository:
    """Repository pattern dla operacji na relations w bazie danych"""

    @staticmethod
    async def save(relation) -> dict:
        """Zapisuje relację do bazy danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    INSERT INTO relations (ulid, soul_hash, alias, source_ulid, target_ulid)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (ulid) DO UPDATE SET
                        soul_hash = EXCLUDED.soul_hash,
                        alias = EXCLUDED.alias,
                        source_ulid = EXCLUDED.source_ulid,
                        target_ulid = EXCLUDED.target_ulid,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING created_at, updated_at
                """
                result = await conn.fetchrow(query,
                    relation.ulid,
                    relation.soul_hash,
                    relation.alias,
                    relation.source_ulid,
                    relation.target_ulid
                )
                if result:
                    relation.created_at = result['created_at']
                    relation.updated_at = result['updated_at']

            return {"success": True, "relation": relation}
        except Exception as e:
            print(f"❌ Error saving relation: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_by_ulid(ulid: str) -> dict:
        """Ładuje relację z bazy danych na podstawie ULID"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM relations WHERE ulid = $1
                """
                row = await conn.fetchrow(query, ulid)
                if row:
                    # Import tutaj aby uniknąć circular imports
                    from database.models.relation import Relation
                    relation = Relation()
                    relation.ulid = row['ulid']
                    relation.soul_hash = row['soul_hash']
                    relation.alias = row['alias']
                    relation.source_ulid = row['source_ulid']
                    relation.target_ulid = row['target_ulid']
                    relation.created_at = row['created_at']
                    relation.updated_at = row['updated_at']
                    return {"success": True, "relation": relation}
                else:
                    return {"success": False, "relation": None}
        except Exception as e:
            print(f"❌ Error loading relation by ulid: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_all_by_soul_hash(soul_hash: str) -> dict:
        """Ładuje wszystkie relacje z bazy danych na podstawie soul_hash"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM relations
                    WHERE soul_hash = $1
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, soul_hash)
                from database.models.relation import Relation
                relations = []
                for row in rows:
                    relation = Relation()
                    relation.ulid = row['ulid']
                    relation.soul_hash = row['soul_hash']
                    relation.alias = row['alias']
                    relation.source_ulid = row['source_ulid']
                    relation.target_ulid = row['target_ulid']
                    relation.created_at = row['created_at']
                    relation.updated_at = row['updated_at']
                    relations.append(relation)

            return {"success": True, "relations": relations}
        except Exception as e:
            print(f"❌ Error loading relations by soul hash: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_all() -> dict:
        """Ładuje wszystkie relacje z bazy danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM relations
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query)
                from database.models.relation import Relation
                relations = []
                for row in rows:
                    relation = Relation()
                    relation.ulid = row['ulid']
                    relation.soul_hash = row['soul_hash']
                    relation.alias = row['alias']
                    relation.source_ulid = row['source_ulid']
                    relation.target_ulid = row['target_ulid']
                    relation.created_at = row['created_at']
                    relation.updated_at = row['updated_at']
                    relations.append(relation)

            return {"success": True, "relations": relations}
        except Exception as e:
            print(f"❌ Error loading all relations: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def load_by_being(being_ulid: str) -> dict:
        """Ładuje wszystkie relacje dla danego being"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM relations
                    WHERE source_ulid = $1 OR target_ulid = $1
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query, being_ulid)
                from database.models.relation import Relation
                relations = []
                for row in rows:
                    relation = Relation()
                    relation.ulid = row['ulid']
                    relation.soul_hash = row['soul_hash']
                    relation.alias = row['alias']
                    relation.source_ulid = row['source_ulid']
                    relation.target_ulid = row['target_ulid']
                    relation.created_at = row['created_at']
                    relation.updated_at = row['updated_at']
                    relations.append(relation)

            return {"success": True, "relations": relations}
        except Exception as e:
            print(f"❌ Error loading relations by being: {e}")
            return {"success": False, "error": str(e)}