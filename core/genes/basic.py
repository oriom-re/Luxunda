
"""
Podstawowe geny dla automatycznie generowanych genotypów
"""

from typing import Dict, Any
from database.models.base import Being


async def initialize_being(being: Being, *args, **kwargs) -> Dict[str, Any]:
    """Inicjalizuje byt z podstawowymi wartościami"""
    print(f"🧬 Inicjalizacja bytu {being.ulid}")
    
    # Ustaw podstawowe wartości jeśli nie są ustawione
    if not hasattr(being, 'created_at') or not being.created_at:
        from datetime import datetime
        being.created_at = datetime.now()
    
    return {
        "status": "initialized", 
        "being_ulid": being.ulid,
        "timestamp": being.created_at.isoformat() if being.created_at else None
    }


async def validate_being(being: Being, *args, **kwargs) -> Dict[str, Any]:
    """Waliduje integralność bytu"""
    print(f"✅ Walidacja bytu {being.ulid}")
    errors = []
    warnings = []
    
    # Sprawdź podstawowe pola
    if not hasattr(being, 'ulid') or not being.ulid:
        errors.append("Brak ULID")
    
    if not hasattr(being, 'soul_hash') or not being.soul_hash:
        warnings.append("Brak soul_hash")
    
    # Sprawdź genotyp
    if hasattr(being, 'genotype') and being.genotype:
        if 'attributes' not in being.genotype:
            warnings.append("Genotyp nie ma zdefiniowanych atrybutów")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "being_ulid": being.ulid
    }


async def serialize_being(being: Being, format: str = "dict", *args, **kwargs) -> Dict[str, Any]:
    """Serializuje byt do różnych formatów"""
    print(f"📦 Serializacja bytu {being.ulid} do formatu {format}")
    
    if format == "dict":
        return being.to_dict()
    elif format == "json":
        import json
        return {"json": json.dumps(being.to_dict(), default=str)}
    elif format == "minimal":
        return {
            "ulid": being.ulid,
            "soul_hash": being.soul_hash,
            "alias": getattr(being, 'alias', None),
            "created_at": getattr(being, 'created_at', None)
        }
    else:
        return {"error": f"Nieznany format: {format}"}


async def get_being_info(being: Being, *args, **kwargs) -> Dict[str, Any]:
    """Zwraca podstawowe informacje o bycie"""
    return {
        "ulid": being.ulid,
        "soul_hash": being.soul_hash,
        "alias": getattr(being, 'alias', None),
        "type": being.__class__.__name__,
        "has_genotype": hasattr(being, 'genotype') and bool(being.genotype),
        "field_count": len(being.to_dict()),
        "created_at": getattr(being, 'created_at', None)
    }
