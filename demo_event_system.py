
"""
Demo systemu eventów bazodanowych
"""

import asyncio
from datetime import datetime

from luxdb.core.event_listener import event_bus, DatabaseEventListener
from luxdb.models.event import Event
from database.postgre_db import Postgre_db

async def demo_database_event_system():
    """
    Demonstracja systemu eventów bazodanowych
    """
    print("🚀 Database Event System Demo")
    print("=" * 50)
    
    # Inicjalizuj bazę danych
    await Postgre_db.initialize()
    
    # 1. Utwórz listenery dla różnych modułów frontendu
    print("\n1. Creating listeners...")
    
    progress_listener = await event_bus.create_listener("progress_ui")
    notification_listener = await event_bus.create_listener("notification_system")
    analytics_listener = await event_bus.create_listener("analytics_tracker")
    
    # 2. Subskrybuj różne typy eventów
    print("\n2. Setting up subscriptions...")
    
    # Progress UI - interesuje się postępami
    progress_listener.subscribe("data_processing", lambda data: print(f"📊 UI Progress: {data['progress']}%"))
    progress_listener.subscribe("file_upload", lambda data: print(f"📤 Upload: {data['progress']}%"))
    
    # Notification system - wszystkie ważne eventy
    notification_listener.subscribe("error", lambda data: print(f"🚨 Error: {data.get('error', 'Unknown')}"))
    notification_listener.subscribe("completion", lambda data: print(f"✅ Completed: {data.get('result', 'Success')}"))
    
    # Analytics - zbiera metryki
    analytics_listener.subscribe("user_action", lambda data: print(f"📈 Analytics: {data}"))
    
    # 3. Uruchom listenery w tle
    print("\n3. Starting listeners...")
    
    # Uruchom każdy listener w osobnym task'u
    tasks = []
    for listener in [progress_listener, notification_listener, analytics_listener]:
        task = asyncio.create_task(listener.start_listening(poll_interval=0.5))
        tasks.append(task)
    
    # Poczekaj chwilę na uruchomienie
    await asyncio.sleep(1)
    
    # 4. Symuluj różne zdarzenia
    print("\n4. Emitting events...")
    
    # Długotrwały proces z postępem
    processing_event = await event_bus.emit_event(
        "data_processing", 
        {"operation": "analyze_data", "file": "dataset.csv"}
    )
    
    # Symuluj postęp
    for progress in [20, 40, 60, 80, 100]:
        await asyncio.sleep(1)
        await processing_event.update_progress(
            progress, 
            "processing" if progress < 100 else "completed",
            {"processed_records": progress * 10}
        )
        print(f"🔄 Processing: {progress}%")
    
    # Upload z błędem
    print("\n📤 Starting file upload...")
    upload_event = await event_bus.emit_event(
        "file_upload",
        {"filename": "document.pdf", "size": 5242880}
    )
    
    await upload_event.update_progress(30, "uploading")
    await asyncio.sleep(1)
    await upload_event.fail("Network timeout", {"retry_count": 3})
    
    # Event użytkownika
    await event_bus.emit_event(
        "user_action",
        {"action": "button_click", "button_id": "save", "user_id": "user123"}
    )
    
    print("\n5. Waiting for processing...")
    await asyncio.sleep(3)
    
    # Zatrzymaj listenery
    for listener in [progress_listener, notification_listener, analytics_listener]:
        listener.stop_listening()
    
    print("\n✅ Demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_database_event_system())
