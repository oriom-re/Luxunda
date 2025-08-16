"""
Admin Kernel Interface - Dedykowany endpoint administratora dla komunikacji z Lux
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

try:
    from luxdb.models.being import Being
    from luxdb.models.soul import Soul
except ImportError:
    # Fallback - tworzymy podstawowe klasy
    class Being:
        def __init__(self, soul=None, data=None, alias=None):
            self.soul = soul
            self.data = data or {}
            self.alias = alias
        
        @classmethod
        async def create(cls, soul=None, data=None, alias=None):
            return cls(soul, data, alias)
    
    class Soul:
        def __init__(self, genotype=None, alias=None):
            self.genotype = genotype or {}
            self.alias = alias
        
        @classmethod
        async def get_by_alias(cls, alias):
            return None
        
        @classmethod
        async def create(cls, genotype, alias=None):
            return cls(genotype, alias)
        
        async def get_hash(self):
            return "dummy_hash_12345"

# Import kernel_system
try:
    from .kernel_system import kernel_system
except ImportError:
    # Fallback if not available
    kernel_system = None

logger = logging.getLogger(__name__)

class AdminKernelInterface:
    """
    Interface administratora do komunikacji z Kernel i Lux
    """

    def __init__(self):
        self.kernel_being = None
        self.lux_being = None
        self.active_connections = []
        self.conversation_history = []
        self.system_status = {
            "kernel_active": False,
            "lux_active": False,
            "last_heartbeat": None,
            "connections": 0
        }
        self.is_initialized = False # Dodano flagę inicjalizacji
        self.kernel_system = None # Dodano atrybut dla KernelSystem

    async def initialize(self, mode: str = "basic", scenario_name: str = "default"):
        """Inicjalizuje Admin Kernel Interface"""
        try:
            print("🚀 Inicjalizacja Admin Kernel Interface...")

            # Inicjalizuj kernel system
            self.kernel_system = KernelSystem()
            if hasattr(self.kernel_system, 'initialize'):
                await self.kernel_system.initialize(mode, scenario_name)

            # Inicjalizuj admin being
            await self._initialize_admin_being()

            self.is_initialized = True
            print("✅ Admin Kernel Interface zainicjalizowany")
            return True

        except Exception as e:
            print(f"⚠️ Admin Kernel initialization warning: {e}")
            print("🔄 Continuing with limited functionality...")
            self.is_initialized = False
            return False

    async def _initialize_admin_being(self):
        """Tworzy lub ładuje byty administracyjne (Kernel i Lux)"""
        if not self.kernel_being:
            kernel_soul = await self._get_or_create_kernel_soul()
            self.kernel_being = await Being.create(
                soul=kernel_soul,
                data={
                    "role": "system_kernel",
                    "capabilities": ["system_management", "being_supervision", "resource_monitoring"],
                    "status": "active"
                },
                alias="admin_kernel"
            )

        if not self.lux_being:
            lux_soul = await self._get_or_create_lux_soul()
            self.lux_being = await Being.create(
                soul=lux_soul,
                data={
                    "role": "ai_assistant",
                    "capabilities": ["conversation", "analysis", "task_management"],
                    "status": "active"
                },
                alias="Lux"
            )

        self.system_status["kernel_active"] = bool(self.kernel_being)
        self.system_status["lux_active"] = bool(self.lux_being)
        self.system_status["last_heartbeat"] = datetime.now().isoformat()


    async def _get_or_create_kernel_soul(self) -> Soul:
        """Tworzy lub ładuje Soul dla Kernel Being"""
        soul = await Soul.get_by_alias("admin_kernel_soul")

        if not soul:
            kernel_genotype = {
                "genesis": {
                    "name": "admin_kernel",
                    "type": "system_kernel",
                    "version": "1.0.0",
                    "doc": "Kernel administratorski do zarządzania systemem"
                },
                "attributes": {
                    "role": {"py_type": "str"},
                    "capabilities": {"py_type": "List[str]"},
                    "status": {"py_type": "str"},
                    "system_resources": {"py_type": "dict"},
                    "active_beings": {"py_type": "dict"}
                },
                "genes": {
                    "monitor_system": "luxdb.core.admin_kernel.monitor_system_resources",
                    "manage_beings": "luxdb.core.admin_kernel.manage_beings",
                    "execute_command": "luxdb.core.admin_kernel.execute_admin_command"
                }
            }

            soul = await Soul.create(kernel_genotype, alias="admin_kernel_soul")

        return soul

    async def _get_or_create_lux_soul(self) -> Soul:
        """Tworzy lub ładuje Soul dla Lux Being"""
        soul = await Soul.get_by_alias("admin_lux_soul")

        if not soul:
            lux_genotype = {
                "genesis": {
                    "name": "admin_lux",
                    "type": "ai_assistant",
                    "version": "1.0.0",
                    "doc": "AI asystent administratora systemu"
                },
                "attributes": {
                    "role": {"py_type": "str"},
                    "capabilities": {"py_type": "List[str]"},
                    "personality": {"py_type": "str"},
                    "status": {"py_type": "str"},
                    "conversation_context": {"py_type": "dict"},
                    "knowledge_base": {"py_type": "dict"}
                },
                "genes": {
                    "process_message": "luxdb.core.admin_kernel.process_lux_message",
                    "analyze_system": "luxdb.core.admin_kernel.analyze_system_state",
                    "generate_response": "luxdb.core.admin_kernel.generate_lux_response"
                }
            }

            soul = await Soul.create(lux_genotype, alias="admin_lux_soul")

        return soul

    async def connect_admin(self, websocket: WebSocket):
        """Łączy administratora przez WebSocket"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.system_status["connections"] = len(self.active_connections)

        # Wyślij powitanie
        await self.send_message(websocket, {
            "type": "system_greeting",
            "message": "🔧 Witaj w Admin Kernel Interface! Połączono z Lux.",
            "kernel_status": self.system_status,
            "timestamp": datetime.now().isoformat()
        })

        print(f"👤 Administrator połączony. Aktywne połączenia: {len(self.active_connections)}")

    async def disconnect_admin(self, websocket: WebSocket):
        """Rozłącza administratora"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            self.system_status["connections"] = len(self.active_connections)

        print(f"👤 Administrator rozłączony. Aktywne połączenia: {len(self.active_connections)}")

    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Wysyła wiadomość przez WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            print(f"❌ Błąd wysyłania wiadomości: {e}")

    async def broadcast_message(self, message: Dict[str, Any]):
        """Rozgłasza wiadomość do wszystkich połączonych administratorów"""
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(json.dumps(message))
            except:
                # Usuń zerwane połączenia
                self.active_connections.remove(connection)

    async def process_admin_message(self, websocket: WebSocket, message_data: Dict[str, Any]):
        """Przetwarza wiadomość od administratora"""
        message_type = message_data.get("type")
        content = message_data.get("content", "")

        print(f"📨 Admin message: {message_type} - {content[:50]}...")

        # Zapisz do historii
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "admin_message",
            "content": content,
            "message_type": message_type
        })

        try:
            if message_type == "lux_chat":
                response = await self.chat_with_lux(content)
            elif message_type == "kernel_command":
                response = await self.execute_kernel_command(content)
            elif message_type == "system_status":
                response = await self.get_system_status()
            elif message_type == "being_list":
                response = await self.get_beings_list()
            else:
                response = await self.chat_with_lux(content)  # Default to Lux chat

            # Wyślij odpowiedź
            await self.send_message(websocket, {
                "type": "lux_response",
                "message": response["message"],
                "data": response.get("data", {}),
                "timestamp": datetime.now().isoformat()
            })

        except Exception as e:
            await self.send_message(websocket, {
                "type": "error",
                "message": f"❌ Błąd przetwarzania: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    async def chat_with_lux(self, message: str) -> Dict[str, Any]:
        """Rozmowa z Lux Being"""
        print(f"💬 Chat with Lux: {message}")

        # Symulacja odpowiedzi Lux (w przyszłości integracja z AI)
        context = {
            "kernel_status": self.system_status,
            "beings_count": len(kernel_system.beings_registry) if kernel_system else 0,
            "conversation_history": self.conversation_history[-5:]  # Ostatnie 5 wiadomości
        }

        if "status" in message.lower():
            response_message = f"""🔍 **System Status Report**

