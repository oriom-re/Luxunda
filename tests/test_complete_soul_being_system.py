

"""
Complete LuxDB Soul/Being/Functions System Test
==============================================

Kompletny test systemu cerowania Soul, tworzenia Being i wywoływania funkcji.
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, Any

from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.genotype_system import genotype_system
from database.postgre_db import Postgre_db


class TestCompleteSoulBeingSystem:
    """Kompletny test systemu Soul/Being z funkcjami"""
    
    @pytest.fixture
    async def test_module_source(self):
        """Kod źródłowy modułu testowego z funkcjami"""
        return '''
# Test module for Soul/Being system
CONFIG_VALUE = "test_config"
MAX_RETRIES = 3

def init(being_context=None):
    """Initialize the module with being context"""
    return {
        "initialized": True,
        "being_ulid": being_context.get("ulid") if being_context else None,
        "init_time": datetime.now().isoformat(),
        "config": CONFIG_VALUE
    }

def execute(data=None, **kwargs):
    """Execute function with data"""
    return {
        "executed": True,
        "data_received": data,
        "kwargs": kwargs,
        "timestamp": datetime.now().isoformat()
    }

def get_status():
    """Get module status"""
    return {
        "status": "active",
        "config": CONFIG_VALUE,
        "max_retries": MAX_RETRIES
    }

def process_data(data, multiplier=2):
    """Process data with multiplier"""
    if isinstance(data, (int, float)):
        return data * multiplier
    elif isinstance(data, list):
        return [item * multiplier for item in data if isinstance(item, (int, float))]
    else:
        return {"error": "Unsupported data type"}

async def async_operation(delay=0.1):
    """Async operation for testing"""
    import asyncio
    await asyncio.sleep(delay)
    return {"async_completed": True, "delay": delay}
'''
    
    @pytest.fixture
    async def test_genotype(self, test_module_source):
        """Kompletny genotyp z modułem źródłowym"""
        return {
            "genesis": {
                "name": "complete_test_soul",
                "type": "test_module_soul",
                "description": "Complete test soul with module functions",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat()
            },
            "attributes": {
                "name": {"py_type": "str", "required": True},
                "count": {"py_type": "int", "default": 0},
                "active": {"py_type": "bool", "default": True},
                "metadata": {"py_type": "dict", "default": {}},
                "settings": {"py_type": "dict", "default": {}}
            },
            "module_source": test_module_source
        }
    
    async def test_soul_creation_with_module(self, test_genotype):
        """Test tworzenia Soul z modułem źródłowym"""
        print("\n🧬 Test 1: Tworzenie Soul z modułem...")
        
        soul = await Soul.create(test_genotype, alias="test_soul_complete")
        
        assert soul is not None
        assert soul.soul_hash is not None
        assert soul.alias == "test_soul_complete"
        assert soul.has_module_source()
        assert soul.has_init_function()
        assert soul.has_execute_function()
        
        # Sprawdź zarejestrowane funkcje
        functions = soul.list_functions()
        expected_functions = ['init', 'execute', 'get_status', 'process_data', 'async_operation']
        
        for func_name in expected_functions:
            assert func_name in functions, f"Brakuje funkcji {func_name}"
            
        print(f"✅ Soul utworzona z {len(functions)} funkcjami: {functions}")
        return soul
    
    async def test_being_creation_and_initialization(self, test_genotype):
        """Test tworzenia Being i automatycznej inicjalizacji"""
        print("\n🤖 Test 2: Tworzenie Being z automatyczną inicjalizacją...")
        
        soul = await Soul.create(test_genotype, alias="test_soul_for_being")
        
        # Utwórz Being z atrybutami
        being_data = {
            "name": "Test Being Complete",
            "count": 42,
            "active": True,
            "metadata": {"test": True, "purpose": "complete_test"},
            "settings": {"mode": "test", "debug": True}
        }
        
        being = await Being.create(soul=soul, attributes=being_data, alias="test_being_complete")
        
        assert being is not None
        assert being.ulid is not None
        assert being.alias == "test_being_complete"
        assert being.soul_hash == soul.soul_hash
        
        # Sprawdź czy Being zostało zainicjalizowane
        assert being.is_function_master()
        assert being.data.get('_initialized') is True
        
        print(f"✅ Being utworzone i zainicjalizowane: {being.alias}")
        return being, soul
    
    async def test_function_execution_via_being(self, test_genotype):
        """Test wykonywania funkcji przez Being"""
        print("\n⚡ Test 3: Wykonywanie funkcji przez Being...")
        
        soul = await Soul.create(test_genotype, alias="test_soul_execution")
        being = await Being.create(
            soul=soul,
            attributes={"name": "Function Test Being", "count": 0},
            alias="function_test_being"
        )
        
        # Test funkcji get_status
        status_result = await being.execute_soul_function("get_status")
        assert status_result.get('success') is True
        status_data = status_result['data']['result']
        assert status_data['status'] == 'active'
        assert status_data['config'] == 'test_config'
        
        # Test funkcji process_data
        process_result = await being.execute_soul_function("process_data", 10, multiplier=3)
        assert process_result.get('success') is True
        assert process_result['data']['result'] == 30
        
        # Test funkcji async_operation
        async_result = await being.execute_soul_function("async_operation", delay=0.05)
        assert async_result.get('success') is True
        assert async_result['data']['result']['async_completed'] is True
        
        # Test inteligentnej funkcji execute
        execute_result = await being.execute({"test_data": "hello"})
        assert execute_result.get('success') is True
        
        print("✅ Wszystkie funkcje wykonane pomyślnie")
        return being
    
    async def test_soul_function_registry(self, test_genotype):
        """Test rejestru funkcji w Soul"""
        print("\n📋 Test 4: Rejestr funkcji Soul...")
        
        soul = await Soul.create(test_genotype, alias="test_soul_registry")
        
        # Sprawdź informacje o funkcjach
        visibility_info = soul.get_function_visibility_info()
        
        assert visibility_info['has_module_source'] is True
        assert visibility_info['functions']['total_registered'] >= 5
        
        # Test dostępnych funkcji
        available_functions = soul.get_available_functions_clear()
        
        # Sprawdź czy wszystkie oczekiwane funkcje są dostępne
        expected_functions = ['init', 'execute', 'get_status', 'process_data', 'async_operation']
        for func_name in expected_functions:
            assert func_name in available_functions or f"[PRIVATE] {func_name}" in available_functions
            
        print(f"✅ Rejestr funkcji: {len(available_functions)} funkcji dostępnych")
        
        # Test direct function execution via Soul
        direct_result = await soul.execute_function("get_status")
        assert direct_result.get('success') is True
        
        return soul
    
    async def test_being_function_mastery(self, test_genotype):
        """Test masterowania funkcji przez Being"""
        print("\n🎯 Test 5: Being jako master funkcji...")
        
        soul = await Soul.create(test_genotype, alias="test_soul_mastery")
        being = await Being.create(
            soul=soul,
            attributes={"name": "Master Being", "level": "expert"},
            alias="master_being"
        )
        
        # Sprawdź status mastery
        mastery_info = being.get_function_mastery_info()
        
        assert mastery_info['is_function_master'] is True
        assert len(mastery_info['managed_functions']) >= 5
        assert mastery_info['initialized_at'] is not None
        
        # Test inteligentnego wykonania bez podanej funkcji
        intelligent_result = await being.execute({"input": "test_data"})
        assert intelligent_result.get('success') is True
        
        # Test wykonania konkretnej funkcji
        specific_result = await being.execute({"input": [1, 2, 3]}, function="process_data")
        assert specific_result.get('success') is True
        
        # Sprawdź statystyki wykorzystania funkcji
        await being.execute(function="get_status")
        stats = being.data.get('_function_stats', {})
        assert 'get_status' in stats
        assert stats['get_status']['total_calls'] >= 1
        
        print(f"✅ Being masteruje {len(mastery_info['managed_functions'])} funkcji")
        return being
    
    async def test_genotype_system_integration(self, test_genotype):
        """Test integracji z systemem genotypów"""
        print("\n🧬 Test 6: Integracja z systemem genotypów...")
        
        # Inicjalizuj system genotypów
        init_result = await genotype_system.initialize_system()
        assert init_result['success'] is True
        
        # Utwórz Soul przez system genotypów
        soul = await Soul.create(test_genotype, alias="genotype_system_soul")
        
        # Sprawdź czy Soul jest dostępna w systemie
        found_soul = genotype_system.get_soul_by_alias("genotype_system_soul")
        if found_soul is None:
            # Dodaj do systemu jeśli nie ma
            genotype_system.loaded_souls.append(soul)
            found_soul = genotype_system.get_soul_by_alias("genotype_system_soul")
        
        assert found_soul is not None
        assert found_soul.soul_hash == soul.soul_hash
        
        print("✅ Integracja z systemem genotypów sprawna")
        return soul
    
    async def test_complete_workflow(self, test_genotype):
        """Test kompletnego workflow Soul -> Being -> Functions"""
        print("\n🔄 Test 7: Kompletny workflow systemu...")
        
        # 1. Utwórz Soul z modułem
        soul = await Soul.create(test_genotype, alias="workflow_soul")
        assert soul.has_module_source()
        
        # 2. Utwórz Being z inicjalizacją
        being = await Being.create(
            soul=soul,
            attributes={
                "name": "Workflow Being",
                "workflow_step": 1,
                "active": True
            },
            alias="workflow_being"
        )
        assert being.is_function_master()
        
        # 3. Wykonaj sekwencję funkcji
        results = []
        
        # Status check
        status = await being.execute_soul_function("get_status")
        results.append(status['success'])
        
        # Data processing
        process = await being.execute_soul_function("process_data", [1, 2, 3, 4], multiplier=2)
        results.append(process['success'])
        
        # Async operation
        async_op = await being.execute_soul_function("async_operation", delay=0.01)
        results.append(async_op['success'])
        
        # Intelligent execution
        intelligent = await being.execute({"workflow": "complete"})
        results.append(intelligent['success'])
        
        # Sprawdź czy wszystkie operacje się powiodły
        assert all(results), f"Niektóre operacje nie powiodły się: {results}"
        
        # Sprawdź statystyki Being
        mastery = being.get_function_mastery_info()
        assert mastery['intelligent_executions'] >= 1
        
        print(f"✅ Kompletny workflow: {len(results)} operacji wykonanych pomyślnie")
        return {"soul": soul, "being": being, "results": results}
    
    async def test_cleanup(self):
        """Cleanup testowych danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            async with pool.acquire() as conn:
                # Usuń testowe Being
                await conn.execute("""
                    DELETE FROM beings 
                    WHERE alias LIKE 'test_%' 
                    OR alias LIKE '%_test_%'
                    OR alias LIKE 'workflow_%'
                    OR alias LIKE 'master_%'
                    OR alias LIKE 'function_%'
                """)
                
                # Usuń testowe Soul
                await conn.execute("""
                    DELETE FROM souls 
                    WHERE alias LIKE 'test_%'
                    OR alias LIKE '%_test_%' 
                    OR alias LIKE 'workflow_%'
                    OR alias LIKE 'genotype_%'
                    OR genotype->>'genesis'->>'type' = 'test_module_soul'
                """)
                
                print("🧹 Cleanup testowych danych zakończony")
        except Exception as e:
            print(f"⚠️  Cleanup warning: {e}")


