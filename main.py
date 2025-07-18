
import asyncio
import asyncpg
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import socketio
from aiohttp import web
import aiohttp_cors

# Socket.IO serwer
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

# Globalna pula połączeń do bazy danych
db_pool = None

@dataclass
class BaseBeing:
    soul: str
    tags: List[str]
    energy_level: int
    genesis: Dict[str, Any]
    attributes: Dict[str, Any]
    memories: List[Dict[str, Any]]
    self_awareness: Dict[str, Any]
    created_at: Optional[datetime] = None
    
    @classmethod
    async def create(cls, genesis: Dict[str, Any], **kwargs):
        """Tworzy nowy byt w bazie danych"""
        soul = str(uuid.uuid4())
        being = cls(
            soul=soul,
            tags=kwargs.get('tags', []),
            energy_level=kwargs.get('energy_level', 0),
            genesis=genesis,
            attributes=kwargs.get('attributes', {}),
            memories=kwargs.get('memories', []),
            self_awareness=kwargs.get('self_awareness', {})
        )
        await being.save()
        return being
    
    async def save(self):
        """Zapisuje byt do bazy danych"""
        global db_pool
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO base_beings (soul, tags, energy_level, genesis, attributes, memories, self_awareness)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (soul) DO UPDATE SET
                tags = EXCLUDED.tags,
                energy_level = EXCLUDED.energy_level,
                genesis = EXCLUDED.genesis,
                attributes = EXCLUDED.attributes,
                memories = EXCLUDED.memories,
                self_awareness = EXCLUDED.self_awareness
            """, self.soul, self.tags, self.energy_level, 
                json.dumps(self.genesis), json.dumps(self.attributes),
                json.dumps(self.memories), json.dumps(self.self_awareness))
    
    @classmethod
    async def load(cls, soul: str):
        """Ładuje byt z bazy danych"""
        global db_pool
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM base_beings WHERE soul = $1", soul)
            if row:
                return cls(
                    soul=row['soul'],
                    tags=row['tags'],
                    energy_level=row['energy_level'],
                    genesis=row['genesis'],
                    attributes=row['attributes'],
                    memories=row['memories'],
                    self_awareness=row['self_awareness'],
                    created_at=row['created_at']
                )
        return None
    
    @classmethod
    async def get_all(cls, limit: int = 100):
        """Pobiera wszystkie byty"""
        global db_pool
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM base_beings LIMIT $1", limit)
            return [cls(
                soul=row['soul'],
                tags=row['tags'],
                energy_level=row['energy_level'],
                genesis=row['genesis'],
                attributes=row['attributes'],
                memories=row['memories'],
                self_awareness=row['self_awareness'],
                created_at=row['created_at']
            ) for row in rows]

@dataclass
class Relationship:
    id: str
    tags: List[str]
    energy_level: int
    source_soul: str
    target_soul: str
    genesis: Dict[str, Any]
    attributes: Dict[str, Any]
    created_at: Optional[datetime] = None
    
    @classmethod
    async def create(cls, source_soul: str, target_soul: str, genesis: Dict[str, Any], **kwargs):
        """Tworzy nową relację"""
        rel_id = str(uuid.uuid4())
        relationship = cls(
            id=rel_id,
            tags=kwargs.get('tags', []),
            energy_level=kwargs.get('energy_level', 0),
            source_soul=source_soul,
            target_soul=target_soul,
            genesis=genesis,
            attributes=kwargs.get('attributes', {})
        )
        await relationship.save()
        return relationship
    
    async def save(self):
        """Zapisuje relację do bazy danych"""
        global db_pool
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO relationships (id, tags, energy_level, source_soul, target_soul, genesis, attributes)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (id) DO UPDATE SET
                tags = EXCLUDED.tags,
                energy_level = EXCLUDED.energy_level,
                genesis = EXCLUDED.genesis,
                attributes = EXCLUDED.attributes
            """, self.id, self.tags, self.energy_level, self.source_soul, 
                self.target_soul, json.dumps(self.genesis), json.dumps(self.attributes))
    
    @classmethod
    async def get_all(cls, limit: int = 100):
        """Pobiera wszystkie relacje"""
        global db_pool
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM relationships LIMIT $1", limit)
            return [cls(
                id=row['id'],
                tags=row['tags'],
                energy_level=row['energy_level'],
                source_soul=row['source_soul'],
                target_soul=row['target_soul'],
                genesis=row['genesis'],
                attributes=row['attributes'],
                created_at=row['created_at']
            ) for row in rows]

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print(f"Klient połączony: {sid}")
    # Wyślij aktualny stan grafu
    await send_graph_data(sid)

@sio.event
async def disconnect(sid):
    print(f"Klient rozłączony: {sid}")

@sio.event
async def get_graph_data(sid, data):
    """Wysyła dane grafu do klienta"""
    await send_graph_data(sid)

