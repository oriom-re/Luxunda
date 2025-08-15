
#!/usr/bin/env python3
"""
🧬 Demo Lazy Soul Execution - Soul wykonuje funkcje bez tworzenia Being

Pokazuje:
1. Soul wykonuje bezpośrednio funkcje bez danych do zapisu
2. Being tworzy się tylko gdy są dane do zapisu
3. Optymalizacja wydajności przez unikanie niepotrzebnych Being
"""

import asyncio
from luxdb.models.soul import Soul

async def demo_lazy_execution():
    print("🧬 DEMO: Lazy Soul Execution - Being tylko gdy potrzeba")
    print("=" * 60)
    
    # 1. Utwórz Soul z funkcjami obliczeniowymi
    calculator_genotype = {
        "genesis": {
            "name": "lazy_calculator",
            "version": "1.0",
            "type": "processor",
            "description": "Calculator that avoids Being creation when possible"
        },
        "attributes": {
            "last_result": {"py_type": "float", "default": 0.0},
            "calculation_count": {"py_type": "int", "default": 0}
        },
        "module_source": '''
def calculate(operation, a, b, being_context=None):
    """Pure calculation - no data to store"""
    if operation == "add":
        return {"result": a + b, "operation": f"{a} + {b}"}
    elif operation == "multiply":
        return {"result": a * b, "operation": f"{a} × {b}"}
    elif operation == "divide":
        if b != 0:
            return {"result": a / b, "operation": f"{a} ÷ {b}"}
        return {"error": "Division by zero"}
    return {"error": "Unknown operation"}

def calculate_and_store(operation, a, b, being_context=None):
    """Calculation with storage - needs Being"""
    result = calculate(operation, a, b, being_context)
    
    if being_context and 'error' not in result:
        # Aktualizuj dane Being
        being_context['data']['last_result'] = result['result']
        being_context['data']['calculation_count'] = being_context['data'].get('calculation_count', 0) + 1
        result['stored'] = True
        result['calculation_count'] = being_context['data']['calculation_count']
    
    return result
'''
    }
    
    soul = await Soul.create(calculator_genotype, "lazy_calculator")
    print(f"✅ Created Soul: {soul.alias} (hash: {soul.soul_hash[:8]})")
    
    print("\n" + "="*60)
    print("📊 DEMO 1: Soul Direct Execution (no Being needed)")
    print("="*60)
    
    # Bez atrybutów = Soul wykonuje bezpośrednio
    result1 = await soul.execute_or_create_being("calculate", 
                                                operation="add", a=10, b=5)
    
    print(f"🧬 Result: {result1['data']['result']['result']}")
    print(f"🧬 Execution mode: {result1['soul_context']['execution_mode']}")
    print(f"🧬 Being created: {result1['soul_context'].get('being_created', False)}")
    
    # Kolejne bezpośrednie wykonanie
    result2 = await soul.execute_or_create_being("calculate", 
                                                operation="multiply", a=7, b=3)
    
    print(f"🧬 Result: {result2['data']['result']['result']}")
    print(f"🧬 Being created: {result2['soul_context'].get('being_created', False)}")
    
    print("\n" + "="*60)
    print("💾 DEMO 2: Lazy Being Creation (data needs storage)")
    print("="*60)
    
    # Z atrybutami = automatyczne utworzenie Being
    result3 = await soul.execute_or_create_being("calculate_and_store",
                                                attributes={"calculation_count": 0, "last_result": 0.0},
                                                alias="persistent_calculator",
                                                operation="divide", a=20, b=4)
    
    print(f"💾 Result: {result3['data']['function_result']['data']['result']['result']}")
    print(f"💾 Execution mode: {result3['soul_context']['execution_mode']}")
    print(f"💾 Being created: {result3['data']['being_created']}")
    print(f"💾 Being ULID: {result3['data']['being']['ulid']}")
    print(f"💾 Stored calculation count: {result3['data']['function_result']['data']['result'].get('calculation_count')}")
    
    print("\n" + "="*60)
    print("🔍 DEMO 3: Soul Capabilities Check")
    print("="*60)
    
    print(f"🧬 Soul can execute directly (no data): {soul.can_execute_directly()}")
    print(f"🧬 Soul can execute directly (with data): {soul.can_execute_directly({'result': 42})}")
    print(f"🧬 Soul has {soul.get_functions_count()} functions registered")
    print(f"🧬 Functions: {soul.list_functions()}")
    
    print("\n" + "="*60)
    print("⚡ PERFORMANCE COMPARISON")
    print("="*60)
    
    import time
    
    # Test wydajności - bezpośrednie wykonanie
    start = time.time()
    for i in range(100):
        await soul.execute_directly("calculate", "add", i, 1)
    direct_time = time.time() - start
    
    print(f"⚡ 100 direct Soul executions: {direct_time:.4f}s")
    print(f"⚡ Average per execution: {direct_time/100*1000:.2f}ms")
    
    print("\n🎯 LAZY EXECUTION SUMMARY:")
    print("✅ Soul wykonuje funkcje bez Being gdy nie ma danych do zapisu")
    print("✅ Being tworzy się automatycznie gdy pojawią się atrybuty")
    print("✅ Znacząca optymalizacja wydajności dla operacji obliczeniowych")
    print("✅ Transparent - użytkownik nie musi się przejmować optymalizacją")

if __name__ == "__main__":
    asyncio.run(demo_lazy_execution())
