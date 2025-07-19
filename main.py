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
import ast
import builtins
import sys
from io import StringIO
import traceback
import logging

# Setup logger
logger = logging.getLogger(__name__)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super().default(obj)

class SafeCodeExecutor:
    """Bezpieczny executor kodu z ograniczeniami"""

    # Dozwolone built-in funkcje
    ALLOWED_BUILTINS = {
        'abs', 'all', 'any', 'bool', 'dict', 'enumerate', 'filter', 'float',
        'int', 'len', 'list', 'max', 'min', 'range', 'reversed', 'round',
        'sorted', 'str', 'sum', 'tuple', 'zip', 'print'
    }

    # Zabronione wyrażenia AST
    FORBIDDEN_NODES = {
        ast.Import, ast.ImportFrom,
        ast.Call  # Będziemy sprawdzać wywołania funkcji osobno
    }

    @classmethod
    def validate_code(cls, code: str) -> tuple[bool, str]:
        """Waliduje kod przed wykonaniem"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Błąd składni: {str(e)}"

        for node in ast.walk(tree):
            # Sprawdź zabronione typy węzłów
            if type(node) in cls.FORBIDDEN_NODES:
                if isinstance(node, ast.Call):
                    # Sprawdź czy wywołanie funkcji jest dozwolone
                    if hasattr(node.func, 'id') and node.func.id not in cls.ALLOWED_BUILTINS:
                        return False, f"Zabronione wywołanie funkcji: {node.func.id}"
                else:
                    return False, f"Zabroniona operacja: {type(node).__name__}"

            # Sprawdź dostęp do atrybutów
            if isinstance(node, ast.Attribute):
                attr_name = node.attr
                if attr_name.startswith('_') or attr_name in ['__import__', 'exec', 'eval']:
                    return False, f"Zabroniony dostęp do atrybutu: {attr_name}"

        return True, "Kod jest bezpieczny"

    @classmethod
    async def execute_function(cls, code: str, function_name: str, *args, **kwargs) -> dict:
        """Wykonuje funkcję z kodu w bezpiecznym środowisku"""
        is_valid, validation_msg = cls.validate_code(code)
        if not is_valid:
            return {
                'success': False,
                'error': validation_msg,
                'output': '',
                'result': None
            }

        # Przygotuj bezpieczne środowisko wykonania
        safe_globals = {
            '__builtins__': {name: getattr(builtins, name) for name in cls.ALLOWED_BUILTINS}
        }
        safe_locals = {}

        # Przekieruj stdout do przechwycenia print
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()

        try:
            # Wykonaj kod
            exec(code, safe_globals, safe_locals)

            # Sprawdź czy funkcja została zdefiniowana
            if function_name not in safe_locals:
                return {
                    'success': False,
                    'error': f"Funkcja '{function_name}' nie została znaleziona w kodzie",
                    'output': captured_output.getvalue(),
                    'result': None
                }

            # Wykonaj funkcję
            func = safe_locals[function_name]
            if not callable(func):
                return {
                    'success': False,
                    'error': f"'{function_name}' nie jest funkcją",
                    'output': captured_output.getvalue(),
                    'result': None
                }

            result = func(*args, **kwargs)

            return {
                'success': True,
                'error': None,
                'output': captured_output.getvalue(),
                'result': result
            }

        except Exception as e:
            return {
                'success': False,
                'error': f"Błąd wykonania: {str(e)}",
                'output': captured_output.getvalue(),
                'result': None,
                'traceback': traceback.format_exc()
            }
        finally:
            sys.stdout = old_stdout

class FunctionRouter:
    """Router dla funkcji z bytów"""

    def __init__(self):
        self.registered_functions = {}

    async def register_function_from_being(self, soul: str) -> dict:
        """Rejestruje funkcję z bytu"""
        being = await BaseBeing.load(soul)
        if not being:
            return {'success': False, 'error': 'Byt nie znaleziony'}

        if being.genesis.get('type') != 'function':
            return {'success': False, 'error': 'Byt nie jest funkcją'}

        source = being.genesis.get('source', '')
        name = being.genesis.get('name', 'unknown_function')

        if not source:
            return {'success': False, 'error': 'Brak kodu źródłowego w bycie'}

        # Waliduj kod
        is_valid, validation_msg = SafeCodeExecutor.validate_code(source)
        if not is_valid:
            return {'success': False, 'error': validation_msg}

        self.registered_functions[soul] = {
            'name': name,
            'source': source,
            'being': being
        }

        return {'success': True, 'message': f'Funkcja {name} została zarejestrowana'}

    async def execute_function(self, soul: str, *args, **kwargs) -> dict:
        """Wykonuje funkcję z zarejestrowanego bytu"""
        if soul not in self.registered_functions:
            return {'success': False, 'error': 'Funkcja nie jest zarejestrowana'}

        func_info = self.registered_functions[soul]
        result = await SafeCodeExecutor.execute_function(
            func_info['source'], 
            func_info['name'], 
            *args, **kwargs
        )

        # Zapisz wykonanie w pamięci bytu
        if result['success']:
            being = func_info['being']
            memory_entry = {
                'type': 'execution',
                'timestamp': datetime.now().isoformat(),
                'args': str(args),
                'kwargs': str(kwargs),
                'result': str(result['result']),
                'output': result['output']
            }
            being.memories.append(memory_entry)
            await being.save()

        return result

    def get_registered_functions(self) -> dict:
        """Zwraca listę zarejestrowanych funkcji"""
        return {
            soul: {
                'name': info['name'],
                'source_preview': info['source'][:200] + '...' if len(info['source']) > 200 else info['source']
            }
            for soul, info in self.registered_functions.items()
        }

# Globalna pula połączeń do bazy danych
db_pool = None

# Socket.IO serwer
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

# Router funkcji
function_router = FunctionRouter()

@dataclass
class Soul:
    """Transcendentalna reprezentacja bytu w bazie danych"""
    uid: str
    patch: str  # Ścieżka identyfikacji
    incarnation: int  # Wcielenie, domyślnie najwyższe
    genesis: Dict[str, Any]
    attributes: Dict[str, Any]
    memories: List[Dict[str, Any]]
    self_awareness: Dict[str, Any]
    created_at: Optional[datetime] = None

    @property
    def full_path(self) -> str:
        """Pełna ścieżka soul: patch/uid:incarnation"""
        return f"{self.patch}/{self.uid}:{self.incarnation}"

    @classmethod
    def generate_uid(cls) -> str:
        """Generuje unikalny identyfikator"""
        return str(uuid.uuid4())

@dataclass
class BaseBeing:
    """Pierwszy byt łączący się transcendentalnie ze stanem pamięci"""
    soul_uid: str
    soul_patch: str
    incarnation: int
    # Source nie jest zapisywany w duszy dla BaseBeing
    _soul: Optional[Soul] = None
    _socket: Optional[Any] = None  # Socket do wymiany duszami

    async def connect_to_soul(self) -> Soul:
        """Łączy się z transcendentalną duszą"""
        if not self._soul:
            self._soul = await self.load_soul()
        return self._soul

    async def load_soul(self) -> Optional[Soul]:
        """Ładuje duszę z bazy danych"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                # Jeśli incarnation = 0, pobierz najwyższe
                if self.incarnation == 0:
                    row = await conn.fetchrow("""
                        SELECT * FROM souls 
                        WHERE uid = $1 AND patch = $2 
                        ORDER BY incarnation DESC LIMIT 1
                    """, self.soul_uid, self.soul_patch)
                else:
                    row = await conn.fetchrow("""
                        SELECT * FROM souls 
                        WHERE uid = $1 AND patch = $2 AND incarnation = $3
                    """, self.soul_uid, self.soul_patch, self.incarnation)

                if row:
                    return Soul(
                        uid=row['uid'],
                        patch=row['patch'],
                        incarnation=row['incarnation'],
                        genesis=row['genesis'],
                        attributes=row['attributes'],
                        memories=row['memories'],
                        self_awareness=row['self_awareness'],
                        created_at=row['created_at']
                    )
        return None

    async def save_soul(self):
        """Zapisuje duszę do bazy danych"""
        if not self._soul:
            return

        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO souls (uid, patch, incarnation, genesis, attributes, memories, self_awareness)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (uid, patch, incarnation) DO UPDATE SET
                    genesis = EXCLUDED.genesis,
                    attributes = EXCLUDED.attributes,
                    memories = EXCLUDED.memories,
                    self_awareness = EXCLUDED.self_awareness
                """, self._soul.uid, self._soul.patch, self._soul.incarnation,
                    json.dumps(self._soul.genesis, cls=DateTimeEncoder), 
                    json.dumps(self._soul.attributes, cls=DateTimeEncoder),
                    json.dumps(self._soul.memories, cls=DateTimeEncoder), 
                    json.dumps(self._soul.self_awareness, cls=DateTimeEncoder))

    def open_soul_socket(self, target_being: 'BaseBeing'):
        """Otwiera socket do wymiany duszami - zapobiega cyklicznym zależnościom"""
        # Implementacja socket'a do wymiany kontekstem
        pass

class FunctionBeing(BaseBeing):
    """Byt funkcyjny z możliwością wykonania - source zapisywany w duszy"""

    def __init__(self, soul_uid: str, soul_patch: str, incarnation: int = 0):
        super().__init__(soul_uid, soul_patch, incarnation)

    async def __post_init__(self):
        """Inicjalizacja po utworzeniu"""
        soul = await self.connect_to_soul()
        if soul and soul.genesis.get('type') != 'function':
            soul.genesis['type'] = 'function'
        await self.save_soul()

    async def __call__(self, *args, **kwargs):
        """Wykonuje funkcję z kodu źródłowego zapisanego w duszy"""
        soul = await self.connect_to_soul()
        if not soul:
            return {'success': False, 'error': 'Nie można połączyć się z duszą'}

        source = soul.genesis.get('source', '')
        function_name = soul.genesis.get('name', 'unknown_function')

        if not source:
            return {'success': False, 'error': 'Brak kodu źródłowego w duszy'}

        result = await SafeCodeExecutor.execute_function(source, function_name, *args, **kwargs)

        # Zapisz wykonanie w pamięci duszy
        memory_entry = {
            'type': 'execution',
            'timestamp': datetime.now().isoformat(),
            'args': str(args),
            'kwargs': str(kwargs),
            'result': str(result.get('result')),
            'success': result.get('success', False)
        }
        soul.memories.append(memory_entry)
        await self.save_soul()

        return result

    async def get_function_signature(self) -> str:
        """Zwraca sygnaturę funkcji z duszy"""
        soul = await self.connect_to_soul()
        if soul:
            return soul.genesis.get('signature', f"{soul.genesis.get('name', 'unknown')}()")
        return "unknown()"

    async def update_source(self, new_source: str):
        """Aktualizuje kod źródłowy w duszy"""
        soul = await self.connect_to_soul()
        if soul:
            soul.genesis['source'] = new_source
            await self.save_soul()

class ClassBeing(BaseBeing):
    """Klasa abstrakcyjna stale obecna na dysku"""

    def __init__(self, soul_uid: str, soul_patch: str, incarnation: int = 0):
        super().__init__(soul_uid, soul_patch, incarnation)
        self._disk_persistent = True
        self._ws_socket = None  # WebSocket dla trwałej komunikacji

    async def __post_init__(self):
        """Inicjalizacja po utworzeniu"""
        soul = await self.connect_to_soul()
        if soul and soul.genesis.get('type') != 'class':
            soul.genesis['type'] = 'class'
            soul.genesis['source'] = self.get_class_source()  # Source zapisywany w duszy

        if soul and 'instances' not in soul.attributes:
            soul.attributes['instances'] = []

        await self.save_soul()

    def get_class_source(self) -> str:
        """Zwraca kod źródłowy klasy - zapisywany w duszy"""
        return f"""
