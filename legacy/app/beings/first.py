
from typing import Dict, Any, List, Optional, Type
from abc import ABC, abstractmethod
from datetime import datetime
import uuid
import json
import importlib
import types


class SelfContainedGene(ABC):
    """Gen samowystarczalny - zawiera wszystkie potrzebne informacje do swojej budowy"""

    def __init__(self, gene_id: Optional[str] = None):
        self.gene_id = gene_id or str(uuid.uuid4())
        self.is_active = False
        self.host_being = None
        self.autonomy_level = 0
        self.gene_memories: List[Dict[str, Any]] = []

        # Samowystarczalne definicje
        self._dependencies = self.get_dependencies()
        self._code_fragments = self.get_code_fragments()
        self._configuration = self.get_configuration()

        # Zbuduj wymagane komponenty
        self._build_internal_components()

    @property
    @abstractmethod
    def gene_type(self) -> str:
        """Typ genu"""
        pass

    @abstractmethod
    def get_dependencies(self) -> Dict[str, str]:
        """Zwraca słownik zależności: nazwa -> kod źródłowy"""
        pass

    @abstractmethod
    def get_code_fragments(self) -> Dict[str, str]:
        """Zwraca fragmenty kodu potrzebne do działania genu"""
        pass

    @abstractmethod
    def get_configuration(self) -> Dict[str, Any]:
        """Zwraca konfigurację genu"""
        pass

    def _build_internal_components(self):
        """Zbuduj wewnętrzne komponenty z zawartych definicji"""
        # Utwórz moduły z dependencies
        self._internal_modules = {}

        for module_name, code in self._dependencies.items():
            module = types.ModuleType(module_name)
            try:
                exec(code, module.__dict__)
                self._internal_modules[module_name] = module
            except Exception as e:
                print(f"Błąd budowy modułu {module_name}: {e}")

        # Wykonaj fragmenty kodu
        for fragment_name, code in self._code_fragments.items():
            try:
                exec(code, globals(), locals())
            except Exception as e:
                print(f"Błąd wykonania fragmentu {fragment_name}: {e}")

    def get_internal_module(self, module_name: str):
        """Pobierz wewnętrzny moduł"""
        return self._internal_modules.get(module_name)

    def to_serializable_dict(self) -> Dict[str, Any]:
        """Serializuj gen do słownika zawierającego wszystkie informacje"""
        return {
            'gene_id': self.gene_id,
            'gene_type': self.gene_type,
            'autonomy_level': self.autonomy_level,
            'dependencies': self._dependencies,
            'code_fragments': self._code_fragments,
            'configuration': self._configuration,
            'memories': self.gene_memories,
            'is_active': self.is_active
        }

    @classmethod
    def from_serializable_dict(cls, data: Dict[str, Any]) -> 'SelfContainedGene':
        """Odtwórz gen ze słownika"""
        # To będzie implementowane w konkretnych genach
        raise NotImplementedError("Implement in subclass")


class SelfContainedDatabaseGene(SelfContainedGene):
    """Samowystarczalny gen bazy danych"""

    @property
    def gene_type(self) -> str:
        return "self_contained_database"

    def get_dependencies(self) -> Dict[str, str]:
        """Wszystkie potrzebne importy jako kod"""
        return {
            'sqlite_wrapper': '''
import sqlite3
import aiosqlite
import json
from datetime import datetime

class SQLiteWrapper:
    def __init__(self, db_path=":memory:"):
        self.db_path = db_path
        self.connection = None

    async def connect(self):
        self.connection = await aiosqlite.connect(self.db_path)
        return self.connection

    async def execute(self, query, params=None):
        if not self.connection:
            await self.connect()
        return await self.connection.execute(query, params or ())

    async def fetchall(self, query, params=None):
        cursor = await self.execute(query, params)
        return await cursor.fetchall()

    async def close(self):
        if self.connection:
            await self.connection.close()
            ''',

            'data_manager': '''
class DataManager:
    def __init__(self, sqlite_wrapper):
        self.db = sqlite_wrapper

    async def store_data(self, key, value, data_type="json"):
        serialized = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
        await self.db.execute(
            "INSERT OR REPLACE INTO gene_data (key, value, data_type, updated_at) VALUES (?, ?, ?, ?)",
            (key, serialized, data_type, datetime.now().isoformat())
        )

    async def get_data(self, key):
        rows = await self.db.fetchall("SELECT value, data_type FROM gene_data WHERE key = ?", (key,))
        if not rows:
            return None

        value, data_type = rows[0]
        if data_type == "json":
            try:
                return json.loads(value)
            except:
                return value
        return value
            '''
        }

    def get_code_fragments(self) -> Dict[str, str]:
        """Fragmenty kodu do wykonania"""
        return {
            'setup_tables': '''
async def setup_database_tables(db_connection):
    await db_connection.execute("""
        CREATE TABLE IF NOT EXISTS gene_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            data_type TEXT DEFAULT 'string',
            updated_at TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await db_connection.execute("""
        CREATE TABLE IF NOT EXISTS gene_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            memory_type TEXT NOT NULL,
            data TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await db_connection.commit()
            '''
        }

    def get_configuration(self) -> Dict[str, Any]:
        """Konfiguracja genu"""
        return {
            'required_energy': 25,
            'compatibility_tags': ['communication', 'ai_model', 'embedding'],
            'db_config': {
                'in_memory': True,
                'sync_interval': 300,
                'auto_backup': True
            },
            'features': ['data_storage', 'memory_management', 'auto_sync']
        }

    async def activate(self, host_being, context):
        """Aktywuj gen używając wbudowanych komponentów"""
        if host_being.energy_level < self._configuration['required_energy']:
            return False

        # Użyj wbudowanych modułów
        sqlite_module = self.get_internal_module('sqlite_wrapper')
        data_manager_module = self.get_internal_module('data_manager')

        # Utwórz instancje z wbudowanych klas
        self.sqlite_wrapper = sqlite_module.SQLiteWrapper()
        await self.sqlite_wrapper.connect()

        # Wykonaj setup z fragmentów kodu
        setup_func = globals().get('setup_database_tables')
        if setup_func:
            await setup_func(self.sqlite_wrapper.connection)

        self.data_manager = data_manager_module.DataManager(self.sqlite_wrapper)

        self.host_being = host_being
        self.is_active = True

        # Odejmij energię
        host_being.energy_level -= self._configuration['required_energy']

        return True

    async def deactivate(self):
        """Dezaktywuj gen"""
        if hasattr(self, 'sqlite_wrapper'):
            await self.sqlite_wrapper.close()
        self.is_active = False
        return True

    async def express(self, stimulus: Dict[str, Any]) -> Dict[str, Any]:
        """Wyraź funkcję genu"""
        if not self.is_active:
            return {'error': 'Gene not active'}

        action = stimulus.get('action')

        if action == 'store':
            await self.data_manager.store_data(
                stimulus.get('key'), 
                stimulus.get('value')
            )
            return {'status': 'stored', 'key': stimulus.get('key')}

        elif action == 'get':
            data = await self.data_manager.get_data(stimulus.get('key'))
            return {'status': 'retrieved', 'data': data}

        elif action == 'get_stats':
            rows = await self.sqlite_wrapper.fetchall("SELECT COUNT(*) FROM gene_data")
            count = rows[0][0] if rows else 0
            return {
                'data_count': count,
                'is_active': self.is_active,
                'autonomy_level': self.autonomy_level
            }

        return {'error': 'Unknown action'}

    @classmethod
    def from_serializable_dict(cls, data: Dict[str, Any]) -> 'SelfContainedDatabaseGene':
        """Odtwórz gen ze słownika"""
        gene = cls(gene_id=data['gene_id'])
        gene.autonomy_level = data['autonomy_level']
        gene.gene_memories = data['memories']
        gene.is_active = data.get('is_active', False)
        return gene


