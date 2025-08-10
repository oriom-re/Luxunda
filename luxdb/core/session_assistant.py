"""
Session-Based Lux Assistant - Kontekstowy asystent dla użytkowników
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import ulid
import threading

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
        self._message_lock = threading.Lock()  # Lock dla sekwencyjnego tworzenia wiadomości

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
        """Przetwarza wiadomość użytkownika z kontekstem ostatnich 10 wiadomości"""
        try:
            # Odśwież aktywność
            self.session.refresh_activity()

            # Pobierz ostatnie 10 wiadomości z konwersacji
            conversation_history = await self.get_recent_messages(limit=10)

            # Utwórz wiadomość użytkownika jako Being
            message = await self.create_contextual_message(message_content)

            # Zbuduj kontekst konwersacji
            conversation_context = self._format_conversation_history(conversation_history)

            # Przetwórz przez Lux z pełnym kontekstem
            enhanced_prompt = f"""
            Kontekst sesji użytkownika:
            - Ostatnie działania: {self.get_recent_actions_summary()}
            - Aktywne projekty: {', '.join(self.session.project_tags)}
            - Czas sesji: {self.session.last_activity.strftime('%H:%M')}

            Historia ostatnich 10 wiadomości:
            {conversation_context}

            Aktywne eventy: {len(self.session.active_events)}

            Aktualna wiadomość użytkownika: {message_content}

            Odpowiedz jako Lux, uwzględniając pełną historię konwersacji i aktualny kontekst.
            """

            response = await self.lux_core.chat(enhanced_prompt)

            # Zapisz odpowiedź jako kolejną wiadomość
            await self.create_contextual_message(response, role="assistant")

            return response

        except Exception as e:
            print(f"❌ Błąd przetwarzania wiadomości: {e}")
            return f"Przepraszam, wystąpił błąd podczas przetwarzania wiadomości: {str(e)}"

    async def create_contextual_message(self, content: str, role: str = "user") -> Message:
        """Tworzy wiadomość z kontekstowymi relacjami z zachowaniem kolejności"""
        # Zapewnij sekwencyjne tworzenie wiadomości
        with self._message_lock:
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

    async def get_recent_messages(self, limit: int = 10, author_ulid: str = None) -> List:
        """
        Pobiera ostatnie wiadomości z konwersacji.
        
        Args:
            limit: Maksymalna liczba wiadomości
            author_ulid: Opcjonalny filtr po autorze
            
        Returns:
            Lista wiadomości posortowana chronologicznie
        """
        try:
            from ..models.message import Message
            
            if author_ulid:
                # Pobierz wiadomości konkretnego autora w tej sesji
                messages = await Message.get_by_author_in_session(
                    author_ulid=author_ulid,
                    fingerprint=self.session.user_fingerprint,
                    limit=limit
                )
            else:
                # Pobierz całą historię konwersacji dla tego fingerprint
                messages = await Message.get_conversation_history(
                    fingerprint=self.session.user_fingerprint,
                    limit=limit
                )
            
            return messages
        except Exception as e:
            print(f"⚠️ Błąd pobierania historii wiadomości: {e}")
            return []

    async def get_conversation_context_for_ai(self, limit: int = 10) -> str:
        """
        Pobiera kontekst konwersacji sformatowany dla AI.
        
        Args:
            limit: Maksymalna liczba wiadomości
            
        Returns:
            Sformatowany kontekst konwersacji
        """
        try:
            # Pobierz ostatnie wiadomości (wszystkich autorów)
            messages = await self.get_recent_messages(limit=limit)
            
            if not messages:
                return "Brak historii konwersacji."
            
            context_lines = []
            for message in messages:
                context_line = message.get_conversation_context()
                context_lines.append(context_line)
            
            return "\n".join(context_lines)
            
        except Exception as e:
            print(f"⚠️ Błąd formatowania kontekstu: {e}")
            return "Błąd podczas pobierania kontekstu konwersacji."

    def _format_conversation_history(self, messages: List) -> str:
        """
        Formatuje historię konwersacji do kontekstu GPT.
        
        Args:
            messages: Lista wiadomości
            
        Returns:
            Sformatowany kontekst konwersacji
        """
        if not messages:
            return "Brak historii konwersacji."
        
        context_lines = []
        for message in messages:
            try:
                context_line = message.get_conversation_context()
                context_lines.append(context_line)
            except Exception as e:
                print(f"⚠️ Błąd formatowania wiadomości {getattr(message, 'ulid', 'unknown')}: {e}")
                continue
        
        return "\n".join(context_lines) if context_lines else "Błąd formatowania historii konwersacji."tekstu"""
        if not messages:
            return "Brak poprzednich wiadomości w tej sesji."

        context_lines = []
        for i, message in enumerate(messages[-10:]):  # Ostatnie 10 wiadomości
            role = getattr(message, 'role', 'user')
            content = getattr(message, 'content', '')
            timestamp = getattr(message, 'timestamp', '')
            
            # Formatuj timestamp jeśli istnieje
            time_str = ""
            if timestamp:
                try:
                    from datetime import datetime
                    if isinstance(timestamp, str):
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = f" ({dt.strftime('%H:%M')})"
                except:
                    pass
            
            if role == 'assistant':
                context_lines.append(f"Assistant{time_str}: {content}")
            else:
                context_lines.append(f"User{time_str}: {content}")

        return '\n'.join(context_lines)

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

    async def build_enhanced_conversation_context(self, fragments: List, memories: List) -> Dict[str, Any]:
        """Buduje rozszerzony kontekst z fragmentami i pamięcią"""
        base_context = await self.build_conversation_context()

        base_context.update({
            "message_fragments_count": len(fragments),
            "relevant_memories_count": len(memories),
            "memory_importance_avg": sum(getattr(m, 'importance_level', 0) for m in memories) / max(len(memories), 1),
            "conversation_fragments": [getattr(f, 'content', '') for f in fragments[:5]]  # Pierwsze 5 fragmentów
        })

        return base_context

    def _format_memory_context(self, memories: List) -> str:
        """Formatuje pamięć wydarzeń do kontekstu"""
        if not memories:
            return "Brak istotnych wspomnień z tej sesji."

        context_lines = []
        for memory in memories[:5]:  # Top 5 najważniejszych
            memory_type = getattr(memory, 'memory_type', 'unknown')
            content = getattr(memory, 'content', '')
            importance = getattr(memory, 'importance_level', 0)
            context_lines.append(f"- [{memory_type.upper()}:{importance:.1f}] {content}")

        return '\n'.join(context_lines)

    def _format_fragments_context(self, fragments: List) -> str:
        """Formatuje fragmenty wiadomości do kontekstu"""
        if not fragments:
            return "Brak fragmentów wiadomości."

        context_lines = []
        for i, fragment in enumerate(fragments):
            frag_type = getattr(fragment, 'fragment_type', 'unknown')
            content = getattr(fragment, 'content', '')
            context_lines.append(f"{i+1}. [{frag_type}] {content}")

        return '\n'.join(context_lines)

    async def extract_and_store_insights(self, user_message: str, assistant_response: str, all_fragments: List):
        """Ekstraktuje i przechowuje istotne wglądy z rozmowy"""
        from ..models.memory_cache import MemoryCache

        # Prosta heurystyka - szukaj faktów i ważnych stwierdzeń
        insight_triggers = [
            "ważne:", "pamiętaj:", "wydarzenie:", "problem:", "rozwiązanie:",
            "ustalenie:", "decyzja:", "plan:", "status:", "aktualizacja:"
        ]

        combined_text = f"{user_message} {assistant_response}".lower()

        for trigger in insight_triggers:
            if trigger in combined_text:
                # Znajdź kontekst wokół trigger'a
                trigger_index = combined_text.find(trigger)
                context_start = max(0, trigger_index - 50)
                context_end = min(len(combined_text), trigger_index + 200)
                context = combined_text[context_start:context_end].strip()

                # Utwórz pamięć z wyższą ważnością
                await MemoryCache.create_memory(
                    memory_type="fact" if trigger in ["ustalenie:", "decyzja:", "status:"] else "insight",
                    content=context,
                    importance_level=0.8 if trigger in ["ważne:", "decyzja:"] else 0.6,
                    context_ulids=[f.ulid for f in all_fragments],
                    conversation_id=self.session.session_id,
                    author_ulid=self.session.user_ulid,
                    tags=["auto_extracted", "conversation"] + list(self.session.project_tags),
                    metadata={
                        "trigger_word": trigger,
                        "auto_extracted": True,
                        "session_duration": int((datetime.now() - self.session.created_at).total_seconds() / 60)
                    }
                )
                break  # Tylko jedna pamięć per wiadomość żeby nie spamować

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
    """Manager sesji dla asystentów AI"""

    def __init__(self):
        self.sessions: Dict[str, 'SessionAssistant'] = {}
        self.cleanup_interval = 3600  # 1 godzina
        self.global_lux_assistant = None  # Globalna instancja Lux Assistant

    async def initialize_global_lux(self, openai_api_key: str = None):
        """Inicjalizuje globalną instancję Lux Assistant"""
        self.global_lux_assistant = LuxAssistant(openai_api_key or "demo-key")
        await self.global_lux_assistant.initialize()
        print("Lux Assistant globalnie zainicjalizowany.")

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

        self.sessions[session_id] = assistant

        # Uruchom cleanup task jeśli nie działa
        if not self.cleanup_task or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self.cleanup_expired_sessions())

        print(f"🎯 Utworzono sesję {session_id} dla użytkownika {user_fingerprint}")
        return assistant

    async def get_session(self, session_id: str) -> Optional[SessionAssistant]:
        """Pobiera sesję asystenta"""
        session = self.sessions.get(session_id)
        if session and not session.is_active:
            # Opcjonalnie: można próbować reaktywować sesję lub zwrócić błąd
            print(f"⚠️ Sesja {session_id} jest nieaktywna (offline).")
            return None
        return session

    async def cleanup_expired_sessions(self):
        """Usuwa wygasłe sesje"""
        current_time = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if (current_time - session.last_activity).total_seconds() > self.cleanup_interval
        ]

        for session_id in expired_sessions:
            del self.sessions[session_id]
            print(f"🗑️ Usunięto wygasłą sesję: {session_id}")

        return len(expired_sessions)

    async def get_global_lux(self):
        """Zwraca globalną instancję Lux Assistant"""
        return self.global_lux_assistant

    async def chat_with_global_lux(self, message: str) -> str:
        """Komunikacja z globalnym Lux Assistant"""
        if self.global_lux_assistant:
            try:
                response = await self.global_lux_assistant.chat(message)
                return response
            except Exception as e:
                return f"❌ Błąd komunikacji z Lux: {e}"
        else:
            return "❌ Lux Assistant nie jest dostępny"

# Globalna instancja
session_manager = SessionManager()