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
import aiosqlite

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Globalna pula połączeń do bazy danych
db_pool = None

# Socket.IO serwer
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

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
    async def create(cls, genesis: Dict[str, Any], **kwargs):
        """Tworzy nowy byt w bazie danych"""
        soul = str(uuid.uuid4())
        
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
        global db_pool
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO base_beings (soul, genesis, attributes, memories, self_awareness)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (soul) DO UPDATE SET
                genesis = EXCLUDED.genesis,
                attributes = EXCLUDED.attributes,
                memories = EXCLUDED.memories,
                self_awareness = EXCLUDED.self_awareness
            """, self.soul, json.dumps(self.genesis), json.dumps(self.attributes),
                json.dumps(self.memories), json.dumps(self.self_awareness))

    @classmethod
    async def load(cls, soul: str):
        """Ładuje byt z bazy danych"""
        global db_pool
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
        return None

    @classmethod
    async def get_all(cls, limit: int = 100):
        """Pobiera wszystkie byty"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
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
            # SQLite fallback - pozostaw zgodne ze starym schematem dla lokalnego rozwoju
            async with db_pool.execute("SELECT * FROM base_beings LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [cls(
                    soul=row[0],
                    genesis=json.loads(row[3]),
                    attributes=json.loads(row[4]),
                    memories=json.loads(row[5]),
                    self_awareness=json.loads(row[6]),
                    created_at=row[7]
                ) for row in rows]

@dataclass
class Relationship:
    id: str
    source_soul: str
    target_soul: str
    genesis: Dict[str, Any]
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
    async def create(cls, source_soul: str, target_soul: str, genesis: Dict[str, Any], **kwargs):
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
        global db_pool
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO relationships (id, source_soul, target_soul, genesis, attributes)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (id) DO UPDATE SET
                genesis = EXCLUDED.genesis,
                attributes = EXCLUDED.attributes
            """, self.id, self.source_soul, self.target_soul, 
                json.dumps(self.genesis), json.dumps(self.attributes))

    @classmethod
    async def get_all(cls, limit: int = 100):
        """Pobiera wszystkie relacje"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
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
            # SQLite fallback - pozostaw zgodne ze starym schematem dla lokalnego rozwoju
            async with db_pool.execute("SELECT * FROM relationships LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [cls(
                    id=row[0],
                    source_soul=row[3],
                    target_soul=row[4],
                    genesis=json.loads(row[5]),
                    attributes=json.loads(row[6]),
                    created_at=row[7]
                ) for row in rows]

# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
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

@sio.event
async def process_intention(sid, data):
    """Przetwarza intencję użytkownika"""
    try:
        intention = data.get('intention', '').lower()
        context = data.get('context', {})
        
        print(f"Otrzymano intencję od {sid}: {intention}")
        
        # Proste przetwarzanie intencji - w przyszłości można dodać AI
        response = await analyze_intention(intention, context)
        
        await sio.emit('intention_response', response, room=sid)
        
    except Exception as e:
        await sio.emit('error', {'message': f'Błąd przetwarzania intencji: {str(e)}'}, room=sid)

