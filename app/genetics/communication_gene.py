
from typing import Dict, Any, List
from app.genetics.base_gene import BaseGene, GeneActivationContext
from app.beings.base import BaseBeing
import asyncio
import json


class CommunicationGene(BaseGene):
    """Gen komunikacji między bytami"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.active_connections: Dict[str, Dict[str, Any]] = {}
        self.message_queue: List[Dict[str, Any]] = []
        self.protocols = ['socket_io', 'direct_call', 'queue_based']
    
    @property
    def gene_type(self) -> str:
        return 'communication'
    
    @property
    def required_energy(self) -> int:
        return 15
    
    @property
    def compatibility_tags(self) -> List[str]:
        return ['database', 'ai_model', 'embedding', 'network']
    
    async def activate(self, host: BaseBeing, context: GeneActivationContext) -> bool:
        """Aktywuj gen komunikacji"""
        if host.energy_level < self.required_energy:
            return False
            
        self.host_being = host
        self.activation_context = context
        self.is_active = True
        
        # Odejmij energię
        host.energy_level -= self.required_energy
        
        # Zapisz aktywację w pamięciach
        await self._record_memory('activation', {
            'activator': context.activator_soul,
            'energy_cost': self.required_energy,
            'protocols_available': self.protocols
        })
        
        print(f"Gen komunikacji aktywowany w istoty {host.soul}")
        return True
    
    async def deactivate(self) -> bool:
        """Dezaktywuj gen"""
        # Zamknij wszystkie połączenia
        for connection_id in list(self.active_connections.keys()):
            await self.close_connection(connection_id)
        
        self.is_active = False
        await self._record_memory('deactivation', {'reason': 'manual'})
        return True
    
    async def express(self, stimulus: Dict[str, Any]) -> Dict[str, Any]:
        """Wyraź funkcję komunikacji"""
        if not self.is_active:
            return {'error': 'Gene not active'}
        
        action = stimulus.get('action', 'send_message')
        
        if action == 'send_message':
            return await self._send_message(stimulus)
        elif action == 'establish_connection':
            return await self._establish_connection(stimulus)
        elif action == 'close_connection':
            return await self._close_connection(stimulus)
        elif action == 'get_messages':
            return await self._get_messages(stimulus)
        else:
            return {'error': f'Unknown action: {action}'}
    
    async def _send_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wyślij wiadomość do innego bytu"""
        target_soul = params.get('target_soul')
        message = params.get('message', '')
        protocol = params.get('protocol', 'direct_call')
        
        if not target_soul:
            return {'error': 'Target soul required'}
        
        # Symulacja wysłania wiadomości
        message_id = f"msg_{len(self.message_queue)}"
        
        message_data = {
            'id': message_id,
            'from_soul': self.host_being.soul,
            'to_soul': target_soul,
            'message': message,
            'protocol': protocol,
            'timestamp': datetime.now().isoformat(),
            'status': 'sent'
        }
        
        self.message_queue.append(message_data)
        
        # Zwiększ autonomię przez komunikację
        await self.evolve_autonomy({'autonomy_boost': 1, 'reason': 'successful_communication'})
        
        await self._record_memory('message_sent', message_data)
        
        return {'status': 'sent', 'message_id': message_id}
    
    async def _establish_connection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Ustanów połączenie z innym bytem"""
        target_soul = params.get('target_soul')
        protocol = params.get('protocol', 'socket_io')
        
        if not target_soul:
            return {'error': 'Target soul required'}
        
        connection_id = f"conn_{target_soul}_{len(self.active_connections)}"
        
        self.active_connections[connection_id] = {
            'target_soul': target_soul,
            'protocol': protocol,
            'established_at': datetime.now().isoformat(),
            'status': 'active'
        }
        
        await self._record_memory('connection_established', {
            'connection_id': connection_id,
            'target_soul': target_soul,
            'protocol': protocol
        })
        
        return {'status': 'connected', 'connection_id': connection_id}
    
    async def close_connection(self, connection_id: str) -> Dict[str, Any]:
        """Zamknij połączenie"""
        if connection_id in self.active_connections:
            connection_info = self.active_connections.pop(connection_id)
            await self._record_memory('connection_closed', {
                'connection_id': connection_id,
                'target_soul': connection_info['target_soul']
            })
            return {'status': 'closed', 'connection_id': connection_id}
        
        return {'error': 'Connection not found'}
    
    async def _close_connection(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper dla close_connection"""
        connection_id = params.get('connection_id')
        if not connection_id:
            return {'error': 'Connection ID required'}
        
        return await self.close_connection(connection_id)
    
    async def _get_messages(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Pobierz wiadomości"""
        limit = params.get('limit', 10)
        return {
            'messages': self.message_queue[-limit:],
            'total_count': len(self.message_queue)
        }
    
    async def _record_memory(self, memory_type: str, data: Dict[str, Any]):
        """Zapisz pamięć genu"""
        from datetime import datetime
        
        memory = {
            'type': memory_type,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'gene_id': self.gene_id
        }
        
        self.gene_memories.append(memory)
        
        # Jeśli host istnieje, dodaj też do jego pamięci
        if self.host_being:
            self.host_being.memories.append(memory)
