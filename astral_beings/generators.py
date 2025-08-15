
"""
Astral Beings Generators
========================

Generatory do tworzenia różnorodnych astralnych bytów.
"""

import random
from typing import Dict, Any, List, Optional
from .core import SoulTemplate, AstralBeing

class SoulGenerator:
    """Generator szablonów duszy dla astralnych bytów"""
    
    # Predefiniowane archetypy
    ARCHETYPES = {
        "guardian": {
            "base_attributes": {"power": 90, "wisdom": 70, "protection": 95},
            "abilities": ["shield", "heal", "protect", "purify"],
            "description": "Noble guardian of astral realms"
        },
        "mage": {
            "base_attributes": {"power": 85, "wisdom": 95, "intellect": 90},
            "abilities": ["cast_spell", "divine", "transmute", "enchant"],
            "description": "Wise mage wielding astral mysteries"
        },
        "warrior": {
            "base_attributes": {"power": 95, "strength": 90, "courage": 85},
            "abilities": ["strike", "charge", "defend", "intimidate"],
            "description": "Fearless warrior of light and shadow"
        },
        "healer": {
            "base_attributes": {"wisdom": 90, "compassion": 95, "life_force": 85},
            "abilities": ["heal", "restore", "bless", "cure"],
            "description": "Gentle healer channeling life energy"
        },
        "scout": {
            "base_attributes": {"agility": 95, "perception": 90, "stealth": 85},
            "abilities": ["scout", "track", "hide", "observe"],
            "description": "Swift scout exploring astral boundaries"
        },
        "sage": {
            "base_attributes": {"wisdom": 95, "knowledge": 90, "memory": 85},
            "abilities": ["remember", "teach", "prophecy", "analyze"],
            "description": "Ancient sage keeper of astral knowledge"
        }
    }
    
    # Dodatkowe atrybuty do losowania
    EXTRA_ATTRIBUTES = [
        "charisma", "luck", "intuition", "creativity", "patience", 
        "focus", "empathy", "determination", "flexibility", "humor"
    ]
    
    @classmethod
    def create_soul(cls, archetype: str, randomize: bool = False) -> SoulTemplate:
        """
        Tworzy duszę określonego archetypu.
        
        Args:
            archetype: Typ archetypu
            randomize: Czy randomizować wartości atrybutów
            
        Returns:
            Wygenerowany szablon duszy
        """
        if archetype not in cls.ARCHETYPES:
            raise ValueError(f"Unknown archetype: {archetype}. Available: {list(cls.ARCHETYPES.keys())}")
        
        archetype_data = cls.ARCHETYPES[archetype]
        attributes = archetype_data["base_attributes"].copy()
        
        if randomize:
            # Randomizuj wartości +/- 15%
            for attr_name, base_value in attributes.items():
                variation = random.randint(-15, 15)
                attributes[attr_name] = max(10, min(100, base_value + variation))
            
            # Dodaj losowy dodatkowy atrybut
            extra_attr = random.choice(cls.EXTRA_ATTRIBUTES)
            attributes[extra_attr] = random.randint(30, 85)
        
        return SoulTemplate.create(
            archetype=archetype,
            attributes=attributes,
            abilities=archetype_data["abilities"],
            description=archetype_data["description"]
        )
    
    @classmethod
    def create_random_soul(cls) -> SoulTemplate:
        """Tworzy całkowicie losową duszę"""
        archetype = random.choice(list(cls.ARCHETYPES.keys()))
        return cls.create_soul(archetype, randomize=True)
    
    @classmethod
    def create_hybrid_soul(cls, primary_archetype: str, secondary_archetype: str, 
                          mix_ratio: float = 0.7) -> SoulTemplate:
        """
        Tworzy hybrydową duszę z dwóch archetypów.
        
        Args:
            primary_archetype: Główny archetyp (dominujący)
            secondary_archetype: Drugorzędny archetyp  
            mix_ratio: Stosunek mieszania (0.0 = tylko secondary, 1.0 = tylko primary)
        """
        if primary_archetype not in cls.ARCHETYPES or secondary_archetype not in cls.ARCHETYPES:
            raise ValueError("Both archetypes must be valid")
        
        primary_data = cls.ARCHETYPES[primary_archetype]
        secondary_data = cls.ARCHETYPES[secondary_archetype]
        
        # Mieszaj atrybuty
        mixed_attributes = {}
        all_attrs = set(primary_data["base_attributes"].keys()) | set(secondary_data["base_attributes"].keys())
        
        for attr in all_attrs:
            primary_val = primary_data["base_attributes"].get(attr, 50)
            secondary_val = secondary_data["base_attributes"].get(attr, 50)
            mixed_attributes[attr] = int(primary_val * mix_ratio + secondary_val * (1 - mix_ratio))
        
        # Mieszaj zdolności
        mixed_abilities = list(set(primary_data["abilities"] + secondary_data["abilities"]))
        
        return SoulTemplate.create(
            archetype=f"hybrid_{primary_archetype}_{secondary_archetype}",
            attributes=mixed_attributes,
            abilities=mixed_abilities,
            description=f"Hybrid of {primary_archetype} and {secondary_archetype}"
        )


