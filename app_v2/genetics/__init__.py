# app_v2/genetics/__init__.py
"""
Genetics module - system genów i zarządzanie zależnościami
"""

from .gene import Gene
from .gene_registry import GeneRegistry
from .decorators import gene, requires, capability

__all__ = ['Gene', 'GeneRegistry', 'gene', 'requires', 'capability']