async def analyze_intention(intention: str, context: dict) -> dict:
    """Analizuje intencję i zwraca odpowiedz z akcjami"""
    
    # Słowa kluczowe dla różnych akcji
    create_keywords = ['utwórz', 'stwórz', 'dodaj', 'nowy', 'nowa', 'nowe']
    connect_keywords = ['połącz', 'zwiąż', 'relacja', 'łącz']
    find_keywords = ['znajdź', 'pokaż', 'gdzie', 'szukaj']
    
    actions = []
    message = "Intencja została przetworzona."
    
    # Rozpoznawanie intencji tworzenia
    if any(keyword in intention for keyword in create_keywords):
        if 'funkcj' in intention:
            # Ekstraktuj nazwę z intencji
            words = intention.split()
            name = "Nowa_Funkcja"
            for i, word in enumerate(words):
                if word in ['funkcj', 'funkcję', 'funkcji'] and i < len(words) - 1:
                    name = words[i + 1].replace(',', '').replace('.', '')
                    break
            
            actions.append({
                'type': 'create_being',
                'data': {
                    'genesis': {
                        'name': name,
                        'type': 'function',
                        'source': f'def {name}():\n    """Funkcja utworzona przez intencję"""\n    pass',
                        'created_by': 'intention'
                    },
                    'tags': ['function', 'intention'],
                    'energy_level': 75,
                    'attributes': {'created_via': 'intention', 'intention_text': intention},
                    'memories': [{'type': 'creation', 'data': intention}],
                    'self_awareness': {'trust_level': 0.8, 'confidence': 0.9}
                }
            })
            message = f"Utworzono funkcję: {name}"
            
        elif 'klas' in intention:
            words = intention.split()
            name = "Nowa_Klasa"
            for i, word in enumerate(words):
                if word in ['klas', 'klasę', 'klasy'] and i < len(words) - 1:
                    name = words[i + 1].replace(',', '').replace('.', '')
                    break
            
            actions.append({
                'type': 'create_being',
                'data': {
                    'genesis': {
                        'name': name,
                        'type': 'class',
                        'source': f'class {name}:\n    """Klasa utworzona przez intencję"""\n    pass',
                        'created_by': 'intention'
                    },
                    'tags': ['class', 'intention'],
                    'energy_level': 80,
                    'attributes': {'created_via': 'intention', 'intention_text': intention},
                    'memories': [{'type': 'creation', 'data': intention}],
                    'self_awareness': {'trust_level': 0.8, 'confidence': 0.9}
                }
            })
            message = f"Utworzono klasę: {name}"
    
    # Rozpoznawanie intencji łączenia
    elif any(keyword in intention for keyword in connect_keywords):
        selected_nodes = context.get('selected_nodes', [])
        if len(selected_nodes) >= 2:
            relationship_type = 'calls'
            if 'dziedzicz' in intention:
                relationship_type = 'inherits'
            elif 'zawier' in intention:
                relationship_type = 'contains'
            elif 'zależ' in intention:
                relationship_type = 'depends'
            
            actions.append({
                'type': 'create_relationship',
                'data': {
                    'source_soul': selected_nodes[0],
                    'target_soul': selected_nodes[1],
                    'genesis': {
                        'type': relationship_type,
                        'created_via': 'intention',
                        'description': f'Relacja utworzona przez intencję: {intention}'
                    },
                    'tags': [relationship_type, 'intention'],
                    'energy_level': 60,
                    'attributes': {'created_via': 'intention', 'intention_text': intention}
                }
            })
            message = f"Utworzono relację typu {relationship_type}"
        else:
            message = "Aby połączyć byty, wybierz najpierw co najmniej 2 węzły w grafie."
    
    # Rozpoznawanie intencji wyszukiwania
    elif any(keyword in intention for keyword in find_keywords):
        message = "Funkcja wyszukiwania zostanie wkrótce dodana."
    
    else:
        message = "Nie rozpoznano intencji. Spróbuj opisać co chcesz zrobić używając słów: utwórz, połącz, znajdź."
    
    return {
        'message': message,
        'actions': actions,
        'intention': intention,
        'context': context
    }

async def send_graph_data(sid):
    """Wysyła dane grafu do konkretnego klienta"""
    try:
        beings = await BaseBeing.get_all()
        relationships = await Relationship.get_all()

        # Konwertuj datetime i UUID na string
        nodes = []
        for being in beings:
            being_dict = asdict(being)
            # Konwersja datetime
            if being_dict.get('created_at'):
                being_dict['created_at'] = being_dict['created_at'].isoformat()
            # Upewnij się, że soul jest stringiem
            being_dict['soul'] = str(being_dict['soul'])
            nodes.append(being_dict)
        
        links = []
        for rel in relationships:
            rel_dict = asdict(rel)
            # Konwersja datetime
            if rel_dict.get('created_at'):
                rel_dict['created_at'] = rel_dict['created_at'].isoformat()
            # Upewnij się, że UUID są stringami
            rel_dict['id'] = str(rel_dict['id'])
            rel_dict['source_soul'] = str(rel_dict['source_soul'])
            rel_dict['target_soul'] = str(rel_dict['target_soul'])
            links.append(rel_dict)

        graph_data = {
            'nodes': nodes,
            'links': links
        }

        await sio.emit('graph_data', graph_data, room=sid)
    except Exception as e:
        print(f"Błąd w send_graph_data: {e}")
        await sio.emit('error', {'message': f'Błąd ładowania danych: {str(e)}'}, room=sid)

