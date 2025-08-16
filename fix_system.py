
#!/usr/bin/env python3
"""
🔧 System Fix - Naprawienie podstawowych problemów LuxOS
"""

import asyncio
import os
from pathlib import Path

async def setup_database():
    """Inicjalizacja bazy danych"""
    try:
        from luxdb.core.postgre_db import Postgre_db
        
        print("🔧 Initializing database tables...")
        
        # Spróbuj połączyć się z bazą
        pool = await Postgre_db.get_db_pool()
        if not pool:
            print("❌ Cannot connect to database. Check environment variables:")
            print("   POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB")
            return False
        
        async with pool.acquire() as conn:
            # Sprawdź czy tabele istnieją
            result = await conn.fetch("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'souls'
            """)
            
            if not result:
                print("🔧 Creating core tables...")
                await Postgre_db.initialize_tables()
            
        print("✅ Database setup complete")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

async def test_basic_operations():
    """Test podstawowych operacji"""
    try:
        from luxdb.models.soul import Soul
        from luxdb.models.being import Being
        
        print("🧪 Testing basic operations...")
        
        # Test Soul
        test_genotype = {
            "genesis": {
                "name": "system_test",
                "version": "1.0.0",
                "description": "System test genotype"
            },
            "attributes": {
                "status": {"py_type": "str", "default": "active"},
                "counter": {"py_type": "int", "default": 0}
            }
        }
        
        soul = await Soul.create(test_genotype, alias="system_test")
        print(f"✅ Soul created: {soul.soul_hash[:8]}...")
        
        # Test Being
        being = await Being.create(
            soul=soul,
            attributes={
                "status": "testing",
                "counter": 42
            },
            persistent=True
        )
        print(f"✅ Being created: {being.ulid[:8]}...")
        
        # Test retrieval
        loaded_souls = await Soul.get_all()
        loaded_beings = await Being.get_all()
        
        print(f"✅ System contains: {len(loaded_souls)} souls, {len(loaded_beings)} beings")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic operations failed: {e}")
        return False

async def main():
    """Główna naprawa systemu"""
    print("🔧 LuxOS System Repair")
    print("=" * 40)
    
    # 1. Setup bazy danych
    db_ok = await setup_database()
    
    if not db_ok:
        print("❌ Cannot proceed without database")
        return 1
    
    # 2. Test podstawowych operacji
    ops_ok = await test_basic_operations()
    
    if ops_ok:
        print("\n🎉 System repair completed successfully!")
        print("💡 System is ready to use. Run: python main.py")
        return 0
    else:
        print("\n⚠️ Some issues remain. Check error messages above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