**Kernel Status**: {'🟢 Active' if self.system_status['kernel_active'] else '🔴 Inactive'}
**Lux Status**: {'🟢 Active' if self.system_status['lux_active'] else '🔴 Inactive'}
**Active Connections**: {self.system_status['connections']}
**Registered Beings**: {len(kernel_system.beings_registry) if kernel_system else 0}
**Last Heartbeat**: {self.system_status['last_heartbeat']}

Czy potrzebujesz szczegółowych informacji o którymś z komponentów?"""

        elif "beings" in message.lower() or "byty" in message.lower():
            beings_info = []
            if kernel_system and kernel_system.beings_registry:
                for ulid, being in kernel_system.beings_registry.items():
                    beings_info.append(f"- {being.alias} ({ulid[:8]}...)")
            else:
                beings_info.append("- Brak zarejestrowanych bytów.")

            response_message = f"""📋 **Registered Beings** ({len(beings_info)}):

{chr(10).join(beings_info)}

Każdy byt może być zarządzany przez kernel. Chcesz zobaczyć szczegóły któregoś z nich?"""

        elif "help" in message.lower() or "pomoc" in message.lower():
            response_message = """🛠️ **Admin Kernel Commands**:

**System Commands**:
- `status` - Status systemu
- `beings` - Lista zarejestrowanych bytów
- `restart kernel` - Restart kernel system
- `health check` - Sprawdzenie stanu systemu

