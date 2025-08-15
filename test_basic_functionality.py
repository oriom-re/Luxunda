
#!/usr/bin/env python3
"""
🧪 LuxOS Basic Functionality Tests
==================================

Quick tests to verify core system functionality
"""

import asyncio
import pytest
from luxdb.core.luxdb import LuxDB
from luxdb.models.soul import Soul
from luxdb.models.being import Being

class TestBasicFunctionality:
    """Basic functionality test suite"""
    
    async def test_database_connection(self):
        """Test database connectivity"""
        db = LuxDB(use_existing_pool=True)
        await db.initialize()
        
        health = await db.health_check()
        assert health['status'] == 'healthy'
        
        await db.close()
        print("✅ Database connection test passed")
    
    async def test_soul_creation(self):
        """Test Soul creation and hash generation"""
        genotype = {
            "genesis": {"name": "test", "version": "1.0.0"},
            "module_source": "def hello(): return 'world'"
        }
        
        soul = await Soul.create(genotype, "test_soul")
        
        assert soul.soul_hash is not None
        assert len(soul.soul_hash) == 64  # SHA-256 hex
        assert soul.alias == "test_soul"
        assert soul.get_functions_count() > 0
        
        print(f"✅ Soul creation test passed: {soul.soul_hash[:16]}...")
    
    async def test_being_creation(self):
        """Test Being creation with data"""
        genotype = {
            "genesis": {"name": "data_holder", "version": "1.0.0"},
            "attributes": {
                "name": {"py_type": "str"},
                "count": {"py_type": "int", "default": 0}
            },
            "module_source": """
def get_info(being_context=None):
    data = being_context.get('data', {})
    return {"name": data.get('name'), "count": data.get('count', 0)}

def execute(request=None, being_context=None, **kwargs):
    return get_info(being_context)
"""
        }
        
        soul = await Soul.create(genotype, "data_holder")
        being = await Being.create(soul, attributes={"name": "Test", "count": 42}, alias="test_being")
        
        assert being.ulid is not None
        assert len(being.ulid) == 26  # ULID length
        assert being.alias == "test_being"
        assert being.data["name"] == "Test"
        assert being.data["count"] == 42
        
        print(f"✅ Being creation test passed: {being.ulid[:8]}...")
    
    async def test_function_execution(self):
        """Test function execution through Being"""
        genotype = {
            "genesis": {"name": "calculator", "version": "1.0.0"},
            "module_source": """
def add(a, b):
    return a + b

def execute(request=None, being_context=None, **kwargs):
    if request and request.get('action') == 'add':
        return add(request.get('a', 0), request.get('b', 0))
    return {"status": "ready"}
"""
        }
        
        soul = await Soul.create(genotype, "test_calculator")
        
        # Test direct Soul execution
        result = await soul.execute_directly("add", a=5, b=3)
        assert result['data']['result'] == 8
        
        # Test Being execution
        being = await Being.create(soul, alias="calc_being")
        result2 = await being.execute_soul_function("execute", request={"action": "add", "a": 10, "b": 20})
        assert result2['data']['result'] == 30
        
        print("✅ Function execution test passed")
    
    async def test_hash_consistency(self):
        """Test hash consistency and immutability"""
        genotype = {
            "genesis": {"name": "test", "version": "1.0.0"},
            "module_source": "def test(): return 'consistent'"
        }
        
        soul1 = await Soul.create(genotype, "consistency_test_1")
        soul2 = await Soul.create(genotype, "consistency_test_2")
        
        # Same genotype should produce same hash
        assert soul1.soul_hash == soul2.soul_hash
        
        # Different genotype should produce different hash
        different_genotype = {
            "genesis": {"name": "test", "version": "1.0.0"},
            "module_source": "def test(): return 'different'"
        }
        
        soul3 = await Soul.create(different_genotype, "different_test")
        assert soul1.soul_hash != soul3.soul_hash
        
        print("✅ Hash consistency test passed")

async def run_all_tests():
    """Run all basic functionality tests"""
    print("🧪 LuxOS Basic Functionality Tests")
    print("=" * 40)
    
    test_suite = TestBasicFunctionality()
    
    try:
        await test_suite.test_database_connection()
        await test_suite.test_soul_creation()
        await test_suite.test_being_creation()
        await test_suite.test_function_execution()
        await test_suite.test_hash_consistency()
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
