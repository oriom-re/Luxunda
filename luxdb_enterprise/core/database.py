
"""
Enterprise Database Management System
====================================

Professional wrapper around LuxDB core functionality
with enterprise-grade naming conventions.
"""

import asyncio
from typing import Dict, Any, Optional, List
from luxdb.core.luxdb import LuxDB as CoreLuxDB
from luxdb.models.soul import Soul
from luxdb.models.being import Being

class EnterpriseDB:
    """
    Enterprise-grade database management system.
    
    Provides professional interface to LuxDB functionality
    without any mystical or spiritual references.
    """
    
    def __init__(self, host: str, port: int = 5432, 
                 user: str = None, password: str = None, 
                 database: str = "luxdb_enterprise"):
        self.core_db = CoreLuxDB(host, port, user, password, database)
        self.initialized = False
        
    async def initialize(self):
        """Initialize the enterprise database system"""
        await self.core_db.initialize()
        self.initialized = True
        print("✅ Enterprise Database System initialized")
        
    async def create_template(self, schema: Dict[str, Any], 
                            template_name: str) -> 'DataTemplate':
        """
        Create a new data template (enterprise wrapper for Soul)
        
        Args:
            schema: Data structure definition
            template_name: Professional template identifier
            
        Returns:
            DataTemplate instance
        """
        from ..models.template import DataTemplate
        
        # Convert enterprise schema to Soul genotype
        genotype = {
            "genesis": {
                "name": template_name,
                "type": "enterprise_template",
                "version": "1.0.0",
                "created_by": "enterprise_system"
            },
            "attributes": schema.get("properties", {}),
            "capabilities": {
                "enterprise_grade": True,
                "production_ready": True,
                "scalable": True
            }
        }
        
        # Create underlying Soul
        soul = await Soul.create(genotype, alias=template_name)
        
        # Return enterprise wrapper
        return DataTemplate(soul)
        
    async def create_instance(self, template: 'DataTemplate', 
                            data: Dict[str, Any],
                            instance_name: str = None) -> 'DataInstance':
        """
        Create a new data instance from template
        
        Args:
            template: Source template
            data: Instance data
            instance_name: Optional instance identifier
            
        Returns:
            DataInstance
        """
        from ..models.instance import DataInstance
        
        # Create underlying Being
        being = await Being.create(
            template.core_soul, 
            attributes=data,
            alias=instance_name
        )
        
        return DataInstance(being, template)
        
    async def get_template(self, template_name: str) -> Optional['DataTemplate']:
        """Retrieve template by name"""
        from ..models.template import DataTemplate
        
        soul = await Soul.get_by_alias(template_name)
        return DataTemplate(soul) if soul else None
        
    async def list_templates(self) -> List['DataTemplate']:
        """List all available templates"""
        from ..models.template import DataTemplate
        
        souls = await Soul.get_all()
        return [DataTemplate(soul) for soul in souls]
        
    async def get_instance(self, instance_id: str) -> Optional['DataInstance']:
        """Retrieve instance by ID"""
        from ..models.instance import DataInstance
        
        being = await Being._get_by_ulid_internal(instance_id)
        if being:
            template_soul = await being.get_soul()
            template = DataTemplate(template_soul) if template_soul else None
            return DataInstance(being, template)
        return None
        
    async def execute_template_processor(self, template_name: str, 
                                       processor_name: str,
                                       **parameters) -> Dict[str, Any]:
        """
        Execute template processor (enterprise wrapper for Soul functions)
        """
        template = await self.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
            
        return await template.execute_processor(processor_name, **parameters)
        
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get enterprise system statistics"""
        return {
            "system_name": "LuxDB Enterprise Edition",
            "version": "1.0.0-enterprise",
            "status": "operational" if self.initialized else "not_initialized",
            "architecture": "template_instance_pattern",
            "compliance": {
                "enterprise_grade": True,
                "no_mystical_references": True,
                "professional_naming": True,
                "boring_but_reliable": True
            }
        }
