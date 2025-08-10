"""
Model Message (Wiadomość) dla LuxDB z relacjami author i fingerprint.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import ulid

from ..core.globals import Globals
from .soul import Soul

@dataclass
class Message:
    """
    Message reprezentuje wiadomość w rozmowie z asystentem.

    Zawiera relacje:
    - author: ULID autora (asystent, użytkownik zalogowany, lub None dla anonima)
    - fingerprint: browser fingerprint dla kontynuacji rozmowy
    """

    ulid: str = field(default_factory=lambda: str(ulid.ulid()))
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    soul_hash: Optional[str] = None
    alias: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    genotype: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    async def create(
        cls,
        content: str,
        role: str = "user",
        author_ulid: Optional[str] = None,
        fingerprint: str = None,
        conversation_id: Optional[str] = None,
        metadata: Dict[str, Any] = None,
        create_fragments: bool = True
    ) -> 'Message':
        """
        Tworzy nową wiadomość.

        Args:
            content: Treść wiadomości
            role: Rola (user/assistant/system)
            author_ulid: ULID autora (None dla anonima)
            fingerprint: Browser fingerprint
            conversation_id: ID konwersacji (opcjonalne)
            metadata: Dodatkowe metadane

        Returns:
            Nowy obiekt Message
        """
        # Pobierz lub utwórz Soul dla wiadomości
        soul = await cls._get_or_create_message_soul()

        message_data = {
            "content": content,
            "role": role,
            "author_ulid": author_ulid,  # None dla anonima
            "fingerprint": fingerprint,
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        from ..repository.soul_repository import BeingRepository

        # Walidacja danych względem genotypu
        errors = soul.validate_data(message_data)
        if errors:
            raise ValueError(f"Data validation errors: {', '.join(errors)}")

        # Tworzenie Message
        message = cls(
            ulid=str(ulid.ulid()),
            soul_hash=soul.soul_hash,
            genotype=soul.genotype,
            alias=f"msg_{role}_{fingerprint[:8]}" if fingerprint else f"msg_{role}"
        )

        # Zastosowanie genotypu
        message._apply_genotype(soul.genotype)

        # Ustal sekwencję dla nowej wiadomości
        sequence_number = await cls._get_next_sequence_number(conversation_id, fingerprint, author_ulid)
        setattr(message, "sequence_number", sequence_number)

        # Ustawienie danych
        for key, value in message_data.items():
            setattr(message, key, value)

        # Zapis do bazy danych
        from ..repository.soul_repository import BeingRepository
        await BeingRepository.insert_data_transaction(message, soul.genotype)

        # Utwórz relacje
        if author_ulid:
            await cls._create_author_relation(message.ulid, author_ulid)

        if fingerprint:
            await cls._create_fingerprint_relation(message.ulid, fingerprint)

        # Automatycznie utwórz fragmenty jeśli wymagane
        if create_fragments and len(content) > 50:  # Tylko dla dłuższych wiadomości
            from .message_fragment import MessageFragment
            await MessageFragment.create_from_message(
                message_content=content,
                message_ulid=message.ulid,
                author_ulid=author_ulid,
                fingerprint=fingerprint,
                conversation_id=conversation_id,
                metadata=metadata
            )

        return message

    def _apply_genotype(self, genotype: dict):
        """Dynamicznie dodaje pola z genotypu do obiektu Message"""
        from dataclasses import make_dataclass, field

        fields = []
        type_map = {
            "str": str,
            "int": int,
            "bool": bool,
            "float": float,
            "dict": dict,
            "List[str]": list,
            "List[float]": list
        }

        attributes = genotype.get("attributes", {})
        for name, meta in attributes.items():
            type_name = meta.get("py_type", "str")
            py_type = type_map.get(type_name, str)
            fields.append((name, py_type, field(default=None)))

        if fields:
            DynamicMessage = make_dataclass(
                cls_name="DynamicMessage",
                fields=fields,
                bases=(self.__class__,),
                frozen=False
            )
            self.__class__ = DynamicMessage

    @classmethod
    async def _get_or_create_message_soul(cls) -> Soul:
        """Pobiera lub tworzy Soul dla wiadomości"""
        try:
            soul = await Soul.get_by_alias("lux_message")
            if soul:
                return soul
        except Exception as e:
            print(f"⚠️ Nie można załadować istniejącej Soul: {e}")

        # Utwórz nowy soul
        message_genotype = {
            "genesis": {
                "name": "lux_message",
                "type": "message",
                "version": "1.0.0",
                "doc": "Wiadomość w rozmowie z asystentem Lux"
            },
            "attributes": {
                "content": {"py_type": "str", "required": True},
                "role": {"py_type": "str", "default": "user"},
                "author_ulid": {"py_type": "str", "required": False},
                "fingerprint": {"py_type": "str", "required": False},
                "conversation_id": {"py_type": "str", "required": False},
                "timestamp": {"py_type": "str", "required": False},
                "sequence_number": {"py_type": "int", "required": True},
                "metadata": {"py_type": "dict", "default": {}}
            }
        }

        try:
            return await Soul.create(message_genotype, alias="lux_message")
        except Exception as e:
            print(f"❌ Błąd tworzenia Soul dla wiadomości: {e}")
            raise e

    @classmethod
    async def _get_next_sequence_number(cls, conversation_id: str, fingerprint: str, author_ulid: Optional[str] = None) -> int:
        """ Pobiera kolejny numer sekwencyjny dla danej konwersacji/sesji. """
        from ..repository.soul_repository import BeingRepository
        from .relationship import Relationship

        # Najpierw spróbuj pobrać wiadomości dla danej konwersacji i autora
        query_params = {
            "conversation_id": conversation_id,
            "fingerprint": fingerprint
        }
        if author_ulid:
            query_params["author_ulid"] = author_ulid

        # Użyj BeingRepository do wyszukania istniejących wiadomości, które pasują do kryteriów
        # Zakładamy, że BeingRepository może przyjmować parametry do filtrowania
        # W tym przykładzie symulujemy pobranie istniejących wiadomości
        # W rzeczywistości potrzebna byłaby bardziej zaawansowana logika wyszukiwania
        
        # Przykładowe pobranie wszystkich wiadomości, a następnie filtrowanie
        # To jest nieefektywne i powinno być zastąpione zapytaniem do bazy danych
        all_messages_data = await BeingRepository.get_all_data_for_type("message") # Symulacja
        
        relevant_messages = []
        for msg_data in all_messages_data:
            if (msg_data.get("conversation_id") == conversation_id and 
                msg_data.get("fingerprint") == fingerprint and
                (not author_ulid or msg_data.get("author_ulid") == author_ulid)):
                relevant_messages.append(msg_data)

        if not relevant_messages:
            return 1  # Pierwsza wiadomość w konwersacji/sesji

        # Znajdź maksymalny sequence_number
        max_sequence = 0
        for msg_data in relevant_messages:
            seq = msg_data.get("sequence_number")
            if seq is not None and seq > max_sequence:
                max_sequence = seq
        
        return max_sequence + 1


    @classmethod
    async def _create_author_relation(cls, message_ulid: str, author_ulid: str):
        """Tworzy relację author między wiadomością a autorem"""
        from .relationship import Relationship

        await Relationship.create(
            source_ulid=author_ulid,
            target_ulid=message_ulid,
            relation_type="authored",
            strength=1.0,
            metadata={
                "description": f"Author {author_ulid} created message {message_ulid}",
                "created_by": "lux_message_system"
            }
        )

    @classmethod
    async def _create_fingerprint_relation(cls, message_ulid: str, fingerprint: str):
        """Tworzy relację fingerprint między wiadomością a przeglądarką"""
        from .relationship import Relationship

        await Relationship.create(
            source_ulid=fingerprint,  # fingerprint jako source
            target_ulid=message_ulid,
            relation_type="browser_session",
            strength=1.0,
            metadata={
                "description": f"Browser {fingerprint[:8]}... created message {message_ulid}",
                "created_by": "lux_message_system"
            }
        )

    @classmethod
    async def get_conversation_history(
        cls,
        fingerprint: str,
        limit: int = 10,
        author_ulid: str = None,
        conversation_id: Optional[str] = None # Dodano conversation_id do filtrowania
    ) -> List['Message']:
        """
        Pobiera historię rozmowy dla danego fingerprint, opcjonalnie autora i ID konwersacji.

        Args:
            fingerprint: Browser fingerprint
            limit: Maksymalna liczba wiadomości (domyślnie 10)
            author_ulid: Opcjonalny filtr po autorze
            conversation_id: Opcjonalny filtr po ID konwersacji

        Returns:
            Lista wiadomości posortowana chronologicznie
        """
        from ..repository.soul_repository import BeingRepository
        from .relationship import Relationship

        # Znajdź wszystkie relacje dla tego fingerprint i opcjonalnie autora
        relationships = await Relationship.get_all()
        message_ulids_from_fingerprint = []
        
        for rel in relationships:
            if (rel.source_ulid == fingerprint and 
                rel.relation_type == "browser_session"):
                message_ulids_from_fingerprint.append(rel.target_ulid)

        message_ulids_from_author = []
        if author_ulid:
            for rel in relationships:
                if (rel.source_ulid == author_ulid and 
                    rel.relation_type == "authored"):
                    message_ulids_from_author.append(rel.target_ulid)
        else:
            # Jeśli nie ma autora, rozważ wszystkie wiadomości z fingerprint
            message_ulids_from_author = message_ulids_from_fingerprint

        # Połącz filtry: wiadomości muszą być powiązane z fingerprint i opcjonalnie z autorem
        filtered_message_ulids = list(set(message_ulids_from_fingerprint) & set(message_ulids_from_author))

        # Jeśli podano conversation_id, dodatkowo filtruj po nim
        final_message_ulids = []
        if conversation_id:
            for msg_ulid in filtered_message_ulids:
                message = await cls.load_by_ulid(msg_ulid)
                if message and getattr(message, 'conversation_id', None) == conversation_id:
                    final_message_ulids.append(msg_ulid)
        else:
            final_message_ulids = filtered_message_ulids

        # Pobierz wiadomości
        messages = []
        # Weź ostatnie 'limit' wiadomości, biorąc pod uwagę ich kolejność
        for message_ulid in sorted(final_message_ulids, key=lambda ulid: cls.load_by_ulid(ulid).get('sequence_number', 0) if cls.load_by_ulid(ulid) else 0)[-limit:]:
            message = await cls.load_by_ulid(message_ulid)
            if message:
                messages.append(message)

        # Sortuj po sequence_number, potem timestamp jako backup
        messages.sort(key=lambda m: (getattr(m, 'sequence_number', 0), getattr(m, 'timestamp', '')), reverse=False)

        return messages

    @classmethod
    async def load_by_ulid(cls, ulid: str) -> Optional['Message']:
        """Ładuje Message po ULID"""
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.get_by_ulid(ulid)
        return result.get('being') if result.get('success') else None

    @classmethod
    async def get_by_author(cls, author_ulid: str, limit: int = 20) -> List['Message']:
        """Pobiera wiadomości danego autora"""
        from .relationship import Relationship

        relationships = await Relationship.get_all()
        message_ulids = []

        for rel in relationships:
            if (rel.source_ulid == author_ulid and
                rel.relation_type == "authored"):
                message_ulids.append(rel.target_ulid)

        messages = []
        # Sortuj ULIDy na podstawie sequence_number przed pobraniem wiadomości
        ulid_sequence_pairs = []
        for message_ulid in message_ulids:
            message = await cls.load_by_ulid(message_ulid)
            if message:
                ulid_sequence_pairs.append((getattr(message, 'sequence_number', float('inf')), message_ulid))
        
        ulid_sequence_pairs.sort() # Sortowanie domyślnie po pierwszym elemencie (sequence_number)

        for _, message_ulid in ulid_sequence_pairs[-limit:]: # Weź ostatnie 'limit' wiadomości
            message = await cls.load_by_ulid(message_ulid)
            if message:
                messages.append(message)

        # Sortuj po sequence_number, potem timestamp jako backup
        messages.sort(key=lambda m: (getattr(m, 'sequence_number', 0), getattr(m, 'timestamp', '')), reverse=False)

        return messages

    @classmethod
    async def get_by_author_in_session(
        cls,
        author_ulid: str,
        fingerprint: str = None,
        limit: int = 10,
        conversation_id: Optional[str] = None # Dodano conversation_id do filtrowania
    ) -> List['Message']:
        """
        Pobiera wiadomości danego autora w kontekście sesji (fingerprint) i konwersacji.

        Args:
            author_ulid: ULID autora
            fingerprint: Browser fingerprint (opcjonalny)
            limit: Maksymalna liczba wiadomości
            conversation_id: Opcjonalny filtr po ID konwersacji

        Returns:
            Lista wiadomości autora posortowana chronologicznie
        """
        from .relationship import Relationship

        relationships = await Relationship.get_all()

        # Znajdź wiadomości autora
        author_message_ulids = []
        for rel in relationships:
            if (rel.source_ulid == author_ulid and
                rel.relation_type == "authored"):
                author_message_ulids.append(rel.target_ulid)

        # Jeśli podano fingerprint, dodatkowo filtruj po sesji
        if fingerprint:
            session_message_ulids = []
            for rel in relationships:
                if (rel.source_ulid == fingerprint and
                    rel.relation_type == "browser_session" and
                    rel.target_ulid in author_message_ulids):
                    session_message_ulids.append(rel.target_ulid)
            author_message_ulids = session_message_ulids
        
        # Jeśli podano conversation_id, dodatkowo filtruj po nim
        if conversation_id:
            conversation_message_ulids = []
            for msg_ulid in author_message_ulids:
                message = await cls.load_by_ulid(msg_ulid)
                if message and getattr(message, 'conversation_id', None) == conversation_id:
                    conversation_message_ulids.append(msg_ulid)
            author_message_ulids = conversation_message_ulids


        # Pobierz wiadomości
        messages = []
        # Sortuj ULIDy na podstawie sequence_number przed pobraniem wiadomości
        ulid_sequence_pairs = []
        for message_ulid in author_message_ulids:
            message = await cls.load_by_ulid(message_ulid)
            if message:
                ulid_sequence_pairs.append((getattr(message, 'sequence_number', float('inf')), message_ulid))
        
        ulid_sequence_pairs.sort() # Sortowanie domyślnie po pierwszym elemencie (sequence_number)

        for _, message_ulid in ulid_sequence_pairs[-limit:]: # Weź ostatnie 'limit' wiadomości
            message = await cls.load_by_ulid(message_ulid)
            if message:
                messages.append(message)

        # Sortuj po sequence_number, potem timestamp jako backup
        messages.sort(key=lambda m: (getattr(m, 'sequence_number', 0), getattr(m, 'timestamp', '')), reverse=False)

        return messages

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje Message do słownika"""
        from dataclasses import asdict
        result = asdict(self)

        # Dodaj dodatkowe pola jeśli istnieją
        for attr in ['content', 'role', 'author_ulid', 'fingerprint', 'timestamp', 'sequence_number', 'conversation_id']:
            if hasattr(self, attr):
                result[attr] = getattr(self, attr)

        return result

    def get_conversation_context(self) -> str:
        """Zwraca kontekst wiadomości do GPT"""
        role = getattr(self, 'role', 'user')
        content = getattr(self, 'content', '')
        author = getattr(self, 'author_ulid', None)

        if role == 'assistant':
            return f"Assistant: {content}"
        elif author:
            return f"User ({author[:8]}...): {content}"
        else:
            return f"Anonymous: {content}"

    def __repr__(self):
        role = getattr(self, 'role', 'unknown')
        content_preview = getattr(self, 'content', '')[:30] + "..." if len(getattr(self, 'content', '')) > 30 else getattr(self, 'content', '')
        sequence_number = getattr(self, 'sequence_number', 'N/A')
        return f"Message(Seq:{sequence_number}, {role}: {content_preview})"