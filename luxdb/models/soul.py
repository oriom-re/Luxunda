import ulid as _ulid
from datetime import datetime
from typing import Dict, Any, Optional

# Placeholder for Being model and BeingRepository
class Being:
    def __init__(self, ulid: str, soul_hash: str, alias: Optional[str], data: Dict[str, Any], created_at: datetime):
        self.ulid = ulid
        self.soul_hash = soul_hash
        self.alias = alias
        self.data = data
        self.created_at = created_at

class BeingRepository:
    @staticmethod
    async def set(being: Being):
        # Simulate saving to a repository
        print(f"Saving Being with ULID: {being.ulid}, Alias: {being.alias}, Data: {being.data}")
        pass

class Soul:
    """
    Soul - GŁÓWNA KLASA systemu LuxDB
    
    Soul jest genotypem - niezmiennym szablonem który definiuje:
    - Funkcje (module_source)
    - Schemat danych (attributes)
    - Metadane (genesis)
    
    Being są tworzone PRZEZ Soul jako instancje/fenotypy.
    """
    
    # Rejestr globalny instancji Soul - zawsze aktualny
    _registry: Dict[str, Dict[str, Any]] = {}
    
    def __init__(self):
        # Soul jako główna klasa - wszystkie operacje zaczynają się tutaj
        self.ulid: Optional[_ulid.ULID] = None
        self.data: Dict[str, Any] = {}
        self._temp_alias: Optional[str] = None
        self._initialized_at: Optional[datetime] = None
        self.soul_hash: str = "some_default_hash" # Placeholder for soul_hash
    
    @property
    def instances(self) -> Dict[str, Any]:
        """Property zwracające aktualne instancje z rejestru"""
        if self.soul_hash not in Soul._registry:
            Soul._registry[self.soul_hash] = {}
        return Soul._registry[self.soul_hash]

    def init(self, alias: str = None, data: Dict[str, Any] = None) -> 'Soul':
        """Inicjalizuje Soul z tymczasowymi polami ulid i data"""
        # Tymczasowe pola w instancji Soul
        self.ulid = _ulid.ULID()
        self.data = data if data is not None else {}
        self._temp_alias = alias
        self._initialized_at = datetime.now()

        return self

    async def set(self) -> 'Being':
        """Zapisuje Being do bazy danych używając tymczasowych pól z init()"""
        if not hasattr(self, 'ulid') or self.ulid is None:
            raise ValueError("Soul musi być zainicjalizowany przez init() przed set()")

        # Tworzenie Being z tymczasowych pól
        being = Being(
            ulid=str(self.ulid),
            soul_hash=self.soul_hash,
            alias=self._temp_alias,
            data=self.data,
            created_at=self._initialized_at
        )

        # Wywołanie init() jeśli istnieje w module (symulacja)
        # W tym przykładzie nie ma modułu źródłowego, więc ten blok jest pomijany.
        # if hasattr(self, 'module_source') and self.module_source:
        #     init_function = getattr(self.module_source, 'init', None)
        #     if init_function:
        #         await init_function(being.data)

        # Zapisanie do bazy
        await BeingRepository.set(being)

        # Czyszczenie tymczasowych pól po udanym zapisie
        if hasattr(self, 'ulid'):
            delattr(self, 'ulid')
        if hasattr(self, 'data'):
            delattr(self, 'data')
        if hasattr(self, '_temp_alias'):
            delattr(self, '_temp_alias')
        if hasattr(self, '_initialized_at'):
            delattr(self, '_initialized_at')

        return being

# Example Usage (for demonstration purposes, not part of the class definition)
async def main():
    # Example 1: Initialize with data
    soul1 = Soul().init(alias="calculator", data={"x": 5, "y": 10})
    print(f"Initial ULID: {soul1.ulid}")
    print(f"Initial Data: {soul1.data}")
    being1 = await soul1.set()
    print(f"Created Being 1: {being1.__dict__}\n")

    # Example 2: Initialize without data, then add data
    soul2 = Soul().init(alias="user_profile")
    print(f"Initial ULID: {soul2.ulid}")
    print(f"Initial Data: {soul2.data}")
    soul2.data = {"name": "Alice", "age": 30} # Modify data before set
    print(f"Modified Data: {soul2.data}")
    being2 = await soul2.set()
    print(f"Created Being 2: {being2.__dict__}\n")

    # Example 3: Trying to set without init (will raise ValueError)
    soul3 = Soul()
    try:
        await soul3.set()
    except ValueError as e:
        print(f"Error as expected: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())