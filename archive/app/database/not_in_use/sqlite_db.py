import asyncpg
import aiosqlite
from app_v2.database.soul_repository import SoulRepository

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