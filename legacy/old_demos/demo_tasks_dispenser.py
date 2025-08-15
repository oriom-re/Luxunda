
#!/usr/bin/env python3
"""
🎯 Demo: Tasks + Dispenser System
Proste, ale potężne zarządzanie zadaniami
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.postgre_db import Postgre_db

async def demo_tasks_dispenser():
    print("🎯 Demo: Tasks + Dispenser System")
    print("=" * 50)
    
    # 1. Inicjalizacja bazy
    print("\n1. 🔄 Database initialization...")
    pool = await Postgre_db.get_db_pool()
    if not pool:
        print("❌ Database connection failed")
        return
    
    # 2. Załaduj genotypy z plików
    print("\n2. 🧬 Loading genotypes...")
    
    from luxdb.utils.genotype_loader import GenotypeLoader
    loader = GenotypeLoader()
    
    # Załaduj tasks soul
    tasks_soul = await loader.load_soul_from_file("genotypes/tasks_soul.json")
    if tasks_soul:
        print(f"✅ Tasks Soul loaded: {tasks_soul.alias}")
    
    # Załaduj dispenser soul  
    dispenser_soul = await loader.load_soul_from_file("genotypes/dispenser_soul.json")
    if dispenser_soul:
        print(f"✅ Dispenser Soul loaded: {dispenser_soul.alias}")
    
    # 3. Utwórz singleton dispenser
    print("\n3. 📦 Creating singleton dispenser...")
    dispenser_being = await Being.get_or_create(
        soul=dispenser_soul,
        alias="main_dispenser",
        unique_by="soul_hash"  # Singleton pattern
    )
    
    # Test dispenser status
    status_result = await dispenser_being.execute()
    print(f"📊 Dispenser status: {status_result.get('data', {})}")
    
    # 4. Utwórz różne zadania
    print("\n4. 🎯 Creating various tasks...")
    
    tasks = []
    
    # Task 1: Message task
    message_task = await Being.create(
        soul=tasks_soul,
        alias="message_task_001",
        attributes={
            "task_type": "message",
            "payload": {"message": "Hello from task system!"}
        }
    )
    tasks.append(message_task)
    
    # Task 2: Calculation task  
    calc_task = await Being.create(
        soul=tasks_soul,
        alias="calc_task_001", 
        attributes={
            "task_type": "calculation",
            "payload": {"operation": "add", "a": 5, "b": 3}
        }
    )
    tasks.append(calc_task)
    
    # Task 3: API call task
    api_task = await Being.create(
        soul=tasks_soul,
        alias="api_task_001",
        attributes={
            "task_type": "api_call", 
            "payload": {"endpoint": "/users", "method": "GET"}
        }
    )
    tasks.append(api_task)
    
    print(f"✅ Created {len(tasks)} tasks")
    
    # 5. Dispatch zadań przez dispenser
    print("\n5. 📤 Dispatching tasks...")
    
    for task in tasks:
        task_status = await task.execute()
        task_data = task_status.get('data', {})
        
        dispatch_request = {
            "action": "dispatch",
            "task_id": task_data.get('task_id'),
            "task_type": task_data.get('task_type'),
            "data": task_data.get('payload')
        }
        
        dispatch_result = await dispenser_being.execute(dispatch_request)
        dispatch_data = dispatch_result.get('data', {})
        
        print(f"📦 Task {dispatch_data.get('task_id')} → {dispatch_data.get('target')}")
    
    # 6. Sprawdź kolejki
    print("\n6. 📋 Checking queues...")
    
    queues_result = await dispenser_being.execute({"action": "get_queue", "target": "both"})
    queues_data = queues_result.get('data', {})
    
    print(f"🖥️  Frontend queue: {len(queues_data.get('frontend_queue', []))} tasks")
    print(f"⚙️  Backend queue: {len(queues_data.get('backend_queue', []))} tasks")
    
    # 7. Symuluj procesowanie zadań
    print("\n7. ⚙️ Processing tasks...")
    
    for task in tasks:
        # Update task status to processing
        await task.execute({
            "action": "update_status", 
            "status": "processing"
        })
        
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        # Complete with result
        result = {"processed": True, "timestamp": "2025-01-30T12:00:00"}
        await task.execute({
            "action": "update_status",
            "status": "completed", 
            "result": result
        })
        
        # Notify dispenser about completion
        await dispenser_being.execute({
            "action": "complete_task",
            "task_id": task.data.get('task_id'),
            "result": result
        })
    
    # 8. Historia zadań
    print("\n8. 📚 Task history...")
    
    for task in tasks:
        history_result = await task.execute({"action": "get_history"})
        history_data = history_result.get('data', {})
        
        print(f"📖 Task {history_data.get('task_id')}: {history_data.get('total_entries')} history entries")
        
        if history_data.get('history'):
            last_entry = history_data['history'][-1]
            print(f"   Latest: {last_entry.get('action', 'N/A')} at {last_entry.get('timestamp', 'N/A')}")
    
    # 9. Final status
    print("\n9. 📊 Final system status...")
    
    final_status = await dispenser_being.execute()
    final_data = final_status.get('data', {})
    
    print(f"📦 Dispenser statistics:")
    stats = final_data.get('statistics', {})
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print(f"\n✅ Demo completed successfully!")

async def main():
    try:
        await demo_tasks_dispenser()
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
