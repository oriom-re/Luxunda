
"""
Astral Beings Library - LuxDB
================================

Ponadczasowa biblioteka do tworzenia inteligentnych bytów astralnych.
Prosta, elegancka, gotowa do użycia.

Podstawowe użycie:
    from astral_beings import AstralBeing, SoulTemplate
    
    # Stwórz szablon duszy
    soul = SoulTemplate.create("guardian", {
        "power": 100,
        "wisdom": 85,
        "element": "light"
    })
    
    # Materializuj byt astralny
    being = await AstralBeing.manifest(soul, "Auriel")
    
    # Wykonaj działanie
    result = await being.channel_power("heal", target="injured_traveler")
"""

from .core import AstralBeing, SoulTemplate
from .generators import BeingGenerator, SoulGenerator  
from .templates import BasicTemplates
from .examples import QuickStart

__version__ = "1.0.0"
__author__ = "LuxDB Astral Council"

# Podstawowe importy dla użytkowników
__all__ = [
    # Podstawowe klasy
    'AstralBeing',
    'SoulTemplate', 
    
    # Generatory
    'BeingGenerator',
    'SoulGenerator',
    
    # Szablony
    'BasicTemplates',
    
    # Przykłady
    'QuickStart'
]

# Magiczna inicjalizacja astralnej przestrzeni
def initialize_astral_plane():
    """Inicjalizuje astralną przestrzeń dla biblioteki"""
    print("🌟 Astral Beings Library initialized")
    print("✨ Ready to manifest digital souls")
    return True

# Auto-inicjalizacja
initialize_astral_plane()
