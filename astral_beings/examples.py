
"""
QuickStart Examples for Astral Beings
====================================

Gotowe przykłady użycia biblioteki - od podstawowych do zaawansowanych.
"""

import asyncio
from typing import List, Dict, Any
from .core import AstralBeing, SoulTemplate
from .generators import BeingGenerator, SoulGenerator
from .templates import BasicTemplates, AdvancedTemplates

class QuickStart:
    """Klasa z gotowymi przykładami użycia"""
    
    @staticmethod
    async def hello_astral_world():
        """Najprostszy przykład - stworzenie pierwszego astralnego bytu"""
        print("🌟 === Hello Astral World Example ===")
        
        # Stwórz prostego strażnika
        guardian = await BasicTemplates.create_guardian("MyGuardian")
        
        print(f"✨ Created: {guardian}")
        print(f"📊 Energy: {guardian.energy_level}")
        print(f"🏛️ Archetype: {guardian.archetype}")
        
        # Przetestuj podstawowe funkcje
        result = await guardian.commune("Hello from astral plane!")
        print(f"💬 Communion result: {result.get('data', {}).get('result', {}).get('astral_echo')}")
        
        # Kanalizuj energię
        energy_result = await guardian.channel_power("shield", target="sacred_temple")
        print(f"🛡️ Shield result: {energy_result.get('data', {}).get('result', {}).get('effect')}")
        
        return guardian
    
    @staticmethod
    async def create_party_example():
        """Przykład tworzenia grupy różnorodnych bytów"""
        print("🌟 === Create Astral Party Example ===")
        
        # Utwórz grupę 4 bytów
        party = await BeingGenerator.create_party(4)
        
        print(f"🎭 Created party of {len(party)} beings:")
        for i, being in enumerate(party, 1):
            print(f"  {i}. {being.name} ({being.archetype}) - Energy: {being.energy_level}")
        
        # Każdy byt wykona swoją specjalną akcję
        print("\n🎯 Party in action:")
        for being in party:
            if being.archetype == "guardian":
                result = await being.channel_power("protect", target="the_party")
            elif being.archetype == "healer": 
                result = await being.channel_power("heal", target="wounded_ally")
            elif being.archetype == "mage":
                result = await being.channel_power("cast_spell", target="enemies")
            elif being.archetype == "scout":
                result = await being.channel_power("scout", target="unknown_territory")
            else:
                result = await being.commune("Ready for adventure!")
            
            effect = result.get('data', {}).get('result', {}).get('effect', 'Action completed')
            print(f"  ⚡ {being.name}: {effect}")
        
        return party
    
    @staticmethod
    async def custom_being_example():
        """Przykład tworzenia niestandardowego bytu"""
        print("🌟 === Custom Astral Being Example ===")
        
        # Utwórz niestandardowego bytu z unikalnymi zdolnościami
        custom_being = await BeingGenerator.create_specialized_being({
            "archetype": "mage",
            "name": "Codex",
            "attributes": {
                "programming_skill": 95,
                "debug_power": 90,
                "algorithm_wisdom": 85,
                "code_clarity": 80
            },
            "abilities": ["code", "debug", "optimize", "refactor", "test"],
            "description": "Astral being specialized in programming and code magic"
        })
        
        print(f"✨ Created custom being: {custom_being}")
        
        # Test custom ability through generic invoke
        result = await custom_being.invoke("channel_energy", 
                                         ability="code", 
                                         target="new_application",
                                         power=20)
        
        print(f"💻 Coding result: {result.get('data', {}).get('result', {}).get('effect')}")
        
        return custom_being
    
    @staticmethod
    async def meditation_and_energy_example():
        """Przykład zarządzania energią astralną"""
        print("🌟 === Energy Management Example ===")
        
        # Utwórz bytu
        mage = await BasicTemplates.create_assistant("EnergyMage")
        print(f"✨ Created: {mage} (Energy: {mage.energy_level})")
        
        # Wykonaj kilka kosztownych akcji
        for i in range(3):
            result = await mage.channel_power("assist", power=25, target=f"task_{i+1}")
            effect = result.get('data', {}).get('result', {})
            print(f"  ⚡ Task {i+1}: {effect.get('effect')} (Energy: {effect.get('remaining_energy')})")
        
        # Medytuj aby przywrócić energię
        print("\n🧘 Meditation session:")
        meditation_result = await mage.meditate(duration=80)
        result_data = meditation_result.get('data', {}).get('result', {})
        print(f"  🔋 Energy restored: {result_data.get('energy_restored')} points")
        print(f"  ✨ Current energy: {result_data.get('current_energy')}")
        
        return mage
    
    @staticmethod
    async def communication_example():
        """Przykład komunikacji między bytami astralnymi"""
        print("🌟 === Astral Communication Example ===")
        
        # Utwórz dwa byty
        messenger = await BasicTemplates.create_messenger("Herald")
        scholar = await BasicTemplates.create_scholar("Librarian")
        
        print(f"📡 Created beings: {messenger.name} and {scholar.name}")
        
        # Symuluj komunikację
        messages = [
            "Greetings from the astral messenger service!",
            "I seek knowledge about ancient astral arts",
            "The library is open to all seeking wisdom"
        ]
        
        beings = [messenger, scholar, messenger]
        
        for i, (being, message) in enumerate(zip(beings, messages)):
            result = await being.commune(message)
            response = result.get('data', {}).get('result', {})
            print(f"  💬 {being.name}: {message}")
            print(f"     Echo: {response.get('astral_echo')}")
        
        return [messenger, scholar]
    
    @staticmethod
    async def advanced_ai_companion_example():
        """Przykład zaawansowanego towarzysza AI"""
        print("🌟 === Advanced AI Companion Example ===")
        
        # Utwórz zaawansowanego towarzysza AI
        template = AdvancedTemplates.get_ai_companion_template()
        ai_companion = await BeingGenerator.create_specialized_being(template)
        
        print(f"🤖 Created AI Companion: {ai_companion}")
        
        # Test różnych zdolności
        abilities_to_test = ["converse", "learn", "create", "analyze"]
        
        for ability in abilities_to_test:
            result = await ai_companion.invoke("channel_energy", 
                                             ability=ability,
                                             target="user_interaction")
            
            effect = result.get('data', {}).get('result', {}).get('effect', f"{ability} completed")
            print(f"  🧠 {ability.title()}: {effect}")
        
        return ai_companion
    
    @staticmethod
    async def run_all_examples():
        """Uruchom wszystkie przykłady po kolei"""
        print("🌌 === Running All Astral Beings Examples ===\n")
        
        examples = [
            QuickStart.hello_astral_world,
            QuickStart.create_party_example,
            QuickStart.custom_being_example, 
            QuickStart.meditation_and_energy_example,
            QuickStart.communication_example,
            QuickStart.advanced_ai_companion_example
        ]
        
        results = []
        for example in examples:
            try:
                result = await example()
                results.append(result)
                print()  # Dodaj pustą linię między przykładami
            except Exception as e:
                print(f"❌ Error in example: {e}")
                results.append(None)
        
        print("✅ All examples completed!")
        return results


