"""
Definicje typów dla LuxDB.
"""

from typing import Dict, Any, Union, List, Optional
from typing_extensions import TypedDict

class AttributeDef(TypedDict, total=False):
    """
    Definicja atrybutu w genotypie.
    """
    py_type: str
    max_length: Optional[int]
    min_length: Optional[int]
    min_value: Optional[Union[int, float]]
    max_value: Optional[Union[int, float]]
    default: Any
    unique: bool
    nullable: bool
    vector_size: Optional[int]
    table_name: Optional[str]

class GenesisDef(TypedDict, total=False):
    """
    Definicja genesis w genotypie.
    """
    name: str
    version: str
    description: Optional[str]
    type: Optional[str]

class GenotypeDef(TypedDict):
    """
    Pełna definicja genotypu.
    """
    genesis: GenesisDef
    attributes: Dict[str, AttributeDef]
    genes: Optional[Dict[str, str]]

# Typy pomocnicze
SoulHash = str
BeingULID = str
RelationshipID = str

# Obsługiwane typy danych w LuxDB
SUPPORTED_TYPES = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "dict": dict,
    "list": list,  # Podstawowy typ list
    "List[str]": list,
    "List[int]": list,
    "List[float]": list,
    "List[dict]": list,
    "Optional[str]": str,
    "Optional[int]": int,
    "Optional[float]": float,
    "Optional[bool]": bool,
    "function": type(lambda: None)
}

# SQL type mapping
SQL_TYPE_MAPPING = {
    "str": "TEXT",
    "int": "INTEGER",
    "float": "FLOAT",
    "bool": "BOOLEAN",
    "dict": "JSONB",
    "List[str]": "JSONB",
    "List[float]": "VECTOR",
    "List[int]": "JSONB",
    "List[dict]": "JSONB",
}