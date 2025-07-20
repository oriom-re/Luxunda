import asyncio
import asyncpg
import aiosqlite
import os
import logging
from typing import Optional, Union, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Menedżer połączeń z bazą danych"""

    def __init__(self, db_type: str = "sqlite", connection_pool=None, connection=None):
        self.db_type = db_type
        self.connection = connection
        self.pool = connection_pool
        self.external_connection = connection is not None or connection_pool is not None

    async def initialize(self) -> bool:
        """Inicjalizuje połączenie z bazą danych"""
        try:
            # Jeśli mamy zewnętrzne połączenie, używamy go
            if self.external_connection:
                logger.info(f"🔗 Używam zewnętrznego połączenia {self.db_type}")
                if self.db_type == "sqlite" and self.connection:
                    await self.setup_sqlite_tables()
                return True

            # Tworzymy własne połączenie
            if self.db_type == "postgresql":
                # Konfiguracja PostgreSQL
                logger.info("🐘 Inicjalizacja PostgreSQL...")
                # Tu będzie kod połączenia z PostgreSQL
                pass
            else:
                # Fallback na SQLite
                logger.info("📁 Inicjalizacja SQLite...")
                self.connection = await aiosqlite.connect('luxos_kernel.db')
                await self.setup_sqlite_tables()

            logger.info(f"✅ Baza danych {self.db_type} zainicjalizowana")
            return True

        except Exception as e:
            logger.error(f"❌ Błąd inicjalizacji bazy danych: {e}")
            return False

    async def setup_sqlite_tables(self):
        """Tworzy tabele SQLite dla kernela"""
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS kernel_state (
                id INTEGER PRIMARY KEY,
                kernel_soul TEXT NOT NULL,
                state_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                user_id TEXT PRIMARY KEY,
                fingerprint TEXT NOT NULL,
                connection_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.connection.commit()

    async def close(self):
        """Zamyka połączenie z bazą danych"""
        if self.connection and not self.external_connection:
            await self.connection.close()
            logger.info("🔒 Połączenie z bazą danych zamknięte")

    def get_pool(self):
        """Zwraca pool połączeń"""
        return self.pool

    def is_postgresql(self) -> bool:
        """Sprawdza czy używa PostgreSQL"""
        return self.db_type == "postgresql"

    def is_sqlite(self) -> bool:
        """Sprawdza czy używa SQLite"""
        return self.db_type == "sqlite"