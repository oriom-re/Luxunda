
#!/usr/bin/env python3
"""
Runner dla testów OpenAI Function Calling
"""

import asyncio
import sys
import os

# Dodaj ścieżkę projektu do sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    """Główna funkcja uruchamiająca testy"""
    print("🧪 LuxOS - Test Suite dla OpenAI Function Calling")
    print("=" * 60)
    
    # Sprawdź dostępność klucza API
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print(f"✅ Klucz OpenAI API: {'*' * 20}{api_key[-4:]}")
    else:
        print("⚠️  Brak klucza OpenAI API - testy integracyjne będą pominięte")
    
    print("\n" + "=" * 60)
    
    # Test 1: Podstawowy test funkcjonalności
    try:
        print("\n🔬 PRAKTYCZNY TEST FUNKCJONALNOŚCI")
        from test_function_calling import run_practical_test
        await run_practical_test()
        print("✅ Test funkcjonalności: PASSED")
    except Exception as e:
        print(f"❌ Test funkcjonalności: FAILED - {str(e)}")
    
    # Test 2: Test integracji z OpenAI (tylko jeśli jest klucz API)
    if api_key:
        try:
            print("\n🌐 TEST INTEGRACJI Z OPENAI")
            from test_openai_integration import test_real_openai_integration
            await test_real_openai_integration()
            print("✅ Test integracji: PASSED")
        except Exception as e:
            print(f"❌ Test integracji: FAILED - {str(e)}")
    else:
        print("\n⚠️  POMINIĘTO TEST INTEGRACJI (brak klucza API)")
    
    # Test 3: Test przypadków brzegowych
    try:
        print("\n🔍 TEST PRZYPADKÓW BRZEGOWYCH")
        await test_edge_cases()
        print("✅ Test przypadków brzegowych: PASSED")
    except Exception as e:
        print(f"❌ Test przypadków brzegowych: FAILED - {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 WSZYSTKIE TESTY ZAKOŃCZONE")
    print("=" * 60)

async def test_edge_cases():
    """Test przypadków brzegowych"""
    from app.ai.function_calling import OpenAIFunctionCaller
    from app.beings.function_being import FunctionBeing
    from app.database import set_db_pool
    import aiosqlite
    from datetime import datetime
    import uuid
    
    # Przygotuj bazę
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
    
    # Test 1: Funkcja z błędnym kodem
    print("  🔹 Test funkcji z błędnym kodem...")
    
    broken_function = FunctionBeing(
        soul=str(uuid.uuid4()),
        genesis={
            'name': 'broken_function',
            'type': 'function',
            'source': '''def broken_function(x):
    # Celowo błędny kod
    return x / zero_variable  # undefined variable''',
            'description': 'Funkcja z błędem'
        },
        attributes={},
        memories=[],
        self_awareness={},
        created_at=datetime.now()
    )
    
    await broken_function.save()
    
    caller = OpenAIFunctionCaller("test_key")
    success = await caller.register_function_being(broken_function)
    
    if success:
        # Spróbuj wykonać funkcję (powinna się nie udać)
        result = await caller._execute_function('broken_function', {'x': 10})
        assert result.get('success') is False
        print("    ✅ Funkcja z błędem poprawnie obsłużona")
    
    # Test 2: Funkcja bez parametrów
    print("  🔹 Test funkcji bez parametrów...")
    
    no_params_function = FunctionBeing(
        soul=str(uuid.uuid4()),
        genesis={
            'name': 'get_timestamp',
            'type': 'function',
            'source': '''def get_timestamp():
    """Zwraca aktualny timestamp"""
    from datetime import datetime
    return datetime.now().isoformat()''',
            'description': 'Zwraca aktualny timestamp'
        },
        attributes={},
        memories=[],
        self_awareness={},
        created_at=datetime.now()
    )
    
    await no_params_function.save()
    
    success = await caller.register_function_being(no_params_function)
    assert success is True
    
    schema = caller.available_functions['get_timestamp']['schema']
    assert len(schema['function']['parameters']['properties']) == 0
    assert len(schema['function']['parameters']['required']) == 0
    print("    ✅ Funkcja bez parametrów poprawnie zarejestrowana")
    
    # Test 3: Funkcja z wieloma typami parametrów
    print("  🔹 Test funkcji z różnymi typami parametrów...")
    
    complex_function = FunctionBeing(
        soul=str(uuid.uuid4()),
        genesis={
            'name': 'complex_function',
            'type': 'function',
            'source': '''def complex_function(text, number, flag, items):
    """Funkcja z różnymi typami parametrów"""
    return {
        'text_length': len(str(text)),
        'number_squared': int(number) ** 2,
        'flag_inverted': not bool(flag),
        'items_count': len(str(items).split(','))
    }''',
            'description': 'Funkcja testowa z różnymi typami'
        },
        attributes={},
        memories=[],
        self_awareness={},
        created_at=datetime.now()
    )
    
    await complex_function.save()
    
    success = await caller.register_function_being(complex_function)
    assert success is True
    
    schema = caller.available_functions['complex_function']['schema']
    params = schema['function']['parameters']['properties']
    assert 'text' in params
    assert 'number' in params
    assert 'flag' in params
    assert 'items' in params
    print("    ✅ Funkcja z wieloma parametrami poprawnie zarejestrowana")
    
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())
