
"""
Core Astral Beings Classes
=========================

Podstawowe klasy dla systemu astralnych bytów.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from luxdb.models.soul import Soul
from luxdb.models.being import Being

class SoulTemplate:
    """
    Szablon duszy dla astralnych bytów.
    Prosty interfejs do tworzenia genotypów.
    """
    
    @staticmethod
    def create(archetype: str, attributes: Dict[str, Any], 
               abilities: List[str] = None, description: str = None) -> Soul:
        """
        Tworzy szablon duszy na podstawie archetypu.
        
        Args:
            archetype: Typ archetypu (guardian, mage, warrior, healer, etc.)
            attributes: Atrybuty duszy (power, wisdom, agility, etc.)
            abilities: Lista zdolności
            description: Opis duszy
            
        Returns:
            Soul object gotowy do manifestacji
        """
        abilities = abilities or []
        
        # Bazowy genotyp astralnego bytu
        genotype = {
            "genesis": {
                "name": f"astral_{archetype}",
                "type": "astral_being",
                "archetype": archetype,
                "version": "1.0.0",
                "description": description or f"Astral {archetype} being",
                "created_at": datetime.now().isoformat()
            },
            
            # Atrybuty astralne
            "attributes": {
                **{f"astral_{key}": {
                    "py_type": type(value).__name__,
                    "default": value,
                    "description": f"Astral {key} attribute"
                } for key, value in attributes.items()},
                
                "manifestation_time": {
                    "py_type": "str", 
                    "default": datetime.now().isoformat(),
                    "description": "When this soul was manifested"
                },
                
                "astral_energy": {
                    "py_type": "int",
                    "default": 100,
                    "description": "Current astral energy level"
                }
            },
            
            # Zdolności astralne
            "capabilities": {
                "archetype": archetype,
                "abilities": abilities,
                "can_channel_energy": True,
                "can_communicate": True,
                "astral_plane_access": True
            }
        }
        
        # Dodaj moduł z podstawowymi funkcjami astralnymi
        if abilities:
            genotype["module_source"] = SoulTemplate._generate_astral_module(archetype, abilities)
        
        return Soul.create(genotype, alias=f"soul_of_{archetype}")

    @staticmethod
    def _generate_astral_module(archetype: str, abilities: List[str]) -> str:
        """Generuje moduł Python z funkcjami astralnymi"""
        
        module_code = f'''
"""
Astral {archetype.title()} Module
Auto-generated astral abilities
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

def init(being_context=None):
    """Initialize astral {archetype}"""
    print(f"✨ Astral {archetype} awakened")
    return {{
        "ready": True,
        "archetype": "{archetype}",
        "awakened_at": datetime.now().isoformat(),
        "astral_plane": "connected"
    }}

async def channel_energy(ability: str, target: str = None, power: int = None, being_context=None):
    """Channel astral energy through specific ability"""
    
    available_abilities = {abilities}
    
    if ability not in available_abilities:
        return {{
            "success": False,
            "error": f"Ability '{{ability}}' not available. Known abilities: {{available_abilities}}"
        }}
    
    # Symuluj kanalizowanie energii astralnej
    energy_cost = power or 10
    current_energy = being_context.get('data', {{}}).get('astral_energy', 100) if being_context else 100
    
    if current_energy < energy_cost:
        return {{
            "success": False,
            "error": "Insufficient astral energy",
            "required": energy_cost,
            "available": current_energy
        }}
    
    # Wykonaj zdolność
    result = {{
        "success": True,
        "ability_used": ability,
        "target": target,
        "energy_cost": energy_cost,
        "remaining_energy": current_energy - energy_cost,
        "effect": f"{{ability}} channeled successfully" + (f" on {{target}}" if target else ""),
        "timestamp": datetime.now().isoformat()
    }}
    
    # Aktualizuj energię w kontekście
    if being_context and 'data' in being_context:
        being_context['data']['astral_energy'] = current_energy - energy_cost
        being_context['data']['last_ability_used'] = ability
    
    return result

async def commune(message: str, being_context=None):
    """Communicate through astral plane"""
    return {{
        "success": True,
        "message_sent": message,
        "astral_echo": f"Astral {archetype} communes: {{message}}",
        "response": "Message resonates through astral plane...",
        "timestamp": datetime.now().isoformat()
    }}

