
"""
Session Data Manager - Zarządza danymi w kontekście sesji
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import ulid

class SessionDataManager:
    """
    Zarządza danymi w ramach sesji użytkownika
    Zapewnia izolację i spójność danych
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.local_cache: Dict[str, Any] = {}
        self.dirty_flags: Dict[str, bool] = {}
        self.access_lock = asyncio.Lock()
        self.last_sync = datetime.now()
    
    async def get_being_safe(self, ulid: str):
        """Bezpieczne pobranie Being z kontrolą współbieżności"""
        async with self.access_lock:
            # Sprawdź cache sesji
            cache_key = f"being_{ulid}"
            if cache_key in self.local_cache:
                return self.local_cache[cache_key]
            
            # Pobierz z bazy
            from ..models.being import Being
            being = await Being.get_by_ulid(ulid)
            
            if being:
                # Oznacz jako należący do sesji
                being_data = being.data.copy()
                being_data['_accessed_by_session'] = self.session_id
                being_data['_access_time'] = datetime.now().isoformat()
                
                # Cache w sesji
                self.local_cache[cache_key] = being
                self.dirty_flags[cache_key] = False
                
            return being
    
    async def create_being_safe(self, soul, data: Dict[str, Any], alias: str = None):
        """Bezpieczne tworzenie Being w kontekście sesji"""
        async with self.access_lock:
            from ..models.being import Being
            
            # Dodaj metadane sesji
            session_data = data.copy()
            session_data.update({
                '_session_id': self.session_id,
                '_created_in_session': True,
                '_creation_time': datetime.now().isoformat()
            })
            
            # Utwórz Being
            being = await Being.create(soul, session_data, alias)
            
            # Cache w sesji
            cache_key = f"being_{being.ulid}"
            self.local_cache[cache_key] = being
            self.dirty_flags[cache_key] = True  # Nowo utworzony
            
            return being
    
    async def sync_changes(self):
        """Synchronizuje zmiany z bazą danych"""
        async with self.access_lock:
            for cache_key, is_dirty in self.dirty_flags.items():
                if is_dirty and cache_key in self.local_cache:
                    being = self.local_cache[cache_key]
                    await being.save()
                    self.dirty_flags[cache_key] = False
            
            self.last_sync = datetime.now()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Zwraca podsumowanie stanu sesji"""
        return {
            "session_id": self.session_id,
            "cached_objects": len(self.local_cache),
            "dirty_objects": sum(1 for dirty in self.dirty_flags.values() if dirty),
            "last_sync": self.last_sync.isoformat()
        }

class GlobalSessionRegistry:
    """
    Globalny rejestr sesji dla koordynacji
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, SessionDataManager] = {}
        self.global_lock = asyncio.Lock()
    
    async def get_session_manager(self, session_id: str) -> SessionDataManager:
        """Pobiera lub tworzy manager dla sesji"""
        async with self.global_lock:
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = SessionDataManager(session_id)
            return self.active_sessions[session_id]
    
    async def cleanup_session(self, session_id: str):
        """Czyści dane sesji"""
        async with self.global_lock:
            if session_id in self.active_sessions:
                # Synchronizuj przed usunięciem
                await self.active_sessions[session_id].sync_changes()
                del self.active_sessions[session_id]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Status wszystkich sesji"""
        return {
            "active_sessions": len(self.active_sessions),
            "sessions": {
                sid: manager.get_session_summary() 
                for sid, manager in self.active_sessions.items()
            }
        }

# Globalna instancja
global_session_registry = GlobalSessionRegistry()
