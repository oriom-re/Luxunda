
"""
Database Event Listener System
"""

import asyncio
import json
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime

from ..models.being import Being
from ..models.soul import Soul
from ..models.relationship import Relationship
from ..repository.soul_repository import SoulRepository

class DatabaseEventListener:
    """
    System listenerów bazodanowych - śledzi zmiany w relacjach
    """
    
    def __init__(self, listener_name: str):
        self.listener_name = listener_name
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.is_listening = False
        self.listener_being: Optional[Being] = None
        
    async def initialize(self):
        """
        Inicjalizuje listener jako Being w systemie
        """
        # Genotype dla Listener
        listener_genotype = {
            "genesis": {
                "name": f"listener_{self.listener_name}",
                "type": "event_listener",
                "version": "1.0.0",
                "description": f"Database event listener: {self.listener_name}"
            },
            "properties": {
                "subscribed_events": list(self.subscriptions.keys()),
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
        }
        
        # Utwórz Soul i Being dla Listener
        soul = await Soul.create(
            genotype=listener_genotype,
            alias=f"listener_soul_{self.listener_name}"
        )
        
        self.listener_being = await Being.create(
            soul=soul,
            alias=f"listener_{self.listener_name}"
        )
        
        print(f"🎧 Listener {self.listener_name} initialized as Being: {self.listener_being.ulid}")
    
    def subscribe(self, event_type: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Subskrybuje określony typ eventów
        """
        if event_type not in self.subscriptions:
            self.subscriptions[event_type] = []
        self.subscriptions[event_type].append(callback)
        
        print(f"📡 {self.listener_name} subscribed to: {event_type}")
    
    async def start_listening(self, poll_interval: float = 1.0):
        """
        Rozpoczyna nasłuchiwanie zmian w bazie danych
        """
        if not self.listener_being:
            await self.initialize()
            
        self.is_listening = True
        print(f"👂 {self.listener_name} started listening...")
        
        while self.is_listening:
            try:
                await self._check_for_new_notifications()
                await asyncio.sleep(poll_interval)
            except Exception as e:
                print(f"❌ Listener error: {e}")
                await asyncio.sleep(poll_interval)
    
    async def _check_for_new_notifications(self):
        """
        Sprawdza nowe notyfikacje w relacjach
        """
        # Znajdź nowe relacje typu "notifies" wskazujące na tego listenera
        new_notifications = await Relationship.get_by_being(self.listener_being.ulid)
        
        for relationship in new_notifications:
            if (relationship.relation_type == "notifies" and 
                relationship.target_ulid == self.listener_being.ulid):
                
                event_type = relationship.metadata.get("event_type")
                
                if event_type in self.subscriptions:
                    # Wywołaj callback dla tego typu eventów
                    for callback in self.subscriptions[event_type]:
                        try:
                            await self._execute_callback(callback, relationship.metadata)
                        except Exception as e:
                            print(f"❌ Callback error for {event_type}: {e}")
                    
                    # Oznacz relację jako przetworzoną
                    relationship.metadata["processed"] = True
                    relationship.metadata["processed_at"] = datetime.now().isoformat()
                    # Tutaj byłaby aktualizacja relacji w bazie
    
    async def _execute_callback(self, callback: Callable, event_data: Dict[str, Any]):
        """
        Wykonuje callback - obsługuje zarówno sync jak i async funkcje
        """
        if asyncio.iscoroutinefunction(callback):
            await callback(event_data)
        else:
            callback(event_data)
    
    def stop_listening(self):
        """
        Zatrzymuje nasłuchiwanie
        """
        self.is_listening = False
        print(f"🛑 {self.listener_name} stopped listening")

class EventBus:
    """
    Główna magistrala eventów - zarządza listenerami i eventami
    """
    
    def __init__(self):
        self.listeners: List[DatabaseEventListener] = []
        
    async def create_listener(self, name: str) -> DatabaseEventListener:
        """
        Tworzy nowy listener
        """
        listener = DatabaseEventListener(name)
        await listener.initialize()
        self.listeners.append(listener)
        return listener
    
    async def emit_event(self, event_type: str, payload: Dict[str, Any], target_modules: List[str] = None):
        """
        Emituje nowe zdarzenie do systemu
        """
        from ..models.event import Event
        
        event = await Event.create_event(
            event_type=event_type,
            payload=payload,
            target_modules=target_modules
        )
        
        print(f"📤 Event emitted: {event_type} ({event.ulid})")
        return event
    
    async def start_all_listeners(self):
        """
        Uruchamia wszystkich listenerów
        """
        tasks = []
        for listener in self.listeners:
            task = asyncio.create_task(listener.start_listening())
            tasks.append(task)
        
        print(f"🚀 Started {len(tasks)} listeners")
        await asyncio.gather(*tasks, return_exceptions=True)

# Globalna instancja
event_bus = EventBus()
