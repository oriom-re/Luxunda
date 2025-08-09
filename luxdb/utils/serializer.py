
"""
Automatyczny serializer dla pól JSONB na podstawie schematu Soul
"""

import json
import datetime
from typing import Any, Dict, List, Optional
from decimal import Decimal


class JSONBSerializer:
    """Automatyczny serializer dla pól JSONB"""
    
    @staticmethod
    def serialize_value(value: Any, py_type: str) -> Any:
        """
        Serializuje wartość zgodnie z typem zdefiniowanym w Soul
        
        Args:
            value: Wartość do serializacji
            py_type: Typ zdefiniowany w genotypie Soul
            
        Returns:
            Zserializowana wartość gotowa do zapisania w JSONB
        """
        if value is None:
            return None
            
        # Podstawowe typy Python
        if py_type == "str":
            return str(value)
        elif py_type == "int":
            return int(value) if value != "" else None
        elif py_type == "float":
            return float(value) if value != "" else None
        elif py_type == "bool":
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        elif py_type == "dict":
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except:
                    return {}
            return dict(value) if value else {}
        
        # Typy listowe
        elif py_type.startswith("List["):
            inner_type = py_type[5:-1]  # Wyciąga typ z List[typ]
            
            if isinstance(value, str):
                try:
                    value = json.loads(value)
                except:
                    return []
                    
            if not isinstance(value, list):
                return []
                
            return [JSONBSerializer.serialize_value(item, inner_type) for item in value]
        
        # Specjalne typy
        elif py_type == "datetime":
            if isinstance(value, str):
                try:
                    return datetime.datetime.fromisoformat(value).isoformat()
                except:
                    return None
            elif isinstance(value, datetime.datetime):
                return value.isoformat()
            return None
        elif py_type == "date":
            if isinstance(value, str):
                try:
                    return datetime.datetime.fromisoformat(value).date().isoformat()
                except:
                    return None
            elif isinstance(value, datetime.date):
                return value.isoformat()
            return None
        elif py_type == "decimal":
            if isinstance(value, (str, int, float)):
                try:
                    return str(Decimal(str(value)))
                except:
                    return None
            elif isinstance(value, Decimal):
                return str(value)
            return None
        
        # Domyślnie konwertuj na string
        return str(value)
    
    @staticmethod
    def deserialize_value(value: Any, py_type: str) -> Any:
        """
        Deserializuje wartość z JSONB do odpowiedniego typu Python
        
        Args:
            value: Wartość z JSONB
            py_type: Typ zdefiniowany w genotypie Soul
            
        Returns:
            Zdeserializowana wartość w odpowiednim typie Python
        """
        if value is None:
            return None
            
        try:
            # Podstawowe typy Python
            if py_type == "str":
                return str(value)
            elif py_type == "int":
                return int(value)
            elif py_type == "float":
                return float(value)
            elif py_type == "bool":
                return bool(value)
            elif py_type == "dict":
                return dict(value) if isinstance(value, dict) else {}
            
            # Typy listowe
            elif py_type.startswith("List["):
                inner_type = py_type[5:-1]
                if isinstance(value, list):
                    return [JSONBSerializer.deserialize_value(item, inner_type) for item in value]
                return []
            
            # Specjalne typy
            elif py_type == "datetime":
                if isinstance(value, str):
                    return datetime.datetime.fromisoformat(value)
                return value
            elif py_type == "date":
                if isinstance(value, str):
                    return datetime.datetime.fromisoformat(value).date()
                return value
            elif py_type == "decimal":
                if isinstance(value, str):
                    return Decimal(value)
                return Decimal(str(value))
            
            return value
            
        except Exception as e:
            print(f"⚠️ Błąd deserializacji {py_type}: {e}")
            return value
    
    @staticmethod
    def serialize_being_data(data: Dict[str, Any], soul: 'Soul') -> Dict[str, Any]:
        """
        Serializuje wszystkie dane Being zgodnie ze schematem Soul
        
        Args:
            data: Surowe dane Being
            soul: Obiekt Soul z definicją schematu
            
        Returns:
            Zserializowane dane gotowe do zapisu w JSONB
        """
        if not soul or not soul.genotype:
            return data
            
        attributes = soul.genotype.get("attributes", {})
        serialized_data = {}
        
        for key, value in data.items():
            attr_config = attributes.get(key, {})
            py_type = attr_config.get("py_type", "str")
            
            try:
                serialized_data[key] = JSONBSerializer.serialize_value(value, py_type)
            except Exception as e:
                print(f"⚠️ Błąd serializacji pola {key}: {e}")
                serialized_data[key] = value
                
        return serialized_data
    
    @staticmethod
    def deserialize_being_data(data: Dict[str, Any], soul: 'Soul') -> Dict[str, Any]:
        """
        Deserializuje dane Being zgodnie ze schematem Soul
        
        Args:
            data: Dane z JSONB
            soul: Obiekt Soul z definicją schematu
            
        Returns:
            Zdeserializowane dane w odpowiednich typach Python
        """
        if not soul or not soul.genotype:
            return data
            
        attributes = soul.genotype.get("attributes", {})
        deserialized_data = {}
        
        for key, value in data.items():
            attr_config = attributes.get(key, {})
            py_type = attr_config.get("py_type", "str")
            
            try:
                deserialized_data[key] = JSONBSerializer.deserialize_value(value, py_type)
            except Exception as e:
                print(f"⚠️ Błąd deserializacji pola {key}: {e}")
                deserialized_data[key] = value
                
        return deserialized_data
    
    @staticmethod
    def validate_and_serialize(data: Dict[str, Any], soul: 'Soul') -> tuple[Dict[str, Any], List[str]]:
        """
        Waliduje i serializuje dane jednocześnie
        
        Args:
            data: Surowe dane do walidacji i serializacji
            soul: Obiekt Soul z definicją schematu
            
        Returns:
            Tuple (zserializowane_dane, lista_błędów)
        """
        errors = []
        
        # Najpierw walidacja
        validation_errors = soul.validate_data(data)
        errors.extend(validation_errors)
        
        # Potem serializacja
        try:
            serialized_data = JSONBSerializer.serialize_being_data(data, soul)
            return serialized_data, errors
        except Exception as e:
            errors.append(f"Błąd serializacji: {str(e)}")
            return data, errors
