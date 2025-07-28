from typing import Dict, Any, List
from datetime import datetime
import json
import uuid
from app_v2.beings.base import Being
from app_v2.beings.message import Message
from app_v2.database.soul_repository import SoulRepository, RelationshipRepository

class Thread(Being):
    """Zarządza wątkami, wiadomościami i relacjami"""

    @property
    def get_last_message_uid(self) -> str:
        """Zwraca UID ostatniej wiadomości w wątku"""
        return self.attributes.get('last_message_uid', None)

    async def create(self, source_uid:str, thread_id:str=None, **kwargs) -> None:
        """Tworzy nowy wątek"""

        self.uid = str(uuid.uuid4())
        self.genesis = {
            "name": f"Thread-{thread_id or str(uuid.uuid4())}",
            "type": "thread",
            "created_by": source_uid,
            "created_at": datetime.utcnow().isoformat()
        }
        self.attributes = {
            "messages": [],
            "last_message_uid": None,
            "instructions": {
                "summary": "Zarządzaj wiadomościami i relacjami w wątku.",
                "context": "Wątki służą do grupowania wiadomości i relacji."
            },
            "mind": {
                "threads": {},
            },
            "context": {},
            "config": {
                "max_messages": 100,
                "max_relations": 50,
                "summary_length": 200,
                "embedding_model": "text-embedding-ada-002",
                "relation_types": ["from_message", "from_thread"],
                "limit": 10,
            }
        }
        self.attributes.update(**kwargs)
        self.memories = ["Wątek został utworzony."]
        self.self_awareness = []
        await self.save()

    async def create_message(self, thread_id: str, message: Dict[str, Any]) -> None:
        """Dodaje wiadomość do wątku"""
        
        message = await Message().create(
            source_uid=message.get('source_uid', str(uuid.uuid4())),
            message=message,
            thread_uid=self.uid
        )
        if message:
            self.attributes["last_message_uid"] = message.uid

    def _generate_summary(self, messages: List[Dict[str, Any]]) -> str:
        """Generuje streszczenie wiadomości"""
        return " ".join([msg["content"] for msg in messages])

    @staticmethod
    def get_thread_context(thread_id: str, limit: int = None) -> Dict[str, Any]:
        """Zwraca kontekst wątku"""

        # pobiera relacje i wiadomości z wątku
        messages = RelationshipRepository.get_thread_context(thread_id, limit=limit)
        return messages