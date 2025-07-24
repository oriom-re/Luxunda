from app.beings.prototyp.base_v2 import Being
import asyncpg
import aiosqlite
from app.database import get_db_pool, set_db_pool
from app.core.gen_loader_from_file import load_all_gen_files_as_souls

async def setup_postgresql_tables():
    """Tworzy tabele w PostgreSQL"""
    db_pool = await get_db_pool()
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


async def init_database():
    """Inicjalizuje połączenie z bazą danych i tworzy tabele"""
    try:
        pool = await asyncpg.create_pool(
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
        set_db_pool(pool)
        print("Połączono z PostgreSQL")
        await setup_postgresql_tables()
    except Exception as e:
        print(f"Nie udało się połączyć z PostgreSQL: {e}")
        print("Używam SQLite jako fallback")
        pool = await aiosqlite.connect('luxos.db')
        set_db_pool(pool)
        print("Połączono z SQLite")

    # Auto-rejestruj funkcje w OpenAI Function Caller
    # if openai_function_caller:
    #     registered_count = await openai_function_caller.auto_register_function_beings()
    #     print(f"Zarejestrowano {registered_count} funkcji w OpenAI Function Caller")

if __name__ == "__main__":
    # bootstrap the application
    import asyncio
    from app.core.dependencies import load_and_run_gen

    async def main():
        print("Inicjalizacja bazy danych...")
        await init_database()
        print("Baza danych zainicjalizowana.")

        print("Ładowanie plików gen jako souls...")
        await load_all_gen_files_as_souls("app/gen_files")
        print("Pliki gen załadowane.")

        db_pool = await get_db_pool()
        print("Uruchamianie gen_logger...")
        modul = await load_and_run_gen("gen_logger", db_pool)
        if modul:
            print("Uruchomiono gen_logger.")
        else:
            print("Nie udało się uruchomić gen_logger.")
        # podtrzymanie działania loggera
        while True:
            await asyncio.sleep(1)

    asyncio.run(main())