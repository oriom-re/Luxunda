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
                    'statement_cache_size': '0',  # Wyłącz cache statementów
                    'plan_cache_mode': 'force_custom_plan'
                }
            )
            await Postgre_db.setup_tables()  # Upewnij się, że tabele są utworzone
            print("✅ Pula połączeń do bazy PostgreSQL zainicjalizowana")
        return db_pool

    @staticmethod
    async def ensure_table(conn: asyncpg.Connection, table_hash: str, table_name:str, column_def: str, index: bool, foreign_key: bool, unique: dict) -> dict:
        """Zapewnia istnienie tabeli w bazie danych PostgreSQL"""
        try:

            # Sprawdź, czy tabela istnieje
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = $1
                )
            """, table_hash)

            if exists:
                print(f"Table {table_hash} already exists, skipping creation.")
                return {"status": "exists", "table_name": table_hash}

            # Transakcja z utworzeniem tabeli i indeksów
            async with conn.transaction():
                await conn.execute(create_query_table(table_hash, table_name, column_def))
                if index:
                    query = create_index(table_hash)
                    await conn.execute(query)
                if foreign_key:
                    # Jeśli chcesz FK na value, dodaj osobny constraint
                    try:
                        query = create_foreign_key(table_hash)
                        await conn.execute(query)
                    except asyncpg.exceptions.DuplicateObjectError:
                        # constraint już istnieje
                        pass
                if unique:
                    unique_sql = create_unique(table_hash)
                    await conn.execute(unique_sql)

            print(f"Table {table_hash} created successfully.")
            return {"status": "created", "table_name": table_hash}
        except Exception as e:
            print(f"Error creating table {table_hash}: {e}")
            return {"status": "error", "error": str(e)}


    @staticmethod
    async def setup_tables():
        """Tworzy tabele w PostgreSQL"""
        global db_pool
        if not db_pool:
            print("❌ Baza danych nie jest zainicjalizowana")
            return

        try:
            async with db_pool.acquire() as conn:

                await conn.execute("""
                        CREATE EXTENSION IF NOT EXISTS vector;
                        CREATE EXTENSION IF NOT EXISTS pgcrypto;
                """)

                await conn.execute("""  
                        CREATE TABLE IF NOT EXISTS souls (
                            soul_hash CHAR(64) PRIMARY KEY,
                            global_ulid CHAR(26) NOT NULL,
                            alias VARCHAR(255),
                            genotype JSONB NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );

                        -- indexy
                        CREATE INDEX IF NOT EXISTS idx_souls_genotype ON souls USING gin (genotype);
                        CREATE INDEX IF NOT EXISTS idx_souls_alias ON souls (alias);
                        CREATE INDEX IF NOT EXISTS idx_souls_created_at ON souls (created_at);
                """)

                await conn.execute("""
                        CREATE TABLE IF NOT EXISTS beings (
                            ulid CHAR(26) PRIMARY KEY,
                            soul_hash CHAR(64) NOT NULL,
                            alias VARCHAR(255),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (soul_hash) REFERENCES souls(soul_hash)
                        );
                        -- indexy
                        CREATE INDEX IF NOT EXISTS idx_beings_soul_hash ON beings (soul_hash);
                        CREATE INDEX IF NOT EXISTS idx_beings_created_at ON beings (created_at);
                        CREATE INDEX IF NOT EXISTS idx_beings_updated_at ON beings (updated_at);
                        CREATE INDEX IF NOT EXISTS idx_beings_alias ON beings (alias);
                """)

                # Tradycyjna tabela relacji dla MVP
                await conn.execute("""
                        CREATE TABLE IF NOT EXISTS relationships (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            source_ulid CHAR(26) NOT NULL,
                            target_ulid CHAR(26) NOT NULL,
                            relation_type VARCHAR(100) NOT NULL DEFAULT 'connection',
                            strength FLOAT DEFAULT 1.0,
                            metadata JSONB DEFAULT '{}',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (source_ulid) REFERENCES beings(ulid) ON DELETE CASCADE,
                            FOREIGN KEY (target_ulid) REFERENCES beings(ulid) ON DELETE CASCADE
                        );
                        -- indexy dla wydajności
                        CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships (source_ulid);
                        CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships (target_ulid);
                        CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships (relation_type);
                        CREATE INDEX IF NOT EXISTS idx_relationships_strength ON relationships (strength);
                        CREATE INDEX IF NOT EXISTS idx_relationships_created_at ON relationships (created_at);
                        CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_relationship ON relationships (source_ulid, target_ulid, relation_type);
                """)

                print("✅ Tabele PostgreSQL utworzone")
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