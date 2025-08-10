
"""
Manager połączeń z bazą danych PostgreSQL.
"""

import asyncpg
from typing import Optional

class ConnectionManager:
    """
    Zarządza połączeniami z bazą danych PostgreSQL.
    """
    
    def __init__(
        self,
        host: str,
        port: int = 5432,
        user: str = None,
        password: str = None,
        database: str = None,
        min_connections: int = 1,
        max_connections: int = 5,
        **kwargs
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.kwargs = kwargs
        self._pool: Optional[asyncpg.Pool] = None
        
    async def initialize(self) -> None:
        """
        Inicjalizuje pulę połączeń.
        """
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                min_size=self.min_connections,
                max_size=self.max_connections,
                server_settings={
                    'statement_cache_size': '0',
                    'plan_cache_mode': 'force_custom_plan'
                },
                **self.kwargs
            )
            
    async def get_pool(self) -> asyncpg.Pool:
        """
        Zwraca pulę połączeń.
        """
        if self._pool is None:
            await self.initialize()
        return self._pool
        
    async def close(self) -> None:
        """
        Zamyka wszystkie połączenia.
        """
        if self._pool:
            await self._pool.close()
            self._pool = None
