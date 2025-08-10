
```python
"""
Przykład użycia funkcji z Soul w OpenAI Function Calling.
"""

import asyncio
import os
from luxdb.models.soul import Soul
from ai.openai_function_caller import OpenAIFunctionCaller

async def demonstrate_soul_functions_with_openai():
    """Demonstracja funkcji Soul z OpenAI"""
    
    # 1. Utwórz funkcję testową
    def calculate_area(length: float, width: float) -> float:
        """Oblicza pole prostokąta"""
        return length * width
    
    def greet_user(name: str, language: str = "en") -> str:
        """Pozdrawia użytkownika w wybranym języku"""
        greetings = {
            "en": f"Hello, {name}!",
            "pl": f"Cześć, {name}!",
            "es": f"¡Hola, {name}!"
        }
        return greetings.get(language, greetings["en"])
    
    # 2. Utwórz Soul dla funkcji
    calculate_soul = await Soul.create_function_soul(
        name="calculate_area",
        func=calculate_area,
        description="Calculates rectangle area",
        alias="area_calculator"
    )
    
    greet_soul = await Soul.create_function_soul(
        name="greet_user", 
        func=greet_user,
        description="Greets user in specified language",
        alias="greeter"
    )
    
    print(f"✅ Created Soul functions:")
    print(f"   - {calculate_soul.alias}: {calculate_soul.soul_hash[:8]}...")
    print(f"   - {greet_soul.alias}: {greet_soul.soul_hash[:8]}...")
    
    # 3. Ustaw OpenAI Function Caller
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Brak klucza OPENAI_API_KEY")
        return
    
    caller = OpenAIFunctionCaller(api_key)
    
    # 4. Zarejestruj funkcje Soul w OpenAI
    count1 = await caller.register_soul_functions_for_openai(calculate_soul)
    count2 = await caller.register_soul_functions_for_openai(greet_soul)
    
    print(f"🎯 Zarejestrowano {count1 + count2} funkcji w OpenAI")
    
    # 5. Przetestuj wywołanie przez OpenAI
    prompt = """
    I need to calculate the area of a rectangle that is 5 meters long and 3 meters wide.
    Also, please greet me in Polish - my name is Łukasz.
    """
    
    result = await caller.call_with_functions(prompt)
    
    print("\n🤖 OpenAI Response:")
    print(f"Response: {result.get('response', 'No response')}")
    
    if result.get('tool_calls'):
        print(f"\n🛠️ Function calls ({len(result['tool_calls'])}):")
        for call in result['tool_calls']:
            print(f"  - {call['function']}: {call['arguments']} → {call['result']}")
    
    if result.get('final_response'):
        print(f"\n💬 Final response: {result['final_response']}")

if __name__ == "__main__":
    asyncio.run(demonstrate_soul_functions_with_openai())
```