async def broadcast_graph_update():
    """Rozgłasza aktualizację grafu do wszystkich klientów"""
    try:
        beings = await BaseBeing.get_all()
        relationships = await Relationship.get_all()

        # Konwertuj datetime i UUID na string
        nodes = []
        for being in beings:
            being_dict = asdict(being)
            # Konwersja datetime
            if being_dict.get('created_at'):
                being_dict['created_at'] = being_dict['created_at'].isoformat()
            # Upewnij się, że soul jest stringiem
            being_dict['soul'] = str(being_dict['soul'])
            nodes.append(being_dict)
        
        links = []
        for rel in relationships:
            rel_dict = asdict(rel)
            # Konwersja datetime
            if rel_dict.get('created_at'):
                rel_dict['created_at'] = rel_dict['created_at'].isoformat()
            # Upewnij się, że UUID są stringami
            rel_dict['id'] = str(rel_dict['id'])
            rel_dict['source_soul'] = str(rel_dict['source_soul'])
            rel_dict['target_soul'] = str(rel_dict['target_soul'])
            links.append(rel_dict)

        graph_data = {
            'nodes': nodes,
            'links': links
        }

        await sio.emit('graph_updated', graph_data)
    except Exception as e:
        print(f"Błąd w broadcast_graph_update: {e}")

# HTTP API endpoints
async def api_beings(request):
    """REST API dla bytów"""
    if request.method == 'GET':
        beings = await BaseBeing.get_all()
        beings_data = []
        for being in beings:
            being_dict = asdict(being)
            if being_dict.get('created_at'):
                being_dict['created_at'] = being_dict['created_at'].isoformat()
            being_dict['soul'] = str(being_dict['soul'])
            beings_data.append(being_dict)
        return web.json_response(beings_data)
    elif request.method == 'POST':
        data = await request.json()
        being = await BaseBeing.create(**data)
        being_dict = asdict(being)
        if being_dict.get('created_at'):
            being_dict['created_at'] = being_dict['created_at'].isoformat()
        being_dict['soul'] = str(being_dict['soul'])
        return web.json_response(being_dict)

async def api_relationships(request):
    """REST API dla relacji"""
    if request.method == 'GET':
        relationships = await Relationship.get_all()
        relationships_data = []
        for rel in relationships:
            rel_dict = asdict(rel)
            if rel_dict.get('created_at'):
                rel_dict['created_at'] = rel_dict['created_at'].isoformat()
            rel_dict['id'] = str(rel_dict['id'])
            rel_dict['source_soul'] = str(rel_dict['source_soul'])
            rel_dict['target_soul'] = str(rel_dict['target_soul'])
            relationships_data.append(rel_dict)
        return web.json_response(relationships_data)
    elif request.method == 'POST':
        data = await request.json()
        relationship = await Relationship.create(**data)
        rel_dict = asdict(relationship)
        if rel_dict.get('created_at'):
            rel_dict['created_at'] = rel_dict['created_at'].isoformat()
        rel_dict['id'] = str(rel_dict['id'])
        rel_dict['source_soul'] = str(rel_dict['source_soul'])
        rel_dict['target_soul'] = str(rel_dict['target_soul'])
        return web.json_response(rel_dict)

