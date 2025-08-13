
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
        self.auto_update_configs = data.get('auto_update_configs', {})
        
        print(f"🧠 Loaded registry: {len(self.alias_mappings)} aliases, {len(self.managed_beings)} beings, {len(self.auto_update_configs)} auto-update configs")
        
    async def _save_registry_data(self):
        """Zapisuje dane registry z pamięci do Being"""
        if not self.kernel_being:
            return
            
        self.kernel_being.data['alias_mappings'] = self.alias_mappings
        self.kernel_being.data['alias_history'] = self.alias_history
        self.kernel_being.data['managed_beings'] = self.managed_beings
        self.kernel_being.data['auto_update_configs'] = getattr(self, 'auto_update_configs', {})
        self.kernel_being.data['registry_stats'] = {
            "aliases_count": len(self.alias_mappings),
            "beings_count": len(self.managed_beings),
            "auto_update_aliases": len(getattr(self, 'auto_update_configs', {})),
            "last_update": datetime.now().isoformat()
        }
        
        await self.kernel_being.save()
        
    async def register_soul_template(self, alias: str, soul_hash: str) -> Dict[str, Any]:
        """Rejestruje Template Soul - używaną tylko do tworzenia Being"""
        old_hash = self.alias_mappings.get(alias)
        self.alias_mappings[alias] = {
            "soul_hash": soul_hash,
            "type": "template",
            "for_creation_only": True,
            "registered_at": datetime.now().isoformat()
        }
        
        await self._save_registry_data()
        
        print(f"📝 Registered template soul: {alias} → {soul_hash[:8]}...")
        return {
            "success": True,
            "alias": alias,
            "soul_hash": soul_hash,
            "type": "template"
        }
        
    async def register_master_soul(self, alias: str, soul_hash: str, being_ulid: str) -> Dict[str, Any]:
        """Rejestruje Master Soul z konkretną instancją Being"""
        old_hash = self.alias_mappings.get(alias)
        self.alias_mappings[alias] = {
            "soul_hash": soul_hash,
            "being_ulid": being_ulid,
            "type": "master",
            "has_instance": True,
            "registered_at": datetime.now().isoformat()
        }
        
        await self._save_registry_data()
        
        print(f"👑 Registered master soul: {alias} → {soul_hash[:8]}... (Being: {being_ulid[:8]}...)")
        return {
            "success": True,
            "alias": alias,
            "soul_hash": soul_hash,
            "being_ulid": being_ulid,
            "type": "master"
        }
        
    async def auto_update_alias_to_latest(self, alias: str, base_name: str) -> Dict[str, Any]:
        """Automatycznie aktualizuje alias do najnowszej wersji Soul o danej nazwie"""
        try:
            from ..models.soul import Soul
            
            # Znajdź wszystkie Soul z daną nazwą (base_name)
            all_souls = await Soul.get_all()
            matching_souls = []
            
            for soul in all_souls:
                if hasattr(soul, 'genotype') and 'genesis' in soul.genotype:
                    genesis = soul.genotype['genesis']
                    if genesis.get('name') == base_name:
                        matching_souls.append({
                            'soul': soul,
                            'version': genesis.get('version', '0.0.0'),
                            'created_at': getattr(soul, 'created_at', None)
                        })
            
            if not matching_souls:
                return {
                    "success": False,
                    "error": f"No souls found with name '{base_name}'"
                }
            
            # Sortuj po wersji i dacie utworzenia
            matching_souls.sort(key=lambda x: (x['version'], x['created_at']), reverse=True)
            latest_soul = matching_souls[0]['soul']
            
            # Aktualizuj alias
            result = await self.register_alias_mapping(
                alias, 
                latest_soul.soul_hash, 
                auto_update=True
            )
            
            print(f"🔄 Auto-updated alias '{alias}' to latest version {matching_souls[0]['version']}")
            return {
                **result,
                "auto_updated": True,
                "latest_version": matching_souls[0]['version'],
                "base_name": base_name
            }
            
        except Exception as e:
            print(f"❌ Auto-update failed for alias '{alias}': {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def setup_auto_update_alias(self, alias: str, base_name: str) -> Dict[str, Any]:
        """Konfiguruje alias do automatycznego śledzenia najnowszej wersji Soul"""
        
        # Znajdź aktualnie najnowszą wersję
        result = await self.auto_update_alias_to_latest(alias, base_name)
        
        if result.get("success"):
            # Zapisz konfigurację auto-update
            if not hasattr(self, 'auto_update_configs'):
                self.auto_update_configs = {}
                
            self.auto_update_configs[alias] = {
                "base_name": base_name,
                "enabled": True,
                "last_update": datetime.now().isoformat(),
                "update_count": 1
            }
            
            await self._save_registry_data()
            
            print(f"✅ Setup auto-update for alias '{alias}' → base_name '{base_name}'")
            return {
                "success": True,
                "alias": alias,
                "base_name": base_name,
                "current_version": result.get("latest_version"),
                "auto_update_enabled": True
            }
        else:
            return result
        
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
        """Kernel tworzy Being na podstawie typu Soul (template/master)"""
        print(f"🧠 Kernel creating being from soul alias: {soul_alias}")
        
        # Sprawdź typ Soul w registry
        alias_data = self.alias_mappings.get(soul_alias)
        if not alias_data:
            # Fallback - znajdź Soul i zarejestruj jako template
            from ..models.soul import Soul
            soul = await Soul.get_by_alias(soul_alias)
            if not soul:
                raise ValueError(f"Soul with alias '{soul_alias}' not found")
            
            # Automatycznie określ typ na podstawie funkcji
            if soul.has_init_function():
                raise ValueError(f"Master Soul '{soul_alias}' must be registered with Being instance first")
            else:
                await self.register_soul_template(soul_alias, soul.soul_hash)
                alias_data = self.alias_mappings.get(soul_alias)
        
        soul_type = alias_data.get("type")
        
        if soul_type == "template":
            # Template Soul - utwórz nowy Being
            return await self._create_being_from_template(soul_alias, alias_data, attributes, persistent)
        
        elif soul_type == "master":
            # Master Soul - zwróć istniejący Being
            being_ulid = alias_data.get("being_ulid")
            from ..models.being import Being
            existing_being = await Being._get_by_ulid_internal(being_ulid)
            if not existing_being:
                raise ValueError(f"Master Being {being_ulid} not found")
            
            print(f"👑 Returning existing master being: {existing_being.ulid}")
            return existing_being
            
        else:
            raise ValueError(f"Unknown soul type: {soul_type}")
    
    async def _create_being_from_template(self, soul_alias: str, alias_data: Dict, attributes: Dict[str, Any], persistent: bool) -> 'Being':
        """Tworzy Being z Template Soul"""
        soul_hash = alias_data["soul_hash"]
        
        from ..repository.soul_repository import SoulRepository
        from ..models.being import Being
        
        soul_result = await SoulRepository.get_soul_by_hash(soul_hash)
        if not soul_result.get('success'):
            raise ValueError(f"Template Soul with hash {soul_hash} not found")
            
        target_soul = soul_result.get('soul')
        
        # Utwórz Being (często nietrwały dla templates)
        being = await Being._create_internal(
            soul=target_soul,
            attributes=attributes,
            persistent=persistent
        )
        
        print(f"📝 Created being from template '{soul_alias}': {being.ulid}")
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
