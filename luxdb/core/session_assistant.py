
"""
Session-Based Lux Assistant - Kontekstowy asystent dla użytkowników
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import ulid

from ..models.being import Being
from ..models.soul import Soul
from ..models.event import Event
from ..models.message import Message
from ..models.relationship import Relationship
from ..ai_lux_assistant import LuxAssistant

@dataclass
class SessionContext:
    """Kontekst sesji użytkownika"""
    session_id: str
    user_fingerprint: str
    user_ulid: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    ttl_minutes: int = 30
    active_events: List[str] = field(default_factory=list)
    user_actions: List[Dict[str, Any]] = field(default_factory=list)
    conversation_context: Dict[str, Any] = field(default_factory=dict)
    project_tags: Set[str] = field(default_factory=set)
    
    def is_expired(self) -> bool:
        """Sprawdza czy sesja wygasła"""
        expiry_time = self.last_activity + timedelta(minutes=self.ttl_minutes)
        return datetime.now() > expiry_time
    
    def refresh_activity(self):
        """Odświeża czas ostatniej aktywności"""
        self.last_activity = datetime.now()

class SessionAssistant:
    """
    Instancja asystenta przypisana do konkretnej sesji użytkownika
    """
    
    def __init__(self, session_context: SessionContext, openai_api_key: str = None):
        self.session = session_context
        self.lux_core = LuxAssistant(openai_api_key or "demo-key")
        self.event_listeners: List[str] = []
        self.is_active = True
        self.offline_mode = False
        
    async def initialize(self):
        """Inicjalizuje asystenta dla sesji"""
        await self.lux_core.initialize()
        
        # Utwórz Being dla tej sesji asystenta
        session_genotype = {
            "genesis": {
                "name": f"session_assistant_{self.session.session_id}",
                "type": "session_assistant",
                "version": "1.0.0",
                "description": f"Asystent sesji dla użytkownika {self.session.user_fingerprint}"
            },
            "attributes": {
                "session_context": {"py_type": "dict"},
                "active_events": {"py_type": "List[str]"},
                "user_actions": {"py_type": "List[dict]"},
                "conversation_threads": {"py_type": "dict"}
            }
        }
        
        soul = await Soul.create(session_genotype, alias=f"session_soul_{self.session.session_id}")
        self.assistant_being = await Being.create(
            soul,
            {
                "session_context": self.session.__dict__,
                "active_events": [],
                "user_actions": [],
                "conversation_threads": {}
            },
            alias=f"session_assistant_{self.session.session_id}"
        )
        
        # Rozpocznij nasłuchiwanie eventów
        await self.start_event_monitoring()
        
        print(f"🤖 Session Assistant initialized for session {self.session.session_id}")
    
    async def start_event_monitoring(self):
        """Rozpoczyna monitorowanie eventów użytkownika"""
        # Znajdź wszystkie active eventy
        all_events = await Event.get_all()
        
        for event in all_events:
            if (hasattr(event, 'status') and event.status == 'active' and
                self._is_user_related_event(event)):
                await self.track_event(event)
    
    def _is_user_related_event(self, event: Event) -> bool:
        """Sprawdza czy event jest związany z tym użytkownikiem"""
        # Implementuj logikę sprawdzania czy event dotyczy tego użytkownika
        # Na podstawie fingerprint, user_ulid, lub innych metadanych
        event_metadata = getattr(event, 'payload', {})
        return (
            event_metadata.get('user_fingerprint') == self.session.user_fingerprint or
            event_metadata.get('user_ulid') == self.session.user_ulid
        )
    
    async def track_event(self, event: Event):
        """Śledzi nowy event użytkownika"""
        self.session.active_events.append(event.ulid)
        
        # Dodaj do kontekstu działań użytkownika
        action_context = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event.event_type,
            "event_ulid": event.ulid,
            "payload": getattr(event, 'payload', {}),
            "status": getattr(event, 'status', 'unknown')
        }
        
        self.session.user_actions.append(action_context)
        
        # Analizuj tagi projektowe
        await self.analyze_project_tags(action_context)
        
        # Odśwież aktywność
        self.session.refresh_activity()
        
        print(f"📊 Tracked event {event.event_type} for session {self.session.session_id}")
    
    async def analyze_project_tags(self, action_context: Dict[str, Any]):
        """Analizuje i dodaje tagi projektowe"""
        payload = action_context.get('payload', {})
        event_type = action_context.get('event_type', '')
        
        # Proste reguły tagowania (można rozbudować o AI)
        if 'luxunda' in str(payload).lower() or 'luxunda' in event_type.lower():
            self.session.project_tags.add('luxunda')
        
        if 'deployment' in event_type.lower():
            self.session.project_tags.add('deployment')
        
        if 'database' in event_type.lower():
            self.session.project_tags.add('database')
        
        # Dodaj więcej reguł...
    
    async def process_message(self, message_content: str) -> str:
        """Przetwarza wiadomość użytkownika z pełnym kontekstem"""
        # Odśwież aktywność
        self.session.refresh_activity()
        
        # Utwórz wiadomość jako Being z relacjami
        message = await self.create_contextual_message(message_content)
        
        # Zbuduj kontekst dla LLM
        context = await self.build_conversation_context()
        
        # Przetwórz przez Lux z kontekstem
        enhanced_prompt = f"""
        Kontekst sesji użytkownika:
        - Ostatnie działania: {self.get_recent_actions_summary()}
        - Aktywne projekty: {', '.join(self.session.project_tags)}
        - Czas sesji: {self.session.last_activity.strftime('%H:%M')}
        
        Aktywne eventy: {len(self.session.active_events)}
        
        Wiadomość użytkownika: {message_content}
        
        Odpowiedz jako Lux, uwzględniając pełny kontekst działań użytkownika.
        """
        
        response = await self.lux_core.chat(enhanced_prompt)
        
        # Zapisz odpowiedź jako kolejną wiadomość
        await self.create_contextual_message(response, role="assistant")
        
        return response
    
    async def create_contextual_message(self, content: str, role: str = "user") -> Message:
        """Tworzy wiadomość z kontekstowymi relacjami"""
        message = await Message.create(
            content=content,
            role=role,
            author_ulid=self.session.user_ulid,
            fingerprint=self.session.user_fingerprint,
            conversation_id=self.session.session_id
        )
        
        # Dodaj relacje do aktywnych projektów
        for project_tag in self.session.project_tags:
            await Relationship.create(
                source_ulid=message.ulid,
                target_ulid=project_tag,  # Możesz stworzyć Being dla projektu
                relation_type="relates_to_project",
                strength=1.0,
                metadata={
                    "project_tag": project_tag,
                    "session_id": self.session.session_id,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Dodaj relacje do ostatnich eventów
        for event_ulid in self.session.active_events[-5:]:  # Ostatnie 5 eventów
            await Relationship.create(
                source_ulid=message.ulid,
                target_ulid=event_ulid,
                relation_type="contextual_event",
                strength=0.8,
                metadata={
                    "session_id": self.session.session_id,
                    "context_type": "recent_activity"
                }
            )
        
        return message
    
    def get_recent_actions_summary(self) -> str:
        """Zwraca podsumowanie ostatnich działań"""
        recent = self.session.user_actions[-5:]  # Ostatnie 5 akcji
        if not recent:
            return "Brak ostatnich działań"
        
        summary = []
        for action in recent:
            event_type = action.get('event_type', 'unknown')
            timestamp = action.get('timestamp', '')
            summary.append(f"- {event_type} ({timestamp[-8:-3]})")  # HH:MM format
        
        return '\n'.join(summary)
    
    async def build_conversation_context(self) -> Dict[str, Any]:
        """Buduje pełny kontekst konwersacji"""
        return {
            "session_info": {
                "duration_minutes": int((datetime.now() - self.session.created_at).total_seconds() / 60),
                "activity_count": len(self.session.user_actions),
                "project_tags": list(self.session.project_tags)
            },
            "recent_activity": self.get_recent_actions_summary(),
            "active_events_count": len(self.session.active_events)
        }
    
    async def check_expiry(self) -> bool:
        """Sprawdza czy sesja wygasła i przełącza w tryb offline"""
        if self.session.is_expired() and self.is_active:
            await self.switch_to_offline_mode()
            return True
        return False
    
    async def switch_to_offline_mode(self):
        """Przełącza asystenta w tryb offline"""
        self.is_active = False
        self.offline_mode = True
        
        print(f"💤 Session Assistant {self.session.session_id} switched to offline mode")
        
        # Zapisz stan sesji przed przejściem w tryb offline
        if hasattr(self, 'assistant_being'):
            await self.assistant_being.save()
    
    async def handle_background_event(self, event: Event):
        """Obsługuje eventy w trybie offline"""
        if not self.offline_mode:
            return
        
        # Logika dla eventów w tle
        print(f"🔄 Background event processed: {event.event_type}")
        
        # Można dodać logikę zapisywania ważnych eventów do odtworzenia przy ponownym logowaniu

class SessionManager:
    """Manager wszystkich sesji asystentów"""
    
    def __init__(self):
        self.active_sessions: Dict[str, SessionAssistant] = {}
        self.cleanup_task = None
    
    async def create_session(self, user_fingerprint: str, user_ulid: str = None, ttl_minutes: int = 30) -> SessionAssistant:
        """Tworzy nową sesję asystenta"""
        session_id = str(ulid.ulid())
        
        context = SessionContext(
            session_id=session_id,
            user_fingerprint=user_fingerprint,
            user_ulid=user_ulid,
            ttl_minutes=ttl_minutes
        )
        
        assistant = SessionAssistant(context)
        await assistant.initialize()
        
        self.active_sessions[session_id] = assistant
        
        # Uruchom cleanup task jeśli nie działa
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self.cleanup_expired_sessions())
        
        print(f"🎯 Created session {session_id} for user {user_fingerprint}")
        return assistant
    
    async def get_session(self, session_id: str) -> Optional[SessionAssistant]:
        """Pobiera sesję asystenta"""
        return self.active_sessions.get(session_id)
    
    async def cleanup_expired_sessions(self):
        """Czyści wygasłe sesje"""
        while True:
            try:
                expired_sessions = []
                
                for session_id, assistant in self.active_sessions.items():
                    if await assistant.check_expiry():
                        expired_sessions.append(session_id)
                
                # Usuń wygasłe sesje
                for session_id in expired_sessions:
                    del self.active_sessions[session_id]
                    print(f"🗑️ Removed expired session {session_id}")
                
                await asyncio.sleep(60)  # Sprawdzaj co minutę
                
            except Exception as e:
                print(f"❌ Cleanup error: {e}")
                await asyncio.sleep(60)

# Globalna instancja
session_manager = SessionManager()
