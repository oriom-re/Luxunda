"""
Główna klasa LuxDB do zarządzania połączeniem i inicjalizacji systemu.
"""

import asyncio
from typing import Optional, Dict, Any, List
from .connection import ConnectionManager
from ..models.soul import Soul
from ..models.being import Being
# Relationships moved to legacy system

class LuxDB:
    """
    Główna klasa LuxDB do zarządzania bazą danych.

    Przykład:
        ```python
        db = LuxDB(
            host='localhost',
            port=5432,
            user='user',
            password='password',
            database='luxdb'
        )
        await db.initialize()
        ```
    """

    def __init__(
        self,
        host: str = None,
        port: int = 5432,
        user: str = None,
        password: str = None,
        database: str = None,
        min_connections: int = 1,
        max_connections: int = 5,
        use_existing_pool: bool = True,
        **kwargs
    ):
        """
        Inicjalizuje LuxDB z parametrami połączenia.

        Args:
            host: Adres serwera PostgreSQL (opcjonalny jeśli use_existing_pool=True)
            port: Port serwera PostgreSQL
            user: Nazwa użytkownika
            password: Hasło
            database: Nazwa bazy danych
            min_connections: Minimalna liczba połączeń w puli
            max_connections: Maksymalna liczba połączeń w puli
            use_existing_pool: Czy użyć istniejącej puli z database.postgre_db
        """
        self.use_existing_pool = use_existing_pool

        if not use_existing_pool and host:
            self.connection_manager = ConnectionManager(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                min_connections=min_connections,
                max_connections=max_connections,
                **kwargs
            )
        else:
            self.connection_manager = None

        self._initialized = False
        self.pool = None

    async def initialize(self) -> None:
        """
        Inicjalizuje połączenie z bazą danych i tworzy podstawowe tabele.
        """
        if self._initialized:
            return

        if self.use_existing_pool:
            # Użyj istniejącej puli z database.postgre_db
            from database.postgre_db import Postgre_db
            self.pool = await Postgre_db.get_db_pool()
        else:
            # Użyj własnego connection manager
            await self.connection_manager.initialize()
            self.pool = await self.connection_manager.get_pool()

        await self._setup_core_tables()
        self._initialized = True

    async def close(self) -> None:
        """
        Zamyka wszystkie połączenia z bazą danych.
        """
        if self.connection_manager:
            await self.connection_manager.close()
        # Nie zamykamy zewnętrznej puli, bo może być używana przez inne komponenty
        self._initialized = False
        self.pool = None

    async def _setup_core_tables(self) -> None:
        """
        Tworzy podstawowe tabele systemu LuxDB.
        """
        if not self.pool:
            if self.connection_manager:
                self.pool = await self.connection_manager.get_pool()
            else:
                from database.postgre_db import Postgre_db
                self.pool = await Postgre_db.get_db_pool()

        async with self.pool.acquire() as conn:
            # Włącz rozszerzenia PostgreSQL
            await conn.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;
                CREATE EXTENSION IF NOT EXISTS pgcrypto;
            """)

            # Tabela souls (genotypów)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS souls (
                    soul_hash CHAR(64) PRIMARY KEY,
                    global_ulid CHAR(26) NOT NULL,
                    alias VARCHAR(255),
                    genotype JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(alias)
                );

                CREATE INDEX IF NOT EXISTS idx_souls_genotype ON souls USING gin (genotype);
                CREATE INDEX IF NOT EXISTS idx_souls_alias ON souls (alias);
                CREATE INDEX IF NOT EXISTS idx_souls_created_at ON souls (created_at);
            """)

            # Tabela beings (bytów)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS beings (
                    ulid CHAR(26) PRIMARY KEY,
                    soul_hash CHAR(64) NOT NULL,
                    alias VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (soul_hash) REFERENCES souls(soul_hash)
                );

                CREATE INDEX IF NOT EXISTS idx_beings_soul_hash ON beings (soul_hash);
                CREATE INDEX IF NOT EXISTS idx_beings_created_at ON beings (created_at);
                CREATE INDEX IF NOT EXISTS idx_beings_updated_at ON beings (updated_at);
                CREATE INDEX IF NOT EXISTS idx_beings_alias ON beings (alias);
            """)

            # Tabela relationships (relacji)
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

                CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships (source_ulid);
                CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships (target_ulid);
                CREATE INDEX IF NOT EXISTS idx_relationships_type ON relationships (relation_type);
                CREATE INDEX IF NOT EXISTS idx_relationships_strength ON relationships (strength);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_relationship 
                ON relationships (source_ulid, target_ulid, relation_type);
            """)

    async def health_check(self) -> Dict[str, Any]:
        """
        Sprawdza stan połączenia z bazą danych.

        Returns:
            Słownik z informacjami o stanie bazy danych
        """
        try:
            if not self.pool:
                if self.connection_manager:
                    self.pool = await self.connection_manager.get_pool()
                else:
                    from database.postgre_db import Postgre_db
                    self.pool = await Postgre_db.get_db_pool()

            async with self.pool.acquire() as conn:
                # Sprawdź połączenie
                result = await conn.fetchval("SELECT 1")

                # Sprawdź liczbę souls i beings
                souls_count = await conn.fetchval("SELECT COUNT(*) FROM souls")
                beings_count = await conn.fetchval("SELECT COUNT(*) FROM beings")
                relationships_count = await conn.fetchval("SELECT COUNT(*) FROM relationships")

                return {
                    "status": "healthy",
                    "connection": "ok" if result == 1 else "error",
                    "souls_count": souls_count,
                    "beings_count": beings_count,
                    "relationships_count": relationships_count,
                    "pool_size": self.pool.get_size() if hasattr(self.pool, 'get_size') else "unknown",
                    "initialized": self._initialized
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "initialized": self._initialized
            }

    def __repr__(self):
        return f"LuxDB(initialized={self._initialized})"

    async def __aenter__(self):
        """Context manager support."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager support."""
        await self.close()