
"""
🧬 LuxDB Core Package - Tylko Soul, bez Being

Główne komponenty:
- Soul: Kompletny model z instancjami 
- Kernel: Zarządzanie systemem
- Database: Persistence layer
"""

from .luxdb import LuxDB
from .simple_kernel import SimpleKernel  
from .intelligent_kernel import IntelligentKernel

# Usuń import unified_kernel - nie istnieje
# from .unified_kernel import unified_kernel

from .postgre_db import Postgre_db
from .access_control import AccessController, access_controller
from .session_data_manager import SessionDataManager
from .genotype_system import GenotypeSystem

__all__ = [
    'LuxDB',
    'SimpleKernel', 
    'IntelligentKernel',
    'Postgre_db',
    'AccessController',
    'access_controller',
    'SessionDataManager',
    'GenotypeSystem'
]
