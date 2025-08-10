
"""
Przykład demonstrujący trwałość funkcji w LuxDB.
Pokazuje jak funkcje są przechowywane w genotypie i odtwarzane po restarcie.
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.core.function_registry import function_registry


def calculator(a: int, b: int, operation: str = "add") -> float:
    """Prosta funkcja kalkulatora"""
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else 0
    }
    return operations.get(operation, operations["add"])(a, b)


async def text_processor(text: str, operation: str = "upper") -> str:
    """Asynchroniczna funkcja przetwarzania tekstu"""
    await asyncio.sleep(0.1)  # Symulacja pracy asynchronicznej
    
    if operation == "upper":
        return text.upper()
    elif operation == "lower":
        return text.lower()
    elif operation == "reverse":
        return text[::-1]
    else:
        return text


async def demo_persistent_functions():
    """Demonstracja trwałości funkcji"""
    print("🔧 LuxDB Persistent Functions Demo")
    print("=" * 50)

    # 1. Rejestruj funkcje w globalnym rejestrze
    print("\n1. Registering functions in global registry...")
    calc_hash = function_registry.register_function(calculator, "calculator")
    text_hash = function_registry.register_function(text_processor, "text_processor")
    
    print(f"✅ Calculator function hash: {calc_hash}")
    print(f"✅ Text processor function hash: {text_hash}")

    # 2. Stwórz Soul z funkcjami
    print("\n2. Creating Soul with functions...")
    
    genotype = {
        "genesis": {
            "name": "persistent_functions_soul",
            "type": "function_collection",
            "version": "1.0.0",
            "description": "Soul demonstrating persistent functions"
        },
        "attributes": {
            "service_name": {"py_type": "str", "default": "PersistentService"},
            "operations_count": {"py_type": "int", "default": 0}
        }
    }
    
    soul = await Soul.create(genotype, alias="persistent_soul")
    
    # Dodaj funkcje do Soul
    await soul.register_function_and_save("calculate", calculator, "Calculator function")
    await soul.register_function_and_save("process_text", text_processor, "Text processing function")
    
    print(f"✅ Created soul with hash: {soul.soul_hash}")
    print(f"📋 Functions in soul: {soul.list_functions()}")

    # 3. Testuj funkcje przed "restartowaniem"
    print("\n3. Testing functions before restart...")
    
    calc_result = await soul.execute_function("calculate", 10, 5, operation="multiply")
    text_result = await soul.execute_function("process_text", "Hello World", operation="upper")
    
    print(f"🔢 10 * 5 = {calc_result['data']['result']}")
    print(f"📝 'Hello World' -> {text_result['data']['result']}")

    # 4. Symuluj "restart" - załaduj Soul z bazy
    print("\n4. Simulating restart - loading Soul from database...")
    
    # Wyczyść lokalny rejestr funkcji w Soul (symulacja restartu)
    soul._function_registry.clear()
    print("🔄 Cleared local function registry")
    
    # Załaduj Soul ponownie
    reloaded_soul = await Soul.get_by_hash(soul.soul_hash)
    print(f"✅ Reloaded soul: {reloaded_soul.alias}")
    print(f"📋 Functions after reload: {reloaded_soul.list_functions()}")

    # 5. Testuj funkcje po "restarcie"
    print("\n5. Testing functions after restart...")
    
    try:
        calc_result2 = await reloaded_soul.execute_function("calculate", 15, 3, operation="divide")
        text_result2 = await reloaded_soul.execute_function("process_text", "LuxDB Rocks", operation="reverse")
        
        print(f"🔢 15 / 3 = {calc_result2['data']['result']}")
        print(f"📝 'LuxDB Rocks' -> {text_result2['data']['result']}")
        
        print("\n✅ All functions work correctly after restart!")
        
    except Exception as e:
        print(f"❌ Error after restart: {e}")

    # 6. Pokaż informacje o funkcjach z genotypu
    print("\n6. Function information from genotype...")
    
    functions_info = reloaded_soul.genotype.get("functions", {})
    for func_name, func_info in functions_info.items():
        print(f"🔧 {func_name}:")
        print(f"   Description: {func_info.get('description')}")
        print(f"   Hash: {func_info.get('function_hash')}")
        print(f"   Is Async: {func_info.get('is_async')}")

    # 7. Sprawdź globalny rejestr funkcji
    print("\n7. Global function registry status...")
    registry_functions = function_registry.list_functions()
    print(f"📚 Functions in global registry: {len(registry_functions)}")
    for func_hash, func_name in registry_functions.items():
        print(f"   {func_hash}: {func_name}")

    print("\n✨ Persistent functions demo completed!")


if __name__ == "__main__":
    asyncio.run(demo_persistent_functions())
