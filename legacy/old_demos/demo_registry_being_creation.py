
#!/usr/bin/env python3
"""
🏛️ Demo tworzenia bytów przez registry (bez wiedzy Being o rejestrze)
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core import genotype_system

async def main():
    print("🏛️ Demo Registry Being Creation System")
    print("=" * 50)

    # 1. Inicjalizuj system genotypów
    print("1. 🧬 Initializing genotype system...")
    result = await genotype_system.initialize_system()
    if not result["success"]:
        print(f"❌ Failed: {result['error']}")
        return
    print(f"   ✅ Loaded {result['loaded_souls_count']} genotypes")

    # 2. Utwórz registry being
    print("\n2. 🏛️ Creating registry being...")
    registry_soul = await Soul.get_by_alias("soul_registry")
    if not registry_soul:
        print("❌ Registry soul not found")
        return
    
    registry_being = await Being.create(soul=registry_soul, persistent=True)
    print(f"   ✅ Registry being created: {registry_being.ulid}")

    # 3. Zarejestruj alias w registry
    print("\n3. 📋 Registering alias 'test_soul' in registry...")
    test_soul = await Soul.get_by_alias("test_soul")
    if not test_soul:
        print("❌ test_soul not found")
        return
    
    register_result = await registry_being.execute_soul_function(
        "execute",
        request={
            "action": "register_alias",
            "alias": "test_soul",
            "soul_hash": test_soul.soul_hash
        }
    )
    
    if register_result.get('success'):
        print(f"   ✅ Alias registered: test_soul → {test_soul.soul_hash[:8]}...")
    else:
        print(f"   ❌ Registration failed: {register_result}")
        return

    # 4. Poproś registry o utworzenie Being przez alias
    print("\n4. 🤖 Requesting registry to create being by alias...")
    create_result = await registry_being.execute_soul_function(
        "execute",
        request={
            "action": "create_being_by_alias",
            "alias": "test_soul",
            "attributes": {"content": "Hello from registry-created being!"},
            "persistent": True
        }
    )
    
    if create_result.get('success'):
        being_ulid = create_result['data']['being_ulid']
        print(f"   ✅ Registry created being: {being_ulid}")
        print(f"   📄 Details: {create_result['data']}")
        
        # 5. Sprawdź czy Being rzeczywiście istnieje
        print("\n5. 🔍 Verifying created being...")
        created_being = await Being.get_by_ulid(being_ulid)
        if created_being:
            print(f"   ✅ Being exists: {created_being.alias}")
            print(f"   📄 Data: {created_being.data}")
        else:
            print("   ❌ Being not found")
    else:
        print(f"   ❌ Creation failed: {create_result}")

    print("\n🎉 Registry being creation demo completed!")

if __name__ == "__main__":
    asyncio.run(main())
