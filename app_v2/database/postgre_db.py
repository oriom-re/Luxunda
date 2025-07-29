
import asyncpg

db_pool = None

class Postgre_db:
    """Klasa do zarządzania połączeniem z bazą danych PostgreSQL"""
    
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
    async def ensure_table(conn: asyncpg.Connection, table_name: str, column_def: str, index: bool, foreign_key: bool) -> dict:
        """Zapewnia istnienie tabeli w bazie danych PostgreSQL"""
        try:
            # Sprawdź, czy tabela istnieje
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = $1
                )
            """, table_name)

            if exists:
                print(f"Table {table_name} already exists, skipping creation.")
                return {"status": "exists", "table_name": table_name}

            # Buduj zapytanie do stworzenia tabeli
            create_table_sql = f"""
                CREATE TABLE {table_name} (
                    ulid CHAR(26) NOT NULL,
                    being_ulid CHAR(26) NOT NULL,
                    soul_hash CHAR(64) NOT NULL,
                    key TEXT NOT NULL,
                    {column_def},
                    PRIMARY KEY (being_ulid, key),
                    FOREIGN KEY (being_ulid) REFERENCES beings(ulid),
                    FOREIGN KEY (soul_hash) REFERENCES souls(soul_hash),
                    -- Dodaj kolumny do śledzenia czasu utworzenia i modyfikacji
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """

            # Transakcja z utworzeniem tabeli i indeksów
            async with conn.transaction():
                await conn.execute(create_table_sql)
                if index:
                    index_name = f"idx_{table_name}_key"
                    await conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} (key)")
                if foreign_key:
                    # Jeśli chcesz FK na value, dodaj osobny constraint
                    fk_name = f"fk_{table_name}_value"
                    try:
                        await conn.execute(f"""
                            ALTER TABLE {table_name}
                            ADD CONSTRAINT {fk_name} FOREIGN KEY (value) REFERENCES beings(ulid)
                        """)
                    except asyncpg.exceptions.DuplicateObjectError:
                        # constraint już istnieje
                        pass

            print(f"Table {table_name} created successfully.")
            return {"status": "created", "table_name": table_name}
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")
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

                print("✅ Tabele PostgreSQL utworzone")
        except Exception as e:
            print(f"❌ Błąd tworzenia tabel PostgreSQL: {e}")


