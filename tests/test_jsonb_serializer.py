#!/usr/bin/env python3
"""
🧪 Test systemu automatycznej serializacji JSONB
"""

import asyncio
import json
from datetime import datetime
from database.models.base import Soul
from luxdb.models.being import Being
from luxdb.utils.serializer import JSONBSerializer

async def test_jsonb_serialization():
    """Test kompletnego systemu serializacji"""
    print("🧪 Testowanie systemu automatycznej serializacji JSONB")

    # 1. Stwórz przykładowy genotyp Soul
    genotype = {
        "attributes": {
            "name": {
                "py_type": "str",
                "required": True,
                "description": "Nazwa użytkownika"
            },
            "age": {
                "py_type": "int",
                "required": False,
                "default": 0,
                "description": "Wiek użytkownika"
            },
            "registered_at": {
                "py_type": "datetime",
                "required": False,
                "description": "Data rejestracji"
            },
            "tags": {
                "py_type": "List[str]",
                "required": False,
                "default": [],
                "description": "Lista tagów"
            },
            "active": {
                "py_type": "bool",
                "required": False,
                "default": True,
                "description": "Czy użytkownik jest aktywny"
            },
            "metadata": {
                "py_type": "dict",
                "required": False,
                "default": {},
                "description": "Dodatkowe metadane"
            }
        }
    }

    # 2. Utwórz Soul
    try:
        soul = await Soul.create(genotype=genotype, alias="test_user")
        print(f"✅ Stworzono Soul: {soul.alias}")
    except Exception as e:
        print(f"❌ Błąd tworzenia Soul: {e}")
        return

    # 3. Przygotuj testowe dane
    test_data = {
        "name": "Jan Kowalski",
        "age": "25",  # String zamiast int - test konwersji
        "registered_at": "2024-01-15T10:30:00",  # String ISO datetime
        "tags": ["admin", "developer"],
        "active": "true",  # String zamiast bool - test konwersji
        "metadata": {"role": "superuser", "level": 5}
    }

    # 4. Test serializacji
    print("\n📝 Testowanie serializacji...")
    serialized_data, errors = JSONBSerializer.validate_and_serialize(test_data, soul)

    if errors:
        print(f"❌ Błędy walidacji: {errors}")
        return

    print(f"✅ Dane zserializowane:")
    print(json.dumps(serialized_data, indent=2, ensure_ascii=False))

    # 5. Test deserializacji
    print("\n📤 Testowanie deserializacji...")
    deserialized_data = JSONBSerializer.deserialize_being_data(serialized_data, soul)

    print(f"✅ Dane zdeserializowane:")
    for key, value in deserialized_data.items():
        print(f"  {key}: {value} ({type(value).__name__})")

    # 6. Test z Being
    print("\n🧬 Testowanie z klasą Being...")

    try:
        being = await Being.create(
            soul=soul,
            alias="test_user_instance",
            attributes=test_data
        )
        print(f"✅ Stworzono Being: {being.ulid}")
        print(f"✅ Dane Being po serializacji: {being.data}")

        # Test zapisu i ładowania
        await being.save()
        print(f"✅ Being zapisany do bazy")

        # Test ładowania
        loaded_being = await Being.load_by_ulid(being.ulid)
        if loaded_being:
            print(f"✅ Being załadowany z bazy")
            print(f"✅ Dane po deserializacji: {loaded_being.data}")

    except Exception as e:
        print(f"❌ Błąd testowania Being: {e}")
        import traceback
        traceback.print_exc()

    # 7. Test generowania JSON Schema
    print("\n📋 Testowanie generowania JSON Schema...")
    schema = JSONBSerializer.get_json_schema(soul)
    print(f"✅ JSON Schema wygenerowane:")
    print(json.dumps(schema, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(test_jsonb_serialization())