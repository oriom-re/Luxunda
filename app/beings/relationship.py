from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid
import json
from app.beings import DateTimeEncoder
from app.database import get_db_pool


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