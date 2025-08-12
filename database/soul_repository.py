from typing import Dict, Any, Optional, List
import json
from database.postgre_db import Postgre_db
from core.globals import Globals
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from luxdb.models.being import Being
    from luxdb.models.soul import Soul

def get_soul_class():
    from luxdb.models.soul import Soul
    return Soul

def get_being_class():
    from luxdb.models.being import Being
    return Being

class SoulRepository:
    """Repository dla operacji na souls w podejściu JSONB"""

    @staticmethod
    async def load_by_alias(alias: str) -> dict:
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
                    from luxdb.models.soul import Soul
                    soul = Soul(
                        genotype=row['genotype'],
                        alias=row['alias'],
                        soul_hash=row['soul_hash'],
                        global_ulid=row['global_ulid']
                    )
                    soul.created_at = row['created_at']
                    return {"success": True, "soul": soul}
                else:
                    return {"success": False, "error": "Soul not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    

    @staticmethod
    async def get_all() -> dict:
        """Pobiera wszystkie souls z bazy danych"""
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
            return {"success": True, "souls": souls}
        except Exception as e:
            print(f"❌ Error getting all souls: {e}")
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
            return {"success": False}
        except Exception as e:
            print(f"❌ Error loading soul by ulid: {e}")
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
            return {"success": True, "souls": souls}
        except Exception as e:
            print(f"❌ Error loading souls by alias: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def create_soul_indexes(conn, soul_hash: str, genotype: Dict):
        """Tworzy indeksy specyficzne dla duszy na podstawie genotypu JSONB"""
        try:
            attributes = genotype.get("attributes", {})

            for attr_name, attr_meta in attributes.items():
                if attr_meta.get("indexed", False):
                    index_type = attr_meta.get("index_type", "gin")
                    index_name = f"idx_{soul_hash[:12]}_{attr_name}"

                    if index_type == "gin":
                        await conn.execute(f"""
                            CREATE INDEX IF NOT EXISTS {index_name}
                            ON beings USING gin ((data->>'{attr_name}'))
                            WHERE soul_hash = '{soul_hash}'
                        """)
                    elif index_type == "btree":
                        await conn.execute(f"""
                            CREATE INDEX IF NOT EXISTS {index_name}
                            ON beings USING btree ((data->>'{attr_name}'))
                            WHERE soul_hash = '{soul_hash}'
                        """)
                    elif index_type == "composite":
                        fields = attr_meta.get("composite_fields", [attr_name])
                        field_expressions = [f"(data->>'{field}')" for field in fields]
                        await conn.execute(f"""
                            CREATE INDEX IF NOT EXISTS {index_name}
                            ON beings ({', '.join(field_expressions)})
                            WHERE soul_hash = '{soul_hash}'
                        """)
                    elif index_type == "vector" and attr_name == "vector_embedding":
                        await conn.execute(f"""
                            CREATE INDEX IF NOT EXISTS {index_name}_vector
                            ON beings USING ivfflat (vector_embedding vector_cosine_ops)
                            WHERE soul_hash = '{soul_hash}'
                        """)

                    print(f"✅ Created index {index_name} for soul {soul_hash[:8]}...")

        except Exception as e:
            print(f"❌ Error creating indexes for soul {soul_hash[:8]}: {e}")

    

class BeingRepository:
    """Repository dla operacji na beings w podejściu JSONB"""

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
    async def save_jsonb(being: 'Being') -> dict:
        """Zapisuje being do bazy danych w podejściu JSONB"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    INSERT INTO beings (ulid, soul_hash, alias, data, vector_embedding, table_type)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (ulid) DO UPDATE SET
                        alias = EXCLUDED.alias,
                        data = EXCLUDED.data,
                        vector_embedding = EXCLUDED.vector_embedding,
                        table_type = EXCLUDED.table_type,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING created_at, updated_at
                """

                # Determine table_type
                table_type = 'being'
                
                # Spróbuj pobrać Soul dla określenia typu
                try:
                    soul = await being.get_soul() if hasattr(being, 'get_soul') else None
                    if soul:
                        soul_alias = getattr(soul, 'alias', None)
                        genotype = getattr(soul, 'genotype', {})
                        genesis_type = genotype.get('genesis', {}).get('type', None)

                        if soul_alias in ['user_profile', 'ai_agent']:
                            table_type = 'soul'
                        elif genesis_type == 'relation' or soul_alias == 'basic_relation':
                            table_type = 'relation'
                except Exception as e:
                    print(f"⚠️ Nie można określić table_type dla Being {being.ulid}: {e}")
                    # Zostaw domyślny 'being'

                result = await conn.fetchrow(query,
                    being.ulid,
                    being.soul_hash,
                    being.alias,
                    json.dumps(being.data),
                    getattr(being, 'vector_embedding', None),
                    table_type
                )

                if result:
                    being.created_at = result['created_at']
                    being.updated_at = result['updated_at']

                return {"success": True}
        except Exception as e:
            print(f"❌ Error saving being: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def update_vector(ulid: str, embedding: List[float]) -> dict:
        """Aktualizuje embedding wektorowy"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    UPDATE beings
                    SET vector_embedding = $2, updated_at = CURRENT_TIMESTAMP
                    WHERE ulid = $1
                """
                await conn.execute(query, ulid, embedding)
                return {"success": True}
        except Exception as e:
            print(f"❌ Error updating vector embedding: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def search_by_jsonb_data(query: Dict[str, Any], soul_hash: str = None) -> List:
        """Wyszukuje beings na podstawie danych JSONB"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return []

            async with pool.acquire() as conn:
                # Buduje zapytanie JSONB
                conditions = []
                params = []
                param_count = 1

                for key, value in query.items():
                    conditions.append(f"data->>'{key}' = ${param_count}")
                    params.append(str(value))
                    param_count += 1

                where_clause = " AND ".join(conditions)
                if soul_hash:
                    where_clause += f" AND soul_hash = ${param_count}"
                    params.append(soul_hash)

                sql_query = f"""
                    SELECT * FROM beings
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                """

                rows = await conn.fetch(sql_query, *params)
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
            print(f"❌ Error searching beings by JSONB data: {e}")
            return []

    @staticmethod
    async def find_similar_beings(embedding: List[float], limit: int = 10, threshold: float = 0.8) -> List:
        """Znajduje podobne beings na podstawie embeddingu wektorowego"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
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
                    being.data = json.loads(row['data']) if row['data'] else {}
                    being.vector_embedding = list(row['vector_embedding']) if row['vector_embedding'] else None
                    being.created_at = row['created_at']
                    being.updated_at = row['updated_at']
                    return {"success": True, "being": being}
            return {"success": False}
        except Exception as e:
            print(f"❌ Error loading being by ulid: {e}")
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
                    being.data = json.loads(row['data']) if row['data'] else {}
                    being.vector_embedding = list(row['vector_embedding']) if row['vector_embedding'] else None
                    being.created_at = row['created_at']
                    being.updated_at = row['updated_at']
                    beings.append(being)
            return {"success": True, "beings": beings}
        except Exception as e:
            print(f"❌ Error loading beings by soul hash: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def get_all() -> dict:
        """Pobiera wszystkie beings z bazy danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    SELECT * FROM beings
                    ORDER BY created_at DESC
                """
                rows = await conn.fetch(query)
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
            print(f"✅ BeingRepository.get_all returning {len(beings)} beings")
            return {"success": True, "beings": beings}
        except Exception as e:
            print(f"❌ Error getting all beings: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e)}

    # Legacy compatibility methods
    @staticmethod
    async def save(being: 'Being') -> dict:
        """Legacy compatibility - delegates to save_jsonb"""
        return await BeingRepository.save_jsonb(being)

    @staticmethod
    async def load(being: 'Being') -> dict:
        """Legacy compatibility"""
        return await BeingRepository.load_by_ulid(being.ulid)

    @staticmethod
    async def load_last_by_soul_hash(soul_hash: str) -> dict:
        """Legacy compatibility"""
        result = await BeingRepository.load_all_by_soul_hash(soul_hash)
        beings = result.get('beings', [])
        if beings:
            return {"success": True, "beings": [beings[0]]}
        return {"success": False, "beings": []}

    @staticmethod
    async def load_all() -> dict:
        """Legacy compatibility - delegates to get_all"""
        return await BeingRepository.get_all()

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
                    being.data = json.loads(row['data']) if row['data'] else {}
                    being.vector_embedding = list(row['vector_embedding']) if row['vector_embedding'] else None
                    being.created_at = row['created_at']
                    being.updated_at = row['updated_at']
                    beings.append(being)
            return {"success": True, "beings": beings}
        except Exception as e:
            print(f"❌ Error loading beings by alias: {e}")
            return {"success": False, "error": str(e)}

# Legacy DynamicRepository for backward compatibility
class DynamicRepository:
    """Legacy repository - now delegates to JSONB approach"""

    @staticmethod
    async def insert_data_transaction(being, genotype: Dict[str, Any]) -> bool:
        """Legacy compatibility - delegates to JSONB save"""
        try:
            result = await BeingRepository.save_jsonb(being)
            return result.get("success", False)
        except Exception as e:
            print(f"❌ Error in legacy insert_data_transaction: {e}")
            return False

    @staticmethod
    async def load_values(being, key_list: List[str], genotype: dict) -> Optional[Dict[str, Any]]:
        """Legacy compatibility - loads from JSONB data"""
        if hasattr(being, 'data') and being.data:
            result = {}
            for key in key_list:
                if key in being.data:
                    result[key] = being.data[key]
                    setattr(being, key, being.data[key])
            return result if result else None
        return None

    @staticmethod
    async def load_full_table(being, key_list: List[str], genotype: dict) -> Optional[Dict[str, Any]]:
        """Legacy compatibility - returns JSONB data"""
        if hasattr(being, 'data') and being.data:
            return {key: being.data.get(key) for key in key_list if key in being.data}
        return None

class RelationRepository:
    """Repository pattern dla operacji na relations w podejściu JSONB"""

    @staticmethod
    async def save(relation) -> dict:
        """Zapisuje relację do bazy danych w podejściu JSONB"""
        try:
            pool = await Postgre_db.get_db_pool()
            if not pool:
                return {"success": False}

            async with pool.acquire() as conn:
                query = """
                    INSERT INTO relations (ulid, soul_hash, alias, source_ulid, target_ulid, data, relation_type, strength)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (ulid) DO UPDATE SET
                        soul_hash = EXCLUDED.soul_hash,
                        alias = EXCLUDED.alias,
                        source_ulid = EXCLUDED.source_ulid,
                        target_ulid = EXCLUDED.target_ulid,
                        data = EXCLUDED.data,
                        relation_type = EXCLUDED.relation_type,
                        strength = EXCLUDED.strength,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING created_at, updated_at
                """

                relation_data = getattr(relation, 'data', {})
                relation_type = getattr(relation, 'relation_type', 'connection')
                strength = getattr(relation, 'strength', 1.0)

                result = await conn.fetchrow(query,
                    relation.ulid,
                    relation.soul_hash,
                    relation.alias,
                    relation.source_ulid,
                    relation.target_ulid,
                    json.dumps(relation_data),
                    relation_type,
                    strength
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
                    from database.models.relation import Relation
                    relation = Relation()
                    relation.ulid = row['ulid']
                    relation.soul_hash = row['soul_hash']
                    relation.alias = row['alias']
                    relation.source_ulid = row['source_ulid']
                    relation.target_ulid = row['target_ulid']
                    relation.data = json.loads(row['data']) if row['data'] else {}
                    relation.relation_type = row['relation_type']
                    relation.strength = row['strength']
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
                    relation.data = json.loads(row['data']) if row['data'] else {}
                    relation.relation_type = row['relation_type']
                    relation.strength = row['strength']
                    relation.created_at = row['created_at']
                    relation.updated_at = row['updated_at']
                    relations.append(relation)

            return {"success": True, "relations": relations}
        except Exception as e:
            print(f"❌ Error loading relations by soul hash: {e}")
            return {"success": False, "error": str(e)}

    @staticmethod
    async def get_all() -> dict:
        """Pobiera wszystkie relacje z bazy danych"""
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
                    relation.data = json.loads(row['data']) if row['data'] else {}
                    relation.relation_type = row['relation_type']
                    relation.strength = row['strength']
                    relation.created_at = row['created_at']
                    relation.updated_at = row['updated_at']
                    relations.append(relation)

            return {"success": True, "relations": relations}
        except Exception as e:
            print(f"❌ Error getting all relations: {e}")
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
                    relation.data = json.loads(row['data']) if row['data'] else {}
                    relation.relation_type = row['relation_type']
                    relation.strength = row['strength']
                    relation.created_at = row['created_at']
                    relation.updated_at = row['updated_at']
                    relations.append(relation)

            return {"success": True, "relations": relations}
        except Exception as e:
            print(f"❌ Error loading relations by being: {e}")
            return {"success": False, "error": str(e)}