async def init_database():
    """Inicjalizuje połączenie z bazą danych i tworzy tabele"""
    global db_pool

    # Próba połączenia z PostgreSQL, fallback na SQLite
    try:
        db_pool = await asyncpg.create_pool(
            host='ep-odd-tooth-a2zcp5by-pooler.eu-central-1.aws.neon.tech',
            port=5432,
            user='neondb_owner',
            password='npg_aY8K9pijAnPI',
            database='neondb',
            min_size=1,
            max_size=5,
            server_settings={
                'statement_cache_size': '0'  # Wyłącz cache statementów
            }
        )
        print("Połączono z PostgreSQL")
        await setup_postgresql_tables()
    except Exception as e:
        print(f"Nie udało się połączyć z PostgreSQL: {e}")
        print("Używam SQLite jako fallback")
        db_pool = await aiosqlite.connect('luxos.db')
        await setup_sqlite_tables()

async def setup_postgresql_tables():
    """Tworzy tabele w PostgreSQL"""
    async with db_pool.acquire() as conn:
        # Tabela base_beings
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS base_beings (
                soul UUID PRIMARY KEY,
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
                source_soul UUID NOT NULL,
                target_soul UUID NOT NULL,
                genesis JSONB NOT NULL,
                attributes JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Constraints dla relationships
        await conn.execute("""
            ALTER TABLE relationships 
            DROP CONSTRAINT IF EXISTS valid_source_soul
        """)
        await conn.execute("""
            ALTER TABLE relationships 
            ADD CONSTRAINT valid_source_soul 
            FOREIGN KEY (source_soul) REFERENCES base_beings (soul)
        """)
        
        await conn.execute("""
            ALTER TABLE relationships 
            DROP CONSTRAINT IF EXISTS valid_target_soul
        """)
        await conn.execute("""
            ALTER TABLE relationships 
            ADD CONSTRAINT valid_target_soul 
            FOREIGN KEY (target_soul) REFERENCES base_beings (soul)
        """)
        
        await conn.execute("""
            ALTER TABLE relationships 
            DROP CONSTRAINT IF EXISTS no_self_relationship
        """)
        await conn.execute("""
            ALTER TABLE relationships 
            ADD CONSTRAINT no_self_relationship 
            CHECK (source_soul <> target_soul)
        """)

        # Indeksy
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_genesis ON base_beings USING gin (genesis)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_attributes ON base_beings USING gin (attributes)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_memories ON base_beings USING gin (memories)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_self_awareness ON base_beings USING gin (self_awareness)")

        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_genesis ON relationships USING gin (genesis)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_attributes ON relationships USING gin (attributes)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships (source_soul)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships (target_soul)")

async def setup_sqlite_tables():
    """Tworzy tabele w SQLite"""
    await db_pool.execute("""
        CREATE TABLE IF NOT EXISTS base_beings (
            soul TEXT PRIMARY KEY,
            tags TEXT DEFAULT '[]',
            energy_level INTEGER DEFAULT 0,
            genesis TEXT NOT NULL,
            attributes TEXT NOT NULL,
            memories TEXT NOT NULL,
            self_awareness TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await db_pool.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            id TEXT PRIMARY KEY,
            tags TEXT DEFAULT '[]',
            energy_level INTEGER DEFAULT 0,
            source_soul TEXT NOT NULL,
            target_soul TEXT NOT NULL,
            genesis TEXT NOT NULL,
            attributes TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await db_pool.commit()

# Konfiguracja aplikacji
async def init_app():
    # Redirect root to landing page
    async def serve_landing(request):
        return web.FileResponse('static/landing.html')

    app.router.add_get('/', serve_landing)

    # Serwowanie plików statycznych
    app.router.add_static('/', 'static', name='static')

    # Dodaj trasy API
    app.router.add_route('GET', '/api/beings', api_beings)
    app.router.add_route('POST', '/api/beings', api_beings)
    app.router.add_route('GET', '/api/relationships', api_relationships)
    app.router.add_route('POST', '/api/relationships', api_relationships)

    # Konfiguracja CORS tylko dla tras API
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })

    # Dodaj CORS tylko do tras API (pomiń Socket.IO)
    for route in list(app.router.routes()):
        if hasattr(route, 'resource') and route.resource.canonical.startswith('/api/'):
            cors.add(route)

    await init_database()

async def main():
    await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    await site.start()
    print("Serwer uruchomiony na http://0.0.0.0:5000")
    
    # Trzymaj serwer żywy
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())