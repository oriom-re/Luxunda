
"""
Demo automatycznej serializacji JSONB na podstawie schematu Soul
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.utils.serializer import JSONBSerializer


async def demo_automatic_serialization():
    """Demonstracja automatycznej serializacji"""
    
    print("🧬 Demo automatycznej serializacji JSONB")
    print("=" * 50)
    
    # 1. Utwórz genotyp z różnymi typami danych
    genotype = {
        "genesis": {
            "name": "user_profile",
            "version": "1.0",
            "description": "Profil użytkownika z automatyczną serializacją"
        },
        "attributes": {
            "name": {"py_type": "str"},
            "age": {"py_type": "int"},
            "height": {"py_type": "float"},
            "is_active": {"py_type": "bool"},
            "skills": {"py_type": "List[str]"},
            "scores": {"py_type": "List[float]"},
            "preferences": {"py_type": "dict"},
            "joined_date": {"py_type": "datetime"},
            "balance": {"py_type": "decimal"}
        }
    }
    
    # 2. Utwórz Soul
    soul = await Soul.create(genotype, alias="user_profile_demo")
    print(f"✅ Utworzono Soul: {soul.alias}")
    
    # 3. Surowe dane (różne typy jako stringi)
    raw_data = {
        "name": "Jan Kowalski",
        "age": "28",  # String -> int
        "height": "175.5",  # String -> float
        "is_active": "true",  # String -> bool
        "skills": '["Python", "JavaScript", "SQL"]',  # JSON string -> List[str]
        "scores": '["85.5", "92.0", "78.5"]',  # JSON string -> List[float]
        "preferences": '{"theme": "dark", "notifications": true}',  # JSON string -> dict
        "joined_date": "2023-01-15T10:30:00",  # ISO string -> datetime
        "balance": "1234.56"  # String -> decimal
    }
    
    print("\n📥 Surowe dane:")
    for key, value in raw_data.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # 4. Automatyczna serializacja
    serialized_data = JSONBSerializer.serialize_being_data(raw_data, soul)
    
    print("\n🔄 Po serializacji:")
    for key, value in serialized_data.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # 5. Utwórz Being z automatyczną serializacją
    being = await Being.create(
        soul_hash=soul.soul_hash,
        alias="jan_kowalski",
        data=raw_data  # Surowe dane - będą automatycznie zserializowane
    )
    
    print(f"\n✅ Utworzono Being: {being.alias}")
    print(f"📊 Zserializowane dane w Being:")
    for key, value in being.data.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # 6. Test deserializacji
    deserialized_data = being.deserialize_data()
    
    print(f"\n🔙 Po deserializacji:")
    for key, value in deserialized_data.items():
        print(f"  {key}: {value} ({type(value).__name__})")
    
    # 7. Test aktualizacji z automatyczną serializacją
    update_data = {
        "age": "29",  # String -> int
        "skills": '["Python", "JavaScript", "SQL", "Docker"]',  # Dodanie nowej umiejętności
        "balance": "1500.75"  # String -> decimal
    }
    
    print(f"\n📝 Aktualizacja danych:")
    success = await being.update_data(update_data)
    
    if success:
        print(f"✅ Dane zaktualizowane pomyślnie")
        print(f"📊 Zaktualizowane dane:")
        for key, value in being.data.items():
            print(f"  {key}: {value} ({type(value).__name__})")
    
    # 8. Test walidacji i serializacji
    print(f"\n🔍 Test walidacji i serializacji:")
    
    # Poprawne dane
    valid_test_data = {
        "name": "Anna Nowak",
        "age": "32",
        "is_active": "false"
    }
    
    serialized, errors = await being.validate_and_serialize_data(valid_test_data)
    print(f"Walidacja poprawnych danych - błędy: {len(errors)}")
    
    # Niepoprawne dane (wiek jako tekst)
    invalid_test_data = {
        "name": "Test User",
        "age": "trzydzieści",  # Nie da się skonwertować na int
        "is_active": "yes"
    }
    
    try:
        serialized, errors = JSONBSerializer.validate_and_serialize(invalid_test_data, soul)
        print(f"Walidacja niepoprawnych danych - błędy: {len(errors)}")
        if errors:
            print(f"  Błędy: {errors}")
    except Exception as e:
        print(f"  Błąd serializacji: {e}")
    
    print(f"\n🎉 Demo zakończone pomyślnie!")


if __name__ == "__main__":
    asyncio.run(demo_automatic_serialization())
