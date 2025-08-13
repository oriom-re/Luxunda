
#!/usr/bin/env python3
"""
🏛️ Demo delegacji Being.create(alias=...) do registry
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core import genotype_system

async def main():
    print("🏛️ Demo Registry Delegation System")
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

    # 3. Test delegacji - Being.create(alias=...) 
    print("\n3. 🔄 Testing delegation: Being.create(alias='test_soul')...")
    
    try:
        # To powinno być delegowane do registry!
        message_being = await Being.create(
            alias="test_soul",  # Tylko alias - bez soul object!
            attributes={"content": "Hello from registry delegation!"}
        )
        
        print(f"   ✅ Being created via registry: {message_being.ulid}")
        print(f"   📄 Being data: {message_being.data}")
        
    except Exception as e:
        print(f"   ❌ Delegation failed: {e}")

    # 4. Sprawdź rejestr
    print("\n4. 📋 Checking registry records...")
    registry_info = await registry_being.execute_soul_function("get_being_info", message_being.ulid)
    if registry_info.get('success'):
        print(f"   ✅ Being found in registry: {registry_info['data']}")
    else:
        print("   ❌ Being not found in registry")

    print("\n🎉 Registry delegation demo completed!")

if __name__ == "__main__":
    asyncio.run(main())
