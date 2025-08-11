
"""
Test integracyjny dla pełnego cyklu: Soul → Being → Funkcje
========================================================

Kompletny test tworzenia Soul, Being i wykonywania funkcji.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any

from luxdb.models.soul import Soul
from luxdb.models.being import Being
from database.postgre_db import Postgre_db
import sys
sys.path.insert(0, '.')

# Test functions for the Soul
def simple_function(x: int, y: int = 10) -> int:
    """Simple test function"""
    return x + y


async def async_function(data: str) -> dict:
    """Async test function"""
    await asyncio.sleep(0.01)
    return {"processed": data.upper()}


def init(being_context=None):
    """Initialize being"""
    if being_context:
        print(f"🧬 Initializing being {being_context.get('alias', 'unknown')}")
        return {
            "status": "initialized", 
            "being_alias": being_context.get('alias'),
            "timestamp": datetime.now().isoformat()
        }
    return {"status": "initialized"}


def execute(data=None, **kwargs):
    """Execute function"""
    if data:
        return {
            "result": f"Processed: {data}",
            "timestamp": datetime.now().isoformat(),
            "kwargs": kwargs
        }
    return {"result": "No data provided", "timestamp": datetime.now().isoformat()}


def process_data(input_data: str) -> str:
    """Process some data"""
    return f"PROCESSED: {input_data}"


class TestIntegrationSoulBeingFunctions:
    """Kompletny test integracyjny Soul + Being + Functions"""

    @pytest.fixture
    async def test_soul_with_functions(self):
        """Soul testowy z funkcjami"""
        # Genotyp z funkcjami w module_source
        genotype = {
            "genesis": {
                "name": "integration_test_soul",
                "type": "test_with_functions",
                "version": "1.0.0",
                "description": "Soul for integration testing with functions"
            },
            "attributes": {
                "name": {"py_type": "str", "required": True},
                "value": {"py_type": "int", "default": 0},
                "active": {"py_type": "bool", "default": True}
            },
            "module_source": '''
def init(being_context=None):
    """Initialize being"""
    if being_context:
        print(f"🧬 Initializing being {being_context.get('alias', 'unknown')}")
        return {
            "status": "initialized", 
            "being_alias": being_context.get('alias'),
            "timestamp": "2025-01-30T00:00:00"
        }
    return {"status": "initialized"}

def execute(data=None, **kwargs):
    """Execute function"""
    if data:
        return {
            "result": f"Processed: {data}",
            "timestamp": "2025-01-30T00:00:00",
            "kwargs": kwargs
        }
    return {"result": "No data provided", "timestamp": "2025-01-30T00:00:00"}

def process_data(input_data):
    """Process some data"""
    return f"PROCESSED: {input_data}"

def calculate(a, b, operation="add"):
    """Calculate two numbers"""
    if operation == "add":
        return a + b
    elif operation == "multiply":
        return a * b
    else:
        return 0

async def async_process(data):
    """Async processing"""
    return {"async_result": f"ASYNC: {data}"}

def _private_function():
    """Private function"""
    return "private result"
'''
        }
        
        return await Soul.create(genotype, alias="integration_test_soul")

    async def test_complete_integration_cycle(self, test_soul_with_functions):
        """Test kompletnego cyklu: Soul → Being → Funkcje"""
        print("\n🔄 Testing complete integration cycle...")
        
        soul = test_soul_with_functions
        
        # 1. Sprawdź czy Soul została utworzona poprawnie
        assert soul is not None
        assert soul.soul_hash is not None
        assert soul.alias == "integration_test_soul"
        print(f"✅ Soul created: {soul.soul_hash[:8]}...")
        
        # 2. Sprawdź funkcje w Soul
        functions = soul.list_functions()
        assert len(functions) > 0
        assert "init" in functions
        assert "execute" in functions
        assert "process_data" in functions
        assert "calculate" in functions
        assert "async_process" in functions
        assert "_private_function" in functions  # Prywatne też są w rejestrze
        print(f"✅ Soul has {len(functions)} functions: {functions}")
        
        # 3. Utwórz Being z Soul
        being_data = {
            "name": "Integration Test Being",
            "value": 42,
            "active": True
        }
        
        being = await Being.create(soul=soul, attributes=being_data, alias="integration_test_being")
        assert being is not None
        assert being.ulid is not None
        assert being.soul_hash == soul.soul_hash
        print(f"✅ Being created: {being.ulid}")
        
        # 4. Sprawdź czy Being jest function masterem (ma init)
        assert being.is_function_master() == True
        print("✅ Being is function master")
        
        # 5. Test wywołania funkcji publicznych przez Being
        
        # Test process_data
        result = await being.execute_soul_function("process_data", input_data="test input")
        assert result["success"] == True
        assert result["data"]["result"] == "PROCESSED: test input"
        print("✅ process_data function executed successfully")
        
        # Test calculate
        result = await being.execute_soul_function("calculate", a=10, b=5, operation="add")
        assert result["success"] == True
        assert result["data"]["result"] == 15
        print("✅ calculate function executed successfully")
        
        # Test calculate multiply
        result = await being.execute_soul_function("calculate", a=10, b=5, operation="multiply")
        assert result["success"] == True
        assert result["data"]["result"] == 50
        print("✅ calculate multiply function executed successfully")
        
        # Test async function
        result = await being.execute_soul_function("async_process", data="async test")
        assert result["success"] == True
        assert result["data"]["result"]["async_result"] == "ASYNC: async test"
        print("✅ async_process function executed successfully")
        
        # 6. Test inteligentnego execute (bez podania konkretnej funkcji)
        result = await being.execute(data="intelligent execution test")
        assert result["success"] == True
        assert "Processed: intelligent execution test" in result["data"]["result"]["result"]
        print("✅ Intelligent execute worked")
        
        # 7. Test ręcznego wywołania konkretnej funkcji przez execute
        result = await being.execute(function="process_data", input_data="manual function call")
        assert result["success"] == True
        assert result["data"]["result"] == "PROCESSED: manual function call"
        print("✅ Manual function execution through execute worked")
        
        # 8. Test funkcji init (jeśli nie została automatycznie wywołana)
        result = await being.init()
        assert result["success"] == True
        assert result["data"]["result"]["status"] == "initialized"
        print("✅ Init function executed successfully")
        
        # 9. Sprawdź statystyki Being
        mastery_info = being.get_function_mastery_info()
        assert mastery_info["is_function_master"] == True
        assert len(mastery_info["managed_functions"]) > 0
        assert mastery_info["function_count"] > 0
        print(f"✅ Function mastery info: {mastery_info['function_count']} functions managed")
        
        # 10. Test dostępu do listy funkcji
        available_functions = await being.list_available_functions()
        public_functions = [f for f in available_functions if not f.startswith('_')]
        assert len(public_functions) > 0
        assert "process_data" in public_functions
        assert "calculate" in public_functions
        print(f"✅ Available public functions: {public_functions}")
        
        print("🎉 Complete integration test PASSED!")

    async def test_function_soul_creation(self):
        """Test tworzenia Soul dla pojedynczej funkcji"""
        print("\n🧬 Testing function Soul creation...")
        
        # Utwórz Soul dla pojedynczej funkcji
        soul = await Soul.create_function_soul(
            name="test_func",
            func=simple_function,
            description="Simple test function",
            alias="simple_function_soul"
        )
        
        assert soul is not None
        assert soul.alias == "simple_function_soul"
        assert "test_func" in soul.list_functions()
        print(f"✅ Function Soul created: {soul.alias}")
        
        # Utwórz Being z tą Soul
        being = await Being.create(
            soul=soul,
            attributes={"name": "Function Test Being"},
            alias="function_test_being"
        )
        
        assert being is not None
        print(f"✅ Being created from function Soul: {being.alias}")
        
        # Test wywołania funkcji
        result = await being.execute_soul_function("test_func", x=5, y=3)
        assert result["success"] == True
        assert result["data"]["result"] == 8
        print("✅ Function Soul function executed successfully")

    async def test_soul_without_functions(self):
        """Test Soul bez funkcji"""
        print("\n📋 Testing Soul without functions...")
        
        genotype = {
            "genesis": {
                "name": "simple_soul",
                "type": "no_functions",
                "version": "1.0.0"
            },
            "attributes": {
                "data": {"py_type": "str", "default": "simple"}
            }
        }
        
        soul = await Soul.create(genotype, alias="simple_soul")
        assert soul is not None
        
        functions = soul.list_functions()
        assert len(functions) == 0
        print("✅ Soul without functions created")
        
        # Utwórz Being
        being = await Being.create(
            soul=soul,
            attributes={"data": "test"},
            alias="simple_being"
        )
        
        assert being is not None
        assert being.is_function_master() == False  # Nie ma init
        print("✅ Being from Soul without functions is not a function master")

    async def test_error_handling(self, test_soul_with_functions):
        """Test obsługi błędów"""
        print("\n❌ Testing error handling...")
        
        soul = test_soul_with_functions
        being = await Being.create(
            soul=soul,
            attributes={"name": "Error Test Being"},
            alias="error_test_being"
        )
        
        # Test nieistniejącej funkcji
        result = await being.execute_soul_function("nonexistent_function")
        assert result["success"] == False
        assert "not found" in result["error"].lower()
        print("✅ Nonexistent function error handled correctly")
        
        # Test błędnych argumentów
        result = await being.execute_soul_function("calculate", wrong_arg="value")
        assert result["success"] == False
        print("✅ Wrong arguments error handled correctly")

    async def test_cleanup(self):
        """Cleanup testowych danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                # Usuń testowe Being
                await conn.execute("""
                    DELETE FROM beings 
                    WHERE alias LIKE '%integration_test%' 
                    OR alias LIKE '%function_test%'
                    OR alias LIKE '%simple_%'
                    OR alias LIKE '%error_test%'
                """)
                # Usuń testowe Soul
                await conn.execute("""
                    DELETE FROM souls 
                    WHERE alias LIKE '%integration_test%'
                    OR alias LIKE '%simple_function%'
                    OR alias LIKE '%simple_soul%'
                    OR genotype->>'genesis'->>'type' = 'test_with_functions'
                    OR genotype->>'genesis'->>'type' = 'no_functions'
                """)
                print("✅ Test cleanup completed")
        except Exception as e:
            print(f"Cleanup warning: {e}")


# Uruchomienie testów
async def run_integration_tests():
    """Uruchom testy integracyjne"""
    test_instance = TestIntegrationSoulBeingFunctions()
    
    print("🔄 Uruchamianie testów integracyjnych Soul + Being + Functions...")
    
    # Przygotuj fixture
    test_soul = await test_instance.test_soul_with_functions()
    
    tests = [
        ("Complete Integration Cycle", test_instance.test_complete_integration_cycle(test_soul)),
        ("Function Soul Creation", test_instance.test_function_soul_creation()),
        ("Soul Without Functions", test_instance.test_soul_without_functions()),
        ("Error Handling", test_instance.test_error_handling(test_soul))
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_coro in tests:
        try:
            await test_coro
            print(f"  ✅ {test_name}")
            passed += 1
        except Exception as e:
            print(f"  ❌ {test_name}: {e}")
            failed += 1
    
    # Cleanup
    await test_instance.test_cleanup()
    
    print(f"\n📊 Wyniki testów integracyjnych: {passed} ✅ | {failed} ❌")
    return passed, failed


if __name__ == "__main__":
    asyncio.run(run_integration_tests())
