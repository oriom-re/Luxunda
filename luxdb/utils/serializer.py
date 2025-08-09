
#!/usr/bin/env python3
"""
🔧 JSONB Serializer - Automatyczna serializacja na podstawie schematu Soul
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from database.models.base import Soul

class JSONBSerializer:
    """Serializer dla danych JSONB na podstawie schematu Soul"""
    
    @staticmethod
    def serialize_being_data(data: Dict[str, Any], soul: 'Soul') -> Dict[str, Any]:
        """
        Serializuje dane Being zgodnie ze schematem Soul
        
        Args:
            data: Dane do serializacji
            soul: Obiekt Soul z definicją schematu
            
        Returns:
            Zserializowane dane gotowe do zapisu w JSONB
        """
        if not data or not soul or not soul.genotype:
            return data or {}
        
        serialized = {}
        attributes = soul.genotype.get("attributes", {})
        
        for attr_name, value in data.items():
            if attr_name in attributes:
                attr_meta = attributes[attr_name]
                py_type = attr_meta.get("py_type", "str")
                
                try:
                    serialized[attr_name] = JSONBSerializer._serialize_value(value, py_type)
                except Exception as e:
                    print(f"⚠️ Błąd serializacji atrybutu '{attr_name}': {e}")
                    serialized[attr_name] = value
            else:
                # Atrybut nie jest zdefiniowany w schemacie - zachowaj jak jest
                serialized[attr_name] = value
        
        # Dodaj atrybuty z defaultami, jeśli nie są obecne
        for attr_name, attr_meta in attributes.items():
            if attr_name not in serialized and "default" in attr_meta:
                default_value = attr_meta["default"]
                py_type = attr_meta.get("py_type", "str")
                serialized[attr_name] = JSONBSerializer._serialize_value(default_value, py_type)
        
        return serialized
    
    @staticmethod
    def deserialize_being_data(data: Dict[str, Any], soul: 'Soul') -> Dict[str, Any]:
        """
        Deserializuje dane Being zgodnie ze schematem Soul
        
        Args:
            data: Dane JSONB do deserializacji
            soul: Obiekt Soul z definicją schematu
            
        Returns:
            Zdeserializowane dane z odpowiednimi typami Python
        """
        if not data or not soul or not soul.genotype:
            return data or {}
        
        deserialized = {}
        attributes = soul.genotype.get("attributes", {})
        
        for attr_name, value in data.items():
            if attr_name in attributes:
                attr_meta = attributes[attr_name]
                py_type = attr_meta.get("py_type", "str")
                
                try:
                    deserialized[attr_name] = JSONBSerializer._deserialize_value(value, py_type)
                except Exception as e:
                    print(f"⚠️ Błąd deserializacji atrybutu '{attr_name}': {e}")
                    deserialized[attr_name] = value
            else:
                # Atrybut nie jest zdefiniowany w schemacie - zachowaj jak jest
                deserialized[attr_name] = value
        
        return deserialized
    
    @staticmethod
    def validate_and_serialize(data: Dict[str, Any], soul: 'Soul') -> tuple[Dict[str, Any], List[str]]:
        """
        Waliduje i serializuje dane zgodnie ze schematem Soul
        
        Args:
            data: Dane do walidacji i serializacji
            soul: Obiekt Soul z definicją schematu
            
        Returns:
            Tuple (zserializowane_dane, lista_błędów)
        """
        if not soul or not soul.genotype:
            return data, ["Brak schematu Soul dla walidacji"]
        
        # Walidacja
        errors = soul.validate_data(data)
        
        if errors:
            return data, errors
        
        # Serializacja
        try:
            serialized_data = JSONBSerializer.serialize_being_data(data, soul)
            return serialized_data, []
        except Exception as e:
            return data, [f"Błąd serializacji: {str(e)}"]
    
    @staticmethod
    def _serialize_value(value: Any, py_type: str) -> Any:
        """Serializuje pojedynczą wartość według typu"""
        if value is None:
            return None
        
        if py_type == "datetime":
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, str):
                # Sprawdź czy to już jest ISO format
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return value
                except ValueError:
                    return value
        
        elif py_type == "List[str]":
            if isinstance(value, (list, tuple)):
                return [str(item) for item in value]
            elif isinstance(value, str):
                return [value]
        
        elif py_type == "List[int]":
            if isinstance(value, (list, tuple)):
                return [int(item) for item in value if str(item).isdigit()]
            elif isinstance(value, (int, str)):
                return [int(value)]
        
        elif py_type == "List[float]":
            if isinstance(value, (list, tuple)):
                return [float(item) for item in value]
            elif isinstance(value, (int, float, str)):
                return [float(value)]
        
        elif py_type == "dict":
            if isinstance(value, dict):
                return value
            elif isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return {"value": value}
        
        elif py_type == "list":
            if isinstance(value, (list, tuple)):
                return list(value)
            else:
                return [value]
        
        elif py_type == "int":
            return int(value)
        
        elif py_type == "float":
            return float(value)
        
        elif py_type == "bool":
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            else:
                return bool(value)
        
        elif py_type == "decimal":
            return str(Decimal(str(value)))
        
        # Default: str
        return str(value)
    
    @staticmethod
    def _deserialize_value(value: Any, py_type: str) -> Any:
        """Deserializuje pojedynczą wartość według typu"""
        if value is None:
            return None
        
        if py_type == "datetime":
            if isinstance(value, str):
                try:
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    return value
            elif isinstance(value, datetime):
                return value
        
        elif py_type in ["List[str]", "List[int]", "List[float]"]:
            if isinstance(value, list):
                if py_type == "List[str]":
                    return [str(item) for item in value]
                elif py_type == "List[int]":
                    return [int(item) for item in value if str(item).isdigit()]
                elif py_type == "List[float]":
                    return [float(item) for item in value]
            else:
                return [value]
        
        elif py_type == "dict":
            if isinstance(value, dict):
                return value
            elif isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return {"value": value}
        
        elif py_type == "list":
            if isinstance(value, list):
                return value
            else:
                return [value]
        
        elif py_type == "int":
            return int(value)
        
        elif py_type == "float":
            return float(value)
        
        elif py_type == "bool":
            if isinstance(value, bool):
                return value
            elif isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            else:
                return bool(value)
        
        elif py_type == "decimal":
            return Decimal(str(value))
        
        # Default: str
        return str(value)
    
    @staticmethod
    def get_json_schema(soul: 'Soul') -> Dict[str, Any]:
        """
        Generuje JSON Schema na podstawie definicji Soul
        
        Args:
            soul: Obiekt Soul
            
        Returns:
            JSON Schema
        """
        if not soul or not soul.genotype:
            return {}
        
        attributes = soul.genotype.get("attributes", {})
        schema = {
            "type": "object",
            "title": soul.alias or "Being Data",
            "properties": {},
            "required": []
        }
        
        for attr_name, attr_meta in attributes.items():
            py_type = attr_meta.get("py_type", "str")
            required = attr_meta.get("required", False)
            description = attr_meta.get("description", "")
            
            # Mapowanie typów Python na JSON Schema
            json_type = JSONBSerializer._python_to_json_type(py_type)
            
            schema["properties"][attr_name] = {
                "type": json_type,
                "description": description
            }
            
            if "default" in attr_meta:
                schema["properties"][attr_name]["default"] = attr_meta["default"]
            
            if required:
                schema["required"].append(attr_name)
        
        return schema
    
    @staticmethod
    def _python_to_json_type(py_type: str) -> str:
        """Mapuje typy Python na typy JSON Schema"""
        mapping = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "dict": "object",
            "list": "array",
            "List[str]": "array",
            "List[int]": "array",
            "List[float]": "array",
            "datetime": "string",
            "decimal": "string"
        }
        return mapping.get(py_type, "string")
