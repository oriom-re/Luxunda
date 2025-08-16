
#!/usr/bin/env python3
"""
🧠 LuxOS Unified Kernel - Jeden kernel z prostą bazą i zaawansowanymi opcjami

Architektura:
- BAZA: Simple Kernel (asynchroniczne zadania, moduły)
- ROZSZERZENIA: Registry, ewolucja, zarządzanie zasobami
- JEDEN PUNKT: Wszystko w jednym miejscu
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

from luxdb.models.soul import Soul
from luxdb.models.being import Being

@dataclass
class Task:
    """Reprezentuje zadanie w systemie (z Simple Kernel)"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    target_module: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class UnifiedKernel:
    """
    🧠 Zunifikowany Kernel LuxOS
    
    BAZA (Simple):
    - Asynchroniczne zadania
    - Moduły systemowe
    - Task management
    
    ROZSZERZENIA (Advanced):
    - Registry aliasów
    - Zarządzanie aktywnych Being
    - Ewolucja bytów
    - Session management
    """

    def __init__(self):
        # === SIMPLE KERNEL BASE ===
        self.active_tasks: Dict[str, Task] = {}
        self.task_listeners: Dict[str, List[Callable]] = {}
        self.modules: Dict[str, Being] = {}
        self.running = False
        self.kernel_id: str = ""
        self.kernel_state: Dict[str, Any] = {}
        
        # === INTELLIGENT EXTENSIONS ===
        self.kernel_being: Optional[Being] = None
        self.alias_mappings: Dict[str, str] = {}  # alias -> soul_hash
        self.alias_history: Dict[str, List[Dict]] = {}
        self.managed_beings: List[Dict] = []
        
        # Registry aktywnych instancji
        self.active_beings: Dict[str, 'Being'] = {}  # ulid -> Being instance
        self.soul_cache: Dict[str, 'Soul'] = {}      # soul_hash -> Soul instance
        self.session_beings: Dict[str, List[str]] = {}  # session_id -> [being_ulids]
        self.fingerprint_mappings: Dict[str, str] = {}  # fingerprint -> lux_being_ulid

        self.active = False

    async def initialize(self, mode: str = "simple"):
        """
        Inicjalizuje Kernel w trybie Simple lub Advanced
        
        Args:
            mode: "simple" (tylko zadania) lub "advanced" (pełne możliwości)
        """
        print(f"🧠 Initializing Unified Kernel in {mode} mode...")

        # === SIMPLE BASE INITIALIZATION ===
        self.kernel_id = f"kernel_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.kernel_state = {
            "active_tasks": {},
            "modules": {},
            "task_history": [],
            "kernel_type": f"unified_{mode}",
            "max_concurrent_tasks": 100,
            "initialized_at": datetime.now().isoformat(),
            "kernel_id": self.kernel_id,
            "mode": mode
        }

        # Załaduj podstawowe moduły
        await self._load_core_modules()

        if mode == "advanced":
            # === ADVANCED EXTENSIONS ===
            await self._initialize_advanced_features()

        self.running = True
        self.active = True
        
        print(f"🧠 Unified Kernel ready: {self.kernel_id} ({mode} mode)")
        return self.kernel_id

    async def _load_core_modules(self):
        """Ładuje podstawowe moduły systemu (Simple Base)"""
        try:
            # Auth module
            auth_being = await self._create_auth_module()
            if auth_being:
                self.modules["auth"] = auth_being
                print("🔐 Auth module loaded")

            # Task dispatcher module
            dispatcher_being = await self._create_dispatcher_module()
            if dispatcher_being:
                self.modules["dispatcher"] = dispatcher_being
                print("📤 Dispatcher module loaded")

        except Exception as e:
            print(f"⚠️ Error loading modules: {e}")

    async def _initialize_advanced_features(self):
        """Inicjalizuje zaawansowane funkcje (Intelligence Extensions)"""
        try:
            # Znajdź lub utwórz Soul dla Kernel Being
            kernel_soul = await self._get_or_create_kernel_soul()

            # Utwórz singleton Kernel Being
            self.kernel_being = await Being.get_or_create(
                soul=kernel_soul,
                alias="unified_kernel",
                attributes={
                    "role": "unified_kernel",
                    "registry_active": True,
                    "managed_beings_count": 0,
                    "alias_mappings_count": 0,
                    "mode": "advanced"
                },
                unique_by="soul_hash"
            )

            # Załaduj istniejące dane registry z Being
            await self._load_registry_data()

            print(f"🧠 Advanced features initialized: {self.kernel_being.ulid}")

        except Exception as e:
            print(f"⚠️ Error initializing advanced features: {e}")

    # === SIMPLE KERNEL METHODS (BASE) ===

    async def create_task(self, task_type: str, target_module: str, payload: Dict[str, Any]) -> str:
        """Tworzy nowe zadanie w systemie (Simple Base)"""
        task = Task(
            task_type=task_type,
            target_module=target_module,
            payload=payload
        )

        self.active_tasks[task.task_id] = task

        print(f"📋 Created task {task.task_id}: {task_type} → {target_module}")

        # Uruchom zadanie asynchronicznie
        asyncio.create_task(self._process_task(task.task_id))

        return task.task_id

    async def _process_task(self, task_id: str):
        """Przetwarza zadanie asynchronicznie (Simple Base)"""
        if task_id not in self.active_tasks:
            return

        task = self.active_tasks[task_id]
        task.status = "processing"

        try:
            print(f"⚙️ Processing task {task_id}: {task.task_type}")

            # Znajdź target module
            target_module = self.modules.get(task.target_module)

            if target_module:
                # Deleguj do modułu
                if isinstance(task.payload, dict):
                    execution_payload = task.payload
                else:
                    execution_payload = {"data": task.payload}

                try:
                    result = await target_module.execute_soul_function("execute", execution_payload)
                    task.result = result
                    task.status = "completed"
                    task.completed_at = datetime.now()
                    print(f"✅ Task {task_id} completed")
                except Exception as exec_e:
                    print(f"⚠️ Module execution failed for {task_id}, trying fallback: {exec_e}")
                    result = await self._kernel_fallback_processing(task)
                    task.result = result
                    task.status = "completed"
                    task.completed_at = datetime.now()
            else:
                # Fallback - kernel sam obsługuje
                result = await self._kernel_fallback_processing(task)
                task.result = result
                task.status = "completed"
                task.completed_at = datetime.now()
                print(f"🧠 Task {task_id} handled by kernel fallback")

            # Powiadom listeners
            await self._notify_task_completion(task_id)

        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            print(f"❌ Task {task_id} failed: {e}")

        # Cleanup po czasie
        asyncio.create_task(self._cleanup_task_after_delay(task_id, delay=300))

    async def _kernel_fallback_processing(self, task: Task) -> Dict[str, Any]:
        """Kernel sam obsługuje zadanie gdy nie ma odpowiedniego modułu"""
        if task.task_type == "ping":
            return {"pong": True, "timestamp": datetime.now().isoformat()}

        elif task.task_type == "status":
            return {
                "kernel_status": "running",
                "active_tasks": len(self.active_tasks),
                "loaded_modules": list(self.modules.keys()),
                "mode": self.kernel_state.get("mode", "simple")
            }

        elif task.task_type == "echo":
            return {"echo": task.payload.get("message", "no message")}

        else:
            return {
                "processed_by": "unified_kernel_fallback",
                "task_type": task.task_type,
                "warning": "No specific module found for this task type"
            }

    async def _notify_task_completion(self, task_id: str):
        """Powiadamia listeners o zakończeniu zadania"""
        listeners = self.task_listeners.get(task_id, [])

        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(task_id, self.active_tasks[task_id])
                else:
                    listener(task_id, self.active_tasks[task_id])
            except Exception as e:
                print(f"⚠️ Listener error for task {task_id}: {e}")

    async def _cleanup_task_after_delay(self, task_id: str, delay: int = 300):
        """Usuwa zadanie z pamięci po określonym czasie"""
        await asyncio.sleep(delay)

        if task_id in self.active_tasks:
            task = self.active_tasks.pop(task_id)

            # Przenieś do historii w pamięci kernel
            history = self.kernel_state.get('task_history', [])
            history.append({
                "task_id": task_id,
                "task_type": task.task_type,
                "status": task.status,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "cleanup_at": datetime.now().isoformat()
            })

            # Zachowaj tylko ostatnie 100 zadań w historii
            self.kernel_state['task_history'] = history[-100:]

            print(f"🗑️ Cleaned up task {task_id}")

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Pobiera status zadania"""
        if task_id not in self.active_tasks:
            return None

        task = self.active_tasks[task_id]
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
            "error": task.error
        }

    # === ADVANCED METHODS (EXTENSIONS) ===

    async def register_soul_template(self, alias: str, soul_hash: str) -> Dict[str, Any]:
        """Rejestruje Template Soul (Advanced Extension)"""
        if not self.kernel_being:
            return {"success": False, "error": "Advanced features not initialized"}

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

    async def register_active_being(self, being: 'Being', session_id: str = None) -> bool:
        """Rejestruje aktywną instancję Being (Advanced Extension)"""
        if not self.kernel_being:
            print("⚠️ Advanced features not initialized")
            return False

        try:
            self.active_beings[being.ulid] = being

            # Dodaj do sesji jeśli podano session_id
            if session_id:
                if session_id not in self.session_beings:
                    self.session_beings[session_id] = []
                self.session_beings[session_id].append(being.ulid)

            print(f"🎯 Registered active being: {being.alias} ({being.ulid[:8]}...)")
            return True

        except Exception as e:
            print(f"❌ Failed to register active being: {e}")
            return False

    async def cleanup_expired_beings(self) -> Dict[str, Any]:
        """Czyści wygasłe byty (Advanced Extension)"""
        if not self.kernel_being:
            return {"cleanup_completed": False, "error": "Advanced features not initialized"}

        print("🧹 Kernel cleaning up expired beings...")

        removed_count = 0
        expired_beings = []

        # Sprawdź TTL dla aktywnych Being
        current_time = datetime.now()
        for ulid, being in list(self.active_beings.items()):
            if hasattr(being, 'ttl_expires') and being.ttl_expires and current_time > being.ttl_expires:
                expired_beings.append(ulid)

        # Usuń wygasłe
        for ulid in expired_beings:
            being = self.active_beings.pop(ulid, None)
            if being:
                removed_count += 1
                print(f"⏰ Removed expired being: {being.alias} ({ulid[:8]}...)")

        await self._save_registry_data()

        return {
            "cleanup_completed": True,
            "removed_count": removed_count,
            "kernel_managed": True,
            "active_beings_count": len(self.active_beings)
        }

    # === HELPER METHODS ===

    async def _create_auth_module(self) -> Optional[Being]:
        """Tworzy moduł autoryzacji"""
        auth_genotype = {
            "genesis": {
                "name": "auth_module",
                "type": "authentication_service",
                "version": "1.0.0"
            },
            "attributes": {
                "module_type": {
                    "py_type": "str",
                    "description": "Type of module"
                }
            },
            "module_source": '''
def execute(request=None, being_context=None, **kwargs):
    """Handles authentication requests"""
    if request is None:
        request = {}
        
    action = request.get('action', 'status')

    if action == 'authenticate':
        user_id = request.get('user_id')
        token = request.get('token')

        if user_id and token:
            return {
                "authenticated": True,
                "user_id": user_id,
                "permissions": ["read", "write"],
                "session_id": f"sess_{user_id}_123"
            }
        else:
            return {"authenticated": False, "error": "Invalid credentials"}

    elif action == 'check_session':
        session_id = request.get('session_id')
        return {
            "valid": bool(session_id and session_id.startswith('sess_')),
            "session_id": session_id
        }

    return {"status": "auth_module_ready", "supported_actions": ["authenticate", "check_session"]}
'''
        }

        try:
            from luxdb.repository.soul_repository import BeingRepository
            
            auth_soul = await Soul.create(auth_genotype, alias="auth_module_soul")
            if not auth_soul:
                return None
                
            being = await BeingRepository.create_being(
                soul_hash=auth_soul.soul_hash,
                alias="auth_module",
                data={"module_type": "authentication"}
            )
            return being
        except Exception as e:
            print(f"❌ Failed to create auth module: {e}")
            return None

    async def _create_dispatcher_module(self) -> Optional[Being]:
        """Tworzy moduł dispatcher"""
        dispatcher_genotype = {
            "genesis": {
                "name": "task_dispatcher",
                "type": "task_distribution_service",
                "version": "1.0.0"
            },
            "attributes": {
                "module_type": {
                    "py_type": "str",
                    "description": "Type of module"
                }
            },
            "module_source": '''
def execute(request=None, being_context=None, **kwargs):
    """Handles task dispatching"""
    if request is None:
        request = {}
        
    action = request.get('action', 'status')

    if action == 'dispatch':
        task_data = request.get('task_data', {})
        target = request.get('target', 'unknown')

        return {
            "dispatched": True,
            "task_id": task_data.get('task_id'),
            "target": target,
            "dispatch_time": "processed"
        }

    elif action == 'route':
        task_type = request.get('task_type')

        routes = {
            "auth": "auth_module",
            "user": "user_manager",
            "data": "data_processor"
        }

        return {
            "route_found": task_type in routes,
            "target_module": routes.get(task_type, "kernel"),
            "task_type": task_type
        }

    return {"status": "dispatcher_ready", "supported_actions": ["dispatch", "route"]}
'''
        }

        try:
            from luxdb.repository.soul_repository import BeingRepository
            
            dispatcher_soul = await Soul.create(dispatcher_genotype, alias="dispatcher_soul")
            if not dispatcher_soul:
                return None
                
            being = await BeingRepository.create_being(
                soul_hash=dispatcher_soul.soul_hash,
                alias="task_dispatcher", 
                data={"module_type": "dispatcher"}
            )
            return being
        except Exception as e:
            print(f"❌ Failed to create dispatcher module: {e}")
            return None

    async def _get_or_create_kernel_soul(self) -> Soul:
        """Tworzy Soul dla Kernel (Advanced Extension)"""
        kernel_genotype = {
            "genesis": {
                "name": "unified_kernel",
                "type": "system_kernel_unified",
                "version": "1.0.0",
                "description": "Zunifikowany kernel LuxOS z prostą bazą i zaawansowanymi rozszerzeniami"
            },
            "attributes": {
                "alias_mappings": {"py_type": "dict", "default": {}},
                "alias_history": {"py_type": "dict", "default": {}},
                "managed_beings": {"py_type": "list", "default": []},
                "registry_stats": {"py_type": "dict", "default": {}},
                "kernel_mode": {"py_type": "str", "default": "advanced"}
            },
            "module_source": '''
def init(being_context=None):
    """Initialize unified kernel"""
    print(f"🧠 Unified Kernel {being_context.get('alias', 'unknown')} initialized")
    return {
        "ready": True,
        "role": "unified_kernel",
        "registry_enabled": True,
        "task_system_enabled": True,
        "suggested_persistence": True
    }

def execute(request=None, being_context=None, **kwargs):
    """Main unified kernel execution"""
    print(f"🧠 Unified Kernel processing: {request}")

    if not request:
        return {"status": "unified_kernel_active", "capabilities": ["tasks", "registry", "management", "cleanup"]}

    action = request.get('action') if isinstance(request, dict) else str(request)

    if action == 'create_task':
        return {"delegated_to": "kernel_method", "action": "create_task"}
    elif action == 'register_being':
        return {"delegated_to": "kernel_method", "action": "register_being"}
    elif action == 'cleanup':
        return {"delegated_to": "kernel_method", "action": "cleanup"}
    else:
        return {"status": "processed", "action": action, "unified_kernel_active": True}
'''
        }

        return await Soul.create(
            genotype=kernel_genotype,
            alias="unified_kernel_soul"
        )

    async def _load_registry_data(self):
        """Ładuje dane registry z Being (Advanced Extension)"""
        if not self.kernel_being:
            return

        data = self.kernel_being.data
        self.alias_mappings = data.get('alias_mappings', {})
        self.alias_history = data.get('alias_history', {})
        self.managed_beings = data.get('managed_beings', [])
        self.fingerprint_mappings = data.get('fingerprint_mappings', {})

        print(f"🧠 Loaded registry: {len(self.alias_mappings)} aliases, {len(self.managed_beings)} beings")

    async def _save_registry_data(self):
        """Zapisuje dane registry do Being (Advanced Extension)"""
        if not self.kernel_being:
            return

        self.kernel_being.data['alias_mappings'] = self.alias_mappings
        self.kernel_being.data['alias_history'] = self.alias_history
        self.kernel_being.data['managed_beings'] = self.managed_beings
        self.kernel_being.data['fingerprint_mappings'] = self.fingerprint_mappings

        self.kernel_being.data['registry_stats'] = {
            "aliases_count": len(self.alias_mappings),
            "managed_beings_count": len(self.managed_beings),
            "active_beings_count": len(self.active_beings),
            "session_count": len(self.session_beings),
            "fingerprint_count": len(self.fingerprint_mappings),
            "last_update": datetime.now().isoformat()
        }

        await self.kernel_being.save()

    def get_system_status(self) -> Dict[str, Any]:
        """Status całego systemu"""
        base_status = {
            "kernel_active": self.running,
            "kernel_id": self.kernel_id,
            "mode": self.kernel_state.get("mode", "simple"),
            "active_tasks_count": len(self.active_tasks),
            "loaded_modules": list(self.modules.keys()),
            "task_listeners_count": sum(len(listeners) for listeners in self.task_listeners.values())
        }

        if self.kernel_being:
            # Advanced features status
            base_status.update({
                "kernel_being_ulid": self.kernel_being.ulid,
                "aliases_count": len(self.alias_mappings),
                "managed_beings_count": len(self.managed_beings),
                "active_beings_count": len(self.active_beings),
                "session_count": len(self.session_beings),
                "registry_active": True
            })

        return base_status

# Globalna instancja
unified_kernel = UnifiedKernel()
