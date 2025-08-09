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

from luxdb.models.being import Being
from database.models.base import Soul

# Import kernel_system - będzie zaimportowany dynamicznie
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

    async def initialize(self):
        """Inicjalizuje Kernel i Lux Beings"""
        print("🚀 Inicjalizacja Admin Kernel Interface...")

        # Dynamiczny import kernel_system
        global kernel_system
        if kernel_system is None:
            from .kernel_system import kernel_system as ks
            kernel_system = ks

        # Inicjalizuj główny Kernel System
        await kernel_system.initialize("advanced")

        # Utwórz lub załaduj Kernel Being
        kernel_soul = await self._get_or_create_kernel_soul()
        self.kernel_being = await Being.create(
            kernel_soul,
            {
                "role": "system_kernel",
                "capabilities": ["system_management", "being_supervision", "resource_monitoring"],
                "status": "active"
            },
            alias="admin_kernel"
        )

        # Utwórz lub załaduj Lux Being
        lux_soul = await self._get_or_create_lux_soul()
        self.lux_being = await Being.create(
            lux_soul,
            {
                "role": "ai_assistant",
                "capabilities": ["conversation", "system_analysis", "support"],
                "personality": "helpful_technical_expert",
                "status": "active"
            },
            alias="admin_lux"
        )

        self.system_status["kernel_active"] = True
        self.system_status["lux_active"] = True
        self.system_status["last_heartbeat"] = datetime.now().isoformat()

        print("✅ Admin Kernel Interface zainicjalizowany")

    async def _get_or_create_kernel_soul(self) -> Soul:
        """Tworzy lub ładuje Soul dla Kernel Being"""
        soul = await Soul.load_by_alias("admin_kernel_soul")

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
        soul = await Soul.load_by_alias("admin_lux_soul")

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
            "beings_count": len(kernel_system.beings_registry),
            "conversation_history": self.conversation_history[-5:]  # Ostatnie 5 wiadomości
        }

        if "status" in message.lower():
            response_message = f"""🔍 **System Status Report**

**Kernel Status**: {'🟢 Active' if self.system_status['kernel_active'] else '🔴 Inactive'}
**Lux Status**: {'🟢 Active' if self.system_status['lux_active'] else '🔴 Inactive'}
**Active Connections**: {self.system_status['connections']}
**Registered Beings**: {len(kernel_system.beings_registry)}
**Last Heartbeat**: {self.system_status['last_heartbeat']}

Czy potrzebujesz szczegółowych informacji o którymś z komponentów?"""

        elif "beings" in message.lower() or "byty" in message.lower():
            beings_info = []
            for ulid, being in kernel_system.beings_registry.items():
                beings_info.append(f"- {being.alias} ({ulid[:8]}...)")

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
            await kernel_system.initialize("advanced")
            return {"message": "🔄 Kernel system zrestartowany"}

        elif "health" in command.lower():
            status = await kernel_system.get_system_status()
            return {
                "message": "🩺 Health Check Complete",
                "data": status
            }

        else:
            return {"message": f"❓ Nieznana komenda kernel: {command}"}

    async def get_system_status(self) -> Dict[str, Any]:
        """Pobiera szczegółowy status systemu"""
        kernel_status = await kernel_system.get_system_status()

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

        for ulid, being in kernel_system.beings_registry.items():
            beings_data.append({
                "ulid": ulid,
                "alias": being.alias,
                "soul_hash": getattr(being, 'soul_hash', 'unknown')[:8] + "..."
            })

        return {
            "message": f"📋 Found {len(beings_data)} beings",
            "data": {"beings": beings_data}
        }

# Globalna instancja
admin_kernel = AdminKernelInterface()

# Gene functions
async def monitor_system_resources(being, context):
    """Monitoruje zasoby systemu"""
    return {
        "cpu_usage": "12%",
        "memory_usage": "245MB", 
        "active_beings": len(kernel_system.beings_registry),
        "connections": len(admin_kernel.active_connections)
    }

async def manage_beings(being, context):
    """Zarządza bytami w systemie"""
    action = context.get("action")
    target_being = context.get("target_being")

    if action == "list":
        return {"beings": list(kernel_system.beings_registry.keys())}
    elif action == "status":
        return {"status": f"Being {target_being} status"}

    return {"result": f"Action {action} executed on {target_being}"}

async def execute_admin_command(being, context):
    """Wykonuje komendy administratorskie"""
    command = context.get("command")
    return {"result": f"Executed: {command}"}

async def process_lux_message(being, context):
    """Przetwarza wiadomość dla Lux"""
    message = context.get("message", "")
    return {"processed": True, "response_ready": True}

async def analyze_system_state(being, context):
    """Analizuje stan systemu"""
    return {
        "system_health": "good",
        "recommendations": ["Monitor memory usage", "Check being connections"],
        "alerts": []
    }

async def generate_lux_response(being, context):
    """Generuje odpowiedź Lux"""
    return {
        "response": "Generated response based on context",
        "confidence": 0.9
    }