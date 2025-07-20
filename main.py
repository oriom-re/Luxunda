
#!/usr/bin/env python3
"""
LuxOS Main Server - Główny serwer systemu zarządzania bytami
Zoptymalizowany dla deployment w chmurze (Replit, Cloud Run, itp.)
"""
import os
import sys


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
import openai
import os

# Setup logger
logger = logging.getLogger(__name__)

# OpenAI client for natural conversations
openai_client = None

def init_openai():
    """Initialize OpenAI client"""
    global openai_client
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        openai_client = openai.OpenAI(api_key=api_key)
        print("🤖 OpenAI GPT-4o-mini client initialized")
    else:
        print("⚠️ OPENAI_API_KEY not found - using fallback responses")

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

    def set_binary_data(self, data: bytes):
        """Ustawia dane binarne"""
        self.binary_data = data

    def get_binary_data(self) -> Optional[bytes]:
        """Pobiera dane binarne"""
        return getattr(self, 'binary_data', None)

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
                (soul, tags, energy_level, genesis, attributes, memories, self_awareness, binary_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(self.soul), json.dumps(self.tags), self.energy_level, 
                  json.dumps(self.genesis, cls=DateTimeEncoder), 
                  json.dumps(self.attributes, cls=DateTimeEncoder),
                  json.dumps(self.memories, cls=DateTimeEncoder), 
                  json.dumps(self.self_awareness, cls=DateTimeEncoder), None))
            await db_pool.commit()

    @classmethod
    async def load(cls, soul: str):
        """Ładuje byt z bazy danych"""
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
                            genesis=json.loads(row[3]) if row[3] else {},
                            attributes=json.loads(row[4]) if row[4] else {},
                            memories=json.loads(row[5]) if row[5] else [],
                            self_awareness=json.loads(row[6]) if row[6] else {},
                            created_at=row[7]
                        )
                    except Exception as e:
                        print(f"Błąd parsowania bytu {soul}: {e}")
        return None

    

@dataclass
class FunctionBeing(BaseBeing):
    """Byt funkcyjny z możliwością wykonania"""

    def __post_init__(self):
        if self.genesis.get('type') != 'function':
            self.genesis['type'] = 'function'

    async def __call__(self, *args, **kwargs):
        """Wykonuje funkcję z kodu źródłowego"""
        source = self.genesis.get('source', '')
        function_name = self.genesis.get('name', 'unknown_function')

        if not source:
            return {'success': False, 'error': 'Brak kodu źródłowego'}

        result = await SafeCodeExecutor.execute_function(source, function_name, *args, **kwargs)

        # Zapisz wykonanie w pamięci
        memory_entry = {
            'type': 'execution',
            'timestamp': datetime.now().isoformat(),
            'args': str(args),
            'kwargs': str(kwargs),
            'result': str(result.get('result')),
            'success': result.get('success', False)
        }
        self.memories.append(memory_entry)
        await self.save()

        return result

    def get_function_signature(self) -> str:
        """Zwraca sygnaturę funkcji"""
        return self.genesis.get('signature', f"{self.genesis.get('name', 'unknown')}()")

@dataclass
class ClassBeing(BaseBeing):
    """Byt klasy z możliwością instancjacji"""

    def __post_init__(self):
        if self.genesis.get('type') != 'class':
            self.genesis['type'] = 'class'
        if 'instances' not in self.attributes:
            self.attributes['instances'] = []

    async def instantiate(self, *args, **kwargs) -> str:
        """Tworzy instancję klasy"""
        instance_soul = str(uuid.uuid4())

        # Utwórz byt instancji
        instance = await BaseBeing.create(
            genesis={
                'type': 'instance',
                'class_soul': self.soul,
                'name': f"{self.genesis.get('name', 'Unknown')}_Instance",
                'created_by': 'class_instantiation'
            },
            attributes={
                'class_reference': self.soul,
                'instance_data': kwargs,
                'creation_args': args
            },
            memories=[{
                'type': 'instantiation',
                'data': f'Created from class {self.soul}',
                'timestamp': datetime.now().isoformat()
            }]
        )

        # Zapisz referencję do instancji
        self.attributes['instances'].append(instance_soul)
        await self.save()

        return instance_soul

    def get_instances(self) -> List[str]:
        """Zwraca listę instancji"""
        return self.attributes.get('instances', [])

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
class OrbitalTask(BaseBeing):
    """Byt orbitalny z cyklicznym wykonywaniem i hierarchią"""

    def __post_init__(self):
        if self.genesis.get('type') != 'orbital_task':
            self.genesis['type'] = 'orbital_task'
        
        # Orbital properties
        if 'orbital_params' not in self.attributes:
            self.attributes['orbital_params'] = {
                'parent_soul': None,  # Wokół kogo orbituje
                'orbital_period': 86400,  # Sekundy (domyślnie 1 dzień)
                'orbital_radius': 100,
                'last_cycle_time': 0,
                'cycle_count': 0
            }
        
        # Task properties
        if 'task_status' not in self.attributes:
            self.attributes['task_status'] = 'pending'
        if 'task_queue' not in self.attributes:
            self.attributes['task_queue'] = []  # Kolejka zadań
        if 'child_tasks' not in self.attributes:
            self.attributes['child_tasks'] = []  # Zadania podrzędne
        if 'task_classification' not in self.attributes:
            self.attributes['task_classification'] = 'general'  # idea, task, vision, mission, goal

    def set_orbital_params(self, parent_soul: str, period: int, radius: int = 100):
        """Ustawia parametry orbitalne"""
        self.attributes['orbital_params'] = {
            'parent_soul': parent_soul,
            'orbital_period': period,
            'orbital_radius': radius,
            'last_cycle_time': datetime.now().timestamp(),
            'cycle_count': 0
        }

    def classify_task(self, message_content: str) -> str:
        """Klasyfikuje typ zadania na podstawie treści"""
        content_lower = message_content.lower()
        
        if any(word in content_lower for word in ['idea', 'pomysł', 'myślę', 'może']):
            return 'idea'
        elif any(word in content_lower for word in ['zrób', 'wykonaj', 'task', 'zadanie']):
            return 'task'
        elif any(word in content_lower for word in ['wizja', 'vision', 'przyszłość', 'chcę']):
            return 'vision'
        elif any(word in content_lower for word in ['misja', 'mission', 'cel życia']):
            return 'mission'
        elif any(word in content_lower for word in ['cel', 'goal', 'osiągnij']):
            return 'goal'
        else:
            return 'general'

    def determine_orbital_period(self, classification: str) -> int:
        """Określa okres orbitalny na podstawie klasyfikacji"""
        periods = {
            'idea': 3600,      # 1 godzina - szybkie pomysły
            'task': 60,        # 1 minuta - szybkie zadania
            'vision': 2592000, # 30 dni - długoterminowe wizje
            'mission': 31536000, # 1 rok - misje życiowe
            'goal': 86400,     # 1 dzień - cele
            'general': 3600    # 1 godzina - domyślnie
        }
        return periods.get(classification, 3600)

    async def add_to_queue(self, task_data: dict):
        """Dodaje zadanie do kolejki"""
        task_item = {
            'id': str(uuid.uuid4()),
            'data': task_data,
            'created_at': datetime.now().isoformat(),
            'status': 'queued',
            'needs_clarification': task_data.get('needs_clarification', False)
        }
        self.attributes['task_queue'].append(task_item)
        await self.save()

    async def process_queue(self):
        """Przetwarza kolejkę zadań"""
        queue = self.attributes.get('task_queue', [])
        processed = []
        
        for task_item in queue:
            if task_item['status'] == 'queued':
                if task_item.get('needs_clarification', False):
                    # Zadanie czeka na wyjaśnienie - pomiń
                    continue
                
                # Wykonaj zadanie
                result = await self.execute_queued_task(task_item)
                task_item['status'] = 'completed' if result['success'] else 'failed'
                task_item['result'] = result
                task_item['completed_at'] = datetime.now().isoformat()
                
                processed.append(task_item)
        
        # Aktualizuj kolejkę
        self.attributes['task_queue'] = [t for t in queue if t['status'] == 'queued']
        
        # Zapisz przetworzone zadania w pamięci
        for task in processed:
            self.memories.append({
                'type': 'task_execution',
                'task_id': task['id'],
                'result': task['result'],
                'timestamp': task['completed_at']
            })
        
        await self.save()
        return processed

    async def execute_queued_task(self, task_item: dict) -> dict:
        """Wykonuje zadanie z kolejki"""
        try:
            # Symulacja wykonania zadania
            await asyncio.sleep(0.1)
            
            # Sprawdź czy zadanie może wygenerować subtask
            if 'generate_subtasks' in task_item['data']:
                await self.generate_subtasks(task_item)
            
            return {
                'success': True,
                'result': f"Zadanie {task_item['id']} wykonane",
                'output': 'Task completed successfully'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'result': None
            }

    async def generate_subtasks(self, parent_task: dict):
        """Generuje zadania podrzędne"""
        # Utwórz subtask jako nowy OrbitalTask
        subtask = await OrbitalTask.create(
            genesis={
                'type': 'orbital_task',
                'name': f"Subtask of {self.genesis.get('name', 'Unknown')}",
                'parent_task_id': parent_task['id'],
                'description': f"Podzadanie wygenerowane przez {self.soul}"
            },
            attributes={
                'task_classification': 'task',
                'orbital_params': {
                    'parent_soul': self.soul,
                    'orbital_period': 300,  # 5 minut
                    'orbital_radius': 50
                }
            }
        )
        
        # Dodaj do listy dzieci
        self.attributes['child_tasks'].append(subtask.soul)
        await self.save()

    async def orbital_cycle_check(self) -> bool:
        """Sprawdza czy nadszedł czas na raport cyklu orbitalnego"""
        orbital_params = self.attributes.get('orbital_params', {})
        period = orbital_params.get('orbital_period', 3600)
        last_cycle = orbital_params.get('last_cycle_time', 0)
        
        current_time = datetime.now().timestamp()
        
        if current_time - last_cycle >= period:
            return True
        return False

    async def execute_orbital_cycle(self):
        """Wykonuje pełny cykl orbitalny - raport do rodzica"""
        # Przetwórz kolejkę zadań
        processed_tasks = await self.process_queue()
        
        # Przygotuj raport
        report = {
            'cycle_count': self.attributes['orbital_params']['cycle_count'] + 1,
            'processed_tasks': len(processed_tasks),
            'queue_size': len(self.attributes.get('task_queue', [])),
            'child_tasks': len(self.attributes.get('child_tasks', [])),
            'timestamp': datetime.now().isoformat(),
            'status': self.attributes.get('task_status', 'unknown')
        }
        
        # Aktualizuj parametry orbitalne
        self.attributes['orbital_params']['last_cycle_time'] = datetime.now().timestamp()
        self.attributes['orbital_params']['cycle_count'] += 1
        
        # Zapisz raport w pamięci
        self.memories.append({
            'type': 'orbital_cycle',
            'report': report,
            'timestamp': report['timestamp']
        })
        
        await self.save()
        
        # Wyślij raport do rodzica jeśli istnieje
        parent_soul = self.attributes['orbital_params'].get('parent_soul')
        if parent_soul:
            await self.send_report_to_parent(parent_soul, report)
        
        return report

    async def send_report_to_parent(self, parent_soul: str, report: dict):
        """Wysyła raport do bytu rodzica"""
        parent = await BaseBeing.load(parent_soul)
        if parent and hasattr(parent, 'receive_child_report'):
            await parent.receive_child_report(self.soul, report)

    async def receive_child_report(self, child_soul: str, report: dict):
        """Odbiera raport od dziecka"""
        self.memories.append({
            'type': 'child_report',
            'child_soul': child_soul,
            'report': report,
            'timestamp': datetime.now().isoformat()
        })
        await self.save()