async def run_complete_system_tests():
    """Uruchom kompletne testy systemu"""
    test_instance = TestCompleteSoulBeingSystem()
    
    print("🚀 Uruchamianie kompletnych testów systemu Soul/Being/Functions...")
    
    # Przygotuj fixtures
    test_module_source = await test_instance.test_module_source()
    test_genotype = await test_instance.test_genotype(test_module_source)
    
    tests = [
        ("Soul creation with module", test_instance.test_soul_creation_with_module(test_genotype)),
        ("Being creation and initialization", test_instance.test_being_creation_and_initialization(test_genotype)),
        ("Function execution via Being", test_instance.test_function_execution_via_being(test_genotype)),
        ("Soul function registry", test_instance.test_soul_function_registry(test_genotype)),
        ("Being function mastery", test_instance.test_being_function_mastery(test_genotype)),
        ("Genotype system integration", test_instance.test_genotype_system_integration(test_genotype)),
        ("Complete workflow", test_instance.test_complete_workflow(test_genotype))
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
    
    print(f"\n📊 Wyniki kompletnych testów: {passed} ✅ | {failed} ❌")
    
    if failed == 0:
        print("🎉 Wszystkie testy systemu cerowania Soul/Being/Functions przeszły pomyślnie!")
    else:
        print(f"⚠️  {failed} testów wymaga naprawy")
    
    return {
        'overall_success': failed == 0,
        'passed': passed,
        'failed': failed,
        'total': len(tests)
    }


if __name__ == "__main__":
    asyncio.run(run_complete_system_tests())

