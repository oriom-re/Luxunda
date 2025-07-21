
import sqlite3
import aiosqlite
from typing import Dict, Any, List, Optional
from app.genetics.base_gene import BaseGene, GeneActivationContext
from app.beings.base import BaseBeing
from datetime import datetime
import json
import asyncio
import os


class DatabaseGene(BaseGene):
    """Gen bazy danych SQLite z możliwością pracy w pamięci"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db_connection: Optional[aiosqlite.Connection] = None
        self.db_path: Optional[str] = None
        self.is_memory_db = True
        self.sync_interval = 300  # 5 minut
        self.last_sync: Optional[datetime] = None
        self.parent_db_soul: Optional[str] = None
        self.sync_task: Optional[asyncio.Task] = None
    
    @property
    def gene_type(self) -> str:
        return 'database_sqlite'
    
    @property
    def required_energy(self) -> int:
        return 25
    
    @property
    def compatibility_tags(self) -> List[str]:
        return ['communication', 'ai_model', 'embedding', 'data_storage']
    
    async def activate(self, host: BaseBeing, context: GeneActivationContext) -> bool:
        """Aktywuj gen bazy danych"""
        if host.energy_level < self.required_energy:
            return False
        
        self.host_being = host
        self.activation_context = context
        
        # Utwórz bazę w pamięci
        if self.is_memory_db:
            self.db_path = ":memory:"
        else:
            self.db_path = f"gene_db_{self.gene_id}.sqlite"
        
        try:
            self.db_connection = await aiosqlite.connect(self.db_path)
            
            # Utwórz podstawowe tabele
            await self._create_tables()
            
            # Załaduj dane z nadrzędnej bazy jeśli istnieje
            if self.parent_db_soul:
                await self._load_from_parent()
            
            self.is_active = True
            host.energy_level -= self.required_energy
            
            # Uruchom zadanie synchronizacji
            if self.parent_db_soul:
                self.sync_task = asyncio.create_task(self._sync_loop())
            
            await self._record_memory('activation', {
                'db_path': self.db_path,
                'is_memory': self.is_memory_db,
                'parent_db': self.parent_db_soul
            })
            
            print(f"Gen bazy danych aktywowany: {self.db_path}")
            return True
            
        except Exception as e:
            await self._record_memory('activation_error', {'error': str(e)})
            return False
    
    async def deactivate(self) -> bool:
        """Dezaktywuj gen"""
        if self.sync_task:
            self.sync_task.cancel()
            
        if self.db_connection:
            # Ostatnia synchronizacja przed zamknięciem
            if self.parent_db_soul:
                await self._sync_to_parent()
            
            await self.db_connection.close()
            self.db_connection = None
        
        self.is_active = False
        await self._record_memory('deactivation', {'reason': 'manual'})
        return True
    
    async def express(self, stimulus: Dict[str, Any]) -> Dict[str, Any]:
        """Wyraź funkcję bazy danych"""
        if not self.is_active or not self.db_connection:
            return {'error': 'Database gene not active'}
        
        action = stimulus.get('action', 'query')
        
        try:
            if action == 'query':
                return await self._execute_query(stimulus)
            elif action == 'insert':
                return await self._insert_data(stimulus)
            elif action == 'update':
                return await self._update_data(stimulus)
            elif action == 'delete':
                return await self._delete_data(stimulus)
            elif action == 'sync':
                return await self._manual_sync(stimulus)
            elif action == 'get_stats':
                return await self._get_stats()
            else:
                return {'error': f'Unknown action: {action}'}
                
        except Exception as e:
            await self._record_memory('expression_error', {
                'action': action,
                'error': str(e),
                'stimulus': stimulus
            })
            return {'error': str(e)}
    
    async def _create_tables(self):
        """Utwórz podstawowe tabele"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS gene_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                data_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS gene_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_type TEXT,
                data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sync_type TEXT,
                records_count INTEGER,
                sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN
            )
            """
        ]
        
        for table_sql in tables:
            await self.db_connection.execute(table_sql)
        
        await self.db_connection.commit()
    
    async def _execute_query(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wykonaj zapytanie SELECT"""
        query = params.get('query', 'SELECT * FROM gene_data LIMIT 10')
        
        cursor = await self.db_connection.execute(query)
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        result = [dict(zip(columns, row)) for row in rows]
        
        await self.evolve_autonomy({'autonomy_boost': 1, 'reason': 'successful_query'})
        
        return {
            'status': 'success',
            'data': result,
            'row_count': len(result)
        }
    
    async def _insert_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wstaw dane"""
        key = params.get('key')
        value = params.get('value')
        data_type = params.get('data_type', 'string')
        
        if not key:
            return {'error': 'Key required'}
        
        # Serialize value if it's not a string
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
            data_type = 'json'
        
        await self.db_connection.execute(
            "INSERT OR REPLACE INTO gene_data (key, value, data_type, updated_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
            (key, value, data_type)
        )
        await self.db_connection.commit()
        
        await self.evolve_autonomy({'autonomy_boost': 1, 'reason': 'data_inserted'})
        
        return {'status': 'inserted', 'key': key}
    
    async def _update_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Aktualizuj dane"""
        key = params.get('key')
        value = params.get('value')
        
        if not key:
            return {'error': 'Key required'}
        
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        cursor = await self.db_connection.execute(
            "UPDATE gene_data SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
            (value, key)
        )
        await self.db_connection.commit()
        
        return {'status': 'updated', 'key': key, 'rows_affected': cursor.rowcount}
    
    async def _delete_data(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Usuń dane"""
        key = params.get('key')
        
        if not key:
            return {'error': 'Key required'}
        
        cursor = await self.db_connection.execute(
            "DELETE FROM gene_data WHERE key = ?",
            (key,)
        )
        await self.db_connection.commit()
        
        return {'status': 'deleted', 'key': key, 'rows_affected': cursor.rowcount}
    
    async def _sync_loop(self):
        """Pętla synchronizacji w tle"""
        while self.is_active:
            try:
                await asyncio.sleep(self.sync_interval)
                if self.is_active:
                    await self._sync_to_parent()
            except asyncio.CancelledError:
                break
            except Exception as e:
                await self._record_memory('sync_error', {'error': str(e)})
    
    async def _sync_to_parent(self) -> Dict[str, Any]:
        """Synchronizuj do nadrzędnej bazy"""
        if not self.parent_db_soul:
            return {'error': 'No parent database configured'}
        
        try:
            # Pobierz wszystkie dane do synchronizacji
            cursor = await self.db_connection.execute(
                "SELECT * FROM gene_data WHERE updated_at > ?",
                (self.last_sync.isoformat() if self.last_sync else '1970-01-01',)
            )
            rows = await cursor.fetchall()
            
            # Tu byłaby logika wysłania do nadrzędnej bazy
            # Np. przez communication_gene lub bezpośrednio do PostgreSQL
            
            sync_count = len(rows)
            self.last_sync = datetime.now()
            
            # Zapisz log synchronizacji
            await self.db_connection.execute(
                "INSERT INTO sync_log (sync_type, records_count, success) VALUES (?, ?, ?)",
                ('to_parent', sync_count, True)
            )
            await self.db_connection.commit()
            
            await self._record_memory('sync_completed', {
                'direction': 'to_parent',
                'records': sync_count,
                'timestamp': self.last_sync.isoformat()
            })
            
            return {'status': 'synced', 'records_count': sync_count}
            
        except Exception as e:
            await self._record_memory('sync_error', {'error': str(e)})
            return {'error': str(e)}
    
    async def _load_from_parent(self):
        """Załaduj dane z nadrzędnej bazy"""
        # Tu byłaby logika ładowania z nadrzędnej bazy
        await self._record_memory('parent_load', {'parent_soul': self.parent_db_soul})
    
    async def _manual_sync(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ręczna synchronizacja"""
        return await self._sync_to_parent()
    
    async def _get_stats(self) -> Dict[str, Any]:
        """Pobierz statystyki bazy"""
        cursor = await self.db_connection.execute("SELECT COUNT(*) FROM gene_data")
        data_count = (await cursor.fetchone())[0]
        
        cursor = await self.db_connection.execute("SELECT COUNT(*) FROM gene_memories")
        memory_count = (await cursor.fetchone())[0]
        
        cursor = await self.db_connection.execute("SELECT COUNT(*) FROM sync_log WHERE success = 1")
        successful_syncs = (await cursor.fetchone())[0]
        
        return {
            'data_records': data_count,
            'memory_records': memory_count,
            'successful_syncs': successful_syncs,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'is_memory_db': self.is_memory_db,
            'autonomy_level': self.autonomy_level
        }
    
    async def _record_memory(self, memory_type: str, data: Dict[str, Any]):
        """Zapisz pamięć genu"""
        memory = {
            'type': memory_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'gene_id': self.gene_id
        }
        
        self.gene_memories.append(memory)
        
        # Zapisz też do bazy SQLite jeśli aktywna
        if self.db_connection:
            try:
                await self.db_connection.execute(
                    "INSERT INTO gene_memories (memory_type, data) VALUES (?, ?)",
                    (memory_type, json.dumps(data))
                )
                await self.db_connection.commit()
            except:
                pass  # Ignore errors during memory recording
        
        # Jeśli host istnieje, dodaj też do jego pamięci
        if self.host_being:
            self.host_being.memories.append(memory)
