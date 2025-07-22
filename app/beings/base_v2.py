from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import uuid
import json
from datetime import datetime
import aiosqlite
import asyncio
from queue import Empty  # Dodanie importu dla obsługi wyjątku w multiprocessing


from multiprocessing import Process, Queue
from concurrent.futures import ProcessPoolExecutor

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

@dataclass
class Soul:
    soul: str
    genesis: Dict[str, Any]
    attributes: Dict[str, Any]
    memories: List[Dict[str, Any]]
    self_awareness: Dict[str, Any]
    created_at: Optional[datetime] = None

    # Inicjalizacja daty utworzenia, jeśli nie jest podana
    def __post_init__(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.now()
        if not self.soul:
            self.soul = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Zwraca reprezentację słownikową bytu."""
        return {
            'soul': self.soul,
            'genesis': self.genesis,
            'attributes': self.attributes,
            'memories': self.memories,
            'self_awareness': self.self_awareness,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        

class Being(Soul):
    db_pool: Optional[aiosqlite.Connection] = None

    def __init__(self, *args, db_path: str = "luxos.db", **kwargs):
        super().__init__(*args, **kwargs)
        self.db_path = db_path
        self.task_queue = asyncio.Queue()
        self.executor = ProcessPoolExecutor()

    async def start(self):
        """Startuje byt: init bazy, pętla, itp."""
        try:
            if hasattr(self, '_main_loop_task') and not self._main_loop_task.done():
                print(f"[{self.soul}] Pętla już uruchomiona.")
                return

            print(f"[{self.soul}] Inicjalizacja...")
            Being.db_pool = await aiosqlite.connect(self.db_path)
            await self.setup_sqlite_tables()
            print("Tabele SQLite zostały utworzone.")
            self._main_loop_task = asyncio.create_task(self._main_loop())
        except Exception as e:
            print(f"[{self.soul}] Błąd podczas inicjalizacji: {e}")

    async def stop(self):
        """Zatrzymuje byt i zamyka połączenie z bazą danych"""
        if self.db_pool:
            await self.db_pool.close()
        print(f"[{self.soul}] Połączenie z bazą danych zamknięte.")
        
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
            if task['type'] == 'intent':
                await self._execute_task(task)
            elif task['type'] == 'cpu_task':
                await self._process_cpu_task(task)
            else:
                print(f"[{self.soul}] Nieznany typ zadania: {task['type']}")
        except Exception as e:
            print(f"[{self.soul}] Błąd podczas dispatchu: {e}")

    async def _execute_task(self, task):
        # Zastępczy kod – np. wykonaj intencję z bazy
        print(f"[{self.soul}] Wykonuję intencję: {task}")
        # Możesz tu dodać np. exec() z kontrolowanym kontekstem

    async def _process_cpu_task(self, task):
        # Używa ProcessPoolExecutor do wykonania zadania CPU-bound
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(self.executor, self._heavy_computation, task['data'])
        print(f"[{self.soul}] Wynik CPU: {result}")

    def _heavy_computation(self, data):
        # Dummy CPU-bound function
        return sum(data)

    async def setup_sqlite_tables(self):
        """Tworzy tabele w SQLite"""
        if not self.db_pool:
            raise RuntimeError("Połączenie z bazą danych nie zostało zainicjalowane.")

        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS base_beings (
                soul TEXT PRIMARY KEY,
                genesis TEXT NOT NULL,
                attributes TEXT NOT NULL,
                memories TEXT NOT NULL,
                self_awareness TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.db_pool.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                source_soul TEXT NOT NULL,
                target_soul TEXT NOT NULL,
                genesis TEXT NOT NULL,
                attributes TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_soul) REFERENCES base_beings (soul),
                FOREIGN KEY (target_soul) REFERENCES base_beings (soul)
            )
        """)

        await self.db_pool.commit()

    async def save(self):
        """Zapisuje byt do bazy danych"""
        if hasattr(self.db_pool, 'acquire'):
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO base_beings (soul, genesis, attributes, memories, self_awareness)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (soul) DO UPDATE SET
                    genesis = EXCLUDED.genesis,
                    attributes = EXCLUDED.attributes,
                    memories = EXCLUDED.memories,
                    self_awareness = EXCLUDED.self_awareness
                """, str(self.soul), json.dumps(self.genesis, cls=DateTimeEncoder), 
                    json.dumps(self.attributes, cls=DateTimeEncoder),
                    json.dumps(self.memories, cls=DateTimeEncoder), 
                    json.dumps(self.self_awareness, cls=DateTimeEncoder))
        else:
            # SQLite fallback
            await self.db_pool.execute("""
                INSERT OR REPLACE INTO base_beings 
                (soul, genesis, attributes, memories, self_awareness)
                VALUES (?, ?, ?, ?, ?)
            """, (str(self.soul), json.dumps(self.genesis, cls=DateTimeEncoder), 
                  json.dumps(self.attributes, cls=DateTimeEncoder),
                  json.dumps(self.memories, cls=DateTimeEncoder), 
                  json.dumps(self.self_awareness, cls=DateTimeEncoder)))
            await self.db_pool.commit()

    @classmethod
    async def load(cls, soul: str):
        """Ładuje byt z bazy danych"""
        async with aiosqlite.connect(cls.db_pool) as conn:
            cursor = await conn.execute("SELECT * FROM base_beings WHERE soul = ?", (soul,))
            row = await cursor.fetchone()
            if row:
                return cls(
                    soul=str(row['soul']),
                    genesis=json.loads(row['genesis']),
                    attributes=json.loads(row['attributes']),
                    memories=json.loads(row['memories']),
                    self_awareness=json.loads(row['self_awareness']),
                    created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
                )
        return None

    @classmethod
    async def get_all(cls, limit: int = 100):
        """Pobiera wszystkie byty"""
        async with cls.db_pool as conn:
            cursor = await conn.execute("SELECT soul, genesis, attributes, memories, self_awareness, created_at FROM base_beings LIMIT ?", (limit,))
            rows = await cursor.fetchall()
            beings = []
            for row in rows:
                try:
                    genesis = json.loads(row[1]) if row[1] else {}
                    attributes = json.loads(row[2]) if row[2] else {}
                    memories = json.loads(row[3]) if row[3] else []
                    self_awareness = json.loads(row[4]) if row[4] else {}

                    beings.append(cls(
                        soul=row[0],
                        genesis=genesis,
                        attributes=attributes,
                        memories=memories,
                        self_awareness=self_awareness,
                        created_at=datetime.fromisoformat(row[5]) if row[5] else None
                    ))
                except Exception as e:
                    print(f"Błąd parsowania wiersza: {e}, wiersz: {row}")
                    continue
            return beings

# @classmethod
    # async def create(cls, genesis: Dict[str, Any], **kwargs):
    #     """Tworzy nowy byt w bazie danych"""
    #     soul = str(uuid.uuid4())

    #     being = cls(
    #         soul=soul,
    #         genesis=genesis,
    #         attributes=attributes,
    #         memories=kwargs.get('memories', []),
    #         self_awareness=kwargs.get('self_awareness', {})
    #     )
    #     await being.save()
    #     return being

@dataclass
class Relationship:
    id: str
    source_soul: str
    target_soul: str
    genesis: Dict[str, Any]
    attributes: Dict[str, Any]
    created_at: Optional[datetime] = None

    @property
    def type(self) -> List[str]:
        """Pobiera typy z atrybutów"""
        return self.attributes.get('type', [])

    @type.setter
    def type(self, value: List[str]):
        """Ustawia typy w atrybutach"""
        self.attributes['type'] = value

    @property
    def energy_level(self) -> int:
        """Pobiera poziom energii z atrybutów"""
        return self.attributes.get('energy_level', 0)

    @energy_level.setter
    def energy_level(self, value: int):
        """Ustawia poziom energii w atrybutach"""
        self.attributes['energy_level'] = value

    @classmethod
    async def create(cls, db_pool, source_soul: str, target_soul: str, genesis: Dict[str, Any], **kwargs):
        """Tworzy nową relację"""
        rel_id = str(uuid.uuid4())

        # Przygotuj atrybuty z tags i energy_level
        attributes = kwargs.get('attributes', {})
        if 'tags' in kwargs:
            attributes['tags'] = kwargs['tags']
        if 'energy_level' in kwargs:
            attributes['energy_level'] = kwargs['energy_level']

        relationship = cls(
            id=rel_id,
            source_soul=source_soul,
            target_soul=target_soul,
            genesis=genesis,
            attributes=attributes
        )
        await relationship.save()
        return relationship
    

    async def save(self):
        """Zapisuje relację do bazy danych"""
        if hasattr(self.db_pool, 'acquire'):
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO relationships (id, source_soul, target_soul, genesis, attributes)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id) DO UPDATE SET
                    genesis = EXCLUDED.genesis,
                    attributes = EXCLUDED.attributes
                """, str(self.id), str(self.source_soul), str(self.target_soul), 
                    json.dumps(self.genesis, cls=DateTimeEncoder), 
                    json.dumps(self.attributes, cls=DateTimeEncoder))
        else:
            # SQLite fallback
            await self.db_pool.execute("""
                INSERT OR REPLACE INTO relationships 
                (id, source_soul, target_soul, genesis, attributes)
                VALUES (?, ?, ?, ?, ?)
            """, (str(self.id), str(self.source_soul), str(self.target_soul),
                  json.dumps(self.genesis, cls=DateTimeEncoder), 
                  json.dumps(self.attributes, cls=DateTimeEncoder)))
            await self.db_pool.commit()

    @classmethod
    async def get_all(cls, limit: int = 100):
        """Pobiera wszystkie relacje"""
        db_pool = cls.db_pool
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            async with db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM relationships LIMIT $1", limit)
                return [cls(
                    id=str(row['id']),
                    source_soul=str(row['source_soul']),
                    target_soul=str(row['target_soul']),
                    genesis=row['genesis'],
                    attributes=row['attributes'],
                    created_at=row['created_at']
                ) for row in rows]
        else:
            # SQLite fallback
            async with db_pool.execute("SELECT id, source_soul, target_soul, genesis, attributes, created_at FROM relationships LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                relationships = []
                for row in rows:
                    try:
                        genesis = json.loads(row[3]) if row[3] else {}
                        attributes = json.loads(row[4]) if row[4] else {}

                        # Dodaj tags i energy_level do attributes jeśli nie ma
                        if 'tags' not in attributes and row[1]:
                            attributes['tags'] = json.loads(row[1])
                        if 'energy_level' not in attributes and row[2]:
                            attributes['energy_level'] = row[2]

                        relationships.append(cls(
                            id=row[0],
                            source_soul=row[3],
                            target_soul=row[4],
                            genesis=genesis,
                            attributes=attributes,
                            created_at=row[7]
                        ))
                    except Exception as e:
                        print(f"Błąd parsowania relacji: {e}, wiersz: {row}")
                        continue
                return relationships
            
    if __name__ == "__main__":
        # Przykładowe użycie
        async def main():
            being = Being(soul="example_soul", genesis={}, attributes={}, memories=[], self_awareness={})
            await being.start()
            await being.save()
            print("Byt zapisany.")
            loaded_being = await Being.load("example_soul")
            print("Byt odczytany:", loaded_being.to_dict())
        
        asyncio.run(main())