class BeingGenerator:
    """Generator kompletnych astralnych bytów"""
    
    # Predefiniowane imiona dla różnych archetypów
    NAMES = {
        "guardian": ["Auriel", "Seraphel", "Guardion", "Protecta", "Valiant"],
        "mage": ["Mystralion", "Arcanum", "Ethros", "Magicka", "Wisdomus"],
        "warrior": ["Valorian", "Striker", "Bladeon", "Courage", "Victor"],
        "healer": ["Healion", "Vitalis", "Restora", "Blessing", "Mercy"],
        "scout": ["Swifton", "Observa", "Tracker", "Stealth", "Ranger"],
        "sage": ["Wisdom", "Memoria", "Ancient", "Scholar", "Prophet"]
    }
    
    @classmethod
    async def create_being(cls, archetype: str, name: Optional[str] = None, 
                          randomize: bool = False) -> AstralBeing:
        """
        Tworzy kompletnego astralnego bytu.
        
        Args:
            archetype: Typ archetypu
            name: Imię (lub losowe jeśli None)
            randomize: Czy randomizować atrybuty
            
        Returns:
            Gotowy astralny byt
        """
        # Wygeneruj duszę
        soul = SoulGenerator.create_soul(archetype, randomize=randomize)
        
        # Wybierz imię
        if not name:
            available_names = cls.NAMES.get(archetype, ["Astral", "Being", "Entity"])
            name = random.choice(available_names)
        
        # Zmaterializuj bytu
        return await AstralBeing.manifest(soul, name)
    
    @classmethod 
    async def create_random_being(cls) -> AstralBeing:
        """Tworzy całkowicie losowego astralnego bytu"""
        archetype = random.choice(list(SoulGenerator.ARCHETYPES.keys()))
        return await cls.create_being(archetype, randomize=True)
    
    @classmethod
    async def create_party(cls, size: int = 4) -> List[AstralBeing]:
        """
        Tworzy grupę zróżnicowanych astralnych bytów.
        
        Args:
            size: Rozmiar grupy
            
        Returns:
            Lista astralnych bytów
        """
        party = []
        used_archetypes = []
        
        for _ in range(size):
            # Staraj się nie powtarzać archetypów
            available_archetypes = [a for a in SoulGenerator.ARCHETYPES.keys() 
                                  if a not in used_archetypes]
            
            if not available_archetypes:
                available_archetypes = list(SoulGenerator.ARCHETYPES.keys())
                used_archetypes = []
            
            archetype = random.choice(available_archetypes)
            used_archetypes.append(archetype)
            
            being = await cls.create_being(archetype, randomize=True)
            party.append(being)
        
        return party
    
    @classmethod
    async def create_specialized_being(cls, specialization: Dict[str, Any]) -> AstralBeing:
        """
        Tworzy wyspecjalizowanego bytu na podstawie specyfikacji.
        
        Args:
            specialization: Dict z kluczami: archetype, attributes, abilities, name
        """
        archetype = specialization.get('archetype', 'guardian')
        custom_attributes = specialization.get('attributes', {})
        custom_abilities = specialization.get('abilities', [])
        name = specialization.get('name')
        
        # Bazowe atrybuty z archetypu
        base_attributes = SoulGenerator.ARCHETYPES[archetype]["base_attributes"].copy()
        base_abilities = SoulGenerator.ARCHETYPES[archetype]["abilities"].copy()
        
        # Dodaj custom elementy
        base_attributes.update(custom_attributes)
        base_abilities.extend(custom_abilities)
        
        # Utwórz custom duszę
        soul = SoulTemplate.create(
            archetype=archetype,
            attributes=base_attributes, 
            abilities=list(set(base_abilities)),  # usuń duplikaty
            description=specialization.get('description', f"Specialized {archetype}")
        )
        
        # Zmaterializuj
        if not name:
            name = f"Specialized{archetype.title()}"
            
        return await AstralBeing.manifest(soul, name)
