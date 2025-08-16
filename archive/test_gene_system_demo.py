
import asyncio
from app.beings.base import Being
from app.genetics.genetic_system import genetic_system
from app.genetics.gene_registry import gene

# Przykład użycia nowego systemu genowego
async def demo_gene_system():
    """Demonstracja nowego systemu genowego"""
    
    # Inicjalizuj system genetyczny
    await genetic_system.initialize()
    
    # Stwórz byt
    test_being = await Being.create(
        genesis={
            'type': 'test',
            'name': 'TestBeing',
            'description': 'Byt testowy dla genów'
        },
        attributes={
            'energy_level': 100
        }
    )
    
    print(f"\n🧬 Testowanie genów dla bytu: {test_being.soul}")
    
    # Sprawdź dostępne geny
    available = test_being.available_genes()
    print(f"📋 Dostępne geny: {available}")
    
    # Test genu debug - teraz można wywołać bez self!
    result = await test_being.genes('debug', 'Witaj świecie genów!', context={'test': True})
    print(f"✅ Debug result: {result}")
    
    # Test genu timer
    timer_start = await test_being.genes('timer', 'start')
    print(f"⏱️ Timer start: {timer_start}")
    
    # Symulacja pracy
    await asyncio.sleep(0.1)
    
    timer_stop = await test_being.genes('timer', 'stop')
    print(f"⏱️ Timer stop: {timer_stop}")
    
    # Test genu memory
    await test_being.genes('memory', 'set', 'test_key', {'important': 'data'})
    memory_result = await test_being.genes('memory', 'get', 'test_key')
    print(f"🧠 Memory result: {memory_result}")
    
    # Test genu log
    log_result = await test_being.genes('log', 'System genowy działa poprawnie!', 'SUCCESS')
    print(f"📝 Log result: {log_result}")
    
    # Test statystyk
    stats = await test_being.genes('stats')
    print(f"📊 Stats: {stats}")
    
    # Test nieistniejącego genu
    invalid_result = await test_being.genes('nonexistent_gene')
    print(f"❌ Invalid gene result: {invalid_result}")
    
    print("\n🎉 Demo zakończone pomyślnie!")

if __name__ == "__main__":
    asyncio.run(demo_gene_system())
