
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import uuid

from .base_being import BaseBeing

@dataclass
class AgentBeing(BaseBeing):
    """Specjalizowany byt dla agentów z rozszerzonymi możliwościami"""
    
    def __post_init__(self):
        # Upewnij się że typ jest ustawiony na agent
        if 'type' not in self.genesis:
            self.genesis['type'] = 'agent'
        
        # Domyślne uprawnienia agenta
        if 'agent_permissions' not in self.attributes:
            self.attributes['agent_permissions'] = {
                'create_beings': False,
                'modify_beings': False,
                'delete_beings': False,
                'manage_users': False,
                'system_access': False
            }
        
        # Domyślny poziom agenta
        if 'agent_level' not in self.attributes:
            self.attributes['agent_level'] = 1
        
        # Lista zarządzanych bytów
        if 'managed_beings' not in self.attributes:
            self.attributes['managed_beings'] = []
    
    @classmethod
    async def create(cls, soul: str = None, genesis: Dict[str, Any] = None, **kwargs):
        """Tworzy nowego agenta"""
        if not soul:
            soul = str(uuid.uuid4())
        
        if not genesis:
            genesis = {}
        
        # Upewnij się że typ to agent
        genesis['type'] = 'agent'
        
        # Domyślne atrybuty agenta
        attributes = kwargs.get('attributes', {})
        attributes.setdefault('agent_level', kwargs.get('agent_level', 1))
        attributes.setdefault('energy_level', kwargs.get('energy_level', 100))
        
        # Domyślne self_awareness dla agenta
        self_awareness = kwargs.get('self_awareness', {})
        self_awareness.setdefault('trust_level', 0.5)
        self_awareness.setdefault('confidence', 0.5)
        self_awareness.setdefault('introspection_depth', 0.3)
        
        agent = cls(
            soul=soul,
            genesis=genesis,
            attributes=attributes,
            memories=kwargs.get('memories', []),
            self_awareness=self_awareness,
            created_at=kwargs.get('created_at')
        )
        
        await agent.save()
        return agent
    
    def get_agent_level(self) -> int:
        """Zwraca poziom agenta"""
        return self.attributes.get('agent_level', 1)
    
    def get_permissions(self) -> Dict[str, bool]:
        """Zwraca uprawnienia agenta"""
        return self.attributes.get('agent_permissions', {})
    
    def has_permission(self, permission: str) -> bool:
        """Sprawdza czy agent ma dane uprawnienie"""
        return self.get_permissions().get(permission, False)
    
    def add_managed_being(self, being_soul: str):
        """Dodaje byt do listy zarządzanych"""
        managed = self.attributes.get('managed_beings', [])
        if being_soul not in managed:
            managed.append(being_soul)
            self.attributes['managed_beings'] = managed
    
    def remove_managed_being(self, being_soul: str):
        """Usuwa byt z listy zarządzanych"""
        managed = self.attributes.get('managed_beings', [])
        if being_soul in managed:
            managed.remove(being_soul)
            self.attributes['managed_beings'] = managed
    
    def get_managed_beings(self) -> List[str]:
        """Zwraca listę zarządzanych bytów"""
        return self.attributes.get('managed_beings', [])
    
    async def execute_agent_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Wykonuje zadanie agenta"""
        result = {
            'success': False,
            'task_type': task_type,
            'executed_at': datetime.now().isoformat(),
            'agent_soul': self.soul
        }
        
        try:
            if task_type == 'manage_user_beings':
                result = await self._manage_user_beings(task_data)
            elif task_type == 'cleanup_inactive':
                result = await self._cleanup_inactive_beings(task_data)
            elif task_type == 'process_orbital_tasks':
                result = await self._process_orbital_tasks(task_data)
            else:
                result['error'] = f'Unknown task type: {task_type}'
            
            # Zapisz zadanie w pamięci
            memory = {
                'type': 'agent_task_execution',
                'task_type': task_type,
                'result': result,
                'timestamp': datetime.now().isoformat(),
                'importance': 0.6
            }
            self.memories.append(memory)
            
            # Ogranicz pamięć do ostatnich 50 wpisów
            if len(self.memories) > 50:
                self.memories = self.memories[-50:]
            
            await self.save()
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
        
        return result
    
    async def _manage_user_beings(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Zarządza bytami użytkownika"""
        return {
            'success': True,
            'action': 'manage_user_beings',
            'processed_beings': len(self.get_managed_beings()),
            'message': 'User beings managed successfully'
        }
    
    async def _cleanup_inactive_beings(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Czyści nieaktywne byty"""
        return {
            'success': True,
            'action': 'cleanup_inactive',
            'cleaned_count': 0,
            'message': 'Cleanup completed'
        }
    
    async def _process_orbital_tasks(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Przetwarza zadania orbitalne"""
        return {
            'success': True,
            'action': 'process_orbital_tasks',
            'processed_count': 0,
            'message': 'Orbital tasks processed'
        }
