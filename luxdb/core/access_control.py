
"""
Access Control System - Zarządzanie strefami dostępu dla LuxOS
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import ulid

class AccessLevel(Enum):
    """Poziomy dostępu do bytów"""
    PUBLIC = "public"           # Dostępne dla wszystkich
    AUTHENTICATED = "authenticated"  # Wymagane zalogowanie
    SENSITIVE = "sensitive"     # Specjalne uprawnienia

class AccessZone:
    """Strefa dostępu z regułami bezpieczeństwa"""
    
    def __init__(self, zone_id: str, access_level: AccessLevel, 
                 description: str = "", metadata: Dict[str, Any] = None):
        self.zone_id = zone_id
        self.access_level = access_level
        self.description = description
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.access_rules: List[Dict[str, Any]] = []
        self.allowed_users: Set[str] = set()
        self.denied_users: Set[str] = set()
    
    def add_access_rule(self, rule_type: str, rule_data: Dict[str, Any]):
        """Dodaje regułę dostępu do strefy"""
        rule = {
            "rule_id": str(ulid.ulid()),
            "rule_type": rule_type,
            "rule_data": rule_data,
            "created_at": datetime.now().isoformat()
        }
        self.access_rules.append(rule)
    
    def grant_user_access(self, user_ulid: str):
        """Przyznaje dostęp konkretnemu użytkownikowi"""
        self.allowed_users.add(user_ulid)
        self.denied_users.discard(user_ulid)
    
    def deny_user_access(self, user_ulid: str):
        """Odmawia dostępu konkretnemu użytkownikowi"""
        self.denied_users.add(user_ulid)
        self.allowed_users.discard(user_ulid)
    
    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje strefę do słownika"""
        return {
            "zone_id": self.zone_id,
            "access_level": self.access_level.value,
            "description": self.description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "access_rules": self.access_rules,
            "allowed_users": list(self.allowed_users),
            "denied_users": list(self.denied_users)
        }