class SelfContainedCommunicationGene(SelfContainedGene):
    """Samowystarczalny gen komunikacji"""

    @property
    def gene_type(self) -> str:
        return "self_contained_communication"

    def get_dependencies(self) -> Dict[str, str]:
        return {
            'message_handler': '''
import json
from datetime import datetime

class MessageHandler:
    def __init__(self):
        self.message_queue = []
        self.connections = {}

    def add_message(self, sender, recipient, content, protocol="direct"):
        message = {
            'id': str(uuid.uuid4())[:8],
            'sender': sender,
            'recipient': recipient,
            'content': content,
            'protocol': protocol,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        self.message_queue.append(message)
        return message

    def get_messages_for(self, recipient):
        return [msg for msg in self.message_queue if msg['recipient'] == recipient]

    def mark_delivered(self, message_id):
        for msg in self.message_queue:
            if msg['id'] == message_id:
                msg['status'] = 'delivered'
                break
            '''
        }

    def get_code_fragments(self) -> Dict[str, str]:
        return {
            'protocol_handlers': '''
def handle_direct_call(message_data):
    return {
        'status': 'delivered',
        'method': 'direct_call',
        'delivered_at': datetime.now().isoformat()
    }

def handle_queue_based(message_data):
    return {
        'status': 'queued',
        'method': 'queue_based',
        'queued_at': datetime.now().isoformat()
    }
            '''
        }

    def get_configuration(self) -> Dict[str, Any]:
        return {
            'required_energy': 15,
            'compatibility_tags': ['database', 'ai_model', 'embedding'],
            'protocols': ['direct_call', 'queue_based', 'socket_io'],
            'max_connections': 50,
            'message_ttl': 3600
        }

    async def activate(self, host_being, context):
        if host_being.energy_level < self._configuration['required_energy']:
            return False

        # Użyj wbudowanych komponentów
        message_module = self.get_internal_module('message_handler')
        self.message_handler = message_module.MessageHandler()

        self.host_being = host_being
        self.is_active = True
        host_being.energy_level -= self._configuration['required_energy']

        return True

    async def deactivate(self):
        self.is_active = False
        return True

    async def express(self, stimulus: Dict[str, Any]) -> Dict[str, Any]:
        if not self.is_active:
            return {'error': 'Gene not active'}

        action = stimulus.get('action')

        if action == 'send_message':
            message = self.message_handler.add_message(
                sender=self.host_being.soul,
                recipient=stimulus.get('target_soul'),
                content=stimulus.get('message'),
                protocol=stimulus.get('protocol', 'direct_call')
            )

            # Symulacja wysyłki
            protocol_handler = globals().get('handle_direct_call')
            if protocol_handler:
                result = protocol_handler(message)
                return {**message, **result}

            return message

        elif action == 'get_messages':
            messages = self.message_handler.get_messages_for(self.host_being.soul)
            return {'messages': messages, 'count': len(messages)}

        return {'error': 'Unknown action'}

    @classmethod
    def from_serializable_dict(cls, data: Dict[str, Any]) -> 'SelfContainedCommunicationGene':
        gene = cls(gene_id=data['gene_id'])
        gene.autonomy_level = data['autonomy_level']
        gene.gene_memories = data['memories']
        gene.is_active = data.get('is_active', False)
        return gene
