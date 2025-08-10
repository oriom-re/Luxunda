"""
Authentication and Session Management System for LuxOS
"""

import asyncio
import hashlib
import secrets
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import ulid

from .session_assistant import SessionManager, session_manager
from .access_control import access_controller, AccessLevel
from ..models.being import Being
from ..models.soul import Soul
from ..models.event import Event
from ..models.relationship import Relationship
from database.postgre_db import Postgre_db

class AuthenticationManager:
    """
    Zarządza autoryzacją użytkowników i sesjami Lux
    """

    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.user_credentials: Dict[str, Dict[str, Any]] = {}
        self.session_connections: Dict[str, str] = {}  # session_id -> connection_ulid
        self.is_initialized = False

    async def initialize(self):
        """Inicjalizuje system autoryzacji"""
        # Utwórz domyślnego administratora
        await self.create_user(
            username="admin",
            password="luxos2025",
            role="admin",
            permissions=["full_access", "user_management", "system_control"]
        )

        print("🔐 Authentication Manager initialized")
        self.is_initialized = True
        return True

    def hash_password(self, password: str) -> str:
        """Hashuje hasło z solą"""
        salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        """Weryfikuje hasło"""
        try:
            salt, hash_part = password_hash.split(':')
            password_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_check.hex() == hash_part
        except:
            return False

    async def create_user(self, username: str, password: str, role: str = "user", permissions: List[str] = None) -> Dict[str, Any]:
        """Tworzy nowego użytkownika"""
        if username in self.user_credentials:
            raise ValueError(f"User {username} already exists")

        user_data = {
            "username": username,
            "password_hash": self.hash_password(password),
            "role": role,
            "permissions": permissions or ["basic_access"],
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "active": True
        }

        self.user_credentials[username] = user_data

        # Utwórz Being dla użytkownika
        user_genotype = {
            "genesis": {
                "name": f"user_{username}",
                "type": "system_user",
                "version": "1.0.0",
                "description": f"System user: {username}"
            },
            "attributes": {
                "username": {"py_type": "str"},
                "role": {"py_type": "str"},
                "permissions": {"py_type": "List[str]"},
                "session_count": {"py_type": "int"},
                "last_activity": {"py_type": "str"}
            }
        }

        soul = await Soul.create(user_genotype, alias=f"user_soul_{username}")
        user_being = await Being.create(
            soul,
            {
                "username": username,
                "role": role,
                "permissions": permissions,
                "session_count": 0,
                "last_activity": datetime.now().isoformat()
            },
            alias=f"user_{username}"
        )

        user_data["user_ulid"] = user_being.ulid

        print(f"👤 Created user: {username} ({role})")
        return {"username": username, "user_ulid": user_being.ulid, "created": True}

    async def authenticate_user(self, username: str, password: str, fingerprint: str) -> Optional[Dict[str, Any]]:
        """Autoryzuje użytkownika i tworzy sesję"""
        if username not in self.user_credentials:
            return None

        user_data = self.user_credentials[username]
        if not user_data["active"] or not self.verify_password(password, user_data["password_hash"]):
            return None

        # Utwórz sesję
        session_id = str(ulid.ulid())
        session_token = secrets.token_urlsafe(32)

        # Utwórz Connection Being dla tej sesji
        connection_being = await self.create_connection_being(session_id, user_data["user_ulid"], fingerprint)

        session_data = {
            "session_id": session_id,
            "session_token": session_token,
            "username": username,
            "user_ulid": user_data["user_ulid"],
            "connection_ulid": connection_being.ulid,
            "fingerprint": fingerprint,
            "role": user_data["role"],
            "permissions": user_data["permissions"],
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "status": "active"
        }

        self.active_sessions[session_id] = session_data
        self.session_connections[session_id] = connection_being.ulid

        # Aktualizuj dane użytkownika
        user_data["last_login"] = datetime.now().isoformat()
        user_data["session_count"] = user_data.get("session_count", 0) + 1

        # Utwórz Lux Assistant dla sesji
        lux_assistant = await session_manager.create_session(
            user_fingerprint=fingerprint,
            user_ulid=user_data["user_ulid"],
            ttl_minutes=1440  # 24 godziny
        )

        session_data["lux_assistant_id"] = lux_assistant.session.session_id

        # Utwórz event logowania
        await Event.create_event(
            "user_login",
            {
                "username": username,
                "session_id": session_id,
                "fingerprint": fingerprint,
                "user_ulid": user_data["user_ulid"],
                "connection_ulid": connection_being.ulid
            }
        )

        print(f"🔓 User authenticated: {username} (session: {session_id[:8]}...)")
        return session_data

    async def create_connection_being(self, session_id: str, user_ulid: str, fingerprint: str) -> Being:
        """Tworzy Being reprezentujący połączenie użytkownika"""
        connection_genotype = {
            "genesis": {
                "name": f"connection_{session_id}",
                "type": "user_connection",
                "version": "1.0.0",
                "description": f"User connection for session {session_id}"
            },
            "attributes": {
                "session_id": {"py_type": "str"},
                "user_ulid": {"py_type": "str"},
                "fingerprint": {"py_type": "str"},
                "status": {"py_type": "str"},
                "last_heartbeat": {"py_type": "str"},
                "events_count": {"py_type": "int"},
                "ttl_expires": {"py_type": "str"}
            }
        }

        soul = await Soul.create(connection_genotype, alias=f"connection_soul_{session_id}")
        connection_being = await Being.create(
            soul,
            {
                "session_id": session_id,
                "user_ulid": user_ulid,
                "fingerprint": fingerprint,
                "status": "connected",
                "last_heartbeat": datetime.now().isoformat(),
                "events_count": 0,
                "ttl_expires": (datetime.now() + timedelta(hours=24)).isoformat()
            },
            alias=f"connection_{session_id}"
        )

        # Utwórz relację connection -> user
        await Relationship.create(
            source_ulid=connection_being.ulid,
            target_ulid=user_ulid,
            relation_type="belongs_to_user",
            strength=1.0,
            metadata={
                "session_id": session_id,
                "connection_type": "user_session"
            }
        )

        return connection_being

    async def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Waliduje sesję użytkownika"""
        for session_id, session_data in self.active_sessions.items():
            if session_data.get("session_token") == session_token:
                # Sprawdź czy nie wygasła
                expires_at = datetime.fromisoformat(session_data["expires_at"])
                if datetime.now() > expires_at:
                    await self.invalidate_session(session_id)
                    return None

                # Zaktualizuj ostatnią aktywność
                session_data["last_activity"] = datetime.now().isoformat()

                # Zaktualizuj heartbeat Connection Being
                await self.update_connection_heartbeat(session_data["connection_ulid"])

                return session_data

        return None

    async def update_connection_heartbeat(self, connection_ulid: str):
        """Aktualizuje heartbeat połączenia"""
        try:
            # Utwórz event heartbeat
            await Event.create_event(
                "connection_heartbeat",
                {
                    "connection_ulid": connection_ulid,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"❌ Error updating heartbeat: {e}")

    async def invalidate_session(self, session_id: str):
        """Unieważnia sesję"""
        if session_id not in self.active_sessions:
            return

        session_data = self.active_sessions[session_id]

        # Utwórz event wylogowania
        await Event.create_event(
            "user_logout",
            {
                "session_id": session_id,
                "username": session_data.get("username"),
                "user_ulid": session_data.get("user_ulid"),
                "connection_ulid": session_data.get("connection_ulid")
            }
        )

        # Usuń z aktywnych sesji
        del self.active_sessions[session_id]
        if session_id in self.session_connections:
            del self.session_connections[session_id]

        print(f"🔒 Session invalidated: {session_id[:8]}...")

    async def get_user_events(self, user_ulid: str, limit: int = 50) -> List[Event]:
        """Pobiera eventy użytkownika"""
        all_events = await Event.get_all()
        user_events = []

        for event in all_events:
            payload = getattr(event, 'payload', {})
            if payload.get('user_ulid') == user_ulid:
                user_events.append(event)

        # Sortuj po czasie utworzenia
        user_events.sort(key=lambda e: getattr(e, 'created_at', ''), reverse=True)

        return user_events[:limit]

    async def get_accessible_beings(self, user_ulid: str) -> List[Being]:
        """Pobiera wszystkie byty dostępne dla użytkownika"""
        if user_ulid not in self.user_credentials:
            return []

        # Znajdź sesję użytkownika
        user_session = None
        for session_data in self.active_sessions.values():
            if session_data.get("user_ulid") == user_ulid:
                user_session = session_data
                break

        # Pobierz wszystkie byty z kontrolą dostępu
        return await Being.get_all(user_ulid, user_session)

    async def create_secured_being(self, user_ulid: str, soul, data: Dict[str, Any],
                                  access_level: str = "authenticated",
                                  alias: str = None, ttl_hours: int = None) -> Being:
        """Tworzy nowy byt z odpowiednimi uprawnieniami"""
        if user_ulid not in self.user_credentials:
            raise PermissionError("User not found")

        user_data = self.user_credentials[user_ulid]
        user_role = user_data.get("role", "user")

        # Sprawdź uprawnienia do tworzenia w różnych strefach
        if access_level == "sensitive" and user_role not in ["admin", "super_admin"]:
            # Użytkownik może tworzyć w strefie sensitive tylko jeśli ma odpowiednie uprawnienia
            permissions = user_data.get("permissions", [])
            if "create_sensitive" not in permissions:
                access_level = "authenticated"  # Przełącz na authenticated

        # Znajdź odpowiednią strefę
        zone_mapping = {
            "public": "public_zone",
            "authenticated": "authenticated_zone",
            "sensitive": "sensitive_zone"
        }
        access_zone = zone_mapping.get(access_level, "authenticated_zone")

        # Utwórz byt
        being = await Being.create(
            soul=soul,
            data=data,
            alias=alias,
            access_zone=access_zone,
            ttl_hours=ttl_hours
        )

        # Przypisz użytkownika jako właściciela dla niepublicznych bytów
        if access_level != "public":
            zone = access_controller.zones.get(access_zone)
            if zone:
                zone.grant_user_access(user_ulid)

        # Utwórz event tworzenia
        await Event.create_event(
            "being_created",
            {
                "being_ulid": being.ulid,
                "creator_ulid": user_ulid,
                "access_zone": access_zone,
                "access_level": access_level
            }
        )

        print(f"🔐 Created secured being: {being.ulid[:8]}... in zone: {access_zone}")
        return being

    def get_user_access_summary(self, user_ulid: str) -> Dict[str, Any]:
        """Zwraca podsumowanie dostępów użytkownika"""
        if user_ulid not in self.user_credentials:
            return {"error": "User not found"}

        # Znajdź sesję użytkownika
        user_session = None
        for session_data in self.active_sessions.values():
            if session_data.get("user_ulid") == user_ulid:
                user_session = session_data
                break

        return access_controller.get_access_summary(user_ulid, user_session)

# Globalna instancja
auth_manager = AuthenticationManager()