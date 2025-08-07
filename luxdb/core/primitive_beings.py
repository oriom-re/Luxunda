
"""
LuxDB Primitive Beings System
============================

System pierwotnych bytów - fundament żywej architektury.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

class PrimitiveBeing:
    """Bazowa klasa dla pierwotnych bytów systemu"""
    
    def __init__(self, being_type: str, ulid: str = None):
        self.being_type = being_type
        self.ulid = ulid or str(uuid.uuid4())
        self.intentions = {}
        self.relations = {}
        self.active = False
        self.created_at = datetime.now()
        
    async def process_intention(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Przetwarza intencję skierowaną do bytu"""
        intention_type = intention.get('type')
        handler = self.intentions.get(intention_type)
        
        if handler:
            return await handler(intention)
        else:
            return {"status": "error", "message": f"Unknown intention: {intention_type}"}

    async def create_relation(self, target_being: 'PrimitiveBeing', relation_type: str, data: Dict[str, Any] = None):
        """Tworzy żywą relację z innym bytem"""
        relation_id = str(uuid.uuid4())
        relation = {
            "id": relation_id,
            "source": self.ulid,
            "target": target_being.ulid,
            "type": relation_type,
            "data": data or {},
            "status": "active",
            "created_at": datetime.now(),
            "history": []
        }
        
        self.relations[relation_id] = relation
        return relation