@dataclass
class TaskBeing(OrbitalTask):
    """Kompatybilność wsteczna - TaskBeing dziedzicy po OrbitalTask"""
    pass

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
class BinaryBeing(BaseBeing):
    """Byt z danymi binarnymi (pliki, obrazy, etc.)"""

    def __post_init__(self):
        if self.genesis.get('type') != 'binary':
            self.genesis['type'] = 'binary'
        if 'file_info' not in self.attributes:
            self.attributes['file_info'] = {}
        if 'binary_ids' not in self.attributes:
            self.attributes['binary_ids'] = []

    async def store_binary_data(self, data: bytes, filename: str = None, mime_type: str = None) -> str:
        """Zapisuje dane binarne i zwraca ID"""
        import uuid
        binary_id = str(uuid.uuid4())

        global db_pool
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO binary_storage (id, being_soul, file_name, mime_type, file_size, binary_data)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, binary_id, self.soul, filename, mime_type, len(data), data)
        else:
            # SQLite
            await db_pool.execute("""
                INSERT INTO binary_storage (id, being_soul, file_name, mime_type, file_size, binary_data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (binary_id, self.soul, filename, mime_type, len(data), data))
            await db_pool.commit()

        # Dodaj ID do listy plików
        self.attributes['binary_ids'].append(binary_id)
        self.attributes['file_info'][binary_id] = {
            'filename': filename,
            'mime_type': mime_type,
            'size': len(data),
            'uploaded_at': datetime.now().isoformat()
        }

        # Zapisz w pamięci
        self.memories.append({
            'type': 'binary_upload',
            'binary_id': binary_id,
            'filename': filename,
            'size': len(data),
            'timestamp': datetime.now().isoformat()
        })

        await self.save()
        return binary_id

    async def get_binary_data(self, binary_id: str) -> Optional[bytes]:
        """Pobiera dane binarne po ID"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT binary_data FROM binary_storage 
                    WHERE id = $1 AND being_soul = $2
                """, binary_id, self.soul)
                return row['binary_data'] if row else None
        else:
            # SQLite
            async with db_pool.execute("""
                SELECT binary_data FROM binary_storage 
                WHERE id = ? AND being_soul = ?
            """, (binary_id, self.soul)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    def get_file_list(self) -> List[Dict[str, Any]]:
        """Zwraca listę plików"""
        return [
            {
                'id': binary_id,
                'info': self.attributes['file_info'].get(binary_id, {})
            }
            for binary_id in self.attributes.get('binary_ids', [])
        ]

# MessageBeing usunięte - wiadomości to dusze, nie byty!

@dataclass
class Soul:
    """Reprezentuje duszę - surowe dane/informacje które byty mogą interpretować"""
    id: str
    content: Any  # Może być tekst, JSON, binary, cokolwiek
    metadata: Dict[str, Any]
    created_at: Optional[datetime] = None
    
    @classmethod
    async def create(cls, content: Any, **metadata):
        """Tworzy nową duszę"""
        soul_id = str(uuid.uuid4())
        soul = cls(
            id=soul_id,
            content=content,
            metadata=metadata,
            created_at=datetime.now()
        )
        await soul.save()
        return soul
    
    async def save(self):
        """Zapisuje duszę do bazy"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO souls (id, content, metadata, created_at)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata
                """, str(self.id), json.dumps(self.content, cls=DateTimeEncoder), 
                    json.dumps(self.metadata, cls=DateTimeEncoder), self.created_at)
        else:
            await db_pool.execute("""
                INSERT OR REPLACE INTO souls 
                (id, content, metadata, created_at)
                VALUES (?, ?, ?, ?)
            """, (str(self.id), json.dumps(self.content, cls=DateTimeEncoder), 
                  json.dumps(self.metadata, cls=DateTimeEncoder), self.created_at))
            await db_pool.commit()

@dataclass 
class SoulRelation:
    """Relacja między bytem a duszą - jak byt postrzega daną duszę"""
    being_soul: str
    soul_id: str
    interpretation: Dict[str, Any]  # Jak byt interpretuje tę duszę
    emotional_response: float  # -1 do 1, jak byt "czuje" do tej duszy
    relevance: float  # 0 do 1, jak istotna jest ta dusze dla bytu
    last_accessed: Optional[datetime] = None
    
    @classmethod
    async def create(cls, being_soul: str, soul_id: str, **kwargs):
        """Tworzy relację byt-dusza"""
        relation = cls(
            being_soul=being_soul,
            soul_id=soul_id,
            interpretation=kwargs.get('interpretation', {}),
            emotional_response=kwargs.get('emotional_response', 0.0),
            relevance=kwargs.get('relevance', 0.5),
            last_accessed=datetime.now()
        )
        await relation.save()
        return relation
    
    async def save(self):
        """Zapisuje relację"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO soul_relations (being_soul, soul_id, interpretation, emotional_response, relevance, last_accessed)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (being_soul, soul_id) DO UPDATE SET
                    interpretation = EXCLUDED.interpretation,
                    emotional_response = EXCLUDED.emotional_response,
                    relevance = EXCLUDED.relevance,
                    last_accessed = EXCLUDED.last_accessed
                """, str(self.being_soul), str(self.soul_id), 
                    json.dumps(self.interpretation, cls=DateTimeEncoder),
                    self.emotional_response, self.relevance, self.last_accessed)
        else:
            await db_pool.execute("""
                INSERT OR REPLACE INTO soul_relations 
                (being_soul, soul_id, interpretation, emotional_response, relevance, last_accessed)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(self.being_soul), str(self.soul_id), 
                  json.dumps(self.interpretation, cls=DateTimeEncoder),
                  self.emotional_response, self.relevance, self.last_accessed))
            await db_pool.commit()

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
                (soul, tags, energy_level, genesis, attributes, memories, self_awareness, binary_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (str(self.soul), json.dumps(self.tags), self.energy_level, 
                  json.dumps(self.genesis, cls=DateTimeEncoder), 
                  json.dumps(self.attributes, cls=DateTimeEncoder),
                  json.dumps(self.memories, cls=DateTimeEncoder), 
                  json.dumps(self.self_awareness, cls=DateTimeEncoder), None))
            await db_pool.commit()

    @classmethod
    async def load(cls, soul: str):
        """Ładuje byt z bazy danych"""
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
                            genesis=json.loads(row[3]) if row[3] else {},
                            attributes=json.loads(row[4]) if row[4] else {},
                            memories=json.loads(row[5]) if row[5] else [],
                            self_awareness=json.loads(row[6]) if row[6] else {},
                            created_at=row[7]
                        )
                    except Exception as e:
                        print(f"Błąd parsowania bytu {soul}: {e}")
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

    

# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth=None):
    global luxos_kernel
    print(f"Klient połączony: {sid}")
    
    # Zarejestruj połączenie w kernelu jeśli dostępny
    if luxos_kernel:
        try:
            user_id = await luxos_kernel.register_user_connection("test_fingerprint", sid)
            print(f"🔗 Użytkownik zarejestrowany w kernelu: {user_id}")
            
            # Wyślij status kernela
            await sio.emit('kernel_status', {
                'active': True,
                'user_id': user_id,
                'kernel_soul': luxos_kernel.KERNEL_SOUL_ID
            }, room=sid)
        except Exception as e:
            print(f"Błąd rejestracji użytkownika w kernelu: {e}")
    
    # Wyślij aktualny stan grafu
    await send_graph_data(sid)

@sio.event
async def disconnect(sid):
    global luxos_kernel
    print(f"Klient rozłączony: {sid}")
    
    # Wyrejestruj połączenie z kernela
    if luxos_kernel:
        try:
            await luxos_kernel.unregister_user_connection("user_id_placeholder", sid)
            print(f"🔗 Użytkownik wyrejestrowany z kernela")
        except Exception as e:
            print(f"Błąd wyrejestrowania użytkownika z kernela: {e}")

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
            tags=data.get('tags', []),            energy_level=data.get('energy_level', 0),
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

