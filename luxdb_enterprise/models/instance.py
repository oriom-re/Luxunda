
"""
Data Instance Model
==================

Professional wrapper for LuxDB Being functionality
with enterprise naming conventions.
"""

from typing import Dict, Any, Optional
from datetime import datetime

class DataInstance:
    """
    Enterprise Data Instance - concrete data object created from template.
    
    Professional wrapper around LuxDB Being with reliable naming.
    """
    
    def __init__(self, core_being, template=None):
        self.core_being = core_being
        self.template = template
        self._instance_id = core_being.ulid
        self._instance_name = core_being.alias
        
    @property
    def instance_id(self) -> str:
        """Unique instance identifier (ULID)"""
        return self._instance_id
        
    @property
    def instance_name(self) -> Optional[str]:
        """Human-readable instance name"""
        return self._instance_name
        
    @property
    def template_id(self) -> str:
        """ID of template this instance was created from"""
        return self.core_being.soul_hash
        
    @property
    def data(self) -> Dict[str, Any]:
        """Instance data"""
        return self.core_being.data.copy()
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Instance metadata"""
        return {
            "instance_id": self.instance_id,
            "instance_name": self.instance_name,
            "template_id": self.template_id,
            "template_name": self.template.template_name if self.template else None,
            "created_at": self.core_being.created_at.isoformat() if self.core_being.created_at else None,
            "updated_at": self.core_being.updated_at.isoformat() if self.core_being.updated_at else None,
            "access_zone": self.core_being.access_zone,
            "is_persistent": self.core_being.data.get('_persistent', True)
        }
        
    def get_attribute(self, name: str, default=None):
        """Get instance attribute value"""
        return self.data.get(name, default)
        
    def set_attribute(self, name: str, value: Any):
        """Set instance attribute value"""
        self.core_being.data[name] = value
        self.core_being.updated_at = datetime.now()
        
    def update_attributes(self, updates: Dict[str, Any]):
        """Update multiple attributes"""
        self.core_being.data.update(updates)
        self.core_being.updated_at = datetime.now()
        
    async def save(self):
        """Persist instance changes to database"""
        if hasattr(self.core_being, 'save'):
            await self.core_being.save()
            
    async def execute_processor(self, processor_name: str, **parameters) -> Dict[str, Any]:
        """
        Execute template processor on this instance
        
        Args:
            processor_name: Name of processor to execute
            **parameters: Processor parameters
            
        Returns:
            Processor execution result
        """
        result = await self.core_being.execute_soul_function(processor_name, **parameters)
        
        # Convert to enterprise format
        if result.get('success'):
            return {
                "success": True,
                "processor": processor_name,
                "result": result.get('data', {}).get('result'),
                "executed_at": result.get('data', {}).get('executed_at'),
                "instance_info": {
                    "instance_id": self.instance_id,
                    "instance_name": self.instance_name,
                    "template_id": self.template_id
                }
            }
        else:
            return {
                "success": False,
                "processor": processor_name,
                "error": result.get('error'),
                "error_code": result.get('error_code')
            }
            
    def to_dict(self) -> Dict[str, Any]:
        """Export instance to dictionary"""
        return {
            "instance_id": self.instance_id,
            "instance_name": self.instance_name,
            "template_id": self.template_id,
            "data": self.data,
            "metadata": self.metadata
        }
        
    def __str__(self):
        return f"DataInstance(name='{self.instance_name}', id='{self.instance_id}')"
        
    def __repr__(self):
        return self.__str__()
