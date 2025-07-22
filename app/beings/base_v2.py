
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import uuid
import json
from datetime import datetime
import aiosqlite
import asyncio
import pickle
import base64
from abc import ABC, abstractmethod

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

class BaseGene(ABC):
    """Bazowa klasa dla genów"""
    
    def __init__(self, gene_id: Optional[str] = None):
        self.gene_id = gene_id or str(uuid.uuid4())
        self.is_active = False
        self.host_being = None
        self.gene_data = {}
    
    @property
    @abstractmethod
    def gene_type(self) -> str:
        """Typ genu"""
        pass
    
    @property
    @abstractmethod
    def required_energy(self) -> int:
        """Wymagana energia do aktywacji"""
        pass
    
    @abstractmethod
    async def activate(self, host_being, context: Dict[str, Any]) -> bool:
        """Aktywuj gen"""
        pass
    
    @abstractmethod
    async def deactivate(self) -> bool:
        """Dezaktywuj gen"""
        pass
    
    @abstractmethod
    async def express(self, stimulus: Dict[str, Any]) -> Dict[str, Any]:
        """Wyraź funkcję genu"""
        pass

class PostgreSQLGene(BaseGene):
    """Gen PostgreSQL - rozszerza możliwości bazy danych"""
    
    @property
    def gene_type(self) -> str:
        return "postgresql"
    
    @property
    def required_energy(self) -> int:
        return 50
    
    async def activate(self, host_being, context: Dict[str, Any]) -> bool:
        if host_being.energy_level < self.required_energy:
            return False
        
        try:
            import asyncpg
            # Tutaj można dodać konfigurację PostgreSQL
            self.connection_string = context.get('postgresql_url', 'postgresql://user:pass@localhost/luxos')
            self.pool = None  # Będzie inicjalizowane przy pierwszym użyciu
            
            self.host_being = host_being
            self.is_active = True
            host_being.energy_level -= self.required_energy
            
            # Zapisz aktywację w historii
            await host_being.add_memory({
                'type': 'gene_activation',
                'gene_type': self.gene_type,
                'gene_id': self.gene_id,
                'energy_cost': self.required_energy
            })
            
            print(f"PostgreSQL gen aktywowany w being {host_being.soul}")
            return True
            
        except ImportError:
            print("asyncpg nie jest dostępne - PostgreSQL gen nie może być aktywowany")
            return False
    
    async def deactivate(self) -> bool:
        if self.pool:
            await self.pool.close()
        self.is_active = False
        return True
    
    async def express(self, stimulus: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_active:
            return {'error': 'PostgreSQL gene not active'}
        
        action = stimulus.get('action')
        
        if action == 'backup_to_sqlite':
            # Stwórz backup całej bazy PostgreSQL do SQLite jako BLOB
            return await self._backup_to_sqlite()
        elif action == 'migrate_beings':
            # Migruj byty z SQLite do PostgreSQL
            return await self._migrate_beings_to_postgresql()
        elif action == 'get_stats':
            return await self._get_postgresql_stats()
        
        return {'error': 'Unknown action'}
    
    async def _backup_to_sqlite(self) -> Dict[str, Any]:
        """Backup PostgreSQL do SQLite jako BLOB"""
        try:
            # Przykładowa implementacja - można rozszerzyć
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'beings_count': 0,  # Tu by była rzeczywista liczba
                'relationships_count': 0
            }
            
            # Serialize backup jako BLOB
            backup_blob = pickle.dumps(backup_data)
            backup_b64 = base64.b64encode(backup_blob).decode('utf-8')
            
            # Zapisz do SQLite
            await self.host_being.db_pool.execute("""
                INSERT INTO gene_backups (gene_id, gene_type, backup_data, created_at)
                VALUES (?, ?, ?, ?)
            """, (self.gene_id, self.gene_type, backup_b64, datetime.now().isoformat()))
            
            await self.host_being.db_pool.commit()
            
            return {
                'status': 'backup_created',
                'size_bytes': len(backup_blob),
                'backup_id': self.gene_id
            }
        except Exception as e:
            return {'error': f'Backup failed: {str(e)}'}
    
    async def _migrate_beings_to_postgresql(self) -> Dict[str, Any]:
        """Migruj byty z SQLite do PostgreSQL"""
        return {'status': 'migration_planned', 'note': 'Feature to be implemented'}
    
    async def _get_postgresql_stats(self) -> Dict[str, Any]:
        """Statystyki PostgreSQL"""
        return {
            'gene_active': self.is_active,
            'connection_available': self.pool is not None,
            'backup_capability': True
        }

