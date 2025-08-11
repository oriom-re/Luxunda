"""
LuxDB Test Suite
================

Complete testing framework for LuxDB library ensuring 100% reliability.
"""

__version__ = "1.0.0"

import sys
import os

# Dodaj katalog główny projektu do ścieżki Pythona
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)