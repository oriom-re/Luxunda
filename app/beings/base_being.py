
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Import będzie dodany po utworzeniu connection
# from ..database.connection import DatabaseManager

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

@dataclass
class BaseBeing:
    soul: str
    genesis: Dict[str, Any]
    attributes: Dict[str, Any]
    memories: List[Dict[str, Any]]
    self_awareness: Dict[str, Any]
    created_at: Optional[datetime] = None

    @property
    def tags(self) -> List[str]:
        """Pobiera tagi z atrybutów"""
        return self.attributes.get('tags', [])

    @tags.setter
    def tags(self, value: List[str]):
        """Ustawia tagi w atrybutach"""
        self.attributes['tags'] = value

    @property
    def energy_level(self) -> int:
        """Pobiera poziom energii z atrybutów"""
        return self.attributes.get('energy_level', 0)

    @energy_level.setter
    def energy_level(self, value: int):
        """Ustawia poziom energii w atrybutach"""
        self.attributes['energy_level'] = value

    @classmethod
    async def create(cls, soul: str = None, genesis: Dict[str, Any] = None, **kwargs):
        """Tworzy nowy byt w bazie danych"""
        if not soul:
            soul = str(uuid.uuid4())
        if not genesis:
            genesis = {}

        # Przygotuj atrybuty z tags i energy_level
        attributes = kwargs.get('attributes', {})
        if 'tags' in kwargs:
            attributes['tags'] = kwargs['tags']
        if 'energy_level' in kwargs:
            attributes['energy_level'] = kwargs['energy_level']

        being = cls(
            soul=soul,
            genesis=genesis,
            attributes=attributes,
            memories=kwargs.get('memories', []),
            self_awareness=kwargs.get('self_awareness', {})
        )
        await being.save()
        return being

    async def save(self):
        """Zapisuje byt do bazy danych"""
        # Import lokalnie aby uniknąć circular import
        from main import db_pool
        
        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO base_beings (soul, genesis, attributes, memories, self_awareness, binary_data)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (soul) DO UPDATE SET
                    genesis = EXCLUDED.genesis,
                    attributes = EXCLUDED.attributes,
                    memories = EXCLUDED.memories,
                    self_awareness = EXCLUDED.self_awareness
                """, str(self.soul), json.dumps(self.genesis, cls=DateTimeEncoder), 
                    json.dumps(self.attributes, cls=DateTimeEncoder),
                    json.dumps(self.memories, cls=DateTimeEncoder), 
                    json.dumps(self.self_awareness, cls=DateTimeEncoder), None)
        else:
            # SQLite fallback
            await db_pool.execute("""
                INSERT OR REPLACE INTO base_beings 
                (soul, genesis, attributes, memories, self_awareness, binary_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(self.soul), 
                  json.dumps(self.genesis, cls=DateTimeEncoder), 
                  json.dumps(self.attributes, cls=DateTimeEncoder),
                  json.dumps(self.memories, cls=DateTimeEncoder), 
                  json.dumps(self.self_awareness, cls=DateTimeEncoder), None))
            await db_pool.commit()

    @classmethod
    async def load(cls, soul: str):
        """Ładuje byt z bazy danych"""
        # Import lokalnie
        from main import db_pool
        
        global db_pool
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM base_beings WHERE soul = $1", soul)
                if row:
                    return cls(
                        soul=str(row['soul']),
                        genesis=row['genesis'],
                        attributes=row['attributes'],
                        memories=row['memories'],
                        self_awareness=row['self_awareness'],
                        created_at=row['created_at']
                    )
        else:
            # SQLite
            async with db_pool.execute("SELECT * FROM base_beings WHERE soul = ?", (soul,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    try:
                        return cls(
                            soul=row[0],
                            genesis=json.loads(row[1]) if row[1] else {},
                            attributes=json.loads(row[2]) if row[2] else {},
                            memories=json.loads(row[3]) if row[3] else [],
                            self_awareness=json.loads(row[4]) if row[4] else {},
                            created_at=row[6]
                        )
                    except Exception as e:
                        print(f"Błąd parsowania bytu {soul}: {e}")
        return None

    @classmethod
    async def get_all(cls, limit: int = 100):
        """Pobiera wszystkie byty"""
        # Import lokalnie
        from main import db_pool
        
        global db_pool
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            async with db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM base_beings LIMIT $1", limit)
                return [cls(
                    soul=str(row['soul']),
                    genesis=row['genesis'],
                    attributes=row['attributes'],
                    memories=row['memories'],
                    self_awareness=row['self_awareness'],
                    created_at=row['created_at']
                ) for row in rows]
        else:
            # SQLite fallback
            async with db_pool.execute("SELECT * FROM base_beings LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                beings = []
                for row in rows:
                    try:
                        beings.append(cls(
                            soul=row[0],
                            genesis=json.loads(row[1]) if row[1] else {},
                            attributes=json.loads(row[2]) if row[2] else {},
                            memories=json.loads(row[3]) if row[3] else [],
                            self_awareness=json.loads(row[4]) if row[4] else {},
                            created_at=row[6]
                        ))
                    except Exception as e:
                        print(f"Błąd parsowania wiersza: {e}")
                        continue
                return beings
