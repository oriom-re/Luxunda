"""
Communication System - Event-driven communication through database
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

# Import ulid safely
try:
    import ulid
except ImportError:
    # Fallback ULID generator
    import uuid
    import time
    
    class ULID:
        @staticmethod
        def ulid():
            # Simple ULID-like generator using timestamp + uuid
            timestamp = int(time.time() * 1000)
            random_part = str(uuid.uuid4()).replace('-', '')[:10]
            return f"{timestamp:013x}{random_part}"
    
    ulid = ULID()

try:
    from .event_listener import DatabaseEventListener, event_bus
except ImportError:
    # Fallback - tworzymy podstawową klasę
    class DatabaseEventListener:
        def __init__(self, name):
            self.name = name
            self.subscribers = {}
            self.is_listening = False
        
        def subscribe(self, event_type: str, handler):
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(handler)
        
        async def start_listening(self, poll_interval: float = 1.0):
            self.is_listening = True
        
        def stop_listening(self):
            self.is_listening = False
    
    # Mock event_bus
    class EventBus:
        async def create_listener(self, name):
            return DatabaseEventListener(name)
    
    event_bus = EventBus()
from ..models.being import Being
from ..models.event import Event
from ..models.relationship import Relationship

class MessageHandler:
    """Handler dla wiadomości w systemie komunikacji"""
    
    def __init__(self):
        self.active_messages = {}
        self.message_history = []
    
    async def process_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Przetwarza wiadomość"""
        message_id = message_data.get("id", str(ulid.ulid()))
        self.active_messages[message_id] = message_data
        
        return {
            "message_id": message_id,
            "status": "processed",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_message_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Pobiera historię wiadomości"""
        return self.message_history[-limit:]

class NamespaceManager:
    """Manager przestrzeni nazw dla komunikacji"""
    
    def __init__(self):
        self.namespaces = {}
        self.default_namespace = "default"
    
    def get_namespace(self, namespace_id: str) -> Dict[str, Any]:
        """Pobiera przestrzeń nazw"""
        return self.namespaces.get(namespace_id, {
            "id": namespace_id,
            "connections": [],
            "created_at": datetime.now().isoformat()
        })
    
    def create_namespace(self, namespace_id: str) -> Dict[str, Any]:
        """Tworzy nową przestrzeń nazw"""
        namespace = {
            "id": namespace_id,
            "connections": [],
            "created_at": datetime.now().isoformat()
        }
        self.namespaces[namespace_id] = namespace
        return namespace

class CommunicationSystem:
    """
    System komunikacji oparty na eventach w bazie danych
    """

    def __init__(self):
        self.backend_listeners: Dict[str, DatabaseEventListener] = {}
        self.frontend_connections: Dict[str, Dict[str, Any]] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.main_backend_listener = None
        self.is_active = False
        self.message_handler = MessageHandler()
        self.event_listeners = []
        self.namespace_manager = NamespaceManager()
        self.is_initialized = True
        print("💬 Communication System initialized")

    async def initialize(self):
        """Inicjalizuje system komunikacji"""
        # Sprawdź czy event_bus jest dostępny
        try:
            from ..models.event import Event
            self.is_active = True
        except ImportError:
            print("⚠️ Event system not available, using basic communication")
            self.is_active = False
            return

        # Utwórz główny listener backendu jeśli event_bus jest dostępny
        try:
            # self.main_backend_listener = await event_bus.create_listener("main_backend")
            self.is_active = True
        except Exception as e:
            print(f"⚠️ Event bus initialization failed: {e}")
            self.is_active = False

        # Subskrybuj kluczowe eventy
        self.main_backend_listener.subscribe("user_login", self._handle_user_login)
        self.main_backend_listener.subscribe("user_logout", self._handle_user_logout)
        self.main_backend_listener.subscribe("connection_heartbeat", self._handle_heartbeat)
        self.main_backend_listener.subscribe("frontend_event", self._handle_frontend_event)
        self.main_backend_listener.subscribe("lux_response", self._handle_lux_response)

        # Uruchom listener
        asyncio.create_task(self.main_backend_listener.start_listening(poll_interval=0.5))

        print("📡 Communication System initialized")

    async def _handle_user_login(self, event_data: Dict[str, Any]):
        """Obsługuje logowanie użytkownika"""
        user_ulid = event_data.get("user_ulid")
        session_id = event_data.get("session_id")
        connection_ulid = event_data.get("connection_ulid")

        if not all([user_ulid, session_id, connection_ulid]):
            return

        # Utwórz dedykowany listener dla użytkownika
        user_listener = await event_bus.create_listener(f"user_{user_ulid}")

        # Subskrybuj eventy specyficzne dla tego użytkownika
        user_listener.subscribe("stream_data", lambda data: self._handle_user_stream(user_ulid, data))
        user_listener.subscribe("notification", lambda data: self._handle_user_notification(user_ulid, data))
        user_listener.subscribe("being_update", lambda data: self._handle_being_update(user_ulid, data))

        # Uruchom listener użytkownika
        asyncio.create_task(user_listener.start_listening(poll_interval=0.3))

        self.backend_listeners[user_ulid] = user_listener

        # Wyślij potwierdzenie połączenia
        await self.send_to_frontend(connection_ulid, {
            "type": "connection_established",
            "session_id": session_id,
            "user_ulid": user_ulid,
            "status": "authenticated",
            "timestamp": datetime.now().isoformat()
        })

        print(f"🔗 User communication established: {user_ulid[:8]}...")

    async def _handle_user_logout(self, event_data: Dict[str, Any]):
        """Obsługuje wylogowanie użytkownika"""
        user_ulid = event_data.get("user_ulid")
        connection_ulid = event_data.get("connection_ulid")

        if user_ulid in self.backend_listeners:
            # Zatrzymaj listener użytkownika
            self.backend_listeners[user_ulid].stop_listening()
            del self.backend_listeners[user_ulid]

        # Wyślij potwierdzenie rozłączenia
        if connection_ulid:
            await self.send_to_frontend(connection_ulid, {
                "type": "connection_closed",
                "user_ulid": user_ulid,
                "reason": "logout",
                "timestamp": datetime.now().isoformat()
            })

        print(f"🔌 User communication closed: {user_ulid[:8]}...")

    async def _handle_heartbeat(self, event_data: Dict[str, Any]):
        """Obsługuje heartbeat połączeń"""
        connection_ulid = event_data.get("connection_ulid")

        if connection_ulid:
            # Aktualizuj status połączenia w bazie
            await Event.create_event(
                "connection_status_update",
                {
                    "connection_ulid": connection_ulid,
                    "status": "alive",
                    "last_seen": datetime.now().isoformat()
                }
            )

    async def _handle_frontend_event(self, event_data: Dict[str, Any]):
        """Obsługuje eventy z frontendu"""
        event_type = event_data.get("event_type")
        user_ulid = event_data.get("user_ulid")
        payload = event_data.get("payload", {})

        if event_type == "lux_message":
            # Przekaż wiadomość do Lux Assistant
            await self._forward_to_lux_assistant(user_ulid, payload)

        elif event_type == "being_action":
            # Obsłuż akcję na bycie
            await self._handle_being_action(user_ulid, payload)

        elif event_type == "stream_request":
            # Rozpocznij streaming danych
            await self._start_data_stream(user_ulid, payload)

        print(f"📥 Frontend event processed: {event_type}")

    async def _forward_to_lux_assistant(self, user_ulid: str, payload: Dict[str, Any]):
        """Przekazuje wiadomość do Lux Assistant"""
        from .auth_session import auth_manager

        # Znajdź aktywną sesję użytkownika
        user_session = None
        for session_data in auth_manager.active_sessions.values():
            if session_data.get("user_ulid") == user_ulid:
                user_session = session_data
                break

        if not user_session:
            return

        # Pobierz Lux Assistant
        from .session_assistant import session_manager
        lux_assistant = await session_manager.get_session(user_session.get("lux_assistant_id"))

        if lux_assistant:
            message_content = payload.get("message", "")
            response = await lux_assistant.process_message(message_content)

            # Wyślij odpowiedź z powrotem do frontendu
            await self.send_to_frontend(user_session["connection_ulid"], {
                "type": "lux_response",
                "message": response,
                "timestamp": datetime.now().isoformat()
            })

    async def _handle_user_stream(self, user_ulid: str, event_data: Dict[str, Any]):
        """Obsługuje stream danych dla użytkownika"""
        stream_type = event_data.get("stream_type")
        data = event_data.get("data")

        # Znajdź connection_ulid dla użytkownika
        from .auth_session import auth_manager
        connection_ulid = None

        for session_data in auth_manager.active_sessions.values():
            if session_data.get("user_ulid") == user_ulid:
                connection_ulid = session_data.get("connection_ulid")
                break

        if connection_ulid:
            await self.send_to_frontend(connection_ulid, {
                "type": "stream_data",
                "stream_type": stream_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })

    async def _handle_user_notification(self, user_ulid: str, event_data: Dict[str, Any]):
        """Obsługuje notyfikacje dla użytkownika"""
        notification_type = event_data.get("notification_type")
        message = event_data.get("message")
        priority = event_data.get("priority", "normal")

        # Znajdź connection_ulid dla użytkownika
        from .auth_session import auth_manager
        connection_ulid = None

        for session_data in auth_manager.active_sessions.values():
            if session_data.get("user_ulid") == user_ulid:
                connection_ulid = session_data.get("connection_ulid")
                break

        if connection_ulid:
            await self.send_to_frontend(connection_ulid, {
                "type": "notification",
                "notification_type": notification_type,
                "message": message,
                "priority": priority,
                "timestamp": datetime.now().isoformat()
            })

    async def _handle_being_update(self, user_ulid: str, event_data: Dict[str, Any]):
        """Obsługuje aktualizacje bytów"""
        being_ulid = event_data.get("being_ulid")
        update_type = event_data.get("update_type")
        changes = event_data.get("changes", {})

        # Znajdź connection_ulid dla użytkownika
        from .auth_session import auth_manager
        connection_ulid = None

        for session_data in auth_manager.active_sessions.values():
            if session_data.get("user_ulid") == user_ulid:
                connection_ulid = session_data.get("connection_ulid")
                break

        if connection_ulid:
            await self.send_to_frontend(connection_ulid, {
                "type": "being_update",
                "being_ulid": being_ulid,
                "update_type": update_type,
                "changes": changes,
                "timestamp": datetime.now().isoformat()
            })

    async def send_to_frontend(self, connection_ulid: str, data: Dict[str, Any]):
        """Wysyła dane do frontendu przez event w bazie"""
        await Event.create_event(
            "frontend_message",
            {
                "target_connection": connection_ulid,
                "message_data": data,
                "priority": data.get("priority", "normal")
            }
        )

        print(f"📤 Message sent to frontend: {connection_ulid[:8]}... ({data.get('type', 'unknown')})")

    async def send_notification_to_user(self, user_ulid: str, notification_type: str, message: str, priority: str = "normal"):
        """Wysyła notyfikację do konkretnego użytkownika"""
        await Event.create_event(
            "notification",
            {
                "target_user": user_ulid,
                "notification_type": notification_type,
                "message": message,
                "priority": priority
            }
        )

    async def broadcast_to_all_users(self, message_type: str, data: Dict[str, Any]):
        """Broadcastuje wiadomość do wszystkich aktywnych użytkowników"""
        from .auth_session import auth_manager

        for session_data in auth_manager.active_sessions.values():
            connection_ulid = session_data.get("connection_ulid")
            if connection_ulid:
                await self.send_to_frontend(connection_ulid, {
                    "type": message_type,
                    **data,
                    "timestamp": datetime.now().isoformat()
                })

    async def start_data_stream_for_user(self, user_ulid: str, stream_type: str, stream_config: Dict[str, Any]):
        """Rozpoczyna streaming danych dla użytkownika"""
        await Event.create_event(
            "stream_data",
            {
                "target_user": user_ulid,
                "stream_type": stream_type,
                "config": stream_config,
                "action": "start"
            }
        )

    async def stop_data_stream_for_user(self, user_ulid: str, stream_type: str):
        """Zatrzymuje streaming danych dla użytkownika"""
        await Event.create_event(
            "stream_data",
            {
                "target_user": user_ulid,
                "stream_type": stream_type,
                "action": "stop"
            }
        )

# Globalna instancja
communication_system = CommunicationSystem()