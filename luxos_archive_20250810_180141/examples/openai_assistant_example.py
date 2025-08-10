
"""
Przykład Soul i Being dla asystenta OpenAI z poprawną strukturą atrybutów.
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.globals import Globals

async def create_openai_assistant_example():
    """Tworzy przykład Soul i Being dla asystenta OpenAI"""
    
    # 1. Definicja Soul - tylko struktura, bez danych
    openai_assistant_genotype = {
        "genesis": {
            "name": "openai_assistant",
            "type": "ai_assistant",
            "version": "1.0.0",
            "description": "Asystent AI wykorzystujący OpenAI API",
            "created_at": "2025-01-10T00:00:00Z"
        },
        "attributes": {
            # Konfiguracja OpenAI
            "api_key": {
                "py_type": "str", 
                "required": True,
                "description": "Klucz API do OpenAI"
            },
            "model": {
                "py_type": "str", 
                "default": "gpt-4",
                "description": "Model OpenAI do użycia"
            },
            "temperature": {
                "py_type": "float", 
                "default": 0.7,
                "min_value": 0.0,
                "max_value": 2.0,
                "description": "Temperatura dla generowania odpowiedzi"
            },
            "max_tokens": {
                "py_type": "int", 
                "default": 1000,
                "description": "Maksymalna liczba tokenów w odpowiedzi"
            },
            
            # Stan asystenta
            "name": {
                "py_type": "str", 
                "default": "LuxAssistant",
                "description": "Nazwa asystenta"
            },
            "personality": {
                "py_type": "str", 
                "default": "helpful_professional",
                "description": "Osobowość asystenta"
            },
            "system_prompt": {
                "py_type": "str", 
                "default": "You are a helpful AI assistant integrated with LuxDB system.",
                "description": "Systemowy prompt dla asystenta"
            },
            "conversation_history": {
                "py_type": "List[dict]", 
                "default": [],
                "description": "Historia konwersacji"
            },
            
            # Statystyki
            "total_interactions": {
                "py_type": "int", 
                "default": 0,
                "description": "Całkowita liczba interakcji"
            },
            "last_interaction": {
                "py_type": "str", 
                "required": False,
                "description": "Czas ostatniej interakcji"
            },
            "status": {
                "py_type": "str", 
                "default": "active",
                "description": "Status asystenta"
            }
        },
        "functions": {
            "chat": {
                "py_type": "function",
                "description": "Główna funkcja do rozmowy z asystentem",
                "parameters": {
                    "message": {"py_type": "str", "required": True},
                    "context": {"py_type": "dict", "required": False}
                },
                "returns": {"py_type": "dict"}
            },
            "get_stats": {
                "py_type": "function", 
                "description": "Pobiera statystyki asystenta",
                "parameters": {},
                "returns": {"py_type": "dict"}
            },
            "reset_conversation": {
                "py_type": "function",
                "description": "Resetuje historię konwersacji",
                "parameters": {},
                "returns": {"py_type": "bool"}
            }
        }
    }
    
    print("🔧 Tworzenie Soul dla asystenta OpenAI...")
    
    # 2. Utwórz Soul (tylko definicja struktury)
    assistant_soul = await Soul.create(openai_assistant_genotype, alias="openai_assistant")
    print(f"✅ Soul utworzony: {assistant_soul.soul_hash[:8]}...")
    
    # 3. Wyświetl domyślne dane z Soul
    default_data = assistant_soul.get_default_data()
    print(f"📋 Domyślne dane z Soul:")
    for key, value in default_data.items():
        print(f"   {key}: {value}")
    
    # 4. Utwórz Being z konkretnymi danymi
    assistant_data = {
        "api_key": "sk-fake-key-for-demo",  # W praktyce z environment variables
        "model": "gpt-4-turbo", 
        "name": "Lux AI Assistant",
        "personality": "creative_helpful",
        "system_prompt": "You are Lux, an advanced AI assistant integrated with the LuxDB evolutionary database system. You help users interact with their data, create beings, and explore the system's capabilities.",
        "temperature": 0.8
    }
    
    print(f"\n🤖 Tworzenie Being asystenta z danymi...")
    assistant_being = await Being.create(assistant_soul, attributes=assistant_data, alias="lux_assistant")
    print(f"✅ Being utworzony: {assistant_being.ulid}")
    
    # 5. Wyświetl dane Being
    print(f"\n📊 Dane Being:")
    for key, value in assistant_being.data.items():
        if key == "api_key":
            print(f"   {key}: ***hidden***")
        else:
            print(f"   {key}: {value}")
    
    # 6. Test walidacji - spróbuj dodać nieprawidłowe dane
    print(f"\n🧪 Test walidacji...")
    try:
        invalid_data = {
            "temperature": 3.0,  # Przekracza max_value
            "max_tokens": "not_a_number"  # Nieprawidłowy typ
        }
        
        errors = assistant_soul.validate_data(invalid_data)
        if errors:
            print(f"❌ Błędy walidacji (zgodnie z oczekiwaniem):")
            for error in errors:
                print(f"   - {error}")
        else:
            print(f"✅ Brak błędów walidacji")
            
    except Exception as e:
        print(f"❌ Błąd podczas walidacji: {e}")
    
    # 7. Test poprawnej aktualizacji danych
    print(f"\n🔄 Test aktualizacji danych...")
    assistant_being.set_attribute("total_interactions", 1)
    assistant_being.set_attribute("last_interaction", "2025-01-10T12:00:00Z")
    assistant_being.set_attribute("status", "busy")
    
    print(f"✅ Dane zaktualizowane:")
    print(f"   total_interactions: {assistant_being.get_attribute('total_interactions')}")
    print(f"   last_interaction: {assistant_being.get_attribute('last_interaction')}")
    print(f"   status: {assistant_being.get_attribute('status')}")
    
    return assistant_soul, assistant_being

async def demo_openai_communication():
    """Demo komunikacji z asystentem OpenAI"""
    
    print("\n" + "="*60)
    print("🚀 DEMO: Komunikacja z asystentem OpenAI")
    print("="*60)
    
    soul, being = await create_openai_assistant_example()
    
    # Symulacja funkcji chat (bez rzeczywistego wywołania OpenAI)
    async def mock_chat_function(message: str, context: dict = None):
        """Symulacja funkcji chat asystenta"""
        
        # Aktualizuj statystyki
        current_interactions = being.get_attribute("total_interactions", 0)
        being.set_attribute("total_interactions", current_interactions + 1)
        being.set_attribute("last_interaction", "2025-01-10T12:30:00Z")
        
        # Dodaj do historii konwersacji
        history = being.get_attribute("conversation_history", [])
        history.append({
            "role": "user",
            "content": message,
            "timestamp": "2025-01-10T12:30:00Z"
        })
        
        # Symulowana odpowiedź asystenta
        response = f"Cześć! Jestem {being.get_attribute('name')}. Otrzymałem twoją wiadomość: '{message}'. Obecnie mam {being.get_attribute('total_interactions')} interakcji w historii."
        
        history.append({
            "role": "assistant", 
            "content": response,
            "timestamp": "2025-01-10T12:30:00Z"
        })
        
        being.set_attribute("conversation_history", history)
        
        return {
            "success": True,
            "response": response,
            "model": being.get_attribute("model"),
            "tokens_used": len(response.split()) * 1.5  # Symulacja
        }
    
    # Rejestruj funkcję w Soul (w przyszłości)
    soul._register_immutable_function("chat", mock_chat_function)
    
    # Test komunikacji
    print(f"\n💬 Test komunikacji z asystentem...")
    
    test_messages = [
        "Witaj! Jak się masz?",
        "Opowiedz mi o systemie LuxDB",
        "Jakie są twoje możliwości?"
    ]
    
    for message in test_messages:
        print(f"\n👤 Użytkownik: {message}")
        
        # Wykonaj funkcję przez Soul
        result = await soul.execute_function("chat", message)
        
        if result.get("success"):
            response_data = result.get("data", {}).get("result", {})
            print(f"🤖 {being.get_attribute('name')}: {response_data.get('response')}")
            print(f"📊 Model: {response_data.get('model')}, Tokeny: {response_data.get('tokens_used')}")
        else:
            print(f"❌ Błąd: {result.get('error')}")
    
    # Wyświetl końcowe statystyki
    print(f"\n📈 Końcowe statystyki:")
    print(f"   Całkowite interakcje: {being.get_attribute('total_interactions')}")
    print(f"   Historia konwersacji: {len(being.get_attribute('conversation_history'))} wpisów")
    print(f"   Status: {being.get_attribute('status')}")
    
    return soul, being

if __name__ == "__main__":
    asyncio.run(demo_openai_communication())
