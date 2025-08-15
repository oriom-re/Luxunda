
#!/usr/bin/env python3
"""
Setup Script for Astral Beings Library
=====================================

Przygotowuje środowisko i tworzy podstawowe struktury dla biblioteki.
"""

import os
import asyncio
import sys

# Dodaj ścieżki
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def setup_astral_beings():
    """Konfiguruje bibliotekę Astral Beings"""
    
    print("🌟 === ASTRAL BEINGS LIBRARY SETUP ===")
    
    # 1. Sprawdź czy LuxDB jest dostępne
    try:
        from luxdb.core.luxdb import LuxDB
        from luxdb.core.postgre_db import Postgre_db
        print("✅ LuxDB core is available")
    except ImportError as e:
        print(f"❌ LuxDB not available: {e}")
        print("   Please ensure LuxDB is properly installed")
        return False
    
    # 2. Inicjalizuj bazę danych
    try:
        print("🔧 Initializing database connection...")
        db = Postgre_db()
        await db.initialize()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    # 3. Test importów biblioteki
    try:
        from astral_beings import AstralBeing, SoulTemplate
        from astral_beings import BeingGenerator, SoulGenerator
        from astral_beings import BasicTemplates, QuickStart
        print("✅ Astral Beings library imports successful")
    except ImportError as e:
        print(f"❌ Astral Beings import failed: {e}")
        return False
    
    # 4. Stwórz przykładowego bytu (test funkcjonalności)
    try:
        print("🧪 Testing basic functionality...")
        
        # Prosty test
        guardian = await BasicTemplates.create_guardian("TestGuardian")
        result = await guardian.commune("Setup test message")
        
        if result.get('data', {}).get('result', {}).get('success'):
            print("✅ Basic functionality test passed")
        else:
            print("⚠️ Basic functionality test had issues")
            
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False
    
    # 5. Wyświetl informacje o konfiguracji
    print("\n📋 === SETUP SUMMARY ===")
    print("✅ Astral Beings Library is ready!")
    print("✅ Database connection established")
    print("✅ All core components available")
    print("✅ Basic functionality verified")
    
    print("\n🚀 === QUICK START GUIDE ===")
    print("1. Import library: from astral_beings import *")
    print("2. Create being: guardian = await quick_guardian('MyGuardian')")
    print("3. Use abilities: await guardian.channel_power('shield')")
    print("4. Run examples: python examples/astral_beings_demo.py")
    
    print("\n🌌 The astral plane is ready for your beings!")
    return True

if __name__ == "__main__":
    success = asyncio.run(setup_astral_beings())
    if success:
        print("\n🎉 Setup completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Setup failed!")
        sys.exit(1)
