
#!/usr/bin/env python3
"""
⚡ LuxOS Quick Test
==================

Szybki test sprawdzający czy system działa poprawnie
"""

import asyncio
from luxdb.core.luxdb import LuxDB
from luxdb.models.soul import Soul
from luxdb.models.being import Being

async def quick_test():
    """Szybki test systemu"""
    print("⚡ LuxOS Quick Test")
    print("-" * 20)
    
    try:
        # 1. Test połączenia z bazą
        print("1. 📊 Testing database connection...")
        db = LuxDB(use_existing_pool=True)
        await db.initialize()
        health = await db.health_check()
        print(f"   Status: {health['status']}")
        
        # 2. Test tworzenia Soul
        print("2. 🧬 Testing Soul creation...")
        simple_genotype = {
            "genesis": {"name": "quick_test", "version": "1.0.0"},
            "module_source": "def greet(name): return f'Hello, {name}!'"
        }
        soul = await Soul.create(simple_genotype, "quick_test_soul")
        print(f"   Soul hash: {soul.soul_hash[:16]}...")
        
        # 3. Test wykonania funkcji
        print("3. ⚙️ Testing function execution...")
        result = await soul.execute_directly("greet", name="World")
        print(f"   Result: {result['data']['result']}")
        
        # 4. Test tworzenia Being
        print("4. 🤖 Testing Being creation...")
        being = await Being.create(soul, alias="quick_test_being")
        print(f"   Being ULID: {being.ulid[:8]}...")
        
        print("\n✅ Quick test completed successfully!")
        await db.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    print(f"\nResult: {'PASS' if success else 'FAIL'}")
