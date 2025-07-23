import asyncio
import json
from datetime import datetime
from dataclasses import asdict
import socketio
from aiohttp import web
import aiohttp_cors
import logging
import os
from lux_tools import LuxTools
import asyncpg
import aiosqlite
from app.database import set_db_pool, get_db_pool
from app.beings.base import BaseBeing, Relationship
from app.beings.being_factory import BeingFactory
from app.beings.function_router import FunctionRouter
from app.beings import DateTimeEncoder
from app.ai.function_calling import OpenAIFunctionCaller
from app.genetics.genetic_system import genetic_system



# Setup logger
logger = logging.getLogger(__name__)

# Globalna pula połączeń do bazy danych
db_pool = None

# Socket.IO serwer
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

# Router funkcji
function_router = FunctionRouter()

# Narzędzia Lux
lux_tools = LuxTools(openai_api_key=os.getenv('OPENAI_API_KEY'))

# OpenAI Function Caller
openai_function_caller = None
if os.getenv('OPENAI_API_KEY'):
    openai_function_caller = OpenAIFunctionCaller(openai_api_key=os.getenv('OPENAI_API_KEY'))





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
    task_id = data.get('taskId')

    try:
        being_type = data.get('being_type', 'base')

        # BLOKUJ tworzenie Lux przez frontend
        genesis = data.get('genesis', {})
        if (genesis.get('name') == 'Lux' or 
            genesis.get('type') == 'agent' and 'lux' in genesis.get('name', '').lower()):
            response = {
                'success': False,
                'error': 'BŁĄD: Nie można tworzyć agenta Lux przez frontend. Lux jest zarządzana przez system genetyczny.',
                'taskId': task_id
            }
            await sio.emit('task_response', response, room=sid)
            return

        being = await BeingFactory.create_being(
            being_type=being_type,
            genesis=genesis,
            tags=data.get('tags', []),            
            energy_level=data.get('energy_level', 0),
            attributes=data.get('attributes', {}),
            memories=data.get('memories', []),
            self_awareness=data.get('self_awareness', {})
        )

        # Konwertuj do JSON-safe format
        being_dict = json.loads(json.dumps(asdict(being), cls=DateTimeEncoder))

        # Wyślij potwierdzenie sukcesu
        if task_id:
            response = {
                'success': True,
                'being': being_dict,
                'message': 'Byt został utworzony pomyślnie',
                'taskId': task_id
            }
            await sio.emit('task_response', response, room=sid)

        # Wyślij do wszystkich klientów
        await sio.emit('being_created', being_dict)
        await sio.emit('node_added', being_dict)

    except Exception as e:
        response = {
            'success': False,
            'error': str(e),
            'taskId': task_id
        }
        await sio.emit('task_response', response, room=sid)

@sio.event
async def create_relationship(sid, data):
    """Tworzy nową relację"""
    global db_pool
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
    global db_pool
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
    global db_pool
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
async def lux_use_tool(sid, data):
    """Wykonuje narzędzie przez Lux"""
    try:
        tool_name = data.get('tool_name')
        parameters = data.get('parameters', {})

        if not tool_name:
            await sio.emit('error', {'message': 'Brak nazwy narzędzia'}, room=sid)
            return

        print(f"Lux używa narzędzia: {tool_name} z parametrami: {parameters}")

        result = await lux_tools.execute_tool(tool_name, parameters)

        # Zapisz użycie narzędzia w pamięci Lux
        if result['success']:
            # Znajdź byt Lux i zapisz w pamięci
            lux_soul = '00000000-0000-0000-0000-000000000001'
            lux_being = await BaseBeing.load(lux_soul)
            if lux_being:
                memory_entry = {
                    'type': 'tool_usage',
                    'tool_name': tool_name,
                    'parameters': parameters,
                    'result_summary': str(result.get('result', {}))[:200],
                    'timestamp': datetime.now().isoformat(),
                    'success': True
                }
                lux_being.memories.append(memory_entry)
                await lux_being.save()

        await sio.emit('lux_tool_result', result, room=sid)

    except Exception as e:
        error_result = {
            'success': False,
            'error': f'Błąd wykonania narzędzia: {str(e)}',
            'tool_name': tool_name if 'tool_name' in locals() else 'unknown'
        }
        await sio.emit('lux_tool_result', error_result, room=sid)

