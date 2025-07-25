# app_v2/main_test.py
"""
Test aplikacji app_v2 - czysta architektura z komunikacją między bytami
"""

import asyncio
import uuid
from datetime import datetime

from app_v2.beings.genotype import Genotype
from app_v2.core.module_registry import ModuleRegistry
from app_v2.services.entity_manager import EntityManager

async def main():
    """Główna funkcja testowa"""
    print("🚀 Uruchamianie testów app_v2...")
    
    # 1. Test rejestracji modułów i genów
    print("\n📝 Test 1: Rejestracja modułów i genów z plików")
    registered_count = await ModuleRegistry.register_all_modules_from_directory("app_v2/gen_files")
    print(f"Zarejestrowano {registered_count} modułów")
    
    # 1b. Test rejestru genów
    print("\n🧬 Test 1b: Sprawdzenie rejestru genów")
    from app_v2.genetics import GeneRegistry
    all_genes = GeneRegistry.get_all_genes()
    print(f"Zarejestrowane geny: {list(all_genes.keys())}")
    
    # Sprawdź zależności
    errors = GeneRegistry.validate_dependencies()
    if errors:
        print(f"⚠️ Błędy zależności: {errors}")
    else:
        print("✅ Wszystkie zależności genów są poprawne")
    
    # 2. Test tworzenia bytu
    print("\n🆕 Test 2: Tworzenie głównego bytu")
    genesis = {"name": "TestLux", "type": "test_entity"}
    attributes = {"version": "2.0", "test_mode": True}
    memories = []
    self_awareness = {"purpose": "testing communication system"}
    
    lux = Genotype(
        uid=str(uuid.uuid4()),
        genesis=genesis,
        attributes=attributes,
        memories=memories,
        self_awareness=self_awareness
    )
    
    # 3. Test komunikacji - tworzenie bytów
    print("\n💬 Test 3: Komunikacja - tworzenie nowego bytu")
    result1 = await lux.execute({
        "command": "create",
        "alias": "logger_test", 
        "template": "test_logger",
        "force_new": True
    })
    print(f"Wynik tworzenia: {result1}")
    
    # 4. Test komunikacji - ładowanie bytów
    print("\n💬 Test 4: Komunikacja - ładowanie bytu")
    result2 = await lux.execute("load entity logger_test")
    print(f"Wynik ładowania: {result2}")
    
    # 5. Test komunikacji - wykonywanie funkcji
    print("\n💬 Test 5: Komunikacja - wykonywanie funkcji")
    result3 = await lux.execute({
        "command": "execute",
        "function": "log",
        "args": ["Hello from communication system!"]
    })
    print(f"Wynik wykonania funkcji: {result3}")
    
    # 6. Test komunikacji między bytami
    print("\n💬 Test 6: Komunikacja między bytami")
    result4 = await lux.execute("send to logger_test test message from main entity")
    print(f"Wynik komunikacji: {result4}")
    
    # 7. Test zapytań
    print("\n💬 Test 7: Zapytania")
    result5 = await lux.execute("query loaded genotypes")
    print(f"Wynik zapytania: {result5}")
    
    # 8. Test nierozpoznanej intencji
    print("\n💬 Test 8: Nierozpoznana intencja")
    result6 = await lux.execute("foobar unknown command")
    print(f"Wynik nierozpoznanej intencji: {result6}")
    
    # 9. Test memories i recall
    print("\n🧠 Test 9: Pamięć bytu")
    lux.remember("test_data", {"value": 42, "description": "test value"})
    recalled = lux.recall("test_data")
    print(f"Zapisane i odczytane z pamięci: {recalled}")
    
    # 10. Test logowania
    print("\n📝 Test 10: System logowania")
    lux.log("Test message from entity", "DEBUG")
    last_log = lux.recall("last_log")
    print(f"Ostatni log: {last_log}")
    
    # 11. Test AI Brain
    await test_ai_brain()
    
    print("\n✅ Wszystkie testy zakończone!")


async def test_ai_brain():
    """Test AI Brain z genami"""
    print("\n🧠 === TEST AI BRAIN ===")
    
    # Zainicjalizuj AI Brain
    from app_v2.ai.ai_brain import AIBrain
    ai = AIBrain()
    
    print(f"🔧 AI Brain ma {len(ai.available_functions)} dostępnych funkcji:")
    for func_name in list(ai.available_functions.keys())[:10]:  # Pokaż pierwsze 10
        print(f"  - {func_name}")
    if len(ai.available_functions) > 10:
        print(f"  ... i {len(ai.available_functions) - 10} więcej")
    
    # Test różnych intencji
    test_inputs = [
        "Find soul named logger",
        "Get soul by name test_logger", 
        "Execute basic_log function",
        "Show me all available genes",
        "Run log_message with hello world",
        "Create new entity called test_bot"
    ]
    
    for user_input in test_inputs:
        print(f"\n👤 User: {user_input}")
        try:
            result = await ai.process_user_intent(user_input)
            
            print(f"🎯 Intent: {result['intent_analysis']['intent']}")
            print(f"🔍 Found {len(result['relevant_functions'])} relevant functions")
            print(f"⚡ Executed {len(result['results'])} actions")
            
            for res in result['results'][:3]:  # Pokaż max 3 wyniki
                if res['success']:
                    print(f"  ✅ {res['function_name']}: {str(res['result'])[:100]}...")
                else:
                    print(f"  ❌ {res['function_name']}: {res['error']}")
        except Exception as e:
            print(f"  ❌ Błąd AI Brain: {e}")
    
    # Test listy funkcji
    print(f"\n📋 Lista dostępnych funkcji AI:")
    functions = ai.list_available_functions()
    for func_name, description in list(functions.items())[:5]:
        print(f"  - {func_name}: {description}")
    
    # Test OpenAI integration (mock)
    print(f"\n🤖 Test OpenAI integration (mock):")
    from app_v2.ai.openai_integration import MockOpenAI
    mock_ai = MockOpenAI()
    
    mock_result = await mock_ai.analyze_intent_with_llm(
        "Find me a logger gene", 
        ai.get_function_registry_for_openai()[:5]
    )
    print(f"Mock OpenAI response: {mock_result}")