@dataclass
class Soul:
    soul: str
    genesis: Dict[str, Any]
    attributes: Dict[str, Any]
    memories: List[Dict[str, Any]]
    self_awareness: Dict[str, Any]
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.soul:
            self.soul = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'soul': self.soul,
            'genesis': self.genesis,
            'attributes': self.attributes,
            'memories': self.memories,
            'self_awareness': self.self_awareness,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Being(Soul):
    """Główny byt z możliwością dynamicznego ładowania genów"""
    
    def __init__(self, *args, db_path: str = "luxos.db", **kwargs):
        super().__init__(*args, **kwargs)
        self.db_path = db_path
        self.db_pool = None
        self.task_queue = asyncio.Queue()
        self.active_genes: Dict[str, BaseGene] = {}
        self.available_genes = {
            'postgresql': PostgreSQLGene
        }

    @property
    def energy_level(self) -> int:
        return self.attributes.get('energy_level', 100)

    @energy_level.setter
    def energy_level(self, value: int):
        self.attributes['energy_level'] = value

    async def start(self):
        """Startuje byt: init bazy, pętla, itp."""
        try:
            print(f"[{self.soul}] Inicjalizacja...")
            self.db_pool = await aiosqlite.connect(self.db_path)
            await self.setup_sqlite_tables()
            print("Tabele SQLite zostały utworzone.")
            
            # Załaduj siebie z bazy jeśli istnieje
            await self.load_self()
            
            self._main_loop_task = asyncio.create_task(self._main_loop())
            print(f"[{self.soul}] Being uruchomiony pomyślnie")
            
        except Exception as e:
            print(f"[{self.soul}] Błąd podczas inicjalizacji: {e}")

    async def stop(self):
        """Zatrzymuje byt i zamyka połączenia"""
        # Dezaktywuj wszystkie geny
        for gene in self.active_genes.values():
            await gene.deactivate()
        
        if self.db_pool:
            await self.db_pool.close()
        print(f"[{self.soul}] Being zatrzymany")

    async def _main_loop(self):
        """Główna pętla event loopa"""
        print(f"[{self.soul}] Pętla uruchomiona.")
        try:
            while True:
                task = await self.task_queue.get()
                await self._dispatch_task(task)
        except asyncio.CancelledError:
            print(f"[{self.soul}] Pętla zatrzymana.")

    async def _dispatch_task(self, task):
        try:
            if task['type'] == 'gene_action':
                await self._handle_gene_action(task)
            elif task['type'] == 'activate_gene':
                await self._activate_gene(task['gene_type'], task.get('context', {}))
            elif task['type'] == 'deactivate_gene':
                await self._deactivate_gene(task['gene_type'])
            else:
                print(f"[{self.soul}] Nieznany typ zadania: {task['type']}")
        except Exception as e:
            print(f"[{self.soul}] Błąd podczas dispatchu: {e}")

    async def _handle_gene_action(self, task):
        """Obsługuj akcję genu"""
        gene_type = task.get('gene_type')
        gene = self.active_genes.get(gene_type)
        
        if gene:
            result = await gene.express(task.get('stimulus', {}))
            print(f"[{self.soul}] Gen {gene_type} wynik: {result}")
        else:
            print(f"[{self.soul}] Gen {gene_type} nie jest aktywny")

    async def activate_gene(self, gene_type: str, context: Dict[str, Any] = None) -> bool:
        """Aktywuj gen"""
        if gene_type in self.active_genes:
            print(f"Gen {gene_type} już jest aktywny")
            return True
        
        if gene_type not in self.available_genes:
            print(f"Nieznany typ genu: {gene_type}")
            return False
        
        gene_class = self.available_genes[gene_type]
        gene = gene_class()
        
        success = await gene.activate(self, context or {})
        if success:
            self.active_genes[gene_type] = gene
            await self.save()  # Zapisz stan
        
        return success

    async def deactivate_gene(self, gene_type: str) -> bool:
        """Dezaktywuj gen"""
        if gene_type not in self.active_genes:
            return False
        
        gene = self.active_genes[gene_type]
        success = await gene.deactivate()
        if success:
            del self.active_genes[gene_type]
            await self.save()
        
        return success

    async def express_gene(self, gene_type: str, stimulus: Dict[str, Any]) -> Dict[str, Any]:
        """Wyraź gen"""
        gene = self.active_genes.get(gene_type)
        if gene:
            return await gene.express(stimulus)
        return {'error': f'Gene {gene_type} not active'}

    async def add_memory(self, memory: Dict[str, Any]):
        """Dodaj pamięć"""
        memory['timestamp'] = datetime.now().isoformat()
        self.memories.append(memory)
        # Ogranicz do ostatnich 1000 wspomnień
        if len(self.memories) > 1000:
            self.memories = self.memories[-1000:]

    async def setup_sqlite_tables(self):
        """Tworzy tabele w SQLite"""
        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS beings (
                soul TEXT PRIMARY KEY,
                genesis TEXT NOT NULL,
                attributes TEXT NOT NULL,
                memories TEXT NOT NULL,
                self_awareness TEXT NOT NULL,
                active_genes TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS gene_backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gene_id TEXT NOT NULL,
                gene_type TEXT NOT NULL,
                backup_data BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.db_pool.commit()

    async def save(self):
        """Zapisuje byt do bazy danych"""
        active_genes_data = {
            gene_type: {
                'gene_id': gene.gene_id,
                'is_active': gene.is_active,
                'gene_data': getattr(gene, 'gene_data', {})
            }
            for gene_type, gene in self.active_genes.items()
        }

        await self.db_pool.execute("""
            INSERT OR REPLACE INTO beings 
            (soul, genesis, attributes, memories, self_awareness, active_genes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(self.soul), 
            json.dumps(self.genesis, cls=DateTimeEncoder),
            json.dumps(self.attributes, cls=DateTimeEncoder),
            json.dumps(self.memories, cls=DateTimeEncoder),
            json.dumps(self.self_awareness, cls=DateTimeEncoder),
            json.dumps(active_genes_data, cls=DateTimeEncoder),
            datetime.now().isoformat()
        ))
        await self.db_pool.commit()

    async def load_self(self):
        """Ładuje swój stan z bazy danych"""
        cursor = await self.db_pool.execute(
            "SELECT * FROM beings WHERE soul = ?", (str(self.soul),)
        )
        row = await cursor.fetchone()
        
        if row:
            # Odtwórz stan z bazy
            self.genesis = json.loads(row[1]) if row[1] else self.genesis
            self.attributes = json.loads(row[2]) if row[2] else self.attributes
            self.memories = json.loads(row[3]) if row[3] else self.memories
            self.self_awareness = json.loads(row[4]) if row[4] else self.self_awareness
            
            # Odtwórz aktywne geny
            active_genes_data = json.loads(row[5]) if row[5] else {}
            for gene_type, gene_info in active_genes_data.items():
                if gene_type in self.available_genes:
                    gene_class = self.available_genes[gene_type]
                    gene = gene_class(gene_id=gene_info['gene_id'])
                    gene.gene_data = gene_info.get('gene_data', {})
                    # Geny będą reaktywowane przez użytkownika gdy będzie potrzeba
                    
            print(f"[{self.soul}] Stan załadowany z bazy danych")

# Przykład użycia
if __name__ == "__main__":
    async def main():
        # Stwórz nowy byt
        being = Being(
            soul="master_being_001",
            genesis={'type': 'master', 'name': 'LuxOS Master'},
            attributes={'energy_level': 100, 'version': '2.0'},
            memories=[],
            self_awareness={'purpose': 'Manage genetic ecosystem'}
        )
        
        await being.start()
        
        # Aktywuj gen PostgreSQL
        print("Aktywacja genu PostgreSQL...")
        success = await being.activate_gene('postgresql', {
            'postgresql_url': 'postgresql://localhost/luxos'
        })
        
        if success:
            print("Gen PostgreSQL aktywowany!")
            
            # Testuj funkcje genu
            result = await being.express_gene('postgresql', {
                'action': 'get_stats'
            })
            print("Stats:", result)
            
            # Stwórz backup
            backup_result = await being.express_gene('postgresql', {
                'action': 'backup_to_sqlite'
            })
            print("Backup:", backup_result)
        
        # Zapisz stan
        await being.save()
        print("Stan zapisany!")
        
        await being.stop()

    asyncio.run(main())
