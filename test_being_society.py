
import asyncio
import os
from app.beings.base_v2 import Being

async def test_being_society():
    """Test społeczności bytów z relacjami i uczeniem się"""
    
    # Usuń testową bazę jeśli istnieje
    if os.path.exists("test_society.db"):
        os.remove("test_society.db")
    
    # Stwórz różne typy bytów
    beings = []
    
    # Byt główny - Kernel
    kernel = Being(
        soul="kernel_001",
        genesis={
            'type': 'kernel',
            'name': 'LuxOS Kernel',
            'purpose': 'System management and coordination'
        },
        attributes={'energy_level': 200, 'authority_level': 'high'},
        memories=[],
        self_awareness={'role': 'system_coordinator', 'confidence': 0.9},
        db_path="test_society.db"
    )
    
    # Byt funkcyjny
    function_being = Being(
        soul="func_001", 
        genesis={
            'type': 'function',
            'name': 'Calculator',
            'source': '''
def calculate(a, b, operation):
    """Prosta funkcja kalkulatora"""
    if operation == 'add':
        return a + b
    elif operation == 'multiply':
        return a * b
    return 0
'''
        },
        attributes={'energy_level': 80, 'skill_level': 'intermediate'},
        memories=[],
        self_awareness={'purpose': 'mathematical_operations'},
        db_path="test_society.db"
    )
    
    # Byt danych
    data_being = Being(
        soul="data_001",
        genesis={
            'type': 'data',
            'name': 'UserStorage',
            'source': '''
class UserStorage:
    def __init__(self):
        self.users = {}
    
    def store_user(self, user_id, data):
        self.users[user_id] = data
'''
        },
        attributes={'energy_level': 120, 'storage_capacity': 'medium'},
        memories=[],
        self_awareness={'purpose': 'data_management'},
        db_path="test_society.db"
    )
    
    beings = [kernel, function_being, data_being]
    
    # Uruchom wszystkie byty
    for being in beings:
        await being.start()
        print(f"Uruchomiono byt: {being.soul}")
    
    # Kernel tworzy wymuszone relacje
    print("\n=== Kernel tworzy wymuszone relacje ===")
    
    # Relacja: function_being ma inicjować gen komunikacji z data_being
    await kernel.create_relationship(
        target_soul="func_001",
        rel_type="gene_initialization", 
        genesis={
            'mandate': 'Initialize communication gene for data collaboration',
            'created_by': 'kernel'
        },
        is_forced=True,
        is_permanent=True
    )
    
    # Relacja: data_being ma współpracować z function_being
    await kernel.create_relationship(
        target_soul="data_001",
        rel_type="collaboration",
        genesis={
            'purpose': 'Provide data storage services',
            'priority': 'high'
        },
        is_forced=True,
        is_permanent=False
    )
    
    print("Wymuszone relacje utworzone przez Kernel")
    
    # Każdy byt rozpoczyna proces uczenia się
    print("\n=== Proces uczenia się i odkrywania ===")
    
    for being in beings:
        print(f"\n[{being.soul}] Rozpoczyna uczenie się...")
        await being.learn_and_evolve()
        
        # Pokaż odkrycia
        discoveries = await being.discover_other_souls()
        print(f"[{being.soul}] Odkrył {len(discoveries)} innych bytów")
        
        for discovery in discoveries:
            analysis = discovery['analysis']
            print(f"  - {discovery['soul']}: {analysis['being_type']} "
                  f"(kompatybilność: {analysis['compatibility_score']:.2f})")
    
    # Pokaż wszystkie relacje
    print("\n=== Analiza powstałych relacji ===")
    
    for being in beings:
        print(f"\n[{being.soul}] Relacje:")
        for rel_id, rel in being.relationships.items():
            print(f"  - {rel['type']} z {rel['target_soul']} "
                  f"(wymuszona: {rel['is_forced']}, trwała: {rel['is_permanent']})")
    
    # Pokaż samoświadomość
    print("\n=== Samoświadomość bytów ===")
    for being in beings:
        print(f"\n[{being.soul}] Samoświadomość:")
        for key, value in being.self_awareness.items():
            print(f"  - {key}: {value}")
    
    # Zatrzymaj wszystkie byty
    for being in beings:
        await being.stop()
    
    print("\n=== Test zakończony ===")

if __name__ == "__main__":
    asyncio.run(test_being_society())
