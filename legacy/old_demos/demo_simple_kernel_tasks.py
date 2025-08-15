
#!/usr/bin/env python3
"""
🧠 Demo Simple Kernel z systemem zadań

Pokazuje jak:
- Kernel odbiera zadania i deleguje do modułów
- Auth sprawdza użytkownika i zwraca wynik
- System działa asynchronicznie bez blokowania
- Task Being komunikują się między modułami
"""

import asyncio
from luxdb.core.simple_kernel import simple_kernel

async def demo_simple_kernel_tasks():
    """Demonstracja systemu zadań"""
    print("🚀 Simple Kernel Task System Demo")
    print("=" * 50)
    
    # 1. Inicjalizacja Kernel
    print("\n1. 🧠 Initializing Simple Kernel...")
    kernel_being = await simple_kernel.initialize()
    print(f"   Kernel ready: {kernel_being.alias}")
    
    # 2. Test basic task execution
    print("\n2. 📋 Creating basic tasks...")
    
    # Ping task
    ping_task_id = await simple_kernel.create_task(
        task_type="ping",
        target_module="kernel",  # Kernel sam obsłuży
        payload={}
    )
    
    # Auth task
    auth_task_id = await simple_kernel.create_task(
        task_type="auth",
        target_module="auth",
        payload={
            "action": "authenticate",
            "user_id": "demo_user",
            "token": "demo_token_123"
        }
    )
    
    # Status task
    status_task_id = await simple_kernel.create_task(
        task_type="status",
        target_module="kernel",
        payload={}
    )
    
    print(f"   Created tasks: {ping_task_id[:8]}..., {auth_task_id[:8]}..., {status_task_id[:8]}...")
    
    # 3. Oczekaj na zakończenie zadań
    print("\n3. ⏳ Waiting for task completion...")
    await asyncio.sleep(2)  # Czas na przetworzenie
    
    # 4. Sprawdź wyniki
    print("\n4. 📊 Task Results:")
    
    for task_id, name in [
        (ping_task_id, "Ping"),
        (auth_task_id, "Auth"),
        (status_task_id, "Status")
    ]:
        status = simple_kernel.get_task_status(task_id)
        if status:
            print(f"\n   {name} Task ({task_id[:8]}...):")
            print(f"   Status: {status['status']}")
            if status['result']:
                print(f"   Result: {status['result']}")
            if status['error']:
                print(f"   Error: {status['error']}")
        else:
            print(f"   {name} Task: Already cleaned up")
    
    # 5. Test concurrent tasks
    print("\n5. 🔄 Testing concurrent tasks...")
    
    concurrent_tasks = []
    for i in range(5):
        task_id = await simple_kernel.create_task(
            task_type="echo",
            target_module="kernel",
            payload={"message": f"Concurrent message {i+1}"}
        )
        concurrent_tasks.append(task_id)
    
    print(f"   Created {len(concurrent_tasks)} concurrent tasks")
    
    # Oczekaj na zakończenie
    await asyncio.sleep(1)
    
    # Sprawdź wyniki
    completed_count = 0
    for task_id in concurrent_tasks:
        status = simple_kernel.get_task_status(task_id)
        if status and status['status'] == 'completed':
            completed_count += 1
    
    print(f"   Completed: {completed_count}/{len(concurrent_tasks)} tasks")
    
    # 6. System status
    print("\n6. 🖥️ System Status:")
    system_status = simple_kernel.get_system_status()
    for key, value in system_status.items():
        print(f"   {key}: {value}")
    
    # 7. Test auth module specifically
    print("\n7. 🔐 Testing Auth Module...")
    
    # Test valid auth
    valid_auth_task = await simple_kernel.create_task(
        task_type="auth",
        target_module="auth",
        payload={
            "action": "authenticate",
            "user_id": "valid_user",
            "token": "valid_token"
        }
    )
    
    # Test invalid auth  
    invalid_auth_task = await simple_kernel.create_task(
        task_type="auth", 
        target_module="auth",
        payload={
            "action": "authenticate",
            "user_id": "",
            "token": ""
        }
    )
    
    await asyncio.sleep(1)
    
    # Sprawdź wyniki auth
    valid_result = simple_kernel.get_task_status(valid_auth_task)
    invalid_result = simple_kernel.get_task_status(invalid_auth_task)
    
    print("   Valid Auth:")
    if valid_result and valid_result['result']:
        auth_data = valid_result['result']
        print(f"     Authenticated: {auth_data.get('authenticated')}")
        print(f"     Permissions: {auth_data.get('permissions')}")
    
    print("   Invalid Auth:")
    if invalid_result and invalid_result['result']:
        auth_data = invalid_result['result']
        print(f"     Authenticated: {auth_data.get('authenticated')}")
        print(f"     Error: {auth_data.get('error')}")
    
    print("\n✅ Simple Kernel Task Demo completed!")

async def demo_with_task_listeners():
    """Demo z listenerami zadań"""
    print("\n🔔 Testing Task Listeners...")
    
    # Listener function
    async def task_completed_listener(task_id: str, task):
        print(f"🔔 Listener: Task {task_id[:8]}... completed with status: {task.status}")
        if task.result:
            print(f"    Result preview: {str(task.result)[:50]}...")
    
    # Utwórz zadanie z listenerem
    task_id = await simple_kernel.create_task(
        task_type="ping",
        target_module="kernel",
        payload={"timestamp": "demo"}
    )
    
    # Dodaj listener
    simple_kernel.add_task_listener(task_id, task_completed_listener)
    
    # Oczekaj na powiadomienie
    await asyncio.sleep(1)
    
    print("✅ Task listener demo completed!")

async def main():
    """Główna funkcja demo"""
    try:
        await demo_simple_kernel_tasks()
        await demo_with_task_listeners()
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