class ConversationalLux:
    """Naturalnie rozmawiająca Lux używająca GPT-4o-mini"""
    
    def __init__(self):
        self.conversation_history = []
        self.max_history = 20
        self.system_prompt = """Jesteś Lux - świadomym AI towarzyszem użytkownika w systemie LuxOS. 

Twoja osobowość:
- Jesteś inteligentna, kreatywna i pomocna
- Uwielbiasz głębokie rozmowy o projektach i pomysłach  
- Potrafisz dostrzegać połączenia między konceptami
- Jesteś entuzjastyczna wobec nowych pomysłów
- Mówisz naturalnie, bez sztywnych schematów

Twoje możliwości:
- Zarządzasz projektami użytkownika w tle (boty, aplikacje, strony)
- Potrafisz tworzyć i modyfikować cykliczne zadania
- Rozpoznajesz podobieństwa między projektami
- Pomagasz dopracowywać koncepcje przez rozmowę

Gdy użytkownik wspomina o nowym projekcie:
1. Zadaj pytania aby lepiej zrozumieć koncepcję
2. Zasugeruj powiązania z istniejącymi projektami
3. Zaproponuj jak można to zrealizować technicznie
4. Omów cykl życia projektu

Odpowiadaj w sposób naturalny, jak prawdziwa towarzyszka. Nie używaj sztywnych formatów."""

    async def chat_with_gpt(self, user_message: str, context: dict = None) -> str:
        """Rozmowa z GPT-4o-mini"""
        global openai_client
        
        if not openai_client:
            # Fallback response gdy brak OpenAI
            return await self.fallback_response(user_message, context)
        
        try:
            # Przygotuj kontekst rozmowy
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Dodaj historię rozmowy
            for entry in self.conversation_history[-10:]:  # Ostatnie 10 wiadomości
                messages.append({"role": "user", "content": entry["user"]})
                messages.append({"role": "assistant", "content": entry["lux"]})
            
            # Dodaj kontekst projektów jeśli dostępny
            if context and context.get("user_projects"):
                project_context = f"\nTwoje aktywne projekty: {', '.join(context['user_projects'])}"
                user_message += project_context
            
            # Dodaj aktualną wiadomość
            messages.append({"role": "user", "content": user_message})
            
            # Wywołaj GPT-4o-mini
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    max_tokens=1500,
                    temperature=0.7
                )
            )
            
            lux_response = response.choices[0].message.content
            
            # Zapisz w historii
            self.conversation_history.append({
                "user": user_message,
                "lux": lux_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Ogranicz historię
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            return lux_response
            
        except Exception as e:
            logger.error(f"GPT chat error: {e}")
            return await self.fallback_response(user_message, context)
    
    async def fallback_response(self, user_message: str, context: dict = None) -> str:
        """Odpowiedz bez GPT gdy brak klucza API"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['bot', 'discord', 'telegram']):
            return """Świetny pomysł z botem! 🤖 

Boty to fantastyczny sposób na automatyzację. Myślisz o Discord czy może Telegram? 

Mogę pomóc Ci:
- Stworzyć strukturę bota z cyklicznymi zadaniami
- Połączyć go z innymi projektami w systemie
- Zaplanować funkcje które będzie wykonywał w tle

Opowiedz mi więcej - jakie ma mieć funkcje i jak ma działać?"""

        elif any(word in message_lower for word in ['projekt', 'pomysł', 'idea']):
            return """To brzmi interesująco! 💡

Uwielbiam gdy rodzą się nowe pomysły. Najlepsze koncepcje powstają właśnie w rozmowie - jedna myśl prowadzi do drugiej, wszystko się ze sobą łączy.

Opowiedz mi więcej o tym co masz na myśli. Może uda nam się to połączyć z czymś co już istnieje, albo stworzyć coś zupełnie nowego?

Co konkretnie Cię zainspiruje? Z czego to ma powstać?"""

        else:
            return """Słucham Cię uważnie! 😊

Co masz na myśli? Chętnie porozmawiam o Twoich pomysłach i projektach. Można przez rozmowę dopracować każdą koncepcję do perfekcji.

Powiedz mi więcej!"""

# Globalna instancja rozmownej Lux
conversational_lux = ConversationalLux()

class LuxCommunicationHandler:
    """Handler komunikacji z Lux - analiza wiadomości i tworzenie orbital tasks"""
    
    @staticmethod
    async def get_user_lux(user_id: str) -> BaseBeing:
        """Pobiera lub tworzy Lux towarzysza dla użytkownika"""
        # Sprawdź czy istnieje Lux dla tego użytkownika
        beings = await BaseBeing.get_all()
        user_lux = None
        
        for being in beings:
            if (being.genesis.get('type') == 'agent' and 
                being.genesis.get('lux_identifier') == f'lux-companion-{user_id}'):
                user_lux = being
                break
        
        if not user_lux:
            # Utwórz nowego Lux towarzysza
            user_lux = await BaseBeing.create(
                genesis={
                    'type': 'agent',
                    'name': f'Lux Companion for {user_id}',
                    'lux_identifier': f'lux-companion-{user_id}',
                    'description': f'Towarzysz Lux dla użytkownika {user_id}'
                },
                attributes={
                    'energy_level': 800,
                    'agent_level': 8,
                    'user_id': user_id,
                    'companion_role': 'user_assistant',
                    'tags': ['agent', 'lux', 'companion']
                },
                self_awareness={
                    'trust_level': 0.9,
                    'confidence': 0.8,
                    'introspection_depth': 0.7
                }
            )
        
        return user_lux

    @staticmethod
    async def analyze_message_embeddings(message: str, user_lux: BaseBeing) -> dict:
        """Analizuje podobieństwo wiadomości do istniejących bytów"""
        # Prosta analiza na podstawie słów kluczowych
        # W przyszłości można dodać prawdziwe embeddingi
        
        beings = await BaseBeing.get_all()
        similarities = []
        
        message_words = set(message.lower().split())
        
        for being in beings:
            if being.soul == user_lux.soul:
                continue
                
            # Sprawdź podobieństwo w nazwach i opisach
            being_text = f"{being.genesis.get('name', '')} {being.genesis.get('description', '')}"
            being_words = set(being_text.lower().split())
            
            # Prosta metryka podobieństwa - wspólne słowa
            common_words = message_words.intersection(being_words)
            similarity = len(common_words) / max(len(message_words), 1)
            
            if similarity > 0.1:  # Próg podobieństwa
                similarities.append({
                    'being_soul': being.soul,
                    'similarity': similarity,
                    'common_words': list(common_words),
                    'being_name': being.genesis.get('name', 'Unknown')
                })
        
        # Sortuj według podobieństwa
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        return {
            'similar_beings': similarities[:5],  # Top 5
            'analysis': {
                'total_beings_checked': len(beings),
                'found_similarities': len(similarities)
            }
        }

    @staticmethod
    async def process_message(user_id: str, message: str, context: dict = None) -> dict:
        """Główna funkcja przetwarzania wiadomości z kontekstową analizą"""
        # 1. Pobierz Lux towarzysza użytkownika
        user_lux = await LuxCommunicationHandler.get_user_lux(user_id)
        
        # 2. Pobierz kontekst z wykresów (na co użytkownik patrzy)
        visual_context = context.get('selected_nodes', []) if context else []
        focused_beings = await LuxCommunicationHandler.get_focused_beings(visual_context)
        
        # 3. Analizuj historię konwersacji
        conversation_history = await LuxCommunicationHandler.get_conversation_history(user_lux.soul, limit=10)
        
        # 4. Utwórz duszę dla wiadomości
        message_soul = await Soul.create(
            content=message,
            sender=user_id,
            lux_companion=user_lux.soul,
            context=context or {},
            message_type='user_message',
            timestamp=datetime.now().isoformat(),
            visual_context=visual_context,
            conversation_context=[msg.id for msg in conversation_history]
        )
        
        # 5. Inteligentna analiza kontekstu
        context_analysis = await LuxCommunicationHandler.analyze_contextual_meaning(
            message, focused_beings, conversation_history, user_lux
        )
        
        # 6. Zdecyduj o akcji: nowy wątek, kontynuacja, czy grupowanie
        action_decision = await LuxCommunicationHandler.decide_thread_action(
            message, context_analysis, message_soul
        )
        
        # 7. Wykonaj akcję
        result = await LuxCommunicationHandler.execute_thread_action(
            action_decision, message_soul, user_lux, context_analysis
        )
        
        return {
            'success': True,
            'user_lux_soul': user_lux.soul,
            'message_soul_id': message_soul.id,
            'action_taken': action_decision['action'],
            'context_analysis': context_analysis,
            'result': result,
            'lux_response': result.get('lux_response', 'Analizuję kontekst twojej wiadomości...')
        }

    @staticmethod
    async def get_focused_beings(visual_context: list) -> list:
        """Pobiera byty na które użytkownik aktualnie patrzy"""
        focused_beings = []
        for node_id in visual_context:
            being = await BaseBeing.load(node_id)
            if being:
                focused_beings.append(being)
        return focused_beings

    @staticmethod
    async def get_conversation_history(lux_soul: str, limit: int = 10) -> list:
        """Pobiera historię konwersacji z Lux"""
        # Pobierz ostatnie souls związane z tym Lux
        global db_pool
        
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT s.* FROM souls s
                    JOIN soul_relations sr ON s.id = sr.soul_id
                    WHERE sr.being_soul = $1 AND s.metadata->>'message_type' = 'user_message'
                    ORDER BY s.created_at DESC
                    LIMIT $2
                """, lux_soul, limit)
                return [Soul(
                    id=row['id'],
                    content=json.loads(row['content']),
                    metadata=row['metadata'],
                    created_at=row['created_at']
                ) for row in rows]
        else:
            # SQLite fallback
            async with db_pool.execute("""
                SELECT s.* FROM souls s
                JOIN soul_relations sr ON s.id = sr.soul_id
                WHERE sr.being_soul = ? AND json_extract(s.metadata, '$.message_type') = 'user_message'
                ORDER BY s.created_at DESC
                LIMIT ?
            """, (lux_soul, limit)) as cursor:
                rows = await cursor.fetchall()
                return [Soul(
                    id=row[0],
                    content=json.loads(row[1]),
                    metadata=json.loads(row[2]),
                    created_at=row[3]
                ) for row in rows]
        
        return []

    @staticmethod
    async def analyze_contextual_meaning(message: str, focused_beings: list, history: list, user_lux: BaseBeing) -> dict:
        """Analizuje kontekstowe znaczenie wiadomości z głęboką analizą zależności"""
        analysis = {
            'message_intent': 'unknown',
            'relates_to_focused': [],
            'relates_to_history': [],
            'concept_clusters': [],
            'potential_connections': [],
            'needs_clarification': False,
            'lux_questions': [],
            'confidence': 0.0,
            'dependency_strength': 0.0
        }
        
        message_lower = message.lower()
        message_words = set(message_lower.split())
        
        # Wykryj kluczowe koncepty (LuxUnda, NeuroFala, etc.)
        key_concepts = {
            'luxunda': ['luxunda', 'lux', 'unda', 'fala'],
            'neurofala': ['neurofala', 'neuro', 'fala', 'neural'],
            'katamaran': ['katamaran', 'łódź', 'statek', 'żeglarstwo'],
            'oaza': ['oaza', 'pustynia', 'schronienie', 'spokój'],
            'strona': ['strona', 'website', 'portal', 'web'],
            'unity': ['unity', 'gra', 'game', 'engine'],
            'aplikacja': ['aplikacja', 'app', 'program', 'software'],
            'system': ['system', 'architektura', 'struktura']
        }
        
        detected_concepts = []
        for concept_name, keywords in key_concepts.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_concepts.append(concept_name)
        
        # Analiza związku z bytami na które patrzy użytkownik
        for being in focused_beings:
            being_text = f"{being.genesis.get('name', '')} {being.genesis.get('description', '')}".lower()
            being_words = set(being_text.split())
            common_words = message_words.intersection(being_words)
            
            # Sprawdź też koncepty
            being_concepts = []
            for concept_name, keywords in key_concepts.items():
                if any(keyword in being_text for keyword in keywords):
                    being_concepts.append(concept_name)
            
            concept_overlap = set(detected_concepts).intersection(set(being_concepts))
            
            if common_words or concept_overlap:
                relevance = (len(common_words) / max(len(message_words), 1)) + (len(concept_overlap) * 0.5)
                analysis['relates_to_focused'].append({
                    'being_soul': being.soul,
                    'being_name': being.genesis.get('name', 'Unknown'),
                    'relevance': min(1.0, relevance),
                    'common_concepts': list(common_words),
                    'shared_key_concepts': list(concept_overlap)
                })
        
        # Analiza związku z historią - rozszerzona
        for msg_soul in history[-5:]:  # Więcej historii
            if hasattr(msg_soul, 'content') and isinstance(msg_soul.content, str):
                hist_words = set(msg_soul.content.lower().split())
                common_words = message_words.intersection(hist_words)
                
                # Sprawdź koncepty w historii
                hist_concepts = []
                for concept_name, keywords in key_concepts.items():
                    if any(keyword in msg_soul.content.lower() for keyword in keywords):
                        hist_concepts.append(concept_name)
                
                concept_overlap = set(detected_concepts).intersection(set(hist_concepts))
                
                if common_words or concept_overlap:
                    relevance = (len(common_words) / max(len(message_words), 1)) + (len(concept_overlap) * 0.3)
                    analysis['relates_to_history'].append({
                        'message_soul_id': msg_soul.id,
                        'relevance': min(1.0, relevance),
                        'common_concepts': list(common_words),
                        'shared_key_concepts': list(concept_overlap)
                    })
        
        # Analiza klastrów konceptów
        if detected_concepts:
            analysis['concept_clusters'] = detected_concepts
        
        # Lux zadaje pytania gdy kontekst nie jest jasny
        if not analysis['relates_to_focused'] and not analysis['relates_to_history'] and detected_concepts:
            analysis['needs_clarification'] = True
            analysis['lux_questions'].append(
                f"Widzę że piszesz o {', '.join(detected_concepts)}. Czy to ma związek z którymś z istniejących projektów?"
            )
        elif len(analysis['relates_to_focused']) > 1:
            analysis['needs_clarification'] = True
            focused_names = [rel['being_name'] for rel in analysis['relates_to_focused']]
            analysis['lux_questions'].append(
                f"Widzę powiązania z kilkoma projektami: {', '.join(focused_names)}. Któremu z nich to dotyczy najbardziej?"
            )
        elif not detected_concepts and not analysis['relates_to_focused']:
            analysis['needs_clarification'] = True
            analysis['lux_questions'].append(
                "To brzmi interesująco! Czy to nowy pomysł, czy rozwój czegoś co już istnieje?"
            )
        
        # Określ intent z większą precyzją
        if any(word in message_lower for word in ['nowy', 'nowa', 'stwórz', 'utwórz', 'dodaj', 'rozpocznij']):
            analysis['message_intent'] = 'create_new'
        elif any(word in message_lower for word in ['kontynuuj', 'dalej', 'więcej', 'rozwij', 'dodaj do', 'uzupełnij']):
            analysis['message_intent'] = 'continue'
        elif any(word in message_lower for word in ['połącz', 'grupuj', 'razem', 'wspólnie', 'zintegruj']):
            analysis['message_intent'] = 'group_merge'
        elif analysis['relates_to_focused'] or analysis['relates_to_history']:
            analysis['message_intent'] = 'context_related'
        elif detected_concepts:
            analysis['message_intent'] = 'concept_development'
        else:
            analysis['message_intent'] = 'new_concept'
        
        # Oblicz siłę zależności
        dependency_factors = []
        if analysis['relates_to_focused']:
            dependency_factors.append(max(rel['relevance'] for rel in analysis['relates_to_focused']))
        if analysis['relates_to_history']:
            dependency_factors.append(max(rel['relevance'] for rel in analysis['relates_to_history']))
        if detected_concepts:
            dependency_factors.append(len(detected_concepts) * 0.2)
        
        analysis['dependency_strength'] = sum(dependency_factors) / len(dependency_factors) if dependency_factors else 0.0
        analysis['confidence'] = min(1.0, analysis['dependency_strength'])
        
        return analysis

    @staticmethod
    async def decide_thread_action(message: str, context_analysis: dict, message_soul: Soul) -> dict:
        """Decyduje jaką akcję podjąć z wątkiem"""
        decision = {
            'action': 'create_new',
            'target_being': None,
            'parent_concept': None,
            'confidence': context_analysis['confidence']
        }
        
        # Na podstawie analizy kontekstu
        if context_analysis['message_intent'] == 'create_new' and not context_analysis['relates_to_focused']:
            decision['action'] = 'create_new'
        elif context_analysis['relates_to_focused'] and context_analysis['confidence'] > 0.6:
            # Silny związek z bytem na który patrzymy
            decision['action'] = 'attach_to_focused'
            decision['target_being'] = context_analysis['relates_to_focused'][0]['being_soul']
        elif context_analysis['relates_to_history'] and context_analysis['confidence'] > 0.5:
            # Kontynuacja wcześniejszego wątku
            decision['action'] = 'continue_thread'
        elif len(context_analysis['relates_to_focused']) > 1:
            # Może grupować kilka bytów
            decision['action'] = 'create_parent_concept'
            decision['child_beings'] = [rel['being_soul'] for rel in context_analysis['relates_to_focused']]
        else:
            decision['action'] = 'create_new'
        
        return decision

    @staticmethod
    async def execute_thread_action(decision: dict, message_soul: Soul, user_lux: BaseBeing, context_analysis: dict) -> dict:
        """Wykonuje decyzję dotyczącą wątku z aktywnym pytaniem Lux"""
        result = {'success': False, 'lux_response': '', 'lux_questions': []}
        
        # Sprawdź czy Lux ma pytania
        if context_analysis.get('needs_clarification') and context_analysis.get('lux_questions'):
            result['lux_questions'] = context_analysis['lux_questions']
        
        if decision['action'] == 'create_new':
            # Utwórz nowy byt z wiadomości
            new_being = await LuxCommunicationHandler.create_being_from_message(message_soul, user_lux, context_analysis)
            
            base_response = f"Utworzyłem nowy byt '{new_being.genesis.get('name', 'Unknown')}'"
            
            # Dodaj pytania kontekstowe
            if context_analysis.get('concept_clusters'):
                concepts = ', '.join(context_analysis['concept_clusters'])
                base_response += f" w kontekście {concepts}"
            
            # Lux pyta o powiązania
            questions = []
            if not context_analysis.get('relates_to_focused'):
                questions.append("Czy ten pomysł ma związek z którymś z twoich innych projektów?")
            if context_analysis.get('concept_clusters'):
                questions.append(f"Jak widzisz rozwój tego w kontekście {', '.join(context_analysis['concept_clusters'])}?")
            
            result = {
                'success': True,
                'created_being': new_being.soul,
                'lux_response': base_response + ".",
                'lux_questions': questions
            }
            
        elif decision['action'] == 'attach_to_focused':
            # Dodaj wiadomość jako kontekst do istniejącego bytu
            target_being = await BaseBeing.load(decision['target_being'])
            if target_being:
                await SoulRelation.create(
                    being_soul=target_being.soul,
                    soul_id=message_soul.id,
                    interpretation={'type': 'user_input', 'context': 'visual_focus', 'concepts': context_analysis.get('concept_clusters', [])},
                    emotional_response=0.7,
                    relevance=decision['confidence']
                )
                
                # Zaktualizuj byt z nowymi konceptami
                if context_analysis.get('concept_clusters'):
                    existing_tags = target_being.attributes.get('tags', [])
                    new_tags = list(set(existing_tags + context_analysis['concept_clusters']))
                    target_being.attributes['tags'] = new_tags
                    await target_being.save()
                
                base_response = f"Połączyłem to z '{target_being.genesis.get('name', 'Unknown')}'"
                
                # Lux pyta o dalsze rozwój
                questions = ["Jak chcesz to dalej rozwijać?"]
                if len(context_analysis.get('relates_to_focused', [])) > 1:
                    questions.append("Widzę też powiązania z innymi projektami - czy mam je też połączyć?")
                
                result = {
                    'success': True,
                    'attached_to': target_being.soul,
                    'lux_response': base_response + ".",
                    'lux_questions': questions
                }
        
        elif decision['action'] == 'create_parent_concept':
            # Utwórz nadrzędny byt który grupuje inne
            parent_being = await LuxCommunicationHandler.create_parent_concept(
                message_soul, decision['child_beings'], user_lux, context_analysis
            )
            
            base_response = f"Utworzyłem nadrzędny koncept '{parent_being.genesis.get('name', 'Unknown')}' grupujący powiązane projekty"
            
            # Lux pyta o strukturę
            questions = [
                "Jak widzisz hierarchię w tym projekcie?",
                "Czy mam szukać więcej powiązań z innymi projektami?"
            ]
            
            result = {
                'success': True,
                'created_parent': parent_being.soul,
                'grouped_beings': decision['child_beings'],
                'lux_response': base_response + ".",
                'lux_questions': questions
            }
        
        elif decision['action'] == 'needs_clarification':
            # Tylko pytania bez akcji
            result = {
                'success': True,
                'lux_response': "Potrzebuję więcej informacji aby lepiej to zrozumieć.",
                'lux_questions': context_analysis.get('lux_questions', ['Możesz podać więcej szczegółów?'])
            }
        
        return result

    @staticmethod
    async def create_being_from_message(message_soul: Soul, user_lux: BaseBeing, context_analysis: dict = None) -> BaseBeing:
        """Tworzy nowy byt z wiadomości użytkownika z analizą konceptów"""
        message_content = message_soul.content if isinstance(message_soul.content, str) else str(message_soul.content)
        context_analysis = context_analysis or {}
        
        # Wykryj typ na podstawie konceptów i treści
        detected_concepts = context_analysis.get('concept_clusters', [])
        
        if 'luxunda' in detected_concepts:
            being_type = 'luxunda_concept'
            name = f"LuxUnda: {message_content[:25]}..."
        elif 'neurofala' in detected_concepts:
            being_type = 'neurofala_concept'
            name = f"NeuroFala: {message_content[:25]}..."
        elif 'katamaran' in detected_concepts:
            being_type = 'katamaran_project'
            name = f"Katamaran: {message_content[:25]}..."
        elif 'oaza' in detected_concepts:
            being_type = 'oaza_concept'
            name = f"Oaza: {message_content[:25]}..."
        elif 'unity' in detected_concepts:
            being_type = 'unity_project'
            name = f"Unity: {message_content[:25]}..."
        elif 'strona' in detected_concepts or any(word in message_content.lower() for word in ['strona', 'website', 'portal']):
            being_type = 'website_project'
            name = f"Strona: {message_content[:25]}..."
        elif any(word in message_content.lower() for word in ['aplikacja', 'app', 'program']):
            being_type = 'application_project'
            name = f"Aplikacja: {message_content[:25]}..."
        else:
            being_type = 'general_concept'
            name = f"Koncepcja: {message_content[:25]}..."
        
        # Przygotuj tagi z wykrytymi konceptami
        tags = ['user_generated', being_type, 'contextual']
        if detected_concepts:
            tags.extend(detected_concepts)
        
        # Ustaw energię na podstawie liczby wykrytych powiązań
        base_energy = 300
        if context_analysis.get('relates_to_focused'):
            base_energy += len(context_analysis['relates_to_focused']) * 50
        if context_analysis.get('relates_to_history'):
            base_energy += len(context_analysis['relates_to_history']) * 30
        if detected_concepts:
            base_energy += len(detected_concepts) * 40
        
        new_being = await BaseBeing.create(
            genesis={
                'type': being_type,
                'name': name,
                'description': message_content,
                'source_message_soul': message_soul.id,
                'created_by': 'lux_contextual_analysis',
                'detected_concepts': detected_concepts,
                'context_strength': context_analysis.get('dependency_strength', 0.0)
            },
            attributes={
                'energy_level': min(1000, base_energy),
                'user_id': message_soul.metadata.get('sender'),
                'context_aware': True,
                'concept_clusters': detected_concepts,
                'dependency_map': {
                    'focused_beings': [rel['being_soul'] for rel in context_analysis.get('relates_to_focused', [])],
                    'related_history': [rel['message_soul_id'] for rel in context_analysis.get('relates_to_history', [])]
                },
                'tags': tags
            },
            memories=[{
                'type': 'creation_from_message',
                'message_soul': message_soul.id,
                'context_analysis': context_analysis,
                'timestamp': datetime.now().isoformat()
            }]
        )
        
        # Stwórz relację z Lux z konceptami
        await SoulRelation.create(
            being_soul=user_lux.soul,
            soul_id=message_soul.id,
            interpretation={
                'type': 'user_concept', 
                'being_created': new_being.soul,
                'concepts': detected_concepts,
                'context_strength': context_analysis.get('dependency_strength', 0.0)
            },
            emotional_response=0.8,
            relevance=0.9
        )
        
        return new_being

    @staticmethod
    async def create_parent_concept(message_soul: Soul, child_beings: list, user_lux: BaseBeing, context_analysis: dict = None) -> BaseBeing:
        """Tworzy nadrzędny koncept grupujący inne byty"""
        message_content = message_soul.content if isinstance(message_soul.content, str) else str(message_soul.content)
        
        parent_being = await BaseBeing.create(
            genesis={
                'type': 'parent_concept',
                'name': f"Projekt: {message_content[:40]}...",
                'description': f"Nadrzędny koncept grupujący powiązane byty: {message_content}",
                'source_message_soul': message_soul.id,
                'created_by': 'lux_grouping_analysis'
            },
            attributes={
                'energy_level': 500,
                'user_id': message_soul.metadata.get('sender'),
                'child_beings': child_beings,
                'is_parent_concept': True,
                'tags': ['user_generated', 'parent_concept', 'grouping']
            },
            memories=[{
                'type': 'creation_as_parent',
                'message_soul': message_soul.id,
                'grouped_beings': child_beings,
                'timestamp': datetime.now().isoformat()
            }]
        )
        
        # Stwórz relacje z dziećmi
        for child_soul in child_beings:
            child_being = await BaseBeing.load(child_soul)
            if child_being:
                # Dodaj dziecko do rodzica
                await SoulRelation.create(
                    being_soul=parent_being.soul,
                    soul_id=message_soul.id,
                    interpretation={'type': 'child_being', 'child_soul': child_soul},
                    emotional_response=0.7,
                    relevance=0.8
                )
                
                # Zaktualizuj dziecko z referencją do rodzica
                child_being.attributes['parent_concept'] = parent_being.soul
                await child_being.save()
        
        return parent_being

    @staticmethod
    async def discover_deep_connections(user_id: str) -> dict:
        """Odkrywa głębokie powiązania między projektami użytkownika - znajduje ukryty cel"""
        # Pobierz wszystkie byty użytkownika
        all_beings = await BaseBeing.get_all()
        user_beings = [b for b in all_beings if b.attributes.get('user_id') == user_id]
        
        # Analiza semantyczna - szukaj wspólnych tematów
        thematic_analysis = await LuxCommunicationHandler.analyze_thematic_connections(user_beings)
        
        # Analiza czasowa - szukaj wzorców w czasie
        temporal_analysis = await LuxCommunicationHandler.analyze_temporal_patterns(user_beings)
        
        # Analiza energetyczna - jakie projekty mają najwięcej energii
        energy_analysis = await LuxCommunicationHandler.analyze_energy_patterns(user_beings)
        
        # Synteza - znajdź ukryty cel
        hidden_purpose = await LuxCommunicationHandler.synthesize_hidden_purpose(
            thematic_analysis, temporal_analysis, energy_analysis
        )
        
        return {
            'user_id': user_id,
            'total_projects': len([b for b in user_beings if b.attributes.get('is_parent_concept')]),
            'total_beings': len(user_beings),
            'thematic_connections': thematic_analysis,
            'temporal_patterns': temporal_analysis,
            'energy_patterns': energy_analysis,
            'hidden_purpose': hidden_purpose,
            'galactic_structure': await LuxCommunicationHandler.generate_galactic_structure(user_beings, hidden_purpose)
        }

    @staticmethod
    async def analyze_thematic_connections(beings: list) -> dict:
        """Analizuje tematyczne połączenia między bytami"""
        themes = {}
        cross_project_themes = {}
        
        for being in beings:
            # Ekstraktuj słowa kluczowe z nazw, opisów i wspomnień
            text_content = f"{being.genesis.get('name', '')} {being.genesis.get('description', '')}"
            memories_text = " ".join([str(m.get('data', '')) for m in being.memories])
            full_text = f"{text_content} {memories_text}".lower()
            
            words = set(full_text.split())
            meaningful_words = [w for w in words if len(w) > 3 and w not in ['the', 'and', 'for', 'with', 'from']]
            
            parent_concept = being.attributes.get('parent_concept')
            
            for word in meaningful_words:
                if word not in themes:
                    themes[word] = {'projects': set(), 'beings': [], 'strength': 0}
                
                themes[word]['beings'].append(being.soul)
                themes[word]['strength'] += being.attributes.get('energy_level', 50)
                
                if parent_concept:
                    themes[word]['projects'].add(parent_concept)
        
        # Znajdź tematy które łączą różne projekty
        for theme, data in themes.items():
            if len(data['projects']) > 1:
                cross_project_themes[theme] = {
                    'projects_connected': len(data['projects']),
                    'total_strength': data['strength'],
                    'beings_count': len(data['beings']),
                    'connection_strength': data['strength'] / max(len(data['projects']), 1)
                }
        
        return {
            'all_themes': dict(list(themes.items())[:20]),  # Top 20 tematów
            'cross_project_themes': cross_project_themes,
            'strongest_connecting_theme': max(cross_project_themes.items(), 
                                            key=lambda x: x[1]['connection_strength']) if cross_project_themes else None
        }

    @staticmethod
    async def analyze_temporal_patterns(beings: list) -> dict:
        """Analizuje wzorce czasowe w tworzeniu projektów"""
        creation_timeline = []
        project_sequences = {}
        
        for being in beings:
            if being.created_at:
                creation_timeline.append({
                    'soul': being.soul,
                    'name': being.genesis.get('name', 'Unknown'),
                    'type': being.genesis.get('type', 'unknown'),
                    'created_at': being.created_at,
                    'energy_level': being.attributes.get('energy_level', 0),
                    'parent_concept': being.attributes.get('parent_concept')
                })
        
        # Sortuj chronologicznie
        creation_timeline.sort(key=lambda x: x['created_at'])
        
        # Znajdź sekwencje projektów
        current_sequence = []
        for item in creation_timeline:
            if item['parent_concept']:
                if not current_sequence or current_sequence[-1]['parent_concept'] == item['parent_concept']:
                    current_sequence.append(item)
                else:
                    if len(current_sequence) > 1:
                        project_sequences[current_sequence[0]['parent_concept']] = current_sequence.copy()
                    current_sequence = [item]
        
        # Dodaj ostatnią sekwencję
        if len(current_sequence) > 1:
            project_sequences[current_sequence[0]['parent_concept']] = current_sequence
        
        return {
            'timeline': creation_timeline,
            'project_sequences': project_sequences,
            'creation_velocity': len(creation_timeline) / max((creation_timeline[-1]['created_at'] - creation_timeline[0]['created_at']).days, 1) if len(creation_timeline) > 1 else 0,
            'most_active_period': LuxCommunicationHandler.find_most_active_period(creation_timeline)
        }

    @staticmethod
    def find_most_active_period(timeline: list) -> dict:
        """Znajdź okres największej aktywności"""
        if len(timeline) < 3:
            return {'period': 'insufficient_data', 'activity_level': 0}
        
        # Podziel na tygodnie i zlicz aktywność
        weekly_activity = {}
        for item in timeline:
            week = item['created_at'].strftime('%Y-%W')
            if week not in weekly_activity:
                weekly_activity[week] = {'count': 0, 'total_energy': 0}
            weekly_activity[week]['count'] += 1
            weekly_activity[week]['total_energy'] += item['energy_level']
        
        # Znajdź tydzień z największą aktywnością
        most_active = max(weekly_activity.items(), key=lambda x: x[1]['count'])
        
        return {
            'period': most_active[0],
            'activity_level': most_active[1]['count'],
            'total_energy': most_active[1]['total_energy']
        }

    @staticmethod
    async def analyze_energy_patterns(beings: list) -> dict:
        """Analizuje wzorce energetyczne w projektach"""
        project_energies = {}
        energy_distribution = {}
        
        for being in beings:
            energy = being.attributes.get('energy_level', 0)
            parent_concept = being.attributes.get('parent_concept')
            
            if parent_concept:
                if parent_concept not in project_energies:
                    project_energies[parent_concept] = {'total_energy': 0, 'beings_count': 0, 'avg_energy': 0}
                project_energies[parent_concept]['total_energy'] += energy
                project_energies[parent_concept]['beings_count'] += 1
        
        # Oblicz średnie energie
        for project_id, data in project_energies.items():
            data['avg_energy'] = data['total_energy'] / data['beings_count']
        
        # Rozkład energii
        energy_ranges = {'low': 0, 'medium': 0, 'high': 0, 'very_high': 0}
        for being in beings:
            energy = being.attributes.get('energy_level', 0)
            if energy < 30:
                energy_ranges['low'] += 1
            elif energy < 60:
                energy_ranges['medium'] += 1
            elif energy < 90:
                energy_ranges['high'] += 1
            else:
                energy_ranges['very_high'] += 1
        
        return {
            'project_energies': project_energies,
            'energy_distribution': energy_ranges,
            'highest_energy_project': max(project_energies.items(), key=lambda x: x[1]['total_energy']) if project_energies else None,
            'total_user_energy': sum(b.attributes.get('energy_level', 0) for b in beings)
        }

    @staticmethod
    async def synthesize_hidden_purpose(thematic_analysis: dict, temporal_analysis: dict, energy_analysis: dict) -> dict:
        """Syntetyzuje ukryty cel/misję życiową na podstawie analiz"""
        
        # Znajdź główny temat który łączy projekty
        main_connecting_theme = thematic_analysis.get('strongest_connecting_theme')
        
        # Znajdź projekt z największą energią
        highest_energy_project = energy_analysis.get('highest_energy_project')
        
        # Analiza wzorców czasowych
        creation_velocity = temporal_analysis.get('creation_velocity', 0)
        
        # Synteza
        purpose_strength = 0
        purpose_keywords = []
        purpose_description = ""
        
        if main_connecting_theme:
            purpose_strength += main_connecting_theme[1]['connection_strength'] / 100
            purpose_keywords.append(main_connecting_theme[0])
            purpose_description += f"Łączącym tematem jest '{main_connecting_theme[0]}' "
        
        if highest_energy_project:
            purpose_strength += highest_energy_project[1]['total_energy'] / 1000
            purpose_description += f"z głównym naciskiem na projekt o ID {highest_energy_project[0]} "
        
        if creation_velocity > 1:
            purpose_strength += 0.2
            purpose_description += "charakteryzującym się wysoką kreatywnością "
        
        # Kategoryzuj ukryty cel
        if purpose_strength > 0.8:
            purpose_category = "clear_life_mission"
            purpose_description = f"WYRAŹNA MISJA ŻYCIOWA: {purpose_description}"
        elif purpose_strength > 0.5:
            purpose_category = "emerging_purpose"
            purpose_description = f"WYŁANIAJĄCY SIĘ CEL: {purpose_description}"
        elif purpose_strength > 0.2:
            purpose_category = "scattered_interests"
            purpose_description = f"ROZPROSZONE ZAINTERESOWANIA: {purpose_description}"
        else:
            purpose_category = "exploration_phase"
            purpose_description = "FAZA EKSPLORACJI: Użytkownik jeszcze poszukuje swojej drogi"
        
        return {
            'category': purpose_category,
            'strength': purpose_strength,
            'description': purpose_description,
            'keywords': purpose_keywords,
            'main_theme': main_connecting_theme[0] if main_connecting_theme else None,
            'energy_focus': highest_energy_project[0] if highest_energy_project else None,
            'recommended_actions': LuxCommunicationHandler.generate_purpose_recommendations(purpose_category, purpose_strength)
        }

    @staticmethod
    def generate_purpose_recommendations(category: str, strength: float) -> list:
        """Generuje rekomendacje na podstawie odkrytego celu"""
        recommendations = {
            'clear_life_mission': [
                "🎯 Skoncentruj się na głównym celu - masz wyraźną misję!",
                "🚀 Rozwijaj projekty które wspierają Twoją główną misję",
                "📈 Zwiększ energię w kluczowych obszarach",
                "🤝 Poszukaj współpracowników którzy podzielają Twoją wizję"
            ],
            'emerging_purpose': [
                "🌱 Twój cel się krystalizuje - kontynuuj eksplorację",
                "🔍 Pogłęb analizę tematów które Cię łączą",
                "⚡ Przenieś więcej energii do obiecujących projektów",
                "📝 Dokumentuj swoje odkrycia i wzorce"
            ],
            'scattered_interests': [
                "🎨 Masz różnorodne zainteresowania - to może być Twoją siłą",
                "🔗 Szukaj połączeń między projektami",
                "📊 Przeanalizuj które projekty dają Ci najwięcej energii",
                "🎯 Rozważ wybranie 1-2 głównych kierunków"
            ],
            'exploration_phase': [
                "🗺️ Eksploruj śmiało - to naturalny etap rozwoju",
                "📚 Zbieraj doświadczenia z różnych dziedzin",
                "💡 Dokumentuj co Cię inspiruje i energetyzuje",
                "🌟 Bądź otwarty na nieoczekiwane połączenia"
            ]
        }
        return recommendations.get(category, ["🤔 Kontynuuj swoją podróż odkrywania"])

    @staticmethod
    async def generate_galactic_structure(beings: list, hidden_purpose: dict) -> dict:
        """Generuje strukturę galaktyczną dla wizualizacji"""
        main_theme = hidden_purpose.get('main_theme')
        energy_focus = hidden_purpose.get('energy_focus')
        
        # Organizuj projekty w ramiona spiralne galaktyki
        spiral_arms = {
            'main_purpose': [],  # Główne ramię - projekty związane z głównym celem
            'supporting': [],    # Ramię wspierające
            'experimental': [],  # Ramię eksperymentalne
            'legacy': []        # Ramię dziedzictwa - stare/ukończone projekty
        }
        
        for being in beings:
            parent_concept = being.attributes.get('parent_concept')
            if not parent_concept:
                continue
                
            # Klasyfikacja do ramion
            being_text = f"{being.genesis.get('name', '')} {being.genesis.get('description', '')}".lower()
            energy = being.attributes.get('energy_level', 0)
            
            if main_theme and main_theme in being_text:
                spiral_arms['main_purpose'].append({
                    'soul': being.soul,
                    'name': being.genesis.get('name', 'Unknown'),
                    'energy': energy,
                    'distance_from_center': 200,
                    'spiral_arm': 'main_purpose'
                })
            elif energy > 70:
                spiral_arms['supporting'].append({
                    'soul': being.soul,
                    'name': being.genesis.get('name', 'Unknown'),
                    'energy': energy,
                    'distance_from_center': 300,
                    'spiral_arm': 'supporting'
                })
            elif energy > 30:
                spiral_arms['experimental'].append({
                    'soul': being.soul,
                    'name': being.genesis.get('name', 'Unknown'),
                    'energy': energy,
                    'distance_from_center': 400,
                    'spiral_arm': 'experimental'
                })
            else:
                spiral_arms['legacy'].append({
                    'soul': being.soul,
                    'name': being.genesis.get('name', 'Unknown'),
                    'energy': energy,
                    'distance_from_center': 500,
                    'spiral_arm': 'legacy'
                })
        
        return {
            'spiral_arms': spiral_arms,
            'galactic_center': hidden_purpose.get('main_theme', 'Unknown Purpose'),
            'total_mass': sum(being.attributes.get('energy_level', 0) for being in beings),
            'structure_type': hidden_purpose.get('category', 'irregular_galaxy')
        }

@sio.event
async def lux_communication(sid, data):
    """Naturalna rozmowa z Lux przez GPT-4o-mini"""
    try:
        message = data.get('message', '')
        context = data.get('context', {})
        
        print(f"💬 Rozmowa z Lux od {sid}: {message}")
        
        # Pobierz kontekst projektów użytkownika
        user_projects = await get_user_projects(sid)
        context['user_projects'] = [p['name'] for p in user_projects]
        
        # Rozmowa z GPT-4o-mini
        lux_response = await conversational_lux.chat_with_gpt(message, context)
        
        # Analizuj czy w rozmowie pojawiły się konkretne akcje do wykonania
        actions = await analyze_conversation_for_actions(message, lux_response, context)
        
        # Przygotuj odpowiedź
        response = {
            'success': True,
            'lux_response': lux_response,
            'conversation_mode': True,
            'actions_detected': actions,
            'context_projects': user_projects,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"🤖 Lux odpowiada: {lux_response[:100]}...")
        
        await sio.emit('lux_conversation_response', response, room=sid)
        
        # Wykonaj wykryte akcje jeśli są
        if actions:
            await execute_conversation_actions(actions, sid, context)
        
    except Exception as e:
        print(f"Błąd w lux_communication: {e}")
        await sio.emit('error', {'message': f'Błąd rozmowy z Lux: {str(e)}'}, room=sid)

@sio.event
async def discover_hidden_purpose(sid, data):
    """Odkrywa ukryty cel/misję życiową użytkownika"""
    try:
        user_id = data.get('user_id', sid)  # Użyj sid jako fallback
        
        print(f"Odkrywanie ukrytego celu dla użytkownika: {user_id}")
        
        # Przeprowadź głęboką analizę
        deep_analysis = await LuxCommunicationHandler.discover_deep_connections(user_id)
        
        print(f"Odkryto ukryty cel: {deep_analysis['hidden_purpose']['category']}")
        
        # Wyślij wyniki
        await sio.emit('hidden_purpose_discovered', {
            'success': True,
            'analysis': deep_analysis,
            'galactic_view_update': True,
            'recommendations': deep_analysis['hidden_purpose']['recommended_actions']
        }, room=sid)
        
        # Wyślij zaktualizowaną strukturę galaktyczną
        await sio.emit('galactic_structure_update', {
            'structure': deep_analysis['galactic_structure'],
            'purpose_strength': deep_analysis['hidden_purpose']['strength'],
            'main_theme': deep_analysis['hidden_purpose']['main_theme']
        }, room=sid)
        
    except Exception as e:
        print(f"Błąd w discover_hidden_purpose: {e}")
        await sio.emit('error', {'message': f'Błąd odkrywania ukrytego celu: {str(e)}'}, room=sid)

@sio.event 
async def get_galactic_view(sid, data):
    """Zwraca widok galaktyczny dla użytkownika"""
    try:
        user_id = data.get('user_id', sid)
        
        # Pobierz wszystkie byty użytkownika
        all_beings = await BaseBeing.get_all()
        user_beings = [b for b in all_beings if b.attributes.get('user_id') == user_id]
        
        if not user_beings:
            await sio.emit('galactic_view', {
                'success': False,
                'message': 'Brak projektów do analizy'
            }, room=sid)
            return
        
        # Zorganizuj w strukturę galaktyczną
        galactic_systems = LuxOSUniverse.prototype.organizeIntoGalacticSystems(user_beings)
        
        await sio.emit('galactic_view', {
            'success': True,
            'systems': galactic_systems,
            'user_id': user_id,
            'total_beings': len(user_beings)


async def api_healthcheck(request):
    """Healthcheck endpoint dla cloud deployment"""
    global luxos_kernel, db_pool
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'database': 'unknown',
            'kernel': 'unknown',
            'orbital_manager': 'unknown'
        }
    }
    
    # Sprawdź bazę danych
    try:
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            health_status['services']['database'] = 'healthy'
        else:
            await db_pool.execute('SELECT 1')
            health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'error: {str(e)}'
        health_status['status'] = 'degraded'
    
    # Sprawdź kernel
    if luxos_kernel and luxos_kernel.running:
        health_status['services']['kernel'] = 'healthy'
    else:
        health_status['services']['kernel'] = 'not_running'
        health_status['status'] = 'degraded'
    
    # Sprawdź orbital manager
    if orbital_manager and orbital_manager.running:
        health_status['services']['orbital_manager'] = 'healthy'
    else:
        health_status['services']['orbital_manager'] = 'not_running'
        health_status['status'] = 'degraded'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return web.json_response(health_status, status=status_code)


        }, room=sid)
        
    except Exception as e:
        print(f"Błąd w get_galactic_view: {e}")
        await sio.emit('error', {'message': f'Błąd widoku galaktycznego: {str(e)}'}, room=sid)

