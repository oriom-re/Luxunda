
"""
Instance Factory
================

Professional factory for creating data instances with validation
and enterprise-grade error handling.
"""

from typing import Dict, Any, Optional, List
import ulid
from datetime import datetime

class InstanceFactory:
    """
    Professional factory for creating and managing data instances.
    
    Provides enterprise-grade instance creation with proper validation,
    error handling, and logging.
    """
    
    def __init__(self, database):
        self.database = database
        self.creation_log = []
        
    async def create_instance(self, template_name: str, 
                            data: Dict[str, Any],
                            instance_name: str = None,
                            validate: bool = True) -> 'DataInstance':
        """
        Create new instance with professional validation
        
        Args:
            template_name: Name of template to use
            data: Instance data
            instance_name: Optional instance name
            validate: Whether to validate data against template
            
        Returns:
            DataInstance
            
        Raises:
            ValueError: If template not found or validation fails
            RuntimeError: If creation fails
        """
        # Get template
        template = await self.database.get_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")
            
        # Validate data if requested
        if validate:
            validation_errors = template.validate_instance_data(data)
            if validation_errors:
                raise ValueError(f"Data validation failed: {'; '.join(validation_errors)}")
                
        # Generate instance name if not provided
        if not instance_name:
            instance_name = f"{template_name}_{str(ulid.ulid()).lower()}"
            
        try:
            # Create instance
            instance = await self.database.create_instance(
                template, data, instance_name
            )
            
            # Log creation
            self._log_creation(instance, template, data)
            
            return instance
            
        except Exception as e:
            raise RuntimeError(f"Instance creation failed: {str(e)}")
            
    async def create_batch_instances(self, template_name: str,
                                   data_list: List[Dict[str, Any]],
                                   name_prefix: str = None) -> List['DataInstance']:
        """
        Create multiple instances from same template
        
        Args:
            template_name: Template to use
            data_list: List of data for each instance
            name_prefix: Optional prefix for instance names
            
        Returns:
            List of created instances
        """
        instances = []
        
        for i, data in enumerate(data_list):
            instance_name = f"{name_prefix or template_name}_batch_{i+1}_{str(ulid.ulid()).lower()}"
            
            try:
                instance = await self.create_instance(
                    template_name, data, instance_name
                )
                instances.append(instance)
                
            except Exception as e:
                print(f"⚠️ Failed to create instance {i+1}: {e}")
                # Continue with remaining instances
                
        return instances
        
    def _log_creation(self, instance: 'DataInstance', template, data: Dict[str, Any]):
        """Log instance creation for audit purposes"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "instance_created",
            "instance_id": instance.instance_id,
            "instance_name": instance.instance_name,
            "template_id": template.template_id,
            "template_name": template.template_name,
            "data_size": len(data),
            "validation_passed": True
        }
        
        self.creation_log.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.creation_log) > 1000:
            self.creation_log = self.creation_log[-1000:]
            
    def get_creation_statistics(self) -> Dict[str, Any]:
        """Get factory creation statistics"""
        return {
            "total_created": len(self.creation_log),
            "recent_creations": self.creation_log[-10:],
            "templates_used": list(set(entry["template_name"] for entry in self.creation_log)),
            "factory_status": "operational"
        }
        
    def clear_creation_log(self):
        """Clear creation log"""
        self.creation_log = []
        print("✅ Creation log cleared")
