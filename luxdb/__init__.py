"""
LuxOS v1.0.0 - Unified System
Main entry point for the LuxDB system
"""

__version__ = "1.0.0"
__author__ = "LuxDB Team"
__email__ = "contact@luxdb.dev"

# Core imports
from .core.luxdb import LuxDB
from .models.soul import Soul
from .models.being import Being
from .core.session_data_manager import GlobalSessionRegistry
from .core.three_table_system import ThreeTableSystem

__all__ = [
    # Core classes
    "LuxDB",
    "Soul",
    "Being",
    "GlobalSessionRegistry",
    "ThreeTableSystem",
]

# Configuration
DEFAULT_CONFIG = {
    "connection_pool_size": 5,
    "connection_timeout": 30,
    "enable_logging": True,
    "auto_create_tables": True,
    "vector_dimensions": 1536,
}