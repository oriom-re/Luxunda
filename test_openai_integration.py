
import asyncio
import os
import json
from app.ai.function_calling import OpenAIFunctionCaller
from app.beings.function_being import FunctionBeing
from app.database import set_db_pool
import aiosqlite
from datetime import datetime
import uuid

async def test_real_openai_integration():
    """Test integracji z prawdziwym API OpenAI"""
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Brak klucza API OpenAI. Ustaw zmienną środowiskową OPENAI_API_KEY")
        return
    
    print("🚀 Test integracji z OpenAI API...")
    
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
    
    # Utwórz użyteczne funkcje
    functions_data = [
        {
            'name': 'calculate_area',
            'source': '''def calculate_area(length: float, width: float) -> float:
    """Oblicza pole prostokąta"""
    return length * width''',
            'description': 'Oblicza pole prostokąta na podstawie długości i szerokości'
        },
        {
            'name': 'generate_password',
            'source': '''def generate_password(length: int) -> str:
    """Generuje losowe hasło"""
    import random
    import string
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))''',
            'description': 'Generuje losowe hasło o podanej długości'
        },
        {
            'name': 'count_words',
            'source': '''def count_words(text: str) -> dict:
    """Liczy słowa w tekście"""
    words = text.lower().split()
    word_count = {}
    for word in words:
        word = word.strip('.,!?;:"()[]{}')
        word_count[word] = word_count.get(word, 0) + 1
    return {
        'total_words': len(words),
        'unique_words': len(word_count),
        'word_frequency': word_count
    }''',
            'description': 'Analizuje tekst i zwraca statystyki słów'
        }
    ]
    
    # Utwórz byty funkcyjne
    function_beings = []
    for func_data in functions_data:
        being = FunctionBeing(
            soul=str(uuid.uuid4()),
            genesis={
                'name': func_data['name'],
                'type': 'function',
                'source': func_data['source'],
                'description': func_data['description'],
                'signature': f"{func_data['name']}(...)"
            },
            attributes={'category': 'utility'},
            memories=[],
            self_awareness={'confidence': 0.9, 'trust_level': 0.85},
            created_at=datetime.now()
        )
        await being.save()
        function_beings.append(being)
    
    print(f"✅ Utworzono {len(function_beings)} bytów funkcyjnych")
    
    # Zarejestruj funkcje w OpenAI
    caller = OpenAIFunctionCaller(api_key)
    
    for being in function_beings:
        success = await caller.register_function_being(being)
        print(f"📝 Rejestracja {being.genesis['name']}: {'✅' if success else '❌'}")
    
    print(f"\n🔧 Dostępne funkcje: {caller.get_available_functions()}")
    
    # Test różnych promptów
    test_prompts = [
        "Oblicz pole prostokąta o długości 5.5 i szerokości 3.2",
        "Wygeneruj bezpieczne hasło długości 12 znaków",
        "Przeanalizuj ten tekst: 'Python jest fantastyczny język Python do programowania Python aplikacji'",
        "Pomóż mi obliczyć pole prostokąta 10x8 metrów i wygenerować hasło na 8 znaków",
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{i}️⃣ Test: {prompt}")
        print("-" * 50)
        
        try:
            result = await caller.call_with_functions(prompt)
            
            if 'error' in result:
                print(f"❌ Błąd: {result['error']}")
                continue
            
            print(f"💬 Odpowiedź: {result.get('response', 'Brak odpowiedzi')}")
            
            if result.get('tool_calls'):
                print(f"🔧 Wywołano funkcji: {len(result['tool_calls'])}")
                for call in result['tool_calls']:
                    print(f"   - {call['function']}({call['arguments']})")
                    print(f"     Wynik: {call['result'].get('result', 'Brak wyniku')}")
            
            if result.get('final_response'):
                print(f"✨ Finalna odpowiedź: {result['final_response']}")
                
        except Exception as e:
            print(f"❌ Błąd podczas testu: {str(e)}")
    
    # Test pamięci funkcji
    print(f"\n🧠 Sprawdzanie pamięci funkcji...")
    for being in function_beings:
        updated_being = await FunctionBeing.load(being.soul)
        if updated_being and updated_being.memories:
            print(f"📝 {being.genesis['name']}: {len(updated_being.memories)} wywołań w pamięci")
            for memory in updated_being.memories[-2:]:  # Pokaż ostatnie 2
                if memory.get('type') == 'openai_execution':
                    print(f"   - {memory.get('timestamp', 'unknown')}: {memory.get('success', False)}")
    
    await db.close()
    print("\n✨ Test integracji zakończony!")


if __name__ == "__main__":
    asyncio.run(test_real_openai_integration())
