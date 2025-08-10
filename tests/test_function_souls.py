
"""
Testy jednostkowe dla Soul z funkcjami.
"""

import pytest
import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being


def test_function(x: int, y: int = 10) -> int:
    """Test function"""
    return x + y


async def async_test_function(data: str) -> dict:
    """Async test function"""
    await asyncio.sleep(0.01)
    return {"processed": data.upper()}


class TestFunctionSouls:
    """Test class for function souls"""

    async def test_create_function_soul(self):
        """Test creating a function soul"""
        soul = await Soul.create_function_soul(
            name="test_func",
            func=test_function,
            description="Test function",
            alias="test_soul"
        )
        
        assert soul is not None
        assert soul.alias == "test_soul"
        assert "test_func" in soul.list_functions()
        assert soul.get_function("test_func") == test_function

    async def test_immutable_function_loading(self):
        """Test loading functions in immutable soul"""
        genotype = {
            "genesis": {
                "name": "test_soul",
                "type": "function_test",
                "version": "1.0.0"
            },
            "attributes": {
                "name": {"py_type": "str"}
            },
            "functions": {
                "test_func": {
                    "py_type": "function",
                    "description": "Test function"
                },
                "async_func": {
                    "py_type": "function", 
                    "description": "Async test function"
                }
            }
        }
        
        soul = await Soul.create(genotype, alias="test_soul")
        # Funkcje muszą być załadowane, nie dynamicznie dodawane
        soul._register_immutable_function("test_func", test_function)
        soul._register_immutable_function("async_func", async_test_function)
        
        assert len(soul.list_functions()) == 2
        assert "test_func" in soul.list_functions()
        assert "async_func" in soul.list_functions()

    async def test_execute_function(self):
        """Test executing functions through soul"""
        soul = await Soul.create_function_soul(
            name="test_func",
            func=test_function,
            alias="test_soul"
        )
        
        # Test synchronous function
        result = await soul.execute_function("test_func", 5, y=15)
        assert result["success"] is True
        assert result["data"]["result"] == 20
        assert result["data"]["function_name"] == "test_func"

    async def test_execute_async_function(self):
        """Test executing async functions"""
        genotype = {
            "genesis": {
                "name": "async_soul",
                "type": "async_test",
                "version": "1.0.0"
            },
            "attributes": {
                "name": {"py_type": "str"}
            }
        }
        
        soul = await Soul.create(genotype, alias="async_soul")
        soul.register_function("async_func", async_test_function)
        
        result = await soul.execute_function("async_func", "hello world")
        assert result["success"] is True
        assert result["data"]["result"]["processed"] == "HELLO WORLD"

    async def test_being_function_execution(self):
        """Test executing functions through being"""
        soul = await Soul.create_function_soul(
            name="test_func",
            func=test_function,
            alias="test_soul"
        )
        
        being_result = await Being.set(
            soul=soul,
            data={"name": "test_being"},
            alias="test_being"
        )
        
        assert being_result["success"] is True
        being = being_result["data"]["being"]
        
        # List functions
        functions = await being.list_available_functions()
        assert "test_func" in functions
        
        # Execute function
        result = await being.execute_soul_function("test_func", 10, y=5)
        assert result["success"] is True
        assert result["data"]["result"] == 15

    async def test_function_validation(self):
        """Test function call validation"""
        soul = await Soul.create_function_soul(
            name="test_func",
            func=test_function,
            alias="test_soul"
        )
        
        # Valid call
        errors = soul.validate_function_call("test_func", 5, y=10)
        assert len(errors) == 0
        
        # Invalid function name
        errors = soul.validate_function_call("nonexistent_func", 5)
        assert len(errors) > 0
        assert "not found" in errors[0]

    async def test_function_info(self):
        """Test getting function information"""
        soul = await Soul.create_function_soul(
            name="test_func",
            func=test_function,
            description="Test function",
            alias="test_soul"
        )
        
        info = soul.get_function_info("test_func")
        assert info is not None
        assert info["py_type"] == "function"
        assert info["description"] == "Test function"
        assert info["is_async"] is False
        assert "signature" in info

    async def test_genotype_with_functions(self):
        """Test genotype validation with functions section"""
        from luxdb.utils.validators import validate_genotype
        
        genotype = {
            "genesis": {
                "name": "function_soul",
                "type": "function_test"
            },
            "attributes": {
                "name": {"py_type": "str"}
            },
            "functions": {
                "test_func": {
                    "py_type": "function",
                    "description": "Test function",
                    "is_primary": True
                }
            }
        }
        
        is_valid, errors = validate_genotype(genotype)
        assert is_valid is True
        assert len(errors) == 0

    async def test_invalid_function_genotype(self):
        """Test invalid function genotype"""
        from luxdb.utils.validators import validate_genotype
        
        genotype = {
            "genesis": {
                "name": "function_soul",
                "type": "function_test"
            },
            "functions": {
                "bad_func": {
                    "py_type": "not_function",  # Invalid type
                    "description": "Bad function"
                }
            }
        }
        
        is_valid, errors = validate_genotype(genotype)
        assert is_valid is False
        assert any("must have py_type 'function'" in error for error in errors)

    async def test_soul_versioning(self):
        """Test Soul versioning and evolution"""
        # Create initial version
        soul_v1 = await Soul.create_function_soul(
            name="test_func",
            func=test_function,
            alias="versioned_soul",
            version="1.0.0"
        )
        
        # Evolve to new version
        soul_v2 = await Soul.create_evolved_version(
            original_soul=soul_v1,
            changes={
                "attributes.new_field": {"py_type": "str", "default": "new"}
            },
            new_version="1.1.0"
        )
        
        # Test versioning
        assert soul_v1.get_version() == "1.0.0"
        assert soul_v2.get_version() == "1.1.0"
        assert soul_v2.is_evolution_of(soul_v1)
        assert soul_v1.is_compatible_with(soul_v2)
        
        # Different hashes for different versions
        assert soul_v1.soul_hash != soul_v2.soul_hash

    async def test_soul_lineage(self):
        """Test Soul evolution lineage"""
        # Create chain of evolution
        soul_v1 = await Soul.create_function_soul(
            name="test_func",
            func=test_function,
            alias="lineage_test",
            version="1.0.0"
        )
        
        soul_v2 = await Soul.create_evolved_version(
            original_soul=soul_v1,
            changes={"attributes.field2": {"py_type": "int"}},
            new_version="1.1.0"
        )
        
        soul_v3 = await Soul.create_evolved_version(
            original_soul=soul_v2,
            changes={"attributes.field3": {"py_type": "bool"}},
            new_version="2.0.0"
        )
        
        # Test lineage
        lineage = await soul_v3.get_lineage()
        assert len(lineage) == 3
        assert lineage[0] == soul_v3  # Current
        assert lineage[1] == soul_v2  # Parent
        assert lineage[2] == soul_v1  # Grandparent


if __name__ == "__main__":
    pytest.main([__file__])
