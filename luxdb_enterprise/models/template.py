
"""
Data Template Model
==================

Professional wrapper for LuxDB Soul functionality
with enterprise naming conventions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

class DataTemplate:
    """
    Enterprise Data Template - defines structure and behavior for data instances.
    
    Professional wrapper around LuxDB Soul with boring, reliable naming.
    """
    
    def __init__(self, core_soul):
        self.core_soul = core_soul
        self._template_id = core_soul.soul_hash
        self._template_name = core_soul.alias
        
    @property
    def template_id(self) -> str:
        """Unique template identifier (hash-based)"""
        return self._template_id
        
    @property
    def template_name(self) -> str:
        """Human-readable template name"""
        return self._template_name
        
    @property
    def schema(self) -> Dict[str, Any]:
        """Template schema definition"""
        return self.core_soul.genotype.get("attributes", {})
        
    @property
    def metadata(self) -> Dict[str, Any]:
        """Template metadata"""
        return {
            "template_id": self.template_id,
            "template_name": self.template_name,
            "version": self.core_soul.get_version(),
            "created_at": self.core_soul.created_at.isoformat() if self.core_soul.created_at else None,
            "type": "enterprise_template",
            "capabilities": self.core_soul.genotype.get("capabilities", {})
        }
        
    def get_available_processors(self) -> List[str]:
        """List available template processors (wrapper for Soul functions)"""
        return self.core_soul.list_functions()
        
    def get_processor_info(self, processor_name: str) -> Optional[Dict[str, Any]]:
        """Get processor information"""
        func_info = self.core_soul.get_function_info(processor_name)
        if func_info:
            return {
                "processor_name": processor_name,
                "description": func_info.get("description", f"Template processor {processor_name}"),
                "parameters": func_info.get("signature", {}).get("parameters", {}),
                "return_type": func_info.get("signature", {}).get("return_type", "Any"),
                "is_async": func_info.get("is_async", False)
            }
        return None
        
    async def execute_processor(self, processor_name: str, **parameters) -> Dict[str, Any]:
        """
        Execute template processor
        
        Args:
            processor_name: Name of processor to execute
            **parameters: Processor parameters
            
        Returns:
            Processor execution result
        """
        result = await self.core_soul.execute_function(processor_name, **parameters)
        
        # Convert to enterprise format
        if result.get('success'):
            return {
                "success": True,
                "processor": processor_name,
                "result": result.get('data', {}).get('result'),
                "executed_at": result.get('data', {}).get('executed_at'),
                "template_info": {
                    "template_id": self.template_id,
                    "template_name": self.template_name
                }
            }
        else:
            return {
                "success": False,
                "processor": processor_name,
                "error": result.get('error'),
                "error_code": result.get('error_code')
            }
            
    def validate_instance_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate data against template schema
        
        Args:
            data: Data to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        return self.core_soul.validate_data(data)
        
    def to_dict(self) -> Dict[str, Any]:
        """Export template to dictionary"""
        return {
            "template_id": self.template_id,
            "template_name": self.template_name,
            "schema": self.schema,
            "metadata": self.metadata,
            "available_processors": self.get_available_processors()
        }
        
    def __str__(self):
        return f"DataTemplate(name='{self.template_name}', id='{self.template_id[:8]}...')"
        
    def __repr__(self):
        return self.__str__()
