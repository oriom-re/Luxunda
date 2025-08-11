
#!/usr/bin/env python3
"""
🧪 Test systemu obsługi duplikowania Soul na podstawie hash
"""

import asyncio
import json
from luxdb.models.soul import Soul
from luxdb.utils.genotype_loader import GenotypeLoader

async def test_soul_hash_duplication():
    """Test czy Soul z identycznym hashem nie są duplikowane"""
    print("🧪 Test duplikowania Soul na podstawie hash")
    print("=" * 60)
    
    # 1. Załaduj genotyp z JSON
    print("\n📂 Ładowanie genotypu z JSON...")
    genotype_loader = GenotypeLoader()
    genotype = await genotype_loader.load_genotype("openai_client")
    
    if not genotype:
        print("❌ Nie udało się załadować genotypu!")
        return
    
    print(f"✅ Załadowano genotyp: {genotype.get('genesis', {}).get('name')}")
    
    # 2. Utwórz pierwszą Soul
    print("\n🧬 Tworzenie pierwszej Soul...")
    soul1 = await Soul.create(genotype, alias="openai_test_1")
    
    print(f"✅ Utworzono Soul 1:")
    print(f"   Hash: {soul1.soul_hash[:16]}...")
    print(f"   Alias: {soul1.alias}")
    print(f"   Functions: {len(soul1.list_functions())}")
    
    # 3. Próba utworzenia drugiej Soul z tym samym genotypem
    print("\n🔄 Próba utworzenia drugiej Soul z identycznym genotypem...")
    soul2 = await Soul.create(genotype, alias="openai_test_2")
    
    print(f"✅ Otrzymano Soul 2:")
    print(f"   Hash: {soul2.soul_hash[:16]}...")
    print(f"   Alias: {soul2.alias}")
    print(f"   Functions: {len(soul2.list_functions())}")
    
    # 4. Sprawdź czy to ta sama Soul
    print("\n🔍 Porównanie Soul...")
    
    if soul1.soul_hash == soul2.soul_hash:
        print("✅ Hash identyczne - system poprawnie zwrócił istniejącą Soul")
        
        if soul1 is soul2:
            print("✅ To dokładnie ten sam obiekt w pamięci")
        else:
            print("ℹ️  To różne obiekty w pamięci, ale z tym samym hashem")
            
        # Sprawdź który alias został zachowany
        print(f"📋 Zachowany alias: {soul2.alias}")
        if soul2.alias == "openai_test_2":
            print("✅ Alias został zaktualizowany na nowszy")
        elif soul2.alias == "openai_test_1":
            print("ℹ️  Zachowano oryginalny alias")
            
    else:
        print("❌ Hash różne - system niepoprawnie utworzył nową Soul!")
        print(f"   Soul1 hash: {soul1.soul_hash}")
        print(f"   Soul2 hash: {soul2.soul_hash}")
    
    # 5. Test z minimalnie zmienionym genotypem
    print("\n🔬 Test z lekko zmienionym genotypem...")
    modified_genotype = genotype.copy()
    modified_genotype["genesis"]["description"] = "Modified OpenAI client"
    
    soul3 = await Soul.create(modified_genotype, alias="openai_modified")
    
    print(f"✅ Utworzono Soul 3 ze zmienionym genotypem:")
    print(f"   Hash: {soul3.soul_hash[:16]}...")
    print(f"   Alias: {soul3.alias}")
    
    if soul3.soul_hash != soul1.soul_hash:
        print("✅ Zmieniony genotyp ma inny hash - poprawne!")
    else:
        print("❌ Zmieniony genotyp ma ten sam hash - błąd!")
    
    # 6. Test funkcji Soul
    print("\n⚡ Test wykonania funkcji...")
    
    # Test funkcji get_status
    result = await soul1.execute_function("get_status")
    if result.get('success'):
        print("✅ Funkcja get_status działa")
        print(f"   Status: {result.get('data', {}).get('result', {}).get('status')}")
    else:
        print(f"❌ Błąd funkcji get_status: {result.get('error')}")
    
    # Test funkcji init
    being_context = {
        'ulid': 'test_being_123',
        'alias': 'test_being',
        'data': {
            'api_key': 'test_key_123',
            'model': 'gpt-4-turbo'
        }
    }
    
    init_result = await soul1.execute_function("init", being_context=being_context)
    if init_result.get('success'):
        print("✅ Funkcja init działa")
        init_data = init_result.get('data', {}).get('result', {})
        print(f"   Initialized: {init_data.get('initialized')}")
        print(f"   Model: {init_data.get('model')}")
    else:
        print(f"❌ Błąd funkcji init: {init_result.get('error')}")
    
    print("\n🎯 Test zakończony!")
    
    return {
        'soul1_hash': soul1.soul_hash,
        'soul2_hash': soul2.soul_hash,
        'soul3_hash': soul3.soul_hash,
        'hashes_match_1_2': soul1.soul_hash == soul2.soul_hash,
        'hashes_match_1_3': soul1.soul_hash == soul3.soul_hash,
        'soul1_functions': soul1.list_functions(),
        'soul2_alias': soul2.alias
    }

async def main():
    """Główna funkcja testowa"""
    try:
        result = await test_soul_hash_duplication()
        
        print("\n📊 Podsumowanie testów:")
        print(f"   Hash Soul 1 i 2 identyczne: {result['hashes_match_1_2']}")
        print(f"   Hash Soul 1 i 3 różne: {not result['hashes_match_1_3']}")
        print(f"   Liczba funkcji w Soul: {len(result['soul1_functions'])}")
        print(f"   Funkcje: {', '.join(result['soul1_functions'])}")
        
        if result['hashes_match_1_2'] and not result['hashes_match_1_3']:
            print("\n🎉 Wszystkie testy przeszły pomyślnie!")
        else:
            print("\n⚠️  Niektóre testy nie przeszły - sprawdź implementację")
            
    except Exception as e:
        print(f"\n💥 Błąd podczas testów: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
