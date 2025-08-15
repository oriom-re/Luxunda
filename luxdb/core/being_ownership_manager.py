"""
Being Ownership Manager - Inteligentne zarządzanie dostępem do zasobów

Każdy Being może być "masterem" swoich zasobów i kontrolować dostęp innych bytów.
To eliminuje konflikty na poziomie architektury - Bank-Being kontroluje swoje zasoby bankowe.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

class BeingOwnershipManager:
    """
    Manager zarządzający własnością i dostępem do zasobów przez byty.

    Kluczowe koncepcje:
    - Being może być masterem określonych zasobów
    - Inne byty muszą prosić o dostęp
    - Automatyczne rozwiązywanie konfliktów
    - Thread-safe operations
    """

    def __init__(self):
        # Mapa: zasób_id -> being_master_ulid
        self.resource_owners: Dict[str, str] = {}

        # Mapa: being_ulid -> lista zasobów które kontroluje
        self.being_resources: Dict[str, List[str]] = {}

        # Mapa: zasób_id -> lista being_ulid oczekujących dostępu
        self.access_queue: Dict[str, List[str]] = {}

        # Aktywne sesje dostępu: zasób_id -> Dict[being_ulid, session_info]
        self.active_sessions: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Locks dla thread safety
        self._locks: Dict[str, asyncio.Lock] = {}

    async def register_being_as_resource_master(self, being_ulid: str, resource_id: str, 
                                               resource_type: str = "general") -> Dict[str, Any]:
        """
        Rejestruje Being jako mastera określonego zasobu.

        Args:
            being_ulid: ULID bytu który stanie się masterem
            resource_id: ID zasobu do kontrolowania
            resource_type: Typ zasobu (bank, data, compute, etc.)

        Returns:
            Wynik rejestracji
        """
        try:
            # Sprawdź czy zasób już ma mastera
            if resource_id in self.resource_owners:
                current_master = self.resource_owners[resource_id]
                return {
                    "success": False,
                    "error": f"Resource {resource_id} already owned by {current_master}",
                    "current_master": current_master
                }

            # Zarejestruj mastera
            self.resource_owners[resource_id] = being_ulid

            # Dodaj zasób do listy zasobów tego bytu
            if being_ulid not in self.being_resources:
                self.being_resources[being_ulid] = []
            self.being_resources[being_ulid].append(resource_id)

            # Utwórz lock dla tego zasobu
            self._locks[resource_id] = asyncio.Lock()

            print(f"🏛️ Being {being_ulid} is now master of resource {resource_id} ({resource_type})")

            return {
                "success": True,
                "resource_id": resource_id,
                "master_being": being_ulid,
                "resource_type": resource_type,
                "registered_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Registration failed: {str(e)}"
            }

    async def request_resource_access(self, requesting_being_ulid: str, resource_id: str,
                                    access_type: str = "read", duration_minutes: int = 60) -> Dict[str, Any]:
        """
        Being prosi o dostęp do zasobu kontrolowanego przez innego bytu.

        Args:
            requesting_being_ulid: ULID bytu prosząco o dostęp
            resource_id: ID zasobu
            access_type: Typ dostępu (read, write, exclusive)
            duration_minutes: Maksymalny czas dostępu w minutach

        Returns:
            Wynik żądania dostępu
        """
        try:
            # Sprawdź czy zasób ma mastera
            if resource_id not in self.resource_owners:
                return {
                    "success": False,
                    "error": f"Resource {resource_id} has no registered master"
                }

            master_being = self.resource_owners[resource_id]

            # Jeśli to ten sam byt - automatyczny dostęp
            if requesting_being_ulid == master_being:
                return await self._grant_access(requesting_being_ulid, resource_id, access_type, 
                                              duration_minutes, auto_granted=True)

            # Sprawdź czy można udzielić dostępu
            can_grant = await self._can_grant_access(resource_id, access_type)

            if can_grant:
                return await self._grant_access(requesting_being_ulid, resource_id, access_type, duration_minutes)
            else:
                # Dodaj do kolejki oczekujących
                if resource_id not in self.access_queue:
                    self.access_queue[resource_id] = []

                if requesting_being_ulid not in self.access_queue[resource_id]:
                    self.access_queue[resource_id].append(requesting_being_ulid)

                return {
                    "success": False,
                    "status": "queued",
                    "message": f"Access request queued. Position: {len(self.access_queue[resource_id])}",
                    "master_being": master_being,
                    "queue_position": len(self.access_queue[resource_id])
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Access request failed: {str(e)}"
            }

    async def _can_grant_access(self, resource_id: str, access_type: str) -> bool:
        """Sprawdza czy można udzielić dostępu do zasobu"""
        if resource_id not in self.active_sessions:
            return True

        current_sessions = self.active_sessions[resource_id]

        # Sprawdź typy dostępu
        if access_type == "exclusive":
            return len(current_sessions) == 0

        if access_type == "write":
            # Write nie może współistnieć z innymi
            return len(current_sessions) == 0

        if access_type == "read":
            # Read może współistnieć tylko z innymi read
            return all(session["access_type"] == "read" for session in current_sessions.values())

        return False

    async def _grant_access(self, being_ulid: str, resource_id: str, access_type: str,
                          duration_minutes: int, auto_granted: bool = False) -> Dict[str, Any]:
        """Udziela dostępu do zasobu"""
        try:
            # Użyj lock dla thread safety
            async with self._locks.get(resource_id, asyncio.Lock()):
                session_id = f"{being_ulid}_{resource_id}_{datetime.now().timestamp()}"

                session_info = {
                    "session_id": session_id,
                    "being_ulid": being_ulid,
                    "access_type": access_type,
                    "granted_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + timedelta(minutes=duration_minutes)).isoformat(),
                    "auto_granted": auto_granted
                }

                # Dodaj sesję
                if resource_id not in self.active_sessions:
                    self.active_sessions[resource_id] = {}

                self.active_sessions[resource_id][being_ulid] = session_info

                print(f"🔑 Access granted: Being {being_ulid} -> Resource {resource_id} ({access_type})")

                return {
                    "success": True,
                    "session_id": session_id,
                    "access_granted": True,
                    "access_type": access_type,
                    "duration_minutes": duration_minutes,
                    "session_info": session_info
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to grant access: {str(e)}"
            }

    async def release_resource_access(self, being_ulid: str, resource_id: str) -> Dict[str, Any]:
        """Being zwalnia dostęp do zasobu"""
        try:
            if (resource_id in self.active_sessions and 
                being_ulid in self.active_sessions[resource_id]):

                # Usuń sesję
                session_info = self.active_sessions[resource_id].pop(being_ulid)

                # Jeśli nie ma więcej sesji, usuń zasób z aktywnych
                if not self.active_sessions[resource_id]:
                    del self.active_sessions[resource_id]

                print(f"🔓 Access released: Being {being_ulid} -> Resource {resource_id}")

                # Sprawdź kolejkę oczekujących
                await self._process_access_queue(resource_id)

                return {
                    "success": True,
                    "released_session": session_info,
                    "message": "Access released successfully"
                }
            else:
                return {
                    "success": False,
                    "error": "No active session found for this being and resource"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to release access: {str(e)}"
            }

    async def _process_access_queue(self, resource_id: str):
        """Przetwarza kolejkę oczekujących na dostęp"""
        if resource_id not in self.access_queue or not self.access_queue[resource_id]:
            return

        # Sprawdź czy można udzielić dostępu następnemu w kolejce
        next_being = self.access_queue[resource_id][0]

        # Dla uproszczenia - standardowy dostęp read na 60 minut
        result = await self.request_resource_access(next_being, resource_id, "read", 60)

        if result.get("success"):
            # Usuń z kolejki
            self.access_queue[resource_id].pop(0)
            print(f"📋 Processed queue: Being {next_being} granted access to {resource_id}")

    def get_being_owned_resources(self, being_ulid: str) -> List[str]:
        """Zwraca listę zasobów kontrolowanych przez byt"""
        return self.being_resources.get(being_ulid, [])

    def get_resource_master(self, resource_id: str) -> Optional[str]:
        """Zwraca ULID mastera zasobu"""
        return self.resource_owners.get(resource_id)

    def get_active_sessions_for_resource(self, resource_id: str) -> Dict[str, Dict[str, Any]]:
        """Zwraca aktywne sesje dla zasobu"""
        return self.active_sessions.get(resource_id, {})

    def get_system_status(self) -> Dict[str, Any]:
        """Zwraca status całego systemu zarządzania własnością"""
        return {
            "total_resources": len(self.resource_owners),
            "total_masters": len(set(self.resource_owners.values())),
            "active_sessions_count": sum(len(sessions) for sessions in self.active_sessions.values()),
            "queued_requests": sum(len(queue) for queue in self.access_queue.values()),
            "resources_by_master": self.being_resources,
            "current_timestamp": datetime.now().isoformat()
        }

# Globalny manager
being_ownership_manager = BeingOwnershipManager()