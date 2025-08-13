
#!/usr/bin/env python3
"""
🧠 Intelligent Kernel - Główny inteligentny byt systemu LuxOS
Zawiera funkcje registry i zarządza całym systemem
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from luxdb.models.soul import Soul
from luxdb.models.being import Being

class IntelligentKernel:
    """
    Inteligentny Kernel - główny byt systemu który:
    - Zarządza rejestrem aliasów (registry)
    - Kontroluje dostęp do zasobów
    - Zarządza TTL i cleanup
    - Jest singletonem systemu
    """
    
    def __init__(self):
        self.kernel_being: Optional[Being] = None
        self.alias_mappings: Dict[str, str] = {}  # alias -> soul_hash
        self.alias_history: Dict[str, List[Dict]] = {}
        self.managed_beings: List[Dict] = []
        self.active = False
        
    async def initialize(self):
        """Inicjalizuje Kernel jako Being z rozszerzoną funkcjonalnością"""
        if self.kernel_being:
            print("🧠 Kernel already initialized")
            return self.kernel_being
            
        print("🧠 Initializing Intelligent Kernel...")
        
        # Znajdź lub utwórz Soul dla Kernel
        kernel_soul = await self._get_or_create_kernel_soul()
        
        # Utwórz singleton Kernel Being
        self.kernel_being = await Being.get_or_create(
            soul=kernel_soul,
            alias="intelligent_kernel",
            attributes={
                "role": "system_kernel",
                "registry_active": True,
                "managed_beings_count": 0,
                "alias_mappings_count": 0
            },
            unique_by="soul_hash"  # Singleton pattern
        )
        
        # Załaduj istniejące dane registry z Being
        await self._load_registry_data()
        
        self.active = True
        print(f"🧠 Intelligent Kernel initialized: {self.kernel_being.ulid}")
        return self.kernel_being
        
    async def _get_or_create_kernel_soul(self) -> Soul:
        """Tworzy Soul dla Kernel z wbudowanymi funkcjami registry"""
        
        kernel_genotype = {
            "genesis": {
                "name": "intelligent_kernel",
                "type": "system_kernel_soul",
                "version": "1.0.0",
                "description": "Główny inteligentny byt systemu z funkcjami registry"
            },
            "attributes": {
                "alias_mappings": {"py_type": "dict", "default": {}},
                "alias_history": {"py_type": "dict", "default": {}},
                "managed_beings": {"py_type": "list", "default": []},
                "registry_stats": {"py_type": "dict", "default": {}}
            },
            "module_source": '''
def init(being_context=None):
    """Initialize intelligent kernel with registry capabilities"""
    print(f"🧠 Intelligent Kernel {being_context.get('alias', 'unknown')} initialized")
    return {
        "ready": True,
        "role": "intelligent_kernel",
        "registry_enabled": True,
        "suggested_persistence": True
    }

def execute(request=None, being_context=None, **kwargs):
    """Main kernel execution with intelligent routing"""
    print(f"🧠 Kernel processing: {request}")
    
    if not request:
        return {"status": "kernel_active", "capabilities": ["registry", "management", "cleanup"]}
        
    action = request.get('action') if isinstance(request, dict) else str(request)
    
    if action == 'register_alias':
        return register_alias_mapping(
            request.get('alias'), 
            request.get('soul_hash'), 
            being_context
        )
    elif action == 'get_current_hash':
        return get_current_hash_for_alias(
            request.get('alias'), 
            being_context
        )
    elif action == 'create_being_by_alias':
        return create_being_by_alias(
            request.get('alias'),
            request.get('attributes', {}),
            request.get('persistent', True),
            being_context
        )
    elif action == 'cleanup':
        return cleanup_expired_beings(being_context)
    else:
        return {"status": "processed", "action": action, "kernel_active": True}

def register_alias_mapping(alias, soul_hash, being_context):
    """Rejestruje mapowanie alias -> soul_hash"""
    if not being_context.get('data'):
        being_context['data'] = {}

    if 'alias_mappings' not in being_context['data']:
        being_context['data']['alias_mappings'] = {}

    if 'alias_history' not in being_context['data']:
        being_context['data']['alias_history'] = {}

    old_hash = being_context['data']['alias_mappings'].get(alias)
    being_context['data']['alias_mappings'][alias] = soul_hash

    # Historia zmian
    if alias not in being_context['data']['alias_history']:
        being_context['data']['alias_history'][alias] = []

    being_context['data']['alias_history'][alias].append({
        "soul_hash": soul_hash,
        "updated_at": "2025-01-30T00:00:00",
        "previous_hash": old_hash
    })

    return {
        "success": True,
        "alias": alias,
        "soul_hash": soul_hash,
        "previous_hash": old_hash,
        "is_update": old_hash is not None
    }

def get_current_hash_for_alias(alias, being_context):
    """Pobiera aktualny hash dla aliasu"""
    alias_mappings = being_context.get('data', {}).get('alias_mappings', {})
    soul_hash = alias_mappings.get(alias)

    if soul_hash:
        return {
            "success": True,
            "alias": alias,
            "soul_hash": soul_hash,
            "found": True
        }
    else:
        return {
            "success": False,
            "alias": alias,
            "found": False,
            "error": f"No soul hash found for alias '{alias}'"
        }

def create_being_by_alias(soul_alias, attributes=None, persistent=True, being_context=None):
    """Kernel tworzy Being na podstawie aliasu Soul"""
    print(f"🧠 Kernel creating being from soul alias: {soul_alias}")
    
    # Tu będzie implementacja w IntelligentKernel.create_being_by_alias()
    return {
        "delegated_to": "kernel_method",
        "soul_alias": soul_alias,
        "attributes": attributes,
        "persistent": persistent
    }

def cleanup_expired_beings(being_context):
    """Czyści wygasłe byty (TTL)"""
    print("🧹 Kernel cleaning up expired beings...")
    return {
        "cleanup_completed": True,
        "removed_count": 0,
        "kernel_managed": True
    }
'''
        }
        
        return await Soul.get_or_create(
            genotype=kernel_genotype,
            alias="intelligent_kernel_soul"
        )
        
    async def _load_registry_data(self):
        """Ładuje dane registry z Being do pamięci"""
        if not self.kernel_being:
            return
            
        data = self.kernel_being.data
        self.alias_mappings = data.get('alias_mappings', {})
        self.alias_history = data.get('alias_history', {})
        self.managed_beings = data.get('managed_beings', [])
        
        print(f"🧠 Loaded registry: {len(self.alias_mappings)} aliases, {len(self.managed_beings)} beings")
        
    async def _save_registry_data(self):
        """Zapisuje dane registry z pamięci do Being"""
        if not self.kernel_being:
            return
            
        self.kernel_being.data['alias_mappings'] = self.alias_mappings
        self.kernel_being.data['alias_history'] = self.alias_history
        self.kernel_being.data['managed_beings'] = self.managed_beings
        self.kernel_being.data['registry_stats'] = {
            "aliases_count": len(self.alias_mappings),
            "beings_count": len(self.managed_beings),
            "last_update": datetime.now().isoformat()
        }
        
        await self.kernel_being.save()
        
    async def register_alias_mapping(self, alias: str, soul_hash: str) -> Dict[str, Any]:
        """Rejestruje mapowanie alias -> soul_hash"""
        old_hash = self.alias_mappings.get(alias)
        self.alias_mappings[alias] = soul_hash
        
        # Historia
        if alias not in self.alias_history:
            self.alias_history[alias] = []
            
        self.alias_history[alias].append({
            "soul_hash": soul_hash,
            "updated_at": datetime.now().isoformat(),
            "previous_hash": old_hash
        })
        
        await self._save_registry_data()
        
        print(f"🧠 Kernel registered alias: {alias} → {soul_hash[:8]}...")
        return {
            "success": True,
            "alias": alias,
            "soul_hash": soul_hash,
            "previous_hash": old_hash,
            "is_update": old_hash is not None
        }
        
    async def get_current_hash_for_alias(self, alias: str) -> Dict[str, Any]:
        """Pobiera aktualny hash dla aliasu"""
        soul_hash = self.alias_mappings.get(alias)
        
        if soul_hash:
            return {
                "success": True,
                "alias": alias,
                "soul_hash": soul_hash,
                "found": True
            }
        else:
            return {
                "success": False,
                "alias": alias,
                "found": False,
                "error": f"No soul hash found for alias '{alias}'"
            }
            
    async def create_being_by_alias(self, soul_alias: str, attributes: Dict[str, Any] = None, persistent: bool = True) -> 'Being':
        """Kernel tworzy Being na podstawie aliasu Soul"""
        print(f"🧠 Kernel creating being from soul alias: {soul_alias}")
        
        # Sprawdź czy mamy zarejestrowany alias
        registry_result = await self.get_current_hash_for_alias(soul_alias)
        
        if registry_result.get('found'):
            # Użyj zarejestrowanego hash
            soul_hash = registry_result['soul_hash']
            print(f"🧠 Using registered hash: {soul_hash[:8]}...")
        else:
            # Spróbuj znaleźć Soul po aliasie
            soul = await Soul.get_by_alias(soul_alias)
            if not soul:
                raise ValueError(f"Soul with alias '{soul_alias}' not found in registry or database")
            soul_hash = soul.soul_hash
            
            # Zarejestruj znaleziony alias
            await self.register_alias_mapping(soul_alias, soul_hash)
        
        # Utwórz Being bezpośrednio (bez delegacji!)
        from ..repository.soul_repository import SoulRepository
        soul_result = await SoulRepository.get_soul_by_hash(soul_hash)
        if not soul_result.get('success'):
            raise ValueError(f"Soul with hash {soul_hash} not found")
            
        target_soul = soul_result.get('soul')
        
        # Utwórz Being przez _create_internal żeby uniknąć rekursji
        being = await Being._create_internal(
            soul=target_soul,
            attributes=attributes,
            persistent=persistent
        )
        
        # Zarejestruj w managed_beings
        self.managed_beings.append({
            "ulid": being.ulid,
            "soul_alias": soul_alias,
            "soul_hash": soul_hash,
            "created_by_kernel": True,
            "registered_at": datetime.now().isoformat()
        })
        
        await self._save_registry_data()
        
        print(f"🧠 Kernel created being: {being.ulid} from alias '{soul_alias}'")
        return being
        
    async def cleanup_expired_beings(self) -> Dict[str, Any]:
        """Czyści wygasłe byty"""
        print("🧹 Kernel cleaning up expired beings...")
        
        # Tu będzie logika cleanup TTL
        removed_count = 0
        
        await self._save_registry_data()
        
        return {
            "cleanup_completed": True,
            "removed_count": removed_count,
            "kernel_managed": True
        }
        
    async def get_system_status(self) -> Dict[str, Any]:
        """Status całego systemu"""
        return {
            "kernel_active": self.active,
            "kernel_being_ulid": self.kernel_being.ulid if self.kernel_being else None,
            "aliases_count": len(self.alias_mappings),
            "managed_beings_count": len(self.managed_beings),
            "registry_mappings": self.alias_mappings,
            "last_update": datetime.now().isoformat()
        }

# Globalna instancja
intelligent_kernel = IntelligentKernel()
