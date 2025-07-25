# app_v2/genetics/gene_registry.py
"""
Rejestr genów - zarządza wszystkimi genami w systemie
"""

from typing import Dict, List, Set, Optional
from .gene import Gene

class GeneRegistry:
    """Globalny rejestr wszystkich genów w systemie"""
    
    _genes: Dict[str, Gene] = {}
    _provides_map: Dict[str, List[str]] = {}  # capability -> lista genów
    _dependency_graph: Dict[str, Set[str]] = {}  # gen -> zależności
    
    @classmethod
    def register_gene(cls, gene: Gene):
        """Rejestruje gen w systemie"""
        print(f"🧬 Rejestrowanie genu: {gene.name}")
        
        cls._genes[gene.name] = gene
        
        # Buduj mapę capabilities
        for capability in gene.provides:
            if capability not in cls._provides_map:
                cls._provides_map[capability] = []
            cls._provides_map[capability].append(gene.name)
        
        # Buduj graf zależności
        cls._dependency_graph[gene.name] = set(gene.requires)
        
        print(f"✅ Gen {gene.name} zarejestrowany (provides: {gene.provides}, requires: {gene.requires})")
    
    @classmethod
    async def register_gene_in_database(cls, gene: Gene):
        """Zapisuje gen do bazy danych"""
        try:
            from app_v2.database.soul_repository import SoulRepository
            
            soul_data = gene.to_soul_format()
            success = await SoulRepository.save(soul_data)
            
            if success:
                print(f"💾 Gen {gene.name} zapisany do bazy danych")
                
                # Utwórz relacje zależności
                await cls._create_dependency_relationships(gene)
                
                return True
            else:
                print(f"❌ Nie udało się zapisać genu {gene.name} do bazy")
                return False
                
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania genu {gene.name}: {e}")
            return False
    
    @classmethod
    async def _create_dependency_relationships(cls, gene: Gene):
        """Tworzy relacje zależności w bazie danych"""
        from app_v2.beings.base import Relationship
        
        for required_gene_name in gene.requires:
            required_gene = cls.get_gene(required_gene_name)
            if required_gene:
                await Relationship.create(
                    source_uid=gene.uid,
                    target_uid=required_gene.uid,
                    attributes={
                        "type": "depends_on",
                        "dependency_type": "gene",
                        "required_capability": required_gene_name
                    }
                )
                print(f"🔗 Utworzono relację zależności: {gene.name} -> {required_gene_name}")
    
    @classmethod
    def get_gene(cls, name: str) -> Optional[Gene]:
        """Pobiera gen po nazwie"""
        return cls._genes.get(name)
    
    @classmethod
    def get_genes_providing(cls, capability: str) -> List[Gene]:
        """Pobiera wszystkie geny dostarczające określoną capability"""
        gene_names = cls._provides_map.get(capability, [])
        return [cls._genes[name] for name in gene_names if name in cls._genes]
    
    @classmethod
    def get_dependencies(cls, gene_name: str) -> Set[str]:
        """Pobiera zależności genu"""
        return cls._dependency_graph.get(gene_name, set())
    
    @classmethod
    def resolve_dependencies(cls, gene_name: str) -> List[str]:
        """Rozwiązuje wszystkie zależności genu w poprawnej kolejności"""
        resolved = []
        visiting = set()
        visited = set()
        
        def dfs(current_gene):
            if current_gene in visiting:
                raise ValueError(f"Cykliczna zależność wykryta: {current_gene}")
            if current_gene in visited:
                return
            
            visiting.add(current_gene)
            
            # Odwiedź wszystkie zależności
            for dependency in cls.get_dependencies(current_gene):
                dfs(dependency)
            
            visiting.remove(current_gene)
            visited.add(current_gene)
            resolved.append(current_gene)
        
        dfs(gene_name)
        return resolved
    
    @classmethod
    def get_all_genes(cls) -> Dict[str, Gene]:
        """Pobiera wszystkie zarejestrowane geny"""
        return cls._genes.copy()
    
    @classmethod
    async def register_all_genes_in_database(cls):
        """Zapisuje wszystkie zarejestrowane geny do bazy danych"""
        success_count = 0
        
        for gene in cls._genes.values():
            if await cls.register_gene_in_database(gene):
                success_count += 1
        
        print(f"💾 Zapisano {success_count}/{len(cls._genes)} genów do bazy danych")
        return success_count
    
    @classmethod
    def validate_dependencies(cls) -> Dict[str, List[str]]:
        """Waliduje czy wszystkie zależności mogą być rozwiązane"""
        errors = {}
        
        for gene_name, gene in cls._genes.items():
            missing_deps = []
            
            for required in gene.requires:
                # Sprawdź czy istnieje gen dostarczający tę capability
                providing_genes = cls.get_genes_providing(required)
                if not providing_genes:
                    # Sprawdź czy istnieje gen o tej nazwie
                    if required not in cls._genes:
                        missing_deps.append(required)
            
            if missing_deps:
                errors[gene_name] = missing_deps
        
        return errors
