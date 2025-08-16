
"""
Three-Table Architecture System
===============================

Simple and clean architecture with:
1. Templates (patterns/genotypes)
2. Instances (concrete objects from templates)
3. Relations (connections between instances with observer context)
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import ulid as _ulid
from luxdb.core.postgre_db import Postgre_db

class TemplateManager:
    """Manages templates (patterns/genotypes)"""
    
    def __init__(self, db: Postgre_db):
        self.db = db
        
    async def create_template(self, name: str, pattern: Dict[str, Any], 
                            metadata: Dict[str, Any] = None) -> str:
        """Create a new template"""
        template_id = str(_ulid.ulid())
        
        query = """
        INSERT INTO templates (id, name, pattern, metadata, created_at)
        VALUES ($1, $2, $3, $4, $5)
        """
        
        await self.db.execute(query, [
            template_id,
            name,
            json.dumps(pattern),
            json.dumps(metadata or {}),
            datetime.now()
        ])
        
        print(f"📋 Created template: {name} ({template_id[:8]}...)")
        return template_id
        
    async def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get template by ID"""
        query = """
        SELECT id, name, pattern, metadata, created_at
        FROM templates WHERE id = $1
        """
        
        result = await self.db.fetch_one(query, [template_id])
        if result:
            return {
                "id": result["id"],
                "name": result["name"],
                "pattern": json.loads(result["pattern"]),
                "metadata": json.loads(result["metadata"]),
                "created_at": result["created_at"]
            }
        return None
        
    async def list_templates(self) -> List[Dict[str, Any]]:
        """List all templates"""
        query = """
        SELECT id, name, pattern, metadata, created_at
        FROM templates ORDER BY created_at DESC
        """
        
        results = await self.db.fetch_all(query)
        return [{
            "id": row["id"],
            "name": row["name"],
            "pattern": json.loads(row["pattern"]),
            "metadata": json.loads(row["metadata"]),
            "created_at": row["created_at"]
        } for row in results]

