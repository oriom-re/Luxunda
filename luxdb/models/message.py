
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
                "metadata": {"py_type": "dict", "default": {}}
            }
        }
        
        try:
            return await Soul.create(message_genotype, alias="lux_message")
        except Exception as e:
            print(f"❌ Błąd tworzenia Soul dla wiadomości: {e}")
            raise e

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
        limit: int = 10
    ) -> List['Message']:
        """
        Pobiera historię rozmowy dla danego fingerprint.
        
        Args:
            fingerprint: Browser fingerprint
            limit: Maksymalna liczba wiadomości (domyślnie 10)
            
        Returns:
            Lista wiadomości posortowana chronologicznie
        """
        from ..repository.being_repository import BeingRepository
        from .relationship import Relationship
        
        # Znajdź wszystkie relacje dla tego fingerprint
        relationships = await Relationship.get_all()
        message_ulids = []
        
        for rel in relationships:
            if (rel.source_ulid == fingerprint and 
                rel.relation_type == "browser_session"):
                message_ulids.append(rel.target_ulid)
        
        # Pobierz wiadomości
        messages = []
        for message_ulid in message_ulids[-limit:]:  # Ostatnie N wiadomości
            message = await cls.load_by_ulid(message_ulid)
            if message:
                messages.append(message)
        
        # Sortuj chronologicznie
        messages.sort(key=lambda m: getattr(m, 'timestamp', ''), reverse=False)
        
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
        for message_ulid in message_ulids[-limit:]:
            message = await cls.load_by_ulid(message_ulid)
            if message:
                messages.append(message)
        
        return messages

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje Message do słownika"""
        from dataclasses import asdict
        result = asdict(self)
        
        # Dodaj dodatkowe pola jeśli istnieją
        for attr in ['content', 'role', 'author_ulid', 'fingerprint', 'timestamp']:
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
        return f"Message({role}: {content_preview})"
