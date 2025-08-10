#!/usr/bin/env python3
"""
LuxDB Unified Serialization System
=================================

Unified serializer for JSONB data in PostgreSQL with complete functionality.
"""

import json
import datetime
from typing import Any, Dict, Union, List, Tuple
from decimal import Decimal


class GeneticResponseFormat:
    """
    Standardowy format odpowiedzi zgodny z zapisem genetycznym Soul.
    Zapewnia spójność między różnymi wersjami systemu.
    """

    @staticmethod
    def success_response(data: Any, soul_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Tworzy standardową odpowiedź sukcesu z kontekstem genetycznym.

        Args:
            data: Dane do zwrócenia
            soul_context: Kontekst Soul (genotyp, hash, itp.)

        Returns:
            Standardowy słownik odpowiedzi
        """
        response = {
            "success": True,
            "genetic_version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        if soul_context:
            response["soul_context"] = {
                "soul_hash": soul_context.get("soul_hash"),
                "genotype_name": soul_context.get("genotype", {}).get("genesis", {}).get("name"),
                "genotype_version": soul_context.get("genotype", {}).get("genesis", {}).get("version"),
                "compatibility": soul_context.get("genotype", {}).get("genesis", {}).get("compatibility", ["1.0.0"])
            }

        return response

    @staticmethod
    def error_response(error: str, error_code: str = "GENERIC_ERROR", soul_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Tworzy standardową odpowiedź błędu z kontekstem genetycznym.
        """
        response = {
            "success": False,
            "genetic_version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "error_code": error_code
        }

        if soul_context:
            response["soul_context"] = {
                "soul_hash": soul_context.get("soul_hash"),
                "genotype_name": soul_context.get("genotype", {}).get("genesis", {}).get("name"),
                "genotype_version": soul_context.get("genotype", {}).get("genesis", {}).get("version")
            }

        return response

    @staticmethod
    def collection_response(items: List[Any], total_count: int = None, soul_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Tworzy standardową odpowiedź dla kolekcji danych.
        """
        if total_count is None:
            total_count = len(items) if items else 0

        response = {
            "success": True,
            "genetic_version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "items": items,
                "count": total_count,
                "has_more": False  # Można rozszerzyć o paginację
            }
        }

        if soul_context:
            response["soul_context"] = {
                "collection_type": soul_context.get("genotype", {}).get("genesis", {}).get("name"),
                "item_compatibility": soul_context.get("genotype", {}).get("genesis", {}).get("compatibility", ["1.0.0"])
            }

        return response

class JSONBSerializer:
    """Unified JSONB Serializer for LuxDB - handles all serialization needs"""

    @staticmethod
    def serialize(data: Any) -> str:
        """Serialize data to JSON string for JSONB storage"""
        return json.dumps(data, cls=LuxDBJSONEncoder, ensure_ascii=False)

    @staticmethod
    def deserialize(json_str: Union[str, dict]) -> Any:
        """Deserialize JSON string or dict from JSONB storage"""
        if isinstance(json_str, dict):
            return json_str
        if isinstance(json_str, str):
            return json.loads(json_str)
        return json_str

    @staticmethod
    def prepare_for_jsonb(data: Any) -> Any:
        """Prepare data for JSONB storage by converting unsupported types"""
        if isinstance(data, datetime.datetime):
            return data.isoformat()
        elif isinstance(data, datetime.date):
            return data.isoformat()
        elif isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, dict):
            return {k: JSONBSerializer.prepare_for_jsonb(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [JSONBSerializer.prepare_for_jsonb(item) for item in data]
        else:
            return data

    @staticmethod
    def serialize_being_data(data: Dict[str, Any], soul: 'Soul') -> Dict[str, Any]:
        """Serialize Being data according to Soul schema"""
        serialized = {}
        attributes = soul.genotype.get("attributes", {})

        for attr_name, attr_meta in attributes.items():
            if attr_name in data:
                value = data[attr_name]
                py_type = attr_meta.get("py_type", "str")

                if py_type == "datetime":
                    serialized[attr_name] = value.isoformat() if isinstance(value, datetime.datetime) else value
                elif py_type == "List[str]":
                    serialized[attr_name] = list(value) if isinstance(value, (list, set)) else [value]
                else:
                    serialized[attr_name] = JSONBSerializer.prepare_for_jsonb(value)

        return serialized

    @staticmethod
    def deserialize_being_data(data: Dict[str, Any], soul: 'Soul') -> Dict[str, Any]:
        """Deserialize Being data according to Soul schema"""
        deserialized = {}
        attributes = soul.genotype.get("attributes", {})

        for attr_name, attr_meta in attributes.items():
            if attr_name in data:
                value = data[attr_name]
                py_type = attr_meta.get("py_type", "str")

                if py_type == "datetime":
                    try:
                        deserialized[attr_name] = datetime.datetime.fromisoformat(value) if isinstance(value, str) else value
                    except (ValueError, TypeError):
                        deserialized[attr_name] = value
                elif py_type == "List[str]":
                    deserialized[attr_name] = list(value) if isinstance(value, (list, set)) else [value]
                else:
                    deserialized[attr_name] = value

        return deserialized

    @staticmethod
    def validate_and_serialize(data: Dict[str, Any], soul: 'Soul') -> Tuple[Dict[str, Any], List[str]]:
        """Validate and serialize data, returning data and errors"""
        errors = soul.validate_data(data)
        if not errors:
            serialized_data = JSONBSerializer.serialize_being_data(data, soul)
            return serialized_data, []
        return data, errors


class LuxDBJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for LuxDB objects"""

    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif hasattr(obj, 'to_dict'):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        return super().default(obj)


# Legacy compatibility aliases
class JsonbSerializer(JSONBSerializer):
    """Legacy alias for backward compatibility"""

    @staticmethod
    def serialize_for_jsonb(data: Any) -> str:
        """Legacy method for backward compatibility"""
        return JSONBSerializer.serialize(data)

    @staticmethod
    def deserialize_from_jsonb(json_data: Union[str, dict]) -> Any:
        """Legacy method for backward compatibility"""
        return JSONBSerializer.deserialize(json_data)


# Convenience functions
def serialize_for_jsonb(data: Any) -> str:
    """Convenience function for JSONB serialization"""
    return JSONBSerializer.serialize(data)


def deserialize_from_jsonb(json_data: Union[str, dict]) -> Any:
    """Convenience function for JSONB deserialization"""
    return JSONBSerializer.deserialize(json_data)