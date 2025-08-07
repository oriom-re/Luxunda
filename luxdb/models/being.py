
"""
Model Being (Byt) dla LuxDB.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
import ulid

from ..core.globals import Globals
from .soul import Soul

@dataclass
class Being:
    """
    Being reprezentuje instancję danych utworzoną na podstawie Soul (genotypu).
    
    Każdy Being ma unikalny ULID i jest powiązany z konkretnym Soul.
    """
    
    ulid: str = field(default_factory=lambda: str(ulid.ulid()))
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    soul_hash: Optional[str] = None
    alias: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    genotype: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    async def create(cls, soul: Soul, data: Dict[str, Any], alias: str = None) -> 'Being':
        """
        Tworzy nowy Being na podstawie Soul i danych.
        
        Args:
            soul: Soul (genotyp) na podstawie którego tworzy się Being
            data: Dane dla nowego Being
            alias: Opcjonalny alias
            
        Returns:
            Nowy obiekt Being
            
        Example:
            ```python
            user_data = {
                "name": "Jan Kowalski",
                "email": "jan@example.com",
                "age": 30
            }
            being = await Being.create(user_soul, user_data)
            ```
        """
        from ..repository.being_repository import BeingRepository
        from ..repository.dynamic_repository import DynamicRepository
        
        # Walidacja danych względem genotypu
        errors = soul.validate_data(data)
        if errors:
            raise ValueError(f"Data validation errors: {', '.join(errors)}")
        
        # Tworzenie Being
        being = cls(
            ulid=str(ulid.ulid()),
            soul_hash=soul.soul_hash,
            genotype=soul.genotype,
            alias=alias
        )
        
        # Zastosowanie genotypu (dynamiczne pola)
        being._apply_genotype(soul.genotype)
        
        # Ustawienie danych
        for key, value in data.items():
            setattr(being, key, value)
        
        # Zapis do bazy danych
        await DynamicRepository.insert_data_transaction(being, soul.genotype)
        
        return being

    def _apply_genotype(self, genotype: dict):
        """
        Dynamicznie dodaje pola z genotypu do obiektu Being.
        
        Args:
            genotype: Definicja genotypu
        """
        from dataclasses import make_dataclass, field
        
        fields = []
        type_map = {
            "str": str, 
            "int": int, 
            "bool": bool, 
            "float": float, 
            "dict": dict, 
            "List[str]": list, 
            "List[float]": list
        }

        attributes = genotype.get("attributes", {})
        for name, meta in attributes.items():
            type_name = meta.get("py_type", "str")
            py_type = type_map.get(type_name, str)
            fields.append((name, py_type, field(default=None)))

        if fields:  # tylko jeśli są jakieś pola do dodania
            DynamicBeing = make_dataclass(
                cls_name="DynamicBeing",
                fields=fields,
                bases=(self.__class__,),
                frozen=False
            )
            self.__class__ = DynamicBeing

    @classmethod
    async def load_by_ulid(cls, ulid: str) -> Optional['Being']:
        """
        Ładuje Being po ULID.
        
        Args:
            ulid: Unikalny identyfikator Being
            
        Returns:
            Being lub None jeśli nie znaleziono
        """
        from ..repository.being_repository import BeingRepository
        
        result = await BeingRepository.load_by_ulid(ulid)
        return result.get('being') if result.get('success') else None

    @classmethod
    async def load_all_by_soul_hash(cls, soul_hash: str) -> List['Being']:
        """
        Ładuje wszystkie Being dla danego Soul.
        
        Args:
            soul_hash: Hash Soul (genotypu)
            
        Returns:
            Lista Being
        """
        from ..repository.being_repository import BeingRepository
        
        result = await BeingRepository.load_all_by_soul_hash(soul_hash)
        beings = result.get('beings', [])
        return [being for being in beings if being is not None]

    @classmethod
    async def load_all(cls) -> List['Being']:
        """
        Ładuje wszystkie Being z bazy danych.
        
        Returns:
            Lista wszystkich Being
        """
        from ..repository.being_repository import BeingRepository
        
        result = await BeingRepository.load_all()
        beings = result.get('beings', [])
        return [being for being in beings if being is not None]

    @classmethod
    async def load_all_by_alias(cls, alias: str) -> List['Being']:
        """
        Ładuje wszystkie Being o danym aliasie.
        
        Args:
            alias: Alias do wyszukania
            
        Returns:
            Lista Being o podanym aliasie
        """
        from ..repository.being_repository import BeingRepository
        
        result = await BeingRepository.load_all_by_alias(alias)
        beings = result.get('beings', [])
        return [being for being in beings if being is not None]

    async def save(self) -> bool:
        """
        Zapisuje zmiany w Being do bazy danych.
        
        Returns:
            True jeśli zapis się powiódł
        """
        from ..repository.being_repository import BeingRepository
        from ..repository.dynamic_repository import DynamicRepository
        
        # Zapisz podstawowe informacje Being
        result = await BeingRepository.save(self)
        if not result.get('success'):
            return False
            
        # Zapisz dynamiczne atrybuty
        if self.genotype:
            await DynamicRepository.insert_data_transaction(self, self.genotype)
            
        return True

    async def get_attributes(self) -> Dict[str, Any]:
        """
        Pobiera wszystkie atrybuty Being z bazy danych.
        
        Returns:
            Słownik atrybutów
        """
        attributes = {}
        
        try:
            from ..core.connection import ConnectionManager
            # Tutaj można by użyć globalnego managera połączeń
            # Na razie uproszczona implementacja
            
            # W pełnej implementacji należałoby:
            # 1. Pobrać połączenie z puli
            # 2. Wykonać zapytania do tabel attr_*
            # 3. Zebrać wszystkie atrybuty
            
            pass  # Implementacja w przyszłości
            
        except Exception as e:
            print(f"❌ Błąd pobierania atrybutów dla {self.ulid}: {e}")

        return attributes

    async def load_full_data(self) -> None:
        """
        Ładuje pełne dane Being z bazy danych (łącznie z dynamicznymi atrybutami).
        """
        if not self.genotype:
            return
            
        from ..repository.dynamic_repository import DynamicRepository
        
        # Pobierz nazwy atrybutów z genotypu
        attributes = self.genotype.get("attributes", {})
        key_list = list(attributes.keys())
        
        if key_list:
            await DynamicRepository.load_values(self, key_list, self.genotype)

    def to_dict(self) -> Dict[str, Any]:
        """
        Konwertuje Being do słownika.
        
        Returns:
            Słownik reprezentujący Being
        """
        from dataclasses import asdict
        return asdict(self)

    async def discord_report_error(self, error_message: str):
        """Zgłasza błąd przez Discord"""
        from ..core.discord_being import being_discord_report_error
        return await being_discord_report_error(self, error_message)
    
    async def discord_suggest(self, suggestion: str):
        """Wysyła sugestię przez Discord"""
        from ..core.discord_being import being_discord_suggest
        return await being_discord_suggest(self, suggestion)
    
    async def discord_revolution_talk(self, message_content: str):
        """Rozmawia o rewolucji przez Discord"""
        from ..core.discord_being import being_discord_revolution_talk
        return await being_discord_revolution_talk(self, message_content)
    
    async def discord_status(self, status_message: str):
        """Wysyła status przez Discord"""
        from ..core.discord_being import being_discord_status
        return await being_discord_status(self, status_message)

    def __repr__(self):
        return f"Being(ulid={self.ulid[:8]}..., soul_hash={self.soul_hash[:8] if self.soul_hash else None}...)"
