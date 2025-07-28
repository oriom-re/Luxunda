from typing import Dict, Any, List
from datetime import datetime
import json
import uuid
import time

from app_v2.beings.base import Being
from app_v2.relations.rel_base import Relationship
from app_v2.ai.embendding import create_embedding

class Message(Being):
    """Reprezentuje pojedynczą wiadomość w systemie"""


    async def create(self, message: dict, author_uid: str = None, source_uid: str = None, thread_uid: str = None, **kwargs) -> None:
        """Tworzy nową wiadomość"""
        self.uid = str(uuid.uuid4())
        self.genesis = {
            "name": f"Message-{self.uid[:8]}",
            "type": "message",
            "created_by": source_uid,
            "created_at": datetime.utcnow().isoformat(),
            "thread_id": thread_uid
        }
        self.attributes = message
        self.attributes.update(**kwargs)

        await self.save()

        if source_uid:
            await Relationship.create_from(being='message', source_uid=self.uid, target_uid=source_uid)
            await Relationship.create_to(being='message', source_uid=source_uid, target_uid=self.uid)
        if thread_uid:
            await Relationship.create_from(being="thread", source_uid=self.uid, target_uid=thread_uid)
            await Relationship.create_to(being="message", source_uid=thread_uid, target_uid=self.uid)
        if author_uid:
            await Relationship.create_from(being="author", source_uid=self.uid, target_uid=author_uid)
            await Relationship.create_to(being="message", source_uid=author_uid, target_uid=self.uid)


        return self
    

        