@sio.event
async def lux_communication(sid, data):
    """Obsługuje komunikację z Lux z inteligentną delegacją zadań"""
    global db_pool
    try:
        message = data.get('message', '').lower()
        context = data.get('context', {})
        task_analysis = data.get('task_analysis', {})

        print(f"Lux otrzymuje komunikat od {sid}: {message}")
        print(f"Analiza zadania: {task_analysis}")

        # Utwórz byt wiadomości z informacjami o delegacji
        message_being = await BeingFactory.create_being(
            being_type='message',
            genesis={
                'type': 'message',
                'name': f'Lux_Communication_{datetime.now().strftime("%H%M%S")}',
                'created_by': 'lux_communication',
                'source': 'user_input'
            },
            attributes={
                'message_data': {
                    'content': message,
                    'length': len(message),
                    'timestamp': datetime.now().isoformat()
                },
                'task_delegation': task_analysis,
                'metadata': {
                    'sender': sid,
                    'context': context,
                    'message_type': 'lux_communication',
                    'frontend_capabilities': context.get('frontend_capabilities', {})
                }
            },
            memories=[{
                'type': 'creation',
                'data': f'Lux communication from user {sid} with delegation analysis',
                'timestamp': datetime.now().isoformat()
            }],
            tags=['message', 'lux_communication', 'user_input', 'delegated_task'],
            energy_level=80
        )

        # Podejmij decyzję o delegacji zadania
        delegation_decision = await make_delegation_decision(message, task_analysis, context)

        # Wykonaj zadanie zgodnie z decyzją o delegacji
        if delegation_decision['execute_on'] == 'backend':
            response = await execute_backend_task(message, context, delegation_decision)
        elif delegation_decision['execute_on'] == 'hybrid':
            response = await execute_hybrid_task(message, context, delegation_decision)
        else:
            # Standardowa analiza dla zadań frontendowych
            response = await analyze_lux_communication(message, context)

        response['message_being_soul'] = message_being.soul
        response['delegation_info'] = delegation_decision

        print(f"Odpowiedź Lux: {response}")
        await sio.emit('lux_communication_response', response, room=sid)

        await broadcast_graph_update()

    except Exception as e:
        print(f"Błąd komunikacji z Lux: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        await sio.emit('error', {'message': f'Błąd komunikacji z Lux: {str(e)}'}, room=sid)

@sio.event
async def get_available_tools(sid, data):
    """Zwraca listę dostępnych narzędzi"""
    try:
        tools_info = {
            'read_file': 'Odczytuje zawartość pliku',
            'write_file': 'Zapisuje zawartość do pliku', 
            'list_files': 'Listuje pliki w katalogu',
            'analyze_code': 'Analizuje kod Python',
            'run_tests': 'Uruchamia testy',
            'ask_gpt': 'Wysyła zapytanie do GPT',
            'create_directory': 'Tworzy katalog',
            'delete_file': 'Usuwa plik',
            'check_syntax': 'Sprawdza składnię kodu',
            'search_in_files': 'Wyszukuje w plikach'
        }

        await sio.emit('available_tools', tools_info, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd pobierania narzędzi: {str(e)}'}, room=sid)

@sio.event
async def get_file_structure(sid, data):
    """Zwraca strukturę plików z pominięciem .gitignore"""
    try:
        from pathlib import Path
        import fnmatch

        root_path = Path(data.get('path', '.'))
        gitignore_patterns = []

        # Wczytaj .gitignore jeśli istnieje
        gitignore_file = Path('.gitignore')
        if gitignore_file.exists():
            with open(gitignore_file, 'r', encoding='utf-8') as f:
                gitignore_patterns = [line.strip() for line in f.readlines() 
                                    if line.strip() and not line.startswith('#')]

        # Dodaj podstawowe wzorce do ignorowania
        default_ignore = ['.git/', '__pycache__/', '*.pyc', '.vscode/', 'node_modules/', '.config/']
        gitignore_patterns.extend(default_ignore)

        def should_ignore(path_str):
            for pattern in gitignore_patterns:
                if fnmatch.fnmatch(path_str, pattern) or fnmatch.fnmatch(path_str, pattern.rstrip('/')):
                    return True
                # Sprawdź czy ścieżka zawiera ignorowany katalog
                if '/' in pattern and pattern.endswith('/'):
                    if f"/{pattern.rstrip('/')}/" in f"/{path_str}/":
                        return True
            return False

        def get_file_structure_recursive(path):
            items = []

            if not path.exists() or should_ignore(str(path.relative_to('.'))):
                return items

            try:
                for item in sorted(path.iterdir()):
                    relative_path = item.relative_to('.')

                    # Pomiń pliki/foldery z .gitignore
                    if should_ignore(str(relative_path)):
                        continue

                    item_data = {
                        'name': item.name,
                        'type': 'folder' if item.is_dir() else 'file',
                        'path': str(relative_path),
                        'size': item.stat().st_size if item.is_file() else 0
                    }

                    if item.is_dir():
                        item_data['children'] = get_file_structure_recursive(item)

                    items.append(item_data)

            except PermissionError:
                pass  # Pomiń katalogi bez dostępu

            return items

        file_structure = {
            'name': 'LuxOS',
            'type': 'folder', 
            'path': '.',
            'children': get_file_structure_recursive(Path('.'))
        }

        await sio.emit('file_structure', file_structure, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd pobierania struktury plików: {str(e)}'}, room=sid)

@sio.event
async def call_openai_with_functions(sid, data):
    """Wywołuje OpenAI z dostępnymi funkcjami"""
    try:
        if not openai_function_caller:
            await sio.emit('error', {'message': 'OpenAI Function Caller nie jest skonfigurowany'}, room=sid)
            return

        prompt = data.get('prompt', '')
        context = data.get('context', {})

        if not prompt:
            await sio.emit('error', {'message': 'Brak prompt dla OpenAI'}, room=sid)
            return

        result = await openai_function_caller.call_with_functions(prompt, context)

        await sio.emit('openai_function_result', result, room=sid)

        # Aktualizuj graf jeśli funkcje były wykonywane
        if result.get('tool_calls'):
            await broadcast_graph_update()

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd wywołania OpenAI: {str(e)}'}, room=sid)

@sio.event
async def register_function_for_openai(sid, data):
    """Rejestruje funkcję dla OpenAI"""
    try:
        if not openai_function_caller:
            await sio.emit('error', {'message': 'OpenAI Function Caller nie jest skonfigurowany'}, room=sid)
            return

        soul = data.get('soul')
        if not soul:
            await sio.emit('error', {'message': 'Brak soul bytu funkcyjnego'}, room=sid)
            return

        # Załaduj byt
        being = await BaseBeing.load(soul)
        if not being or being.genesis.get('type') != 'function':
            await sio.emit('error', {'message': 'Byt nie jest funkcją'}, room=sid)
            return

        # Konwertuj na FunctionBeing
        from app.beings.function_being import FunctionBeing
        function_being = FunctionBeing(
            soul=being.soul,
            genesis=being.genesis,
            attributes=being.attributes,
            memories=being.memories,
            self_awareness=being.self_awareness,
            created_at=being.created_at
        )

        success = await openai_function_caller.register_function_being(function_being)

        if success:
            await sio.emit('function_registered_for_openai', {
                'soul': soul,
                'name': being.genesis.get('name', 'unknown'),
                'message': 'Funkcja zarejestrowana dla OpenAI'
            }, room=sid)
        else:
            await sio.emit('error', {'message': 'Nie udało się zarejestrować funkcji'}, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd rejestracji funkcji: {str(e)}'}, room=sid)

@sio.event
async def get_openai_functions(sid, data):
    """Zwraca listę funkcji dostępnych dla OpenAI"""
    try:
        if not openai_function_caller:
            await sio.emit('openai_functions_list', {'functions': []}, room=sid)
            return

        functions = openai_function_caller.get_available_functions()
        await sio.emit('openai_functions_list', {'functions': functions}, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd pobierania funkcji: {str(e)}'}, room=sid)

@sio.event
async def read_file(sid, data):
    """Odczytuje zawartość pliku"""
    try:
        file_path = data.get('file_path', '')

        if not file_path:
            await sio.emit('error', {'message': 'Brak ścieżki pliku'}, room=sid)
            return

        from pathlib import Path

        path = Path(file_path)

        if not path.exists():
            await sio.emit('error', {'message': f'Plik nie istnieje: {file_path}'}, room=sid)
            return

        if not path.is_file():
            await sio.emit('error', {'message': f'Ścieżka nie jest plikiem: {file_path}'}, room=sid)
            return

        # Sprawdź czy plik nie jest zbyt duży (max 1MB)
        if path.stat().st_size > 1024 * 1024:
            await sio.emit('error', {'message': f'Plik zbyt duży: {file_path}'}, room=sid)
            return

        try:
            # Spróbuj odczytać jako tekst
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Jeśli nie można jako tekst, oznacz jako binarny
            content = f"[Plik binarny: {path.name}]"

        file_data = {
            'file_path': file_path,
            'content': content,
            'size': path.stat().st_size,
            'extension': path.suffix
        }

        await sio.emit('file_content', file_data, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd odczytu pliku: {str(e)}'}, room=sid)

@sio.event
async def update_being(sid, data):
    """Aktualizuje istniejący byt"""
    try:
        soul = data.get('soul')
        if not soul:
            await sio.emit('error', {'message': 'Brak soul bytu do aktualizacji'}, room=sid)
            return

        # Przygotuj dane do aktualizacji
        genesis = data.get('genesis', {})
        attributes = data.get('attributes', {})
        self_awareness = data.get('self_awareness', {})

        query = """
        UPDATE base_beings SET
            genesis = $2,
            attributes = $3,
            self_awareness = $4
        WHERE soul = $1
        """

        result = await db_pool.execute(
            query, 
            soul, 
            json.dumps(genesis), 
            json.dumps(attributes), 
            json.dumps(self_awareness)
        )

        if result == 'UPDATE 0':
            await sio.emit('error', {'message': 'Byt nie znaleziony'}, room=sid)
            return

        # Wyślij aktualizację do wszystkich klientów
        await broadcast_graph_update()
        await sio.emit('being_updated', {
            'soul': soul,
            'message': 'Byt został zaktualizowany pomyślnie'
        }, room=sid)

    except Exception as e:
        logger.error(f"Błąd podczas aktualizacji bytu: {e}")
        await sio.emit('error', {'message': f'Błąd aktualizacji: {str(e)}'}, room=sid)

@sio.event
async def delete_being(sid, data):
    """Usuwa byt z systemu"""
    soul = data.get('soul')
    task_id = data.get('taskId')

    if not soul:
        response = {
            'success': False,
            'error': 'Brak soul bytu do usunięcia',
            'taskId': task_id
        }
        await sio.emit('task_response', response, room=sid)
        return

    try:
        print(f"🗑️ Usuwam byt: {soul} (Task ID: {task_id})")

        # BLOKUJ usywanie agenta Lux
        lux_soul = '00000000-0000-0000-0000-000000000001'
        if soul == lux_soul:
            response = {
                'success': False,
                'error': 'BŁĄD: Nie można usunąć agenta Lux! To główny agent świadomości systemu.',
                'taskId': task_id
            }
            await sio.emit('task_response', response, room=sid)
            return

        db_pool = await get_db_pool()

        if hasattr(db_pool, 'acquire'):
            # PostgreSQL - usuń tylko byt, zostaw relacje jako historię
            async with db_pool.acquire() as conn:
                # Sprawdź czy byt istnieje
                check_result = await conn.fetchrow("""
                    SELECT soul FROM base_beings WHERE soul = $1
                """, soul)

                if not check_result:
                    response = {
                        'success': False,
                        'error': 'Byt nie znaleziony w bazie danych',
                        'taskId': task_id
                    }
                    await sio.emit('task_response', response, room=sid)
                    return

                # Usuń tylko byt - relacje zostają jako historia
                result = await conn.execute("""
                    DELETE FROM base_beings WHERE soul = $1
                """, soul)

                print(f"✅ Usunięto byt z bazy: {result}")
                print(f"📚 Relacje zostały zachowane jako historia")
        else:
            # SQLite fallback - usuń tylko byt, zostaw relacje
            cursor = await db_pool.execute("""
                SELECT soul FROM base_beings WHERE soul = ?
            """, (soul,))

            if not await cursor.fetchone():
                response = {
                    'success': False,
                    'error': 'Byt nie znaleziony w bazie danych',
                    'taskId': task_id
                }
                await sio.emit('task_response', response, room=sid)
                return

            # Usuń tylko byt - relacje zostają jako historia
            cursor = await db_pool.execute("""
                DELETE FROM base_beings WHERE soul = ?
            """, (soul,))

            await db_pool.commit()
            print(f"✅ Usunięto byt z SQLite")
            print(f"📚 Relacje zostały zachowane jako historia")

        # Usuń z systemu genetycznego jeśli istnieje
        if hasattr(genetic_system, 'beings') and soul in genetic_system.beings:
            del genetic_system.beings[soul]
            print(f"🧬 Usunięto byt z systemu genetycznego")

        # Wyślij potwierdzenie sukcesu do klienta
        response = {
            'success': True,
            'soul': soul,
            'message': 'Byt został usunięty pomyślnie',
            'taskId': task_id,
            'deleted_soul': soul  # Dodaj explicit info o usuniętym bycie
        }
        await sio.emit('task_response', response, room=sid)

        # Wyślij powiadomienie o usunięciu
        try:
            await sio.emit('being_removed', {
                'soul': soul,
                'message': f'Byt {soul} został usunięty'
            })
            print(f"✅ Wysłano powiadomienie o usunięciu: {soul}")

        except Exception as e:
            print(f"❌ Błąd wysyłania powiadomienia o usunięciu: {e}")

    except Exception as e:
        print(f"❌ Błąd podczas usuwania bytu {soul}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

        response = {
            'success': False,
            'error': f'Błąd usuwania: {str(e)}',
            'taskId': task_id
        }
        await sio.emit('task_response', response, room=sid)

@sio.event
async def delete_relationship(sid, data):
    global db_pool
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

async def analyze_lux_communication(message: str, context: dict) -> dict:
    """Analizuje komunikację z Lux i określa czy powinna użyć narzędzi lub funkcji"""
    # Najpierw spróbuj OpenAI Function Calling jeśli dostępne
    if openai_function_caller and openai_function_caller.get_available_functions():
        try:
            result = await openai_function_caller.call_with_functions(message, context)

            response = {
                'message': result.get('final_response') or result.get('response') or 'Przeanalizowałem twoją prośbę.',
                'openai_response': True,
                'function_calls': result.get('tool_calls', []),
                'actions': []
            }

            # Jeśli były wywołania funkcji, dodaj informacje
            if result.get('tool_calls'):
                response['message'] += f"\n\nWykonałem {len(result['tool_calls'])} funkcji z bytów astralnych."

            return response

        except Exception as e:
            print(f"Błąd OpenAI Function Calling: {e}")
            # Fallback do starego systemu

    # Fallback - użyj starego parsera narzędzi
    from tool_parser import analyze_message_for_tools

    parser_result = analyze_message_for_tools(message)

    response = {
        'message': 'Analizuję twoją prośbę...',
        'suggested_tools': parser_result['suggested_tools'],
        'actions': [],
        'openai_response': False
    }

    # Jeśli parser nie wykrył narzędzi z wystarczającą pewnością, dodaj GPT jako fallback
    if not response['suggested_tools'] or parser_result['highest_confidence'] < 0.5:
        response['suggested_tools'].append({
            'tool': 'ask_gpt',
            'reason': 'Przekażę twoją prośbę do GPT dla lepszej analizy',
            'parameters': {'prompt': f"Użytkownik napisał: '{message}'. Jak mogę pomóc?"},
            'confidence': 0.4
        })

    # Aktualizuj wiadomość na podstawie wyników parsera
    if parser_result['total_detected'] > 0:
        highest_confidence = parser_result['highest_confidence']
        confidence_text = "wysoką" if highest_confidence > 0.8 else "średnią" if highest_confidence > 0.5 else "niską"
        response['message'] = f"Wykryłem {parser_result['total_detected']} narzędzi z {confidence_text} pewnością."
    else:
        response['message'] = "Nie wykryłem konkretnych narzędzi, przekażę zapytanie do GPT."

    return response

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
                        'created_by': 'intention',
                    }}})


async def make_delegation_decision(message: str, task_analysis: dict, context: dict) -> dict:
    """Podejmuje decyzję o delegacji zadania między frontend a backend"""

    decision = {
        'execute_on': 'backend',  # backend, frontend, hybrid
        'reason': '',
        'frontend_actions': [],
        'backend_actions': [],
        'requires_long_term_execution': False
    }

    # Analiza złożoności zadania
    if task_analysis.get('is_heavy_task') or task_analysis.get('requires_file_operations'):
        decision['execute_on'] = 'backend'
        decision['reason'] = 'Zadanie wymaga ciężkich operacji lub dostępu do plików'
        decision['backend_actions'] = ['file_operations', 'heavy_computation']

    elif task_analysis.get('requires_database'):
        decision['execute_on'] = 'backend'
        decision['reason'] = 'Zadanie wymaga operacji na bazie danych'
        decision['backend_actions'] = ['database_operations']

    elif task_analysis.get('is_long_term'):
        decision['execute_on'] = 'backend'
        decision['reason'] = 'Zadanie długoterminowe - backend zarządza trwałością'
        decision['backend_actions'] = ['long_term_scheduling', 'persistent_execution']
        decision['requires_long_term_execution'] = True

    elif task_analysis.get('is_frontend_task'):
        decision['execute_on'] = 'hybrid'
        decision['reason'] = 'Zadanie wizualne - frontend z wsparciem backendu'
        decision['frontend_actions'] = ['ui_updates', 'visualization']
        decision['backend_actions'] = ['data_preparation']

    # Sprawdź możliwości frontendu
    frontend_caps = context.get('frontend_capabilities', {})
    if not frontend_caps.get('webgl_rendering') and 'wizualizuj' in message:
        decision['execute_on'] = 'backend'
        decision['reason'] = 'Frontend nie obsługuje WebGL - backend przygotuje dane'

    return decision

async def execute_backend_task(message: str, context: dict, delegation: dict) -> dict:
    """Wykonuje zadanie na backendzie z wykorzystaniem wszystkich możliwości Lux"""

    response = {
        'message': 'Lux wykonuje zadanie na backendzie...',
        'task_status': 'backend_processing',
        'actions': [],
        'results': {},
        'delegation_info': delegation
    }

    try:
        # Użyj OpenAI Function Calling jeśli dostępne
        if openai_function_caller and openai_function_caller.get_available_functions():
            ai_result = await openai_function_caller.call_with_functions(message, context)
            response['ai_analysis'] = ai_result
            response['message'] = ai_result.get('final_response', 'Analiza AI zakończona.')

            if ai_result.get('tool_calls'):
                response['actions'].extend(ai_result['tool_calls'])

        # Operacje na plikach
        if 'file_operations' in delegation['backend_actions']:
            response['message'] += '\n📁 Analizuję pliki...'

        # Operacje na bazie danych
        if 'database_operations' in delegation['backend_actions']:
            response['message'] += '\n💾 Przetwarzam dane z bazy...'
            # Dodaj statystyki bazy
            response['results']['database_stats'] = {
                'beings_count': len(await BaseBeing.get_all()),
                'relationships_count': len(await Relationship.get_all())
            }

        # Zadania długoterminowe
        if delegation['requires_long_term_execution']:
            response['message'] += '\n⏰ Konfiguruję zadanie długoterminowe...'
            await schedule_long_term_task(message, context)
            response['results']['scheduled_task'] = True

        # Użyj LuxTools dla operacji systemowych
        if any(keyword in message for keyword in ['plik', 'kod', 'test', 'analiz']):
            response['message'] += '\n🛠️ Używam narzędzi systemowych...'

    except Exception as e:
        response['message'] = f'Błąd wykonania zadania na backendzie: {str(e)}'
        response['task_status'] = 'backend_error'

    return response

async def execute_hybrid_task(message: str, context: dict, delegation: dict) -> dict:
    """Wykonuje zadanie hybrydowe - koordynacja między frontend a backend"""

    response = {
        'message': 'Lux koordynuje zadanie między frontendem a backendem...',
        'task_status': 'hybrid_processing',
        'frontend_instructions': [],
        'backend_results': {},
        'delegation_info': delegation
    }

    # Przygotuj dane na backendzie
    if 'data_preparation' in delegation['backend_actions']:
        beings = await BaseBeing.get_all(limit=50)  # Ograniczenie dla frontendu
        response['backend_results']['prepared_data'] = {
            'beings_summary': [{'soul': b.soul, 'type': b.genesis.get('type')} for b in beings[:10]]
        }

    # Instrukcje dla frontendu
    if 'ui_updates' in delegation['frontend_actions']:
        response['frontend_instructions'].append({
            'action': 'update_visualization',
            'data': response['backend_results']['prepared_data']
        })

    if 'visualization' in delegation['frontend_actions']:
        response['frontend_instructions'].append({
            'action': 'create_visualization',
            'type': 'graph_update',
            'animate': True
        })

    response['message'] = 'Dane przygotowane. Frontend może przejąć wizualizację.'

    return response

async def schedule_long_term_task(message: str, context: dict):
    """Harmonogramuje zadanie długoterminowe w systemie genetycznym"""

    # Utwórz byt zadania długoterminowego
    long_term_task = await BeingFactory.create_being(
        being_type='task',
        genesis={
            'type': 'task',
            'name': f'LongTerm_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            'description': f'Zadanie długoterminowe: {message}',
            'created_by': 'lux_delegation_system'
        },
        attributes={
            'task_type': 'long_term',
            'original_message': message,
            'execution_context': context,
            'schedule': {
                'created_at': datetime.now().isoformat(),
                'next_execution': datetime.now().isoformat(),
                'interval': 'on_demand',
                'max_executions': 1
            }
        },
        memories=[{
            'type': 'scheduling',
            'data': f'Scheduled by Lux delegation system',
            'timestamp': datetime.now().isoformat()
        }],
        tags=['task', 'long_term', 'scheduled', 'lux_managed'],
        energy_level=100
    )

    print(f"📅 Zaplanowano zadanie długoterminowe: {long_term_task.soul}")
    return long_term_task


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
    global db_pool
    try:
        # Pobierz dane wszechświata z systemu genetycznego
        beings_data = []
        relationships_data = []

        # Pobierz wszystkie byty
        all_beings = await BaseBeing.get_all()
        for being in all_beings:
            try:
                being_data = {
                    'soul': being.soul,
                    'soul_uid': being.soul,
                    'genesis': being.genesis if isinstance(being.genesis, dict) else json.loads(being.genesis),
                    'attributes': being.attributes if isinstance(being.attributes, dict) else json.loads(being.attributes),
                    'memories': being.memories if isinstance(being.memories, list) else json.loads(being.memories),
                    'self_awareness': being.self_awareness if isinstance(being.self_awareness, dict) else json.loads(being.self_awareness),
                    'created_at': being.created_at.isoformat() if being.created_at else None
                }
                beings_data.append(being_data)
            except Exception as e:
                print(f"❌ Błąd serializacji bytu {being.soul}: {e}")

        # Pobierz wszystkie relacje
        all_relationships = await Relationship.get_all()
        print(f"🔗 Znaleziono {len(all_relationships)} relacji w bazie")

        for rel in all_relationships:
            try:
                # Bezpieczne parsowanie genesis
                genesis_data = rel.genesis
                if isinstance(rel.genesis, str):
                    try:
                        genesis_data = json.loads(rel.genesis)
                    except json.JSONDecodeError:
                        print(f"⚠️ Błąd parsowania genesis relacji {rel.id}")
                        genesis_data = {'type': 'unknown'}

                # Bezpieczne parsowanie attributes
                attributes_data = rel.attributes
                if isinstance(rel.attributes, str):
                    try:
                        attributes_data = json.loads(rel.attributes)
                    except json.JSONDecodeError:
                        print(f"⚠️ Błąd parsowania attributes relacji {rel.id}")
                        attributes_data = {}

                rel_data = {
                    'id': rel.id,
                    'source_soul': rel.source_soul,
                    'target_soul': rel.target_soul,
                    'genesis': genesis_data,
                    'attributes': attributes_data,
                    'created_at': rel.created_at.isoformat() if rel.created_at else None
                }
                relationships_data.append(rel_data)
                print(f"🔗 Relacja: {rel.source_soul} → {rel.target_soul} ({genesis_data.get('type', 'unknown')})")

            except Exception as e:
                print(f"❌ Błąd serializacji relacji {rel.id}: {e}")

        print(f"📊 Wysyłam do frontendu: {len(beings_data)} bytów, {len(relationships_data)} relacji")

        data = {
            'nodes': beings_data,
            'relationships': relationships_data,
            'links': relationships_data  # Dodaj również jako 'links' dla kompatybilności
        }

        await sio.emit('graph_data', data)
    except Exception as e:
        print(f"Błąd w send_graph_data: {e}")
        await sio.emit('error', {'message': f'Błąd ładowania danych: {str(e)}'}, room=sid)

async def broadcast_graph_update():
    """Rozgłasza aktualizację grafu do wszystkich klientów"""
    global db_pool
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
    global db_pool
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
    global db_pool
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
    # Próba połączenia z PostgreSQL, fallback na SQLite
    try:
        pool = await asyncpg.create_pool(
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
        set_db_pool(pool)
        print("Połączono z PostgreSQL")
        await setup_postgresql_tables()
    except Exception as e:
        print(f"Nie udało się połączyć z PostgreSQL: {e}")
        print("Używam SQLite jako fallback")
        pool = await aiosqlite.connect('luxos.db')
        set_db_pool(pool)
        await setup_sqlite_tables()

    # Auto-rejestruj funkcje w OpenAI Function Caller
    if openai_function_caller:
        registered_count = await openai_function_caller.auto_register_function_beings()
        print(f"Zarejestrowano {registered_count} funkcji w OpenAI Function Caller")

async def setup_postgresql_tables():
    """Tworzy tabele w PostgreSQL"""
    db_pool = await get_db_pool()
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
    db_pool = await get_db_pool()
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



async def main():
    print("🚀 Uruchamianie serwera LuxOS...")

    # Najpierw inicjalizuj bazę danych
    await init_database()

    # Potem inicjalizuj system genetyczny
    await genetic_system.initialize()

    # Uruchom serwer
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

@sio.event
async def get_beings(sid):
    """Pobierz wszystkie byty"""
    try:
        beings = await BaseBeing.get_all()
        relationships = await Relationship.get_all()

        beings_data = []
        for being in beings:
            beings_data.append({
                'soul': being.soul,
                'genesis': being.genesis,
                'attributes': being.attributes,
                'memories': being.memories,
                'self_awareness': being.self_awareness,
                'created_at': being.created_at.isoformat() if being.created_at else None
            })

        relationships_data = []
        for rel in relationships:
            relationships_data.append({
                'id': rel.id,
                'source_soul': rel.source_soul,
                'target_soul': rel.target_soul,
                'genesis': rel.genesis,
                'attributes': rel.attributes,
                'created_at': rel.created_at.isoformat() if rel.created_at else None
            })

        # Dodaj status systemu genetycznego
        genetic_status = await genetic_system.get_universe_status()

        await sio.emit('beings_data', {
            'beings': beings_data,
            'relationships': relationships_data,
            'genetic_status': genetic_status
        }, room=sid)

    except Exception as e:
        print(f"Błąd pobierania bytów: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def get_lux_status(sid):
    """Pobierz status agenta Lux"""
    try:
        lux_status = await genetic_system.get_lux_status()
        await sio.emit('lux_status', lux_status, room=sid)

        if lux_status.get('exists'):
            print(f"✨ Agent Lux aktywny: {lux_status}")
        else:
            print("❌ Agent Lux nie został znaleziony")

    except Exception as e:
        print(f"Błąd pobierania statusu Lux: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def initialize_lux_agent(sid):
    """Wymusza inicjalizację agenta Lux"""
    try:
        await genetic_system.create_initial_beings()
        lux_status = await genetic_system.get_lux_status()

        await sio.emit('lux_initialized', lux_status, room=sid)
        await broadcast_graph_update()

        print(f"🧬 Agent Lux zainicjalizowany: {lux_status}")

    except Exception as e:
        print(f"Błąd inicjalizacji Lux: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event 
async def genetic_evolution(sid, data):
    """Endpoint do ewolucji bytów"""
    try:
        being_soul = data.get('being_soul')
        gene_path = data.get('gene_path')

        if not being_soul or not gene_path:
            await sio.emit('error', {
                'message': 'Brak wymaganych parametrów: being_soul, gene_path'
            }, room=sid)
            return

        await genetic_system.evolve_being(being_soul, gene_path)

        await sio.emit('genetic_evolution_complete', {
            'being_soul': being_soul,
            'gene_path': gene_path,
            'success': True
        }, room=sid)

        await broadcast_graph_update()

    except Exception as e:
        print(f"Błąd ewolucji genetycznej: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def load_gene_from_file(sid, data):
    """Endpoint do ładowania/aktualizacji genu z pliku"""
    try:
        file_path = data.get('file_path')

        if not file_path:
            await sio.emit('error', {
                'message': 'Brak wymaganego parametru: file_path'
            }, room=sid)
            return

        # Załaduj gen z pliku
        gene_being = await genetic_system.load_gene_from_file_path(file_path)

        if gene_being:
            await sio.emit('gene_loaded', {
                'file_path': file_path,
                'gene_soul': gene_being.soul,
                'gene_hash': gene_being.attributes.get('gene_hash'),
                'success': True,
                'evolution_detected': any(m.get('type') == 'code_evolution' 
                                        for m in gene_being.memories[-3:])  # Sprawdź ostatnie 3 wpisy
            }, room=sid)
        else:
            await sio.emit('error', {
                'message': f'Nie udało się załadować genu z {file_path}'
            }, room=sid)

        await broadcast_graph_update()

    except Exception as e:
        print(f"Błąd ładowania genu: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def create_genetic_thought(sid, data):
    """Endpoint do tworzenia myśli/relacji subiektywnych"""
    try:
        source_soul = data.get('source_soul')
        target_soul = data.get('target_soul') 
        thought = data.get('thought')

        if not all([source_soul, target_soul, thought]):
            await sio.emit('error', {
                'message': 'Brak wymaganych parametrów: source_soul, target_soul, thought'
            }, room=sid)
            return

        await genetic_system.think_about_relationship(source_soul, target_soul, thought)

        await sio.emit('genetic_thought_created', {
            'source_soul': source_soul,
            'target_soul': target_soul,
            'thought': thought,
            'success': True
        }, room=sid)

        await broadcast_graph_update()

    except Exception as e:
        print(f"Błąd tworzenia myśli: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def clean_duplicate_genes(sid, data):
    """Endpoint do czyszczenia duplikatów genów"""
    try:
        removed_count = await genetic_system.clean_duplicate_genes()

        await sio.emit('duplicate_genes_cleaned', {
            'removed_count': removed_count,
            'message': f'Usunięto {removed_count} duplikatów genów'
        }, room=sid)

        await broadcast_graph_update()

    except Exception as e:
        print(f"Błąd czyszczenia duplikatów genów: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

if __name__ == '__main__':
    asyncio.run(main())