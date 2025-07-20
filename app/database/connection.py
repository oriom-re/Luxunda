
import asyncio
import asyncpg
import aiosqlite
import os
import logging
from typing import Optional, Union

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Menedżer połączeń z bazą danych"""
    
    def __init__(self):
        self.pool: Optional[Union[asyncpg.Pool, aiosqlite.Connection]] = None
        self.db_type: str = "unknown"
    
    async def initialize(self) -> bool:
        """Inicjalizuje połączenie z bazą danych"""
        try:
            # Próba połączenia z PostgreSQL
            self.pool = await asyncpg.create_pool(
                host='ep-odd-tooth-a2zcp5by-pooler.eu-central-1.aws.neon.tech',
                port=5432,
                user='neondb_owner',
                password='npg_aY8K9pijAnPI',
                database='neondb',
                min_size=1,
                max_size=10,
                server_settings={
                    'statement_cache_size': '0'
                }
            )
            self.db_type = "postgresql"
            logger.info("✅ Połączono z PostgreSQL")
            await self.setup_postgresql_tables()
            return True
            
        except Exception as e:
            logger.warning(f"Nie udało się połączyć z PostgreSQL: {e}")
            logger.info("Używam SQLite jako fallback")
            
            # Fallback na SQLite
            try:
                self.pool = await aiosqlite.connect('luxos.db')
                self.db_type = "sqlite"
                logger.info("✅ Połączono z SQLite")
                await self.setup_sqlite_tables()
                return True
                
            except Exception as e:
                logger.error(f"Nie udało się połączyć z SQLite: {e}")
                return False
    
    async def setup_postgresql_tables(self):
        """Tworzy tabele w PostgreSQL"""
        if self.db_type != "postgresql" or not self.pool:
            return
        
        async with self.pool.acquire() as conn:
            # Tabela base_beings
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS base_beings (
                    soul UUID PRIMARY KEY,
                    genesis JSONB NOT NULL,
                    attributes JSONB NOT NULL,
                    memories JSONB NOT NULL,
                    self_awareness JSONB NOT NULL,
                    binary_data BYTEA,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela relationships
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id UUID PRIMARY KEY,
                    source_soul UUID NOT NULL,
                    target_soul UUID NOT NULL,
                    genesis JSONB NOT NULL,
                    attributes JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indeksy
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_genesis ON base_beings USING gin (genesis)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_attributes ON base_beings USING gin (attributes)")
    
    async def setup_sqlite_tables(self):
        """Tworzy tabele w SQLite"""
        if self.db_type != "sqlite" or not self.pool:
            return
        
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS base_beings (
                soul TEXT PRIMARY KEY,
                genesis TEXT NOT NULL,
                attributes TEXT NOT NULL,
                memories TEXT NOT NULL,
                self_awareness TEXT NOT NULL,
                binary_data BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.pool.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                source_soul TEXT NOT NULL,
                target_soul TEXT NOT NULL,
                genesis TEXT NOT NULL,
                attributes TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self.pool.commit()
    
    async def close(self):
        """Zamyka połączenie z bazą danych"""
        if self.pool:
            if self.db_type == "postgresql":
                await self.pool.close()
            else:
                await self.pool.close()
            logger.info("🔌 Zamknięto połączenie z bazą danych")
    
    def get_pool(self):
        """Zwraca pool połączeń"""
        return self.pool
    
    def is_postgresql(self) -> bool:
        """Sprawdza czy używa PostgreSQL"""
        return self.db_type == "postgresql"
    
    def is_sqlite(self) -> bool:
        """Sprawdza czy używa SQLite"""
        return self.db_type == "sqlite"
