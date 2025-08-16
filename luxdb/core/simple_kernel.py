#!/usr/bin/env python3
"""
🧠 Simple Kernel - Prosty asynchroniczny kernel z systemem zadań

Kernel jako master function który:
- Odbiera zadania (tasks)
- Deleguje do modułów (auth, dispatcher, etc.)
- Zarządza wieloma zadaniami asynchronicznie
- Używa Task Being dla komunikacji
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
    """Reprezentuje zadanie w systemie"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    target_module: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, processing, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SimpleKernel:
    """
    Prosty Kernel działający jak master function z asynchronicznym systemem zadań
    """

    def __init__(self):
        self.kernel_being: Optional[Being] = None # Zostawione dla kompatybilności, ale nieużywane do stanu
        self.active_tasks: Dict[str, Task] = {}
        self.task_listeners: Dict[str, List[Callable]] = {}
        self.modules: Dict[str, Being] = {}
        self.running = False
        self.kernel_id: str = ""
        self.kernel_state: Dict[str, Any] = {}


    async def initialize(self):
        """Inicjalizuje prosty kernel"""
        print("🧠 Initializing Simple Kernel...")

        # Kernel nie tworzy własnych bytów - tylko zarządza zadaniami
        self.kernel_id = f"kernel_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.kernel_state = {
            "active_tasks": {},
            "modules": {},
            "task_history": [],
            "kernel_type": "simple_async",
            "max_concurrent_tasks": 100,
            "initialized_at": datetime.now().isoformat(),
            "kernel_id": self.kernel_id
        }

        # Kernel nie jest Being - jest czystym koordynatorem
        print(f"🧠 Simple Kernel ready: {self.kernel_id}")

        # Załaduj podstawowe moduły
        await self._load_core_modules()

        # Załaduj tasks i dispenser
        await self._load_tasks_dispenser()

        self.running = True
        return self.kernel_id # Zwraca ID kernela zamiast Being

    async def _load_core_modules(self):
        """Ładuje podstawowe moduły systemu"""
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

        # Simulacja sprawdzenia auth
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
        # Simulacja sprawdzenia sesji
        return {
            "valid": bool(session_id and session_id.startswith('sess_')),
            "session_id": session_id
        }

    return {"status": "auth_module_ready", "supported_actions": ["authenticate", "check_session"]}
