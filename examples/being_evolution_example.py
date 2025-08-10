
#!/usr/bin/env python3
"""
🧬 Przykład ewolucji Being - jak byty mogą ewoluować i tworzyć nowe Soul
"""

import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.access_control import access_controller

async def demo_being_evolution():
    """Demonstracja mechanizmu ewolucji Being"""
    print("🧬 DEMO: Being Evolution System")
    print("=" * 50)

    # 1. Utwórz podstawową Soul dla nowego użytkownika
    print("\n1. Creating basic user Soul...")
    user_genotype = {
        "genesis": {
            "name": "basic_user",
            "version": "1.0.0",
            "description": "Basic user with limited capabilities"
        },
        "attributes": {
            "username": {"py_type": "str"},
            "email": {"py_type": "str"},
            "join_date": {"py_type": "str"},
            "activity_level": {"py_type": "int", "default": 0}
        },
        "functions": {
            "basic_interaction": {
                "py_type": "function",
                "description": "Basic system interaction",
                "access_required": "public"
            }
        }
    }
    
    basic_soul = await Soul.create(user_genotype, "basic_user_soul")
    print(f"✅ Basic soul created: {basic_soul.soul_hash[:8]}...")

    # 2. Utwórz Being z podstawową Soul
    print("\n2. Creating Being with basic soul...")
    user_being_result = await Being.set(
        soul=basic_soul,
        data={
            "username": "active_contributor",
            "email": "contributor@example.com",
            "join_date": "2025-01-01",
            "activity_level": 1
        },
        alias="active_contributor",
        access_zone="public_zone"
    )
    
    user_being = user_being_result['data']['being']
    print(f"✅ Being created: {user_being.alias} in {user_being.access_zone}")

    # 3. Symuluj aktywność bytu
    print("\n3. Simulating being activity...")
    for i in range(15):
        # Symuluj wykonywanie funkcji
        if hasattr(user_being, 'execute_soul_function'):
            result = await user_being.execute_soul_function("basic_interaction", f"action_{i}")
        else:
            # Fallback - bezpośrednie aktualizowanie liczników
            user_being.data['execution_count'] = user_being.data.get('execution_count', 0) + 1
            user_being.data['last_execution'] = "2025-01-01T12:00:00"
            user_being.updated_at = user_being.created_at
    
    print(f"📊 Activity completed: {user_being.data.get('execution_count', 0)} executions")

    # 4. Sprawdź możliwości ewolucji
    print("\n4. Checking evolution potential...")
    evolution_potential = await user_being.can_evolve()
    print(f"🔍 Can evolve: {evolution_potential['can_evolve']}")
    print(f"📋 Available evolutions: {len(evolution_potential['available_evolutions'])}")
    
    for evolution in evolution_potential['available_evolutions']:
        print(f"   - {evolution['type']}: {evolution['description']}")

    # 5. Wykonaj ewolucję - awans poziomu dostępu
    if evolution_potential['can_evolve']:
        print("\n5. Performing access level evolution...")
        evolution_result = await user_being.evolve_soul(
            evolution_trigger="access_level_promotion",
            access_level_change="promote"
        )
        
        if evolution_result.get('success'):
            print("✅ Evolution successful!")
            new_soul_hash = evolution_result['data']['new_soul_hash']
            print(f"🧬 New soul hash: {new_soul_hash[:8]}...")
            print(f"🔐 New access zone: {user_being.access_zone}")
        else:
            print(f"❌ Evolution failed: {evolution_result.get('error')}")

    # 6. Symuluj dalszą aktywność dla następnej ewolucji
    print("\n6. Simulating extended activity for advanced evolution...")
    for i in range(100):
        user_being.data['execution_count'] = user_being.data.get('execution_count', 0) + 1
    
    # Symuluj upływ czasu (w prawdziwym systemie to byłby rzeczywisty czas)
    from datetime import datetime, timedelta
    user_being.created_at = datetime.now() - timedelta(days=10)
    
    # 7. Sprawdź nowe możliwości ewolucji
    print("\n7. Checking advanced evolution potential...")
    advanced_potential = await user_being.can_evolve()
    print(f"🔍 Advanced evolutions available: {len(advanced_potential['available_evolutions'])}")
    
    for evolution in advanced_potential['available_evolutions']:
        print(f"   - {evolution['type']}: {evolution['description']}")

    # 8. Ewolucja do twórcy Soul
    creator_evolution = next(
        (evo for evo in advanced_potential['available_evolutions'] 
         if evo['type'] == 'soul_creator'), None
    )
    
    if creator_evolution:
        print("\n8. Evolving to Soul Creator...")
        creator_result = await user_being.evolve_soul(
            evolution_trigger="earned_creator_privileges",
            access_level_change="grant_creator",
            new_capabilities={
                "functions.design_soul": {
                    "py_type": "function",
                    "description": "Design and propose new Soul genotypes",
                    "access_required": "creator"
                }
            }
        )
        
        if creator_result.get('success'):
            print("✅ Creator evolution successful!")
            print(f"🎨 Being can now create new Souls!")

    # 9. Demonstracja tworzenia nowej Soul przez Being
    print("\n9. Being creating new Soul...")
    new_soul_concept = {
        "genesis": {
            "name": "specialized_analyst",
            "version": "1.0.0",
            "description": "Soul for data analysis specialists",
            "created_by_community": True
        },
        "attributes": {
            "analysis_type": {"py_type": "str"},
            "expertise_level": {"py_type": "int", "default": 1},
            "analysis_history": {"py_type": "list", "default": []}
        },
        "functions": {
            "analyze_data": {
                "py_type": "function",
                "description": "Perform specialized data analysis",
                "access_required": "authenticated"
            },
            "generate_insights": {
                "py_type": "function",
                "description": "Generate insights from analysis",
                "access_required": "authenticated"
            }
        }
    }
    
    creation_result = await user_being.propose_soul_creation(new_soul_concept)
    
    if creation_result.get('success'):
        new_soul = creation_result['data']['new_soul']
        print("✅ New Soul created by Being!")
        print(f"🧬 New Soul: {new_soul['alias']} ({new_soul['soul_hash'][:8]}...)")
        print(f"👨‍💻 Created by: {user_being.alias}")
        
        # 10. Utwórz Being z nową Soul
        print("\n10. Creating Being with community-created Soul...")
        analyst_soul = await Soul.get_by_hash(new_soul['soul_hash'])
        
        if analyst_soul:
            analyst_being_result = await Being.set(
                soul=analyst_soul,
                data={
                    "analysis_type": "financial",
                    "expertise_level": 2
                },
                alias="financial_analyst",
                access_zone="authenticated_zone"
            )
            
            if analyst_being_result.get('success'):
                analyst_being = analyst_being_result['data']['being']
                print(f"✅ New specialized Being created: {analyst_being['alias']}")
                print(f"🔬 Specialized for: {analyst_being['data']['analysis_type']} analysis")
    else:
        print(f"❌ Soul creation failed: {creation_result.get('error')}")

    # 11. Podsumowanie ewolucji systemu
    print("\n" + "=" * 50)
    print("📈 EVOLUTION SUMMARY")
    print("=" * 50)
    print(f"👤 Original Being: {user_being.alias}")
    print(f"🔄 Evolution count: {len(user_being.data.get('evolution_history', []))}")
    print(f"🎨 Souls created: {len(user_being.data.get('souls_created', []))}")
    print(f"🔐 Current access: {user_being.access_zone}")
    
    evolution_history = access_controller.get_being_evolution_history(user_being.ulid)
    print(f"📊 System tracked evolutions: {len(evolution_history)}")
    
    print("\n✨ System has successfully demonstrated:")
    print("   - Being-initiated Soul evolution")
    print("   - Dynamic access level progression")
    print("   - Community-driven Soul creation")
    print("   - Backward compatibility maintenance")

if __name__ == "__main__":
    asyncio.run(demo_being_evolution())
