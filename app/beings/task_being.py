import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from app.beings.base import BaseBeing

@dataclass
class TaskBeing(BaseBeing):
    """Byt zadania z asynchronicznym wykonywaniem"""
    
    def __post_init__(self):
        if self.genesis.get('type') != 'task':
            self.genesis['type'] = 'task'
        if 'task_status' not in self.attributes:
            self.attributes['task_status'] = 'pending'
        if 'async_result' not in self.attributes:
            self.attributes['async_result'] = None
    
    async def execute_async(self, delay: float = 1.0) -> str:
        """Wykonuje zadanie asynchronicznie"""
        task_id = str(uuid.uuid4())
        
        async def async_task():
            self.attributes['task_status'] = 'running'
            self.attributes['started_at'] = datetime.now().isoformat()
            await self.save()
            
            # Symulacja długotrwałego zadania
            await asyncio.sleep(delay)
            
            result = f"Task completed at {datetime.now().isoformat()}"
            self.attributes['task_status'] = 'completed'
            self.attributes['async_result'] = result
            self.attributes['completed_at'] = datetime.now().isoformat()
            
            # Zapisz w pamięci
            self.memories.append({
                'type': 'async_completion',
                'task_id': task_id,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })
            
            await self.save()
            return result
        
        # Uruchom zadanie w tle
        asyncio.create_task(async_task())
        return task_id
    
    def get_status(self) -> Dict[str, Any]:
        """Zwraca status zadania"""
        return {
            'status': self.attributes.get('task_status', 'pending'),
            'started_at': self.attributes.get('started_at'),
            'completed_at': self.attributes.get('completed_at'),
            'result': self.attributes.get('async_result')
        }

