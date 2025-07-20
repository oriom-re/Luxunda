import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import List
from app.beings.base import BaseBeing

@dataclass
class ClassBeing(BaseBeing):
    """Byt klasy z możliwością instancjacji"""
    
    def __post_init__(self):
        if self.genesis.get('type') != 'class':
            self.genesis['type'] = 'class'
        if 'instances' not in self.attributes:
            self.attributes['instances'] = []
    
    async def instantiate(self, *args, **kwargs) -> str:
        """Tworzy instancję klasy"""
        instance_soul = str(uuid.uuid4())
        
        # Utwórz byt instancji
        instance = await BaseBeing.create(
            genesis={
                'type': 'instance',
                'class_soul': self.soul,
                'name': f"{self.genesis.get('name', 'Unknown')}_Instance",
                'created_by': 'class_instantiation'
            },
            attributes={
                'class_reference': self.soul,
                'instance_data': kwargs,
                'creation_args': args
            },
            memories=[{
                'type': 'instantiation',
                'data': f'Created from class {self.soul}',
                'timestamp': datetime.now().isoformat()
            }]
        )
        
        # Zapisz referencję do instancji
        self.attributes['instances'].append(instance_soul)
        await self.save()
        
        return instance_soul
    
    def get_instances(self) -> List[str]:
        """Zwraca listę instancji"""
        return self.attributes.get('instances', [])