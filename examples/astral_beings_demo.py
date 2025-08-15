
#!/usr/bin/env python3
"""
Complete Astral Beings Library Demo
==================================

Kompleksowa demonstracja biblioteki Astral Beings.
Pokazuje wszystkie możliwości od podstawowych po zaawansowane.
"""

import asyncio
import sys
import os

# Dodaj ścieżki do importów
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astral_beings import AstralBeing, SoulTemplate, BeingGenerator, SoulGenerator
from astral_beings import BasicTemplates, AdvancedTemplates, QuickStart
from astral_beings import quick_guardian, quick_assistant, quick_party
from astral_beings import list_archetypes, get_archetype_info

async def main():
    """Główna demonstracja biblioteki"""
    
    print("🌌 === ASTRAL BEINGS LIBRARY - COMPLETE DEMO ===")
    print("Biblioteka do tworzenia inteligentnych bytów astralnych")
    print("=" * 60)
    
    # 1. Podstawowe informacje o bibliotece
    print("\n📚 1. LIBRARY OVERVIEW")
    print(f"🎭 Available archetypes: {', '.join(list_archetypes())}")
    
    # Pokaż info o jednym archetyp
    guardian_info = get_archetype_info("guardian")
    print(f"🛡️ Guardian archetype:")
    print(f"   Attributes: {guardian_info['base_attributes']}")
    print(f"   Abilities: {guardian_info['abilities']}")
    
    # 2. Szybkie tworzenie bytów
    print("\n⚡ 2. QUICK CREATION")
    
    # Prosty strażnik
    guardian = await quick_guardian("Protector")
    print(f"✨ Created: {guardian}")
    
    # Prosty asystent
    assistant = await quick_assistant("Helper")  
    print(f"✨ Created: {assistant}")
    
    # 3. Grupa bytów
    print("\n🎭 3. PARTY CREATION")
    party = await quick_party(3)
    print(f"🎪 Created party of {len(party)} beings:")
    for being in party:
        print(f"   - {being.name} ({being.archetype})")
    
    # 4. Testowanie podstawowych funkcji
    print("\n🧪 4. BASIC FUNCTIONS TEST")
    
    # Test komunikacji
    comm_result = await guardian.commune("Greetings from the astral realm!")
    echo = comm_result.get('data', {}).get('result', {}).get('astral_echo', 'No echo')
    print(f"💬 Communication: {echo}")
    
    # Test kanalizowania energii
    energy_result = await guardian.channel_power("shield", target="ancient_temple")
    effect = energy_result.get('data', {}).get('result', {}).get('effect', 'No effect')
    print(f"⚡ Energy channeling: {effect}")
    
    # Test medytacji
    meditation_result = await guardian.meditate(60)
    med_data = meditation_result.get('data', {}).get('result', {})
    print(f"🧘 Meditation: Restored {med_data.get('energy_restored', 0)} energy")
    
    # 5. Zaawansowane tworzenie
    print("\n🔬 5. ADVANCED CREATION")
    
    # Niestandardowy byt
    custom_being = await BeingGenerator.create_specialized_being({
        "archetype": "mage",
        "name": "CodeWizard",
        "attributes": {
            "programming_power": 95,
            "debugging_skill": 90,
            "algorithm_mastery": 85
        },
        "abilities": ["code", "debug", "optimize", "architect"],
        "description": "Master of code and digital architectures"
    })
    
    print(f"🧙 Created custom being: {custom_being}")
    
    # Test custom akcji
    code_result = await custom_being.invoke("channel_energy", 
                                          ability="code",
                                          target="astral_application")
    print(f"💻 Coding action: {code_result.get('data', {}).get('result', {}).get('effect', 'Coded successfully')}")
    
    # 6. Zaawansowane szablony
    print("\n🏛️ 6. ADVANCED TEMPLATES")
    
    # AI Companion
    ai_template = AdvancedTemplates.get_ai_companion_template()
    ai_companion = await BeingGenerator.create_specialized_being(ai_template)
    print(f"🤖 Created AI Companion: {ai_companion}")
    
    # Data Guardian
    data_template = AdvancedTemplates.get_data_guardian_template()
    data_guardian = await BeingGenerator.create_specialized_being(data_template)
    print(f"🔒 Created Data Guardian: {data_guardian}")
    
    # 7. Symulacja interakcji
    print("\n🎬 7. INTERACTION SIMULATION")
    
    # Scenariusz: Strażnik, Asystent i AI współpracują
    print("📜 Scenario: Guardian, Assistant and AI working together")
    
    # Strażnik zabezpiecza
    guard_action = await guardian.channel_power("protect", target="data_center")
    print(f"   🛡️ Guardian: {guard_action.get('data', {}).get('result', {}).get('effect', 'Protected')}")
    
    # Asystent organizuje
    assist_action = await assistant.invoke("channel_energy", ability="organize", target="workflow")
    print(f"   📋 Assistant: {assist_action.get('data', {}).get('result', {}).get('effect', 'Organized')}")
    
    # AI analizuje
    ai_action = await ai_companion.invoke("channel_energy", ability="analyze", target="system_performance")
    print(f"   🧠 AI Companion: {ai_action.get('data', {}).get('result', {}).get('effect', 'Analyzed')}")
    
    # 8. Zarządzanie energią
    print("\n🔋 8. ENERGY MANAGEMENT")
    
    print(f"⚡ Energy levels before intensive work:")
    beings = [guardian, assistant, ai_companion]
    for being in beings:
        print(f"   {being.name}: {being.energy_level}")
    
    # Wykonaj intensywną pracę
    for being in beings:
        await being.invoke("channel_energy", ability="assist", power=30)
    
    print(f"⚡ Energy levels after work:")
    for being in beings:
        print(f"   {being.name}: {being.energy_level}")
    
    # Medytacja grupowa
    print("🧘 Group meditation session...")
    for being in beings:
        await being.meditate(40)
    
    print(f"⚡ Energy levels after meditation:")
    for being in beings:
        print(f"   {being.name}: {being.energy_level}")
    
    # 9. Statystyki i podsumowanie
    print("\n📊 9. SUMMARY AND STATISTICS")
    
    total_beings = len([guardian, assistant, ai_companion, custom_being, data_guardian])
    archetypes_used = set([b.archetype for b in [guardian, assistant, ai_companion, custom_being, data_guardian]])
    
    print(f"🎭 Total beings created: {total_beings}")
    print(f"🏛️ Archetypes used: {', '.join(archetypes_used)}")
    print(f"⚡ Average energy level: {sum([b.energy_level for b in beings]) // len(beings)}")
    
    print("\n✅ DEMO COMPLETED SUCCESSFULLY!")
    print("🌌 The astral beings are ready to serve in your applications!")
    
    return {
        "beings_created": total_beings,
        "archetypes_used": list(archetypes_used),
        "demo_successful": True
    }

async def run_quickstart_examples():
    """Uruchamia wszystkie przykłady QuickStart"""
    print("\n🚀 === QUICKSTART EXAMPLES ===")
    return await QuickStart.run_all_examples()

if __name__ == "__main__":
    # Uruchom główną demonstrację
    print("Starting Astral Beings Library Demo...")
    
    try:
        # Główne demo
        demo_result = asyncio.run(main())
        
        print("\n" + "=" * 60)
        
        # QuickStart przykłady
        examples_result = asyncio.run(run_quickstart_examples())
        
        print(f"\n🎉 ALL DEMOS COMPLETED!")
        print(f"📈 Demo statistics: {demo_result}")
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        sys.exit(1)
