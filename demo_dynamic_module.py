
#!/usr/bin/env python3
"""
Demo dynamicznego ładowania modułów z genotypu Soul
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being

async def demo_gpt_callfunction_module():
    """Demonstracja Soul z modułem callfunction jako source code"""
    
    # Kod źródłowy modułu callfunction
    callfunction_source = '''
import openai
import json
from typing import Dict, Any, List

class GPTCallFunction:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def make_completion(self, messages: List[Dict], functions: List[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Wykonuje completion z opcjonalnymi funkcjami"""
        try:
            completion_params = {
                "model": self.model,
                "messages": messages,
                **kwargs
            }
            
            if functions:
                completion_params["tools"] = [
                    {"type": "function", "function": func} for func in functions
                ]
                completion_params["tool_choice"] = "auto"
            
            response = self.client.chat.completions.create(**completion_params)
            
            return {
                "success": True,
                "response": response.model_dump(),
                "content": response.choices[0].message.content if response.choices[0].message.content else None,
                "tool_calls": response.choices[0].message.tool_calls if response.choices[0].message.tool_calls else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Globalna instancja klienta - będzie dostępna dla Being
_gpt_client = None

def initialize_gpt(api_key: str, model: str = "gpt-4"):
    """Inicjalizuje klienta GPT"""
    global _gpt_client
    _gpt_client = GPTCallFunction(api_key, model)
    return {"initialized": True, "model": model}

def call_gpt_function(messages: List[Dict], functions: List[Dict] = None, **kwargs):
    """Handler dla wywołań GPT z funkcjami"""
    if not _gpt_client:
        return {"error": "GPT client not initialized"}
    
    return _gpt_client.make_completion(messages, functions, **kwargs)

def analyze_text(text: str, instruction: str = "Przeanalizuj ten tekst"):
    """Analizuje tekst używając GPT"""
    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": text}
    ]
    
    return call_gpt_function(messages)

def chat_with_context(message: str, context: List[Dict] = None):
    """Chat z kontekstem"""
    messages = context or []
    messages.append({"role": "user", "content": message})
    
    return call_gpt_function(messages)
'''

    # Genotyp z kodem źródłowym modułu
    gpt_specialist_genotype = {
        "genesis": {
            "name": "gpt_callfunction_specialist",
            "version": "1.0.0",
            "description": "GPT specialist z pełnym modułem callfunction",
            "type": "dynamic_module_soul"
        },
        "attributes": {
            "api_key": {"py_type": "str", "sensitive": True},
            "model": {"py_type": "str", "default": "gpt-4"},
            "total_calls": {"py_type": "int", "default": 0},
            "context_history": {"py_type": "list", "default": []}
        },
        "functions": {
            "initialize_gpt": {
                "description": "Inicjalizuje klienta GPT z kluczem API",
                "parameters": ["api_key", "model"]
            },
            "call_gpt_function": {
                "description": "Wykonuje wywołanie GPT z opcjonalnymi funkcjami",
                "parameters": ["messages", "functions"]
            },
            "analyze_text": {
                "description": "Analizuje tekst używając GPT",
                "parameters": ["text", "instruction"]
            },
            "chat_with_context": {
                "description": "Chat z zachowaniem kontekstu",
                "parameters": ["message", "context"]
            }
        },
        # Cały moduł jako string w genotypie!
        "module_source": callfunction_source
    }

    print("🧬 Tworzenie Soul z dynamicznym modułem...")
    
    # Utwórz Soul z modułem
    gpt_soul = await Soul.create(
        genotype=gpt_specialist_genotype,
        alias="gpt_specialist"
    )
    
    print(f"✅ Soul utworzone: {gpt_soul.alias}")
    print(f"📦 Zawiera kod modułu: {gpt_soul.has_module_source()}")
    
    # Utwórz Being - automatycznie załaduje moduł
    gpt_being = await Being.create(
        soul=gpt_soul,
        attributes={
            "api_key": "sk-test-key-here",  # W rzeczywistości z secrets
            "model": "gpt-4",
            "total_calls": 0
        },
        alias="gpt_specialist_being"
    )
    
    print(f"🤖 Being utworzone: {gpt_being.alias}")
    
    # Sprawdź załadowane handlery
    handlers = gpt_being.list_dynamic_handlers()
    print(f"🎯 Załadowano {len(handlers)} handlerów: {handlers}")
    
    # Test wykonania handlera (symulacja - bez prawdziwego klucza API)
    try:
        result = await gpt_being.execute_dynamic_handler(
            "initialize_gpt",
            api_key="test-key",
            model="gpt-4"
        )
        print(f"🔧 Test inicjalizacji: {result.get('success', False)}")
        
        # Test analizy tekstu
        analysis_result = await gpt_being.execute_dynamic_handler(
            "analyze_text",
            text="To jest przykład tekstu do analizy",
            instruction="Podsumuj główne punkty"
        )
        print(f"📝 Test analizy: {analysis_result.get('success', False)}")
        
    except Exception as e:
        print(f"⚠️  Test error (oczekiwany bez prawdziwego API key): {e}")
    
    print(f"\n✨ Being ma teraz wszystkie funkcje z modułu callfunction jako handlery!")
    print(f"📊 Statystyki: {gpt_being.data}")
    
    return gpt_being

async def main():
    """Główna demo"""
    print("🚀 LuxDB Dynamic Module Demo")
    print("=" * 50)
    
    # Demo GPT CallFunction
    gpt_being = await demo_gpt_callfunction_module()
    
    print(f"\n🎉 Demo zakończone pomyślnie!")
    print(f"Being '{gpt_being.alias}' ma teraz pełny zestaw narzędzi GPT")
    
    # Wylistuj wszystkie dostępne możliwości
    soul = await gpt_being.get_soul()
    print(f"\nDostępne funkcje z genotypu: {list(soul.genotype.get('functions', {}).keys())}")
    print(f"Załadowane handlery: {gpt_being.list_dynamic_handlers()}")

if __name__ == "__main__":
    asyncio.run(main())
