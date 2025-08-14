
```python
"""
Being Ownership Manager - Zarządza własnością Being przez Kernel
W tym systemie Kernel Being jest właścicielem wszystkich innych Being
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

class BeingOwnershipManager:
    """
    Zarządza własnością Being w systemie Kernel-Being
    
    Zasady:
    - Kernel Being jest master'em swojej instancji
    - Każdy Being ma owner_ulid wskazujący na Kernel
    - Lux Being reprezentuje użytkownika trwale
    - Brak tradycyjnych sesji HTTP
    """
    
    def __init__(self, kernel_being_ulid: str):
        self.kernel_being_ulid = kernel_being_ulid
        self.owned_beings: Dict[str, 'Being'] = {}
        self.ownership_hierarchy: Dict[str, List[str]] = {}
        
    async def register_being_ownership(self, being: 'Being', owner_ulid: str = None):
        """Rejestruje Being jako należący do tego Kernel"""
        owner = owner_ulid or self.kernel_being_ulid
        
        # Dodaj metadane właściciela
        being.data['_owner_kernel'] = self.kernel_being_ulid
        being.data['_owned_by'] = owner
        being.data['_owned_at'] = datetime.now().isoformat()
        
        # Rejestruj w cache
        self.owned_beings[being.ulid] = being
        
        # Buduj hierarchię
        if owner not in self.ownership_hierarchy:
            self.ownership_hierarchy[owner] = []
        self.ownership_hierarchy[owner].append(being.ulid)
        
        print(f"🏛️ Kernel {self.kernel_being_ulid[:8]} owns Being {being.alias} ({being.ulid[:8]})")
        
    async def get_being_safe(self, being_ulid: str, requester_ulid: str = None):
        """
        Bezpieczne pobranie Being - sprawdza ownership
        
        Konflikty są niemożliwe bo:
        - Tylko owner może modyfikować Being
        - Inne Being mogą tylko czytać (jeśli mają uprawnienia)
        """
        being = self.owned_beings.get(being_ulid)
        
        if not being:
            return None
            
        # Sprawdź uprawnienia
        if self._can_access_being(being, requester_ulid):
            return being
        else:
            print(f"❌ Access denied: {requester_ulid} → {being_ulid}")
            return None
    
    async def modify_being_safe(self, being_ulid: str, modifier_ulid: str, changes: Dict[str, Any]):
        """
        Bezpieczna modyfikacja Being - tylko przez owner'a
        
        TO ELIMINUJE KONFLIKTY PISANIA!
        """
        being = self.owned_beings.get(being_ulid)
        
        if not being:
            return {"success": False, "error": "Being not found"}
            
        # Sprawdź czy modifier jest owner'em
        being_owner = being.data.get('_owned_by', being.data.get('_owner_kernel'))
        
        if modifier_ulid != being_owner and modifier_ulid != self.kernel_being_ulid:
            return {
                "success": False, 
                "error": f"Only owner {being_owner[:8]} can modify this Being"
            }
        
        # Modyfikuj bezpiecznie
        being.data.update(changes)
        being.data['_last_modified'] = datetime.now().isoformat()
        being.data['_modified_by'] = modifier_ulid
        
        # Automatyczny save jeśli persistent
        if being.is_persistent():
            await being.save()
            
        return {"success": True, "being": being}
    
    def _can_access_being(self, being: 'Being', requester_ulid: str) -> bool:
        """Sprawdza czy requester może odczytać Being"""
        
        # Kernel może wszystko
        if requester_ulid == self.kernel_being_ulid:
            return True
            
        # Owner może wszystko
        being_owner = being.data.get('_owned_by', being.data.get('_owner_kernel'))
        if requester_ulid == being_owner:
            return True
            
        # Sprawdź strefy dostępu
        access_zone = being.access_zone
        if access_zone == "public_zone":
            return True
            
        # Sprawdź czy requester należy do tej samej hierarchii
        if requester_ulid in self.ownership_hierarchy.get(being_owner, []):
            return True
            
        return False
    
    def get_ownership_summary(self) -> Dict[str, Any]:
        """Podsumowanie systemu własności"""
        return {
            "kernel_being": self.kernel_being_ulid,
            "total_owned_beings": len(self.owned_beings),
            "ownership_hierarchy": {
                owner: len(beings) 
                for owner, beings in self.ownership_hierarchy.items()
            },
            "hierarchy_depth": len(self.ownership_hierarchy)
        }

class KernelBeingManager:
    """
    Manager dla Kernel Being - implementuje logikę master'a systemu
    """
    
    def __init__(self, kernel_being: 'Being'):
        self.kernel_being = kernel_being
        self.ownership_manager = BeingOwnershipManager(kernel_being.ulid)
        
    async def create_lux_being_for_user(self, user_identifier: str, user_data: Dict[str, Any] = None):
        """
        Tworzy Lux Being dla użytkownika - TRWAŁY BYT zamiast sesji
        """
        from ..models.being import Being
        
        # Sprawdź czy użytkownik już ma Lux Being
        existing_lux = await self._find_lux_for_user(user_identifier)
        if existing_lux:
            print(f"👤 Returning existing Lux for {user_identifier}: {existing_lux.ulid[:8]}")
            return existing_lux
        
        # Utwórz nowy Lux Being
        lux_data = {
            "user_identifier": user_identifier,
            "user_type": "authenticated" if user_data else "anonymous",
            "created_by_kernel": self.kernel_being.ulid,
            "user_data": user_data or {},
            "active_since": datetime.now().isoformat()
        }
        
        lux_being = await Being.create(
            alias="lux",
            attributes=lux_data,
            persistent=True  # TRWAŁY - nie sesyjny!
        )
        
        # Rejestruj ownership
        await self.ownership_manager.register_being_ownership(lux_being, self.kernel_being.ulid)
        
        print(f"👤 Created new Lux Being for {user_identifier}: {lux_being.ulid[:8]}")
        return lux_being
    
    async def _find_lux_for_user(self, user_identifier: str):
        """Znajduje istniejący Lux Being dla użytkownika"""
        from ..models.being import Being
        
        # Przeszukaj wszystkie Being z aliasem "lux"
        all_lux = await Being.get_by_alias("lux")
        
        for lux in all_lux:
            if (lux.data.get("user_identifier") == user_identifier and 
                lux.data.get("created_by_kernel") == self.kernel_being.ulid):
                return lux
                
        return None
    
    async def handle_being_communication(self, sender_ulid: str, target_ulid: str, message: Dict[str, Any]):
        """
        Obsługuje komunikację między Being - Kernel jako mediator
        
        BRAK KONFLIKTÓW bo wszystko przechodzi przez Kernel!
        """
        
        # Sprawdź czy sender może komunikować się z target
        sender = await self.ownership_manager.get_being_safe(sender_ulid, sender_ulid)
        target = await self.ownership_manager.get_being_safe(target_ulid, sender_ulid)
        
        if not sender or not target:
            return {"success": False, "error": "Communication not allowed"}
        
        # Kernel mediuje komunikację
        communication_log = {
            "from": sender_ulid,
            "to": target_ulid, 
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "mediated_by": self.kernel_being.ulid
        }
        
        # Dodaj do historii komunikacji w Kernel Being
        if '_communications' not in self.kernel_being.data:
            self.kernel_being.data['_communications'] = []
            
        self.kernel_being.data['_communications'].append(communication_log)
        
        # Wyślij do target Being
        if '_received_messages' not in target.data:
            target.data['_received_messages'] = []
            
        target.data['_received_messages'].append({
            "from": sender_ulid,
            "message": message,
            "received_at": datetime.now().isoformat()
        })
        
        await target.save()
        await self.kernel_being.save()
        
        return {"success": True, "communication_logged": True}
```
