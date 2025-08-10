# Adding the ensure_tables_exist method to the Postgre_db class and adjusting get_db_pool.
import asyncpg

from database.parser_table import create_foreign_key, parse_py_type, build_table_name, create_query_table, create_index, create_unique
db_pool = None

class Postgre_db:
    """Klasa do zarządzania połączeniem z bazą danych PostgreSQL"""

    def __init__(self):
        self.connection = None
        self.pool = None

    async def initialize(self):
        """Inicjalizacja połączenia z bazą danych"""
        try:
            await self.connect()
            print("✅ PostgreSQL połączenie zainicjalizowane")
        except Exception as e:
            print(f"❌ Błąd inicjalizacji PostgreSQL: {e}")
            raise

    @staticmethod
    async def get_db_pool():
        """Zwraca pulę połączeń do bazy danych PostgreSQL"""
        global db_pool
        if db_pool is None:
            print("🔄 Inicjalizacja puli połączeń do bazy PostgreSQL...")
            from asyncpg import create_pool
            db_pool = await create_pool(
                host='ep-odd-tooth-a2zcp5by-pooler.eu-central-1.aws.neon.tech',
                port=5432,
                user='neondb_owner',
                password='npg_aY8K9pijAnPI',
                database='neondb',
                min_size=1,
                max_size=5,
                server_settings={
                    'statement_cache_size': '0',
                    'plan_cache_mode': 'force_custom_plan',
                    'application_name': 'luxdb_jsonb'
                },
                command_timeout=30
            )
            await Postgre_db.setup_tables()
            print("✅ Pula połączeń do bazy PostgreSQL zainicjalizowana")
        return db_pool

    @staticmethod
    async def ensure_table(conn: asyncpg.Connection, table_hash: str, table_name:str, column_def: str, index: bool, foreign_key: bool, unique: dict) -> dict:
        """Zapewnia istnienie tabeli w bazie danych PostgreSQL (legacy compatibility)"""
        # Ta metoda pozostaje dla kompatybilności wstecznej
        return {"status": "skipped", "message": "JSONB approach does not use dynamic tables"}

    @staticmethod
    async def setup_tables():
        """Tworzy tabele w PostgreSQL dla podejścia JSONB"""
        global db_pool
        if not db_pool:
            print("❌ Baza danych nie jest zainicjalizowana")
            return

        try:
            async with db_pool.acquire() as conn:
                # Rozszerzenia PostgreSQL
                # Sprawdź czy extensions istnieją przed utworzeniem
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                except:
                    print("⚠️ Vector extension not available, skipping...")
                    
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
                except:
                    print("⚠️ Pgcrypto extension not available, skipping...")
                    
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS btree_gin;")
                except:
                    print("⚠️ Btree_gin extension not available, skipping...")

                # Tabela souls - bez zmian
                await conn.execute("""  
                    CREATE TABLE IF NOT EXISTS souls (
                        soul_hash CHAR(64) PRIMARY KEY,
                        global_ulid CHAR(26) NOT NULL,
                        alias VARCHAR(255),
                        genotype JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Indeksy dla souls
                    CREATE INDEX IF NOT EXISTS idx_souls_genotype ON souls USING gin (genotype);
                    CREATE INDEX IF NOT EXISTS idx_souls_alias ON souls (alias);
                    CREATE INDEX IF NOT EXISTS idx_souls_created_at ON souls (created_at);
                """)

                # Tabela beings - NOWA STRUKTURA Z JSONB
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS beings (
                        ulid CHAR(26) PRIMARY KEY,
                        soul_hash CHAR(64) NOT NULL,
                        alias VARCHAR(255),
                        data JSONB DEFAULT '{}',
                        vector_embedding vector(1536),
                        table_type VARCHAR(50) DEFAULT 'being',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (soul_hash) REFERENCES souls(soul_hash)
                    );

                    -- Główne indeksy dla beings
                    CREATE INDEX IF NOT EXISTS idx_beings_soul_hash ON beings (soul_hash);
                    CREATE INDEX IF NOT EXISTS idx_beings_data ON beings USING gin (data);
                    CREATE INDEX IF NOT EXISTS idx_beings_created_at ON beings (created_at);
                    CREATE INDEX IF NOT EXISTS idx_beings_updated_at ON beings (updated_at);
                    CREATE INDEX IF NOT EXISTS idx_beings_alias ON beings (alias);
                    CREATE INDEX IF NOT EXISTS idx_beings_table_type ON beings (table_type);

                    -- Indeks wektorowy
                    CREATE INDEX IF NOT EXISTS idx_beings_vector ON beings USING ivfflat (vector_embedding vector_cosine_ops)
                    WITH (lists = 100);
                """)

                # Tabela relations - NOWA STRUKTURA Z JSONB
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS relations (
                        ulid CHAR(26) PRIMARY KEY,
                        soul_hash CHAR(64) NOT NULL,
                        alias VARCHAR(255),
                        source_ulid CHAR(26),
                        target_ulid CHAR(26),
                        data JSONB DEFAULT '{}',
                        relation_type VARCHAR(100) DEFAULT 'connection',
                        strength FLOAT DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (soul_hash) REFERENCES souls(soul_hash),
                        FOREIGN KEY (source_ulid) REFERENCES beings(ulid) ON DELETE CASCADE,
                        FOREIGN KEY (target_ulid) REFERENCES beings(ulid) ON DELETE CASCADE
                    );

                    -- Indeksy dla relations
                    CREATE INDEX IF NOT EXISTS idx_relations_soul_hash ON relations (soul_hash);
                    CREATE INDEX IF NOT EXISTS idx_relations_source ON relations (source_ulid);
                    CREATE INDEX IF NOT EXISTS idx_relations_target ON relations (target_ulid);
                    CREATE INDEX IF NOT EXISTS idx_relations_data ON relations USING gin (data);
                    CREATE INDEX IF NOT EXISTS idx_relations_type ON relations (relation_type);
                    CREATE INDEX IF NOT EXISTS idx_relations_strength ON relations (strength);
                    CREATE INDEX IF NOT EXISTS idx_relations_created_at ON relations (created_at);
                    CREATE INDEX IF NOT EXISTS idx_relations_updated_at ON relations (updated_at);
                    CREATE INDEX IF NOT EXISTS idx_relations_alias ON relations (alias);
                """)

                # Tabela relationships - zachowana dla kompatybilności
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS relationships (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        source_ulid CHAR(26),
                        target_ulid CHAR(26),
                        source_id VARCHAR(64) NOT NULL,
                        target_id VARCHAR(64) NOT NULL,
                        source_type VARCHAR(20) DEFAULT 'being',
                        target_type VARCHAR(20) DEFAULT 'being',
                        relation_type VARCHAR(100) NOT NULL DEFAULT 'connection',
                        strength FLOAT DEFAULT 1.0,
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(source_id, target_id, relation_type)
                    );

                    -- Indeksy dla relationships
                    CREATE INDEX IF NOT EXISTS idx_relationships_source_id ON relationships (source_id);
                    CREATE INDEX IF NOT EXISTS idx_relationships_target_id ON relationships (target_id);
                    CREATE INDEX IF NOT EXISTS idx_relationships_source_type ON relationships (source_type);
                    CREATE INDEX IF NOT EXISTS idx_relationships_target_type ON relationships (target_type);
                    CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships (relation_type);
                    CREATE INDEX IF NOT EXISTS idx_relationships_strength ON relationships (strength);
                    CREATE INDEX IF NOT EXISTS idx_relationships_metadata ON relationships USING gin (metadata);
                    CREATE INDEX IF NOT EXISTS idx_relationships_created_at ON relationships (created_at);
                """)

                print("✅ Tabele PostgreSQL utworzone w podejściu JSONB")
        except Exception as e:
            print(f"❌ Błąd tworzenia tabel PostgreSQL: {e}")

    async def connect(self):
        """Łączy się z bazą danych PostgreSQL"""
        try:
            self.pool = await Postgre_db.get_db_pool()
            print("✅ Connected to PostgreSQL database")
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            raise