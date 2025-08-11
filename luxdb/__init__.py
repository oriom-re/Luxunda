"""
LuxDB - Genetic Database Library
================================

Nie relacja. Nie dokument. Ewolucja danych.

LuxDB to rewolucyjna biblioteka bazy danych oparta na koncepcji genotypów i bytów.
Zamiast tradycyjnych tabel i dokumentów, używa żywych struktur danych.

Przykład użycia:
    ```python
    import asyncio
    from luxdb import LuxDB, Soul, Being

    async def main():
        # Inicjalizacja
        db = LuxDB(
            host='localhost',
            port=5432,
            user='user',
            password='password',
            database='luxdb'
        )
        await db.initialize()

        # Definicja genotypu
        genotype = {
            "genesis": {"name": "user", "version": "1.0"},
            "attributes": {
                "name": {"py_type": "str"},
                "email": {"py_type": "str", "unique": True},
                "age": {"py_type": "int"}
            }
        }

        # Utworzenie soul i being
        soul = await Soul.create(genotype, alias="user")
        being = await Being.create(soul, {
            "name": "Jan", 
            "email": "jan@example.com", 
            "age": 30
        })

        print(f"Utworzono: {being.ulid}")

    asyncio.run(main())
    ```
"""

__version__ = "0.1.0"
__author__ = "LuxDB Team"
__email__ = "contact@luxdb.dev"

# Core imports
from .core.luxdb import LuxDB
from .models.soul import Soul
from .models.being import Being
# Relationship moved to legacy

# Utilities
from .utils.types import GenotypeDef, AttributeDef
from .utils.validators import validate_genotype

__all__ = [
    # Core classes
    "LuxDB",
    "Soul", 
    "Being",
    # Relationship moved to legacy

    # Types
    "GenotypeDef",
    "AttributeDef",

    # Utilities
    "validate_genotype",

    # Meta
    "__version__",
    "__author__",
    "__email__",
]

# Configuration
DEFAULT_CONFIG = {
    "connection_pool_size": 5,
    "connection_timeout": 30,
    "enable_logging": True,
    "auto_create_tables": True,
    "vector_dimensions": 1536,
}