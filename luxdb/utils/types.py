
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

# Supported Python types
SUPPORTED_TYPES = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "dict": dict,
    "List[str]": list,
    "List[float]": list,
    "List[int]": list,
    "List[dict]": list,
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
