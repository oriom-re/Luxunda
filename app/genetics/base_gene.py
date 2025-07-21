
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type
from dataclasses import dataclass
from datetime import datetime
import uuid
import json
from app.beings.base import BaseBeing


@dataclass
class GeneActivationContext:
    """Kontekst aktywacji genu"""
    activator_soul: str
    activation_time: datetime
    activation_params: Dict[str, Any]
    energy_cost: int = 10


class BaseGene(ABC):
    """Bazowa klasa dla wszystkich genów"""
    
    def __init__(self, gene_id: Optional[str] = None):
        self.gene_id = gene_id or str(uuid.uuid4())
        self.is_active = False
        self.host_being: Optional[BaseBeing] = None
        self.activation_context: Optional[GeneActivationContext] = None
        self.gene_memories: List[Dict[str, Any]] = []
        self.autonomy_level = 0  # 0-100, powyżej 80 może się usamodzielnić
        
    @property
    @abstractmethod
    def gene_type(self) -> str:
        """Typ genu"""
        pass
    
    @property
    @abstractmethod
    def required_energy(self) -> int:
        """Wymagana energia do aktywacji"""
        pass
    
    @property
    @abstractmethod
    def compatibility_tags(self) -> List[str]:
        """Tagi kompatybilności z innymi genami"""
        pass
    
    @abstractmethod
    async def activate(self, host: BaseBeing, context: GeneActivationContext) -> bool:
        """Aktywuj gen w istoty-gospodarzu"""
        pass
    
    @abstractmethod
    async def deactivate(self) -> bool:
        """Dezaktywuj gen"""
        pass
    
    @abstractmethod
    async def express(self, stimulus: Dict[str, Any]) -> Dict[str, Any]:
        """Wyraź funkcję genu - główna logika"""
        pass
    
    async def mutate(self, mutation_params: Dict[str, Any]) -> 'BaseGene':
        """Mutuj gen - tworzy nową wersję"""
        # Każdy gen może implementować własną mutację
        return self
    
    async def evolve_autonomy(self, experience: Dict[str, Any]):
        """Zwiększ autonomię na podstawie doświadczeń"""
        if self.autonomy_level < 100:
            self.autonomy_level += experience.get('autonomy_boost', 1)
            
        # Zapisz doświadczenie
        self.gene_memories.append({
            'type': 'evolution',
            'experience': experience,
            'autonomy_before': self.autonomy_level - experience.get('autonomy_boost', 1),
            'autonomy_after': self.autonomy_level,
            'timestamp': datetime.now().isoformat()
        })
    
    async def can_become_independent(self) -> bool:
        """Sprawdź czy gen może stać się niezależną istotą"""
        return self.autonomy_level >= 80 and self.is_active
    
    async def spawn_independent_being(self) -> Optional[BaseBeing]:
        """Utwórz niezależną istotę z tego genu"""
        if not await self.can_become_independent():
            return None
            
        # Import here to avoid circular import
        from app.beings.being_factory import BeingFactory
        
        new_being = await BeingFactory.create_being(
            being_type='function',
            genesis={
                'type': 'autonomous_gene',
                'name': f'Independent_{self.gene_type}_{self.gene_id[:8]}',
                'parent_gene_id': self.gene_id,
                'parent_being_soul': self.host_being.soul if self.host_being else None,
                'spawned_at': datetime.now().isoformat()
            },
            attributes={
                'gene_type': self.gene_type,
                'autonomy_level': self.autonomy_level,
                'original_host': self.host_being.soul if self.host_being else None,
                'energy_level': self.required_energy * 2
            },
            memories=self.gene_memories.copy()
        )
        
        return new_being
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializuj gen do słownika"""
        return {
            'gene_id': self.gene_id,
            'gene_type': self.gene_type,
            'is_active': self.is_active,
            'autonomy_level': self.autonomy_level,
            'required_energy': self.required_energy,
            'compatibility_tags': self.compatibility_tags,
            'gene_memories': self.gene_memories,
            'host_being_soul': self.host_being.soul if self.host_being else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseGene':
        """Deserializuj gen ze słownika"""
        # To będzie implementowane w konkretnych genach
        raise NotImplementedError("Subclasses must implement from_dict")
