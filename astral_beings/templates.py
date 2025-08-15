
"""
Basic Templates for Astral Beings
=================================

Gotowe szablony i predefiniowane konfiguracje dla typowych przypadków użycia.
"""

from typing import Dict, Any, List
from .core import SoulTemplate, AstralBeing
from .generators import SoulGenerator, BeingGenerator

class BasicTemplates:
    """Kolekcja podstawowych szablonów astralnych bytów"""
    
    @staticmethod
    def get_guardian_template() -> Dict[str, Any]:
        """Szablon dla bytu strażnika"""
        return {
            "archetype": "guardian",
            "attributes": {
                "protection_power": 95,
                "wisdom": 75,
                "loyalty": 100,
                "vigilance": 90
            },
            "abilities": ["shield", "protect", "guard", "watch", "defend"],
            "name": "Guardian",
            "description": "A noble protector of sacred spaces"
        }
    
    @staticmethod
    def get_assistant_template() -> Dict[str, Any]:
        """Szablon dla bytu asystenta"""
        return {
            "archetype": "sage", 
            "attributes": {
                "helpfulness": 95,
                "knowledge": 85,
                "patience": 90,
                "efficiency": 80
            },
            "abilities": ["assist", "organize", "remember", "calculate", "advise"],
            "name": "Assistant",
            "description": "A helpful digital assistant being"
        }
    
    @staticmethod
    def get_messenger_template() -> Dict[str, Any]:
        """Szablon dla bytu posłańca"""
        return {
            "archetype": "scout",
            "attributes": {
                "speed": 90,
                "reliability": 95,
                "communication": 85,
                "discretion": 80
            },
            "abilities": ["deliver", "transmit", "relay", "notify", "connect"],
            "name": "Messenger",
            "description": "Swift bearer of messages and information"
        }
    
    @staticmethod
    def get_healer_template() -> Dict[str, Any]:
        """Szablon dla bytu uzdrowiciela"""
        return {
            "archetype": "healer",
            "attributes": {
                "compassion": 100,
                "healing_power": 90,
                "empathy": 95,
                "gentleness": 85
            },
            "abilities": ["heal", "restore", "comfort", "cure", "rejuvenate"],
            "name": "Healer",
            "description": "Gentle being focused on healing and restoration"
        }
    
    @staticmethod
    def get_scholar_template() -> Dict[str, Any]:
        """Szablon dla bytu uczonego"""
        return {
            "archetype": "sage",
            "attributes": {
                "intelligence": 95,
                "curiosity": 90,
                "memory": 100,
                "analysis": 85
            },
            "abilities": ["research", "analyze", "learn", "teach", "document"],
            "name": "Scholar", 
            "description": "Dedicated seeker and keeper of knowledge"
        }
    
    @classmethod
    async def create_guardian(cls, name: str = None) -> AstralBeing:
        """Tworzy gotowego strażnika"""
        template = cls.get_guardian_template()
        return await BeingGenerator.create_specialized_being({
            **template,
            "name": name or template["name"]
        })
    
    @classmethod
    async def create_assistant(cls, name: str = None) -> AstralBeing:
        """Tworzy gotowego asystenta"""
        template = cls.get_assistant_template()
        return await BeingGenerator.create_specialized_being({
            **template,
            "name": name or template["name"]
        })
    
    @classmethod
    async def create_messenger(cls, name: str = None) -> AstralBeing:
        """Tworzy gotowego posłańca"""
        template = cls.get_messenger_template()
        return await BeingGenerator.create_specialized_being({
            **template,
            "name": name or template["name"]
        })
    
    @classmethod
    async def create_healer(cls, name: str = None) -> AstralBeing:
        """Tworzy gotowego uzdrowiciela"""
        template = cls.get_healer_template()
        return await BeingGenerator.create_specialized_being({
            **template,
            "name": name or template["name"]
        })
    
    @classmethod
    async def create_scholar(cls, name: str = None) -> AstralBeing:
        """Tworzy gotowego uczonego"""
        template = cls.get_scholar_template()
        return await BeingGenerator.create_specialized_being({
            **template,
            "name": name or template["name"]
        })
    
    @classmethod
    def list_templates(cls) -> List[Dict[str, Any]]:
        """Lista wszystkich dostępnych szablonów"""
        return [
            cls.get_guardian_template(),
            cls.get_assistant_template(), 
            cls.get_messenger_template(),
            cls.get_healer_template(),
            cls.get_scholar_template()
        ]
    
    @classmethod
    def get_template_by_name(cls, template_name: str) -> Dict[str, Any]:
        """Pobiera szablon po nazwie"""
        templates = {
            "guardian": cls.get_guardian_template,
            "assistant": cls.get_assistant_template,
            "messenger": cls.get_messenger_template,
            "healer": cls.get_healer_template,
            "scholar": cls.get_scholar_template
        }
        
        if template_name not in templates:
            raise ValueError(f"Template '{template_name}' not found. Available: {list(templates.keys())}")
        
        return templates[template_name]()


class AdvancedTemplates:
    """Bardziej zaawansowane szablony astralnych bytów"""
    
    @staticmethod
    def get_ai_companion_template() -> Dict[str, Any]:
        """Szablon dla towarzysza AI"""
        return {
            "archetype": "mage",
            "attributes": {
                "intelligence": 95,
                "creativity": 85,
                "adaptability": 90,
                "learning_ability": 100,
                "emotional_intelligence": 80
            },
            "abilities": [
                "converse", "learn", "adapt", "create", "analyze",
                "empathize", "remember", "suggest", "assist", "inspire"
            ],
            "name": "AI_Companion",
            "description": "Advanced AI companion with learning capabilities"
        }
    
    @staticmethod
    def get_data_guardian_template() -> Dict[str, Any]:
        """Szablon dla strażnika danych"""
        return {
            "archetype": "guardian",
            "attributes": {
                "security": 100,
                "integrity": 95,
                "vigilance": 90,
                "encryption_power": 85,
                "access_control": 90
            },
            "abilities": [
                "encrypt", "decrypt", "validate", "monitor", "protect",
                "backup", "restore", "audit", "secure", "authenticate"
            ],
            "name": "DataGuardian",
            "description": "Protector of digital information and data integrity"
        }
    
    @staticmethod 
    def get_creative_muse_template() -> Dict[str, Any]:
        """Szablon dla muzy kreatywnej"""
        return {
            "archetype": "mage",
            "attributes": {
                "creativity": 100,
                "inspiration": 95,
                "imagination": 90,
                "artistic_vision": 85,
                "innovation": 80
            },
            "abilities": [
                "inspire", "create", "imagine", "design", "compose",
                "paint", "write", "innovate", "brainstorm", "visualize"
            ],
            "name": "CreativeMuse",
            "description": "Inspirational being that sparks creativity and innovation"
        }
