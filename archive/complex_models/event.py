
"""
Event Model - reprezentuje zdarzenia systemowe jako Being
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .being import Being
from .soul import Soul

@dataclass
class Event(Being):
    """
    Event dziedziczy po Being - każde zdarzenie to byt
    """
    
    event_type: str = "generic"
    payload: Dict[str, Any] = field(default_factory=dict)
    progress: float = 0.0
    status: str = "pending"
    target_modules: List[str] = field(default_factory=list)
    
    @classmethod
    async def create_event(
        cls, 
        event_type: str,
        payload: Dict[str, Any],
        target_modules: List[str] = None,
        alias: str = None
    ) -> 'Event':
        """
        Tworzy nowe zdarzenie jako Being
        """
        # Genotype dla Event
        event_genotype = {
            "genesis": {
                "name": f"event_{event_type}",
                "type": "system_event",
                "version": "1.0.0",
                "description": f"System event of type {event_type}"
            },
            "properties": {
                "event_type": event_type,
                "payload": payload,
                "progress": 0.0,
                "status": "pending",
                "target_modules": target_modules or [],
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Utwórz Soul dla Event
        soul = await Soul.create(
            genotype=event_genotype,
            alias=f"event_soul_{event_type}"
        )
        
        # Utwórz Event Being
        event = cls(
            soul=soul,
            alias=alias or f"event_{event_type}_{datetime.now().strftime('%H%M%S')}",
            event_type=event_type,
            payload=payload,
            target_modules=target_modules or []
        )
        
        await event.save()
        return event
    
    async def update_progress(self, progress: float, status: str = None, additional_data: Dict = None):
        """
        Aktualizuje postęp zdarzenia - automatycznie powiadamia listenerów
        """
        self.progress = progress
        if status:
            self.status = status
            
        if additional_data:
            self.payload.update(additional_data)
            
        # Aktualizuj genotype w Soul
        self.soul.genotype["properties"].update({
            "progress": progress,
            "status": status or self.status,
            "payload": self.payload,
            "updated_at": datetime.now().isoformat()
        })
        
        await self.save()
        
        # Trigger dla listenerów - aktualizacja w bazie wywoła notyfikacje
        await self._notify_listeners()
    
    async def _notify_listeners(self):
        """
        Powiadamia listenery poprzez relacje w bazie
        """
        from ..repository.soul_repository import SoulRepository
        
        # Znajdź wszystkich listenerów tego typu eventów
        listeners = await SoulRepository.find_by_genotype_type("event_listener")
        
        for listener in listeners:
            if self.event_type in listener.genotype.get("properties", {}).get("subscribed_events", []):
                # Utwórz relację Event -> Listener
                from .relationship import Relationship
                await Relationship.create(
                    source_ulid=self.ulid,
                    target_ulid=listener.ulid,
                    relation_type="notifies",
                    strength=1.0,
                    metadata={
                        "event_type": self.event_type,
                        "progress": self.progress,
                        "status": self.status,
                        "timestamp": datetime.now().isoformat()
                    }
                )
    
    async def complete(self, result: Dict[str, Any] = None):
        """
        Oznacza zdarzenie jako zakończone
        """
        await self.update_progress(100.0, "completed", result or {})
    
    async def fail(self, error: str, details: Dict[str, Any] = None):
        """
        Oznacza zdarzenie jako nieudane
        """
        error_data = {"error": error}
        if details:
            error_data.update(details)
        await self.update_progress(self.progress, "failed", error_data)
