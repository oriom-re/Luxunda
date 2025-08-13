
#!/usr/bin/env python3
"""
🔗 Demo systemu relacji can_use z Registry
Pokazuje jak Being może używać innych Being przez relacje kierunkowe
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being

async def demo_relations_system():
    """Demo pełnego systemu relacji can_use"""
    print("🔗 === DEMO SYSTEMU RELACJI CAN_USE ===")

    # 1. Utwórz soul funkcji do użycia
    print("\n1. 🧬 Tworzenie soul funkcji matematycznych...")
    math_genotype = {
        "genesis": {
            "name": "math_functions",
            "type": "function_soul",
            "version": "1.0.0"
        },
        "attributes": {
            "last_calculation": {"py_type": "str"}
        },
        "module_source": '''
def init(being_context=None):
    print(f"🧮 Math functions ready: {being_context.get('alias')}")
    return {"ready": True, "provides": ["add", "multiply", "advanced_math"]}

def execute(operation=None, a=None, b=None, being_context=None):
    """Wykonuje operacje matematyczne"""
    if operation == "add":
        result = a + b
        print(f"➕ {a} + {b} = {result}")
        return {"operation": "add", "result": result}
    elif operation == "multiply":
        result = a * b
        print(f"✖️ {a} × {b} = {result}")
        return {"operation": "multiply", "result": result}
    else:
        return {"error": "unknown_operation", "operation": operation}
'''
    }

    math_soul = await Soul.create(math_genotype, "math_functions")
    print(f"   ✅ Math Soul: {math_soul.alias}")

    # 2. Utwórz coordinator który będzie używał math functions
    print("\n2. 🎯 Tworzenie coordinator soul...")
    coordinator_genotype = {
        "genesis": {
            "name": "task_coordinator", 
            "type": "coordinator_soul",
            "version": "1.0.0"
        },
        "attributes": {
            "delegated_tasks": {"py_type": "dict", "default": {}}
        },
        "module_source": '''
def init(being_context=None):
    print(f"🎯 Task coordinator ready: {being_context.get('alias')}")
    return {"ready": True, "role": "coordinator"}

async def execute(task=None, target_being_ulid=None, being_context=None):
    """Koordynuje zadania - używa innych bytów przez relacje"""
    from luxdb.models.being import Being
    
    if task == "math_task":
        print(f"🎯 Coordinator delegating math task to {target_being_ulid[:8]}...")
        
        # 1. Sprawdź relację can_use przez registry
        registry_being = await get_registry()
        can_use_result = await check_can_use_relation(being_context.get('ulid'), target_being_ulid)
        
        if not can_use_result.get('can_use'):
            return {"error": "no_permission", "target": target_being_ulid}
        
        # 2. Pobierz target being przez registry
        target_result = await registry_being.execute_soul_function(
            "execute", 
            action="get_or_wake", 
            being_ulid=target_being_ulid
        )
        
        if not target_result.get('success'):
            return {"error": "target_not_available", "target": target_being_ulid}
        
        # 3. Wywołaj execute na target being
        target_being = target_result['data']['result'].get('being')
        if target_being:
            print(f"🔗 Using being {target_being.alias} via can_use relation")
            math_result = await target_being.execute_soul_function(
                "execute",
                operation="add",
                a=10,
                b=5
            )
            return {
                "task_completed": True,
                "delegated_to": target_being.alias,
                "result": math_result.get('data', {}).get('result')
            }
        
        return {"error": "delegation_failed"}
    
    return {"task": task, "status": "unknown_task"}

async def get_registry():
    """Pobiera singleton registry"""
    # W rzeczywistości byłoby cache'owane
    from luxdb.models.being import Being
    registry_beings = await Being.get_by_alias("system_registry")
    return registry_beings[0] if registry_beings else None
    
async def check_can_use_relation(source_ulid, target_ulid):
    """Sprawdza relację can_use"""
    # Uproszczona implementacja - w rzeczywistości sprawdzałaby relacje
    return {"can_use": True, "relation_type": "can_use"}
'''
    }

    coordinator_soul = await Soul.create(coordinator_genotype, "task_coordinator")
    print(f"   ✅ Coordinator Soul: {coordinator_soul.alias}")

    # 3. Utwórz souls dla relacji i registry
    print("\n3. 🏛️ Tworzenie Registry i Relations souls...")
    
    # Relations soul (już utworzyliśmy w pliku)
    relations_soul = await Soul.get_by_alias("soul_relations")
    if not relations_soul:
        print("   ❌ Relations soul not found - run demo_relations_system.py first")
        return

    # Registry soul (już utworzyliśmy w pliku)  
    registry_soul = await Soul.get_by_alias("soul_registry")
    if not registry_soul:
        print("   ❌ Registry soul not found - run demo_relations_system.py first")
        return

    # 4. Utwórz beings
    print("\n4. 🤖 Tworzenie beings...")
    
    # Math being
    math_being = await Being.create(
        soul=math_soul,
        alias="math_calculator",
        attributes={"specialty": "mathematics"}
    )
    
    # Coordinator being
    coordinator_being = await Being.create(
        soul=coordinator_soul,
        alias="task_manager", 
        attributes={"role": "coordinator"}
    )
    
    # Registry being (singleton)
    registry_being = await Being.get_or_create(
        soul=registry_soul,
        alias="system_registry",
        unique_by="alias"
    )
    
    print(f"   ✅ Math Being: {math_being.alias} ({math_being.ulid[:8]}...)")
    print(f"   ✅ Coordinator Being: {coordinator_being.alias} ({coordinator_being.ulid[:8]}...)")
    print(f"   ✅ Registry Being: {registry_being.alias} ({registry_being.ulid[:8]}...)")

    # 5. Zarejestruj math being w registry
    print("\n5. 📝 Rejestrowanie math being w registry...")
    register_result = await registry_being.execute_soul_function(
        "execute",
        action="register",
        being_ulid=math_being.ulid,
        ttl_hours=2
    )
    print(f"   ✅ Registration: {register_result.get('data', {})}")

    # 6. Utwórz relację can_use
    print("\n6. 🔗 Tworzenie relacji can_use...")
    relation_being = await Being.create(
        soul=relations_soul,
        alias=f"relation_{coordinator_being.ulid[:8]}_to_{math_being.ulid[:8]}",
        attributes={
            "source_being_ulid": coordinator_being.ulid,
            "target_being_ulid": math_being.ulid,
            "relation_type": "can_use"
        }
    )
    print(f"   ✅ Relation created: {relation_being.alias}")

    # 7. Test delegacji przez relacje
    print("\n7. 🧪 Test delegacji przez relacje can_use...")
    
    delegation_result = await coordinator_being.execute_soul_function(
        "execute",
        task="math_task",
        target_being_ulid=math_being.ulid
    )
    
    print(f"   📊 Delegation result: {delegation_result.get('data', {})}")

    # 8. Test TTL cleanup
    print("\n8. 🧹 Test TTL cleanup...")
    cleanup_result = await registry_being.execute_soul_function(
        "execute",
        action="cleanup"
    )
    print(f"   📊 Cleanup result: {cleanup_result.get('data', {})}")

    print("\n✅ Demo completed - Relations system with Registry working!")

if __name__ == "__main__":
    asyncio.run(demo_relations_system())
