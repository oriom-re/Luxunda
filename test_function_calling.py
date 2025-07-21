
import asyncio
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from app.ai.function_calling import OpenAIFunctionCaller
from app.beings.function_being import FunctionBeing
from app.beings.base import BaseBeing
from app.database import set_db_pool
import aiosqlite
from datetime import datetime
import uuid

class TestOpenAIFunctionCalling:
    """Test suite dla systemu OpenAI Function Calling"""
    
    @pytest.fixture
    async def setup_db(self):
        """Przygotuj bazę danych SQLite do testów"""
        db = await aiosqlite.connect(':memory:')
        set_db_pool(db)
        
        # Utwórz tabele
        await db.execute("""
            CREATE TABLE base_beings (
                soul TEXT PRIMARY KEY,
                genesis TEXT NOT NULL,
                attributes TEXT NOT NULL,
                memories TEXT NOT NULL,
                self_awareness TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()
        return db
    
    @pytest.fixture
    def mock_openai_client(self):
        """Mock klienta OpenAI"""
        with patch('openai.OpenAI') as mock_client:
            yield mock_client
    
    @pytest.fixture
    async def sample_function_being(self, setup_db):
        """Przygotuj przykładowy byt funkcyjny"""
        function_being = FunctionBeing(
            soul=str(uuid.uuid4()),
            genesis={
                'name': 'test_function',
                'type': 'function',
                'source': '''def test_function(x: int, y: int) -> int:
    """Dodaje dwie liczby"""
    return x + y''',
                'description': 'Funkcja testowa dodająca dwie liczby',
                'signature': 'test_function(x: int, y: int) -> int'
            },
            attributes={'test': True},
            memories=[],
            self_awareness={'confidence': 0.9, 'trust_level': 0.8},
            created_at=datetime.now()
        )
        await function_being.save()
        return function_being
    
    @pytest.mark.asyncio
    async def test_register_function_being(self, sample_function_being, mock_openai_client):
        """Test rejestracji bytu funkcyjnego"""
        caller = OpenAIFunctionCaller("test_api_key")
        
        success = await caller.register_function_being(sample_function_being)
        
        assert success is True
        assert 'test_function' in caller.available_functions
        
        func_info = caller.available_functions['test_function']
        assert func_info['soul'] == sample_function_being.soul
        assert func_info['being'] == sample_function_being
        assert func_info['schema']['function']['name'] == 'test_function'
        assert func_info['schema']['function']['description'] == 'Funkcja testowa dodająca dwie liczby'
    
    @pytest.mark.asyncio
    async def test_extract_function_parameters(self, mock_openai_client):
        """Test ekstraktowania parametrów funkcji"""
        caller = OpenAIFunctionCaller("test_api_key")
        
        source = '''def calculate_sum(a: int, b: int, message: str) -> int:
    """Oblicza sumę dwóch liczb"""
    print(message)
    return a + b'''
        
        parameters = caller._extract_function_parameters(source, 'calculate_sum')
        
        assert parameters['type'] == 'object'
        assert 'a' in parameters['properties']
        assert 'b' in parameters['properties']
        assert 'message' in parameters['properties']
        assert len(parameters['required']) == 3
        assert all(param in parameters['required'] for param in ['a', 'b', 'message'])
    
    @pytest.mark.asyncio
    async def test_call_with_functions_no_tools(self, mock_openai_client):
        """Test wywołania OpenAI bez dostępnych funkcji"""
        # Przygotuj mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Testowa odpowiedź"
        mock_response.choices[0].message.tool_calls = None
        
        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.return_value = mock_response
        mock_openai_client.return_value = mock_client_instance
        
        caller = OpenAIFunctionCaller("test_api_key")
        
        result = await caller.call_with_functions("Test prompt")
        
        assert result['response'] == "Testowa odpowiedź"
        assert result['tool_calls'] == []
        assert result['function_results'] == []
        assert 'error' not in result
    
    @pytest.mark.asyncio
    async def test_call_with_functions_with_tool_call(self, sample_function_being, mock_openai_client):
        """Test wywołania OpenAI z wykorzystaniem funkcji z bytu"""
        # Przygotuj mock response dla pierwszego wywołania
        mock_tool_call = Mock()
        mock_tool_call.function.name = 'test_function'
        mock_tool_call.function.arguments = '{"x": 5, "y": 3}'
        mock_tool_call.id = 'call_123'
        
        mock_first_response = Mock()
        mock_first_response.choices = [Mock()]
        mock_first_response.choices[0].message.content = None
        mock_first_response.choices[0].message.tool_calls = [mock_tool_call]
        
        # Przygotuj mock response dla drugiego wywołania (z wynikami funkcji)
        mock_final_response = Mock()
        mock_final_response.choices = [Mock()]
        mock_final_response.choices[0].message.content = "Wynik: 8"
        
        mock_client_instance = Mock()
        mock_client_instance.chat.completions.create.side_effect = [
            mock_first_response,
            mock_final_response
        ]
        mock_openai_client.return_value = mock_client_instance
        
        # Mock SafeCodeExecutor
        with patch('app.safety.executor.SafeCodeExecutor.execute_function') as mock_executor:
            mock_executor.return_value = AsyncMock(return_value={
                'success': True,
                'result': 8,
                'output': 'Function executed successfully'
            })()
            
            caller = OpenAIFunctionCaller("test_api_key")
            await caller.register_function_being(sample_function_being)
            
            result = await caller.call_with_functions("Dodaj 5 i 3")
            
            assert result['final_response'] == "Wynik: 8"
            assert len(result['tool_calls']) == 1
            assert result['tool_calls'][0]['function'] == 'test_function'
            assert result['tool_calls'][0]['arguments'] == {'x': 5, 'y': 3}
            assert result['tool_calls'][0]['result']['success'] is True
            assert result['tool_calls'][0]['result']['result'] == 8
    
    @pytest.mark.asyncio
    async def test_execute_function_success(self, sample_function_being):
        """Test pomyślnego wykonania funkcji"""
        caller = OpenAIFunctionCaller("test_api_key")
        await caller.register_function_being(sample_function_being)
        
        with patch('app.safety.executor.SafeCodeExecutor.execute_function') as mock_executor:
            mock_executor.return_value = AsyncMock(return_value={
                'success': True,
                'result': 15,
                'output': 'Function executed'
            })()
            
            result = await caller._execute_function('test_function', {'x': 10, 'y': 5})
            
            assert result['success'] is True
            assert result['result'] == 15
            assert result['function_name'] == 'test_function'
            
            # Sprawdź czy pamięć została zapisana
            updated_being = await BaseBeing.load(sample_function_being.soul)
            assert len(updated_being.memories) == 1
            assert updated_being.memories[0]['type'] == 'openai_execution'
            assert updated_being.memories[0]['success'] is True
    
    @pytest.mark.asyncio
    async def test_execute_function_not_found(self):
        """Test wykonania nieistniejącej funkcji"""
        caller = OpenAIFunctionCaller("test_api_key")
        
        result = await caller._execute_function('nonexistent_function', {})
        
        assert result['error'] == "Funkcja nonexistent_function nie jest dostępna"
    
    @pytest.mark.asyncio
    async def test_auto_register_function_beings(self, setup_db):
        """Test automatycznej rejestracji wszystkich bytów funkcyjnych"""
        # Utwórz kilka bytów funkcyjnych w bazie
        function_beings = []
        for i in range(3):
            being = FunctionBeing(
                soul=str(uuid.uuid4()),
                genesis={
                    'name': f'auto_function_{i}',
                    'type': 'function',
                    'source': f'def auto_function_{i}(): return {i}',
                    'description': f'Auto function {i}'
                },
                attributes={},
                memories=[],
                self_awareness={},
                created_at=datetime.now()
            )
            await being.save()
            function_beings.append(being)
        
        # Utwórz też byt nie-funkcyjny
        non_function_being = BaseBeing(
            soul=str(uuid.uuid4()),
            genesis={'name': 'not_function', 'type': 'class'},
            attributes={},
            memories=[],
            self_awareness={},
            created_at=datetime.now()
        )
        await non_function_being.save()
        
        caller = OpenAIFunctionCaller("test_api_key")
        
        registered_count = await caller.auto_register_function_beings()
        
        assert registered_count == 3
        assert len(caller.get_available_functions()) == 3
        assert 'auto_function_0' in caller.available_functions
        assert 'auto_function_1' in caller.available_functions
        assert 'auto_function_2' in caller.available_functions
        assert 'not_function' not in caller.available_functions
    
    @pytest.mark.asyncio
    async def test_get_available_functions(self, sample_function_being):
        """Test pobierania listy dostępnych funkcji"""
        caller = OpenAIFunctionCaller("test_api_key")
        
        # Początkowo pusta lista
        assert caller.get_available_functions() == []
        
        # Po rejestracji funkcji
        await caller.register_function_being(sample_function_being)
        functions = caller.get_available_functions()
        
        assert len(functions) == 1
        assert 'test_function' in functions
    
    def test_error_handling_invalid_api_key(self):
        """Test obsługi błędów przy nieprawidłowym kluczu API"""
        caller = OpenAIFunctionCaller("invalid_key")
        
        # Sprawdź czy obiekt został utworzony
        assert caller.client is not None
        assert caller.available_functions == {}


# Funkcja uruchamiająca testy
async def run_practical_test():
    """Praktyczny test funkcjonalności"""
    print("🔬 Rozpoczynam praktyczny test OpenAI Function Calling...")
    
    # Test 1: Tworzenie prostej funkcji matematycznej
    print("\n1️⃣ Test tworzenia bytu funkcyjnego...")
    
    # Przygotuj bazę danych
    db = await aiosqlite.connect(':memory:')
    set_db_pool(db)
    
    await db.execute("""
        CREATE TABLE base_beings (
            soul TEXT PRIMARY KEY,
            genesis TEXT NOT NULL,
            attributes TEXT NOT NULL,
            memories TEXT NOT NULL,
            self_awareness TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    await db.commit()
    
    # Utwórz byt funkcyjny
    math_function = FunctionBeing(
        soul=str(uuid.uuid4()),
        genesis={
            'name': 'multiply',
            'type': 'function',
            'source': '''def multiply(a: int, b: int) -> int:
    """Mnoży dwie liczby"""
    result = a * b
    print(f"Mnożę {a} * {b} = {result}")
    return result''',
            'description': 'Mnoży dwie liczby całkowite',
            'signature': 'multiply(a: int, b: int) -> int'
        },
        attributes={'category': 'math', 'complexity': 'simple'},
        memories=[],
        self_awareness={'confidence': 0.95, 'trust_level': 0.9},
        created_at=datetime.now()
    )
    
    await math_function.save()
    print(f"✅ Utworzono byt funkcyjny: {math_function.genesis['name']}")
    
    # Test 2: Rejestracja w OpenAI Function Caller
    print("\n2️⃣ Test rejestracji funkcji...")
    
    # Użyj prawdziwego klucza API jeśli dostępny
    api_key = os.getenv('OPENAI_API_KEY', 'test_key')
    caller = OpenAIFunctionCaller(api_key)
    
    success = await caller.register_function_being(math_function)
    print(f"✅ Rejestracja: {'Sukces' if success else 'Błąd'}")
    
    if success:
        print(f"📋 Dostępne funkcje: {caller.get_available_functions()}")
        
        # Wyświetl schemat funkcji
        schema = caller.available_functions['multiply']['schema']
        print(f"🔧 Schemat funkcji:")
        print(f"   Nazwa: {schema['function']['name']}")
        print(f"   Opis: {schema['function']['description']}")
        print(f"   Parametry: {list(schema['function']['parameters']['properties'].keys())}")
    
    # Test 3: Symulacja wywołania funkcji
    print("\n3️⃣ Test wykonania funkcji...")
    
    # Mock wykonanie funkcji (bez prawdziwego OpenAI)
    with patch('app.safety.executor.SafeCodeExecutor.execute_function') as mock_executor:
        mock_executor.return_value = {
            'success': True,
            'result': 42,
            'output': 'Mnożę 6 * 7 = 42'
        }
        
        result = await caller._execute_function('multiply', {'a': 6, 'b': 7})
        
        print(f"🎯 Wynik wykonania:")
        print(f"   Sukces: {result.get('success')}")
        print(f"   Rezultat: {result.get('result')}")
        print(f"   Output: {result.get('output')}")
    
    # Test 4: Auto-rejestracja wszystkich funkcji
    print("\n4️⃣ Test auto-rejestracji...")
    
    # Dodaj więcej funkcji
    for i in range(3):
        func_being = FunctionBeing(
            soul=str(uuid.uuid4()),
            genesis={
                'name': f'function_{i}',
                'type': 'function',
                'source': f'def function_{i}(): return "Result {i}"',
                'description': f'Test function {i}'
            },
            attributes={},
            memories=[],
            self_awareness={},
            created_at=datetime.now()
        )
        await func_being.save()
    
    new_caller = OpenAIFunctionCaller(api_key)
    registered_count = await new_caller.auto_register_function_beings()
    
    print(f"🔄 Auto-zarejestrowano {registered_count} funkcji")
    print(f"📋 Wszystkie funkcje: {new_caller.get_available_functions()}")
    
    print("\n✨ Test zakończony pomyślnie!")
    
    await db.close()


if __name__ == "__main__":
    # Uruchom praktyczny test
    asyncio.run(run_practical_test())
