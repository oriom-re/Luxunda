
"""
LuxDB Models
===========

Modele danych dla systemu LuxDB.
"""

from .soul import Soul
from .being import Being
# Relationship model moved to legacy - remove import

__all__ = ["Soul", "Being"]
