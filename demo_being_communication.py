
#!/usr/bin/env python3
"""
🔄 Demo Being Communication System - Komunikacja z automatycznym budzeniem
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.postgre_db import Postgre_db
from luxdb.core.being_communication_manager import BeingCommunicationManager, communication_dispenser

async def demo_being_communication():
    """Demonstracja komunikacji między bytami z automatycznym budzeniem"""
    print("🔄 Demo Being Communication System")
    print("=" * 50)

    # Inicjalizacja bazy danych
    await Postgre_db.initialize_db()

    # 1. Stwórz dwóch bytów
    print("\n1. 🧬 Tworzenie dwóch bytów...")
    
    # Being A - aktywny
    being_a = Being(soul_hash="test_hash_a", data={"name": "Alice", "role": "communicator"})
    being_a.ulid = "01HZ123ALICE456789ABCDEF"
    await being_a.save()
    await being_a.activate()  # Aktywuj w systemie
    
    # Being B - nieaktywny (śpiący)
    being_b = Being(soul_hash="test_hash_b", data={"name": "Bob", "role": "responder"})
    being_b.ulid = "01HZ123BOB456789ABCDEF12"
    await being_b.save()
    # Nie aktywujemy - będzie śpić
    
    print(f"   ✅ Being A (Alice): {being_a.ulid} - AKTYWNY")
    print(f"   ✅ Being B (Bob): {being_b.ulid} - ŚPIĄCY")

    # 2. Uruchom dispenser w tle
    print("\n2. 🔔 Uruchamianie Communication Dispenser...")
    dispenser_task = asyncio.create_task(communication_dispenser.start_listening())

    # 3. Test komunikacji bezpośredniej (A → A)
    print("\n3. 📞 Test komunikacji bezpośredniej (aktywny → aktywny)...")
    result1 = await being_a.send_intention_to(
        target_ulid=being_a.ulid,
        intention_type="self_test",
        content="Hello myself!",
        data={"test": "direct_communication"}
    )
    print(f"   Wynik: {result1['communication_type']}")

    # 4. Test komunikacji z budzeniem (A → B)
    print("\n4. 🌅 Test komunikacji z budzeniem (aktywny → śpiący)...")
    result2 = await being_a.send_intention_to(
        target_ulid=being_b.ulid,
        intention_type="wake_up_call",
        content="Hello Bob, wake up!",
        data={"urgent": True, "message": "Meeting in 5 minutes"}
    )
    print(f"   Wynik: {result2['communication_type']}")
    print(f"   Status: {result2['status']}")

    # 5. Czekaj chwilę na dispenser
    print("\n5. ⏳ Czekanie na dispenser...")
    await asyncio.sleep(3)

    # 6. Sprawdź czy Bob został wybudzony
    print("\n6. 🔍 Sprawdzanie statusu bytów...")
    active_beings = BeingCommunicationManager.get_active_beings()
    print(f"   Aktywne byty: {active_beings}")

    if being_b.ulid in active_beings:
        print(f"   ✅ Bob został pomyślnie wybudzony!")
        
        # Test komunikacji bezpośredniej po wybudzeniu
        result3 = await being_a.send_intention_to(
            target_ulid=being_b.ulid,
            intention_type="follow_up",
            content="Are you awake now?",
            data={"test": "post_wake_communication"}
        )
        print(f"   Follow-up communication: {result3['communication_type']}")
    else:
        print(f"   ⚠️ Bob nadal śpi...")

    # 7. Pokaż historię komunikacji
    print("\n7. 📜 Historia komunikacji:")
    
    # Reload beings to get updated communication history
    from luxdb.repository.soul_repository import BeingRepository
    
    alice_updated = await BeingRepository.get_by_ulid(being_a.ulid)
    if alice_updated["success"]:
        alice_history = alice_updated["being"].data.get("communication_history", [])
        print(f"   Alice wysłała: {len(alice_history)} komunikatów")
    
    bob_updated = await BeingRepository.get_by_ulid(being_b.ulid)
    if bob_updated["success"]:
        bob_history = bob_updated["being"].data.get("communication_history", [])
        print(f"   Bob odebrał: {len(bob_history)} komunikatów")
        for msg in bob_history:
            print(f"     - {msg['type']}: {msg['content']}")

    # 8. Cleanup
    print("\n8. 🧹 Cleanup...")
    communication_dispenser.active = False
    dispenser_task.cancel()
    
    await being_a.deactivate()
    if being_b.ulid in BeingCommunicationManager.get_active_beings():
        await being_b.deactivate()

    print("\n✅ Demo zakończone pomyślnie!")
    print("\n🎯 Kluczowe funkcje przetestowane:")
    print("   • Komunikacja bezpośrednia (aktywny → aktywny)")
    print("   • Automatyczne budzenie (aktywny → śpiący)")
    print("   • Dispenser task system")
    print("   • Historia komunikacji")
    print("   • Rejestr aktywnych bytów")

if __name__ == "__main__":
    asyncio.run(demo_being_communication())
