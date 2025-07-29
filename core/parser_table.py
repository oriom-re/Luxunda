
from dataclasses import make_dataclass, field
from typing import Dict, Any
import json

def apply_genotype_to_being(being, genotype: dict):
    """Tworzy dynamiczną wersję bytu z polami z genotypu"""
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
        typ_name = meta.get("py_type", "str")
        typ = type_map.get(typ_name, str)
        fields.append((name, typ, field(default=None)))

    if fields:  # tylko jeśli są jakieś pola do dodania
        DynamicBeing = make_dataclass(
            cls_name="DynamicBeing",
            fields=fields,
            bases=(being.__class__,),
            frozen=False
        )
        being.__class__ = DynamicBeing

async def save_being_data(being, soul, data: Dict[str, Any] = None):
    """Zapisuje dane bytu do bazy danych"""
    from database.soul_repository import DynamicRepository
    
    # Walidacja genotypu
    if not soul.genotype or not soul.genotype.get("attributes"):
        raise ValueError("Soul genotype must have attributes defined")
    
    # Przygotowanie danych do zapisu
    data_to_save = {}
    for key, metadata in soul.genotype.get("attributes", {}).items():
        if not hasattr(being, key):
            raise ValueError(f"Being instance does not have attribute {key}")
        data_to_save[metadata.get('table_name')] = getattr(being, key)

    # Ustawienie dodatkowych danych
    if data:
        for key, value in data.items():
            setattr(being, key, value)

    print(f"💾 Saving being with soul hash: {soul.soul_hash}")
    await DynamicRepository.insert_data_transaction(being, soul.genotype)
    return being

def validate_genotype_structure(genotype: Dict[str, Any]) -> bool:
    """Waliduje strukturę genotypu"""
    if not isinstance(genotype, dict):
        return False
    
    if "attributes" not in genotype:
        return False
        
    attributes = genotype.get("attributes", {})
    if not isinstance(attributes, dict):
        return False
        
    return True

def extract_genotype_fields(genotype: Dict[str, Any]) -> list:
    """Wyciąga pola z genotypu dla dynamicznego tworzenia klas"""
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
        typ_name = meta.get("py_type", "str")
        typ = type_map.get(typ_name, str)
        fields.append((name, typ, field(default=None)))
    
    return fields
