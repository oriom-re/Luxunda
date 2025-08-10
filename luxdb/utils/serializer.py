#!/usr/bin/env python3
"""
LuxDB Serialization Utilities
============================

Utilities for serializing/deserializing data for JSONB storage in PostgreSQL.
"""

import json
import datetime
from typing import Any, Dict, Union
from decimal import Decimal


class JsonbSerializer:
    """Serializer for JSONB data in PostgreSQL"""

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
            return {k: JsonbSerializer.prepare_for_jsonb(v) for k, v in data.items()}
        elif isinstance(data, (list, tuple)):
            return [JsonbSerializer.prepare_for_jsonb(item) for item in data]
        else:
            return data


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


def serialize_for_jsonb(data: Any) -> str:
    """Convenience function for JSONB serialization"""
    return JsonbSerializer.serialize(data)


def deserialize_from_jsonb(json_data: Union[str, dict]) -> Any:
    """Convenience function for JSONB deserialization"""
    return JsonbSerializer.deserialize(json_data)