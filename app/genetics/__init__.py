
# Genetics module for LuxOS beings
# Genetics module for LuxOS beings
from app.genetics.gene_registry import GeneRegistry
from app.genetics.communication_gene import CommunicationGene  
from app.genetics.database_gene import DatabaseGene

# Rejestruj dostępne geny
GeneRegistry.register_gene(CommunicationGene)
GeneRegistry.register_gene(DatabaseGene)

print("🧬 Genetics system initialized with genes:", GeneRegistry.get_all_gene_types())
