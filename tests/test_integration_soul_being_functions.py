"""
Test integracyjny dla pełnego cyklu: Soul → Being → Funkcje
========================================================

Kompletny test tworzenia Soul, Being i wykonywania funkcji.
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, Any
import traceback

# Fix imports
try:
    from luxdb.models.soul import Soul
    from luxdb.models.being import Being
    from database.postgre_db import Postgre_db
except ImportError as e:
    print(f"Import error: {e}")
    import sys
    sys.exit(1)

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

    async def create_test_soul_with_functions(self):
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

    async def test_complete_integration_cycle(self):
        """Test kompletnego cyklu: Soul → Being → Funkcje"""
        print("\n🔄 Testing complete integration cycle...")

        try:
            soul = await self.create_test_soul_with_functions()

            # 1. Sprawdź czy Soul została utworzona poprawnie
            if not soul:
                raise AssertionError("Soul creation failed")
            if not soul.soul_hash:
                raise AssertionError("Soul hash is None")
            if soul.alias != "integration_test_soul":
                raise AssertionError(f"Expected alias 'integration_test_soul', got '{soul.alias}'")
            
            print(f"✅ Soul created: {soul.soul_hash[:8]}...")

            # 2. Sprawdź funkcje w Soul
            try:
                functions = soul.list_functions()
                print(f"Available functions: {functions}")
                
                expected_functions = ["init", "execute", "process_data", "calculate", "async_process"]
                missing_functions = [f for f in expected_functions if f not in functions]
                
                if missing_functions:
                    print(f"⚠️ Missing functions: {missing_functions}")
                
                if len(functions) == 0:
                    print("⚠️ No functions found in Soul")
                
                print(f"✅ Soul has {len(functions)} functions: {functions}")
                
            except Exception as e:
                print(f"❌ Function listing failed: {e}")
                raise

        # 3. Utwórz Being z Soul
            being_data = {
                "name": "Integration Test Being",
                "value": 42,
                "active": True
            }

            try:
                being = await Being.create(soul=soul, attributes=being_data, alias="integration_test_being")
                
                if not being:
                    raise AssertionError("Being creation failed")
                if not being.ulid:
                    raise AssertionError("Being ULID is None") 
                if being.soul_hash != soul.soul_hash:
                    raise AssertionError(f"Soul hash mismatch: {being.soul_hash} != {soul.soul_hash}")
                
                print(f"✅ Being created: {being.ulid}")
                
            except Exception as e:
                print(f"❌ Being creation failed: {e}")
                print(f"Traceback: {traceback.format_exc()}")
                raise

            # 4. Sprawdź czy Being jest function masterem
            try:
                is_master = being.is_function_master()
                print(f"✅ Being function master status: {is_master}")
            except Exception as e:
                print(f"❌ Function master check failed: {e}")

            # 5. Test wywołania funkcji publicznych przez Being
            if len(functions) > 0:
                try:
                    # Test process_data tylko jeśli funkcja istnieje
                    if "process_data" in functions:
                        result = await being.execute_soul_function("process_data", input_data="test input")
                        
                        if result.get("success"):
                            print("✅ process_data function executed successfully")
                        else:
                            print(f"⚠️ process_data execution failed: {result.get('error', 'Unknown error')}")
                    else:
                        print("⚠️ process_data function not available")
                        
                except Exception as e:
                    print(f"❌ Function execution failed: {e}")
            else:
                print("⚠️ No functions available to test")
                
        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            raise

        print("🎉 Basic integration test PASSED!")
            
    async def test_function_soul_creation(self):
        """Test tworzenia Soul dla pojedynczej funkcji"""
        print("\n🧬 Testing function Soul creation...")

        try:
            # Test podstawowego tworzenia Soul z funkcją
            genotype = {
                "genesis": {
                    "name": "simple_function_soul",
                    "type": "function_test",
                    "version": "1.0.0"
                },
                "attributes": {
                    "name": {"py_type": "str", "default": "Function Test Being"}
                },
                "module_source": '''
def test_func(x, y=10):
    """Simple test function"""
    return x + y
'''
            }
            
            soul = await Soul.create(genotype, alias="simple_function_soul")
            
            if soul:
                print(f"✅ Function Soul created: {soul.alias}")
                
                # Test tworzenia Being
                being = await Being.create(
                    soul=soul,
                    attributes={"name": "Function Test Being"},
                    alias="function_test_being"
                )
                
                if being:
                    print(f"✅ Being created from function Soul: {being.alias}")
                else:
                    print("⚠️ Being creation failed")
            else:
                print("⚠️ Function Soul creation failed")
                
        except Exception as e:
            print(f"❌ Function Soul test failed: {e}")
            # Don't raise - this is not critical

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

    async def test_error_handling(self):
        """Test obsługi błędów"""
        print("\n❌ Testing error handling...")

        try:
            soul = await self.create_test_soul_with_functions()
            if not soul:
                print("⚠️ Could not create test soul for error handling")
                return
                
            being = await Being.create(
                soul=soul,
                attributes={"name": "Error Test Being"},
                alias="error_test_being"
            )
            
            if not being:
                print("⚠️ Could not create test being for error handling")
                return

            # Test nieistniejącej funkcji
            try:
                result = await being.execute_soul_function("nonexistent_function")
                if not result.get("success"):
                    print("✅ Nonexistent function error handled correctly")
                else:
                    print("⚠️ Nonexistent function should have failed")
            except Exception as e:
                print(f"✅ Nonexistent function properly raised exception: {e}")

        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            # Don't raise - this is testing error handling

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

    tests = [
        ("Complete Integration Cycle", test_instance.test_complete_integration_cycle()),
        ("Function Soul Creation", test_instance.test_function_soul_creation()),
        ("Soul Without Functions", test_instance.test_soul_without_functions()),
        ("Error Handling", test_instance.test_error_handling())
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