# Funkcje pomocnicze dla szybkiego startu
async def quick_guardian(name: str = "Guardian") -> AstralBeing:
    """Szybkie tworzenie strażnika"""
    return await BasicTemplates.create_guardian(name)

async def quick_assistant(name: str = "Assistant") -> AstralBeing:
    """Szybkie tworzenie asystenta"""
    return await BasicTemplates.create_assistant(name)

async def quick_party(size: int = 3) -> List[AstralBeing]:
    """Szybkie tworzenie grupy"""
    return await BeingGenerator.create_party(size)

def list_archetypes() -> List[str]:
    """Lista dostępnych archetypów"""
    return list(SoulGenerator.ARCHETYPES.keys())

def get_archetype_info(archetype: str) -> Dict[str, Any]:
    """Informacje o konkretnym archetyp"""
    if archetype not in SoulGenerator.ARCHETYPES:
        return {"error": f"Unknown archetype: {archetype}"}
    
    return SoulGenerator.ARCHETYPES[archetype]

# Przykład użycia dla dokumentacji
USAGE_EXAMPLE = """
# === Astral Beings Library - Quick Usage ===

from astral_beings import QuickStart, quick_guardian, quick_party

# Najprostszy przykład
guardian = await quick_guardian("MyGuardian")
result = await guardian.channel_power("shield", target="sacred_place")

# Grupa bytów
party = await quick_party(4)
for being in party:
    await being.commune(f"Hello, I am {being.name}")

# Wszystkie przykłady
await QuickStart.run_all_examples()
"""
