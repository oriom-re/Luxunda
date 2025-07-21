
from typing import Dict, Any, List, Optional
from app.beings.base import BaseBeing
from app.genetics.base_gene import BaseGene, GeneActivationContext
from app.genetics.gene_registry import GeneRegistry
from app.genetics.self_contained_gene import SelfContainedGene
from datetime import datetime
import asyncio


class GeneticBeing(BaseBeing):
    """Byt z zdolnościami genetycznymi"""
    
    def __post_init__(self):
        super().__post_init__()
        self.max_active_genes = self.attributes.get('max_genes', 5)
        self.gene_compatibility_matrix: Dict[str, List[str]] = {}
    
    async def add_gene_from_dict(self, gene_data: Dict[str, Any]) -> bool:
        """Dodaj gen z pełnej definicji słownikowej"""
        if len(self.active_genes) >= self.max_active_genes:
            return False
        
        gene_type = gene_data.get('gene_type')
        
        # Import odpowiedniej klasy genu
        if gene_type == 'self_contained_database':
            from app.genetics.self_contained_gene import SelfContainedDatabaseGene
            gene = SelfContainedDatabaseGene.from_serializable_dict(gene_data)
        elif gene_type == 'self_contained_communication':
            from app.genetics.self_contained_gene import SelfContainedCommunicationGene
            gene = SelfContainedCommunicationGene.from_serializable_dict(gene_data)
        else:
            return False
        
        if self.energy_level < gene._configuration['required_energy']:
            return False
        
        # Aktywuj gen
        context = GeneActivationContext(
            activator_soul=self.soul,
            activation_time=datetime.now(),
            activation_params={'from_dict': True}
        )
        
        success = await gene.activate(self, context)
        
        if success:
            self.active_genes[gene.gene_id] = gene
            
            # Dodaj do biblioteki
            self.gene_library.append({
                'gene_type': gene_type,
                'gene_id': gene.gene_id,
                'added_at': datetime.now().isoformat(),
                'status': 'active',
                'full_definition': gene_data
            })
        
        return success

    async def add_gene(self, gene_type: str, **gene_kwargs) -> bool:
        """Dodaj gen do biblioteki i opcjonalnie aktywuj"""
        if len(self.active_genes) >= self.max_active_genes:
            await self._record_genetic_memory('gene_add_failed', {
                'gene_type': gene_type,
                'reason': 'max_genes_reached',
                'max_genes': self.max_active_genes
            })
            return False
        
        # Sprawdź czy mamy wystarczająco energii
        gene = GeneRegistry.create_gene(gene_type, **gene_kwargs)
        if not gene:
            await self._record_genetic_memory('gene_add_failed', {
                'gene_type': gene_type,
                'reason': 'unknown_gene_type'
            })
            return False
        
        if self.energy_level < gene.required_energy:
            await self._record_genetic_memory('gene_add_failed', {
                'gene_type': gene_type,
                'reason': 'insufficient_energy',
                'required': gene.required_energy,
                'available': self.energy_level
            })
            return False
        
        # Sprawdź kompatybilność
        if not await self._check_gene_compatibility(gene):
            await self._record_genetic_memory('gene_add_failed', {
                'gene_type': gene_type,
                'reason': 'incompatible_with_existing_genes'
            })
            return False
        
        # Dodaj do biblioteki
        self.gene_library.append({
            'gene_type': gene_type,
            'gene_id': gene.gene_id,
            'added_at': datetime.now().isoformat(),
            'status': 'available',
            'kwargs': gene_kwargs
        })
        
        # Automatycznie aktywuj
        activation_success = await self.activate_gene(gene.gene_id)
        
        await self._record_genetic_memory('gene_added', {
            'gene_type': gene_type,
            'gene_id': gene.gene_id,
            'activated': activation_success
        })
        
        return activation_success
    
    async def activate_gene(self, gene_id: str) -> bool:
        """Aktywuj gen z biblioteki"""
        # Znajdź gen w bibliotece
        gene_info = None
        for gene in self.gene_library:
            if gene['gene_id'] == gene_id:
                gene_info = gene
                break
        
        if not gene_info:
            return False
        
        if gene_id in self.active_genes:
            return True  # Już aktywny
        
        # Utwórz instancję genu
        gene_instance = GeneRegistry.create_gene(
            gene_info['gene_type'], 
            gene_id=gene_id,
            **gene_info.get('kwargs', {})
        )
        
        if not gene_instance:
            return False
        
        # Aktywuj gen
        context = GeneActivationContext(
            activator_soul=self.soul,
            activation_time=datetime.now(),
            activation_params={'auto_activation': True}
        )
        
        success = await gene_instance.activate(self, context)
        
        if success:
            self.active_genes[gene_id] = gene_instance
            # Aktualizuj status w bibliotece
            gene_info['status'] = 'active'
            
            await self._record_genetic_memory('gene_activated', {
                'gene_type': gene_instance.gene_type,
                'gene_id': gene_id,
                'energy_cost': gene_instance.required_energy
            })
        
        return success
    
    async def deactivate_gene(self, gene_id: str) -> bool:
        """Dezaktywuj gen"""
        if gene_id not in self.active_genes:
            return False
        
        gene = self.active_genes[gene_id]
        success = await gene.deactivate()
        
        if success:
            del self.active_genes[gene_id]
            
            # Aktualizuj status w bibliotece
            for gene_info in self.gene_library:
                if gene_info['gene_id'] == gene_id:
                    gene_info['status'] = 'available'
                    break
            
            await self._record_genetic_memory('gene_deactivated', {
                'gene_type': gene.gene_type,
                'gene_id': gene_id
            })
        
        return success
    
    async def remove_gene(self, gene_id: str) -> bool:
        """Usuń gen z biblioteki"""
        # Dezaktywuj jeśli aktywny
        if gene_id in self.active_genes:
            await self.deactivate_gene(gene_id)
        
        # Usuń z biblioteki
        self.gene_library = [g for g in self.gene_library if g['gene_id'] != gene_id]
        
        await self._record_genetic_memory('gene_removed', {
            'gene_id': gene_id
        })
        
        return True
    
    async def express_gene(self, gene_id: str, stimulus: Dict[str, Any]) -> Dict[str, Any]:
        """Wyraź funkcję genu"""
        if gene_id not in self.active_genes:
            return {'error': 'Gene not active'}
        
        gene = self.active_genes[gene_id]
        result = await gene.express(stimulus)
        
        await self._record_genetic_memory('gene_expressed', {
            'gene_id': gene_id,
            'gene_type': gene.gene_type,
            'stimulus': stimulus,
            'result': result
        })
        
        return result
    
    async def evolve_genes(self, experience: Dict[str, Any]):
        """Ewolucja wszystkich aktywnych genów"""
        for gene_id, gene in self.active_genes.items():
            await gene.evolve_autonomy(experience)
            
            # Sprawdź czy gen może się usamodzielnić
            if await gene.can_become_independent():
                await self._handle_gene_independence(gene)
    
    async def _handle_gene_independence(self, gene: BaseGene):
        """Obsłuż gen dążący do niezależności"""
        # Zaproponuj utworzenie niezależnej istoty
        independent_being = await gene.spawn_independent_being()
        
        if independent_being:
            await self._record_genetic_memory('gene_became_independent', {
                'original_gene_id': gene.gene_id,
                'gene_type': gene.gene_type,
                'new_being_soul': independent_being.soul,
                'autonomy_level': gene.autonomy_level
            })
            
            # Opcjonalnie usuń gen lub zostaw jako połączenie
            # await self.deactivate_gene(gene.gene_id)
    
    async def _check_gene_compatibility(self, new_gene: BaseGene) -> bool:
        """Sprawdź kompatybilność nowego genu z aktywnymi"""
        for active_gene in self.active_genes.values():
            if not GeneRegistry.check_compatibility(new_gene.gene_type, active_gene.gene_type):
                return False
        return True
    
    async def get_genetic_status(self) -> Dict[str, Any]:
        """Pobierz status genetyczny"""
        return {
            'total_genes_in_library': len(self.gene_library),
            'active_genes_count': len(self.active_genes),
            'max_active_genes': self.max_active_genes,
            'active_genes': {
                gene_id: {
                    'type': gene.gene_type,
                    'autonomy_level': gene.autonomy_level,
                    'is_active': gene.is_active,
                    'can_become_independent': await gene.can_become_independent()
                }
                for gene_id, gene in self.active_genes.items()
            },
            'gene_library': self.gene_library,
            'total_genetic_memories': len(self.genetic_memories)
        }
    
    async def _record_genetic_memory(self, memory_type: str, data: Dict[str, Any]):
        """Zapisz pamięć genetyczną"""
        memory = {
            'type': memory_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'being_soul': self.soul
        }
        
        self.genetic_memories.append(memory)
        self.memories.append(memory)  # Dodaj też do głównych pamięci
