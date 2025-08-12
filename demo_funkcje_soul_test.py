
#!/usr/bin/env python3
"""
🧬 Praktyczny test systemu funkcji Soul
Sprawdzamy jak działa przechowywanie kodu i wykonywanie funkcji!
"""

import asyncio
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from luxdb.models.soul import Soul
from luxdb.models.being import Being
from database.postgre_db import Postgre_db

async def demo_funkcje_soul():
    print("🧬 Demo: System Funkcji Soul w Praktyce")
    print("=" * 50)
    
    # Inicjalizacja bazy danych
    print("📊 Inicjalizacja PostgreSQL...")
    db = Postgre_db()
    await db.initialize()
    
    # 1. Tworzenie Soul z kodem źródłowym
    print("\n1. 📝 Tworzenie Soul z module_source...")
    
    calculator_code = '''
def dodaj(a, b):
    """Dodaje dwie liczby"""
    return a + b

def odejmij(a, b):
    """Odejmuje drugą liczbę od pierwszej"""
    return a - b

def pomnoz(a, b):
    """Mnoży dwie liczby"""
    return a * b

def podziel(a, b):
    """Dzieli pierwszą liczbę przez drugą"""
    if b == 0:
        return "Nie można dzielić przez zero!"
    return a / b

def _helper_validate(num):
    """Prywatna funkcja pomocnicza - waliduje liczby"""
    return isinstance(num, (int, float))

def zaawansowane_obliczenie(x, y, operacja="dodaj"):
    """Zaawansowana funkcja używająca prywatnej funkcji"""
    if not _helper_validate(x) or not _helper_validate(y):
        return "Błąd: Podaj prawidłowe liczby!"
    
    if operacja == "dodaj":
        return dodaj(x, y)
    elif operacja == "odejmij":
        return odejmij(x, y)
    elif operacja == "pomnoz":
        return pomnoz(x, y)
    elif operacja == "podziel":
        return podziel(x, y)
    else:
        return "Nieznana operacja!"

def init(being_context=None):
    """Inicjalizacja kalkulatora"""
    if being_context:
        print(f"🔧 Inicjalizacja kalkulatora dla {being_context.get('alias', 'Unknown')}")
    return {"status": "Calculator ready!", "version": "1.0"}

def execute(data=None, **kwargs):
    """Główna funkcja wykonawcza"""
    if not data:
        return "Podaj dane do przetworzenia!"
    
    if "operacja" in data and "a" in data and "b" in data:
        return zaawansowane_obliczenie(data["a"], data["b"], data["operacja"])
    
    return f"Przetworzono dane: {data}"
'''
    
    # Tworzenie genotypu z module_source
    calculator_genotype = {
        "genesis": {
            "name": "calculator_soul",
            "type": "function_calculator",
            "version": "1.0.0",
            "description": "Soul z funkcjami kalkulatora"
        },
        "attributes": {
            "calculator_name": {"py_type": "str", "default": "SuperCalculator"},
            "precision": {"py_type": "int", "default": 2},
            "last_result": {"py_type": "float"}
        },
        "module_source": calculator_code
    }
    
    # Soul automatycznie rozpozna funkcje z module_source
    calculator_soul = await Soul.create(calculator_genotype, alias="calculator_demo")
    
    print(f"✅ Soul created: {calculator_soul.alias}")
    print(f"📋 Soul hash: {calculator_soul.soul_hash[:16]}...")
    
    # 2. Sprawdź rozpoznane funkcje
    print(f"\n2. 🔍 Analiza rozpoznanych funkcji...")
    
    visibility_info = calculator_soul.get_function_visibility_info()
    print(f"📊 Funkcje publiczne: {visibility_info['functions']['public']['count']}")
    print(f"📊 Funkcje prywatne: {visibility_info['functions']['private']['count']}")
    print(f"📊 Wszystkich funkcji: {visibility_info['functions']['total_registered']}")
    
    print(f"\n🔓 Publiczne funkcje:")
    for func_name in visibility_info['functions']['public']['names']:
        print(f"   • {func_name}")
    
    print(f"\n🔒 Prywatne funkcje:")
    for func_name in visibility_info['functions']['private']['names']:
        print(f"   • {func_name}")
    
    # 3. Testowanie funkcji bezpośrednio przez Soul
    print(f"\n3. ⚡ Testowanie funkcji bezpośrednio przez Soul...")
    
    # Test podstawowych funkcji
    result1 = await calculator_soul.execute_function("dodaj", 15, 25)
    print(f"📈 15 + 25 = {result1['data']['result']}")
    
    result2 = await calculator_soul.execute_function("pomnoz", 7, 8)
    print(f"📈 7 × 8 = {result2['data']['result']}")
    
    result3 = await calculator_soul.execute_function("podziel", 100, 4)
    print(f"📈 100 ÷ 4 = {result3['data']['result']}")
    
    # Test zaawansowanej funkcji
    result4 = await calculator_soul.execute_function("zaawansowane_obliczenie", 20, 5, operacja="podziel")
    print(f"📈 Zaawansowane: 20 ÷ 5 = {result4['data']['result']}")
    
    # 4. Tworzenie Being i testowanie przez Being
    print(f"\n4. 🤖 Tworzenie Being i testowanie funkcji...")
    
    being_result = await Being.set(
        soul=calculator_soul,
        data={
            "calculator_name": "MegaCalculator Pro",
            "precision": 3,
            "last_result": 0.0
        },
        alias="calculator_being"
    )
    
    if being_result.get('success'):
        calc_being = being_result['data']['being']
        print(f"✅ Being created: {calc_being.alias}")
        
        # Lista funkcji dostępnych przez Being
        available_functions = await calc_being.list_available_functions()
        print(f"📋 Funkcje dostępne przez Being: {len(available_functions)}")
        
        # Testuj funkcje przez Being
        being_result1 = await calc_being.execute_soul_function("dodaj", 33, 77)
        if being_result1.get('success'):
            print(f"🤖 Being calc: 33 + 77 = {being_result1['data']['result']}")
        
        being_result2 = await calc_being.execute_soul_function("odejmij", 100, 25)
        if being_result2.get('success'):
            print(f"🤖 Being calc: 100 - 25 = {being_result2['data']['result']}")
            
        # Test funkcji init i execute
        init_result = await calc_being.execute_soul_function("init", being_context={"alias": calc_being.alias})
        if init_result.get('success'):
            print(f"🔧 Init result: {init_result['data']['result']}")
            
        execute_result = await calc_being.execute_soul_function("execute", data={
            "operacja": "pomnoz", 
            "a": 12, 
            "b": 9
        })
        if execute_result.get('success'):
            print(f"⚡ Execute result: {execute_result['data']['result']}")
    
    # 5. Test walidacji funkcji
    print(f"\n5. ✅ Test walidacji wywołań funkcji...")
    
    # Prawidłowe wywołanie
    errors1 = calculator_soul.validate_function_call("dodaj", 5, 10)
    print(f"Walidacja 'dodaj(5, 10)': {len(errors1)} błędów")
    
    # Nieprawidłowe wywołanie - nieistniejąca funkcja
    errors2 = calculator_soul.validate_function_call("nieistniejaca_funkcja", 1, 2)
    print(f"Walidacja 'nieistniejaca_funkcja': {len(errors2)} błędów")
    if errors2:
        print(f"   Błąd: {errors2[0]}")
    
    # 6. Test informacji o funkcjach
    print(f"\n6. ℹ️ Informacje o funkcjach...")
    
    dodaj_info = calculator_soul.get_function_info("dodaj")
    if dodaj_info:
        print(f"Funkcja 'dodaj': {dodaj_info.get('description', 'Brak opisu')}")
        print(f"   Typ: {dodaj_info.get('py_type')}")
        print(f"   Async: {dodaj_info.get('is_async', False)}")
    
    # 7. Test specjalnych funkcji Soul
    print(f"\n7. 🔧 Test specjalnych funkcji Soul...")
    
    print(f"Ma funkcję init: {calculator_soul.has_init_function()}")
    print(f"Ma funkcję execute: {calculator_soul.has_execute_function()}")
    print(f"Ma module_source: {calculator_soul.has_module_source()}")
    
    # Test auto-init
    if calculator_soul.has_init_function():
        auto_init_result = await calculator_soul.auto_init({"test": "context"})
        print(f"🔧 Auto-init result: {auto_init_result.get('success', False)}")
    
    print(f"\n✨ Demo zakończone pomyślnie!")
    print(f"\n🎯 Kluczowe odkrycia:")
    print(f"   • Soul automatycznie rozpoznaje funkcje z module_source")
    print(f"   • Funkcje publiczne (bez _) są dostępne przez Being")
    print(f"   • Funkcje prywatne (z _) są dostępne tylko wewnętrznie")
    print(f"   • System waliduje wywołania funkcji")
    print(f"   • init i execute to specjalne funkcje orkiestratora")

if __name__ == "__main__":
    asyncio.run(demo_funkcje_soul())
