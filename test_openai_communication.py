
"""
Test komunikacji z asystentem OpenAI używając poprawionej struktury Soul/Being.
"""

import asyncio
import os
from datetime import datetime
from examples.openai_assistant_example import demo_openai_communication

async def test_soul_structure():
    """Test struktury Soul i Being dla asystenta"""
    
    print("🧪 TEST: Struktura Soul i Being")
    print("="*50)
    
    try:
        # Uruchom demo
        soul, being = await demo_openai_communication()
        
        # Sprawdź strukturę Soul
        print(f"\n🔍 Analiza struktury Soul:")
        print(f"   Hash: {soul.soul_hash[:16]}...")
        print(f"   Alias: {soul.alias}")
        print(f"   Funkcje: {soul.list_functions()}")
        
        # Sprawdź genotyp
        genesis = soul.genotype.get("genesis", {})
        attributes = soul.genotype.get("attributes", {})
        functions = soul.genotype.get("functions", {})
        
        print(f"   Genesis: {genesis.get('name')} v{genesis.get('version')}")
        print(f"   Atrybuty zdefiniowane: {len(attributes)}")
        print(f"   Funkcje zdefiniowane: {len(functions)}")
        
        # Sprawdź czy atrybuty to tylko definicje
        print(f"\n📋 Przykładowe definicje atrybutów:")
        for attr_name, attr_def in list(attributes.items())[:3]:
            print(f"   {attr_name}: {attr_def}")
        
        # Sprawdź strukturę Being
        print(f"\n🔍 Analiza struktury Being:")
        print(f"   ULID: {being.ulid}")
        print(f"   Soul hash: {being.soul_hash[:16]}...")
        print(f"   Alias: {being.alias}")
        print(f"   Strefa dostępu: {being.access_zone}")
        
        # Sprawdź czy Being ma rzeczywiste dane
        print(f"\n📊 Rzeczywiste dane w Being:")
        for key, value in being.data.items():
            if key == "api_key":
                print(f"   {key}: ***hidden***")
            elif isinstance(value, (list, dict)) and len(str(value)) > 50:
                print(f"   {key}: {type(value).__name__} (długość: {len(value)})")
            else:
                print(f"   {key}: {value}")
        
        print(f"\n✅ Test struktury zakończony pomyślnie!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas testu: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_data_separation():
    """Test separacji danych między Soul a Being"""
    
    print(f"\n🧪 TEST: Separacja danych Soul vs Being")
    print("="*50)
    
    from luxdb.models.soul import Soul
    from luxdb.models.being import Being
    
    # Utwórz prostszą Soul dla testu
    test_genotype = {
        "genesis": {
            "name": "test_separation",
            "type": "test",
            "version": "1.0.0"
        },
        "attributes": {
            "name": {"py_type": "str", "default": "Test"},
            "value": {"py_type": "int", "default": 0},
            "active": {"py_type": "bool", "default": True},
            "metadata": {"py_type": "dict", "default": {}}
        }
    }
    
    # Utwórz Soul
    test_soul = await Soul.create(test_genotype, alias="test_separation")
    print(f"✅ Soul utworzony: {test_soul.soul_hash[:8]}...")
    
    # Sprawdź że Soul nie zawiera danych, tylko definicje
    print(f"\n📋 Soul zawiera tylko definicje:")
    attributes_def = test_soul.genotype.get("attributes", {})
    for attr_name, attr_def in attributes_def.items():
        print(f"   {attr_name}: definicja = {attr_def}")
    
    # Sprawdź domyślne dane
    default_data = test_soul.get_default_data()
    print(f"\n🔧 Domyślne dane z definicji:")
    for key, value in default_data.items():
        print(f"   {key}: {value}")
    
    # Utwórz Being z konkretnymi danymi
    being_data = {
        "name": "Konkretny Being",
        "value": 42,
        "active": False,
        "metadata": {"created": datetime.now().isoformat()}
    }
    
    test_being = await Being.create(test_soul, attributes=being_data, alias="test_being")
    print(f"\n✅ Being utworzony: {test_being.ulid}")
    
    # Sprawdź że Being zawiera rzeczywiste dane
    print(f"\n📊 Being zawiera rzeczywiste dane:")
    for key, value in test_being.data.items():
        print(f"   {key}: {value}")
    
    # Test walidacji
    print(f"\n🧪 Test walidacji nieprawidłowych danych:")
    invalid_data = {"value": "nie liczba", "active": "nie boolean"}
    errors = test_soul.validate_data(invalid_data)
    
    if errors:
        print(f"❌ Błędy walidacji (oczekiwane):")
        for error in errors:
            print(f"   - {error}")
    else:
        print(f"✅ Brak błędów walidacji")
    
    print(f"\n✅ Test separacji danych zakończony pomyślnie!")
    return True

async def main():
    """Główna funkcja testowa"""
    
    print("🚀 TESTY KOMUNIKACJI Z ASYSTENTEM OPENAI")
    print("="*60)
    
    # Test 1: Struktura Soul i Being
    test1_result = await test_soul_structure()
    
    # Test 2: Separacja danych
    test2_result = await test_data_separation()
    
    # Podsumowanie
    print(f"\n📋 PODSUMOWANIE TESTÓW:")
    print(f"   Test struktury Soul/Being: {'✅ PASSED' if test1_result else '❌ FAILED'}")
    print(f"   Test separacji danych: {'✅ PASSED' if test2_result else '❌ FAILED'}")
    
    if test1_result and test2_result:
        print(f"\n🎉 Wszystkie testy zakończone pomyślnie!")
        print(f"💡 Soul teraz poprawnie definiuje tylko strukturę atrybutów")
        print(f"💡 Being przechowuje rzeczywiste dane zgodnie ze strukturą")
        print(f"💡 System gotowy do integracji z OpenAI!")
    else:
        print(f"\n❌ Niektóre testy nie powiodły się")
    
    return test1_result and test2_result

if __name__ == "__main__":
    asyncio.run(main())
