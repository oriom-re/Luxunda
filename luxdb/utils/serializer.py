
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
    pass


# Convenience functions
def serialize_for_jsonb(data: Any) -> str:
    """Convenience function for JSONB serialization"""
    return JSONBSerializer.serialize(data)


def deserialize_from_jsonb(json_data: Union[str, dict]) -> Any:
    """Convenience function for JSONB deserialization"""
    return JSONBSerializer.deserialize(json_data)
