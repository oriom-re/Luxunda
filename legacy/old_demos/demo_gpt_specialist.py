
#!/usr/bin/env python3
"""
Demo GPT Specialist using regular Soul with GPT functions
"""

import asyncio
import os
from datetime import datetime
from luxdb.models.gpt_specialist_soul import GPTSpecialistFactory
from luxdb.models.being import Being


async def example_analysis_function(text: str, analysis_type: str = "sentiment") -> dict:
    """Przykładowa funkcja analizy tekstu"""
    # Symulacja analizy
    results = {
        "sentiment": {"score": 0.7, "label": "positive"},
        "keywords": {"keywords": ["example", "analysis", "text"]},
        "summary": {"summary": f"Podsumowanie: {text[:50]}..."}
    }
    
    return {
        "analysis_type": analysis_type,
        "input_text": text,
        "result": results.get(analysis_type, {"error": "Unknown analysis type"}),
        "timestamp": datetime.now().isoformat()
    }


async def example_data_processor(data: dict, operation: str = "process") -> dict:
    """Przykładowa funkcja przetwarzania danych"""
    operations = {
        "process": {"processed": True, "data": data},
        "validate": {"valid": True, "errors": []},
        "transform": {"transformed_data": {k: str(v).upper() for k, v in data.items()}}
    }
    
    return {
        "operation": operation,
        "result": operations.get(operation, {"error": "Unknown operation"}),
        "timestamp": datetime.now().isoformat()
    }


async def demo_gpt_specialist():
    """Demo GPT Specialist jako regularna Soul"""
    
    # Sprawdź klucz API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Brak klucza OpenAI API. Ustaw OPENAI_API_KEY w zmiennych środowiskowych.")
        return
    
    print("🤖 === Demo GPT Specialist Soul ===")
    
    # Dostępne funkcje tools
    available_functions = {
        "analyze_text": example_analysis_function,
        "process_data": example_data_processor
    }
    
    # System prompt
    system_prompt = """Jesteś specjalistą analizy danych i tekstu. 
    Masz dostęp do funkcji analyze_text i process_data.
    Odpowiadaj zwięźle i konkretnie."""
    
    try:
        # Utwórz GPT specialist jako REGULARNĄ Soul
        gpt_soul = await GPTSpecialistFactory.create_gpt_specialist_soul(
            specialist_name="data_analyst",
            api_key=api_key,
            model="gpt-3.5-turbo",  # Tańszy model do testów
            available_functions=available_functions,
            system_prompt=system_prompt,
            alias="gpt_data_analyst"
        )
        
        print(f"✅ Utworzono GPT Soul: {gpt_soul.alias}")
        print(f"📋 Hash: {gpt_soul.soul_hash[:8]}...")
        print(f"🔧 Dostępne funkcje: {gpt_soul.list_functions()}")
        
        # Utwórz Being na podstawie Soul
        gpt_being = await Being.create(gpt_soul, attributes={
            "specialist_type": "data_analyst",
            "active": True
        })
        
        print(f"🧬 Utworzono Being: {gpt_being.alias}")
        
        # Test 1: Podstawowe wywołanie GPT
        print("\n📞 === Test 1: Podstawowe wywołanie GPT ===")
        response1 = await gpt_being.execute_soul_function(
            "gpt_call",
            user_message="Witaj! Kim jesteś i co potrafisz?",
            use_tools=False
        )
        
        if response1.get('success'):
            result = response1['data']['result']
            print(f"🤖 GPT Response: {result.get('response', 'Brak odpowiedzi')}")
        else:
            print(f"❌ Błąd: {response1.get('error')}")
        
        # Test 2: Wywołanie z tools
        print("\n🔧 === Test 2: GPT z tools ===")
        response2 = await gpt_being.execute_soul_function(
            "gpt_call",
            user_message="Przeanalizuj sentyment tego tekstu: 'Uwielbiam programować w Pythonie!'",
            use_tools=True
        )
        
        if response2.get('success'):
            result = response2['data']['result']
            print(f"🤖 GPT Response: {result.get('response', 'Brak odpowiedzi')}")
            
            if result.get('tool_calls'):
                print("🔧 Tool calls:")
                for tool_call in result['tool_calls']:
                    print(f"  - {tool_call['function']}: {tool_call.get('result', tool_call.get('error'))}")
        else:
            print(f"❌ Błąd: {response2.get('error')}")
        
        # Test 3: Historia konwersacji
        print("\n📚 === Test 3: Historia konwersacji ===")
        history = await gpt_being.execute_soul_function("get_conversation")
        
        if history.get('success'):
            conv_history = history['data']['result']
            print(f"📜 Historia ({len(conv_history)} wiadomości):")
            for msg in conv_history[-4:]:  # Ostatnie 4 wiadomości
                print(f"  {msg['role']}: {msg['content'][:100]}...")
        
        # Test 4: Sprawdź że to NORMALNA Soul
        print("\n🧬 === Test 4: Weryfikacja Soul ===")
        print(f"🔍 Typ obiektu: {type(gpt_soul).__name__}")
        print(f"📊 Genotyp genesis: {gpt_soul.genotype.get('genesis', {}).get('name')}")
        print(f"⚙️ Funkcje w rejestrze: {len(gpt_soul._function_registry)}")
        print(f"📋 Atrybuty w genotypie: {list(gpt_soul.genotype.get('attributes', {}).keys())}")
        
        # Test 5: Soul może być używana normalnie
        print("\n🔄 === Test 5: Normalne operacje Soul ===")
        
        # Sprawdź informacje o funkcji
        func_info = gpt_soul.get_function_info("gpt_call")
        if func_info:
            print(f"ℹ️ Info o funkcji gpt_call: {func_info.get('description')}")
        
        # Walidacja wywołania
        errors = gpt_soul.validate_function_call("gpt_call", "test message")
        print(f"✅ Walidacja wywołania: {'Brak błędów' if not errors else errors}")
        
        print("\n🎉 === Soul pozostała Soul z dodatkowymi funkcjami GPT! ===")
        
    except Exception as e:
        print(f"❌ Błąd w demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(demo_gpt_specialist())
