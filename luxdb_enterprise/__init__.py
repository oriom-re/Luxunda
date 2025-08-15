
"""
LuxDB Enterprise Edition - Professional Template Management System
================================================================

For serious enterprise developers who prefer:
- Templates instead of Souls
- Instances instead of Beings  
- Factories instead of Astral Manifestation
- Processors instead of Magical Functions
- Repositories instead of Mystical Storage

No magic, no spirits, just solid enterprise architecture.
"""

from .core.database import EnterpriseDB
from .models.template import DataTemplate
from .models.instance import DataInstance
from .factories.instance_factory import InstanceFactory

__version__ = "1.0.0-enterprise"
__author__ = "LuxDB Professional Team"

__all__ = [
    "EnterpriseDB",
    "DataTemplate", 
    "DataInstance",
    "InstanceFactory"
]
