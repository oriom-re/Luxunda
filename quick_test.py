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
            "module_source": "def greet(name=\"World\"):\n    return f\"Hello, {name}! Test completed successfully.\""
        }
        soul = await Soul.create(simple_genotype, "quick_test_soul")
        print("📝 Soul creation report generated:", report_path)
        print(f"   Soul hash: {soul.soul_hash[:16]}...")
        print("3. ⚙️ Testing function execution...")

        # Test wykonania funkcji
        result = await soul.execute_function('greet', name="LuxOS")
        if result.get('success'):
            print(f"   Function result: {result['data']['result']}")
            print("✅ Quick test completed successfully!")
            return "PASS"
        else:
            print(f"❌ Quick test failed: {result.get('error')}")
            return "FAIL"

    except Exception as e:
        print(f"\n❌ Quick test failed: {e}")
        return "FAIL"

if __name__ == "__main__":
    success = asyncio.run(quick_test())
    print(f"\nResult: {success}")