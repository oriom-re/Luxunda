
#!/usr/bin/env python3
"""
🎯 Demo systemu automatycznej serializacji JSONB
"""

import asyncio
import json
from datetime import datetime
from database.models.base import Soul
from luxdb.models.being import Being
from luxdb.utils.serializer import JSONBSerializer

async def main():
    """Demo automatycznej serializacji"""
    print("🎯 Demo systemu automatycznej serializacji JSONB dla LuxDB")
    print("=" * 60)
    
    # Przykład 1: User Profile
    print("\n📝 Przykład 1: Profil użytkownika")
    user_genotype = {
        "attributes": {
            "username": {"py_type": "str", "required": True},
            "email": {"py_type": "str", "required": True},
            "age": {"py_type": "int", "required": False, "default": 18},
            "created_at": {"py_type": "datetime", "required": False},
            "preferences": {"py_type": "dict", "required": False, "default": {}},
            "tags": {"py_type": "List[str]", "required": False, "default": []},
            "is_active": {"py_type": "bool", "required": False, "default": True}
        }
    }
    
    user_soul = await Soul.create(genotype=user_genotype, alias="user_profile")
    
    user_data = {
        "username": "lux_developer",
        "email": "dev@luxdb.ai",
        "age": "28",  # String będzie przekonwertowany na int
        "created_at": datetime.now(),
        "preferences": {"theme": "dark", "language": "pl"},
        "tags": ["developer", "ai_enthusiast"],
        "is_active": "true"  # String będzie przekonwertowany na bool
    }
    
    user_being = await Being.create(
        soul=user_soul,
        alias="developer_profile",
        attributes=user_data
    )
    
    print(f"✅ Stworzono User Being: {user_being.ulid}")
    print(f"📊 Zserializowane dane: {json.dumps(user_being.data, indent=2, ensure_ascii=False, default=str)}")
    
    # Przykład 2: Product Catalog
    print("\n🛍️ Przykład 2: Katalog produktów")
    product_genotype = {
        "attributes": {
            "name": {"py_type": "str", "required": True},
            "price": {"py_type": "float", "required": True},
            "category": {"py_type": "str", "required": True},
            "in_stock": {"py_type": "bool", "required": False, "default": True},
            "specifications": {"py_type": "dict", "required": False, "default": {}},
            "tags": {"py_type": "List[str]", "required": False, "default": []},
            "ratings": {"py_type": "List[float]", "required": False, "default": []}
        }
    }
    
    product_soul = await Soul.create(genotype=product_genotype, alias="product")
    
    product_data = {
        "name": "LuxDB Pro License",
        "price": "99.99",  # String będzie przekonwertowany na float
        "category": "software",
        "in_stock": True,
        "specifications": {
            "max_beings": 10000,
            "vector_search": True,
            "ai_integration": True
        },
        "tags": ["database", "ai", "professional"],
        "ratings": [4.8, 4.9, 5.0, 4.7]
    }
    
    product_being = await Being.create(
        soul=product_soul,
        alias="luxdb_pro",
        attributes=product_data
    )
    
    print(f"✅ Stworzono Product Being: {product_being.ulid}")
    print(f"📊 Zserializowane dane: {json.dumps(product_being.data, indent=2, ensure_ascii=False, default=str)}")
    
    # Przykład 3: Event Log
    print("\n📋 Przykład 3: Log wydarzeń")
    event_genotype = {
        "attributes": {
            "event_type": {"py_type": "str", "required": True},
            "timestamp": {"py_type": "datetime", "required": True},
            "user_id": {"py_type": "str", "required": False},
            "data": {"py_type": "dict", "required": False, "default": {}},
            "severity": {"py_type": "str", "required": False, "default": "info"},
            "processed": {"py_type": "bool", "required": False, "default": False}
        }
    }
    
    event_soul = await Soul.create(genotype=event_genotype, alias="event_log")
    
    event_data = {
        "event_type": "user_login",
        "timestamp": "2024-01-15T14:30:00Z",
        "user_id": user_being.ulid,
        "data": {
            "ip_address": "192.168.1.100",
            "user_agent": "LuxDB-Client/1.0",
            "success": True
        },
        "severity": "info",
        "processed": False
    }
    
    event_being = await Being.create(
        soul=event_soul,
        alias="login_event",
        attributes=event_data
    )
    
    print(f"✅ Stworzono Event Being: {event_being.ulid}")
    print(f"📊 Zserializowane dane: {json.dumps(event_being.data, indent=2, ensure_ascii=False, default=str)}")
    
    # Test ładowania i deserializacji
    print("\n🔄 Test ładowania z automatyczną deserializacją")
    
    loaded_user = await Being.load_by_ulid(user_being.ulid)
    if loaded_user:
        await loaded_user.load_full_data()
        print(f"✅ Załadowano User Being z bazy")
        print(f"🔍 Sprawdzenie typów po deserializacji:")
        for key, value in loaded_user.data.items():
            print(f"  {key}: {value} ({type(value).__name__})")
    
    print("\n🎉 Demo zakończone pomyślnie!")
    print("✨ System automatycznej serializacji działa!")

if __name__ == "__main__":
    asyncio.run(main())
