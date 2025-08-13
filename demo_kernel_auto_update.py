
#!/usr/bin/env python3
"""
🧠 Demo automatycznego aktualizowania aliasów przez Intelligent Kernel
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core import genotype_system
from luxdb.core.intelligent_kernel import intelligent_kernel

async def main():
    print("🧠 Demo Kernel Auto-Update Aliasów")
    print("=" * 50)

    # 1. Inicjalizuj system
    print("1. 🧬 Initializing system...")
    result = await genotype_system.initialize_system()
    if not result["success"]:
        print(f"❌ Failed: {result['error']}")
        return

    # Inicjalizuj Kernel
    await intelligent_kernel.initialize()

    # 2. Utwórz pierwszą wersję Soul "calculator"
    print("\n2. 📊 Creating calculator soul v1.0...")
    calc_soul_v1 = await Soul.create({
        "genesis": {
            "name": "calculator",
            "type": "calculator_soul", 
            "version": "1.0.0",
            "description": "Basic calculator"
        },
        "attributes": {
            "precision": {"py_type": "int", "default": 2},
            "operations": {"py_type": "list", "default": ["add", "subtract"]}
        },
        "module_source": '''
def init(being_context=None):
    return {"ready": True, "version": "1.0.0"}

def execute(request=None, being_context=None, **kwargs):
    a = request.get('a', 0)
    b = request.get('b', 0)
    op = request.get('operation', 'add')
    
    if op == 'add':
        return {"result": a + b, "version": "1.0.0"}
    elif op == 'subtract':
        return {"result": a - b, "version": "1.0.0"}
    else:
        return {"error": "Unknown operation", "version": "1.0.0"}
'''
    }, alias="calculator_v1")
    
    print(f"   ✅ Calculator v1.0: {calc_soul_v1.soul_hash[:8]}...")

    # 3. Setup auto-update alias
    print("\n3. 🔄 Setting up auto-update alias 'calc_latest'...")
    auto_result = await intelligent_kernel.setup_auto_update_alias(
        alias="calc_latest",
        base_name="calculator"
    )
    
    if auto_result.get("success"):
        print(f"   ✅ Auto-update alias setup successful")
        print(f"   📌 Current version: {auto_result['current_version']}")
    else:
        print(f"   ❌ Setup failed: {auto_result}")
        return

    # 4. Test używania aliasu
    print("\n4. 🧮 Testing current alias...")
    being1 = await intelligent_kernel.create_being_by_alias("calc_latest")
    result1 = await being1.execute_soul_function("execute", a=10, b=5, operation="add")
    print(f"   📊 10 + 5 = {result1.get('data', {}).get('result')} (version: {result1.get('data', {}).get('version')})")

    # 5. Utwórz nową wersję calculator (v2.0)
    print("\n5. 🆕 Creating calculator soul v2.0...")
    calc_soul_v2 = await Soul.create({
        "genesis": {
            "name": "calculator",  # Ta sama nazwa!
            "type": "calculator_soul",
            "version": "2.0.0", 
            "description": "Advanced calculator with multiplication",
            "parent_hash": calc_soul_v1.soul_hash
        },
        "attributes": {
            "precision": {"py_type": "int", "default": 4},
            "operations": {"py_type": "list", "default": ["add", "subtract", "multiply", "divide"]}
        },
        "module_source": '''
def init(being_context=None):
    return {"ready": True, "version": "2.0.0", "enhanced": True}

def execute(request=None, being_context=None, **kwargs):
    a = request.get('a', 0)
    b = request.get('b', 0)
    op = request.get('operation', 'add')
    
    if op == 'add':
        return {"result": a + b, "version": "2.0.0"}
    elif op == 'subtract':
        return {"result": a - b, "version": "2.0.0"}
    elif op == 'multiply':
        return {"result": a * b, "version": "2.0.0"}
    elif op == 'divide':
        if b != 0:
            return {"result": a / b, "version": "2.0.0"}
        else:
            return {"error": "Division by zero", "version": "2.0.0"}
    else:
        return {"error": "Unknown operation", "version": "2.0.0"}
'''
    }, alias="calculator_v2")
    
    print(f"   ✅ Calculator v2.0: {calc_soul_v2.soul_hash[:8]}...")

    # 6. Auto-update alias do najnowszej wersji
    print("\n6. 🔄 Auto-updating alias to latest version...")
    update_result = await intelligent_kernel.auto_update_alias_to_latest(
        alias="calc_latest",
        base_name="calculator"
    )
    
    if update_result.get("success"):
        print(f"   ✅ Alias updated to version: {update_result['latest_version']}")
        print(f"   🔗 New hash: {update_result['soul_hash'][:8]}...")
    else:
        print(f"   ❌ Update failed: {update_result}")

    # 7. Test nowej wersji
    print("\n7. 🧮 Testing updated alias...")
    being2 = await intelligent_kernel.create_being_by_alias("calc_latest")
    result2 = await being2.execute_soul_function("execute", a=10, b=5, operation="multiply")
    print(f"   📊 10 * 5 = {result2.get('data', {}).get('result')} (version: {result2.get('data', {}).get('version')})")

    # 8. Test bezpośredniego dostępu do starych wersji
    print("\n8. 🎯 Testing direct access to old versions...")
    old_being = await intelligent_kernel.create_being_by_alias("calculator_v1")
    old_result = await old_being.execute_soul_function("execute", a=10, b=5, operation="multiply")
    print(f"   📊 v1.0 multiply test: {old_result.get('data', {})}")  # Powinno zwrócić error

    # 9. Status systemu
    print("\n9. 📋 System status...")
    status = await intelligent_kernel.get_system_status()
    print(f"   🧠 Active aliases: {list(status['registry_mappings'].keys())}")
    print(f"   🔄 Auto-update configs: {len(status.get('auto_update_configs', {}))}")

    print("\n🎉 Demo completed!")
    print("\nKey Benefits:")
    print("- 🔄 Alias 'calc_latest' automatycznie wskazuje najnowszą wersję")
    print("- 🎯 Stare wersje nadal dostępne przez konkretne aliasy")
    print("- 📜 Historia aktualizacji zachowana")
    print("- 🧠 Kernel zarządza wszystkim inteligentnie")

if __name__ == "__main__":
    asyncio.run(main())
