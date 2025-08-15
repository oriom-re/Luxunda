
#!/usr/bin/env python3
"""
🧬 Demo Instrukcji Użytkownika - Praktyczny przykład użycia Soul, Being i Intelligent Kernel
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.intelligent_kernel import intelligent_kernel
from luxdb.core.postgre_db import Postgre_db

async def demo_instrukcje():
    """Demonstracja zgodna z instrukcjami użytkownika"""
    
    print("🧬 DEMO: Instrukcje Użytkownika - Soul, Being, Intelligent Kernel")
    print("=" * 70)
    
    # Inicjalizacja bazy
    await Postgre_db.initialize()
    await intelligent_kernel.initialize()
    
    # 1. TWORZENIE SOUL Z FUNKCJAMI
    print("\n1. 🧬 Tworzenie Soul z funkcjami...")
    
    task_genotype = {
        "genesis": {
            "name": "task_manager",
            "type": "productivity_tool",
            "version": "1.0.0",
            "description": "Zarządca zadań z funkcjami"
        },
        "attributes": {
            "tasks": {"py_type": "list", "default": []},
            "completed_count": {"py_type": "int", "default": 0},
            "owner": {"py_type": "str", "default": "unknown"}
        },
        "module_source": '''
def init(being_context=None):
    """Inicjalizacja zarządcy zadań"""
    alias = being_context.get('alias', 'TaskManager')
    print(f"🎯 Task Manager {alias} initialized and ready!")
    
    return {
        "ready": True,
        "suggested_persistence": True,
        "message": f"Task Manager {alias} is now your personal productivity assistant"
    }

def execute(request=None, being_context=None):
    """Główna funkcja wykonawcza - router działań"""
    if not request:
        return {
            "status": "ready",
            "available_actions": ["add_task", "complete_task", "list_tasks", "stats"],
            "usage": "Send request with 'action' field"
        }
    
    action = request.get('action')
    
    if action == 'add_task':
        return add_task(request.get('task', ''), request.get('priority', 'normal'), being_context)
    elif action == 'complete_task':
        return complete_task(request.get('task_id', 0), being_context)
    elif action == 'list_tasks':
        return list_tasks(being_context)
    elif action == 'stats':
        return get_stats(being_context)
    else:
        return {"error": f"Unknown action: {action}", "available_actions": ["add_task", "complete_task", "list_tasks", "stats"]}

def add_task(task_description, priority, being_context):
    """Dodaje nowe zadanie"""
    if not task_description:
        return {"error": "Task description is required"}
    
    tasks = being_context['data'].get('tasks', [])
    new_task = {
        "id": len(tasks),
        "description": task_description,
        "priority": priority,
        "completed": False,
        "created_at": "2025-01-30T12:00:00"
    }
    
    tasks.append(new_task)
    being_context['data']['tasks'] = tasks
    
    return {
        "success": True,
        "task_added": new_task,
        "total_tasks": len(tasks),
        "message": f"Added task: {task_description}"
    }

def complete_task(task_id, being_context):
    """Oznacza zadanie jako ukończone"""
    tasks = being_context['data'].get('tasks', [])
    
    if task_id >= len(tasks):
        return {"error": f"Task with ID {task_id} not found", "total_tasks": len(tasks)}
    
    task = tasks[task_id]
    if task['completed']:
        return {"error": f"Task '{task['description']}' is already completed"}
    
    tasks[task_id]['completed'] = True
    completed_count = being_context['data'].get('completed_count', 0) + 1
    being_context['data']['completed_count'] = completed_count
    
    return {
        "success": True,
        "completed_task": task['description'],
        "total_completed": completed_count,
        "message": f"Completed: {task['description']}"
    }

def list_tasks(being_context):
    """Lista wszystkich zadań"""
    tasks = being_context['data'].get('tasks', [])
    pending = [t for t in tasks if not t['completed']]
    completed = [t for t in tasks if t['completed']]
    
    return {
        "all_tasks": tasks,
        "pending_tasks": pending,
        "completed_tasks": completed,
        "summary": {
            "total": len(tasks),
            "pending": len(pending), 
            "completed": len(completed)
        }
    }

def get_stats(being_context):
    """Statystyki produktywności"""
    tasks = being_context['data'].get('tasks', [])
    completed = [t for t in tasks if t['completed']]
    high_priority = [t for t in tasks if t.get('priority') == 'high']
    
    return {
        "total_tasks": len(tasks),
        "completed_tasks": len(completed),
        "completion_rate": len(completed) / len(tasks) * 100 if tasks else 0,
        "high_priority_tasks": len(high_priority),
        "productivity_score": len(completed) * 10  # Prosta metryka
    }
'''
    }
    
    # Tworzenie Soul
    task_soul = await Soul.create(task_genotype, alias="task_manager_v1")
    print(f"✅ Utworzono Soul: {task_soul.alias}")
    print(f"   Hash: {task_soul.soul_hash[:12]}...")
    print(f"   Funkcje: {task_soul.list_functions()}")
    
    # 2. REJESTRACJA W INTELLIGENT KERNEL
    print("\n2. 🧠 Rejestracja w Intelligent Kernel...")
    
    alias = "tm_prod_v1"
    result = await intelligent_kernel.register_alias_mapping(alias, task_soul.soul_hash)
    print(f"✅ Zarejestrowano alias '{alias}' → {task_soul.soul_hash[:12]}...")
    
    # 3. TWORZENIE BEING PRZEZ KERNEL (AUTOMATYCZNA DELEGACJA!)
    print("\n3. 🤖 Tworzenie Being przez Kernel (delegacja)...")
    
    # To jest KLUCZOWE - tylko alias, Kernel znajdzie Soul
    task_being = await Being.create(
        alias="tm_prod_v1",  # Kernel automatycznie deleguje
        attributes={
            "owner": "demo_user",
            "workspace": "productivity_demo"
        }
    )
    
    print(f"✅ Utworzono Being przez Kernel: {task_being.alias}")
    print(f"   ULID: {task_being.ulid}")
    print(f"   Function Master: {task_being.is_function_master()}")
    
    # 4. UŻYCIE BEING - RÓŻNE WZORCE
    print("\n4. 🎯 Używanie Being - różne wzorce wykonania...")
    
    # Wzorzec A: Inteligentne wykonanie (Being wybiera funkcję)
    print("\n   A) Inteligentne wykonanie bez argumentów:")
    result = await task_being.execute()
    print(f"      Status: {result['data']['status']}")
    print(f"      Dostępne akcje: {result['data']['available_actions']}")
    
    # Wzorzec B: Konkretna funkcja przez execute
    print("\n   B) Dodawanie zadań:")
    result1 = await task_being.execute({
        "action": "add_task",
        "task": "Napisać dokumentację API", 
        "priority": "high"
    })
    print(f"      ✅ {result1['data']['message']}")
    
    result2 = await task_being.execute({
        "action": "add_task",
        "task": "Przetestować system zadań",
        "priority": "normal"
    })
    print(f"      ✅ {result2['data']['message']}")
    
    result3 = await task_being.execute({
        "action": "add_task", 
        "task": "Zoptymalizować wydajność",
        "priority": "low"
    })
    print(f"      ✅ {result3['data']['message']}")
    
    # Wzorzec C: Lista zadań
    print("\n   C) Lista wszystkich zadań:")
    tasks_result = await task_being.execute({"action": "list_tasks"})
    summary = tasks_result['data']['summary']
    print(f"      📋 Total: {summary['total']}, Pending: {summary['pending']}, Completed: {summary['completed']}")
    
    for task in tasks_result['data']['pending_tasks']:
        print(f"      - [{task['id']}] {task['description']} ({task['priority']})")
    
    # Wzorzec D: Ukończenie zadania
    print("\n   D) Ukończenie zadania:")
    complete_result = await task_being.execute({
        "action": "complete_task",
        "task_id": 0
    })
    print(f"      ✅ {complete_result['data']['message']}")
    
    # Wzorzec E: Statystyki
    print("\n   E) Statystyki produktywności:")
    stats_result = await task_being.execute({"action": "stats"})
    stats = stats_result['data']
    print(f"      📊 Completion Rate: {stats['completion_rate']:.1f}%")
    print(f"      🏆 Productivity Score: {stats['productivity_score']}")
    
    # 5. MONITORING I STATUS
    print("\n5. 🔧 Monitoring i Status systemu...")
    
    # Status Soul
    visibility_info = task_soul.get_function_visibility_info()
    print(f"   Soul functions: {visibility_info['functions']['public']['count']} public")
    
    # Status Being
    mastery_info = task_being.get_function_mastery_info()
    print(f"   Being executions: {mastery_info['intelligent_executions']}")
    
    # Status Kernel
    kernel_status = await intelligent_kernel.get_system_status()
    print(f"   Kernel manages: {kernel_status['managed_beings_count']} beings")
    print(f"   Registered aliases: {kernel_status['aliases_count']}")
    
    # 6. DODATKOWE BEING PRZEZ TEN SAM ALIAS
    print("\n6. 🔄 Tworzenie kolejnego Being z tego samego Soul...")
    
    another_being = await Being.create(
        alias="tm_prod_v1",  # Ten sam alias - Kernel użyje tego samego Soul
        attributes={
            "owner": "another_user",
            "workspace": "team_tasks"
        }
    )
    
    # Dodaj zadanie do nowego Being
    await another_being.execute({
        "action": "add_task",
        "task": "Team standup meeting",
        "priority": "high"
    })
    
    print(f"✅ Utworzono drugie Being: {another_being.ulid}")
    print(f"   Używa tego samego Soul ale ma własne dane")
    
    # Final status
    final_kernel_status = await intelligent_kernel.get_system_status()
    print(f"\n🎯 FINAL STATUS:")
    print(f"   Kernel zarządza: {final_kernel_status['managed_beings_count']} beings")
    print(f"   Registry aliases: {list(final_kernel_status['registry_mappings'].keys())}")
    
    print("\n✅ Demo completed! System działa zgodnie z instrukcjami użytkownika.")

if __name__ == "__main__":
    asyncio.run(demo_instrukcje())