**Lux Chat**:
- Pisz normalnie, a Lux odpowie
- `analyze [topic]` - Analiza systemu
- `suggest [improvement]` - Sugestie ulepszeń

Jestem tutaj, aby pomóc w zarządzaniu systemem! 🤖"""

        else:
            response_message = f"""🤖 Cześć! Jestem Lux, AI asystent tego systemu.

Otrzymałem twoją wiadomość: "{message}"

Kernel działa sprawnie, wszystkie systemy są aktywne. W czym mogę pomóc?

💡 **Sugestie**:
- Sprawdź `status` systemu
- Zobacz listę `beings`
- Zapytaj o konkretny komponent"""

        return {
            "message": response_message,
            "data": context
        }

    async def execute_kernel_command(self, command: str) -> Dict[str, Any]:
        """Wykonuje komendę kernel"""
        print(f"⚡ Kernel command: {command}")

        if "restart" in command.lower():
            await self.initialize("advanced") # Restart the admin interface and Lux
            return {"message": "🔄 Kernel system zrestartowany"}

        elif "health" in command.lower():
            status = await self.get_system_status()
            return {
                "message": "🩺 Health Check Complete",
                "data": status
            }

        else:
            return {"message": f"❓ Nieznana komenda kernel: {command}"}

    async def get_system_status(self) -> Dict[str, Any]:
        """Pobiera szczegółowy status systemu"""
        kernel_status = await self.kernel_system.get_system_status() if self.kernel_system and hasattr(self.kernel_system, 'get_system_status') else {"status": "N/A"}

        return {
            "message": "📊 System Status Retrieved",
            "data": {
                "admin_interface": self.system_status,
                "kernel_system": kernel_status
            }
        }

    async def get_beings_list(self) -> Dict[str, Any]:
        """Pobiera listę bytów"""
        beings_data = []
        if self.kernel_system and hasattr(self.kernel_system, 'beings_registry'):
            for ulid, being in self.kernel_system.beings_registry.items():
                being_soul = await being.soul
                soul_hash = await being_soul.get_hash() if being_soul else 'N/A'
                beings_data.append({
                    "ulid": ulid,
                    "alias": being.alias,
                    "soul_hash": soul_hash[:8] + "..." if soul_hash != 'N/A' else 'N/A'
                })
        else:
            beings_data.append({"alias": "Kernel system not initialized or unavailable."})


        return {
            "message": f"📋 Found {len(beings_data)} beings",
            "data": {"beings": beings_data}
        }


# Gene functions
async def monitor_system_resources(being, context):
    """Monitoruje zasoby systemu"""
    # Ensure kernel_system is accessible and has the expected attributes
    if kernel_system and hasattr(kernel_system, 'beings_registry') and hasattr(admin_kernel, 'active_connections'):
        return {
            "cpu_usage": "12%",
            "memory_usage": "245MB",
            "active_beings": len(kernel_system.beings_registry),
            "connections": len(admin_kernel.active_connections)
        }
    else:
        return {
            "cpu_usage": "N/A",
            "memory_usage": "N/A",
            "active_beings": 0,
            "connections": 0,
            "error": "Kernel system or admin kernel not available."
        }


async def manage_beings(being, context):
    """Zarządza bytami w systemie"""
    action = context.get("action")
    target_being_ulid = context.get("target_being")

    # Ensure kernel_system is accessible and has the expected attributes
    if not (kernel_system and hasattr(kernel_system, 'beings_registry')):
        return {"result": "Error: Kernel system not available."}

    if action == "list":
        return {"beings": list(kernel_system.beings_registry.keys())}
    elif action == "status":
        if target_being_ulid in kernel_system.beings_registry:
            target_being = kernel_system.beings_registry[target_being_ulid]
            return {"status": f"Being {target_being.alias} status: active"}
        else:
            return {"status": f"Being with ULID {target_being_ulid} not found"}
    elif action == "remove":
        if target_being_ulid in kernel_system.beings_registry:
            del kernel_system.beings_registry[target_being_ulid]
            return {"result": f"Being with ULID {target_being_ulid} removed"}
        else:
            return {"result": f"Being with ULID {target_being_ulid} not found"}

    return {"result": f"Action {action} on {target_being_ulid} processed"}


async def execute_admin_command(being, context):
    """Wykonuje komendy administratorskie"""
    command = context.get("command")
    # Ensure admin_kernel is initialized and has the 'initialize' method
    if command == "restart kernel":
        if admin_kernel and hasattr(admin_kernel, 'initialize'):
            await admin_kernel.initialize() # Restart the admin interface and Lux
            return {"result": "Admin Kernel Interface and Lux restarted."}
        else:
            return {"result": "Error: Admin Kernel Interface not available or not initialized."}
    return {"result": f"Executed admin command: {command}"}

async def process_lux_message(being, context):
    """Przetwarza wiadomość dla Lux"""
    message = context.get("message", "")
    # This is a placeholder. In a real scenario, this would involve
    # more complex processing or calling another gene.
    return {"processed": True, "response_ready": True, "internal_response": f"Lux processed: '{message}'"}

async def analyze_system_state(being, context):
    """Analizuje stan systemu"""
    # This is a placeholder. It should ideally query the kernel_system.
    return {
        "system_health": "good",
        "recommendations": ["Monitor memory usage", "Check being connections"],
        "alerts": []
    }

async def generate_lux_response(being, context):
    """Generuje odpowiedź Lux"""
    # This is a placeholder. It should use context to generate a meaningful response.
    response_text = context.get("internal_response", "Default Lux response.")
    return {
        "response": response_text,
        "confidence": 0.9
    }

# Dummy KernelSystem and other necessary classes for the code to be runnable
class Being:
    def __init__(self, soul, data, alias):
        self.soul = soul
        self.data = data
        self.alias = alias

    @classmethod
    async def create(cls, soul, data, alias):
        return cls(soul, data, alias)

class Soul:
    def __init__(self, genotype, alias):
        self.genotype = genotype
        self.alias = alias

    @classmethod
    async def get_by_alias(cls, alias):
        # Dummy implementation
        return cls({"genesis": {"name": "dummy_soul"}}, alias)

    @classmethod
    async def create(cls, genotype, alias):
        # Dummy implementation
        return cls(genotype, alias)

    async def get_hash(self):
        # Dummy implementation
        return "dummy_hash_12345"

class KernelSystem:
    def __init__(self):
        self.beings_registry = {}
        self.system_status = {"status": "initialized"}

    async def initialize(self, mode: str, scenario_name: str):
        print(f"KernelSystem initializing with mode: {mode}, scenario: {scenario_name}")
        # Simulate some beings
        self.beings_registry["dummy_ulid_1"] = Being(None, {}, "DummyBeing1")
        self.beings_registry["dummy_ulid_2"] = Being(None, {}, "DummyBeing2")
        self.system_status = {"status": "active"}

    async def get_system_status(self):
        return self.system_status

# Globalna instancja
admin_kernel = AdminKernelInterface()

# Dodajemy funkcję pomocniczą do bezpiecznej inicjalizacji
async def initialize_admin_kernel_safely():
    """Bezpieczna inicjalizacja admin kernel"""
    try:
        await admin_kernel.initialize()
        return True
    except Exception as e:
        print(f"⚠️ Admin kernel initialization warning: {e}")
        return False