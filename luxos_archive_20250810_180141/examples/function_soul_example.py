
"""
Przykład wykorzystania Soul z funkcjami w LuxDB.
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being


# Przykładowe funkcje do zarejestrowania
def simple_calculator(a: int, b: int, operation: str = "add") -> float:
    """Prosta funkcja kalkulatora"""
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return a / b if b != 0 else 0
    else:
        raise ValueError(f"Unsupported operation: {operation}")


async def async_data_processor(data: list, being_context: dict = None) -> dict:
    """Asynchroniczna funkcja przetwarzania danych"""
    await asyncio.sleep(0.1)  # Symulacja pracy asynchronicznej
    
    result = {
        "processed_items": len(data),
        "sum": sum(data) if all(isinstance(x, (int, float)) for x in data) else 0,
        "processed_by": being_context.get("alias", "unknown") if being_context else "unknown"
    }
    
    return result


def greeting_generator(name: str, language: str = "en") -> str:
    """Generator powitań w różnych językach"""
    greetings = {
        "en": f"Hello, {name}!",
        "pl": f"Cześć, {name}!",
        "es": f"¡Hola, {name}!",
        "fr": f"Bonjour, {name}!"
    }
    return greetings.get(language, greetings["en"])


async def demo_function_souls():
    """Demonstracja Soul z funkcjami"""
    print("🧬 LuxDB Function Souls Demo")
    print("=" * 50)

    # 1. Tworzenie specjalizowanego Soul dla funkcji kalkulatora
    print("\n1. Creating calculator function soul...")
    calc_soul = await Soul.create_function_soul(
        name="calculate",
        func=simple_calculator,
        description="Simple calculator function",
        alias="calculator_soul"
    )
    
    print(f"✅ Created: {calc_soul}")
    print(f"📋 Available functions: {calc_soul.list_functions()}")

    # 2. Wykonywanie funkcji bezpośrednio przez Soul
    print("\n2. Executing function directly through soul...")
    result = await calc_soul.execute_function("calculate", 10, 5, operation="multiply")
    print(f"🔢 10 * 5 = {result['data']['result']}")

    # 3. Tworzenie Soul z wieloma funkcjami
    print("\n3. Creating multi-function soul...")
    multi_genotype = {
        "genesis": {
            "name": "utility_functions",
            "type": "multi_function_soul",
            "version": "1.0.0",
            "description": "Soul with multiple utility functions"
        },
        "attributes": {
            "service_name": {"py_type": "str"},
            "total_executions": {"py_type": "int", "default": 0}
        }
    }

    multi_soul = await Soul.create(multi_genotype, alias="utility_soul")
    
    # Zarejestruj funkcje i zapisz zmiany
    await multi_soul.register_function_and_save("greet", greeting_generator, "Generate greetings")
    await multi_soul.register_function_and_save("process_data", async_data_processor, "Process data asynchronously")
    await multi_soul.register_function_and_save("calculate", simple_calculator, "Calculator function")

    print(f"✅ Created multi-function soul: {multi_soul}")
    print(f"📋 Functions: {', '.join(multi_soul.list_functions())}")

    # 4. Tworzenie Being i wykonywanie funkcji
    print("\n4. Creating being and executing soul functions...")
    utility_being = await Being.set(
        soul=multi_soul,
        data={
            "service_name": "UtilityBot",
            "total_executions": 0
        },
        alias="utility_bot"
    )
    
    if utility_being.get('success'):
        being = utility_being['data']['being']
        
        # Lista dostępnych funkcji
        functions = await being.list_available_functions()
        print(f"🤖 Being functions: {functions}")

        # Wykonaj funkcję powitania
        greeting_result = await being.execute_soul_function("greet", "Alice", language="pl")
        if greeting_result.get('success'):
            print(f"👋 Greeting: {greeting_result['data']['result']}")

        # Wykonaj funkcję przetwarzania danych
        data_result = await being.execute_soul_function("process_data", [1, 2, 3, 4, 5])
        if data_result.get('success'):
            print(f"📊 Data processing: {data_result['data']['result']}")

        # Wykonaj kalkulację
        calc_result = await being.execute_soul_function("calculate", 15, 3, operation="divide")
        if calc_result.get('success'):
            print(f"🔢 15 / 3 = {calc_result['data']['result']}")

    # 5. Walidacja wywołań funkcji
    print("\n5. Function validation demo...")
    errors = multi_soul.validate_function_call("calculate", 10, 0, operation="invalid_op")
    if errors:
        print(f"⚠️ Validation errors: {errors}")
    
    # Prawidłowe wywołanie
    errors = multi_soul.validate_function_call("calculate", 10, 5, operation="add")
    print(f"✅ Valid call - errors: {errors}")

    # 6. Informacje o funkcjach
    print("\n6. Function information...")
    for func_name in multi_soul.list_functions():
        info = multi_soul.get_function_info(func_name)
        print(f"🔧 {func_name}: {info.get('description', 'No description')}")
        if 'signature' in info:
            sig = info['signature']
            print(f"   Parameters: {list(sig.get('parameters', {}).keys())}")
            print(f"   Returns: {sig.get('return_type', 'Any')}")
            print(f"   Async: {info.get('is_async', False)}")

    print("\n✨ Function souls demo completed!")


if __name__ == "__main__":
    asyncio.run(demo_function_souls())
