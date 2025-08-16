"""
Session Data Manager - Three-Table Architecture
Templates -> Instances -> Relations

Simplified session management without complex typing.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import ulid as _ulid

class SessionDataManager:
    """
    Simple session data manager for three-table architecture:
    - Templates (genotypes/patterns)
    - Instances (concrete objects)
    - Relations (connections between instances with observer context)
    """

    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(_ulid.ulid())
        self.templates = {}  # Template cache
        self.instances = {}  # Instance cache
        self.relations = {}  # Relations cache
        self.user_context = {}
        self.conversation_history = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    async def store_template(self, template_id: str, template_data: Dict[str, Any]):
        """Store template in session cache"""
        self.templates[template_id] = {
            "id": template_id,
            "data": template_data,
            "created_at": datetime.now().isoformat(),
            "type": "template"
        }
        self.last_activity = datetime.now()

    async def store_instance(self, instance_id: str, template_id: str, instance_data: Dict[str, Any]):
        """Store instance linked to template"""
        self.instances[instance_id] = {
            "id": instance_id,
            "template_id": template_id,
            "data": instance_data,
            "created_at": datetime.now().isoformat(),
            "type": "instance"
        }
        self.last_activity = datetime.now()

    async def store_relation(self, relation_id: str, source_id: str, target_id: str, 
                           observer_context: Dict[str, Any], relation_data: Dict[str, Any]):
        """Store relation with observer context"""
        self.relations[relation_id] = {
            "id": relation_id,
            "source_id": source_id,
            "target_id": target_id,
            "observer_context": observer_context,
            "data": relation_data,
            "created_at": datetime.now().isoformat(),
            "type": "relation"
        }
        self.last_activity = datetime.now()

    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID"""
        return self.templates.get(template_id)

    async def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get instance by ID"""
        return self.instances.get(instance_id)

    async def get_relation(self, relation_id: str) -> Optional[Dict[str, Any]]:
        """Get relation by ID"""
        return self.relations.get(relation_id)

    async def get_instances_by_template(self, template_id: str) -> List[Dict[str, Any]]:
        """Get all instances created from a template"""
        return [instance for instance in self.instances.values() 
                if instance.get("template_id") == template_id]

    async def get_relations_for_instance(self, instance_id: str) -> List[Dict[str, Any]]:
        """Get all relations where instance is source or target"""
        return [relation for relation in self.relations.values()
                if relation.get("source_id") == instance_id or relation.get("target_id") == instance_id]

    async def update_user_context(self, key: str, value: Any):
        """Update user context"""
        self.user_context[key] = value
        self.last_activity = datetime.now()

    async def add_conversation_entry(self, message: str, response: str, metadata: Dict[str, Any] = None):
        """Add conversation entry"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "response": response,
            "metadata": metadata or {}
        }
        self.conversation_history.append(entry)

        # Keep last 100 entries
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-100:]

        self.last_activity = datetime.now()

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "templates_count": len(self.templates),
            "instances_count": len(self.instances),
            "relations_count": len(self.relations),
            "conversation_entries": len(self.conversation_history),
            "context_keys": len(self.user_context)
        }

class GlobalSessionRegistry:
    """
    Global registry for all active sessions.
    Simplified for three-table architecture.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.active_sessions = {}
            cls._instance.initialized = False
        return cls._instance

    async def initialize(self):
        """Initialize session registry"""
        if self.initialized:
            return

        print("🎯 Session registry initializing...")
        self.initialized = True
        print(f"✅ Session registry ready")

    async def get_or_create_session_manager(self, session_id: str = None) -> SessionDataManager:
        """Get or create session manager"""
        if session_id is None:
            session_id = str(_ulid.ulid())
            
        if session_id not in self.active_sessions:
            print(f"🆕 Creating new session: {session_id}")
            self.active_sessions[session_id] = SessionDataManager(session_id)
        else:
            self.active_sessions[session_id].last_activity = datetime.now()

        return self.active_sessions[session_id]

    async def get_session_manager(self, session_id: str = None) -> SessionDataManager:
        """Alias for get_or_create_session_manager for backward compatibility"""
        return await self.get_or_create_session_manager(session_id)

    async def get_session(self, session_id: str) -> Optional[SessionDataManager]:
        """Get session without creating new one"""
        return self.active_sessions.get(session_id)

    async def cleanup_session(self, session_id: str):
        """Cleanup session and associated data"""
        if session_id in self.active_sessions:
            print(f"🗑️ Cleaning up session: {session_id}")
            del self.active_sessions[session_id]

    async def build_conversation_context(self, session_id: str, message: str) -> Dict[str, Any]:
        """Build conversation context for AI processing"""
        session_manager = self.active_sessions.get(session_id)

        if not session_manager:
            return {
                "session_id": session_id,
                "message": message,
                "user_context": {},
                "conversation_history": [],
                "timestamp": datetime.now().isoformat(),
                "system_status": "no_session",
                "architecture": "three_table"
            }

        stats = session_manager.get_session_stats()
        return {
            "session_id": session_id,
            "message": message,
            "user_context": session_manager.user_context,
            "conversation_history": session_manager.conversation_history,
            "session_stats": stats,
            "timestamp": datetime.now().isoformat(),
            "system_status": "active",
            "architecture": "three_table"
        }

    async def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old inactive sessions"""
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        sessions_to_remove = []

        for session_id, session_manager in self.active_sessions.items():
            if session_manager.last_activity.timestamp() < cutoff_time:
                sessions_to_remove.append(session_id)

        for session_id in sessions_to_remove:
            await self.cleanup_session(session_id)

        if sessions_to_remove:
            print(f"🧹 Cleaned up {len(sessions_to_remove)} old sessions")

        return len(sessions_to_remove)

# Add missing method to SessionDataManager
from datetime import datetime
from typing import Dict, Any, List, Optional

# Global session registry
global_session_registry = {}

class SessionDataManager:
    """Extended with missing methods for compatibility"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.templates = {}
        self.instances = {}
        self.relations = {}
        self.user_context = {}
        self.conversation_history = []
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    async def build_conversation_context(self, message: str) -> Dict[str, Any]:
        """Build conversation context for this session"""
        return {
            "session_id": self.session_id,
            "message": message,
            "user_context": self.user_context,
            "conversation_history": self.conversation_history,
            "timestamp": datetime.now().isoformat(),
            "system_status": "active"
        }

    # ... rest of methods remain unchanged

# SessionManager alias for backward compatibility
SessionManager = SessionDataManager

# Global instance for backward compatibility
global_session_registry = GlobalSessionRegistry()