import uuid
from app.beings.genotype import Genotype
import asyncpg
import aiosqlite
from app.database import get_db_pool, set_db_pool
from app.core.gen_loader_from_file import register_all_genotypes

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
        await register_all_genotypes("app/gen_files")
        print("Pliki gen załadowane.")

        print("🧪 Testowanie gen_logger jako demon genotypu...")
        
        # Test 1: Przez obiekt Genotype (główny test)
        genesis = {"name": "Lux"}
        attributes = {}
        memories = []
        self_awareness = {}
        uid = str(uuid.uuid4())
        
        lux = Genotype(uid=uid, genesis=genesis, attributes=attributes, 
                       memories=memories, self_awareness=self_awareness)
        lux.cxt = globals()  # Dostęp do globalnego kontekstu
        
        print("🚀 Uruchamianie genotypu jako demon...")
        await lux.load_and_run_genotype("gen_logger", call_init=True)
        
        if lux:
            print("✅ Demon genotypu uruchomiony!")
            print(f"🔍 Kontekst Lux zawiera: {len(lux.cxt)} elementów")
        
        # Test 2: Alternatywne uruchomienie (opcjonalne)
        print("🔄 Test alternatywnego uruchomienia...")
        modul = await load_and_run_gen("gen_logger")
        if modul:
            print("✅ Moduł gen_logger załadowany.")
        else:
            print("❌ Nie udało się załadować modułu gen_logger.")
        
        print("🔄 Demon działa w tle... (Ctrl+C aby zatrzymać)")
        try:
            while True:
                await asyncio.sleep(10)  # Zwiększony interwał dla czytelności logów
        except KeyboardInterrupt:
            print("\n🛑 Zatrzymywanie demona...")

    asyncio.run(main())