class DatabaseBeing(PrimitiveBeing):
    """Byt bazy danych - żywy system przechowywania i zarządzania danymi"""
    
    def __init__(self):
        super().__init__("database")
        self.storage = {}
        self.schemas = {}
        self.connections = {}
        
        # Rejestracja intencji
        self.intentions = {
            "store_data": self._store_data,
            "retrieve_data": self._retrieve_data,
            "create_schema": self._create_schema,
            "query_data": self._query_data,
            "establish_connection": self._establish_connection
        }
    
    async def _store_data(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Przechowuje dane zgodnie z intencją"""
        data = intention.get('data')
        schema = intention.get('schema', 'default')
        
        if schema not in self.storage:
            self.storage[schema] = []
            
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "data": data,
            "stored_at": datetime.now(),
            "intention_id": intention.get('id')
        }
        
        self.storage[schema].append(entry)
        
        return {
            "status": "success",
            "entry_id": entry_id,
            "stored_in": schema
        }
    
    async def _retrieve_data(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Pobiera dane zgodnie z intencją"""
        schema = intention.get('schema', 'default')
        filters = intention.get('filters', {})
        
        if schema not in self.storage:
            return {"status": "error", "message": f"Schema {schema} not found"}
        
        results = []
        for entry in self.storage[schema]:
            if self._matches_filters(entry['data'], filters):
                results.append(entry)
        
        return {
            "status": "success",
            "results": results,
            "count": len(results)
        }
    
    async def _create_schema(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Tworzy nowy schemat danych"""
        schema_name = intention.get('schema_name')
        schema_def = intention.get('schema_definition')
        
        self.schemas[schema_name] = {
            "definition": schema_def,
            "created_at": datetime.now(),
            "creator": intention.get('creator')
        }
        
        if schema_name not in self.storage:
            self.storage[schema_name] = []
        
        return {
            "status": "success",
            "schema": schema_name,
            "created": True
        }
    
    async def _query_data(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Wykonuje zaawansowane zapytania"""
        query = intention.get('query')
        
        # Tutaj można zaimplementować zaawansowany silnik zapytań
        # Na razie prosty przykład
        results = []
        for schema_name, entries in self.storage.items():
            for entry in entries:
                if query.get('type') == 'all':
                    results.append({
                        "schema": schema_name,
                        "entry": entry
                    })
        
        return {
            "status": "success",
            "results": results,
            "query": query
        }
    
    async def _establish_connection(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Nawiązuje połączenie z bazą danych"""
        connection_id = str(uuid.uuid4())
        client_id = intention.get('client_id')
        
        connection = {
            "id": connection_id,
            "client_id": client_id,
            "established_at": datetime.now(),
            "status": "active",
            "queries_count": 0
        }
        
        self.connections[connection_id] = connection
        
        return {
            "status": "success",
            "connection_id": connection_id,
            "message": "Database connection established"
        }
    
    def _matches_filters(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Sprawdza czy dane pasują do filtrów"""
        for key, value in filters.items():
            if key not in data or data[key] != value:
                return False
        return True

class CommunicationBeing(PrimitiveBeing):
    """Byt komunikacyjny - zarządza wszystkimi formami komunikacji w systemie"""
    
    def __init__(self):
        super().__init__("communication")
        self.channels = {}
        self.active_connections = {}
        self.message_history = []
        
        self.intentions = {
            "create_channel": self._create_channel,
            "send_message": self._send_message,
            "establish_socket": self._establish_socket,
            "broadcast_message": self._broadcast_message,
            "get_message_history": self._get_message_history
        }
    
    async def _create_channel(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Tworzy nowy kanał komunikacyjny"""
        channel_name = intention.get('channel_name')
        channel_type = intention.get('channel_type', 'general')
        
        channel_id = str(uuid.uuid4())
        channel = {
            "id": channel_id,
            "name": channel_name,
            "type": channel_type,
            "created_at": datetime.now(),
            "participants": [],
            "message_count": 0,
            "status": "active"
        }
        
        self.channels[channel_id] = channel
        
        return {
            "status": "success",
            "channel_id": channel_id,
            "channel": channel
        }
    
    async def _send_message(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Wysyła wiadomość przez kanał"""
        channel_id = intention.get('channel_id')
        message = intention.get('message')
        sender = intention.get('sender')
        
        if channel_id not in self.channels:
            return {"status": "error", "message": "Channel not found"}
        
        message_id = str(uuid.uuid4())
        message_entry = {
            "id": message_id,
            "channel_id": channel_id,
            "sender": sender,
            "content": message,
            "sent_at": datetime.now(),
            "type": "message"
        }
        
        self.message_history.append(message_entry)
        self.channels[channel_id]["message_count"] += 1
        
        return {
            "status": "success",
            "message_id": message_id,
            "delivered": True
        }
    
    async def _establish_socket(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Nawiązuje połączenie socketowe"""
        client_id = intention.get('client_id')
        socket_type = intention.get('socket_type', 'websocket')
        
        connection_id = str(uuid.uuid4())
        connection = {
            "id": connection_id,
            "client_id": client_id,
            "type": socket_type,
            "established_at": datetime.now(),
            "status": "connected",
            "last_ping": datetime.now()
        }
        
        self.active_connections[connection_id] = connection
        
        # Tworzymy relację connection_ws z danymi połączenia
        await self.create_relation(
            target_being=self,  # Self-relation dla socketów
            relation_type="connection_ws",
            data={
                "connection_id": connection_id,
                "status": "connected",
                "client_info": intention.get('client_info', {})
            }
        )
        
        return {
            "status": "success",
            "connection_id": connection_id,
            "socket_established": True
        }
    
    async def _broadcast_message(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Rozsyła wiadomość do wszystkich połączonych klientów"""
        message = intention.get('message')
        sender = intention.get('sender', 'system')
        
        broadcast_id = str(uuid.uuid4())
        delivered_count = 0
        
        for connection_id, connection in self.active_connections.items():
            if connection['status'] == 'connected':
                # Tutaj normalnie wysłalibyśmy przez socket
                delivered_count += 1
        
        broadcast_entry = {
            "id": broadcast_id,
            "message": message,
            "sender": sender,
            "delivered_to": delivered_count,
            "broadcast_at": datetime.now()
        }
        
        self.message_history.append(broadcast_entry)
        
        return {
            "status": "success",
            "broadcast_id": broadcast_id,
            "delivered_count": delivered_count
        }
    
    async def _get_message_history(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Pobiera historię wiadomości"""
        channel_id = intention.get('channel_id')
        limit = intention.get('limit', 50)
        
        if channel_id:
            messages = [msg for msg in self.message_history if msg.get('channel_id') == channel_id]
        else:
            messages = self.message_history
        
        # Sortuj według daty i ogranicz
        messages = sorted(messages, key=lambda x: x.get('sent_at', x.get('broadcast_at')), reverse=True)[:limit]
        
        return {
            "status": "success",
            "messages": messages,
            "count": len(messages)
        }

class KernelBeing(PrimitiveBeing):
    """Byt jądra - zarządza całym systemem i koordynuje działanie innych bytów"""
    
    def __init__(self):
        super().__init__("kernel")
        self.registered_beings = {}
        self.system_state = "initializing"
        self.task_queue = []
        self.performance_metrics = {}
        
        self.intentions = {
            "register_being": self._register_being,
            "execute_system_task": self._execute_system_task,
            "get_system_status": self._get_system_status,
            "coordinate_beings": self._coordinate_beings,
            "shutdown_system": self._shutdown_system
        }
    
    async def _register_being(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Rejestruje nowy byt w systemie"""
        being_info = intention.get('being_info')
        being_id = being_info.get('ulid')
        
        self.registered_beings[being_id] = {
            "info": being_info,
            "registered_at": datetime.now(),
            "status": "active",
            "last_heartbeat": datetime.now()
        }
        
        return {
            "status": "success",
            "being_id": being_id,
            "registered": True
        }
    
    async def _execute_system_task(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Wykonuje zadanie systemowe"""
        task = intention.get('task')
        priority = intention.get('priority', 1)
        
        task_id = str(uuid.uuid4())
        task_entry = {
            "id": task_id,
            "task": task,
            "priority": priority,
            "created_at": datetime.now(),
            "status": "queued"
        }
        
        self.task_queue.append(task_entry)
        self.task_queue.sort(key=lambda x: x['priority'], reverse=True)
        
        return {
            "status": "success",
            "task_id": task_id,
            "queued": True
        }
    
    async def _get_system_status(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Zwraca status całego systemu"""
        return {
            "status": "success",
            "system_state": self.system_state,
            "registered_beings": len(self.registered_beings),
            "active_tasks": len([t for t in self.task_queue if t['status'] == 'running']),
            "queued_tasks": len([t for t in self.task_queue if t['status'] == 'queued']),
            "uptime": (datetime.now() - self.created_at).total_seconds(),
            "beings": list(self.registered_beings.keys())
        }
    
    async def _coordinate_beings(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Koordynuje działanie między bytami"""
        coordination_type = intention.get('coordination_type')
        beings = intention.get('beings', [])
        
        coordination_id = str(uuid.uuid4())
        coordination = {
            "id": coordination_id,
            "type": coordination_type,
            "beings": beings,
            "initiated_at": datetime.now(),
            "status": "coordinating"
        }
        
        # Tutaj logika koordynacji między bytami
        
        return {
            "status": "success",
            "coordination_id": coordination_id,
            "coordinating": True
        }
    
    async def _shutdown_system(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Wyłącza system w kontrolowany sposób"""
        shutdown_reason = intention.get('reason', 'manual')
        
        self.system_state = "shutting_down"
        
        # Powiadom wszystkie byty o wyłączeniu
        for being_id in self.registered_beings:
            # Wyślij intencję shutdown do każdego bytu
            pass
        
        return {
            "status": "success",
            "message": "System shutdown initiated",
            "reason": shutdown_reason
        }

class DispatcherBeing(PrimitiveBeing):
    """Dispatcher - inteligentnie kieruje powiadomienia tylko do zainteresowanych bytów"""
    
    def __init__(self):
        super().__init__("dispatcher")
        self.subscriptions = {}  # {relation_type: [being_ulids]}
        self.being_interests = {}  # {being_ulid: [relation_types]}
        self.notification_queue = []
        
        self.intentions = {
            "subscribe_to_relation": self._subscribe_to_relation,
            "unsubscribe_from_relation": self._unsubscribe_from_relation,
            "dispatch_notification": self._dispatch_notification,
            "get_subscribers": self._get_subscribers,
            "process_queue": self._process_queue
        }
    
    async def _subscribe_to_relation(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Rejestruje byt do otrzymywania powiadomień o określonym typie relacji"""
        being_ulid = intention.get('being_ulid')
        relation_type = intention.get('relation_type')
        
        if relation_type not in self.subscriptions:
            self.subscriptions[relation_type] = []
        
        if being_ulid not in self.subscriptions[relation_type]:
            self.subscriptions[relation_type].append(being_ulid)
        
        if being_ulid not in self.being_interests:
            self.being_interests[being_ulid] = []
        
        if relation_type not in self.being_interests[being_ulid]:
            self.being_interests[being_ulid].append(relation_type)
        
        return {
            "status": "success",
            "message": f"Being {being_ulid} subscribed to {relation_type}",
            "subscribers_count": len(self.subscriptions[relation_type])
        }
    
    async def _unsubscribe_from_relation(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Wypisuje byt z powiadomień"""
        being_ulid = intention.get('being_ulid')
        relation_type = intention.get('relation_type')
        
        if relation_type in self.subscriptions and being_ulid in self.subscriptions[relation_type]:
            self.subscriptions[relation_type].remove(being_ulid)
        
        if being_ulid in self.being_interests and relation_type in self.being_interests[being_ulid]:
            self.being_interests[being_ulid].remove(relation_type)
        
        return {
            "status": "success",
            "message": f"Being {being_ulid} unsubscribed from {relation_type}"
        }
    
    async def _dispatch_notification(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Wysyła powiadomienie tylko do zainteresowanych bytów"""
        relation_type = intention.get('relation_type')
        notification_data = intention.get('notification_data')
        source_being = intention.get('source_being')
        
        subscribers = self.subscriptions.get(relation_type, [])
        dispatched_count = 0
        
        notification = {
            "id": str(uuid.uuid4()),
            "relation_type": relation_type,
            "data": notification_data,
            "source_being": source_being,
            "timestamp": datetime.now(),
            "dispatched_to": []
        }
        
        for subscriber_ulid in subscribers:
            # Tutaj normalnie wysłalibyśmy do konkretnego bytu
            notification["dispatched_to"].append(subscriber_ulid)
            dispatched_count += 1
        
        self.notification_queue.append(notification)
        
        return {
            "status": "success",
            "notification_id": notification["id"],
            "dispatched_count": dispatched_count,
            "subscribers": subscribers
        }
    
    async def _get_subscribers(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Zwraca listę subskrybentów dla danego typu relacji"""
        relation_type = intention.get('relation_type')
        
        return {
            "status": "success",
            "relation_type": relation_type,
            "subscribers": self.subscriptions.get(relation_type, []),
            "total_subscribers": len(self.subscriptions.get(relation_type, []))
        }
    
    async def _process_queue(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Przetwarza kolejkę powiadomień"""
        processed = len(self.notification_queue)
        
        # Tutaj normalnie wysłalibyśmy wszystkie powiadomienia
        self.notification_queue.clear()
        
        return {
            "status": "success",
            "processed_notifications": processed
        }

# System Orchestrator - łączy wszystkie pierwotne byty
class PrimitiveSystemOrchestrator:
    """Orkiestrator systemu pierwotnych bytów"""
    
    def __init__(self):
        self.kernel = KernelBeing()
        self.database = DatabaseBeing()
        self.communication = CommunicationBeing()
        self.dispatcher = DispatcherBeing()
        self.intention_router = {}
        
    async def initialize(self):
        """Inicjalizuje system pierwotnych bytów"""
        print("🚀 Inicjalizacja systemu pierwotnych bytów...")
        
        # Aktywuj byty
        self.kernel.active = True
        self.database.active = True
        self.communication.active = True
        self.dispatcher.active = True
        
        # Zarejestruj byty w kernel
        await self.kernel.process_intention({
            "type": "register_being",
            "being_info": {"ulid": self.database.ulid, "type": "database"}
        })
        
        await self.kernel.process_intention({
            "type": "register_being", 
            "being_info": {"ulid": self.communication.ulid, "type": "communication"}
        })
        
        await self.kernel.process_intention({
            "type": "register_being", 
            "being_info": {"ulid": self.dispatcher.ulid, "type": "dispatcher"}
        })
        
        # Utwórz relacje między bytami
        await self.kernel.create_relation(self.database, "manages_data", {"role": "data_manager"})
        await self.kernel.create_relation(self.communication, "manages_comm", {"role": "communication_manager"})
        await self.kernel.create_relation(self.dispatcher, "manages_notifications", {"role": "notification_dispatcher"})
        await self.database.create_relation(self.communication, "data_channel", {"purpose": "data_exchange"})
        
        # Setup automatic subscriptions
        # Communication subskrybuje connection_ws relacje
        await self.dispatcher.process_intention({
            "type": "subscribe_to_relation",
            "being_ulid": self.communication.ulid,
            "relation_type": "connection_ws"
        })
        
        # Database subskrybuje data_update relacje
        await self.dispatcher.process_intention({
            "type": "subscribe_to_relation",
            "being_ulid": self.database.ulid,
            "relation_type": "data_update"
        })
        
        # Uaktualnij stan systemu
        self.kernel.system_state = "running"
        
        print("✅ System pierwotnych bytów zainicjalizowany")
        print(f"📡 Dispatcher aktywny z {len(self.dispatcher.subscriptions)} typami subskrypcji")
        
        return {
            "status": "initialized",
            "beings": {
                "kernel": self.kernel.ulid,
                "database": self.database.ulid,
                "communication": self.communication.ulid,
                "dispatcher": self.dispatcher.ulid
            }
        }
    
    async def process_intention(self, intention: Dict[str, Any]) -> Dict[str, Any]:
        """Kieruje intencję do odpowiedniego bytu"""
        target_being = intention.get('target_being', 'kernel')
        
        if target_being == 'kernel':
            return await self.kernel.process_intention(intention)
        elif target_being == 'database':
            return await self.database.process_intention(intention)
        elif target_being == 'communication':
            return await self.communication.process_intention(intention)
        elif target_being == 'dispatcher':
            return await self.dispatcher.process_intention(intention)
        else:
            return {"status": "error", "message": f"Unknown target being: {target_being}"}
    
    async def get_system_overview(self) -> Dict[str, Any]:
        """Zwraca przegląd całego systemu"""
        kernel_status = await self.kernel.process_intention({"type": "get_system_status"})
        
        return {
            "system_status": kernel_status,
            "beings": {
                "kernel": {
                    "ulid": self.kernel.ulid,
                    "active": self.kernel.active,
                    "relations": len(self.kernel.relations)
                },
                "database": {
                    "ulid": self.database.ulid,
                    "active": self.database.active,
                    "schemas": len(self.database.schemas),
                    "connections": len(self.database.connections)
                },
                "communication": {
                    "ulid": self.communication.ulid,
                    "active": self.communication.active,
                    "channels": len(self.communication.channels),
                    "connections": len(self.communication.active_connections)
                },
                "dispatcher": {
                    "ulid": self.dispatcher.ulid,
                    "active": self.dispatcher.active,
                    "subscriptions": len(self.dispatcher.subscriptions),
                    "queue_size": len(self.dispatcher.notification_queue),
                    "total_subscribers": sum(len(subs) for subs in self.dispatcher.subscriptions.values())
                }
            }
        }
