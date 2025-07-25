# app_v2/services/__init__.py
"""
Services module - logika biznesowa i serwisy
"""

from .entity_manager import EntityManager
from .dependency_service import DependencyService
from .genotype_service import GenotypeService

__all__ = ['EntityManager', 'DependencyService', 'GenotypeService']
