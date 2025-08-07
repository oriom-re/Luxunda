
"""
Demo Systemu Pierwotnych Bytów
==============================

Demonstracja żywej architektury z Database, Communication i Kernel beings.
"""

import asyncio
from luxdb.core.primitive_beings import PrimitiveSystemOrchestrator

async def demo_primitive_system():
    """Demonstracja systemu pierwotnych bytów"""
    
    print("🧬 === DEMO SYSTEMU PIERWOTNYCH BYTÓW ===")
    
    # Inicjalizacja orkiestratora
    orchestrator = PrimitiveSystemOrchestrator()
    init_result = await orchestrator.initialize()
    print(f"Inicjalizacja: {init_result}")
    
    print("\n" + "="*50)
    print("📊 1. TEST KERNEL BEING - Zarządzanie systemem")
    
    # Test kernel being
    system_status = await orchestrator.process_intention({
        "target_being": "kernel",
        "type": "get_system_status"
    })
    print(f"Status systemu: {system_status}")
    
    # Dodaj zadanie systemowe
    task_result = await orchestrator.process_intention({
        "target_being": "kernel",
        "type": "execute_system_task",
        "task": {"action": "optimize_performance", "priority": 5},
        "priority": 5
    })
    print(f"Zadanie systemowe: {task_result}")
    
    print("\n" + "="*50)
    print("💾 2. TEST DATABASE BEING - Żywa baza danych")
    
    # Utwórz schemat
    schema_result = await orchestrator.process_intention({
        "target_being": "database",
        "type": "create_schema",
        "schema_name": "user_profiles",
        "schema_definition": {
            "fields": ["name", "email", "created_at"],
            "constraints": {"email": "unique"}
        },
        "creator": "demo_system"
    })
    print(f"Schemat utworzony: {schema_result}")
    
    # Zapisz dane
    store_result = await orchestrator.process_intention({
        "target_being": "database",
        "type": "store_data",
        "schema": "user_profiles",
        "data": {
            "name": "Jan Kowalski",
            "email": "jan@example.com",
            "active": True
        }
    })
    print(f"Dane zapisane: {store_result}")
    
    # Pobierz dane
    retrieve_result = await orchestrator.process_intention({
        "target_being": "database",
        "type": "retrieve_data",
        "schema": "user_profiles",
        "filters": {"name": "Jan Kowalski"}
    })
    print(f"Dane pobrane: {retrieve_result}")
    
    print("\n" + "="*50)
    print("🌐 3. TEST COMMUNICATION BEING - Żywa komunikacja")
    
    # Utwórz kanał
    channel_result = await orchestrator.process_intention({
        "target_being": "communication",
        "type": "create_channel",
        "channel_name": "system_notifications",
        "channel_type": "broadcast"
    })
    print(f"Kanał utworzony: {channel_result}")
    
    channel_id = channel_result.get('channel_id')
    
    # Wyślij wiadomość
    message_result = await orchestrator.process_intention({
        "target_being": "communication",
        "type": "send_message",
        "channel_id": channel_id,
        "message": "System został zainicjalizowany pomyślnie!",
        "sender": "kernel"
    })
    print(f"Wiadomość wysłana: {message_result}")
    
    # Nawiąż połączenie websocket
    socket_result = await orchestrator.process_intention({
        "target_being": "communication",
        "type": "establish_socket",
        "client_id": "demo_client_001",
        "socket_type": "websocket",
        "client_info": {"browser": "Chrome", "platform": "Web"}
    })
    print(f"Socket nawiązany: {socket_result}")
    
    # Broadcast wiadomość
    broadcast_result = await orchestrator.process_intention({
        "target_being": "communication",
        "type": "broadcast_message",
        "message": "Witamy w systemie żywych bytów!",
        "sender": "system"
    })
    print(f"Broadcast wysłany: {broadcast_result}")
    
    print("\n" + "="*50)
    print("🔗 4. TEST RELACJI MIĘDZY BYTAMI")
    
    # Sprawdź relacje w systemie
    system_overview = await orchestrator.get_system_overview()
    print(f"Przegląd systemu: {system_overview}")
    
    print("\n" + "="*50)
    print("🧪 5. TEST ZAAWANSOWANYCH INTENCJI")
    
    # Koordynacja między bytami przez kernel
    coordination_result = await orchestrator.process_intention({
        "target_being": "kernel",
        "type": "coordinate_beings",
        "coordination_type": "data_sync",
        "beings": [orchestrator.database.ulid, orchestrator.communication.ulid]
    })
    print(f"Koordynacja bytów: {coordination_result}")
    
    # Zapytanie do bazy przez intencję
    query_result = await orchestrator.process_intention({
        "target_being": "database",
        "type": "query_data",
        "query": {"type": "all", "limit": 10}
    })
    print(f"Zapytanie do bazy: {query_result}")
    
    # Historia komunikacji
    history_result = await orchestrator.process_intention({
        "target_being": "communication",
        "type": "get_message_history",
        "limit": 5
    })
    print(f"Historia komunikacji: {history_result}")
    
    print("\n" + "="*50)
    print("✅ DEMO ZAKOŃCZONE - System pierwotnych bytów działa!")
    
    return orchestrator

if __name__ == "__main__":
    asyncio.run(demo_primitive_system())
