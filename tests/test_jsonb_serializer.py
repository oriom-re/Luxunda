
"""
Testy dla automatycznego serializatora JSONB
"""

import pytest
import asyncio
from datetime import datetime, date
from decimal import Decimal
from luxdb.utils.serializer import JSONBSerializer
from luxdb.models.soul import Soul


class TestJSONBSerializer:
    
    def test_serialize_basic_types(self):
        """Test serializacji podstawowych typów"""
        
        # String
        assert JSONBSerializer.serialize_value("test", "str") == "test"
        assert JSONBSerializer.serialize_value(123, "str") == "123"
        
        # Integer
        assert JSONBSerializer.serialize_value("123", "int") == 123
        assert JSONBSerializer.serialize_value(123.5, "int") == 123
        
        # Float
        assert JSONBSerializer.serialize_value("123.5", "float") == 123.5
        assert JSONBSerializer.serialize_value(123, "float") == 123.0
        
        # Boolean
        assert JSONBSerializer.serialize_value("true", "bool") == True
        assert JSONBSerializer.serialize_value("false", "bool") == False
        assert JSONBSerializer.serialize_value(1, "bool") == True
        assert JSONBSerializer.serialize_value(0, "bool") == False
    
    def test_serialize_complex_types(self):
        """Test serializacji złożonych typów"""
        
        # Dict
        test_dict = {"key": "value", "number": 123}
        result = JSONBSerializer.serialize_value(test_dict, "dict")
        assert result == test_dict
        
        # String do dict
        dict_string = '{"key": "value"}'
        result = JSONBSerializer.serialize_value(dict_string, "dict")
        assert result == {"key": "value"}
        
        # List[str]
        test_list = ["a", "b", "c"]
        result = JSONBSerializer.serialize_value(test_list, "List[str]")
        assert result == ["a", "b", "c"]
        
        # List[int]
        test_list = ["1", "2", "3"]
        result = JSONBSerializer.serialize_value(test_list, "List[int]")
        assert result == [1, 2, 3]
    
    def test_serialize_special_types(self):
        """Test serializacji specjalnych typów"""
        
        # Datetime
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = JSONBSerializer.serialize_value(dt, "datetime")
        assert result == dt.isoformat()
        
        # Date
        d = date(2023, 1, 1)
        result = JSONBSerializer.serialize_value(d, "date")
        assert result == d.isoformat()
        
        # Decimal
        dec = Decimal("123.45")
        result = JSONBSerializer.serialize_value(dec, "decimal")
        assert result == "123.45"
    
    def test_deserialize_basic_types(self):
        """Test deserializacji podstawowych typów"""
        
        assert JSONBSerializer.deserialize_value("test", "str") == "test"
        assert JSONBSerializer.deserialize_value(123, "int") == 123
        assert JSONBSerializer.deserialize_value(123.5, "float") == 123.5
        assert JSONBSerializer.deserialize_value(True, "bool") == True
    
    async def test_serialize_being_data(self):
        """Test serializacji danych Being"""
        
        # Utwórz testowy genotyp
        genotype = {
            "genesis": {"name": "test_user", "version": "1.0"},
            "attributes": {
                "name": {"py_type": "str"},
                "age": {"py_type": "int"},
                "active": {"py_type": "bool"},
                "scores": {"py_type": "List[float]"},
                "metadata": {"py_type": "dict"}
            }
        }
        
        # Utwórz Soul
        soul = Soul()
        soul.genotype = genotype
        
        # Testowe dane
        test_data = {
            "name": "John Doe",
            "age": "25",  # String, powinien być skonwertowany na int
            "active": "true",  # String, powinien być skonwertowany na bool
            "scores": ["85.5", "92.0", "78.5"],  # List[str], powinien być List[float]
            "metadata": '{"role": "user", "level": 1}'  # String JSON, powinien być dict
        }
        
        # Serializacja
        result = JSONBSerializer.serialize_being_data(test_data, soul)
        
        assert result["name"] == "John Doe"
        assert result["age"] == 25
        assert result["active"] == True
        assert result["scores"] == [85.5, 92.0, 78.5]
        assert result["metadata"] == {"role": "user", "level": 1}
    
    async def test_validate_and_serialize(self):
        """Test walidacji i serializacji jednocześnie"""
        
        genotype = {
            "genesis": {"name": "test_user", "version": "1.0"},
            "attributes": {
                "name": {"py_type": "str"},
                "age": {"py_type": "int"},
                "email": {"py_type": "str", "required": True}
            }
        }
        
        soul = Soul()
        soul.genotype = genotype
        
        # Poprawne dane
        valid_data = {
            "name": "John",
            "age": "25",
            "email": "john@example.com"
        }
        
        result, errors = JSONBSerializer.validate_and_serialize(valid_data, soul)
        assert len(errors) == 0
        assert result["age"] == 25
        
        # Niepoprawne dane (brak wymaganego pola)
        invalid_data = {
            "name": "John",
            "age": "25"
            # brak email
        }
        
        result, errors = JSONBSerializer.validate_and_serialize(invalid_data, soul)
        assert len(errors) > 0
        assert any("email" in error for error in errors)


if __name__ == "__main__":
    pytest.main([__file__])