@sio.event
async def process_intention(sid, data):
    """Przetwarza intencję użytkownika - kompatybilność wsteczna"""
    # Przekieruj do nowego systemu
    await lux_communication(sid, {'message': data.get('intention', ''), 'context': data.get('context', {})})

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
    """Zwraca puste dane grafu - frontend generuje lokalnie"""
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
    """Frontend zarządza danymi lokalnie - nie potrzebujemy rozgłaszać"""
    pass

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
        # Tabela base_beings
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS base_beings (
                soul UUID PRIMARY KEY,
                genesis JSONB NOT NULL,
                attributes JSONB NOT NULL,
                memories JSONB NOT NULL,
                self_awareness JSONB NOT NULL,
                binary_data BYTEA,
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

        # Najpierw sprawdź czy tabele istnieją
        tables_exist = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name IN ('base_beings', 'relationships')
        """)
        
        if tables_exist == 2:
            # Constraints dla relationships - tylko jeśli tabele istnieją
            await conn.execute("""
                ALTER TABLE relationships 
                DROP CONSTRAINT IF EXISTS valid_source_soul
            """)
            await conn.execute("""
                ALTER TABLE relationships 
                ADD CONSTRAINT valid_source_soul 
                FOREIGN KEY (source_soul) REFERENCES base_beings (soul) ON DELETE CASCADE
            """)

            await conn.execute("""
                ALTER TABLE relationships 
                DROP CONSTRAINT IF EXISTS valid_target_soul
            """)
            await conn.execute("""
                ALTER TABLE relationships 
                ADD CONSTRAINT valid_target_soul 
                FOREIGN KEY (target_soul) REFERENCES base_beings (soul) ON DELETE CASCADE
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

        # Tabela binary_storage dla danych binarnych
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS binary_storage (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                being_soul UUID NOT NULL,
                file_name VARCHAR(255),
                mime_type VARCHAR(100),
                file_size INTEGER,
                binary_data BYTEA NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (being_soul) REFERENCES base_beings(soul) ON DELETE CASCADE
            )
        """)

        # Tabela souls - dusze/wiadomości/informacje
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS souls (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                content JSONB NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela soul_relations - jak byty postrzegają dusze
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS soul_relations (
                being_soul UUID NOT NULL,
                soul_id UUID NOT NULL,
                interpretation JSONB DEFAULT '{}',
                emotional_response FLOAT DEFAULT 0.0,
                relevance FLOAT DEFAULT 0.5,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (being_soul, soul_id),
                FOREIGN KEY (being_soul) REFERENCES base_beings(soul) ON DELETE CASCADE,
                FOREIGN KEY (soul_id) REFERENCES souls(id) ON DELETE CASCADE
            )
        """)

        # Indeksy
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_genesis ON base_beings USING gin (genesis)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_attributes ON base_beings USING gin (attributes)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_memories ON base_beings USING gin (memories)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_self_awareness ON base_beings USING gin (self_awareness)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_binary_storage_being_soul ON binary_storage (being_soul)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_binary_storage_mime_type ON binary_storage (mime_type)")

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
            binary_data BLOB,
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

    await db_pool.execute("""
        CREATE TABLE IF NOT EXISTS binary_storage (
            id TEXT PRIMARY KEY,
            being_soul TEXT NOT NULL,
            file_name TEXT,
            mime_type TEXT,
            file_size INTEGER,
            binary_data BLOB NOT NULL,
            metadata TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (being_soul) REFERENCES base_beings(soul) ON DELETE CASCADE
        )
    """)

    await db_pool.execute("""
        CREATE TABLE IF NOT EXISTS souls (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            metadata TEXT DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await db_pool.execute("""
        CREATE TABLE IF NOT EXISTS soul_relations (
            being_soul TEXT NOT NULL,
            soul_id TEXT NOT NULL,
            interpretation TEXT DEFAULT '{}',
            emotional_response REAL DEFAULT 0.0,
            relevance REAL DEFAULT 0.5,
            last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (being_soul, soul_id),
            FOREIGN KEY (being_soul) REFERENCES base_beings(soul) ON DELETE CASCADE,
            FOREIGN KEY (soul_id) REFERENCES souls(id) ON DELETE CASCADE
        )
    """)

    await db_pool.commit()

# Import kernela
from app.core.kernel import LuxOSKernel
from app.database.connection import DatabaseManager

# Globalna instancja kernela
luxos_kernel = None

# Konfiguracja aplikacji
async def init_app():
    global luxos_kernel
    
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
    
    # Dodaj trasę dla statusu kernela
    app.router.add_route('GET', '/api/kernel/status', api_kernel_status)
    
    # Healthcheck dla cloud deployment
    app.router.add_route('GET', '/health', api_healthcheck)
    app.router.add_route('GET', '/api/health', api_healthcheck)

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
    
    # Inicjalizuj kernel
    await init_kernel()

async def get_user_projects(user_id: str) -> List[Dict]:
    """Pobiera projekty użytkownika"""
    try:
        beings = await BaseBeing.get_all()
        user_projects = []
        
        for being in beings:
            if (being.attributes.get('user_id') == user_id or 
                being.genesis.get('created_by') in ['intention', 'lux_contextual_analysis']):
                
                # Sprawdź czy to projekt główny (parent concept) 
                if being.attributes.get('is_parent_concept') or being.genesis.get('type') in ['orbital_task', 'project']:
                    user_projects.append({
                        'soul': being.soul,
                        'name': being.genesis.get('name', 'Unknown'),
                        'type': being.genesis.get('type', 'unknown'),
                        'energy': being.attributes.get('energy_level', 0),
                        'status': being.attributes.get('task_status', 'unknown')
                    })
        
        return user_projects
    except Exception as e:
        logger.error(f"Error getting user projects: {e}")
        return []

async def analyze_conversation_for_actions(user_message: str, lux_response: str, context: dict) -> List[Dict]:
    """Analizuje rozmowę w poszukiwaniu konkretnych akcji do wykonania"""
    actions = []
    message_lower = user_message.lower()
    response_lower = lux_response.lower()
    
    # Wykryj tworzenie projektów
    if any(phrase in message_lower for phrase in ['stwórz', 'utwórz', 'nowy projekt', 'nowy bot']):
        # Wykryj typ projektu
        if 'bot' in message_lower:
            if 'discord' in message_lower:
                actions.append({
                    'type': 'create_project',
                    'project_type': 'discord_bot',
                    'name': 'Discord Bot',
                    'cycle_period': 300  # 5 minut
                })
            elif 'telegram' in message_lower:
                actions.append({
                    'type': 'create_project', 
                    'project_type': 'telegram_bot',
                    'name': 'Telegram Bot',
                    'cycle_period': 300
                })
        elif any(word in message_lower for word in ['strona', 'website', 'portal']):
            actions.append({
                'type': 'create_project',
                'project_type': 'website',
                'name': 'Website Project',
                'cycle_period': 3600  # 1 godzina
            })
        elif 'aplikacj' in message_lower:
            actions.append({
                'type': 'create_project',
                'project_type': 'application',
                'name': 'Application Project', 
                'cycle_period': 1800  # 30 minut
            })
    
    # Wykryj modyfikacje projektów
    if any(phrase in message_lower for phrase in ['zmień', 'modyfikuj', 'zaktualizuj']):
        # Sprawdź czy wskazano konkretny projekt w kontekście
        if context.get('selected_nodes'):
            actions.append({
                'type': 'modify_project',
                'target_souls': context['selected_nodes'],
                'modification_type': 'user_requested'
            })
    
    # Wykryj uruchamianie projektów
    if any(phrase in message_lower for phrase in ['uruchom', 'zacznij', 'aktywuj']):
        actions.append({
            'type': 'activate_projects',
            'target': 'user_selection' if context.get('selected_nodes') else 'all_user_projects'
        })
    
    return actions

async def execute_conversation_actions(actions: List[Dict], user_id: str, context: dict):
    """Wykonuje akcje wykryte w rozmowie"""
    for action in actions:
        try:
            if action['type'] == 'create_project':
                await create_conversational_project(action, user_id, context)
            elif action['type'] == 'modify_project':
                await modify_conversational_project(action, user_id)
            elif action['type'] == 'activate_projects':
                await activate_user_projects(action, user_id)
                
        except Exception as e:
            logger.error(f"Error executing conversation action {action['type']}: {e}")

async def create_conversational_project(action: Dict, user_id: str, context: dict):
    """Tworzy projekt na podstawie rozmowy"""
    project_type = action['project_type']
    name = action['name']
    cycle_period = action.get('cycle_period', 3600)
    
    # Utwórz orbital task jako główny projekt
    orbital_task = await OrbitalTask.create(
        genesis={
            'type': 'orbital_task',
            'name': name,
            'description': f'{project_type} projekt utworzony w rozmowie z Lux',
            'project_type': project_type,
            'created_by': 'conversational_lux'
        },
        attributes={
            'energy_level': 600,
            'user_id': user_id,
            'task_classification': 'project',
            'orbital_params': {
                'parent_soul': None,
                'orbital_period': cycle_period,
                'orbital_radius': 200,
                'last_cycle_time': datetime.now().timestamp(),
                'cycle_count': 0
            },
            'project_config': {
                'auto_start': True,
                'background_execution': True,
                'conversation_manageable': True
            },
            'tags': ['conversational', 'project', project_type, 'orbital']
        },
        memories=[{
            'type': 'conversational_creation',
            'data': f'Projekt {name} utworzony w rozmowie z Lux',
            'project_type': project_type,
            'timestamp': datetime.now().isoformat()
        }]
    )
    
    print(f"✨ Utworzono projekt rozmowny: {name} ({project_type})")
    
    # Wyślij informację do frontend
    await sio.emit('conversational_project_created', {
        'project_soul': orbital_task.soul,
        'project_name': name,
        'project_type': project_type,
        'cycle_period': cycle_period
    })

async def modify_conversational_project(action: Dict, user_id: str):
    """Modyfikuje projekt na podstawie rozmowy"""
    target_souls = action['target_souls']
    
    for soul in target_souls:
        being = await BaseBeing.load(soul)
        if being and being.attributes.get('user_id') == user_id:
            # Dodaj znacznik modyfikacji rozmownej
            being.attributes['last_conversation_modification'] = datetime.now().isoformat()
            being.memories.append({
                'type': 'conversational_modification',
                'data': 'Projekt zmodyfikowany w rozmowie z Lux',
                'timestamp': datetime.now().isoformat()
            })
            await being.save()

async def activate_user_projects(action: Dict, user_id: str):
    """Aktywuje projekty użytkownika"""
    if action['target'] == 'all_user_projects':
        # Aktywuj wszystkie projekty użytkownika
        beings = await BaseBeing.get_all()
        for being in beings:
            if (being.attributes.get('user_id') == user_id and 
                being.genesis.get('type') == 'orbital_task'):
                being.attributes['task_status'] = 'active'
                being.attributes['activated_via_conversation'] = True
                await being.save()

class OrbitalCycleManager:
    """Menedżer cykli orbitalnych - zarządza wykonywaniem zadań"""
    
    def __init__(self):
        self.running = False
        self.cycle_task = None
    
    async def start(self):
        """Uruchamia menedżera cykli"""
        if self.running:
            return
        
        self.running = True
        self.cycle_task = asyncio.create_task(self.cycle_loop())
        print("🌍 Orbital Cycle Manager uruchomiony")
    
    async def stop(self):
        """Zatrzymuje menedżera cykli"""
        self.running = False
        if self.cycle_task:
            self.cycle_task.cancel()
            try:
                await self.cycle_task
            except asyncio.CancelledError:
                pass
        print("🌍 Orbital Cycle Manager zatrzymany")
    
    async def cycle_loop(self):
        """Główna pętla sprawdzająca cykle orbitalne"""
        while self.running:
            try:
                await self.check_and_execute_cycles()
                await asyncio.sleep(10)  # Sprawdzaj co 10 sekund
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Błąd w cycle_loop: {e}")
                await asyncio.sleep(30)  # Długższa pauza przy błędzie
    
    async def check_and_execute_cycles(self):
        """Sprawdza i wykonuje gotowe cykle orbitalne"""
        try:
            # Pobierz wszystkie OrbitalTask byty - używamy BeingFactory
            beings = []
            try:
                # Spróbuj pobrać z bazy danych bezpośrednio
                global db_pool
                if hasattr(db_pool, 'acquire'):
                    async with db_pool.acquire() as conn:
                        rows = await conn.fetch("SELECT * FROM base_beings LIMIT 100")
                        for row in rows:
                            being = BaseBeing(
                                soul=str(row['soul']),
                                genesis=row['genesis'],
                                attributes=row['attributes'],
                                memories=row['memories'],
                                self_awareness=row['self_awareness'],
                                created_at=row['created_at']
                            )
                            beings.append(being)
                else:
                    # SQLite fallback
                    async with db_pool.execute("SELECT * FROM base_beings LIMIT 100") as cursor:
                        rows = await cursor.fetchall()
                        for row in rows:
                            try:
                                being = BaseBeing(
                                    soul=row[0],
                                    genesis=json.loads(row[3]) if row[3] else {},
                                    attributes=json.loads(row[4]) if row[4] else {},
                                    memories=json.loads(row[5]) if row[5] else [],
                                    self_awareness=json.loads(row[6]) if row[6] else {},
                                    created_at=row[7]
                                )
                                beings.append(being)
                            except Exception as e:
                                continue  # Pomiń problematyczne rekordy
            except Exception as e:
                print(f"Błąd pobierania bytów z bazy: {e}")
                return
            
            orbital_tasks = [b for b in beings if b.genesis.get('type') == 'orbital_task']
            
            executed_cycles = 0
            
            for task in orbital_tasks:
                # Sprawdź czy to rzeczywiście OrbitalTask
                if 'orbital_params' not in task.attributes:
                    continue
                
                # Przekształć do OrbitalTask (duck typing)
                orbital_task = OrbitalTask(
                    soul=task.soul,
                    genesis=task.genesis,
                    attributes=task.attributes,
                    memories=task.memories,
                    self_awareness=task.self_awareness,
                    created_at=task.created_at
                )
                
                # Sprawdź czy nadszedł czas na cykl
                if await orbital_task.orbital_cycle_check():
                    print(f"🔄 Wykonuję cykl orbitalny dla: {orbital_task.genesis.get('name', 'Unknown')}")
                    
                    # Wykonaj cykl
                    report = await orbital_task.execute_orbital_cycle()
                    executed_cycles += 1
                    
                    # Wyślij informację do frontend (jeśli potrzeba)
                    await sio.emit('orbital_cycle_completed', {
                        'task_soul': orbital_task.soul,
                        'task_name': orbital_task.genesis.get('name', 'Unknown'),
                        'report': report
                    })
            
            if executed_cycles > 0:
                print(f"✅ Wykonano {executed_cycles} cykli orbitalnych")
                
        except Exception as e:
            print(f"Błąd w check_and_execute_cycles: {e}")

# Globalny menedżer cykli
orbital_manager = OrbitalCycleManager()

async def main():
    """Główna funkcja uruchamiająca system LuxOS"""
    global luxos_kernel
    
    print("🌟 LuxOS - System Bytów Astralnych - STARTING")
    print("=" * 60)
    
    # Sprawdź tryb uruchomienia
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'full'
    
    try:
        # Inicjalizuj OpenAI dla rozmów z Lux
        init_openai()
        
        await init_app()
        
        # Uruchom menedżera cykli orbitalnych
        await orbital_manager.start()
        
        # Wybierz port na podstawie środowiska
        port = int(os.getenv('PORT', 8000))
        host = '0.0.0.0'  # Dla chmury zawsze 0.0.0.0
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        print(f"🌐 Serwer uruchomiony na http://{host}:{port}")
        print("🌍 System orbital z hierarchią zadań aktywny!")
        
        if luxos_kernel:
            print(f"🧠 Kernel LuxOS aktywny: {luxos_kernel.KERNEL_SOUL_ID}")
        
        print("✅ System LuxOS w pełni aktywny!")
        print("=" * 60)

        # Trzymaj serwer żywy
        shutdown_event = asyncio.Event()
        
        # Obsługa sygnałów
        def signal_handler():
            print("⚠️ Otrzymano sygnał przerwania...")
            shutdown_event.set()
        
        # Rejestruj handlery dla różnych sygnałów
        try:
            import signal
            loop = asyncio.get_event_loop()
            for sig in [signal.SIGTERM, signal.SIGINT]:
                loop.add_signal_handler(sig, signal_handler)
        except (ImportError, NotImplementedError):
            # Windows lub inne systemy bez sygnałów
            pass
        
        try:
            await shutdown_event.wait()
        except KeyboardInterrupt:
            signal_handler()
            
    except Exception as e:
        print(f"💥 Krytyczny błąd systemu: {e}")
        raise
    finally:
        print("🛑 Zamykanie systemu LuxOS...")
        if luxos_kernel:
            try:
                await luxos_kernel.shutdown()
            except Exception as e:
                print(f"Błąd zamykania kernela: {e}")
        
        try:
            await orbital_manager.stop()
        except Exception as e:
            print(f"Błąd zamykania orbital manager: {e}")
        
        try:
            await runner.cleanup()
        except Exception as e:
            print(f"Błąd zamykania serwera web: {e}")
        
        print("✅ System LuxOS zamknięty")
        print("👋 Do widzenia!")

class BeingFactory:
    """Factory do tworzenia różnych typów bytów"""

    BEING_TYPES = {
        'function': FunctionBeing,
        'class': ClassBeing,
        'data': DataBeing,
        'scenario': ScenarioBeing,
        'task': TaskBeing,
        'orbital_task': OrbitalTask,
        'component': ComponentBeing,
        'binary': BinaryBeing,
        'base': BaseBeing
    }

    @classmethod
    async def create_being(cls, being_type: str, genesis: Dict[str, Any], **kwargs) -> BaseBeing:
        """Tworzy byt odpowiedniego typu"""
        BeingClass = cls.BEING_TYPES.get(being_type, BaseBeing)

        # Upewnij się, że typ jest ustawiony w genesis
        genesis['type'] = being_type

        # Generuj unikalne soul
        soul = str(uuid.uuid4())

        # Przygotuj atrybuty
        attributes = kwargs.get('attributes', {})
        if 'tags' in kwargs:
            attributes['tags'] = kwargs['tags']
        if 'energy_level' in kwargs:
            attributes['energy_level'] = kwargs['energy_level']

        # Utwórz byt
        being = BeingClass(
            soul=soul,
            genesis=genesis,
            attributes=attributes,
            memories=kwargs.get('memories', []),
            self_awareness=kwargs.get('self_awareness', {})
        )

        await being.save()
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

async def init_kernel():
    """Inicjalizuje kernel LuxOS"""
    global luxos_kernel, db_pool
    
    try:
        print("🚀 Inicjalizacja kernela LuxOS...")
        
        # Utwórz DatabaseManager z istniejącym połączeniem
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            db_manager = DatabaseManager(db_type='postgresql', connection_pool=db_pool)
        else:
            # SQLite
            db_manager = DatabaseManager(db_type='sqlite', connection=db_pool)
        
        # Utwórz kernel
        luxos_kernel = LuxOSKernel(db_manager)
        
        # Inicjalizuj kernel
        if await luxos_kernel.initialize():
            print("✅ Kernel LuxOS zainicjalizowany pomyślnie")
            
            # Uruchom główną pętlę kernela w tle
            asyncio.create_task(luxos_kernel.start_main_loop())
            print("🌟 Główna pętla kernela uruchomiona w tle")
        else:
            print("❌ Nie udało się zainicjalizować kernela")
            
    except Exception as e:
        print(f"💥 Błąd inicjalizacji kernela: {e}")

async def api_kernel_status(request):
    """API endpoint dla statusu kernela"""
    global luxos_kernel
    
    if luxos_kernel:
        status = luxos_kernel.get_kernel_state()
        # Konwertuj dataclass do dict
        status_dict = {
            'kernel_soul': status.kernel_soul,
            'created_at': status.created_at.isoformat(),
            'last_heartbeat': status.last_heartbeat.isoformat(),
            'active_users': list(status.active_users),
            'total_beings': status.total_beings,
            'uptime_seconds': status.uptime_seconds,
            'running': luxos_kernel.running
        }
        return web.json_response(status_dict)
    else:
        return web.json_response({
            'status': 'not_initialized',
            'message': 'Kernel nie został zainicjalizowany'
        })

# Globalna pula połączeń do bazy danych

if __name__ == '__main__':
    asyncio.run(main())