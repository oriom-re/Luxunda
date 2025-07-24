import asyncio
from dataclasses import dataclass
import importlib
import sys
from typing import Dict, Any, List, Optional
import uuid
import json
from datetime import datetime
from app.database import get_db_pool
from app.genetics.gene_registry import gene_registry, create_gene_context
from app.core.gen_loader_from_file import get_soul_by_name

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

@dataclass
class Being:
    uid: str
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

    async def genes(self, gene_name: str, *args, **kwargs):
        """Wywołuje gen w kontekście tego bytu"""
        with create_gene_context(self.soul) as context:
            return await context(gene_name, *args, **kwargs)
    
    def available_genes(self) -> List[str]:
        """Zwraca listę dostępnych genów"""
        return gene_registry.get_available_genes()

    @classmethod
    async def create(cls, data: Dict[str, Any]=None, **kwargs):
        """Tworzy nowy byt w bazie danych"""
        uid = str(uuid.uuid4())

        # Przygotuj atrybuty z tags i energy_level
        attributes = kwargs.get('attributes', {})
        if 'tags' in kwargs:
            attributes['tags'] = kwargs['tags']
        if 'energy_level' in kwargs:
            attributes['energy_level'] = kwargs['energy_level']

        being = cls(
            uid=data.get('uid', kwargs.get('uid', uid)),
            genesis=data.get('genesis', kwargs.get('genesis', {})),
            attributes=data.get('attributes', kwargs.get('attributes', {})),
            memories=data.get('memories', kwargs.get('memories', [])),
            self_awareness=data.get('self_awareness', kwargs.get('self_awareness', []))
        )
        await being.save()
        print(f"🧬 Stworzono byt: {being.uid}")
        return being

    async def save(self):
        """Zapisuje byt do bazy danych"""
        db_pool = await get_db_pool()
        if not db_pool:
            print("Database pool is not initialized.")
            return
        print(f"🗄️ Zapisuję byt {self.uid} do bazy danych...")
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO souls (uid, genesis, attributes, memories, self_awareness)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (uid) DO UPDATE SET
                    genesis = EXCLUDED.genesis,
                    attributes = EXCLUDED.attributes,
                    memories = EXCLUDED.memories,
                    self_awareness = EXCLUDED.self_awareness
                """, str(self.uid), json.dumps(self.genesis, cls=DateTimeEncoder), 
                    json.dumps(self.attributes, cls=DateTimeEncoder),
                    json.dumps(self.memories, cls=DateTimeEncoder), 
                    json.dumps(self.self_awareness, cls=DateTimeEncoder))

                print(f"🗄️ Zapisano byt {self.uid} do bazy danych.")
        else:
            # SQLite fallback
            await db_pool.execute("""
                INSERT OR REPLACE INTO souls 
                (uid, genesis, attributes, memories, self_awareness)
                VALUES (?, ?, ?, ?, ?)
            """, (str(self.soul), json.dumps(self.genesis, cls=DateTimeEncoder), 
                  json.dumps(self.attributes, cls=DateTimeEncoder),
                  json.dumps(self.memories, cls=DateTimeEncoder), 
                  json.dumps(self.self_awareness, cls=DateTimeEncoder)))
            await db_pool.commit()

    @classmethod
    async def load(cls, soul: str):
        """Ładuje byt z bazy danych"""
        db_pool = await get_db_pool()
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM base_beings WHERE soul = $1", soul)
                if row:
                    return cls(
                        uid=str(row['uid']),
                        genesis=json.loads(row['genesis']),
                        attributes=json.loads(row['attributes']),
                        memories=json.loads(row['memories']),
                        self_awareness=json.loads(row['self_awareness']),
                        created_at=row['created_at']
                    )
        else:
            # SQLite fallback
            async with db_pool.execute("SELECT soul, genesis, attributes, memories, self_awareness, created_at FROM base_beings WHERE soul = ?", (soul,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    # row[0]=uid, row[1]=genesis, row[2]=attributes, row[3]=memories, row[4]=self_awareness, row[5]=created_at
                    return cls(
                        uid=row[0],
                        genesis=json.loads(row[1]) if row[1] else {},
                        attributes=json.loads(row[2]) if row[2] else {},
                        memories=json.loads(row[3]) if row[3] else [],
                        self_awareness=json.loads(row[4]) if row[4] else [],
                        created_at=row[5]
                    )
        return None

    @classmethod
    async def get_all(cls, limit: int = 100):
        """Pobiera wszystkie byty"""
        db_pool = await get_db_pool()
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            async with db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM souls LIMIT $1", limit)
                return [cls(
                    uid=str(row['uid']),
                    genesis=json.loads(row['genesis']),
                    attributes=json.loads(row['attributes']),
                    memories=json.loads(row['memories']),
                    self_awareness=json.loads(row['self_awareness']),
                    created_at=row['created_at']
                ) for row in rows]
        else:
            # SQLite fallback
            async with db_pool.execute("SELECT uid, genesis, attributes, memories, self_awareness, created_at FROM base_beings LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                beings = []
                for row in rows:
                    # row[0]=uid, row[1]=genesis, row[2]=attributes, row[3]=memories, row[4]=self_awareness, row[5]=created_at
                    try:
                        genesis = json.loads(row[1]) if row[1] else {}
                        attributes = json.loads(row[2]) if row[2] else {}
                        memories = json.loads(row[3]) if row[3] else []
                        self_awareness = json.loads(row[4]) if row[4] else {}

                        # Dodaj tags i energy_level do attributes jeśli nie ma
                        if 'tags' not in attributes and row[1]:
                            attributes['tags'] = json.loads(row[1])
                        if 'energy_level' not in attributes and row[2]:
                            attributes['energy_level'] = row[2]

                        beings.append(cls(
                            soul=row[0],
                            genesis=genesis,
                            attributes=attributes,
                            memories=memories,
                            self_awareness=self_awareness,
                            created_at=row[5]
                        ))
                    except Exception as e:
                        print(f"Błąd parsowania wiersza: {e}, wiersz: {row}")
                        continue
                return beings

@dataclass
class Relationship:
    uid: str
    source_uid: str
    target_uid: str
    attributes: Dict[str, Any]
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
    async def create(cls, source_uid: str, target_uid: str, **kwargs):
        """Tworzy nową relację"""
        rel_id = str(uuid.uuid4())

        # Przygotuj atrybuty z tags i energy_level
        attributes = kwargs.get('attributes', {})
        if 'tags' in kwargs:
            attributes['tags'] = kwargs['tags']
        if 'energy_level' in kwargs:
            attributes['energy_level'] = kwargs['energy_level']

        relationship = cls(
            uid=rel_id,
            source_uid=source_uid,
            target_uid=target_uid,
            attributes=attributes
        )
        await relationship.save()
        return relationship

    async def save(self):
        """Zapisuje relację do bazy danych"""
        db_pool = await get_db_pool()
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO relationships (uid, source_uid, target_uid, attributes)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (uid) DO UPDATE SET
                    attributes = EXCLUDED.attributes
                """, str(self.uid), str(self.source_uid), str(self.target_uid), 
                    json.dumps(self.attributes, cls=DateTimeEncoder))
        else:
            # SQLite fallback
            await db_pool.execute("""
                INSERT OR REPLACE INTO relationships 
                (uid, source_uid, target_uid, attributes)
                VALUES (?, ?, ?, ?)
            """, (str(self.uid), str(self.source_uid), str(self.target_uid),
                  json.dumps(self.attributes, cls=DateTimeEncoder)))
            await db_pool.commit()
        print(f"🗄️ Zapisano relację {self.uid} do bazy danych.")
    
    @classmethod
    async def load(cls, rel_id: str):
        """Ładuje relację z bazy danych"""
        db_pool = await get_db_pool()
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM relationships WHERE uid = $1", rel_id)
                if row:
                    return cls(
                        uid=str(row['uid']),
                        source_uid=str(row['source_uid']),
                        target_uid=str(row['target_uid']),
                        attributes=json.loads(row['attributes']) if row['attributes'] else {},
                        created_at=row['created_at']
                    )
        else:
            # SQLite fallback
            async with db_pool.execute("SELECT uid, source_uid, target_uid, attributes, created_at FROM relationships WHERE uid = ?", (rel_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return cls(
                        uid=row[0],
                        source_uid=row[1],
                        target_uid=row[2],
                        attributes=json.loads(row[3]) if row[3] else {},
                        created_at=row[4]
                    )
        return None

    @classmethod
    async def get_all(cls, limit: int = 100):
        """Pobiera wszystkie relacje"""
        db_pool = await get_db_pool()
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            async with db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM relationships LIMIT $1", limit)
                return [cls(
                    uid=str(row['uid']),
                    source_uid=str(row['source_uid']),
                    target_uid=str(row['target_uid']),
                    attributes=json.loads(row['attributes']) if row['attributes'] else {},
                    created_at=row['created_at']
                ) for row in rows]
        else:
            # SQLite fallback
            async with db_pool.execute("SELECT uid, source_uid, target_uid, attributes, created_at FROM relationships LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                relationships = []
                for row in rows:
                    try:

                        relationships.append(cls(
                            uid=row[0],
                            source_uid=row[1],
                            target_uid=row[2],
                            attributes=json.loads(row[3]) if row[3] else {},
                            created_at=row[4]
                        ))
                    except Exception as e:
                        print(f"Błąd parsowania relacji: {e}, wiersz: {row}")
                        continue
                return relationships