@sio.event
async def create_being(sid, data):
    """Tworzy nowy byt"""
    try:
        being = await BaseBeing.create(
            genesis=data.get('genesis', {}),
            tags=data.get('tags', []),
            energy_level=data.get('energy_level', 0),
            attributes=data.get('attributes', {}),
            memories=data.get('memories', []),
            self_awareness=data.get('self_awareness', {})
        )
        await sio.emit('being_created', asdict(being))
        await broadcast_graph_update()
    except Exception as e:
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def create_relationship(sid, data):
    """Tworzy nową relację"""
    try:
        relationship = await Relationship.create(
            source_soul=data['source_soul'],
            target_soul=data['target_soul'],
            genesis=data.get('genesis', {}),
            tags=data.get('tags', []),
            energy_level=data.get('energy_level', 0),
            attributes=data.get('attributes', {})
        )
        await sio.emit('relationship_created', asdict(relationship))
        await broadcast_graph_update()
    except Exception as e:
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def update_being(sid, data):
    """Aktualizuje byt"""
    try:
        being = await BaseBeing.load(data['soul'])
        if being:
            # Aktualizuj pola
            for key, value in data.items():
                if hasattr(being, key) and key != 'soul':
                    setattr(being, key, value)
            await being.save()
            await sio.emit('being_updated', asdict(being))
            await broadcast_graph_update()
        else:
            await sio.emit('error', {'message': 'Byt nie znaleziony'}, room=sid)
    except Exception as e:
        await sio.emit('error', {'message': str(e)}, room=sid)

async def send_graph_data(sid):
    """Wysyła dane grafu do konkretnego klienta"""
    beings = await BaseBeing.get_all()
    relationships = await Relationship.get_all()
    
    graph_data = {
        'nodes': [asdict(being) for being in beings],
        'links': [asdict(rel) for rel in relationships]
    }
    
    await sio.emit('graph_data', graph_data, room=sid)

async def broadcast_graph_update():
    """Rozgłasza aktualizację grafu do wszystkich klientów"""
    beings = await BaseBeing.get_all()
    relationships = await Relationship.get_all()
    
    graph_data = {
        'nodes': [asdict(being) for being in beings],
        'links': [asdict(rel) for rel in relationships]
    }
    
    await sio.emit('graph_updated', graph_data)

# HTTP API endpoints
async def api_beings(request):
    """REST API dla bytów"""
    if request.method == 'GET':
        beings = await BaseBeing.get_all()
        return web.json_response([asdict(being) for being in beings])
    elif request.method == 'POST':
        data = await request.json()
        being = await BaseBeing.create(**data)
        return web.json_response(asdict(being))

async def api_relationships(request):
    """REST API dla relacji"""
    if request.method == 'GET':
        relationships = await Relationship.get_all()
        return web.json_response([asdict(rel) for rel in relationships])
    elif request.method == 'POST':
        data = await request.json()
        relationship = await Relationship.create(**data)
        return web.json_response(asdict(relationship))

async def init_database():
    """Inicjalizuje połączenie z bazą danych i tworzy tabele"""
    global db_pool
    
    # Połączenie z PostgreSQL
    db_pool = await asyncpg.create_pool(
        host='localhost',
        port=5432,
        user='postgres',
        password='password',
        database='luxos',
        min_size=5,
        max_size=20
    )
    
    # Tworzenie tabel
    async with db_pool.acquire() as conn:
        # Tabela base_beings
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS base_beings (
                soul UUID PRIMARY KEY,
                tags TEXT[] DEFAULT '{}',
                energy_level INTEGER DEFAULT 0,
                genesis JSONB NOT NULL,
                attributes JSONB NOT NULL,
                memories JSONB NOT NULL,
                self_awareness JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela relationships
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id UUID PRIMARY KEY,
                tags TEXT[] DEFAULT '{}',
                energy_level INTEGER DEFAULT 0,
                source_soul UUID NOT NULL,
                target_soul UUID NOT NULL,
                genesis JSONB NOT NULL,
                attributes JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_soul) REFERENCES base_beings (soul),
                FOREIGN KEY (target_soul) REFERENCES base_beings (soul)
            )
        """)
        
        # Indeksy
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_genesis ON base_beings USING gin (genesis)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_attributes ON base_beings USING gin (attributes)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_memories ON base_beings USING gin (memories)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_self_awareness ON base_beings USING gin (self_awareness)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_energy_level ON base_beings (energy_level)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_being_tags ON base_beings USING gin (tags)")
        
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_genesis ON relationships USING gin (genesis)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_attributes ON relationships USING gin (attributes)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships (source_soul)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships (target_soul)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_energy_level ON relationships (energy_level)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_rel_tags ON relationships USING gin (tags)")

# Konfiguracja aplikacji
async def init_app():
    # Redirect root to landing page
    async def serve_landing(request):
        return web.FileResponse('static/landing.html')
    
    app.router.add_get('/', serve_landing)
    
    # Serwowanie plików statycznych
    app.router.add_static('/', 'static', name='static')
    
    # Konfiguracja CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    
    # Dodaj CORS do konkretnych tras API
    cors.add(app.router.add_route('GET', '/api/beings', api_beings))
    cors.add(app.router.add_route('POST', '/api/beings', api_beings))
    cors.add(app.router.add_route('GET', '/api/relationships', api_relationships))
    cors.add(app.router.add_route('POST', '/api/relationships', api_relationships))
    
    await init_database()

if __name__ == '__main__':
    asyncio.run(init_app())
    web.run_app(app, host='0.0.0.0', port=5000)
