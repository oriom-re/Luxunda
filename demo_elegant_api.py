#!/usr/bin/env python3
"""
🧬 Demo Eleganckiego API Soul - Nowa Filozofia LuxDB
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.postgre_db import Postgre_db
from datetime import datetime
from typing import List

async def demo_new_soul_philosophy():
    """Demonstracja NOWEJ FILOZOFII Soul: Wzbogacony Soul + Wirtualne Being"""
    print("🧬 Demo NOWEJ FILOZOFII Soul: Wzbogacony Soul + Wirtualne Being")
    print("=" * 50)

    # Inicjalizacja bazy danych
    await Postgre_db.initialize_db()

    print("\n🎯 NOWA FILOZOFIA:")
    print("   • Soul.create() = init + zapis + pełne przetwarzanie")
    print("   • Soul.init() = wirtualna instancja z ULID + data")
    print("   • Soul.execute() = pełna funkcjonalność")
    print("   • Soul.set() = zapis wirtualnej instancji jako Being")
    print("   • Being = tylko wirtualny kontener danych")

    # 1. Tworzenie Soul z pełnym module_source
    print("\n1. 🧬 Soul.create() - Pełnoprawny funkcjonalny Soul...")

    calculator_genotype = {
        "genesis": {
            "name": "enhanced_calculator",
            "type": "calculator",
            "version": "2.0.0",
            "description": "Wzbogacony kalkulator z init i execute"
        },
        "attributes": {
            "precision": {"py_type": "int", "default": 2},
            "mode": {"py_type": "str", "default": "standard"},
            "history": {"py_type": "List[dict]", "default": []}
        },
        "module_source": '''
def init(instance_context=None):
    """Inicjalizuje kalkulator z konfiguracją"""
    if instance_context:
        print(f"🔧 Initializing calculator instance: {instance_context.get('instance_ulid', 'unknown')[:8]}")
        return {
            "instance_updates": {
                "initialized": True,
                "calculation_count": 0,
                "last_operation": None
            }
        }
    return {"status": "ready"}

def execute(execution_context=None, operation=None, a=None, b=None):
    """Główna funkcja execute kalkulatora"""
    if not execution_context:
        return {"error": "Execution context required"}

    data = execution_context.get('data', {})
    operation = operation or data.get('operation')
    a = a or data.get('a')
    b = b or data.get('b')

    if operation == 'add':
        result = _add(a, b)
    elif operation == 'multiply':
        result = _multiply(a, b)
    else:
        result = {"error": "Unknown operation"}

    return {
        "operation": operation,
        "operands": [a, b],
        "result": result,
        "executed_at": execution_context.get('execution_timestamp'),
        "instance_ulid": execution_context.get('instance_ulid')
    }

def _add(a, b):
    """Prywatna funkcja dodawania"""
    return a + b

def _multiply(a, b):
    """Prywatna funkcja mnożenia"""
    return a * b
'''
    }

    # Tworzenie Soul z pełnym przetwarzaniem
    calculator_soul = await Soul.create(calculator_genotype, alias="enhanced_calculator")
    print(f"   ✅ Soul created with {calculator_soul.get_functions_count()} functions")

    # 2. Soul.init() - Wirtualna instancja
    print("\n2. 🧬 Soul.init() - Tworzy wirtualną instancję...")
    init_result = await calculator_soul.init(data={"precision": 4, "mode": "scientific"})
    instance_ulid = init_result['data']['instance_ulid']
    print(f"   ✅ Virtual instance created: {instance_ulid[:8]}")

    # 3. Soul.execute() - Pełna funkcjonalność
    print("\n3. 🧬 Soul.execute() - Wykonanie z wirtualną instancją...")
    exec_result = await calculator_soul.execute(
        data={"operation": "add", "a": 15, "b": 25},
        instance_ulid=instance_ulid
    )
    print(f"   ✅ Calculation result: {exec_result['data']['result']}")

    # 4. Soul.execute() - Bez instancji (chwilowe dane)
    print("\n4. 🧬 Soul.execute() - Chwilowe wykonanie...")
    temp_result = await calculator_soul.execute(
        data={"operation": "multiply", "a": 6, "b": 7}
    )
    print(f"   ✅ Temporary calculation: {temp_result['data']['result']}")

    # 5. Soul.set() - Zapis wirtualnej instancji jako Being
    print("\n5. 🧬 Soul.set() - Zapisz wirtualną instancję jako Being...")
    instance_data = init_result['data']['instance_data']
    instance_data.update({
        "calculations_performed": 1,
        "last_result": exec_result['data']['result']
    })

    save_result = await calculator_soul.set(
        instance_data=instance_data,
        instance_ulid=instance_ulid
    )
    being_ulid = save_result['data']['being_ulid']
    print(f"   ✅ Virtual instance saved as Being: {being_ulid[:8]}")

    # 6. Demonstracja Being jako kontener danych
    print("\n6. 🧬 Being jako wirtualny kontener danych...")

    saved_being = await Being.get(being_ulid)
    print(f"   ✅ Being loaded: {saved_being.ulid[:8]}")
    print(f"   📊 Being data: precision={saved_being.data.get('precision')}, mode={saved_being.data.get('mode')}")
    print(f"   📈 Calculations: {saved_being.data.get('calculations_performed')}")

    print("\n🎯 PODSUMOWANIE NOWEJ FILOZOFII:")
    print("   ✅ Soul jest pełnoprawnym wykonawcą")
    print("   ✅ Wirtualne instancje z ULID + data")  
    print("   ✅ Chwilowe wykonanie bez historii")
    print("   ✅ Being tylko kontener danych z historią")
    print("   ✅ Eleganckie API: init → execute → set")

async def main():
    await demo_new_soul_philosophy()

if __name__ == "__main__":
    asyncio.run(main())