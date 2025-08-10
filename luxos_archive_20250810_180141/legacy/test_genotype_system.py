
"""
Test systemu genotypów z automatyczną rejestracją genów
"""

import asyncio
from app.genetics.genetic_system import genetic_system

async def test_genotype_system():
    """Test kompletnego systemu genotypów"""
    print("🧪 === TEST SYSTEMU GENOTYPÓW Z GENAMI ===")
    
    # Inicjalizacja systemu
    await genetic_system.initialize()
    
    print(f"\n📊 Status po inicjalizacji:")
    print(f"   Byty: {len(genetic_system.beings)}")
    print(f"   Geny: {len(genetic_system.genes)}")
    print(f"   Relacje: {len(genetic_system.relationships)}")
    
    # Sprawdź genotypy
    genotypes = [being for being in genetic_system.beings.values() 
                if being.genesis.get('type') == 'genotype']
    
    print(f"\n🧬 Znalezione genotypy: {len(genotypes)}")
    for genotype in genotypes:
        print(f"   - {genotype.genesis.get('name')} (ID: {genotype.soul[:8]}...)")
        
        # Znajdź geny tego genotypu
        genotype_genes = []
        for rel in genetic_system.relationships.values():
            if (rel.source_soul == genotype.soul and 
                rel.genesis.get('relationship_type') == 'contains_gene'):
                gene_soul = rel.target_soul
                if gene_soul in genetic_system.genes:
                    gene_data = genetic_system.genes[gene_soul]
                    genotype_genes.append({
                        'name': gene_data.get('metadata', {}).get('name', 'unknown'),
                        'function': rel.genesis.get('function_name', 'unknown')
                    })
        
        print(f"     Geny ({len(genotype_genes)}):")
        for gene in genotype_genes:
            print(f"       • {gene['name']} (funkcja: {gene['function']})")
    
    # Test wywołania genu przez system genetyczny
    if genetic_system.genes:
        print(f"\n🧪 Test wywoływania genów:")
        
        # Spróbuj znaleźć gen advanced_log
        for gene_soul, gene_data in genetic_system.genes.items():
            gene_name = gene_data.get('metadata', {}).get('name')
            if gene_name == 'advanced_log':
                print(f"   Testowanie genu: {gene_name}")
                # Tutaj można dodać test wywołania genu
                break
    
    print(f"\n✅ Test zakończony pomyślnie!")

if __name__ == "__main__":
    asyncio.run(test_genotype_system())