async def meditate(duration: int = 60, being_context=None):
    """Restore astral energy through meditation"""
    energy_restored = min(duration, 50)
    current_energy = being_context.get('data', {{}}).get('astral_energy', 100) if being_context else 100
    new_energy = min(current_energy + energy_restored, 100)
    
    if being_context and 'data' in being_context:
        being_context['data']['astral_energy'] = new_energy
    
    return {{
        "success": True,
        "meditation_duration": duration,
        "energy_restored": energy_restored,
        "current_energy": new_energy,
        "message": f"Astral {archetype} meditated for {{duration}} moments"
    }}

# Główna funkcja execute dla protokołu Soul
async def execute(request=None, being_context=None):
    """Main execution function for astral being"""
    
    if not request:
        return {{
            "success": True,
            "message": "Astral {archetype} ready for commands",
            "available_actions": ["channel_energy", "commune", "meditate"],
            "archetype": "{archetype}",
            "abilities": {abilities}
        }}
    
    action = request.get('action') if isinstance(request, dict) else str(request)
    
    if action == 'channel_energy':
        ability = request.get('ability', 'basic_energy')
        target = request.get('target')
        power = request.get('power')
        return await channel_energy(ability, target, power, being_context)
    
    elif action == 'commune':
        message = request.get('message', 'Greetings from astral plane')
        return await commune(message, being_context)
    
    elif action == 'meditate':
        duration = request.get('duration', 60)
        return await meditate(duration, being_context)
    
    else:
        return {{
            "success": False,
            "error": f"Unknown action: {{action}}",
            "available_actions": ["channel_energy", "commune", "meditate"]
        }}
'''
        
        return module_code


class AstralBeing:
    """
    Klasa reprezentująca zmaterializowany byt astralny.
    Główny interfejs do interakcji z astralnym bytem.
    """
    
    def __init__(self, being: Being):
        self.being = being
        self.soul_template = None
        
    @staticmethod
    async def manifest(soul_template: Soul, name: str, 
                      initial_attributes: Dict[str, Any] = None) -> 'AstralBeing':
        """
        Materializuje astralny byt na podstawie szablonu duszy.
        
        Args:
            soul_template: Szablon duszy do zmaterializowania
            name: Imię astralnego bytu
            initial_attributes: Dodatkowe atrybuty początkowe
            
        Returns:
            Zmaterializowany astralny byt
        """
        
        # Przygotuj atrybuty manifestacji
        manifest_attributes = {
            "astral_name": name,
            "manifestation_time": datetime.now().isoformat(),
            "astral_state": "manifested",
            "energy_level": 100
        }
        
        if initial_attributes:
            manifest_attributes.update(initial_attributes)
        
        # Materializuj Being
        being = await Being.create(
            soul=soul_template,
            alias=f"astral_{name.lower().replace(' ', '_')}",
            attributes=manifest_attributes,
            persistent=True
        )
        
        astral_being = AstralBeing(being)
        astral_being.soul_template = soul_template
        
        print(f"✨ Astral being '{name}' manifested successfully")
        return astral_being
    
    async def channel_power(self, ability: str, **kwargs) -> Dict[str, Any]:
        """Kanalizuje moc astralną przez określoną zdolność"""
        return await self.being.execute_soul_function(
            'channel_energy',
            ability=ability,
            **kwargs
        )
    
    async def commune(self, message: str) -> Dict[str, Any]:
        """Komunikuje się przez astralną płaszczyznę"""
        return await self.being.execute_soul_function('commune', message=message)
    
    async def meditate(self, duration: int = 60) -> Dict[str, Any]:
        """Medytuje aby przywrócić energię astralną"""
        return await self.being.execute_soul_function('meditate', duration=duration)
    
    async def invoke(self, action: str, **params) -> Dict[str, Any]:
        """Uniwersalne wywołanie działania astralnego"""
        return await self.being.execute_soul_function('execute', 
                                                     request={'action': action, **params})
    
    @property
    def name(self) -> str:
        """Imię astralnego bytu"""
        return self.being.data.get('astral_name', self.being.alias)
    
    @property
    def archetype(self) -> str:
        """Archetyp astralnego bytu"""
        soul = asyncio.run(self.being.get_soul())
        return soul.genotype.get('genesis', {}).get('archetype', 'unknown')
    
    @property
    def energy_level(self) -> int:
        """Obecny poziom energii astralnej"""
        return self.being.data.get('astral_energy', 100)
    
    def __str__(self):
        return f"AstralBeing(name='{self.name}', archetype='{self.archetype}', energy={self.energy_level})"
    
    def __repr__(self):
        return self.__str__()
