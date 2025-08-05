
"""
Namespace Manager - Handles isolated database instances
"""

import asyncio
import hashlib
from typing import Dict, List, Optional, Any
from ..core.luxdb import LuxDB


class NamespaceManager:
    """
    Manages multiple isolated LuxDB namespaces
    Each namespace has its own set of tables with prefixed names
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config
        self.namespaces: Dict[str, LuxDB] = {}
        self._master_db: Optional[LuxDB] = None
        
    async def initialize(self):
        """Initialize the namespace manager"""
        # Create master database connection for namespace management
        self._master_db = LuxDB(**self.db_config)
        await self._master_db.initialize()
        
        # Create namespaces table
        await self._setup_namespace_tables()
        
        # Load existing namespaces
        await self._load_existing_namespaces()
    
    async def close(self):
        """Close all database connections"""
        for db in self.namespaces.values():
            await db.close()
        if self._master_db:
            await self._master_db.close()
    
    async def _setup_namespace_tables(self):
        """Create tables for namespace management"""
        pool = await self._master_db.connection_manager.get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS luxdb_namespaces (
                    namespace_id VARCHAR(255) PRIMARY KEY,
                    namespace_hash CHAR(64) UNIQUE NOT NULL,
                    config JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_namespaces_hash ON luxdb_namespaces (namespace_hash);
                CREATE INDEX IF NOT EXISTS idx_namespaces_created ON luxdb_namespaces (created_at);
            """)
    
    async def _load_existing_namespaces(self):
        """Load existing namespaces from database"""
        pool = await self._master_db.connection_manager.get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT namespace_id FROM luxdb_namespaces")
            for row in rows:
                namespace_id = row['namespace_id']
                await self._create_namespace_database(namespace_id)
    
    def _generate_namespace_hash(self, namespace_id: str) -> str:
        """Generate unique hash for namespace"""
        return hashlib.sha256(f"luxdb_ns_{namespace_id}".encode()).hexdigest()
    
    async def _create_namespace_database(self, namespace_id: str) -> LuxDB:
        """Create database connection for namespace"""
        if namespace_id in self.namespaces:
            return self.namespaces[namespace_id]
        
        # Create namespaced database instance
        db = NamespacedLuxDB(namespace_id, **self.db_config)
        await db.initialize()
        
        self.namespaces[namespace_id] = db
        return db
    
    async def create_namespace(self, namespace_id: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create new namespace"""
        if namespace_id in self.namespaces:
            raise ValueError(f"Namespace {namespace_id} already exists")
        
        namespace_hash = self._generate_namespace_hash(namespace_id)
        config = config or {}
        
        # Save namespace to master database
        pool = await self._master_db.connection_manager.get_pool()
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO luxdb_namespaces (namespace_id, namespace_hash, config)
                VALUES ($1, $2, $3)
            """, namespace_id, namespace_hash, config)
        
        # Create namespace database
        db = await self._create_namespace_database(namespace_id)
        
        return {
            "namespace_id": namespace_id,
            "namespace_hash": namespace_hash,
            "config": config,
            "status": "created"
        }
    
    async def delete_namespace(self, namespace_id: str) -> Dict[str, Any]:
        """Delete namespace and all its data"""
        if namespace_id not in self.namespaces:
            raise ValueError(f"Namespace {namespace_id} not found")
        
        # Close database connection
        await self.namespaces[namespace_id].close()
        del self.namespaces[namespace_id]
        
        # Drop all namespace tables
        pool = await self._master_db.connection_manager.get_pool()
        async with pool.acquire() as conn:
            # Get namespace prefix
            prefix = f"ns_{namespace_id}_"
            
            # Drop all tables with namespace prefix
            tables_result = await conn.fetch("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' AND tablename LIKE $1
            """, f"{prefix}%")
            
            for table_row in tables_result:
                table_name = table_row['tablename']
                await conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
            
            # Remove from namespaces table
            await conn.execute(
                "DELETE FROM luxdb_namespaces WHERE namespace_id = $1",
                namespace_id
            )
        
        return {"namespace_id": namespace_id, "status": "deleted"}
    
    async def list_namespaces(self) -> List[str]:
        """List all available namespaces"""
        return list(self.namespaces.keys())
    
    async def get_namespace_info(self, namespace_id: str) -> Dict[str, Any]:
        """Get information about namespace"""
        if namespace_id not in self.namespaces:
            raise ValueError(f"Namespace {namespace_id} not found")
        
        db = self.namespaces[namespace_id]
        health = await db.health_check()
        
        pool = await self._master_db.connection_manager.get_pool()
        async with pool.acquire() as conn:
            info = await conn.fetchrow("""
                SELECT namespace_hash, config, created_at, updated_at
                FROM luxdb_namespaces WHERE namespace_id = $1
            """, namespace_id)
        
        return {
            "namespace_id": namespace_id,
            "namespace_hash": info['namespace_hash'],
            "config": info['config'],
            "created_at": info['created_at'].isoformat(),
            "updated_at": info['updated_at'].isoformat(),
            "health": health
        }
    
    async def get_database(self, namespace_id: str) -> LuxDB:
        """Get database connection for namespace"""
        if namespace_id not in self.namespaces:
            raise ValueError(f"Namespace {namespace_id} not found")
        return self.namespaces[namespace_id]


class NamespacedLuxDB(LuxDB):
    """
    LuxDB instance with namespaced table names
    """
    
    def __init__(self, namespace_id: str, **kwargs):
        super().__init__(**kwargs)
        self.namespace_id = namespace_id
        self.table_prefix = f"ns_{namespace_id}_"
    
    async def _setup_core_tables(self) -> None:
        """
        Create namespaced core tables
        """
        pool = await self.connection_manager.get_pool()
        async with pool.acquire() as conn:
            # Enable extensions
            await conn.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;
                CREATE EXTENSION IF NOT EXISTS pgcrypto;
            """)
            
            # Namespaced souls table
            souls_table = f"{self.table_prefix}souls"
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {souls_table} (
                    soul_hash CHAR(64) PRIMARY KEY,
                    global_ulid CHAR(26) NOT NULL,
                    alias VARCHAR(255),
                    genotype JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(alias)
                );
                
                CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}souls_genotype ON {souls_table} USING gin (genotype);
                CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}souls_alias ON {souls_table} (alias);
                CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}souls_created_at ON {souls_table} (created_at);
            """)
            
            # Namespaced beings table
            beings_table = f"{self.table_prefix}beings"
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {beings_table} (
                    ulid CHAR(26) PRIMARY KEY,
                    soul_hash CHAR(64) NOT NULL,
                    alias VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (soul_hash) REFERENCES {souls_table}(soul_hash)
                );
                
                CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}beings_soul_hash ON {beings_table} (soul_hash);
                CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}beings_created_at ON {beings_table} (created_at);
                CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}beings_updated_at ON {beings_table} (updated_at);
                CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}beings_alias ON {beings_table} (alias);
            """)
            
            # Namespaced relationships table
            relationships_table = f"{self.table_prefix}relationships"
            await conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {relationships_table} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    source_ulid CHAR(26) NOT NULL,
                    target_ulid CHAR(26) NOT NULL,
                    relation_type VARCHAR(100) NOT NULL DEFAULT 'connection',
                    strength FLOAT DEFAULT 1.0,
                    metadata JSONB DEFAULT '{{}}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_ulid) REFERENCES {beings_table}(ulid) ON DELETE CASCADE,
                    FOREIGN KEY (target_ulid) REFERENCES {beings_table}(ulid) ON DELETE CASCADE
                );
                
                CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}relationships_source ON {relationships_table} (source_ulid);
                CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}relationships_target ON {relationships_table} (target_ulid);
                CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}relationships_type ON {relationships_table} (relation_type);
                CREATE INDEX IF NOT EXISTS idx_{self.table_prefix}relationships_strength ON {relationships_table} (strength);
                CREATE UNIQUE INDEX IF NOT EXISTS idx_{self.table_prefix}unique_relationship 
                ON {relationships_table} (source_ulid, target_ulid, relation_type);
            """)
    
    def get_table_name(self, base_name: str) -> str:
        """Get namespaced table name"""
        return f"{self.table_prefix}{base_name}"
