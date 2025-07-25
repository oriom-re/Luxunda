import asyncpg
import aiosqlite
from app_v2.database.soul_repository import SoulRepository

async def setup_postgresql_tables():
    """Tworzy tabele w PostgreSQL"""
    db_pool = await SoulRepository.get_db_pool()
    async with db_pool.acquire() as conn:
        # Tabela base_beings
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

        # Tabela relationships
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


async def setup_sqlite_tables(db_pool):
    """Tworzy tabele w SQLite"""
    try:
        # Tabela souls
        await db_pool.execute("""
            CREATE TABLE IF NOT EXISTS souls (
                uid TEXT PRIMARY KEY,
                genesis TEXT NOT NULL,
                attributes TEXT NOT NULL,
                memories TEXT NOT NULL,
                self_awareness TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela relationships
        await db_pool.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                uid TEXT PRIMARY KEY,
                source_uid TEXT NOT NULL,
                target_uid TEXT NOT NULL,
                attributes TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db_pool.commit()
        print("✅ Tabele SQLite utworzone")
        
    except Exception as e:
        print(f"❌ Błąd tworzenia tabel SQLite: {e}")

async def init_database():
    """Inicjalizuje połączenie z bazą danych i tworzy tabele"""
    try:
        # Dla testów używamy SQLite
        print("🔄 Inicjalizacja SQLite dla testów...")
        pool = await aiosqlite.connect('app_v2_test.db')
        await SoulRepository.set_db_pool(pool)
        await setup_sqlite_tables(pool)
        print("✅ Połączono z SQLite")
        return True
    except Exception as e:
        print(f"❌ Nie udało się zainicjalizować bazy danych: {e}")
        return False