'''
        }

        try:
            from luxdb.repository.soul_repository import SoulRepository, BeingRepository
            
            # Create Soul through repository
            auth_soul = await Soul.create(auth_genotype, alias="auth_module_soul")
            if not auth_soul:
                return None
                
            # Create Being through repository only
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

        # Routing logic
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
            from luxdb.repository.soul_repository import SoulRepository, BeingRepository
            
            # Create Soul through repository
            dispatcher_soul = await Soul.create(dispatcher_genotype, alias="dispatcher_soul")
            if not dispatcher_soul:
                return None
                
            # Create Being through repository only
            being = await BeingRepository.create_being(
                soul_hash=dispatcher_soul.soul_hash,
                alias="task_dispatcher", 
                data={"module_type": "dispatcher"}
            )
            return being
        except Exception as e:
            print(f"❌ Failed to create dispatcher module: {e}")
            return None

    async def _load_tasks_dispenser(self):
        """Ładuje system zadań i dispenser"""
        try:
            # Simplified loading without GenotypeLoader for now
            from luxdb.models.soul import Soul

            # Load tasks and dispenser souls by alias
            tasks_soul = await Soul.get_by_alias("tasks_soul")
            if tasks_soul:
                print("🎯 Tasks soul found")

            dispenser_soul = await Soul.get_by_alias("dispenser_soul")
            if dispenser_soul:
                dispenser_being = await Being.get_or_create(
                    soul=dispenser_soul,
                    alias="kernel_dispenser",
                    unique_by="soul_hash"
                )
                self.modules["dispenser"] = dispenser_being
                print("📦 Dispenser singleton loaded")

        except Exception as e:
            print(f"⚠️ Error loading tasks/dispenser: {e}")

    async def create_task(self, task_type: str, target_module: str, payload: Dict[str, Any]) -> str:
        """Tworzy nowe zadanie w systemie"""
        task = Task(
            task_type=task_type,
            target_module=target_module,
            payload=payload
        )

        self.active_tasks[task.task_id] = task

        # Utwórz Task Being dla komunikacji
        await self._create_task_being(task)

        print(f"📋 Created task {task.task_id}: {task_type} → {target_module}")

        # Uruchom zadanie asynchronicznie
        asyncio.create_task(self._process_task(task.task_id))

        return task.task_id

    async def _create_task_being(self, task: Task) -> Being:
        """Tworzy Task Being dla komunikacji"""
        task_genotype = {
            "genesis": {
                "name": "task_entity",
                "type": "communication_task",
                "version": "1.0.0"
            },
            "attributes": {
                "task_id": {"py_type": "str"},
                "status": {"py_type": "str"},
                "result": {"py_type": "dict"},
                "listeners": {"py_type": "list"}
            }
        }

        from luxdb.repository.soul_repository import SoulRepository, BeingRepository
        
        task_soul = await Soul.create(task_genotype, alias=f"task_soul_{task.task_id[:8]}")
        if not task_soul:
            return None

        # Create Being through repository only - no persistence for tasks
        return await BeingRepository.create_being(
            soul_hash=task_soul.soul_hash,
            alias=f"task_{task.task_id[:8]}",
            data={
                "task_id": task.task_id,
                "task_type": task.task_type,
                "target_module": task.target_module,
                "status": task.status,
                "created_at": task.created_at.isoformat(),
                "persistent": False
            }
        )

    async def _process_task(self, task_id: str):
        """Przetwarza zadanie asynchronicznie"""
        if task_id not in self.active_tasks:
            return

        task = self.active_tasks[task_id]
        task.status = "processing"

        try:
            print(f"⚙️ Processing task {task_id}: {task.task_type}")

            # Znajdź target module
            target_module = self.modules.get(task.target_module)

            if target_module:
                # Deleguj do modułu - ensure payload is dict and properly formatted
                if isinstance(task.payload, dict):
                    execution_payload = task.payload
                else:
                    execution_payload = {"data": task.payload}

                # Execute with proper error handling
                try:
                    result = await target_module.execute_soul_function("execute", execution_payload)
                    task.result = result
                    task.status = "completed"
                    task.completed_at = datetime.now()
                    print(f"✅ Task {task_id} completed")
                except Exception as exec_e:
                    print(f"⚠️ Module execution failed for {task_id}, trying direct call: {exec_e}")
                    # Fallback to kernel processing
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
        asyncio.create_task(self._cleanup_task_after_delay(task_id, delay=300))  # 5 min

    async def _kernel_fallback_processing(self, task: Task) -> Dict[str, Any]:
        """Kernel sam obsługuje zadanie gdy nie ma odpowiedniego modułu"""
        if task.task_type == "ping":
            return {"pong": True, "timestamp": datetime.now().isoformat()}

        elif task.task_type == "status":
            return {
                "kernel_status": "running",
                "active_tasks": len(self.active_tasks),
                "loaded_modules": list(self.modules.keys())
            }

        elif task.task_type == "echo":
            return {"echo": task.payload.get("message", "no message")}

        else:
            return {
                "processed_by": "kernel_fallback",
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

    def add_task_listener(self, task_id: str, listener: Callable):
        """Dodaje listener dla konkretnego zadania"""
        if task_id not in self.task_listeners:
            self.task_listeners[task_id] = []

        self.task_listeners[task_id].append(listener)

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

    def get_system_status(self) -> Dict[str, Any]:
        """Status całego systemu"""
        return {
            "kernel_active": self.running,
            "kernel_id": self.kernel_id,
            "active_tasks_count": len(self.active_tasks),
            "loaded_modules": list(self.modules.keys()),
            "task_listeners_count": sum(len(listeners) for listeners in self.task_listeners.values())
        }

    async def create_default_module(self, module_type: str, config):
        """Create default modules for kernel"""
        try:
            from luxdb.repository.soul_repository import SoulRepository, BeingRepository
            
            # Ensure config is a dict
            if isinstance(config, str):
                config = {"config_string": config}
            elif config is None:
                config = {}

            # Create being through repository only
            being = await BeingRepository.create_being(
                soul_hash=None,  # Generic module without specific soul
                alias=f"{module_type}_module",
                data={
                    "module_type": module_type,
                    "config": config,
                    "status": "active"
                }
            )

            self.modules[module_type] = being
            print(f"✅ Created {module_type} module: {being.ulid[:8]}")
            return being

        except Exception as e:
            print(f"❌ Failed to create {module_type} module: {e}")
            return None

# Globalna instancja
simple_kernel = SimpleKernel()