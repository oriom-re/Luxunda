import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from app.beings.base import Being

@dataclass
class ScenarioBeing(Being):
    """Byt scenariusza z sekwencją kroków"""
    
    def __post_init__(self):
        if self.genesis.get('type') != 'scenario':
            self.genesis['type'] = 'scenario'
        if 'steps' not in self.attributes:
            self.attributes['steps'] = []
        if 'current_step' not in self.attributes:
            self.attributes['current_step'] = 0
    
    def add_step(self, step_name: str, step_data: Dict[str, Any]):
        """Dodaje krok do scenariusza"""
        step = {
            'name': step_name,
            'data': step_data,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        self.attributes['steps'].append(step)
    
    async def execute_next_step(self) -> Dict[str, Any]:
        """Wykonuje następny krok scenariusza"""
        steps = self.attributes.get('steps', [])
        current_step = self.attributes.get('current_step', 0)
        
        if current_step >= len(steps):
            return {'success': False, 'error': 'Brak więcej kroków'}
        
        step = steps[current_step]
        step['status'] = 'executing'
        step['started_at'] = datetime.now().isoformat()
        
        # Symulacja wykonania kroku
        await asyncio.sleep(0.1)
        
        step['status'] = 'completed'
        step['completed_at'] = datetime.now().isoformat()
        
        self.attributes['current_step'] = current_step + 1
        
        # Zapisz w pamięci
        self.memories.append({
            'type': 'step_execution',
            'step_name': step['name'],
            'step_index': current_step,
            'timestamp': datetime.now().isoformat()
        })
        
        await self.save()
        return {'success': True, 'step': step}