class AccessController:
    """Kontroler dostępu dla całego systemu"""
    
    def __init__(self):
        self.zones: Dict[str, AccessZone] = {}
        self.being_zones: Dict[str, str] = {}  # being_ulid -> zone_id
        self.initialize_default_zones()
    
    def initialize_default_zones(self):
        """Inicjalizuje domyślne strefy dostępu"""
        # Strefa publiczna
        public_zone = AccessZone(
            "public_zone",
            AccessLevel.PUBLIC,
            "Publicznie dostępne byty - bez wymagań autoryzacji"
        )
        
        # Strefa dla zalogowanych
        auth_zone = AccessZone(
            "authenticated_zone", 
            AccessLevel.AUTHENTICATED,
            "Byty dostępne po zalogowaniu"
        )
        
        # Strefa wrażliwa
        sensitive_zone = AccessZone(
            "sensitive_zone",
            AccessLevel.SENSITIVE,
            "Wrażliwe byty - specjalne uprawnienia"
        )
        
        self.zones["public_zone"] = public_zone
        self.zones["authenticated_zone"] = auth_zone
        self.zones["sensitive_zone"] = sensitive_zone
        
        print("🛡️ Access Control System initialized with default zones")
    
    def create_zone(self, zone_id: str, access_level: AccessLevel, 
                   description: str = "", metadata: Dict[str, Any] = None) -> AccessZone:
        """Tworzy nową strefę dostępu"""
        if zone_id in self.zones:
            raise ValueError(f"Zone {zone_id} already exists")
        
        zone = AccessZone(zone_id, access_level, description, metadata)
        self.zones[zone_id] = zone
        
        print(f"🔐 Created access zone: {zone_id} ({access_level.value})")
        return zone
    
    def assign_being_to_zone(self, being_ulid: str, zone_id: str):
        """Przypisuje byt do strefy dostępu"""
        if zone_id not in self.zones:
            raise ValueError(f"Zone {zone_id} does not exist")
        
        old_zone = self.being_zones.get(being_ulid)
        self.being_zones[being_ulid] = zone_id
        
        if old_zone and old_zone != zone_id:
            print(f"🔄 Being {being_ulid[:8]}... evolved from {old_zone} to {zone_id}")
        else:
            print(f"🎯 Being {being_ulid[:8]}... assigned to zone: {zone_id}")

    def track_being_evolution(self, being_ulid: str, evolution_info: Dict[str, Any]):
        """Śledzi ewolucję bytu w systemie kontroli dostępu"""
        if not hasattr(self, 'evolution_history'):
            self.evolution_history = {}
        
        if being_ulid not in self.evolution_history:
            self.evolution_history[being_ulid] = []
        
        self.evolution_history[being_ulid].append({
            "timestamp": datetime.now().isoformat(),
            "evolution_info": evolution_info,
            "new_zone": self.being_zones.get(being_ulid)
        })

    def get_being_evolution_history(self, being_ulid: str) -> List[Dict[str, Any]]:
        """Zwraca historię ewolucji bytu"""
        if not hasattr(self, 'evolution_history'):
            return []
        return self.evolution_history.get(being_ulid, [])
    
    def get_being_zone(self, being_ulid: str) -> Optional[AccessZone]:
        """Pobiera strefę dostępu dla bytu"""
        zone_id = self.being_zones.get(being_ulid)
        if zone_id:
            return self.zones.get(zone_id)
        
        # Domyślnie publiczna strefa
        return self.zones.get("public_zone")
    
    def check_access(self, being_ulid: str, user_ulid: str = None, 
                    user_session: Dict[str, Any] = None) -> bool:
        """Sprawdza czy użytkownik ma dostęp do bytu"""
        zone = self.get_being_zone(being_ulid)
        if not zone:
            return False
        
        # Publiczne byty - zawsze dostępne
        if zone.access_level == AccessLevel.PUBLIC:
            return True
        
        # Brak użytkownika - brak dostępu do niepublicznych
        if not user_ulid:
            return False
        
        # Sprawdź czy użytkownik nie jest na czarnej liście
        if user_ulid in zone.denied_users:
            return False
        
        # Sprawdź czy użytkownik jest na białej liście
        if user_ulid in zone.allowed_users:
            return True
        
        # Authenticated - wystarczy być zalogowanym
        if zone.access_level == AccessLevel.AUTHENTICATED:
            return user_session is not None
        
        # Sensitive - wymagane specjalne uprawnienia
        if zone.access_level == AccessLevel.SENSITIVE:
            if not user_session:
                return False
            
            user_permissions = user_session.get("permissions", [])
            user_role = user_session.get("role", "user")
            
            # Administratorzy mają dostęp do wszystkiego
            if user_role in ["admin", "super_admin"]:
                return True
            
            # Sprawdź specjalne uprawnienia
            return "sensitive_access" in user_permissions
        
        return False
    
    def filter_accessible_beings(self, being_list: List[Any], 
                                user_ulid: str = None, 
                                user_session: Dict[str, Any] = None) -> List[Any]:
        """Filtruje listę bytów według uprawnień dostępu"""
        accessible_beings = []
        
        for being in being_list:
            being_ulid = getattr(being, 'ulid', None)
            if being_ulid and self.check_access(being_ulid, user_ulid, user_session):
                accessible_beings.append(being)
        
        return accessible_beings
    
    def get_access_summary(self, user_ulid: str = None, 
                          user_session: Dict[str, Any] = None) -> Dict[str, Any]:
        """Zwraca podsumowanie dostępów dla użytkownika"""
        summary = {
            "user_ulid": user_ulid,
            "zones": {},
            "total_beings": len(self.being_zones),
            "accessible_beings": 0
        }
        
        for zone_id, zone in self.zones.items():
            zone_beings = [bid for bid, zid in self.being_zones.items() if zid == zone_id]
            accessible_count = 0
            
            for being_ulid in zone_beings:
                if self.check_access(being_ulid, user_ulid, user_session):
                    accessible_count += 1
            
            summary["zones"][zone_id] = {
                "access_level": zone.access_level.value,
                "description": zone.description,
                "total_beings": len(zone_beings),
                "accessible_beings": accessible_count,
                "has_access": accessible_count > 0
            }
            
            summary["accessible_beings"] += accessible_count
        
        return summary

# Globalna instancja kontrolera dostępu
access_controller = AccessController()
