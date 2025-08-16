"""
Session Data Manager - Zarządza danymi w kontekście sesji

UWAGA: W LuxOS z Kernel jako Being, ten manager może być zastąpiony
przez bezpośrednią komunikację Being → Kernel → Being.
Każdy Lux Being może mieć własne dane zarządzane przez Kernel Being.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import ulid

class SessionDataManager:
    """
    Zarządza danymi w ramach sesji użytkownika
    Zapewnia izolację i spójność danych - OPTIMIZED VERSION
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.local_cache: Dict[str, Any] = {}
        self.dirty_flags: Dict[str, bool] = {}
        self.access_lock = asyncio.Lock()
        self.last_sync = datetime.now()

        # Performance optimizations
        self.batch_size = 10
        self.sync_interval = 30  # seconds
        self.cache_hits = 0
        self.cache_misses = 0
        self.read_only_cache = {}  # Shared read-only data

        # Task queue system for beings
        self.being_task_queues: Dict[str, asyncio.Queue] = {}
        self.being_workers: Dict[str, asyncio.Task] = {}
        self.queue_stats: Dict[str, Dict[str, int]] = {}

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
        """Synchronizuje zmiany z bazą danych - BATCH OPTIMIZED"""
        async with self.access_lock:
            dirty_beings = []

            # Collect dirty beings
            for cache_key, is_dirty in self.dirty_flags.items():
                if is_dirty and cache_key in self.local_cache:
                    dirty_beings.append(self.local_cache[cache_key])

            # Batch save (up to batch_size at once)
            for i in range(0, len(dirty_beings), self.batch_size):
                batch = dirty_beings[i:i + self.batch_size]

                # Parallel save operations
                save_tasks = [being.save() for being in batch]
                await asyncio.gather(*save_tasks, return_exceptions=True)

                # Mark as clean
                for being in batch:
                    cache_key = f"being_{being.ulid}"
                    self.dirty_flags[cache_key] = False

            self.last_sync = datetime.now()

    async def fast_get_being(self, ulid: str):
        """Fast read without lock for read-only operations"""
        cache_key = f"being_{ulid}"

        # Quick cache hit
        if cache_key in self.local_cache:
            self.cache_hits += 1
            return self.local_cache[cache_key]

        # Check shared read-only cache
        if cache_key in self.read_only_cache:
            self.cache_hits += 1
            return self.read_only_cache[cache_key]

        self.cache_misses += 1
        return None

    def get_session_summary(self) -> Dict[str, Any]:
        """Zwraca podsumowanie stanu sesji"""
        total_queued = sum(stats["queued"] for stats in self.queue_stats.values())
        total_processed = sum(stats["processed"] for stats in self.queue_stats.values())
        total_failed = sum(stats["failed"] for stats in self.queue_stats.values())

        return {
            "session_id": self.session_id,
            "cached_objects": len(self.local_cache),
            "dirty_objects": sum(1 for dirty in self.dirty_flags.values() if dirty),
            "last_sync": self.last_sync.isoformat(),
            "cache_performance": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_ratio": self.cache_hits / max(1, self.cache_hits + self.cache_misses)
            },
            "task_queues": {
                "active_beings": len(self.being_task_queues),
                "total_queued": total_queued,
                "total_processed": total_processed,
                "total_failed": total_failed,
                "success_rate": total_processed / max(1, total_processed + total_failed)
            }
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
        """Cleanup session and associated data"""
        if session_id in self.active_sessions:
            session_data = self.active_sessions[session_id]

            # Cleanup Lux Being if exists
            if 'lux_being_ulid' in session_data:
                # Being cleanup would be handled by Being ownership manager
                pass

            # Remove from active sessions
            del self.active_sessions[session_id]
            print(f"🗑️ Session {session_id[:8]} cleaned up")

    async def enqueue_being_task(self, being_ulid: str, task: Dict[str, Any]) -> bool:
        """
        Dodaje zadanie do kolejki Being - WRITE-SAFE
        Tylko właściciel Being może zapisywać
        """
        async with self.access_lock:
            # Sprawdź czy Being należy do tej sesji
            cache_key = f"being_{being_ulid}"
            if cache_key not in self.local_cache:
                return False  # Being nie należy do tej sesji

            # Utwórz kolejkę jeśli nie istnieje
            if being_ulid not in self.being_task_queues:
                self.being_task_queues[being_ulid] = asyncio.Queue(maxsize=100)
                self.queue_stats[being_ulid] = {
                    "queued": 0, "processed": 0, "failed": 0
                }

                # Uruchom worker dla tego Being
                self.being_workers[being_ulid] = asyncio.create_task(
                    self._being_task_worker(being_ulid)
                )

            # Dodaj zadanie do kolejki
            try:
                await self.being_task_queues[being_ulid].put(task)
                self.queue_stats[being_ulid]["queued"] += 1
                return True
            except asyncio.QueueFull:
                return False  # Kolejka pełna

    async def _being_task_worker(self, being_ulid: str):
        """
        Worker obsługujący kolejkę zadań dla konkretnego Being
        SYNCHRONICZNE przetwarzanie - brak konfliktów
        """
        queue = self.being_task_queues[being_ulid]
        stats = self.queue_stats[being_ulid]

        while True:
            try:
                # Pobierz zadanie z kolejki (czeka jeśli pusta)
                task = await queue.get()

                # Pobierz Being z cache
                cache_key = f"being_{being_ulid}"
                being = self.local_cache.get(cache_key)

                if not being:
                    stats["failed"] += 1
                    continue

                # SYNCHRONICZNE wykonanie zadania
                result = await self._execute_being_task(being, task)

                if result.get("success"):
                    stats["processed"] += 1
                    # Oznacz jako dirty do synchronizacji
                    self.dirty_flags[cache_key] = True
                else:
                    stats["failed"] += 1

                # Oznacz zadanie jako zakończone
                queue.task_done()

            except Exception as e:
                stats["failed"] += 1
                print(f"Task worker error for {being_ulid}: {e}")

    async def _execute_being_task(self, being, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Wykonuje zadanie na Being - THREAD-SAFE
        """
        try:
            task_type = task.get("type")
            task_data = task.get("data", {})

            # Różne typy zadań
            if task_type == "execute_function":
                return await being.execute_soul_function(
                    task_data.get("function_name"),
                    **task_data.get("kwargs", {})
                )

            elif task_type == "update_data":
                being.data.update(task_data)
                being.updated_at = datetime.now()
                return {"success": True, "message": "Data updated"}

            elif task_type == "add_dynamic_function":
                return await being.add_dynamic_function(
                    task_data.get("function_name"),
                    task_data.get("function_definition"),
                    task_data.get("source", "task_queue")
                )

            else:
                return {"success": False, "error": f"Unknown task type: {task_type}"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_queue_status(self, being_ulid: str) -> Dict[str, Any]:
        """Status kolejki dla Being"""
        if being_ulid not in self.queue_stats:
            return {"error": "No queue for this being"}

        queue = self.being_task_queues.get(being_ulid)
        return {
            "queue_size": queue.qsize() if queue else 0,
            "stats": self.queue_stats[being_ulid],
            "worker_active": being_ulid in self.being_workers
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Status wszystkich sesji"""
        return {
            "active_sessions": len(self.active_sessions),
            "sessions": {
                sid: manager.get_session_summary() 
                for sid, manager in self.active_sessions.items()
            }
        }

    async def build_conversation_context(self, session_id: str, message: str) -> Dict[str, Any]:
        """Build conversation context for AI processing"""
        session_manager = self.active_sessions.get(session_id)
        
        if not session_manager:
            return {
                "session_id": session_id,
                "message": message,
                "user_context": {},
                "conversation_history": [],
                "timestamp": datetime.now().isoformat(),
                "system_status": "no_session"
            }

        return {
            "session_id": session_id,
            "message": message,
            "user_context": getattr(session_manager, 'user_context', {}),
            "conversation_history": getattr(session_manager, 'conversation_history', []),
            "cached_objects": len(session_manager.local_cache),
            "cache_performance": {
                "hits": session_manager.cache_hits,
                "misses": session_manager.cache_misses,
                "hit_ratio": session_manager.cache_hits / max(1, session_manager.cache_hits + session_manager.cache_misses)
            },
            "timestamp": datetime.now().isoformat(),
            "system_status": "active"
        }

class SessionManager:
    """
    Główny manager sesji - pojedyncza instancja dla całego systemu
    """

    def __init__(self):
        self.registry = GlobalSessionRegistry()
        self.is_initialized = False

    async def initialize(self):
        """Inicjalizuje system sesji"""
        self.is_initialized = True
        print("🎯 Session Manager initialized")
        return True

    async def create_session(self, user_fingerprint: str, user_ulid: str = None, ttl_minutes: int = 30):
        """Tworzy nową sesję"""
        return await self.registry.get_session_manager(user_fingerprint)

    async def get_session(self, session_id: str):
        """Pobiera sesję"""
        return await self.registry.get_session_manager(session_id)

    async def cleanup_session(self, session_id: str):
        """Czyści sesję"""
        await self.registry.cleanup_session(session_id)

# Globalne instancje
global_session_registry = GlobalSessionRegistry()
session_manager = SessionManager()