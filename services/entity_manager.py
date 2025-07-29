# app_v2/services/entity_manager.py
"""
Zarządza tworzeniem i ładowaniem bytów
"""

from typing import Dict, Any, Optional
import uuid
from datetime import datetime

class EntityManager:
    """Zarządza tworzeniem i ładowaniem bytów"""
    
    _entities: Dict[str, Any] = {}  # Cache aktywnych bytów
    
    @classmethod
    async def create_or_load(cls, alias: str, genotype_template: str = None, 
                           force_new: bool = False, version: str = "latest"):
        """
        Uniwersalna funkcja - tworzy nowego lub ładuje istniejącego byt
        
        Args:
            alias: Unikalny alias bytu
            genotype_template: Nazwa szablonu genotypu do użycia
            force_new: Czy zawsze tworzyć nowego (True) czy użyć istniejącego (False)
            version: Wersja genotypu do użycia
        """
        # Sprawdź cache aktywnych bytów
        if not force_new and alias in cls._entities:
            print(f"🔍 Znaleziono aktywny byt o aliasie: {alias}")
            return cls._entities[alias]
        
        # Sprawdź bazę danych czy byt już istnieje
        if not force_new:
            existing_entity = await cls._find_entity_by_alias(alias)
            if existing_entity:
                print(f"🔍 Ładowanie istniejącego bytu: {alias}")
                entity = await cls._load_entity_from_soul(existing_entity)
                if entity:
                    cls._entities[alias] = entity
                    return entity
        
        # Twórz nowego byt
        if genotype_template:
            print(f"🆕 Tworzenie nowego bytu: {alias} na podstawie {genotype_template}")
            entity = await cls._create_new_entity(alias, genotype_template, version)
            if entity:
                cls._entities[alias] = entity
                await entity.save()  # Zapisz do bazy danych
                return entity
        
        print(f"❌ Nie udało się utworzyć/załadować bytu: {alias}")
        return None
    
    @classmethod
    async def _find_entity_by_alias(cls, alias: str) -> Optional[Dict[str, Any]]:
        """Szuka bytu w bazie danych po aliasie"""
        from app_v2.database.soul_repository import SoulRepository
        
        # Sprawdź w atrybutach
        soul = await SoulRepository.get_by_field("alias", alias)
        if soul:
            return soul
        
        # Sprawdź w nazwie
        soul = await SoulRepository.get_by_name(alias)
        return soul
    
    @classmethod
    async def _load_entity_from_soul(cls, soul: Dict[str, Any]):
        """Ładuje byt z soul z bazy danych"""
        try:
            from app_v2.beings.genotype import Genotype
            
            entity = Genotype(
                uid=soul["uid"],
                genesis=soul["genesis"],
                attributes=soul["attributes"],
                memories=soul["memories"],
                self_awareness=soul["self_awareness"]
            )
            
            # Załaduj genotypy tego bytu
            loaded_genotypes = soul["genesis"].get("loaded_genotypes", [])
            for genotype_name in loaded_genotypes:
                await entity.load_and_run_genotype(genotype_name, call_init=False)
            
            return entity
        except Exception as e:
            print(f"❌ Błąd podczas ładowania bytu: {e}")
            return None
    
    @classmethod
    async def _create_new_entity(cls, alias: str, genotype_template: str, version: str):
        """Tworzy nowego byt na podstawie szablonu genotypu"""
        try:
            from app_v2.beings.genotype import Genotype
            
            # Stwórz podstawową strukturę bytu
            genesis = {
                "name": alias,
                "alias": alias,
                "template": genotype_template,
                "version": version,
                "created_at": datetime.now().isoformat(),
                "loaded_genotypes": []
            }
            
            attributes = {
                "status": "active",
                "creation_method": "template",
                "template_used": genotype_template
            }
            
            entity = Genotype(
                uid=str(uuid.uuid4()),
                genesis=genesis,
                attributes=attributes,
                memories=[],
                self_awareness={}
            )
            
            # Załaduj genotyp szablonu
            template_module = await entity.load_and_run_genotype(genotype_template, call_init=True)
            if template_module:
                entity.genesis["loaded_genotypes"].append(genotype_template)
            
            return entity
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia nowego bytu: {e}")
            return None
