
"""
Podstawowy przykład użycia LuxDB.
"""

import asyncio
from luxdb import LuxDB, Soul, Being, Relationship

async def main():
    """
    Podstawowy przykład użycia LuxDB.
    """
    
    # 1. Inicjalizacja LuxDB
    print("🚀 Inicjalizacja LuxDB...")
    
    # Konfiguracja bazy danych (użyj swoich danych)
    db = LuxDB(
        host='localhost',  # lub twój host Neon.tech
        port=5432,
        user='your_user',
        password='your_password',
        database='your_database'
    )
    
    async with db:  # Context manager automatically initializes and closes
        
        # 2. Definicja genotypu użytkownika
        print("👤 Tworzenie genotypu użytkownika...")
        
        user_genotype = {
            "genesis": {
                "name": "user_profile",
                "version": "1.0",
                "description": "Profil użytkownika systemu"
            },
            "attributes": {
                "name": {"py_type": "str", "max_length": 100},
                "email": {"py_type": "str", "unique": True},
                "age": {"py_type": "int", "min_value": 0, "max_value": 150},
                "preferences": {"py_type": "dict"},
                "active": {"py_type": "bool", "default": True},
                "bio": {"py_type": "str", "nullable": True}
            }
        }
        
        # Utworzenie Soul
        user_soul = await Soul.create(user_genotype, alias="user_profile")
        print(f"✅ Soul utworzony: {user_soul.soul_hash[:16]}...")
        
        # 3. Tworzenie użytkowników
        print("👥 Tworzenie użytkowników...")
        
        # Użytkownik 1
        user1_data = {
            "name": "Jan Kowalski",
            "email": "jan@example.com",
            "age": 30,
            "preferences": {"theme": "dark", "language": "pl"},
            "bio": "Programista Python"
        }
        
        user1 = await Being.create(user_soul, user1_data)
        print(f"✅ Użytkownik 1: {user1.ulid[:16]}...")
        
        # Użytkownik 2
        user2_data = {
            "name": "Anna Nowak",
            "email": "anna@example.com", 
            "age": 28,
            "preferences": {"theme": "light", "language": "en"},
            "bio": "UX Designer"
        }
        
        user2 = await Being.create(user_soul, user2_data)
        print(f"✅ Użytkownik 2: {user2.ulid[:16]}...")
        
        # 4. Tworzenie relacji
        print("🔗 Tworzenie relacji...")
        
        friendship = await Relationship.create(
            source_ulid=user1.ulid,
            target_ulid=user2.ulid,
            relation_type="friendship",
            strength=0.8,
            metadata={"since": "2025-01-01", "context": "work"}
        )
        print(f"✅ Relacja utworzona: {friendship.id[:16]}...")
        
        # 5. Wczytywanie danych
        print("📖 Wczytywanie danych...")
        
        # Wczytaj wszystkich użytkowników
        all_users = await Being.load_all_by_soul_hash(user_soul.soul_hash)
        print(f"📊 Znaleziono {len(all_users)} użytkowników")
        
        # Wczytaj konkretnego użytkownika
        loaded_user = await Being.load_by_ulid(user1.ulid)
        if loaded_user:
            print(f"🔍 Wczytano użytkownika: {loaded_user.name}")
        
        # 6. Sprawdzenie stanu bazy
        health = await db.health_check()
        print(f"🏥 Stan bazy: {health['status']}")
        print(f"📈 Souls: {health['souls_count']}, Beings: {health['beings_count']}")

if __name__ == "__main__":
    asyncio.run(main())
