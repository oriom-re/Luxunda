
#!/usr/bin/env python3
"""
🔍 Quick System Check - Sprawdzenie stanu LuxOS/LuxDB
"""

import asyncio
import sys
from pathlib import Path

async def check_database():
    """Test połączenia z bazą danych"""
    try:
        from luxdb.core.postgre_db import Postgre_db
        pool = await Postgre_db.get_db_pool()
        if pool:
            async with pool.acquire() as conn:
                result = await conn.fetch("SELECT 1 as test")
                if result:
                    print("✅ Database: CONNECTED")
                    return True
        print("❌ Database: FAILED")
        return False
    except Exception as e:
        print(f"❌ Database: ERROR - {e}")
        return False

async def check_core_models():
    """Test podstawowych modeli"""
    try:
        from luxdb.models.soul import Soul
        from luxdb.models.being import Being
        print("✅ Core Models: IMPORTED")
        return True
    except Exception as e:
        print(f"❌ Core Models: ERROR - {e}")
        return False

async def check_web_interface():
    """Test interfejsu web"""
    try:
        from luxdb.web_lux_interface import app
        print("✅ Web Interface: AVAILABLE")
        return True
    except Exception as e:
        print(f"❌ Web Interface: ERROR - {e}")
        return False

async def check_basic_functionality():
    """Test podstawowej funkcjonalności"""
    try:
        # Test tworzenia Soul
        simple_genotype = {
            "genesis": {
                "name": "test_soul", 
                "version": "1.0.0"
            },
            "attributes": {
                "message": {"py_type": "str", "default": "Hello World"}
            }
        }
        
        from luxdb.models.soul import Soul
        soul = await Soul.create(simple_genotype, alias="test_check")
        
        if soul:
            print("✅ Soul Creation: WORKING")
            
            # Test tworzenia Being
            from luxdb.models.being import Being
            being = await Being.create(
                soul=soul,
                attributes={"message": "Test successful"},
                persistent=False
            )
            
            if being:
                print("✅ Being Creation: WORKING")
                return True
        
        return False
        
    except Exception as e:
        print(f"❌ Basic Functionality: ERROR - {e}")
        return False

async def main():
    """Główne sprawdzenie systemu"""
    print("🔍 LuxOS/LuxDB System Check")
    print("=" * 40)
    
    results = []
    
    # Sprawdzenie modeli
    models_ok = await check_core_models()
    results.append(models_ok)
    
    # Sprawdzenie bazy danych
    db_ok = await check_database()
    results.append(db_ok)
    
    # Sprawdzenie interfejsu
    web_ok = await check_web_interface()
    results.append(web_ok)
    
    # Test podstawowej funkcjonalności (tylko jeśli baza działa)
    if db_ok:
        func_ok = await check_basic_functionality()
        results.append(func_ok)
    else:
        print("⚠️ Skipping functionality tests (database not available)")
        results.append(False)
    
    print("\n" + "=" * 40)
    
    if all(results):
        print("🎉 System Status: WSZYSTKO DZIAŁA!")
        print("💡 Uruchom: python main.py")
        return 0
    else:
        print("⚠️ System Status: PROBLEMY WYKRYTE")
        print("💡 Sprawdź konfigurację bazy danych")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
