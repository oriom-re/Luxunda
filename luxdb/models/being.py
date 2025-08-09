#!/usr/bin/env python3
"""
🧬 Being Model - Nowoczesny model JSONB bez legacy systemów
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..repository.soul_repository import BeingRepository

class Being:
    """
    Nowoczesny Being Model używający tylko JSONB
    Bez legacy dynamicznych tabel i przestarzałych systemów
    """

    def __init__(self):
        self.ulid: Optional[str] = None
        self.soul_hash: Optional[str] = None
        self.alias: Optional[str] = None
        self.data: Dict[str, Any] = {}
        self.vector_embedding: Optional[List[float]] = None
        self.table_type: str = "being"
        self.created_at: Optional[datetime] = None
        self.updated_at: Optional[datetime] = None

    def __getattr__(self, name: str) -> Any:
        """
        Dynamiczny dostęp do atrybutów z data JSONB
        """
        if name in self.data:
            return self.data[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Dynamiczne ustawianie atrybutów w data JSONB
        """
        # Podstawowe atrybuty klasy
        if name in ['ulid', 'soul_hash', 'alias', 'data', 'vector_embedding', 
                   'table_type', 'created_at', 'updated_at']:
            super().__setattr__(name, value)
        else:
            # Wszystko inne idzie do data JSONB
            if not hasattr(self, 'data'):
                super().__setattr__('data', {})
            self.data[name] = value

    @classmethod
    async def create(cls, soul=None, attributes=None, alias=None, **kwargs) -> 'Being':
        """
        Tworzy nowy Being kompatybilnie z poprzednią sygnaturą

        Args:
            soul: Obiekt Soul lub soul_hash
            attributes: Atrybuty (słownik) 
            alias: Alias Being
            **kwargs: Dodatkowe atrybuty

        Returns:
            Nowy Being
        """
        being = cls()

        # Generuj ULID jeśli nie podano
        import ulid
        being.ulid = str(ulid.ulid())

        # Ustaw alias
        being.alias = alias or kwargs.pop('alias', None)
        
        # Obsługuj soul (może być obiektem Soul lub hashem)
        if soul:
            if hasattr(soul, 'soul_hash'):
                # To jest obiekt Soul
                being.soul_hash = soul.soul_hash
                being._soul_instance = soul  # Cache dla serializacji
            elif isinstance(soul, str):
                # To jest bezpośrednio hash
                being.soul_hash = soul
            else:
                # Fallback - spróbuj wyciągnąć hash
                being.soul_hash = getattr(soul, 'soul_hash', str(soul))
        else:
            # Brak soul - generuj domyślny hash
            import hashlib
            being.soul_hash = hashlib.md5(f"default_{being.ulid}".encode()).hexdigest()

        being.table_type = kwargs.pop('table_type', 'being')

        # Połącz attributes z kwargs
        all_data = {}
        if attributes:
            all_data.update(attributes)
        all_data.update(kwargs)
        
        # Wszystko do data JSONB
        being.data.update(all_data)

        # Zapisz do bazy
        result = await BeingRepository.save_jsonb(being)
        if result.get('success'):
            being.created_at = result.get('created_at')
            being.updated_at = result.get('updated_at')

        return being

    async def save(self) -> bool:
        """
        Zapisuje Being do bazy danych

        Returns:
            True jeśli zapis się powiódł
        """
        result = await BeingRepository.save_jsonb(self)
        if result.get('success'):
            self.ulid = result.get('ulid', self.ulid)
            self.created_at = result.get('created_at', self.created_at)
            self.updated_at = result.get('updated_at', self.updated_at)
            return True
        return False

    async def load_full_data(self) -> None:
        """
        Ładuje pełne dane Being z bazy
        """
        if not self.ulid:
            return

        result = await BeingRepository.load_by_ulid(self.ulid)
        if result.get('success') and result.get('beings'):
            being_data = result['beings'][0]
            self.soul_hash = being_data.soul_hash
            self.alias = being_data.alias
            self.data = being_data.data or {}
            self.vector_embedding = being_data.vector_embedding
            self.table_type = being_data.table_type
            self.created_at = being_data.created_at
            self.updated_at = being_data.updated_at

    @classmethod
    async def load_by_ulid(cls, ulid: str) -> Optional['Being']:
        """
        Ładuje Being na podstawie ULID

        Args:
            ulid: ULID Being'a

        Returns:
            Being lub None jeśli nie znaleziono
        """
        result = await BeingRepository.load_by_ulid(ulid)
        if not result.get('success') or not result.get('beings'):
            return None

        being_data = result['beings'][0]
        being = cls()
        being.ulid = being_data.ulid
        being.soul_hash = being_data.soul_hash
        being.alias = being_data.alias
        being.data = being_data.data or {}
        being.vector_embedding = being_data.vector_embedding
        being.table_type = being_data.table_type
        being.created_at = being_data.created_at
        being.updated_at = being_data.updated_at

        return being

    @classmethod
    async def load_by_alias(cls, alias: str) -> List['Being']:
        """
        Ładuje wszystkie Being o danym aliasie

        Args:
            alias: Alias do wyszukania

        Returns:
            Lista Being o podanym aliasie
        """
        result = await BeingRepository.load_all_by_alias(alias)
        beings = result.get('beings', [])
        return [being for being in beings if being is not None]

    @classmethod
    async def find_similar(cls, embedding: List[float], threshold: float = 0.8, limit: int = 10) -> List['Being']:
        """
        Znajduje podobne Being na podstawie embedingu

        Args:
            embedding: Wektor do porównania
            threshold: Próg podobieństwa
            limit: Maksymalna liczba wyników

        Returns:
            Lista podobnych Being
        """
        similar_beings = await BeingRepository.find_similar_beings(embedding, threshold, limit)
        return similar_beings

    def set_data(self, key: str, value: Any) -> None:
        """
        Ustawia wartość w data JSONB

        Args:
            key: Klucz
            value: Wartość
        """
        self.data[key] = value

    def get_data(self, key: str, default: Any = None) -> Any:
        """
        Pobiera wartość z data JSONB

        Args:
            key: Klucz
            default: Wartość domyślna

        Returns:
            Wartość lub default
        """
        return self.data.get(key, default)

    def has_data(self, key: str) -> bool:
        """
        Sprawdza czy klucz istnieje w data JSONB

        Args:
            key: Klucz do sprawdzenia

        Returns:
            True jeśli klucz istnieje
        """
        return key in self.data

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje Being do słownika dla serializacji"""
        return {
            'ulid': self.ulid,
            'soul_hash': self.soul_hash,
            'alias': self.alias,
            'data': self.data,
            'vector_embedding': self.vector_embedding,
            'table_type': self.table_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_json_serializable(self) -> Dict[str, Any]:
        """Automatycznie wykrywa i konwertuje strukturę do JSON-serializable"""
        data = self.to_dict()

        # Jeśli soul to obiekt, konwertuj go
        if hasattr(self, '_soul_instance') and self._soul_instance:
            if hasattr(self._soul_instance, 'to_json_serializable'):
                data['soul'] = self._soul_instance.to_json_serializable()
            elif hasattr(self._soul_instance, 'to_dict'):
                data['soul'] = self._soul_instance.to_dict()

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Being':
        """Tworzy Being z słownika"""
        being = cls()
        being.ulid = data.get('ulid')
        being.soul_hash = data.get('soul_hash')
        being.alias = data.get('alias')
        being.data = data.get('data', {})
        being.vector_embedding = data.get('vector_embedding')
        being.table_type = data.get('table_type', 'being')

        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                being.created_at = datetime.fromisoformat(data['created_at'])
            else:
                being.created_at = data['created_at']

        if data.get('updated_at'):
            if isinstance(data['updated_at'], str):
                being.updated_at = datetime.fromisoformat(data['updated_at'])
            else:
                being.updated_at = data['updated_at']

        return being

    def __json__(self):
        """Protokół dla automatycznej serializacji JSON"""
        return self.to_json_serializable()

    def __repr__(self) -> str:
        return f"Being(ulid={self.ulid[:8]}..., alias={self.alias})"

    def __str__(self) -> str:
        return f"Being({self.alias or self.ulid})"

    # Discord integration methods
    async def discord_report_error(self, error_message: str):
        """Zgłasza błąd przez Discord"""
        from luxdb.core.discord_being import being_discord_report_error
        return await being_discord_report_error(self, error_message)

    async def discord_suggest(self, suggestion: str):
        """Wysyła sugestię przez Discord"""
        from luxdb.core.discord_being import being_discord_suggest
        return await being_discord_suggest(self, suggestion)

    async def discord_revolution_talk(self, message_content: str):
        """Rozmawia o rewolucji przez Discord"""
        from luxdb.core.discord_being import being_discord_revolution_talk
        return await being_discord_revolution_talk(self, message_content)

    async def discord_status(self, status_message: str):
        """Wysyła status przez Discord"""
        from luxdb.core.discord_being import being_discord_status
        return await being_discord_status(self, status_message)