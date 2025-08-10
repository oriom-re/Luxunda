
#!/usr/bin/env python3
"""
🧬 Przykład ewolucji Being przez system Kernel
Demonstracja jak Being może żądać ewolucji, a Kernel ją przeprowadzić.
"""

import asyncio
from datetime import datetime, timedelta
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.kernel_system import kernel_system
from luxdb.core.access_control import access_controller
from database.postgre_db import Postgre_db


async def main():
    print("🧬 LUXDB EVOLUTION SYSTEM DEMO")
    print("=" * 50)
    print("Demonstracja systemu ewolucji Being przez Kernel")
    print()

    # 1. Inicjalizacja systemu
    print("1. Initializing LuxDB system...")
    await Postgre_db.initialize()
    await kernel_system.initialize("default")

    # 2. Utworzenie podstawowego genotypu użytkownika
    print("\n2. Creating basic user soul...")
    user_genotype = {
        "genesis": {
            "name": "basic_user",
            "type": "user_profile",
            "version": "1.0.0",
            "description": "Basic user with learning capabilities"
        },
        "attributes": {
            "name": {"py_type": "str"},
            "skill_level": {"py_type": "int", "default": 1},
            "access_level": {"py_type": "str", "default": "basic"}
        },
        "capabilities": {
            "can_learn": True,
            "can_interact": True
        }
    }

    user_soul = await Soul.create(user_genotype, alias="basic_user_soul")
    print(f"✅ Created user soul: {user_soul.soul_hash[:8]}...")

    # 3. Utworzenie bytu użytkownika
    print("\n3. Creating user being...")
    user_data = {
        "name": "Alice Learning",
        "skill_level": 1,
        "access_level": "basic"
    }

    user_being_result = await Being.set(user_soul, user_data, alias="alice_user")
    user_being = await Being._get_by_ulid_internal(
        user_being_result["data"]["being"]["ulid"]
    )
    print(f"✅ Created user being: {user_being.alias} ({user_being.ulid[:8]}...)")

    # 4. Symulacja aktywności aby kwalifikować się do ewolucji
    print("\n4. Simulating user activity...")
    for i in range(15):
        user_being.data['execution_count'] = user_being.data.get('execution_count', 0) + 1
        if i % 5 == 0:
            print(f"   📊 Execution count: {user_being.data['execution_count']}")

    await user_being.save()
    print(f"✅ Final execution count: {user_being.data['execution_count']}")

    # 5. Sprawdzenie możliwości ewolucji
    print("\n5. Checking evolution potential...")
    evolution_potential = await user_being.can_evolve()
    print(f"🔍 Can evolve: {evolution_potential['can_evolve']}")
    
    if evolution_potential['available_evolutions']:
        print("📋 Available evolutions:")
        for evo in evolution_potential['available_evolutions']:
            print(f"   - {evo['type']}: {evo['description']}")

    # 6. Being żąda ewolucji (ale nie może się sam ewoluować)
    print("\n6. Being requests evolution...")
    evolution_request_result = await user_being.request_evolution(
        evolution_trigger="learning_milestone_achieved",
        new_capabilities={
            "attributes.advanced_skills": {"py_type": "list", "default": []},
            "functions.analyze_data": {"py_type": "function", "description": "Advanced data analysis"}
        },
        access_level_change="promote"
    )

    if evolution_request_result.get('success'):
        print("✅ Evolution request submitted successfully")
        print(f"   Request ID: {evolution_request_result['data']['request_id']}")
        print(f"   Message: {evolution_request_result['data']['message']}")
    else:
        print(f"❌ Evolution request failed: {evolution_request_result.get('error')}")
        return

    # 7. Kernel sprawdza oczekujące żądania
    print("\n7. Kernel checking pending evolution requests...")
    pending_requests = await kernel_system.get_pending_evolution_requests()
    print(f"📋 Pending requests: {len(pending_requests)}")
    
    for request in pending_requests:
        print(f"   - Being: {request['being_alias']} ({request['being_ulid'][:8]}...)")
        print(f"     Trigger: {request['request']['evolution_trigger']}")
        print(f"     Requested: {request['request']['request_timestamp']}")

    # 8. Kernel przetwarza żądanie ewolucji
    print("\n8. Kernel processing evolution request...")
    if pending_requests:
        first_request = pending_requests[0]
        
        evolution_result = await kernel_system.process_evolution_request(
            being_ulid=first_request['being_ulid'],
            request_id=first_request['request_id'],
            approve=True,
            processed_by="admin_kernel"
        )

        if evolution_result.get('success'):
            print("✅ Evolution approved and executed!")
            print(f"   Old soul: {evolution_result['data']['old_soul_hash'][:8]}...")
            print(f"   New soul: {evolution_result['data']['new_soul_hash'][:8]}...")
            print(f"   Processed by: {evolution_result['data']['processed_by']}")
        else:
            print(f"❌ Evolution processing failed: {evolution_result.get('error')}")

    # 9. Sprawdzenie historii ewolucji przez relacje
    print("\n9. Checking evolution history from relationships...")
    evolution_history = await kernel_system.get_evolution_history_for_being(user_being.ulid)
    
    print(f"📊 Evolution history entries: {len(evolution_history)}")
    for i, evolution in enumerate(evolution_history):
        print(f"\n   Evolution #{i+1}:")
        print(f"   - From soul: {evolution['old_soul_hash'][:8]}...")
        print(f"   - To soul: {evolution['new_soul_hash'][:8]}...")
        print(f"   - Trigger: {evolution['evolution_trigger']}")
        print(f"   - Processed by: {evolution['processed_by']}")
        print(f"   - Date: {evolution['processed_at']}")

    # 10. Sprawdzenie aktualnego stanu bytu
    print("\n10. Checking being's current state...")
    refreshed_being = await Being.get_by_ulid(user_being.ulid)
    current_soul = await refreshed_being.get_soul()
    
    print(f"🔄 Being {refreshed_being.alias}:")
    print(f"   - Current soul: {refreshed_being.soul_hash[:8]}...")
    print(f"   - Access zone: {refreshed_being.access_zone}")
    print(f"   - Soul version: {current_soul.get_version()}")
    print(f"   - Parent soul: {current_soul.get_parent_hash()[:8] if current_soul.get_parent_hash() else 'None'}...")

    # 11. Test drugiej ewolucji
    print("\n11. Testing second evolution request...")
    
    # Dodaj więcej aktywności
    for i in range(50):
        refreshed_being.data['execution_count'] = refreshed_being.data.get('execution_count', 0) + 1

    # Symuluj upływ czasu
    refreshed_being.created_at = datetime.now() - timedelta(days=10)
    await refreshed_being.save()

    # Żądaj kolejnej ewolucji
    second_evolution = await refreshed_being.request_evolution(
        evolution_trigger="expert_level_achieved",
        new_capabilities={
            "attributes.expert_rating": {"py_type": "float", "default": 0.0},
            "capabilities.can_mentor": True
        },
        access_level_change="grant_creator"
    )

    if second_evolution.get('success'):
        print("✅ Second evolution request submitted")
        
        # Kernel automatycznie przetwarza
        pending = await kernel_system.get_pending_evolution_requests()
        if pending:
            second_result = await kernel_system.process_evolution_request(
                being_ulid=pending[0]['being_ulid'],
                request_id=pending[0]['request_id'],
                approve=True
            )
            
            if second_result.get('success'):
                print("✅ Second evolution completed!")

    # 12. Finalna historia ewolucji
    print("\n12. Final evolution history...")
    final_history = await kernel_system.get_evolution_history_for_being(user_being.ulid)
    
    print(f"📈 Total evolutions: {len(final_history)}")
    print("\n🌟 EVOLUTION TIMELINE:")
    for i, evo in enumerate(final_history):
        print(f"   {i+1}. {evo['processed_at'][:19]} - {evo['evolution_trigger']}")
        print(f"      Soul: {evo['old_soul_hash'][:8]}... → {evo['new_soul_hash'][:8]}...")
        print(f"      By: {evo['processed_by']}")

    print("\n" + "=" * 50)
    print("✨ EVOLUTION SYSTEM DEMO COMPLETED")
    print("=" * 50)
    print("Key concepts demonstrated:")
    print("• Being can only REQUEST evolution, not execute it")
    print("• Kernel has authority to approve/reject evolution")
    print("• Each evolution creates relationship records")
    print("• Full evolution history is preserved in relationships")
    print("• Being maintains continuity through ULID despite soul changes")


if __name__ == "__main__":
    asyncio.run(main())
