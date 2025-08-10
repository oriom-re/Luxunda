
"""
Przykład demonstracyjny funkcji zapisanych jako dusze w bazie danych.
Pokazuje wyszukiwanie po hash i alias oraz wykonywanie przez exec.
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.function_registry import function_registry


def calculator(a: float, b: float, operation: str = "add") -> float:
    """Kalkulator matematyczny"""
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


async def data_processor(data: list, operation: str = "sum") -> dict:
    """Asynchroniczny procesor danych"""
    if operation == "sum":
        result = sum(data)
    elif operation == "average":
        result = sum(data) / len(data) if data else 0
    elif operation == "max":
        result = max(data) if data else 0
    elif operation == "min":
        result = min(data) if data else 0
    else:
        result = len(data)
    
    return {
        "operation": operation,
        "result": result,
        "count": len(data)
    }


async def demo_function_souls_database():
    """Demonstracja funkcji jako dusze w bazie danych"""
    print("🧬 LuxDB Function Souls Database Demo")
    print("=" * 50)

    # 1. Utwórz Soul i zarejestruj funkcje - automatycznie utworzą się dusze funkcji
    print("\n1. Creating Soul and registering functions...")
    
    main_genotype = {
        "genesis": {
            "name": "math_processor",
            "type": "service",
            "version": "1.0.0"
        },
        "attributes": {
            "service_name": {"py_type": "str", "default": "MathProcessor"},
            "active": {"py_type": "bool", "default": True}
        }
    }
    
    main_soul = await Soul.create(main_genotype, alias="math_service")
    
    # Te operacje automatycznie utworzą dusze funkcji w bazie
    await main_soul.register_function_and_save("calculator", calculator, "Mathematical calculator")
    await main_soul.register_function_and_save("data_processor", data_processor, "Data processing function")
    
    print(f"✅ Created main soul: {main_soul.alias}")
    print(f"   Functions registered: {main_soul.list_functions()}")

    # 2. Sprawdź czy dusze funkcji zostały utworzone w bazie
    print("\n2. Checking function souls in database...")
    
    function_souls = await Soul.get_function_souls()
    print(f"✅ Found {len(function_souls)} function souls in database:")
    
    for soul in function_souls:
        genesis = soul.genotype.get("genesis", {})
        print(f"   - {genesis.get('name')} (alias: {soul.alias})")
        print(f"     Hash: {soul.soul_hash}")
        print(f"     Description: {genesis.get('description')}")

    # 3. Wyszukiwanie funkcji po alias (najnowsza wersja)
    print("\n3. Finding functions by alias...")
    
    calc_soul = await Soul.find_function_by_alias("calculator")
    if calc_soul:
        print(f"✅ Found calculator function by alias: {calc_soul.alias}")
        print(f"   Hash: {calc_soul.soul_hash}")
        
        # Wykonaj funkcję przez duszę
        result = await calc_soul.execute_function_from_soul(10, 5, operation="multiply")
        if result.get("success"):
            print(f"   Execution result: 10 * 5 = {result['data']['result']}")

    # 4. Wyszukiwanie funkcji po hash (konkretna wersja)
    print("\n4. Finding functions by hash...")
    
    if function_souls:
        target_soul = function_souls[0]
        found_soul = await Soul.find_function_by_hash(target_soul.soul_hash)
        
        if found_soul:
            print(f"✅ Found function by hash: {found_soul.soul_hash[:16]}...")
            
            # Wykonaj przez hash
            if "data_processor" in found_soul.alias:
                result = await found_soul.execute_function_from_soul([1, 2, 3, 4, 5], operation="average")
                if result.get("success"):
                    print(f"   Execution result: average([1,2,3,4,5]) = {result['data']['result']['result']}")

    # 5. Wykorzystanie Being do wykonania funkcji
    print("\n5. Using Being to execute functions...")
    
    # Znajdź Being funkcji po alias
    calc_being = await Being.find_function_being("calculator", "alias")
    if calc_being:
        print(f"✅ Created function being: {calc_being.alias}")
        
        # Wykonaj funkcję przez Being
        result = await calc_being.exec_function(15, 3, operation="divide")
        if result.get("success"):
            print(f"   Being execution: 15 / 3 = {result['data']['result']}")

    # 6. Wykorzystanie globalnego rejestru funkcji
    print("\n6. Using global function registry...")
    
    # Wykonaj funkcję przez rejestr używając hash duszy
    if function_souls:
        target_hash = function_souls[0].soul_hash
        result = await function_registry.exec_function_by_soul(target_hash, [10, 20, 30], operation="sum")
        
        if result.get("success"):
            print(f"✅ Registry execution by hash: {result['data']['result']}")

    # 7. Statystyki użycia funkcji
    print("\n7. Function usage statistics...")
    
    for soul in function_souls[:2]:  # Sprawdź pierwsze 2 funkcje
        being_result = await Being.set(
            soul=soul,
            data=soul.get_default_data(),
            alias=f"stats_{soul.soul_hash[:8]}"
        )
        
        if being_result.get("success"):
            being = being_result["data"]["being"]
            stats_data = being.get_data()
            
            print(f"   Function: {stats_data.get('function_name', 'unknown')}")
            print(f"   Usage count: {stats_data.get('usage_count', 0)}")
            print(f"   Last used: {stats_data.get('last_used', 'never')}")

    print("\n✨ Function souls database demo completed!")
    print("\n📝 Key features demonstrated:")
    print("  • Functions automatically saved as souls in database")
    print("  • Search by hash (specific version) and alias (latest version)")  
    print("  • Execute functions through soul.execute_function_from_soul()")
    print("  • Execute functions through Being.exec_function()")
    print("  • Execute functions through global registry")
    print("  • Usage statistics tracking")
    print("  • Source code preservation in soul attributes")


if __name__ == "__main__":
    asyncio.run(demo_function_souls_database())
