
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
                    'statement_cache_size': '0'  # Wyłącz cache statementów
                }
            )
            await Postgre_db.setup_tables()  # Upewnij się, że tabele są utworzone
            print("✅ Pula połączeń do bazy PostgreSQL zainicjalizowana")
        return db_pool
    
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
                    CREATE TABLE IF NOT EXISTS souls (
                        uid UUID PRIMARY KEY,
                        genesis JSONB NOT NULL,
                        attributes JSONB NOT NULL,
                        memories JSONB NOT NULL,
                        self_awareness JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS relationships (
                        uid UUID PRIMARY KEY,
                        source_uid UUID NOT NULL,
                        target_uid UUID NOT NULL,
                        attributes JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Indeksy
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_souls_genesis ON souls USING gin (genesis)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_souls_attributes ON souls USING gin (attributes)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_souls_memories ON souls USING gin (memories)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_souls_self_awareness ON souls USING gin (self_awareness)")

                await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_attributes ON relationships USING gin (attributes)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships (source_uid)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships (target_uid)") 
                print("✅ Tabele PostgreSQL utworzone")
        except Exception as e:
            print(f"❌ Błąd tworzenia tabel PostgreSQL: {e}")