
#!/usr/bin/env python3
"""
🧬 Demo Eleganckiego API Soul - Nowa Filozofia LuxDB
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.core.postgre_db import Postgre_db

async def demo_elegant_soul_api():
    """Demonstracja nowego eleganckiego API Soul"""
    print("🧬 Demo Eleganckiego API Soul")
    print("=" * 50)
    
    # Inicjalizacja bazy danych
    await Postgre_db.initialize_db()
    
    # 1. Tworzenie Soul z prostą funkcją dodawania
    print("\n1. Tworzenie Soul 'dodawanie'...")
    
    dodawanie_genotype = {
        "genesis": {
            "name": "dodawanie",
            "type": "calculator",
            "version": "1.0.0",
            "description": "Prosta funkcja dodawania"
        },
        "attributes": {
            "result": {"py_type": "float", "description": "Wynik dodawania"}
        },
        "module_source": '''
def execute(data=None, **kwargs):
    """
    Główna funkcja publiczna - tylko ona jest dostępna zewnętrznie.
    Funkcje prywatne są ukryte.
    """
    if not data:
        return {"error": "Brak danych do dodawania"}
    
    a = data.get('a', 0)
    b = data.get('b', 0)
    
    # Wywołanie prywatnej funkcji
    result = _private_add(a, b)
    
    return {
        "operation": "addition",
        "a": a,
        "b": b, 
        "result": result,
        "message": f"{a} + {b} = {result}"
    }

def _private_add(x, y):
    """Prywatna funkcja dodawania - niedostępna zewnętrznie"""
    return x + y

def _private_multiply(x, y):  
    """Kolejna prywatna funkcja - również ukryta"""
    return x * y
'''
    }
    
    # Utwórz Soul tradycyjnie
    dodawanie_soul = await Soul.create(dodawanie_genotype, "dodawanie")
    print(f"✅ Created Soul: {dodawanie_soul.alias}")
    
    # 2. NOWE API: Eleganckie wykonanie
    print("\n2. Nowe eleganckie API...")
    
    # Styl 1: Bezpośrednie wykonanie
    print("\n🎯 Styl 1: Soul(alias).execute(data)")
    soul1 = Soul(alias="dodawanie")
    result1 = await soul1.execute(data={"a": 15, "b": 25})
    print(f"Result: {result1['data']['result']}")
    
    # Styl 2: Wykonanie przez hash  
    print("\n🎯 Styl 2: Soul().execute(hash=hash, data=data)")
    soul2 = Soul()
    result2 = await soul2.execute(hash=dodawanie_soul.soul_hash, data={"a": 100, "b": 200})
    print(f"Result: {result2['data']['result']}")
    
    # 3. Tworzenie Being z nowym API
    print("\n3. Tworzenie Being z eleganckiej składni...")
    
    message_genotype = {
        "genesis": {
            "name": "message",
            "type": "data_container",
            "version": "1.0.0"
        },
        "attributes": {
            "title": {"py_type": "str"},
            "content": {"py_type": "str"},
            "author": {"py_type": "str"}
        },
        "module_source": '''
def init(being_context=None, **kwargs):
    """Inicjalizacja Being"""
    return {
        "initialized": True,
        "being_ulid": being_context.get('ulid') if being_context else None,
        "message": "Message Being ready"
    }

def execute(data=None, **kwargs):
    """Execute dla Message Being"""
    return {
        "processed_message": data,
        "timestamp": "2025-01-30",
        "status": "processed"
    }
'''
    }
    
    message_soul = await Soul.create(message_genotype, "message")
    print(f"✅ Created Message Soul: {message_soul.alias}")
    
    # NOWE API: init().set()
    print("\n🎯 Nowe API: Soul().init(alias, data).set()")
    
    soul3 = Soul(alias="message") 
    lazy_creator = await soul3.init(
        alias="my_message_001",
        data={
            "title": "Test Message",
            "content": "To jest testowa wiadomość",
            "author": "LuxDB System"
        }
    )
    
    creation_result = await lazy_creator.set()
    print(f"Being created: {creation_result['success']}")
    if creation_result['success']:
        being_data = creation_result['data']['being']
        print(f"Being ULID: {being_data['ulid']}")
    
    print("\n🎯 Demonstracja funkcji publicznych vs prywatnych")
    print("✅ Publiczne: execute() - dostępne zewnętrznie")
    print("❌ Prywatne: _private_add(), _private_multiply() - tylko wewnętrzne")
    
    # Sprawdź dostępne funkcje
    functions_info = dodawanie_soul.get_available_functions_clear()
    print(f"\nDostępne funkcje publiczne: {len([f for f in functions_info if not f.startswith('[')])}")
    print(f"Funkcje prywatne (ukryte): {len([f for f in functions_info if f.startswith('[PRIVATE]')])}")

if __name__ == "__main__":
    asyncio.run(demo_elegant_soul_api())
