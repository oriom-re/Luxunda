
import asyncio
from app.beings.genetic_being import GeneticBeing
import app.genetics  # To trigger gene registration


async def test_genetic_system():
    """Test podstawowych funkcji systemu genowego"""
    print("🧬 Testowanie systemu genowego...")
    
    # Utwórz genetyczną istotę
    being = GeneticBeing(
        soul="test-genetic-being",
        genesis={'type': 'genetic', 'name': 'TestGeneticBeing'},
        attributes={'energy_level': 100, 'max_genes': 3},
        memories=[],
        self_awareness={}
    )
    
    print(f"✅ Utworzono genetyczną istotę: {being.soul}")
    
    # Test dodawania genu komunikacyjnego
    print("\n📡 Testowanie genu komunikacyjnego...")
    comm_success = await being.add_gene('communication')
    print(f"Gen komunikacyjny dodany: {comm_success}")
    
    if comm_success:
        # Test wyrażenia genu
        message_result = await being.express_gene(
            list(being.active_genes.keys())[0],  # Pierwszy aktywny gen
            {
                'action': 'send_message',
                'target_soul': 'some-other-being',
                'message': 'Witaj z systemu genowego!',
                'protocol': 'direct_call'
            }
        )
        print(f"Wysłano wiadomość: {message_result}")
    
    # Test dodawania genu bazy danych
    print("\n💾 Testowanie genu bazy danych...")
    db_success = await being.add_gene('database_sqlite', is_memory_db=True)
    print(f"Gen bazy danych dodany: {db_success}")
    
    if db_success:
        # Znajdź gen bazy danych
        db_gene_id = None
        for gene_id, gene in being.active_genes.items():
            if gene.gene_type == 'database_sqlite':
                db_gene_id = gene_id
                break
        
        if db_gene_id:
            # Test operacji na bazie
            insert_result = await being.express_gene(
                db_gene_id,
                {
                    'action': 'insert',
                    'key': 'test_key',
                    'value': {'test': 'data', 'number': 42}
                }
            )
            print(f"Wstawiono dane: {insert_result}")
            
            query_result = await being.express_gene(
                db_gene_id,
                {
                    'action': 'query',
                    'query': 'SELECT * FROM gene_data'
                }
            )
            print(f"Zapytanie do bazy: {query_result}")
            
            stats_result = await being.express_gene(
                db_gene_id,
                {'action': 'get_stats'}
            )
            print(f"Statystyki bazy: {stats_result}")
    
    # Test statusu genetycznego
    print("\n🧬 Status genetyczny istoty:")
    genetic_status = await being.get_genetic_status()
    print(f"Aktywne geny: {genetic_status['active_genes_count']}/{genetic_status['max_active_genes']}")
    print(f"Typy aktywnych genów: {[info['type'] for info in genetic_status['active_genes'].values()]}")
    
    # Test ewolucji genów
    print("\n🔄 Testowanie ewolucji genów...")
    await being.evolve_genes({
        'autonomy_boost': 5,
        'reason': 'successful_operations',
        'context': 'test_evolution'
    })
    
    # Sprawdź poziomy autonomii
    for gene_id, gene in being.active_genes.items():
        print(f"Gen {gene.gene_type} (autonomia: {gene.autonomy_level})")
        if await gene.can_become_independent():
            print(f"  ⚡ Gen {gene.gene_type} może się usamodzielnić!")
    
    print("\n✅ Test systemu genowego zakończony pomyślnie!")
    
    # Cleanup
    for gene_id in list(being.active_genes.keys()):
        await being.deactivate_gene(gene_id)


if __name__ == "__main__":
    asyncio.run(test_genetic_system())
