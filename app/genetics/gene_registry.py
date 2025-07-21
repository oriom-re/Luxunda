
from typing import Dict, Type, List, Optional
from app.genetics.base_gene import BaseGene


class GeneRegistry:
    """Rejestr wszystkich dostępnych genów"""
    
    _genes: Dict[str, Type[BaseGene]] = {}
    _compatibility_matrix: Dict[str, List[str]] = {}
    
    @classmethod
    def register_gene(cls, gene_class: Type[BaseGene]):
        """Zarejestruj nowy typ genu"""
        # Tymczasowo utwórz instancję żeby pobrać gene_type
        temp_instance = gene_class()
        gene_type = temp_instance.gene_type
        
        cls._genes[gene_type] = gene_class
        cls._compatibility_matrix[gene_type] = temp_instance.compatibility_tags
        
        print(f"Zarejestrowano gen: {gene_type}")
    
    @classmethod
    def create_gene(cls, gene_type: str, **kwargs) -> Optional[BaseGene]:
        """Utwórz instancję genu"""
        if gene_type not in cls._genes:
            return None
            
        gene_class = cls._genes[gene_type]
        return gene_class(**kwargs)
    
    @classmethod
    def get_compatible_genes(cls, gene_type: str) -> List[str]:
        """Pobierz geny kompatybilne z danym genem"""
        if gene_type not in cls._compatibility_matrix:
            return []
            
        return cls._compatibility_matrix[gene_type]
    
    @classmethod
    def get_all_gene_types(cls) -> List[str]:
        """Pobierz wszystkie dostępne typy genów"""
        return list(cls._genes.keys())
    
    @classmethod
    def check_compatibility(cls, gene1_type: str, gene2_type: str) -> bool:
        """Sprawdź kompatybilność dwóch genów"""
        if gene1_type not in cls._compatibility_matrix:
            return False
            
        compatible_with_gene1 = cls._compatibility_matrix[gene1_type]
        return gene2_type in compatible_with_gene1
