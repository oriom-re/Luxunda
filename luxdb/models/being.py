#!/usr/bin/env python3
"""
🧬 Being Model - Nowoczesny model JSONB bez legacy systemów
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from ..repository.soul_repository import BeingRepository
from luxdb.utils.serializer import JSONBSerializer
import ulid # Import ulid globally
import time # Import time globally
from dataclasses import dataclass, field # Import dataclass and field
from luxdb.core.globals import Globals # Import Globals

@dataclass
class Being:
    """
    Being reprezentuje instancję bytu - konkretny obiekt utworzony na podstawie Soul.

    Każdy Being:
    - Ma unikalny ULID
    - Odwołuje się do Soul przez hash
    - Zawiera dane w formacie JSONB
    - Ma kontrolę dostępu i TTL
    """

    ulid: str = None
    global_ulid: str = field(default=Globals.GLOBAL_ULID)
    soul_hash: str = None
    alias: str = None
    data: Dict[str, Any] = field(default_factory=dict)
    access_zone: str = "public_zone"  # Domyślnie publiczne
    ttl_expires: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Cache dla Soul (lazy loading z TTL)
    _soul_cache: Optional[Any] = field(default=None, init=False, repr=False)
    _soul_cache_ttl: Optional[float] = field(default=None, init=False, repr=False)

    def __post_init__(self):
        """Inicjalizacja po utworzeniu obiektu"""
        if not self.ulid:
            self.ulid = str(ulid.ulid())
        if not self.created_at:
            self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @classmethod
    async def set(cls, soul, data: Dict[str, Any], alias: str = None,
                  access_zone: str = "public_zone", ttl_hours: int = None) -> Dict[str, Any]:
        """
        Metoda set dla Being zgodna z formatem genetycznym.

        Args:
            soul: Obiekt Soul (genotyp)
            data: Dane bytu
            alias: Opcjonalny alias
            access_zone: Strefa dostępu
            ttl_hours: TTL w godzinach

        Returns:
            Standardowy słownik odpowiedzi z nowym Being
        """
        from luxdb.utils.serializer import GeneticResponseFormat
        
        try:
            being = await cls._create_internal(soul, alias=alias, attributes=data, access_zone=access_zone, ttl_hours=ttl_hours)
            
            soul_context = {
                "soul_hash": being.soul_hash,
                "genotype": soul.genotype if hasattr(soul, 'genotype') else {}
            }
            
            return GeneticResponseFormat.success_response(
                data={"being": being.to_json_serializable()},
                soul_context=soul_context
            )
            
        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=str(e),
                error_code="BEING_SET_ERROR"
            )
    
    @classmethod
    async def _get_by_ulid_internal(cls, ulid_value: str) -> Optional['Being']:
        """Wewnętrzna metoda get_by_ulid zwracająca obiekt Being"""
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.get_by_ulid(ulid_value)
        return result.get('being') if result.get('success') else None
    
    @classmethod
    async def _create_internal(cls, soul_or_hash=None, alias: str = None, attributes: Dict[str, Any] = None, **kwargs) -> 'Being':
        """Wewnętrzna metoda create zwracająca obiekt Being"""

    @classmethod
    async def get(cls, ulid_value: str) -> Dict[str, Any]:
        """
        Standardowa metoda get dla Being zgodna z formatem genetycznym.

        Args:
            ulid_value: ULID bytu

        Returns:
            Standardowy słownik odpowiedzi z Being lub błędem
        """
        from luxdb.utils.serializer import GeneticResponseFormat
        
        try:
            being = await cls._get_by_ulid_internal(ulid_value)
            
            if being:
                # Pobierz kontekst Soul
                soul = await being.get_soul()
                soul_context = {
                    "soul_hash": being.soul_hash,
                    "genotype": soul.genotype if soul else {}
                }
                
                return GeneticResponseFormat.success_response(
                    data={"being": being.to_json_serializable()},
                    soul_context=soul_context
                )
            else:
                return GeneticResponseFormat.error_response(
                    error="Being not found",
                    error_code="BEING_NOT_FOUND"
                )
                
        except Exception as e:
            return GeneticResponseFormat.error_response(
                error=str(e),
                error_code="BEING_GET_ERROR"
            )

    @classmethod
    async def create(cls, soul_or_hash=None, alias: str = None, attributes: Dict[str, Any] = None, force_new: bool = False, soul: 'Soul' = None, soul_hash: str = None) -> 'Being':
        """Tworzy nowy Being na podstawie Soul - z kompatybilnością wsteczną"""

        # Backward compatibility handling
        if soul is not None:
            # New style: create(soul=soul_object, ...)
            target_soul = soul
        elif soul_hash is not None:
            # Legacy style: create(soul_hash="...", ...)
            from ..repository.soul_repository import SoulRepository
            result = await SoulRepository.get_soul_by_hash(soul_hash)
            if not result or not result.get('success'):
                raise ValueError(f"Soul with hash {soul_hash} not found")
            target_soul = result.get('soul')
        elif isinstance(soul_or_hash, str):
            # Legacy style: create("hash_string", ...)
            from ..repository.soul_repository import SoulRepository
            result = await SoulRepository.get_soul_by_hash(soul_or_hash)
            if not result or not result.get('success'):
                raise ValueError(f"Soul with hash {soul_or_hash} not found")
            target_soul = result.get('soul')
        else:
            # New style: create(soul_object, ...)
            target_soul = soul_or_hash

        if not target_soul:
             raise ValueError("Soul object or hash must be provided.")

        being = cls()
        being.soul_hash = target_soul.soul_hash
        being.global_ulid = target_soul.global_ulid
        being.alias = alias or f"being_{being.ulid[:8]}"

        # Walidacja i serializacja danych
        if attributes:
            serialized_data, errors = JSONBSerializer.validate_and_serialize(attributes, target_soul)
            if errors:
                raise ValueError(f"Validation errors: {', '.join(errors)}")
            being.data = serialized_data
        else:
            being.data = {}

        # Ustawienie pozostałych atrybutów z metadanych Soul
        for key, value in target_soul.genotype.items():
            if key != 'attributes':
                setattr(being, key, value)

        # Zapis do bazy danych
        from ..repository.soul_repository import BeingRepository
        await BeingRepository.insert_data_transaction(being, target_soul.genotype)

        # Przypisanie do strefy dostępu
        from ..core.access_control import access_controller
        access_controller.assign_being_to_zone(being.ulid, being.access_zone) # Use the being's access_zone

        return being
    
    async def _create_internal(cls, soul_or_hash=None, alias: str = None, attributes: Dict[str, Any] = None, force_new: bool = False, soul: 'Soul' = None, soul_hash: str = None, access_zone: str = "public_zone", ttl_hours: int = None) -> 'Being':
        """Wewnętrzna metoda create - kopia oryginalnej logiki"""
        # Backward compatibility handling
        if soul is not None:
            target_soul = soul
        elif soul_hash is not None:
            from ..repository.soul_repository import SoulRepository
            result = await SoulRepository.get_soul_by_hash(soul_hash)
            if not result or not result.get('success'):
                raise ValueError(f"Soul with hash {soul_hash} not found")
            target_soul = result.get('soul')
        elif isinstance(soul_or_hash, str):
            from ..repository.soul_repository import SoulRepository
            result = await SoulRepository.get_soul_by_hash(soul_or_hash)
            if not result or not result.get('success'):
                raise ValueError(f"Soul with hash {soul_or_hash} not found")
            target_soul = result.get('soul')
        else:
            target_soul = soul_or_hash

        if not target_soul:
             raise ValueError("Soul object or hash must be provided.")

        being = cls()
        being.soul_hash = target_soul.soul_hash
        being.global_ulid = target_soul.global_ulid
        being.alias = alias or f"being_{being.ulid[:8]}"
        being.access_zone = access_zone

        # Walidacja i serializacja danych
        if attributes:
            from luxdb.utils.serializer import JSONBSerializer
            serialized_data, errors = JSONBSerializer.validate_and_serialize(attributes, target_soul)
            if errors:
                raise ValueError(f"Validation errors: {', '.join(errors)}")
            being.data = serialized_data
        else:
            being.data = {}

        # TTL
        if ttl_hours:
            from datetime import timedelta
            being.ttl_expires = datetime.now() + timedelta(hours=ttl_hours)

        # Zapis do bazy danych
        from ..repository.soul_repository import BeingRepository
        await BeingRepository.insert_data_transaction(being, target_soul.genotype)

        # Przypisanie do strefy dostępu
        from ..core.access_control import access_controller
        access_controller.assign_being_to_zone(being.ulid, being.access_zone)

        return being

    async def get_soul(self):
        """
        Pobiera Soul z cache lub bazy danych (lazy loading z TTL).

        Returns:
            Obiekt Soul
        """
        # Sprawdź cache i TTL
        current_time = time.time()
        if (self._soul_cache and self._soul_cache_ttl and
            current_time < self._soul_cache_ttl):
            return self._soul_cache

        # Załaduj Soul z bazy
        if self.soul_hash:
            from .soul import Soul
            soul = await Soul.get_by_hash(self.soul_hash)

            # Zaktualizuj cache
            if soul:
                self._soul_cache = soul
                self._soul_cache_ttl = current_time + 3600  # 1 godzina TTL

            return soul

        return None

    def check_access(self, user_ulid: str = None, user_session: Dict[str, Any] = None) -> bool:
        """
        Sprawdza czy użytkownik ma dostęp do tego bytu.

        Args:
            user_ulid: ULID użytkownika
            user_session: Sesja użytkownika

        Returns:
            True jeśli ma dostęp
        """
        from ..core.access_control import access_controller
        return access_controller.check_access(self.ulid, user_ulid, user_session)

    def is_expired(self) -> bool:
        """Sprawdza czy byt wygasł (TTL)"""
        if not self.ttl_expires:
            return False
        return datetime.now() > self.ttl_expires

    def extend_ttl(self, hours: int):
        """Przedłuża TTL bytu"""
        if self.ttl_expires:
            self.ttl_expires += timedelta(hours=hours)
        else:
            self.ttl_expires = datetime.now() + timedelta(hours=hours)
        self.updated_at = datetime.now()

    @classmethod
    async def get_by_ulid(cls, ulid_value: str) -> Optional['Being']:
        """
        Ładuje Being po ULID.

        Args:
            ulid_value: ULID bytu

        Returns:
            Being lub None jeśli nie znaleziono
        """
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.get_by_ulid(ulid_value)
        return result.get('being') if result.get('success') else None

    @classmethod
    async def get_by_alias(cls, alias: str) -> List['Being']:
        """
        Ładuje Beings po aliasie.

        Args:
            alias: Alias bytów

        Returns:
            Lista Being
        """
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.get_by_alias(alias)
        beings = result.get('beings', [])
        return [being for being in beings if being is not None]

    @classmethod
    async def get_all(cls, user_ulid: str = None, user_session: Dict[str, Any] = None) -> List['Being']:
        """
        Ładuje wszystkie Being z kontrolą dostępu.

        Args:
            user_ulid: ULID użytkownika (dla kontroli dostępu)
            user_session: Sesja użytkownika

        Returns:
            Lista dostępnych Being
        """
        from ..repository.soul_repository import BeingRepository
        from ..core.access_control import access_controller

        result = await BeingRepository.get_all_beings()
        beings = result.get('beings', [])
        beings = [being for being in beings if being is not None]

        # Filtrowanie według uprawnień dostępu
        return access_controller.filter_accessible_beings(beings, user_ulid, user_session)

    @classmethod
    async def get_by_access_zone(cls, zone_id: str, user_ulid: str = None,
                                user_session: Dict[str, Any] = None) -> List['Being']:
        """
        Pobiera byty z określonej strefy dostępu.

        Args:
            zone_id: ID strefy dostępu
            user_ulid: ULID użytkownika
            user_session: Sesja użytkownika

        Returns:
            Lista dostępnych bytów ze strefy
        """
        from ..repository.soul_repository import BeingRepository
        from ..core.access_control import access_controller

        # Sprawdź czy użytkownik ma dostęp do strefy
        zone = access_controller.zones.get(zone_id)
        if not zone:
            return []

        # Pobierz wszystkie byty i filtruj według strefy
        result = await BeingRepository.get_all_beings()
        beings = result.get('beings', [])
        beings = [being for being in beings if being is not None]

        zone_beings = [being for being in beings if being.access_zone == zone_id]

        # Filtrowanie według uprawnień dostępu
        return access_controller.filter_accessible_beings(zone_beings, user_ulid, user_session)

    async def save(self) -> bool:
        """
        Zapisuje zmiany w Being do bazy danych.

        Returns:
            True jeśli zapis się powiódł
        """
        from ..repository.soul_repository import BeingRepository

        self.updated_at = datetime.now()
        result = await BeingRepository.set(self)
        return result.get('success', False)

    async def delete(self) -> bool:
        """
        Usuwa Being z bazy danych.

        Returns:
            True jeśli usunięcie się powiodło
        """
        from ..repository.soul_repository import BeingRepository

        result = await BeingRepository.delete_being(self.ulid)
        return result.get('success', False)

    def get_attributes(self) -> Dict[str, Any]:
        """Zwraca atrybuty/dane bytu"""
        return self.data

    def set_attribute(self, key: str, value: Any):
        """Ustawia atrybut bytu"""
        self.data[key] = value
        self.updated_at = datetime.now()

    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Pobiera atrybut bytu"""
        return self.data.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Konwertuje Being do słownika dla serializacji"""
        return {
            'ulid': self.ulid,
            'global_ulid': self.global_ulid,
            'soul_hash': self.soul_hash,
            'alias': self.alias,
            'data': self.data,
            'access_zone': self.access_zone,
            'ttl_expires': self.ttl_expires.isoformat() if self.ttl_expires else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def to_json_serializable(self) -> Dict[str, Any]:
        """Automatycznie wykrywa i konwertuje strukturę do JSON-serializable"""
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Being':
        """Tworzy Being z słownika"""
        being = cls()
        being.ulid = data.get('ulid')
        being.global_ulid = data.get('global_ulid', Globals.GLOBAL_ULID)
        being.soul_hash = data.get('soul_hash')
        being.alias = data.get('alias')
        being.data = data.get('data', {})
        being.access_zone = data.get('access_zone', 'public_zone')

        # Konwersja dat
        if data.get('ttl_expires'):
            if isinstance(data['ttl_expires'], str):
                being.ttl_expires = datetime.fromisoformat(data['ttl_expires'])
            else:
                being.ttl_expires = data['ttl_expires']

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
        return self.to_dict()

    def __repr__(self):
        status = "EXPIRED" if self.is_expired() else "ACTIVE"
        return f"Being(ulid={self.ulid[:8]}..., alias={self.alias}, zone={self.access_zone}, status={status})"