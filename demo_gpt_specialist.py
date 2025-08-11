
#!/usr/bin/env python3
"""
Demo GPT Specialist - pokazuje jak Being może być gotowym specjalistą GPT
"""

import asyncio
import os
from luxdb.models.gpt_specialist_soul import GPTSpecialistSoul
from luxdb.models.being import Being

# Przykładowe funkcje narzędzi dla specjalisty
def analyze_code(code: str, language: str = "python") -> dict:
    """Analizuje kod i zwraca podstawowe informacje"""
    lines = code.split('\n')
    return {
        "lines_count": len(lines),
        "language": language,
        "has_functions": "def " in code,
        "has_classes": "class " in code,
        "complexity": "simple" if len(lines) < 20 else "complex"
    }

def calculate_math(expression: str) -> dict:
    """Bezpiecznie oblicza wyrażenie matematyczne"""
    try:
        # Proste zabezpieczenie - tylko podstawowe operacje
        allowed_chars = "0123456789+-*/.() "
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            return {
                "expression": expression,
                "result": result,
                "success": True
            }
        else:
            return {
                "error": "Expression contains forbidden characters",
                "success": False
            }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }

def get_system_info() -> dict:
    """Pobiera informacje o systemie"""
    import platform
    import psutil
    
    return {
        "platform": platform.system(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "disk_usage": {
            "total": round(psutil.disk_usage('/').total / (1024**3), 2),
            "free": round(psutil.disk_usage('/').free / (1024**3), 2)
        }
    }

async def main():
    """Demo główne"""
    
    # Sprawdź czy jest klucz API (można ustawić jako zmienną środowiskową)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Brak klucza OPENAI_API_KEY - używam mock demo")
        # W demo możemy symulować bez rzeczywistego API
        api_key = "mock-api-key-for-demo"
    
    print("🤖 Tworzenie GPT Specialist Soul...")
    
    # Zdefiniuj dostępne narzędzia
    specialist_tools = {
        "analyze_code": analyze_code,
        "calculate_math": calculate_math,
        "get_system_info": get_system_info
    }
    
    # System prompt dla specjalisty
    system_prompt = """
    Jesteś specjalistą programistą i analitykiem systemowym. 
    Masz dostęp do narzędzi do analizy kodu, obliczeń matematycznych 
    i pobierania informacji o systemie. 
    Używaj ich gdy potrzebujesz konkretnych danych.
    Odpowiadaj po polsku.
    """
    
    # Utwórz specjalistyczną Soul
    gpt_soul = await GPTSpecialistSoul.create_gpt_callfunction_soul(
        specialist_name="code_analyst_gpt",
        api_key=api_key,
        model="gpt-4",
        available_functions=specialist_tools,
        system_prompt=system_prompt
    )
    
    print(f"✅ Utworzono Soul: {gpt_soul.alias}")
    print(f"📋 Dostępne funkcje: {gpt_soul.list_functions()}")
    
    # Utwórz Being z tym Soul
    print("\n🧬 Tworzenie Being specjalisty...")
    
    being_data = {
        "specialist_type": "code_analyst",
        "created_for": "demo purposes",
        "tools_count": len(specialist_tools)
    }
    
    specialist_being = await Being.create(
        soul=gpt_soul,
        attributes=being_data,
        alias="code_analyst_specialist"
    )
    
    print(f"✅ Utworzono Being: {specialist_being.alias}")
    print(f"🆔 ULID: {specialist_being.ulid}")
    
    # Demo interakcji z specjalistą
    print("\n💬 Demo interakcji z GPT specjalistą:")
    
    # Test 1: Analiza kodu
    print("\n1️⃣ Prośba o analizę kodu:")
    test_code = """
def hello_world():
    print("Hello, World!")
    return True

class TestClass:
    def __init__(self):
        self.value = 42
"""
    
    # Symulacja wywołania (bez rzeczywistego API)
    print(f"Kod do analizy:\n{test_code}")
    
    try:
        # W rzeczywistej implementacji:
        # result = await specialist_being.execute_soul_function(
        #     "gpt_call", 
        #     f"Przeanalizuj ten kod Python:\n\n{test_code}"
        # )
        
        # Demo symulacji:
        code_analysis = analyze_code(test_code)
        print(f"📊 Analiza kodu: {code_analysis}")
        
    except Exception as e:
        print(f"❌ Błąd: {e}")
    
    # Test 2: Obliczenia
    print("\n2️⃣ Test obliczeń:")
    math_result = calculate_math("(10 + 5) * 3 - 8")
    print(f"🧮 Wynik obliczeń: {math_result}")
    
    # Test 3: Informacje o systemie  
    print("\n3️⃣ Informacje o systemie:")
    try:
        sys_info = get_system_info()
        print(f"💻 System info: {sys_info}")
    except Exception as e:
        print(f"❌ Błąd pobierania info: {e}")
    
    # Test 4: Lista funkcji Being
    print("\n4️⃣ Dostępne funkcje w Being:")
    available_funcs = await specialist_being.list_available_functions()
    print(f"🛠️  Funkcje: {available_funcs}")
    
    print("\n✅ Demo zakończone!")
    print("\n🎯 Kluczowe zalety:")
    print("- Being ma wbudowanego klienta GPT")
    print("- Narzędzia są gotowe do użycia")
    print("- Brak potrzeby zarządzania wątkami")
    print("- Każdy Being to samodzielny specjalista")
    print("- Tools schema automatycznie generowane")

if __name__ == "__main__":
    asyncio.run(main())
