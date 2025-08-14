
#!/usr/bin/env python3
"""
🎯 System Manager - Jednolity zarządca całego systemu LuxOS

Centralizuje:
- Kernel management
- Being lifecycle
- Session handling
- Resource cleanup
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import ulid

from .simple_kernel import simple_kernel
from .intelligent_kernel import intelligent_kernel
from .session_data_manager import global_session_registry
from .being_ownership_manager import KernelBeingManager
from ..models.soul import Soul
from ..models.being import Being

class SystemManager:
    """
    Centralny manager systemu - jedna ścieżka dla wszystkich operacji
    """
    
    def __init__(self):
        self.active = False
        self.kernel_type = None
        self.kernel_instance = None
        self.kernel_being_manager = None
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.system_stats = {
            "started_at": None,
            "souls_created": 0,
            "beings_created": 0,
            "sessions_active": 0
        }
        
    async def initialize_system(self, kernel_type: str = "simple", load_genotypes: bool = True):
        """
        Główna inicjalizacja systemu - JEDNA ŚCIEŻKA
        """
        print(f"🎯 SystemManager: Initializing {kernel_type} system...")
        
        # 1. Initialize kernel
        if kernel_type == "simple":
            self.kernel_instance = await simple_kernel.initialize()
        elif kernel_type == "intelligent":
            self.kernel_instance = await intelligent_kernel.initialize()
        else:
            raise ValueError(f"Unknown kernel type: {kernel_type}")
            
        self.kernel_type = kernel_type
        
        # 2. Initialize Being ownership management
        self.kernel_being_manager = KernelBeingManager(self.kernel_instance)
        
        # 3. Load genotypes if requested
        if load_genotypes:
            await self._load_genotypes()
            
        # 4. System ready
        self.active = True
        self.system_stats["started_at"] = datetime.now().isoformat()
        
        print(f"✅ SystemManager: {kernel_type} system ready")
        return True
        
    async def _load_genotypes(self):
        """Load genotype system"""
        try:
            from . import genotype_system
            result = await genotype_system.initialize_system()
            print(f"🧬 Loaded {result.get('loaded_souls_count', 0)} genotypes")
        except Exception as e:
            print(f"⚠️ Genotype loading failed: {e}")
            
    async def create_user_session(self, user_identifier: str, session_data: Dict[str, Any] = None):
        """
        Tworzy sesję użytkownika - UNIFIED PATH
        """
        if not self.active:
            raise RuntimeError("System not initialized")
            
        session_id = str(ulid.ulid())
        
        # Create Lux Being for user via Kernel Being Manager
        lux_being = await self.kernel_being_manager.create_lux_being_for_user(
            user_identifier, session_data
        )
        
        # Register session
        self.active_sessions[session_id] = {
            "user_identifier": user_identifier,
            "lux_being_ulid": lux_being.ulid,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat()
        }
        
        self.system_stats["sessions_active"] = len(self.active_sessions)
        
        print(f"👤 Created session {session_id[:8]} for user {user_identifier}")
        
        return {
            "session_id": session_id,
            "lux_being": lux_being,
            "status": "created"
        }
        
    async def get_session_lux(self, session_id: str) -> Optional['Being']:
        """
        Pobiera Lux Being dla sesji - UNIFIED ACCESS
        """
        session = self.active_sessions.get(session_id)
        if not session:
            return None
            
        lux_ulid = session["lux_being_ulid"]
        
        # Update last activity
        session["last_activity"] = datetime.now().isoformat()
        
        # Get Lux Being through ownership manager
        return await self.kernel_being_manager.ownership_manager.get_being_safe(
            lux_ulid, lux_ulid
        )
        
    async def create_soul(self, genotype: Dict[str, Any], alias: str = None) -> 'Soul':
        """
        Unified Soul creation
        """
        soul = await Soul.create(genotype, alias)
        self.system_stats["souls_created"] += 1
        return soul
        
    async def create_being(self, soul: 'Soul', attributes: Dict[str, Any] = None, 
                          persistent: bool = True, owner_session: str = None) -> 'Being':
        """
        Unified Being creation with ownership tracking
        """
        being = await Being.create(soul, attributes, persistent)
        
        # Register ownership
        if owner_session and owner_session in self.active_sessions:
            session = self.active_sessions[owner_session]
            lux_ulid = session["lux_being_ulid"]
            await self.kernel_being_manager.ownership_manager.register_being_ownership(
                being, lux_ulid
            )
        else:
            # Default to kernel ownership
            await self.kernel_being_manager.ownership_manager.register_being_ownership(
                being, self.kernel_instance.ulid
            )
            
        self.system_stats["beings_created"] += 1
        return being
        
    async def execute_function(self, soul_hash: str, function_name: str, 
                              arguments: Dict[str, Any], session_id: str = None):
        """
        Unified function execution path
        """
        if self.kernel_type == "intelligent":
            # Use intelligent kernel's execution system
            return await intelligent_kernel.execute_function_via_master_soul(
                soul_hash, function_name, {"arguments": arguments}
            )
        else:
            # Use simple kernel's task system
            task_id = await simple_kernel.create_task(
                "execute_function",
                "kernel",
                {
                    "soul_hash": soul_hash,
                    "function_name": function_name,
                    "arguments": arguments
                }
            )
            return {"task_id": task_id, "status": "queued"}
            
    async def cleanup_session(self, session_id: str):
        """
        Cleanup session resources
        """
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            
            # Cleanup through session registry
            await global_session_registry.cleanup_session(session_id)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            self.system_stats["sessions_active"] = len(self.active_sessions)
            
            print(f"🗑️ Cleaned up session {session_id[:8]}")
            
    async def get_system_status(self) -> Dict[str, Any]:
        """
        Complete system status
        """
        souls = await Soul.get_all()
        beings = await Being.get_all()
        
        return {
            "system_active": self.active,
            "kernel_type": self.kernel_type,
            "kernel_ulid": self.kernel_instance.ulid if self.kernel_instance else None,
            "souls_total": len(souls),
            "beings_total": len(beings),
            "active_sessions": len(self.active_sessions),
            "stats": self.system_stats,
            "timestamp": datetime.now().isoformat()
        }

# Global system manager instance
system_manager = SystemManager()
