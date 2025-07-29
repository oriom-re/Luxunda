
import asyncio
import os
from app.beings.prototyp.base_v2 import Being, PostgreSQLGene

async def test_simplified_being():
    """Test uproszczonego systemu Being"""
    
    # Usuń starą bazę dla czystego testu
    if os.path.exists("test_luxos.db"):
        os.remove("test_luxos.db")
    
    print("=== Test Uproszczonego Systemu Being ===")
    
    # Stwórz główny byt
    master_being = Being(
        soul="master_001",
        genesis={
            'type': 'master',
            'name': 'LuxOS Master Being',
            'purpose': 'Zarządzanie ekosystemem genów'
        },
        attributes={
            'energy_level': 150,
            'version': '2.0',
            'capabilities': ['gene_management', 'data_storage']
        },
        memories=[],
        self_awareness={
            'knows_self': True,
            'can_evolve': True,
            'autonomy_level': 'high'
        },
        db_path="test_luxos.db"
    )
    
    print(f"Tworzę Master Being: {master_being.soul}")
    
    # Uruchom byt
    await master_being.start()
    print(f"Master Being uruchomiony. Energia: {master_being.energy_level}")
    
    # Test zapisu i odczytu
    await master_being.save()
    print("Stan zapisany do SQLite")
    
    # Dodaj wspomnienie
    await master_being.add_memory({
        'type': 'initialization',
        'event': 'Master Being created and started',
        'energy_level': master_being.energy_level
    })
    
    # Test aktywacji genu PostgreSQL
    print("\n=== Test Genu PostgreSQL ===")
    
    # Symuluj kontekst aktywacji
    postgresql_context = {
        'postgresql_url': 'postgresql://user:pass@localhost/luxos_test',
        'purpose': 'Rozszerzone zarządzanie danymi'
    }
    
    print("Próba aktywacji genu PostgreSQL...")
    success = await master_being.activate_gene('postgresql', postgresql_context)
    
    if success:
        print("✅ Gen PostgreSQL aktywowany!")
        print(f"Energia po aktywacji: {master_being.energy_level}")
        
        # Test funkcji genu
        print("\nTestowanie funkcji genu...")
        
        # Pobierz statystyki
        stats = await master_being.express_gene('postgresql', {
            'action': 'get_stats'
        })
        print(f"PostgreSQL Stats: {stats}")
        
        # Stwórz backup
        backup_result = await master_being.express_gene('postgresql', {
            'action': 'backup_to_sqlite'
        })
        print(f"Backup Result: {backup_result}")
        
        # Test nieznane akcji
        unknown_result = await master_being.express_gene('postgresql', {
            'action': 'unknown_action'
        })
        print(f"Unknown Action Result: {unknown_result}")
        
    else:
        print("❌ Gen PostgreSQL nie mógł być aktywowany (prawdopodobnie brak asyncpg)")
    
    # Test listy aktywnych genów
    print(f"\nAktywne geny: {list(master_being.active_genes.keys())}")
    
    # Sprawdź stan po zapisie
    await master_being.save()
    print("Stan z genami zapisany")
    
    # Test dezaktywacji
    if 'postgresql' in master_being.active_genes:
        print("\nDezaktywacja genu PostgreSQL...")
        deactivate_success = await master_being.deactivate_gene('postgresql')
        print(f"Dezaktywacja {'udana' if deactivate_success else 'nieudana'}")
        print(f"Energia po dezaktywacji: {master_being.energy_level}")
    
    # Wyświetl final state
    print(f"\n=== Stan końcowy ===")
    print(f"Soul: {master_being.soul}")
    print(f"Energia: {master_being.energy_level}")
    print(f"Liczba wspomnień: {len(master_being.memories)}")
    print(f"Aktywne geny: {list(master_being.active_genes.keys())}")
    
    # Ostatnie wspomnienie
    if master_being.memories:
        print(f"Ostatnie wspomnienie: {master_being.memories[-1]}")
    
    await master_being.stop()
    print("Master Being zatrzymany")

if __name__ == "__main__":
    asyncio.run(test_simplified_being())
