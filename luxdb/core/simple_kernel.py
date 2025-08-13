
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
from datetime import datetime
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
        self.kernel_being: Optional[Being] = None
        self.active_tasks: Dict[str, Task] = {}
        self.task_listeners: Dict[str, List[Callable]] = {}
        self.modules: Dict[str, Being] = {}
        self.running = False
        
    async def initialize(self):
        """Inicjalizuje prosty kernel"""
        print("🧠 Initializing Simple Kernel...")
        
        # Utwórz Soul dla Kernel
        kernel_genotype = {
            "genesis": {
                "name": "simple_kernel",
                "type": "async_kernel",
                "version": "1.0.0",
                "description": "Prosty asynchroniczny kernel z systemem zadań"
            },
            "attributes": {
                "active_tasks": {"py_type": "dict", "default": {}},
                "modules": {"py_type": "dict", "default": {}},
                "task_history": {"py_type": "list", "default": []}
            },
            "module_source": '''
def init(being_context=None):
    """Initialize simple kernel"""
    print(f"🧠 Simple Kernel {being_context.get('alias', 'unknown')} ready")
    return {"ready": True, "type": "async_kernel", "suggested_persistence": True}

def execute(request=None, being_context=None, **kwargs):
    """Main kernel execution - delegates to task system"""
    print(f"🧠 Kernel processing request: {request}")
    
    if not request:
        return {"status": "kernel_ready", "active_tasks": len(being_context.get('data', {}).get('active_tasks', {}))}
    
    # Wszystkie żądania stają się zadaniami
    task_type = request.get('task_type', 'generic')
    target_module = request.get('target_module', 'kernel')
    payload = request.get('payload', {})
    
    return {
        "task_created": True,
        "task_type": task_type,
        "target_module": target_module,
        "delegated_to": "async_task_system"
    }
'''
        }
        
        kernel_soul = await Soul.create(kernel_genotype, alias="simple_kernel_soul")
        
        # Utwórz Kernel Being
        self.kernel_being = await Being.create(
            soul=kernel_soul,
            alias="simple_kernel",
            attributes={
                "kernel_type": "simple_async",
                "max_concurrent_tasks": 100,
                "initialized_at": datetime.now().isoformat()
            }
        )
        
        # Załaduj podstawowe moduły
        await self._load_core_modules()
        
        # Załaduj tasks i dispenser
        await self._load_tasks_dispenser()
        
        print(f"🧠 Simple Kernel initialized: {self.kernel_being.ulid}")
        return self.kernel_being
        
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
            "module_source": '''
def execute(request=None, being_context=None, **kwargs):
    """Handles authentication requests"""
    action = request.get('action') if request else 'status'
    
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
            auth_soul = await Soul.create(auth_genotype, alias="auth_module_soul")
            return await Being.create(
                soul=auth_soul,
                alias="auth_module",
                attributes={"module_type": "authentication"}
            )
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
            "module_source": '''
def execute(request=None, being_context=None, **kwargs):
    """Handles task dispatching"""
    action = request.get('action', 'status')
    
    if action == 'dispatch':
        task_data = request.get('task_data', {})
        target = request.get('target', 'unknown')
        
        return {
            "dispatched": True,
            "task_id": task_data.get('task_id'),
            "target": target,
            "dispatch_time": "2025-01-30T00:00:00"
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
            dispatcher_soul = await Soul.create(dispatcher_genotype, alias="dispatcher_soul")
            return await Being.create(
                soul=dispatcher_soul,
                alias="task_dispatcher",
                attributes={"module_type": "dispatcher"}
            )
        except Exception as e:
            print(f"❌ Failed to create dispatcher module: {e}")
            return None
    
    async def _load_tasks_dispenser(self):
        """Ładuje system zadań i dispenser"""
        try:
            from luxdb.utils.genotype_loader import GenotypeLoader
            loader = GenotypeLoader()
            
            # Load tasks soul
            tasks_soul = await loader.load_soul_from_file("genotypes/tasks_soul.json")
            if tasks_soul:
                print("🎯 Tasks soul loaded")
            
            # Load and create singleton dispenser
            dispenser_soul = await loader.load_soul_from_file("genotypes/dispenser_soul.json") 
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
        
        task_soul = await Soul.create(task_genotype, alias=f"task_soul_{task.task_id[:8]}")
        
        return await Being.create(
            soul=task_soul,
            alias=f"task_{task.task_id[:8]}",
            attributes={
                "task_id": task.task_id,
                "task_type": task.task_type,
                "target_module": task.target_module,
                "status": task.status,
                "created_at": task.created_at.isoformat()
            },
            persistent=False  # Task beings są nietrwałe
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
                # Deleguj do modułu
                result = await target_module.execute(task.payload)
                
                task.result = result
                task.status = "completed"
                task.completed_at = datetime.now()
                
                print(f"✅ Task {task_id} completed")
                
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
            
            # Przenieś do historii w Kernel Being
            if self.kernel_being:
                history = self.kernel_being.data.get('task_history', [])
                history.append({
                    "task_id": task_id,
                    "task_type": task.task_type,
                    "status": task.status,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "cleanup_at": datetime.now().isoformat()
                })
                
                # Zachowaj tylko ostatnie 100 zadań w historii
                self.kernel_being.data['task_history'] = history[-100:]
                await self.kernel_being.save()
            
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
            "kernel_being_ulid": self.kernel_being.ulid if self.kernel_being else None,
            "active_tasks_count": len(self.active_tasks),
            "loaded_modules": list(self.modules.keys()),
            "task_listeners_count": sum(len(listeners) for listeners in self.task_listeners.values())
        }

# Globalna instancja
simple_kernel = SimpleKernel()