class InstanceManager:
    """Manages instances (concrete objects from templates)"""
    
    def __init__(self, db: Postgre_db):
        self.db = db
        
    async def create_instance(self, template_id: str, name: str, data: Dict[str, Any],
                            metadata: Dict[str, Any] = None) -> str:
        """Create new instance from template"""
        instance_id = str(_ulid.ulid())
        
        query = """
        INSERT INTO instances (id, template_id, name, data, metadata, created_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        """
        
        await self.db.execute(query, [
            instance_id,
            template_id,
            name,
            json.dumps(data),
            json.dumps(metadata or {}),
            datetime.now()
        ])
        
        print(f"🎯 Created instance: {name} ({instance_id[:8]}...) from template {template_id[:8]}...")
        return instance_id
        
    async def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get instance by ID"""
        query = """
        SELECT i.id, i.template_id, i.name, i.data, i.metadata, i.created_at,
               t.name as template_name
        FROM instances i
        LEFT JOIN templates t ON i.template_id = t.id
        WHERE i.id = $1
        """
        
        result = await self.db.fetch_one(query, [instance_id])
        if result:
            return {
                "id": result["id"],
                "template_id": result["template_id"],
                "template_name": result["template_name"],
                "name": result["name"],
                "data": json.loads(result["data"]),
                "metadata": json.loads(result["metadata"]),
                "created_at": result["created_at"]
            }
        return None
        
    async def get_instances_by_template(self, template_id: str) -> List[Dict[str, Any]]:
        """Get all instances created from template"""
        query = """
        SELECT i.id, i.template_id, i.name, i.data, i.metadata, i.created_at,
               t.name as template_name
        FROM instances i
        LEFT JOIN templates t ON i.template_id = t.id
        WHERE i.template_id = $1
        ORDER BY i.created_at DESC
        """
        
        results = await self.db.fetch_all(query, [template_id])
        return [{
            "id": row["id"],
            "template_id": row["template_id"],
            "template_name": row["template_name"],
            "name": row["name"],
            "data": json.loads(row["data"]),
            "metadata": json.loads(row["metadata"]),
            "created_at": row["created_at"]
        } for row in results]

class RelationManager:
    """Manages relations between instances with observer context"""
    
    def __init__(self, db: Postgre_db):
        self.db = db
        
    async def create_relation(self, source_id: str, target_id: str, relation_type: str,
                            observer_context: Dict[str, Any], data: Dict[str, Any] = None,
                            metadata: Dict[str, Any] = None) -> str:
        """Create relation between instances with observer context"""
        relation_id = str(_ulid.ulid())
        
        query = """
        INSERT INTO relations (id, source_id, target_id, relation_type, 
                             observer_context, data, metadata, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """
        
        await self.db.execute(query, [
            relation_id,
            source_id,
            target_id,
            relation_type,
            json.dumps(observer_context),
            json.dumps(data or {}),
            json.dumps(metadata or {}),
            datetime.now()
        ])
        
        print(f"🔗 Created relation: {source_id[:8]}... -> {target_id[:8]}... ({relation_type})")
        return relation_id
        
    async def get_relation(self, relation_id: str) -> Optional[Dict[str, Any]]:
        """Get relation by ID"""
        query = """
        SELECT r.id, r.source_id, r.target_id, r.relation_type,
               r.observer_context, r.data, r.metadata, r.created_at,
               s.name as source_name, t.name as target_name
        FROM relations r
        LEFT JOIN instances s ON r.source_id = s.id
        LEFT JOIN instances t ON r.target_id = t.id
        WHERE r.id = $1
        """
        
        result = await self.db.fetch_one(query, [relation_id])
        if result:
            return {
                "id": result["id"],
                "source_id": result["source_id"],
                "target_id": result["target_id"],
                "source_name": result["source_name"],
                "target_name": result["target_name"],
                "relation_type": result["relation_type"],
                "observer_context": json.loads(result["observer_context"]),
                "data": json.loads(result["data"]),
                "metadata": json.loads(result["metadata"]),
                "created_at": result["created_at"]
            }
        return None
        
    async def get_relations_for_instance(self, instance_id: str, 
                                       observer_filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get relations for instance, optionally filtered by observer context"""
        base_query = """
        SELECT r.id, r.source_id, r.target_id, r.relation_type,
               r.observer_context, r.data, r.metadata, r.created_at,
               s.name as source_name, t.name as target_name
        FROM relations r
        LEFT JOIN instances s ON r.source_id = s.id
        LEFT JOIN instances t ON r.target_id = t.id
        WHERE (r.source_id = $1 OR r.target_id = $1)
        """
        
        results = await self.db.fetch_all(base_query, [instance_id])
        
        relations = []
        for row in results:
            relation = {
                "id": row["id"],
                "source_id": row["source_id"],
                "target_id": row["target_id"],
                "source_name": row["source_name"],
                "target_name": row["target_name"],
                "relation_type": row["relation_type"],
                "observer_context": json.loads(row["observer_context"]),
                "data": json.loads(row["data"]),
                "metadata": json.loads(row["metadata"]),
                "created_at": row["created_at"]
            }
            
            # Filter by observer context if provided
            if observer_filter:
                observer_context = relation["observer_context"]
                matches = all(observer_context.get(k) == v for k, v in observer_filter.items())
                if matches:
                    relations.append(relation)
            else:
                relations.append(relation)
                
        return relations

class ThreeTableSystem:
    """
    Main system managing templates, instances, and relations
    """
    
    def __init__(self, db: Postgre_db):
        self.db = db
        self.templates = TemplateManager(db)
        self.instances = InstanceManager(db)
        self.relations = RelationManager(db)
        
    async def initialize_tables(self):
        """Create necessary tables"""
        
        # Templates table
        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS templates (
            id VARCHAR(50) PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            pattern JSONB NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Instances table
        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS instances (
            id VARCHAR(50) PRIMARY KEY,
            template_id VARCHAR(50) REFERENCES templates(id),
            name VARCHAR(255) NOT NULL,
            data JSONB NOT NULL,
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Relations table
        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS relations (
            id VARCHAR(50) PRIMARY KEY,
            source_id VARCHAR(50) REFERENCES instances(id),
            target_id VARCHAR(50) REFERENCES instances(id),
            relation_type VARCHAR(100) NOT NULL,
            observer_context JSONB NOT NULL,
            data JSONB DEFAULT '{}',
            metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Indexes for performance
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_instances_template ON instances(template_id)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_relations_source ON relations(source_id)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_relations_target ON relations(target_id)")
        await self.db.execute("CREATE INDEX IF NOT EXISTS idx_relations_type ON relations(relation_type)")
        
        print("✅ Three-table system initialized")
        
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        templates_count = await self.db.fetch_value("SELECT COUNT(*) FROM templates")
        instances_count = await self.db.fetch_value("SELECT COUNT(*) FROM instances")  
        relations_count = await self.db.fetch_value("SELECT COUNT(*) FROM relations")
        
        return {
            "architecture": "three_table",
            "templates_count": templates_count,
            "instances_count": instances_count,
            "relations_count": relations_count,
            "timestamp": datetime.now().isoformat()
        }
