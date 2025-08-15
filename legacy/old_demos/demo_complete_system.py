
#!/usr/bin/env python3
"""
🧬 LuxDB Complete System Demo - "Na otwartym sercu"
Pokazuje pełny cykl życia: Soul → Being → Functions → Evolution
"""

import asyncio
import json
from datetime import datetime
from luxdb.core.postgre_db import Postgre_db
from luxdb.models.soul import Soul
from luxdb.models.being import Being

async def demo_complete_cycle():
    """Kompletny cykl życia LuxDB"""
    
    print("🚀 LuxDB Complete Demo - Starting...")
    
    # 1. Inicjalizacja bazy
    await Postgre_db.initialize()
    print("✅ Database initialized")
    
    # 2. Utworzenie Soul z kodem
    calculator_code = '''
def add(a, b):
    """Dodaje dwie liczby"""
    return a + b

def multiply(a, b):
    """Mnoży dwie liczby"""  
    return a * b

def init(being_context):
    """Inicjalizacja calculatora"""
    print(f"Calculator {being_context['alias']} is ready!")
    return {"initialized": True, "capabilities": ["add", "multiply"]}

def execute(data):
    """Główna funkcja wykonawcza"""
    operation = data.get("operation")
    a = data.get("a", 0)
    b = data.get("b", 0)
    
    if operation == "add":
        return add(a, b)
    elif operation == "multiply":
        return multiply(a, b)
    else:
        return {"error": "Unknown operation"}
'''
    
    calculator_genotype = {
        "genesis": {
            "name": "smart_calculator",
            "version": "1.0.0",
            "description": "Inteligentny kalkulator z funkcjami"
        },
        "attributes": {
            "last_calculation": {"py_type": "str"},
            "calculation_count": {"py_type": "int", "default": 0}
        },
        "module_source": calculator_code
    }
    
    # 3. Tworzenie Soul
    calc_soul = await Soul.create(calculator_genotype, alias="smart_calculator")
    print(f"✅ Soul created: {calc_soul.alias} (functions: {calc_soul.get_functions_count()})")
    
    # 4. Tworzenie Being z atrybutami
    calc_being = await Being.create(
        soul=calc_soul,
        attributes={
            "last_calculation": "none",
            "calculation_count": 0
        },
        alias="calculator_master"
    )
    print(f"✅ Being created: {calc_being.alias}")
    print(f"🎯 Function master: {calc_being.is_function_master()}")
    
    # 5. Wykonywanie funkcji
    print("\n🔢 Testing calculations...")
    
    # Dodawanie
    result1 = await calc_being.execute_soul_function("add", a=5, b=3)
    print(f"add(5, 3) = {result1['data']['result']}")
    
    # Mnożenie  
    result2 = await calc_being.execute_soul_function("multiply", a=4, b=7)
    print(f"multiply(4, 7) = {result2['data']['result']}")
    
    # Inteligentne execute
    result3 = await calc_being.execute(data={
        "operation": "add",
        "a": 10,
        "b": 20
    })
    print(f"smart execute: add(10, 20) = {result3['data']['result']}")
    
    # 6. Sprawdzenie stanu Being
    await calc_being.save()
    print(f"\n📊 Being stats: {calc_being.get_function_mastery_info()}")
    
    # 7. Ewolucja - Being prosi o nowe możliwości
    evolution_request = await calc_being.request_evolution(
        "Need advanced math functions",
        new_capabilities={"advanced_math": True}
    )
    print(f"🧬 Evolution requested: {evolution_request['success']}")
    
    # 8. Tworzenie drugiego Being z tego samego Soul
    calc_being2 = await Being.create(
        soul=calc_soul,
        attributes={"calculation_count": 0},
        alias="calculator_backup"
    )
    print(f"✅ Second Being created: {calc_being2.alias}")
    
    # 9. Lista wszystkich Soul i Being
    all_souls = await Soul.get_all()
    all_beings = await Being.get_all()
    
    print(f"\n📈 System Summary:")
    print(f"   Souls: {len(all_souls)}")
    print(f"   Beings: {len(all_beings)}")
    print(f"   Calculator functions: {len(calc_soul.list_functions())}")
    
    # 10. Test get_or_create
    calc_being3 = await Being.get_or_create(
        soul=calc_soul,
        alias="calculator_master",  # Ten sam alias
        unique_by="alias"
    )
    print(f"🔄 Get or create: {'EXISTING' if calc_being3.ulid == calc_being.ulid else 'NEW'}")
    
    print("\n🎉 Demo completed successfully!")
    return {
        "souls_created": len([s for s in all_souls if "calculator" in s.alias.lower()]),
        "beings_created": len([b for b in all_beings if "calculator" in b.alias.lower()]),
        "functions_available": calc_soul.get_functions_count(),
        "demo_status": "SUCCESS"
    }

async def main():
    """Main demo runner"""
    try:
        result = await demo_complete_cycle()
        print(f"\n✨ Final result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