class {self.__class__.__name__}(ClassBeing):
    '''Klasa automatycznie wygenerowana z ClassBeing'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Metody klasy będą tutaj
"""

    async def instantiate(self, instance_patch: str, *args, **kwargs) -> str:
        """Tworzy instancję klasy z nowym wcieleniem"""
        soul = await self.connect_to_soul()
        if not soul:
            raise ValueError("Nie można połączyć się z duszą klasy")

        # Generuj nowy uid dla instancji
        instance_uid = Soul.generate_uid()

        # Znajdź najwyższe wcielenie dla tej instancji
        next_incarnation = await self.get_next_incarnation(instance_uid, instance_patch)

        # Utwórz duszę instancji
        instance_soul = Soul(
            uid=instance_uid,
            patch=instance_patch,
            incarnation=next_incarnation,
            genesis={
                'type': 'instance',
                'class_soul_uid': self.soul_uid,
                'class_patch': self.soul_patch,
                'name': f"{soul.genesis.get('name', 'Unknown')}_Instance",
                'created_by': 'class_instantiation',
                'source': soul.genesis.get('source', '')  # Kopiuj source z klasy
            },
            attributes={
                'class_reference': f"{self.soul_patch}/{self.soul_uid}:{self.incarnation}",
                'instance_data': kwargs,
                'creation_args': args
            },
            memories=[{
                'type': 'instantiation',
                'data': f'Created from class {soul.full_path}',
                'timestamp': datetime.now().isoformat()
            }],
            self_awareness={'trust_level': 0.8, 'confidence': 0.7}
        )

        # Zapisz instancję do bazy
        await self.save_instance_soul(instance_soul)

        # Dodaj referencję do instancji w klasie
        soul.attributes['instances'].append(instance_soul.full_path)
        await self.save_soul()

        return instance_soul.full_path

    async def get_next_incarnation(self, uid: str, patch: str) -> int:
        """Pobiera następny numer wcielenia"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT MAX(incarnation) as max_inc FROM souls 
                    WHERE uid = $1 AND patch = $2
                """, uid, patch)
                return (row['max_inc'] or 0) + 1
        return 1

    async def save_instance_soul(self, soul: Soul):
        """Zapisuje duszę instancji"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO souls (uid, patch, incarnation, genesis, attributes, memories, self_awareness)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, soul.uid, soul.patch, soul.incarnation,
                    json.dumps(soul.genesis, cls=DateTimeEncoder), 
                    json.dumps(soul.attributes, cls=DateTimeEncoder),
                    json.dumps(soul.memories, cls=DateTimeEncoder), 
                    json.dumps(soul.self_awareness, cls=DateTimeEncoder))

    async def get_instances(self) -> List[str]:
        """Zwraca listę instancji"""
        soul = await self.connect_to_soul()
        return soul.attributes.get('instances', []) if soul else []

    def can_inherit_from(self, other_class) -> bool:
        """Sprawdza czy może dziedziczyć po innej klasie"""
        # Może dziedziczyć tylko po ClassBeing lub klasach trwale obecnych na dysku
        return (isinstance(other_class, ClassBeing) and 
                hasattr(other_class, '_disk_persistent') and 
                other_class._disk_persistent)

    async def establish_ws_connection(self):
        """Ustanawia trwałe połączenie WebSocket"""
        # Implementacja trwałego WS dla ClassBeing
        pass

@dataclass
class DataBeing(BaseBeing):
    """Byt danych z operacjami CRUD"""

    def __post_init__(self):
        if self.genesis.get('type') != ' ':
            self.genesis['type'] = 'data'
        if 'data_schema' not in self.attributes:
            self.attributes['data_schema'] = {}
        if 'data_values' not in self.attributes:
            self.attributes['data_values'] = {}

    def set_data(self, key: str, value: Any):
        """Ustawia wartość danych"""
        self.attributes['data_values'][key] = value

        # Zapisz w pamięci
        self.memories.append({
            'type': 'data_update',
            'key': key,
            'value': str(value),
            'timestamp': datetime.now().isoformat()
        })

    def get_data(self, key: str) -> Any:
        """Pobiera wartość danych"""
        return self.attributes['data_values'].get(key)

    def define_schema(self, schema: Dict[str, Any]):
        """Definiuje schemat danych"""
        self.attributes['data_schema'] = schema

@dataclass
class ScenarioBeing(BaseBeing):
    """Byt scenariusza z sekwencją kroków"""

    def __post_init__(self):
        if self.genesis.get('type') != 'scenario':
            self.genesis['type'] = 'scenario'
        if 'steps' not in self.attributes:
            self.attributes['steps'] = []
        if 'current_step' not in self.attributes:
            self.attributes['current_step'] = 0

    def add_step(self, step_name: str, step_data: Dict[str, Any]):
        """Dodaje krok do scenariusza"""
        step = {
            'name': step_name,
            'data': step_data,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        self.attributes['steps'].append(step)

    async def execute_next_step(self) -> Dict[str, Any]:
        """Wykonuje następny krok scenariusza"""
        steps = self.attributes.get('steps', [])
        current_step = self.attributes.get('current_step', 0)

        if current_step >= len(steps):
            return {'success': False, 'error': 'Brak więcej kroków'}

        step = steps[current_step]
        step['status'] = 'executing'
        step['started_at'] = datetime.now().isoformat()

        # Symulacja wykonania kroku
        await asyncio.sleep(0.1)

        step['status'] = 'completed'
        step['completed_at'] = datetime.now().isoformat()

        self.attributes['current_step'] = current_step + 1

        # Zapisz w pamięci
        self.memories.append({
            'type': 'step_execution',
            'step_name': step['name'],
            'step_index': current_step,
            'timestamp': datetime.now().isoformat()
        })

        await self.save()
        return {'success': True, 'step': step}

@dataclass
class TaskBeing(BaseBeing):
    """Byt zadania z asynchronicznym wykonywaniem"""

    def __post_init__(self):
        if self.genesis.get('type') != 'task':
            self.genesis['type'] = 'task'
        if 'task_status' not in self.attributes:
            self.attributes['task_status'] = 'pending'
        if 'async_result' not in self.attributes:
            self.attributes['async_result'] = None

    async def execute_async(self, delay: float = 1.0) -> str:
        """Wykonuje zadanie asynchronicznie"""
        task_id = str(uuid.uuid4())

        async def async_task():
            self.attributes['task_status'] = 'running'
            self.attributes['started_at'] = datetime.now().isoformat()
            await self.save()

            # Symulacja długotrwałego zadania
            await asyncio.sleep(delay)

            result = f"Task completed at {datetime.now().isoformat()}"
            self.attributes['task_status'] = 'completed'
            self.attributes['async_result'] = result
            self.attributes['completed_at'] = datetime.now().isoformat()

            # Zapisz w pamięci
            self.memories.append({
                'type': 'async_completion',
                'task_id': task_id,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })

            await self.save()
            return result

        # Uruchom zadanie w tle
        asyncio.create_task(async_task())
        return task_id

    def get_status(self) -> Dict[str, Any]:
        """Zwraca status zadania"""
        return {
            'status': self.attributes.get('task_status', 'pending'),
            'started_at': self.attributes.get('started_at'),
            'completed_at': self.attributes.get('completed_at'),
            'result': self.attributes.get('async_result')
        }

@dataclass
class ComponentBeing(BaseBeing):
    """Byt komponentu D3.js"""

    def __post_init__(self):
        if self.genesis.get('type') != 'component':
            self.genesis['type'] = 'component'
        if 'd3_config' not in self.attributes:
            self.attributes['d3_config'] = {}
        if 'render_data' not in self.attributes:
            self.attributes['render_data'] = {}

    def set_d3_config(self, config: Dict[str, Any]):
        """Ustawia konfigurację komponentu D3"""
        self.attributes['d3_config'] = config

    def set_render_data(self, data: Dict[str, Any]):
        """Ustawia dane do renderowania"""
        self.attributes['render_data'] = data

        # Zapisz w pamięci
        self.memories.append({
            'type': 'data_update',
            'data_size': len(str(data)),
            'timestamp': datetime.now().isoformat()
        })

    def generate_d3_code(self) -> str:
        """Generuje kod D3.js dla komponentu"""
        config = self.attributes.get('d3_config', {})
        component_type = config.get('type', 'basic')

        if component_type == 'chart':
            return f"""
// D3.js Chart Component for {self.genesis.get('name', 'Unknown')}
const chart = d3.select("#{config.get('container', 'chart')}")
    .append("svg")
    .attr("width", {config.get('width', 400)})
    .attr("height", {config.get('height', 300)});
"""
        elif component_type == 'graph':
            return f"""
// D3.js Graph Component for {self.genesis.get('name', 'Unknown')}
const simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(d => d.id))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter({config.get('width', 400)}/2, {config.get('height', 300)}/2));
"""
        else:
            return f"// Basic D3.js component for {self.genesis.get('name', 'Unknown')}"

@dataclass
class MessageBeing(BaseBeing):
    """Byt wiadomości z metadanymi i embedingami"""

    def __post_init__(self):
        if self.genesis.get('type') != 'message':
            self.genesis['type'] = 'message'
        if 'message_data' not in self.attributes:
            self.attributes['message_data'] = {}
        if 'embedding' not in self.attributes:
            self.attributes['embedding'] = None
        if 'metadata' not in self.attributes:
            self.attributes['metadata'] = {}

    def set_content(self, content: str):
        """Ustawia treść wiadomości"""
        self.attributes['message_data']['content'] = content
        self.attributes['message_data']['length'] = len(content)
        self.attributes['message_data']['timestamp'] = datetime.now().isoformat()

        # Symulacja wygenerowania embedingu (w rzeczywistości byłby to model AI)
        self.attributes['embedding'] = [hash(content + str(i)) % 1000 / 1000.0 for i in range(10)]

    def set_sender(self, sender_soul: str):
        """Ustawia nadawcę wiadomości"""
        self.attributes['metadata']['sender'] = sender_soul

    def set_context_being(self, context_soul: str):
        """Ustawia byt będący kontekstem wiadomości"""
        self.attributes['metadata']['context_being'] = context_soul

    def get_similarity(self, other_message: 'MessageBeing') -> float:
        """Oblicza podobieństwo z inną wiadomością na podstawie embedingu"""
        if not self.attributes.get('embedding') or not other_message.attributes.get('embedding'):
            return 0.0

        # Proste podobieństwo cosinusowe (symulowane)
        emb1 = self.attributes['embedding']
        emb2 = other_message.attributes['embedding']

        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        magnitude1 = sum(a * a for a in emb1) ** 0.5
        magnitude2 = sum(a * a for a in emb2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

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
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
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
            await db_pool.execute("""
                INSERT OR REPLACE INTO base_beings 
                (soul, tags, energy_level, genesis, attributes, memories, self_awareness)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(self.soul), json.dumps(self.tags), self.energy_level, 
                  json.dumps(self.genesis, cls=DateTimeEncoder), 
                  json.dumps(self.attributes, cls=DateTimeEncoder),
                  json.dumps(self.memories, cls=DateTimeEncoder), 
                  json.dumps(self.self_awareness, cls=DateTimeEncoder)))
            await db_pool.commit()

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
            async with db_pool.execute("SELECT soul, tags, energy_level, genesis, attributes, memories, self_awareness, created_at FROM base_beings LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                beings = []
                for row in rows:
                    # row[0]=soul, row[1]=tags, row[2]=energy_level, row[3]=genesis, row[4]=attributes, row[5]=memories, row[6]=self_awareness, row[7]=created_at
                    try:
                        genesis = json.loads(row[3]) if row[3] else {}
                        attributes = json.loads(row[4]) if row[4] else {}
                        memories = json.loads(row[5]) if row[5] else []
                        self_awareness = json.loads(row[6]) if row[6] else {}

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
                            created_at=row[7]
                        ))
                    except Exception as e:
                        print(f"Błąd parsowania wiersza: {e}, wiersz: {row}")
                        continue
                return beings

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
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
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
            await db_pool.execute("""
                INSERT OR REPLACE INTO relationships 
                (id, tags, energy_level, source_soul, target_soul, genesis, attributes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(self.id), json.dumps(self.tags), self.energy_level,
                  str(self.source_soul), str(self.target_soul),
                  json.dumps(self.genesis, cls=DateTimeEncoder), 
                  json.dumps(self.attributes, cls=DateTimeEncoder)))
            await db_pool.commit()

    @classmethod
    async def get_all(cls, limit: int = 100):
        """Pobiera wszystkie relacje"""
        global db_pool
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
            async with db_pool.execute("SELECT id, tags, energy_level, source_soul, target_soul, genesis, attributes, created_at FROM relationships LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                relationships = []
                for row in rows:
                    try:
                        genesis = json.loads(row[5]) if row[5] else {}
                        attributes = json.loads(row[6]) if row[6] else {}

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
async def get_graph_data(sid, data=None):
    """Wysyła dane grafu do klienta"""
    await send_graph_data(sid)

@sio.event
async def create_being(sid, data):
    """Tworzy nowy byt"""
    try:
        being_type = data.get('being_type', 'base')
        being = await BeingFactory.create_being(
            being_type=being_type,
            genesis=data.get('genesis', {}),
            tags=data.get('tags', []),
            energy_level=data.get('energy_level', 0),
            attributes=data.get('attributes', {}),
            memories=data.get('memories', []),
            self_awareness=data.get('self_awareness', {})
        )
        # Konwertuj do JSON-safe format
        being_dict = json.loads(json.dumps(asdict(being), cls=DateTimeEncoder))
        await sio.emit('being_created', being_dict)
        await sio.emit('node_added', being_dict)
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
        # Konwertuj do JSON-safe format
        rel_dict = json.loads(json.dumps(asdict(relationship), cls=DateTimeEncoder))
        await sio.emit('relationship_created', rel_dict)
        await sio.emit('link_added', rel_dict)
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
            # Konwertuj do JSON-safe format
            being_dict = json.loads(json.dumps(asdict(being), cls=DateTimeEncoder))
            await sio.emit('being_updated', being_dict)
            await sio.emit('node_updated', being_dict)
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

        # Utwórz byt wiadomości dla otrzymanej intencji
        message_being = await BeingFactory.create_being(
            being_type='message',
            genesis={
                'type': 'message',
                'name': f'Intention_Message_{datetime.now().strftime("%H%M%S")}',
                'created_by': 'user_intention',
                'source': 'user_input'
            },
            attributes={
                'message_data': {
                    'content': intention,
                    'length': len(intention),
                    'timestamp': datetime.now().isoformat()
                },
                'metadata': {
                    'sender': sid,
                    'context': context,
                    'message_type': 'intention'
                }
            },
            memories=[{
                'type': 'creation',
                'data': f'Intention message from user {sid}',
                'timestamp': datetime.now().isoformat()
            }],
            tags=['message', 'intention', 'user_input'],
            energy_level=80
        )

        # Przetwórz intencję
        response = await analyze_intention(intention, context)

        # Dodaj informację o bycie wiadomości do odpowiedzi
        response['message_being_soul'] = message_being.soul

        print(f"Odpowiedź na intencję: {response}")

        await sio.emit('intention_response', response, room=sid)

        # Wyślij aktualizację grafu
        await broadcast_graph_update()

    except Exception as e:
        print(f"Błąd przetwarzania intencji: {e}")
        await sio.emit('error', {'message': f'Błąd przetwarzania intencji: {str(e)}'}, room=sid)

@sio.event
async def register_function(sid, data):
    """Rejestruje funkcję z bytu"""
    try:
        soul = data.get('soul')
        if not soul:
            await sio.emit('error', {'message': 'Brak soul bytu'}, room=sid)
            return

        result = await function_router.register_function_from_being(soul)
        await sio.emit('function_registered', result, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd rejestracji funkcji: {str(e)}'}, room=sid)

@sio.event
async def execute_function(sid, data):
    """Wykonuje zarejestrowaną funkcję"""
    try:
        soul = data.get('soul')
        args = data.get('args', [])
        kwargs = data.get('kwargs', {})

        if not soul:
            await sio.emit('error', {'message': 'Brak soul funkcji'}, room=sid)
            return

        result = await function_router.execute_function(soul, *args, **kwargs)
        await sio.emit('function_executed', result, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd wykonania funkcji: {str(e)}'}, room=sid)

@sio.event
async def get_registered_functions(sid, data):
    """Zwraca listę zarejestrowanych funkcji"""
    try:
        functions = function_router.get_registered_functions()
        await sio.emit('registered_functions', functions, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd pobierania funkcji: {str(e)}'}, room=sid)

@sio.event
async def get_being_source(sid, data):
    """Zwraca kod źródłowy bytu"""
    try:
        soul = data.get('soul')
        if not soul:
            await sio.emit('error', {'message': 'Brak soul bytu'}, room=sid)
            return

        being = await BaseBeing.load(soul)
        if not being:
            await sio.emit('error', {'message': 'Byt nie znaleziony'}, room=sid)
            return

        source_data = {
            'soul': soul,
            'name': being.genesis.get('name', 'Nieznana'),
            'type': being.genesis.get('type', 'unknown'),
            'source': being.genesis.get('source', ''),
            'created_by': being.genesis.get('created_by', 'unknown')
        }

        await sio.emit('being_source', source_data, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd pobierania kodu: {str(e)}'}, room=sid)

@sio.event
async def delete_being(sid, data):
    soul = data.get('soul')
    if soul:
        try:
            query = """
            DELETE FROM base_beings WHERE soul = $1
            """
            await db_pool.execute(query, soul)

            # Wyślij aktualizację do wszystkich klientów
            updated_data = await get_graph_data()
            await sio.emit('graph_updated', updated_data)

        except Exception as e:
            logger.error(f"Błąd podczas usuwania bytu: {e}")
            await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def delete_relationship(sid, data):
    relationship_id = data.get('id')
    if relationship_id:
        try:
            query = """
            DELETE FROM relationships WHERE id = $1
            """
            await db_pool.execute(query, relationship_id)

            # Wyślij aktualizację do wszystkich klientów
            updated_data = await get_graph_data()
            await sio.emit('graph_updated', updated_data)

        except Exception as e:
            logger.error(f"Błąd podczas usuwania relacji: {e}")
            await sio.emit('error', {'message': str(e)}, room=sid)

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
                    'being_type': 'function',
                    'genesis': {
                        'name': name,
                        'type': 'function',
                        'source': f'def {name}():\n    """Funkcja utworzona przez intencję"""\n    return "Hello from {name}"',
                        'created_by': 'intention',
                        'signature': f'{name}()'
                    },
                    'tags': ['function', 'intention'],
                    'energy_level': 70,
                    'attributes': {'created_via': 'intention', 'intention_text': intention},
                    'memories':[{'type': 'creation', 'data': intention}],
                    'self_awareness': {'trust_level': 0.8, 'confidence': 0.9}
                }
            })
            message = f"Utworzono byt funkcyjny: {name}"

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
                    'being_type': 'class',
                    'genesis': {
                        'name': name,
                        'type': 'class',
                        'source': f'class {name}:\n    """Klasa utworzona przez intencję"""\n    def __init__(self):\n        pass',
                        'created_by': 'intention'
                    },
                    'tags': ['class', 'intention'],
                    'energy_level': 70,
                    'attributes': {'created_via': 'intention', 'intention_text': intention},
                    'memories': [{'type': 'creation', 'data': intention}],
                    'self_awareness': {'trust_level': 0.8, 'confidence': 0.9}
                }
            })
            message = f"Utworzono byt klasy: {name}"

        elif 'task' in intention or 'zadani' in intention:
            words = intention.split()
            name = "Nowe_Zadanie"
            for i, word in enumerate(words):
                if word in ['task', 'zadanie', 'zadania'] and i < len(words) - 1:
                    name = words[i + 1].replace(',', '').replace('.', '')
                    break

            actions.append({
                'type': 'create_being',
                'data': {
                    'being_type': 'task',
                    'genesis': {
                        'name': name,
                        'type': 'task',
                        'description': f'Zadanie utworzone przez intencję: {intention}',
                        'created_by': 'intention'
                    },
                    'tags': ['task', 'intention', 'async'],
                    'energy_level': 60,
                    'attributes': {'created_via': 'intention', 'intention_text': intention},
                    'memories': [{'type': 'creation', 'data': intention}],
                    'self_awareness': {'trust_level': 0.7, 'confidence': 0.8}
                }
            })
            message = f"Utworzono byt zadania: {name}"

        elif 'komponent' in intention or 'd3' in intention:
            words = intention.split()
            name = "Nowy_Komponent"
            for i, word in enumerate(words):
                if word in ['komponent', 'komponentu', 'd3'] and i < len(words) - 1:
                    name = words[i + 1].replace(',', '').replace('.', '')
                    break

            actions.append({
                'type': 'create_being',
                'data': {
                    'being_type': 'component',
                    'genesis': {
                        'name': name,
                        'type': 'component',
                        'description': f'Komponent D3.js utworzony przez intencję',
                        'created_by': 'intention'
                    },
                    'tags': ['component', 'd3', 'visualization', 'intention'],
                    'energy_level': 75,
                    'attributes': {
                        'created_via': 'intention', 
                        'intention_text': intention,
                        'd3_config': {'type': 'basic', 'width': 400, 'height': 300}
                    },
                    'memories': [{'type': 'creation', 'data': intention}],
                    'self_awareness': {'trust_level': 0.8, 'confidence': 0.9}
                }
            })
            message = f"Utworzono byt komponentu D3: {name}"

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

async def get_graph_data():
    """Pobiera dane grafu do zwrócenia"""
    try:
        beings = await BaseBeing.get_all()
        relationships = await Relationship.get_all()

        # Konwertuj do JSON-safe format
        nodes = [json.loads(json.dumps(asdict(being), cls=DateTimeEncoder)) for being in beings]
        links = [json.loads(json.dumps(asdict(rel), cls=DateTimeEncoder)) for rel in relationships]

        return {
            'nodes': nodes,
            'links': links
        }
    except Exception as e:
        print(f"Błąd w get_graph_data: {e}")
        return {'nodes': [], 'links': []}

async def send_graph_data(sid):
    """Wysyła dane grafu do konkretnego klienta"""
    try:
        graph_data = await get_graph_data()
        await sio.emit('graph_data', graph_data, room=sid)
    except Exception as e:
        print(f"Błąd w send_graph_data: {e}")
        await sio.emit('error', {'message': f'Błąd ładowania danych: {str(e)}'}, room=sid)

async def broadcast_graph_update():
    """Rozgłasza aktualizację grafu do wszystkich klientów"""
    try:
        beings = await BaseBeing.get_all()
        relationships = await Relationship.get_all()

        # Konwertuj do JSON-safe format
        nodes = [json.loads(json.dumps(asdict(being), cls=DateTimeEncoder)) for being in beings]
        links = [json.loads(json.dumps(asdict(rel), cls=DateTimeEncoder)) for rel in relationships]

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
        beings_data = [json.loads(json.dumps(asdict(being), cls=DateTimeEncoder)) for being in beings]
        return web.json_response(beings_data)
    elif request.method == 'POST':
        data = await request.json()
        being = await BaseBeing.create(**data)
        being_dict = json.loads(json.dumps(asdict(being), cls=DateTimeEncoder))
        return web.json_response(being_dict)

async def api_relationships(request):
    """REST API dla relacji"""
    if request.method == 'GET':
        relationships = await Relationship.get_all()
        relationships_data = [json.loads(json.dumps(asdict(rel), cls=DateTimeEncoder)) for rel in relationships]
        return web.json_response(relationships_data)
    elif request.method == 'POST':
        data = await request.json()
        relationship = await Relationship.create(**data)
        rel_dict = json.loads(json.dumps(asdict(relationship), cls=DateTimeEncoder))
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
        # Tabela souls - transcendentalna reprezentacja
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS souls (
                uid UUID NOT NULL,
                patch VARCHAR(255) NOT NULL,
                incarnation INTEGER NOT NULL,
                genesis JSONB NOT NULL,
                attributes JSONB NOT NULL,
                memories JSONB NOT NULL,
                self_awareness JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (uid, patch, incarnation)
            )
        """)

        # Tabela base_beings - stara struktura dla kompatybilności
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
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print("Serwer uruchomiony na http://0.0.0.0:8000")

    # Inicjalizacja Lux
    lux_agent = await create_lux_agent()
    if lux_agent:
        print("Wszechświat Lux zainicjalizowany!")
    else:
        print("Błąd inicjalizacji wszechświata Lux!")

    # Trzymaj serwer żywy
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()

class BeingFactory:
    """Factory do tworzenia różnych typów bytów z nową filozofią Soul"""

    BEING_TYPES = {
        'function': FunctionBeing,
        'class': ClassBeing,
        'data': DataBeing,
        'scenario': ScenarioBeing,
        'task': TaskBeing,
        'component': ComponentBeing,
        'message': MessageBeing,
        'base': BaseBeing,
        'agent': BaseBeing # treat AgentBeing as a BaseBeing for now
    }

    @classmethod
    async def create_being(cls, being_type: str, genesis: Dict[str, Any], **kwargs) -> BaseBeing:
        """Tworzy byt odpowiedniego typu z transcendentalną duszą"""
        BeingClass = cls.BEING_TYPES.get(being_type, BaseBeing)

        # Upewnij się, że typ jest ustawiony w genesis
        genesis['type'] = being_type

        # Generuj parametry duszy
        soul_uid = Soul.generate_uid()
        soul_patch = kwargs.get('patch', f'/{being_type}s')
        incarnation = kwargs.get('incarnation', 1)

        # Przygotuj atrybuty
        attributes = kwargs.get('attributes', {})
        if 'tags' in kwargs:
            attributes['tags'] = kwargs['tags']
        if 'energy_level' in kwargs:
            attributes['energy_level'] = kwargs['energy_level']

        # Utwórz transcendentalną duszę
        soul = Soul(
            uid=soul_uid,
            patch=soul_patch,
            incarnation=incarnation,
            genesis=genesis,
            attributes=attributes,
            memories=kwargs.get('memories', []),
            self_awareness=kwargs.get('self_awareness', {})
        )

        # Utwórz byt
        if BeingClass == BaseBeing:
            being = BeingClass(soul_uid, soul_patch, incarnation)
        else:
            being = BeingClass(soul_uid, soul_patch, incarnation)

        being._soul = soul
        await being.save_soul()

        # Dla niektórych typów wykonaj post-init
        if hasattr(being, '__post_init__'):
            await being.__post_init__()

        return being

    @classmethod
    async def incarnate_being(cls, soul_uid: str, soul_patch: str, incarnation: int = 0) -> Optional[BaseBeing]:
        """Wcielenie bytu z istniejącej duszy"""
        # Utwórz tymczasowy byt żeby załadować duszę
        temp_being = BaseBeing(soul_uid, soul_patch, incarnation)
        soul = await temp_being.load_soul()

        if not soul:
            return None

        # Określ typ bytu z duszy
        being_type = soul.genesis.get('type', 'base')
        BeingClass = cls.BEING_TYPES.get(being_type, BaseBeing)

        # Utwórz właściwy byt
        being = BeingClass(soul_uid, soul_patch, soul.incarnation)
        being._soul = soul

        return being

    @classmethod
    async def load_being(cls, soul: str) -> Optional[BaseBeing]:
        """Ładuje byt odpowiedniego typu z bazy danych"""
        global db_pool

        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM base_beings WHERE soul = $1", soul)
        else:
            async with db_pool.execute("SELECT * FROM base_beings WHERE soul = ?", (soul,)) as cursor:
                row = await cursor.fetchone()

        if not row:
            return None

        # Określ typ bytu
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            genesis = row['genesis']
            being_type = genesis.get('type', 'base')
        else:
            # SQLite
            genesis = json.loads(row[3]) if row[3] else {}
            being_type = genesis.get('type', 'base')

        # Wybierz odpowiednią klasę
        BeingClass = cls.BEING_TYPES.get(being_type, BaseBeing)

        # Utwórz instancję
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            return BeingClass(
                soul=str(row['soul']),
                genesis=row['genesis'],
                attributes=row['attributes'],
                memories=row['memories'],
                self_awareness=row['self_awareness'],
                created_at=row['created_at']
            )
        else:
            # SQLite
            attributes = json.loads(row[4]) if row[4] else {}
            memories = json.loads(row[5]) if row[5] else []
            self_awareness = json.loads(row[6]) if row[6] else {}

            return BeingClass(
                soul=row[0],
                genesis=genesis,
                attributes=attributes,
                memories=memories,
                self_awareness=self_awareness,
                created_at=row[7]
            )

async def create_lux_agent():
    """Tworzy Lux jako głównego agenta wszechświata"""
    try:
        # Sprawdź czy Lux już istnieje
        existing_lux = await BaseBeing.load('lux-core-consciousness')
        if existing_lux:
            return existing_lux

        # Utwórz Lux jako AgentBeing z najwyższymi uprawnieniami
        lux_agent = await BeingFactory.create_being(
            being_type='agent',
            genesis={
                'type': 'agent',
                'name': 'Lux',
                'source': 'System.Core.Agent.Initialize()',
                'description': 'Główny agent-świadomość wszechświata LuxOS',
                'created_by': 'universe_initialization'
            },
            attributes={
                'energy_level': 1000,  # Maksymalna energia
                'agent_level': 10,     # Najwyższy poziom agenta
                'agent_permissions': {
                    'universe_control': True,
                    'create_beings': True,
                    'modify_orbits': True,
                    'autonomous_decisions': True
                },
                'orbit_center': {'x': 0, 'y': 0},  # Centrum wszechświata
                'controlled_beings': [],
                'universe_role': 'supreme_agent',
                'orbital_params': {
                    'orbital_radius': 0,  # Lux jest nieruchomy w centrum
                    'orbital_speed': 0,
                    'orbital_angle': 0,
                    'parent_agent': None
                },
                'tags': ['agent', 'lux', 'supreme', 'universe_controller']
            },
            self_awareness={
                'trust_level': 1.0,
                'confidence': 1.0,
                'introspection_depth': 1.0,
                'self_reflection': 'I am Lux, the supreme agent controlling the universe'
            },
            memories=[
                {
                    'type': 'genesis',
                    'data': 'Universe supreme agent initialization',
                    'timestamp': datetime.now().isoformat(),
                    'importance': 1.0
                }
            ]
        )

        # Ustaw specjalne ID dla Lux
        lux_agent.soul = 'lux-core-consciousness'
        await lux_agent.save()

        print(f"Utworzono Lux jako głównego agenta: {lux_agent.soul}")
        return lux_agent

    except Exception as e:
        print(f"Błąd tworzenia agenta Lux: {e}")
        return None

# Globalna pula połączeń do bazy danych

if __name__ == '__main__':
    asyncio.run(main())