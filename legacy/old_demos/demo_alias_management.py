
#!/usr/bin/env python3
"""
🏛️ Demo zarządzania aliasami przez Registry Being
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core import genotype_system

async def main():
    print("🏛️ Demo Registry Alias Management")
    print("=" * 50)

    # 1. Inicjalizuj system
    print("1. 🧬 Initializing genotype system...")
    result = await genotype_system.initialize_system()
    if not result["success"]:
        print(f"❌ Failed: {result['error']}")
        return
    print(f"   ✅ Loaded {result['loaded_souls_count']} genotypes")

    # 2. Utwórz registry being (singleton)
    print("\n2. 🏛️ Getting registry being...")
    registry_being = await Being.get_or_create(
        soul_hash=None,
        alias="system_registry",  # To znajdzie istniejący lub utworzy nowy
        unique_by="soul_hash"
    )
    print(f"   ✅ Registry: {registry_being.ulid}")

    # 3. Utwórz pierwszą wersję Soul "message"
    print("\n3. 📝 Creating message soul v1.0...")
    message_soul_v1 = await Soul.create({
        "genesis": {
            "name": "message",
            "type": "message_soul",
            "version": "1.0.0",
            "description": "Simple message handler"
        },
        "attributes": {
            "content": {"py_type": "str", "default": ""},
            "author": {"py_type": "str", "default": "anonymous"}
        }
    }, alias="message")
    
    print(f"   ✅ Message Soul v1.0: {message_soul_v1.soul_hash[:8]}...")

    # 4. Zarejestruj alias w registry
    print("\n4. 📋 Registering alias 'message' in registry...")
    register_result = await registry_being.execute_soul_function(
        "register_alias_mapping",
        alias="message",
        soul_hash=message_soul_v1.soul_hash
    )
    
    if register_result.get('success'):
        print(f"   ✅ Alias registered: message → {message_soul_v1.soul_hash[:8]}...")
    else:
        print(f"   ❌ Registration failed: {register_result}")
        return

    # 5. Test: Utwórz Being przez alias (delegacja do registry)
    print("\n5. 🤖 Creating being via alias delegation...")
    message_being1 = await Being.create(
        alias="message",  # TYLKO alias - to wyzwoli delegację do registry!
        attributes={"content": "Hello from v1.0!", "author": "Alice"}
    )
    print(f"   ✅ Created being via alias: {message_being1.ulid}")
    print(f"   📄 Content: {message_being1.data.get('content')}")

    # 6. Utwórz nową wersję Soul "message" 
    print("\n6. 🆕 Creating message soul v2.0...")
    message_soul_v2 = await Soul.create({
        "genesis": {
            "name": "message", 
            "type": "message_soul",
            "version": "2.0.0",
            "description": "Enhanced message handler with timestamp",
            "parent_hash": message_soul_v1.soul_hash  # Ewolucja!
        },
        "attributes": {
            "content": {"py_type": "str", "default": ""},
            "author": {"py_type": "str", "default": "anonymous"},
            "timestamp": {"py_type": "str", "default": "2025-01-30T00:00:00"}  # NOWE!
        }
    }, alias="message")  # Ten sam alias!
    
    print(f"   ✅ Message Soul v2.0: {message_soul_v2.soul_hash[:8]}...")

    # 7. Aktualizuj mapowanie aliasu w registry
    print("\n7. 🔄 Updating alias mapping to v2.0...")
    update_result = await registry_being.execute_soul_function(
        "update_alias_mapping",
        alias="message",
        new_soul_hash=message_soul_v2.soul_hash
    )
    
    if update_result.get('success'):
        print(f"   ✅ Alias updated: message → {message_soul_v2.soul_hash[:8]}...")
        print(f"   📜 Previous hash: {update_result['data']['previous_hash'][:8] if update_result['data']['previous_hash'] else 'None'}...")
    else:
        print(f"   ❌ Update failed: {update_result}")

    # 8. Test: Nowy Being przez alias używa teraz v2.0!
    print("\n8. 🆕 Creating new being via alias (should use v2.0)...")
    message_being2 = await Being.create(
        alias="message",  # Ten sam alias, ale teraz wskazuje na v2.0!
        attributes={
            "content": "Hello from v2.0!", 
            "author": "Bob",
            "timestamp": "2025-01-30T12:00:00"  # Nowy atrybut!
        }
    )
    print(f"   ✅ Created being via alias: {message_being2.ulid}")
    print(f"   📄 Content: {message_being2.data.get('content')}")
    print(f"   🕐 Timestamp: {message_being2.data.get('timestamp')}")

    # 9. Porównanie - stary Being używa v1.0, nowy v2.0
    print("\n9. 📊 Comparison:")
    print(f"   Being1 (v1.0): {message_being1.soul_hash[:8]}... - {message_being1.data}")
    print(f"   Being2 (v2.0): {message_being2.soul_hash[:8]}... - {message_being2.data}")

    # 10. Test: Bezpośredni dostęp do konkretnej wersji przez hash
    print("\n10. 🎯 Direct access to specific version via hash...")
    message_being_v1_direct = await Being.create(
        soul_hash=message_soul_v1.soul_hash,  # Konkretny hash = konkretna wersja
        attributes={"content": "Direct v1.0 access", "author": "Charlie"}
    )
    print(f"    ✅ Direct v1.0 being: {message_being_v1_direct.ulid}")
    print(f"    📄 Uses old schema: {list(message_being_v1_direct.data.keys())}")

    print("\n🎉 Alias management demo completed!")
    print("\nKey Benefits:")
    print("- 🔄 Alias 'message' zawsze wskazuje na najnowszą wersję")
    print("- 🎯 Hash pozwala na dostęp do konkretnej wersji") 
    print("- 🏛️ Registry centralizuje zarządzanie aliasami")
    print("- 📜 Historia zmian jest zachowana")

if __name__ == "__main__":
    asyncio.run(main())
