
import asyncio
import json
from dataclasses import dataclass
from database.models.base import Being
from core.genetics_generator import GeneticsGenerator

@dataclass
class MessageBeing(Being):
    """Przykładowa klasa dziedzicząca po Being"""
    content: str = None
    timestamp: str = None
    embedding: str = None

@dataclass  
class UserBeing(Being):
    """Kolejna przykładowa klasa"""
    name: str = None
    email: str = None
    preferences: dict = None

async def demo_simple_soul_creation():
    """Demo prostego tworzenia Soul z klas"""
    print("🧬 DEMO: Proste tworzenie Soul z klas")
    print("=" * 50)
    
    # 1. Generuj genotyp z MessageBeing
    print("\n📋 Generowanie genotypu MessageBeing...")
    message_genotype = GeneticsGenerator.generate_genotype_from_class(MessageBeing)
    print(json.dumps(message_genotype, indent=2, ensure_ascii=False))
    
    # 2. Generuj genotyp z UserBeing  
    print("\n📋 Generowanie genotypu UserBeing...")
    user_genotype = GeneticsGenerator.generate_genotype_from_class(UserBeing)
    print(json.dumps(user_genotype, indent=2, ensure_ascii=False))
    
    # 3. W prawdziwej aplikacji z bazą danych:
    print("\n👻 Tworzenie Soul (symulacja)...")
    try:
        # message_soul = await GeneticsGenerator.create_soul_from_class(MessageBeing, "message_soul")
        # user_soul = await GeneticsGenerator.create_soul_from_class(UserBeing, "user_soul")
        print("✅ Soul zostałby utworzony lub pobrany z bazy")
        print("🔄 System automatycznie sprawdziłby czy soul_hash już istnieje")
    except Exception as e:
        print(f"⚠️ Błąd (bez bazy): {e}")

if __name__ == "__main__":
    asyncio.run(demo_simple_soul_creation())
