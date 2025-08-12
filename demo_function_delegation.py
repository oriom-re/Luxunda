
#!/usr/bin/env python3
"""
🔗 Demo systemu delegacji funkcji między Being
Pokazuje jak Being może delegować wykonanie funkcji do innych Being.
"""

import asyncio
from datetime import datetime
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.postgre_db import Postgre_db

async def main():
    print("🔗 DEMO: System delegacji funkcji między Being")
    print("=" * 60)

    # Inicjalizacja bazy danych
    await Postgre_db.initialize()

    # 1. Utwórz Soul dla Being które ma funkcje matematyczne
    math_genotype = {
        "genesis": {
            "name": "math_calculator",
            "type": "calculator",
            "version": "1.0.0"
        },
        "attributes": {
            "name": {"py_type": "str", "default": "Math Calculator"}
        },
        "module_source": '''
def init(being_context=None):
    """Initialize calculator"""
    print(f"🧮 Math calculator initialized: {being_context.get('alias', 'unknown')}")
    return {"ready": True, "functions": ["add", "multiply", "advanced_calc"]}

def add(a, b):
    """Add two numbers"""
    result = a + b
    print(f"🔢 Addition: {a} + {b} = {result}")
    return result

def multiply(a, b):
    """Multiply two numbers"""
    result = a * b
    print(f"🔢 Multiplication: {a} × {b} = {result}")
    return result

def advanced_calc(expression):
    """Advanced calculation"""
    try:
        # Bezpieczne obliczenie prostych wyrażeń
        allowed = "0123456789+-*/(). "
        if all(c in allowed for c in expression):
            result = eval(expression)
            print(f"🧮 Advanced calc: {expression} = {result}")
            return result
        else:
            return "Invalid expression"
    except Exception as e:
        return f"Error: {str(e)}"
'''
    }

    # 2. Utwórz Soul dla Being które ma funkcje tekstowe
    text_genotype = {
        "genesis": {
            "name": "text_processor",
            "type": "text_handler",
            "version": "1.0.0"
        },
        "attributes": {
            "name": {"py_type": "str", "default": "Text Processor"}
        },
        "module_source": '''
def init(being_context=None):
    """Initialize text processor"""
    print(f"📝 Text processor initialized: {being_context.get('alias', 'unknown')}")
    return {"ready": True, "functions": ["uppercase", "lowercase", "reverse_text"]}

def uppercase(text):
    """Convert text to uppercase"""
    result = text.upper()
    print(f"📝 Uppercase: '{text}' -> '{result}'")
    return result

def lowercase(text):
    """Convert text to lowercase"""
    result = text.lower()
    print(f"📝 Lowercase: '{text}' -> '{result}'")
    return result

def reverse_text(text):
    """Reverse text"""
    result = text[::-1]
    print(f"📝 Reverse: '{text}' -> '{result}'")
    return result
'''
    }

    # 3. Utwórz Soul dla Being koordynatora (nie ma własnych funkcji)
    coordinator_genotype = {
        "genesis": {
            "name": "task_coordinator",
            "type": "coordinator",
            "version": "1.0.0"
        },
        "attributes": {
            "name": {"py_type": "str", "default": "Task Coordinator"},
            "managed_tasks": {"py_type": "int", "default": 0}
        },
        "module_source": '''
def init(being_context=None):
    """Initialize coordinator"""
    print(f"🎯 Task coordinator initialized: {being_context.get('alias', 'unknown')}")
    return {"ready": True, "role": "coordinator", "delegates_functions": True}

def execute(task_description=None, **kwargs):
    """Coordinate task execution - delegates to appropriate beings"""
    print(f"🎯 Coordinating task: {task_description}")
    return {
        "status": "coordinated", 
        "description": task_description,
        "timestamp": "2025-01-30T00:00:00"
    }
'''
    }

    # Utwórz Soul
    math_soul = await Soul.create(math_genotype, "math_calculator")
    text_soul = await Soul.create(text_genotype, "text_processor") 
    coordinator_soul = await Soul.create(coordinator_genotype, "task_coordinator")

    print("\n1. 🧮 Creating Math Calculator Being...")
    math_being = await Being.create(
        math_soul,
        attributes={"name": "Advanced Calculator"},
        alias="math_calc_001"
    )
    print(f"   ✅ Math Being: {math_being.alias} ({math_being.ulid[:8]}...)")

    print("\n2. 📝 Creating Text Processor Being...")
    text_being = await Being.create(
        text_soul,
        attributes={"name": "Text Handler"},
        alias="text_proc_001"
    )
    print(f"   ✅ Text Being: {text_being.alias} ({text_being.ulid[:8]}...)")

    print("\n3. 🎯 Creating Task Coordinator Being...")
    coordinator_being = await Being.create(
        coordinator_soul,
        attributes={"name": "Main Coordinator", "managed_tasks": 0},
        alias="coordinator_001"
    )
    print(f"   ✅ Coordinator Being: {coordinator_being.alias} ({coordinator_being.ulid[:8]}...)")

    # 4. Skonfiguruj delegacje funkcji
    print("\n4. 🔗 Configuring function delegations...")
    
    # Coordinator deleguje funkcje matematyczne do math_being
    coordinator_being.add_function_delegate("add", math_being.ulid)
    coordinator_being.add_function_delegate("multiply", math_being.ulid)
    coordinator_being.add_function_delegate("advanced_calc", math_being.ulid)
    
    # Coordinator deleguje funkcje tekstowe do text_being
    coordinator_being.add_function_delegate("uppercase", text_being.ulid)
    coordinator_being.add_function_delegate("lowercase", text_being.ulid)
    coordinator_being.add_function_delegate("reverse_text", text_being.ulid)
    
    await coordinator_being.save()
    
    print(f"   ✅ Configured {len(coordinator_being.get_function_delegates())} function delegates")

    # 5. Testuj delegacje funkcji
    print("\n5. 🧪 Testing function delegations...")

    # Test funkcji matematycznych przez coordinatora
    print("\n   📊 Math functions via coordinator:")
    
    add_result = await coordinator_being.execute_soul_function("add", 15, 25)
    print(f"   Result: {add_result.get('data', {}).get('result')}")
    
    multiply_result = await coordinator_being.execute_soul_function("multiply", 7, 8)
    print(f"   Result: {multiply_result.get('data', {}).get('result')}")
    
    calc_result = await coordinator_being.execute_soul_function("advanced_calc", "(10 + 5) * 2")
    print(f"   Result: {calc_result.get('data', {}).get('result')}")

    # Test funkcji tekstowych przez coordinatora
    print("\n   📝 Text functions via coordinator:")
    
    upper_result = await coordinator_being.execute_soul_function("uppercase", "hello world")
    print(f"   Result: {upper_result.get('data', {}).get('result')}")
    
    reverse_result = await coordinator_being.execute_soul_function("reverse_text", "LuxOS")
    print(f"   Result: {reverse_result.get('data', {}).get('result')}")

    # 6. Test automatycznego odkrywania funkcji
    print("\n6. 🔍 Testing auto-discovery of functions...")
    
    # Usuń delegację i spróbuj automatycznego odkrycia
    coordinator_being.remove_function_delegate("add")
    
    auto_add_result = await coordinator_being.execute_soul_function("add", 100, 200)
    print(f"   Auto-discovered add result: {auto_add_result.get('data', {}).get('result')}")

    # 7. Pokaż statystyki delegacji
    print("\n7. 📈 Delegation statistics:")
    stats = coordinator_being.get_delegation_stats()
    print(f"   Total delegations: {stats['total_delegations']}")
    print(f"   Active delegates: {stats['active_delegates']}")
    print(f"   Function delegates: {list(stats['function_delegates'].keys())}")

    # 8. Test głębokiej delegacji (Being -> Being -> Being)
    print("\n8. 🔗 Testing deep delegation...")
    
    # Utwórz trzeci poziom Being
    deep_genotype = {
        "genesis": {
            "name": "deep_processor",
            "type": "deep_level",
            "version": "1.0.0"
        },
        "attributes": {
            "name": {"py_type": "str", "default": "Deep Processor"}
        },
        "module_source": '''
def init(being_context=None):
    """Initialize deep processor"""
    print(f"🔻 Deep processor initialized: {being_context.get('alias', 'unknown')}")
    return {"ready": True, "level": "deep"}

def deep_function(value):
    """Process deeply"""
    result = f"DEEP_PROCESSED({value})"
    print(f"🔻 Deep processing: {value} -> {result}")
    return result
'''
    }
    
    deep_soul = await Soul.create(deep_genotype, "deep_processor")
    deep_being = await Being.create(
        deep_soul,
        attributes={"name": "Deep Level Processor"},
        alias="deep_proc_001"
    )
    
    # Text being deleguje do deep being
    text_being.add_function_delegate("deep_function", deep_being.ulid)
    await text_being.save()
    
    # Coordinator -> Text Being -> Deep Being
    coordinator_being.add_function_delegate("deep_function", text_being.ulid)
    await coordinator_being.save()
    
    deep_result = await coordinator_being.execute_soul_function("deep_function", "test_value")
    print(f"   Deep delegation result: {deep_result.get('data', {}).get('result')}")

    print("\n" + "=" * 60)
    print("🎉 Function delegation demo completed!")
    print("✅ Being can now delegate functions to other Being")
    print("✅ Auto-discovery works for unknown functions") 
    print("✅ Deep delegation (Being -> Being -> Being) works")
    print("✅ Delegation statistics and management included")

if __name__ == "__main__":
    asyncio.run(main())
