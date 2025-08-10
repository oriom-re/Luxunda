
"""
LuxDB System Initialization Tests
================================

Testy inicjalizacji i uruchomienia całego systemu LuxDB.
"""

import pytest
import asyncio
import os
from datetime import datetime
from typing import Dict, Any

from luxdb.core.luxdb import LuxDB
from luxdb.core.kernel_system import kernel_system
from luxdb.core.admin_kernel import admin_kernel
from luxdb.core.auth_session import auth_manager
from luxdb.core.communication_system import communication_system
from database.postgre_db import Postgre_db


class TestSystemInitialization:
    """Testy inicjalizacji systemu"""
    
    def __init__(self):
        self.test_db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'database': os.getenv('DB_NAME', 'luxdb_test'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
    
    async def test_database_connection(self):
        """Test połączenia z bazą danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            
            async with pool.acquire() as conn:
                # Test podstawowego zapytania
                result = await conn.fetchval("SELECT 1")
                assert result == 1
                
                # Test dostępu do tabel
                tables = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                
                table_names = [row['table_name'] for row in tables]
                required_tables = ['souls', 'beings', 'relationships']
                
                for table in required_tables:
                    assert table in table_names, f"Brakuje tabeli {table}"
            
            return True
            
        except Exception as e:
            raise AssertionError(f"Database connection failed: {e}")
    
    async def test_luxdb_initialization(self):
        """Test inicjalizacji głównej klasy LuxDB"""
        try:
            luxdb = LuxDB(**self.test_db_config)
            await luxdb.initialize()
            
            # Test czy LuxDB jest poprawnie zainicjalizowane
            assert luxdb.pool is not None
            
            # Test podstawowych operacji
            status = await luxdb.get_system_status()
            assert isinstance(status, dict)
            
            return True
            
        except Exception as e:
            raise AssertionError(f"LuxDB initialization failed: {e}")
    
    async def test_kernel_system_initialization(self):
        """Test inicjalizacji systemu kernel"""
        try:
            await kernel_system.initialize("basic")
            
            # Sprawdź status
            status = await kernel_system.get_system_status()
            
            assert status is not None
            assert 'active_scenario' in status
            assert 'kernel_beings' in status
            assert status['active_scenario'] == 'basic'
            
            return True
            
        except Exception as e:
            raise AssertionError(f"Kernel system initialization failed: {e}")
    
    async def test_admin_kernel_initialization(self):
        """Test inicjalizacji admin kernel"""
        try:
            await admin_kernel.initialize()
            
            # Sprawdź status
            assert admin_kernel.system_status is not None
            assert 'kernel_active' in admin_kernel.system_status
            assert 'lux_active' in admin_kernel.system_status
            
            return True
            
        except Exception as e:
            raise AssertionError(f"Admin kernel initialization failed: {e}")
    
    async def test_auth_manager_initialization(self):
        """Test inicjalizacji managera uwierzytelniania"""
        try:
            await auth_manager.initialize()
            
            # Test podstawowych operacji
            assert auth_manager.is_initialized is True
            
            return True
            
        except Exception as e:
            raise AssertionError(f"Auth manager initialization failed: {e}")
    
    async def test_communication_system_initialization(self):
        """Test inicjalizacji systemu komunikacji"""
        try:
            await communication_system.initialize()
            
            # Sprawdź czy system jest aktywny
            assert communication_system.is_active is True
            
            return True
            
        except Exception as e:
            raise AssertionError(f"Communication system initialization failed: {e}")
    
    async def test_database_schema_validation(self):
        """Test walidacji schematu bazy danych"""
        try:
            pool = await Postgre_db.get_db_pool()
            
            async with pool.acquire() as conn:
                # Sprawdź strukturę tabeli souls
                souls_columns = await conn.fetch("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'souls'
                """)
                
                souls_column_names = [row['column_name'] for row in souls_columns]
                required_souls_columns = ['soul_hash', 'alias', 'genotype', 'created_at']
                
                for col in required_souls_columns:
                    assert col in souls_column_names, f"Brakuje kolumny {col} w tabeli souls"
                
                # Sprawdź strukturę tabeli beings
                beings_columns = await conn.fetch("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'beings'
                """)
                
                beings_column_names = [row['column_name'] for row in beings_columns]
                required_beings_columns = ['ulid', 'soul_hash', 'created_at']
                
                for col in required_beings_columns:
                    assert col in beings_column_names, f"Brakuje kolumny {col} w tabeli beings"
            
            return True
            
        except Exception as e:
            raise AssertionError(f"Database schema validation failed: {e}")
    
    async def test_system_dependencies(self):
        """Test zależności systemu"""
        try:
            # Test importów
            from luxdb.models.soul import Soul
            from luxdb.models.being import Being
            from luxdb.models.relationship import Relationship
            from luxdb.utils.validators import validate_genotype
            from luxdb.utils.serializer import JsonbSerializer
            
            # Test czy klasy są dostępne
            assert Soul is not None
            assert Being is not None
            assert Relationship is not None
            assert validate_genotype is not None
            assert JsonbSerializer is not None
            
            return True
            
        except Exception as e:
            raise AssertionError(f"System dependencies check failed: {e}")
    
    async def test_environment_variables(self):
        """Test zmiennych środowiskowych"""
        try:
            # Sprawdź kluczowe zmienne
            required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER']
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            # Nie wszystkie muszą być ustawione (mają domyślne wartości)
            # ale sprawdźmy czy są dostępne
            
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = int(os.getenv('DB_PORT', 5432))
            db_name = os.getenv('DB_NAME', 'luxdb_test')
            
            assert isinstance(db_host, str)
            assert isinstance(db_port, int)
            assert isinstance(db_name, str)
            
            return True
            
        except Exception as e:
            raise AssertionError(f"Environment variables check failed: {e}")
    
    async def test_full_system_startup(self):
        """Test pełnego uruchomienia systemu"""
        try:
            # Inicjalizuj komponenty w kolejności
            
            # 1. Baza danych
            pool = await Postgre_db.get_db_pool()
            assert pool is not None
            
            # 2. LuxDB core
            luxdb = LuxDB(**self.test_db_config)
            await luxdb.initialize()
            
            # 3. Kernel system
            await kernel_system.initialize("basic")
            
            # 4. Admin kernel
            await admin_kernel.initialize()
            
            # 5. Auth manager
            await auth_manager.initialize()
            
            # 6. Communication system
            await communication_system.initialize()
            
            # Test czy wszystko działa razem
            status = await luxdb.get_system_status()
            assert status is not None
            
            kernel_status = await kernel_system.get_system_status()
            assert kernel_status is not None
            
            return True
            
        except Exception as e:
            raise AssertionError(f"Full system startup failed: {e}")
    
    async def test_system_performance(self):
        """Test wydajności systemu"""
        try:
            start_time = datetime.now()
            
            # Test szybkości inicjalizacji
            luxdb = LuxDB(**self.test_db_config)
            await luxdb.initialize()
            
            init_time = (datetime.now() - start_time).total_seconds()
            
            # Inicjalizacja powinna zająć mniej niż 10 sekund
            assert init_time < 10, f"Initialization too slow: {init_time}s"
            
            # Test szybkości podstawowych operacji
            pool = await Postgre_db.get_db_pool()
            
            query_start = datetime.now()
            async with pool.acquire() as conn:
                await conn.fetchval("SELECT COUNT(*) FROM souls")
            query_time = (datetime.now() - query_start).total_seconds()
            
            # Zapytanie powinno zająć mniej niż 1 sekundę
            assert query_time < 1, f"Query too slow: {query_time}s"
            
            return True
            
        except Exception as e:
            raise AssertionError(f"System performance test failed: {e}")


# Uruchomienie testów
async def run_initialization_tests():
    """Uruchom testy inicjalizacji"""
    test_instance = TestSystemInitialization()
    
    print("🚀 Uruchamianie testów inicjalizacji systemu...")
    
    tests = [
        ("Połączenie z bazą danych", test_instance.test_database_connection()),
        ("Inicjalizacja LuxDB", test_instance.test_luxdb_initialization()),
        ("Inicjalizacja Kernel System", test_instance.test_kernel_system_initialization()),
        ("Inicjalizacja Admin Kernel", test_instance.test_admin_kernel_initialization()),
        ("Inicjalizacja Auth Manager", test_instance.test_auth_manager_initialization()),
        ("Inicjalizacja Communication System", test_instance.test_communication_system_initialization()),
        ("Walidacja schematu bazy", test_instance.test_database_schema_validation()),
        ("Zależności systemu", test_instance.test_system_dependencies()),
        ("Zmienne środowiskowe", test_instance.test_environment_variables()),
        ("Pełne uruchomienie systemu", test_instance.test_full_system_startup()),
        ("Wydajność systemu", test_instance.test_system_performance())
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
    
    print(f"\n📊 Wyniki testów inicjalizacji: {passed} ✅ | {failed} ❌")
    
    return {
        'overall_success': failed == 0,
        'passed': passed,
        'failed': failed,
        'total': len(tests)
    }


if __name__ == "__main__":
    asyncio.run(run_initialization_tests())
