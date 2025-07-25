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
from app_v2.database.db_manager import init_database
from app_v2.database.soul_repository import SoulRepository

async def main():
    """Główna funkcja testowa"""
    print("🚀 Uruchamianie testów app_v2...")
    
    # 0. Inicjalizacja bazy danych
    print("\n🔄 Inicjalizacja bazy danych...")
    await init_database()

    # 1. Test rejestracji modułów
    print("\n📝 Test 1: Rejestracja modułów z plików")
    registered_count = await ModuleRegistry.register_all_modules_from_directory("app_v2/gen_files")
    print(f"Zarejestrowano {registered_count} modułów")
    
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
    
    print("\n✅ Wszystkie testy zakończone!")

if __name__ == "__main__":
    asyncio.run(main())
