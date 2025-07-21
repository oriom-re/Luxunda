
import asyncio
from datetime import datetime
from app.beings.genetic_being import GeneticBeing
from app.genetics.self_contained_gene import SelfContainedDatabaseGene, SelfContainedCommunicationGene


async def test_self_contained_genes():
    print("🧬 Test samowystarczalnych genów")
    
    # Utwórz istotę genetyczną
    being = GeneticBeing(
        soul="test-genetic-being",
        genesis={'name': 'TestBeing', 'type': 'genetic'},
        attributes={'energy_level': 100, 'max_genes': 10},
        memories=[]
    )
    
    print(f"✨ Utworzono istotę: {being.soul}")
    
    # Test 1: Samowystarczalny gen bazy danych
    print("\n💾 Test samowystarczalnego genu bazy danych...")
    
    db_gene = SelfContainedDatabaseGene()
    db_data = db_gene.to_serializable_dict()
    
    print(f"📊 Gen zawiera {len(db_data['dependencies'])} zależności:")
    for dep_name in db_data['dependencies'].keys():
        print(f"  - {dep_name}")
    
    print(f"📋 Gen zawiera {len(db_data['code_fragments'])} fragmentów kodu:")
    for fragment_name in db_data['code_fragments'].keys():
        print(f"  - {fragment_name}")
    
    # Dodaj gen z pełnej definicji
    success = await being.add_gene_from_dict(db_data)
    print(f"Gen bazy danych dodany z definicji: {success}")
    
    if success:
        # Test operacji na bazie
        db_gene_id = list(being.active_genes.keys())[0]
        
        store_result = await being.express_gene(db_gene_id, {
            'action': 'store',
            'key': 'test_data',
            'value': {'message': 'Hello from self-contained gene!', 'number': 42}
        })
        print(f"Zapisano dane: {store_result}")
        
        get_result = await being.express_gene(db_gene_id, {
            'action': 'get',
            'key': 'test_data'
        })
        print(f"Pobrano dane: {get_result}")
        
        stats_result = await being.express_gene(db_gene_id, {
            'action': 'get_stats'
        })
        print(f"Statystyki: {stats_result}")
    
    # Test 2: Samowystarczalny gen komunikacji
    print("\n📡 Test samowystarczalnego genu komunikacji...")
    
    comm_gene = SelfContainedCommunicationGene()
    comm_data = comm_gene.to_serializable_dict()
    
    success = await being.add_gene_from_dict(comm_data)
    print(f"Gen komunikacji dodany z definicji: {success}")
    
    if success:
        # Znajdź gen komunikacji
        comm_gene_id = None
        for gene_id, gene in being.active_genes.items():
            if gene.gene_type == 'self_contained_communication':
                comm_gene_id = gene_id
                break
        
        if comm_gene_id:
            send_result = await being.express_gene(comm_gene_id, {
                'action': 'send_message',
                'target_soul': 'another-being',
                'message': 'Hello from self-contained communication gene!',
                'protocol': 'direct_call'
            })
            print(f"Wysłano wiadomość: {send_result}")
            
            messages_result = await being.express_gene(comm_gene_id, {
                'action': 'get_messages'
            })
            print(f"Wiadomości: {messages_result}")
    
    # Test 3: Serializacja i deserializacja całej istoty
    print("\n💾 Test pełnej serializacji istoty z genami...")
    
    genetic_status = await being.get_genetic_status()
    print(f"Status genetyczny: {genetic_status['active_genes_count']} aktywnych genów")
    
    # Wyeksportuj wszystkie geny do słownika
    genes_export = {}
    for gene_id, gene in being.active_genes.items():
        if isinstance(gene, (SelfContainedDatabaseGene, SelfContainedCommunicationGene)):
            genes_export[gene_id] = gene.to_serializable_dict()
    
    print(f"📤 Wyeksportowano {len(genes_export)} samowystarczalnych genów")
    
    # Symuluj odtworzenie (nowa istota z tymi samymi genami)
    new_being = GeneticBeing(
        soul="restored-being",
        genesis={'name': 'RestoredBeing', 'type': 'genetic'},
        attributes={'energy_level': 200, 'max_genes': 10},
        memories=[]
    )
    
    restored_count = 0
    for gene_data in genes_export.values():
        success = await new_being.add_gene_from_dict(gene_data)
        if success:
            restored_count += 1
    
    print(f"📥 Odtworzono {restored_count}/{len(genes_export)} genów w nowej istoty")
    
    print("\n✅ Test samowystarczalnych genów zakończony!")


if __name__ == "__main__":
    asyncio.run(test_self_contained_genes())
