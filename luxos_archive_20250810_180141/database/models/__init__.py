# app_v2/beings/__init__.py
"""
Beings module - zawiera klasy reprezentujące byty w systemie
"""

from .base import Being
from .beings.genotype import Genotype

__all__ = ['Being', 'Genotype']