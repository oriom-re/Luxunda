# app_v2/core/__init__.py
"""
Core module - podstawowe funkcjonalności systemu
"""

from .communication import Communication, IntentRecognizer
from .module_registry import ModuleRegistry

__all__ = ['Communication', 'IntentRecognizer', 'ModuleRegistry']
