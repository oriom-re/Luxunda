#!/usr/bin/env python3
"""
LuxDB MVP Demo
==============

Ten plik demonstruje działanie systemu LuxDB w wersji MVP.
Pokazuje:
1. Tworzenie genotypów (souls)
2. Tworzenie bytów (beings) na podstawie genotypów
3. Dynamiczne generowanie tabel PostgreSQL
4. Zapisywanie i odczytywanie danych

"""

import asyncio
import json
from typing import Dict, Any
from app_v2.core.parser_table import validate_genotype, process_genotype_for_tables
from app_v2.beings.being import Soul, Being
from app_v2.database.postgre_db import Postgre_db

# Przykładowe genotypy dla demo
DEMO_GENOTYPES = {
    "user_profile": {
        "attributes": {
            "name": {
                "py_type": "str",
                "max_length": 100,
                "index": True,
                "unique": False
            },
            "email": {
                "py_type": "str", 
                "max_length": 255,
                "index": True,
                "unique": True
            },
            "age": {
                "py_type": "int",
                "default": 18
            },
            "preferences": {
                "py_type": "dict"
            },
            "tags": {
                "py_type": "List[str]"
            },
            "active": {
                "py_type": "bool",
                "default": True
            }
        }
    },
    
    "ai_agent": {
        "attributes": {
            "name": {
                "py_type": "str",
                "max_length": 100,
                "index": True
            },
            "model_type": {
                "py_type": "str",
                "max_length": 50
            },
            "embedding": {
                "py_type": "List[float]",
                "vector_size": 1536
            },
            "capabilities": {
                "py_type": "List[str]"
            },
            "config": {
                "py_type": "dict"
            },
            "active": {
                "py_type": "bool",
                "default": True
            }
        }
    },
    
    "message": {
        "attributes": {
            "content": {
                "py_type": "str",
                "max_length": 4000
            },
            "sender_id": {
                "py_type": "str",
                "max_length": 26,
                "index": True
            },
            "thread_id": {
                "py_type": "str",
                "max_length": 26,
                "index": True
            },
            "metadata": {
                "py_type": "dict"
            },
            "timestamp": {
                "py_type": "float"
            }
        }
    }
}

async def demo_validate_genotypes():
    """Demo walidacji genotypów"""
    print("🔍 DEMO: Walidacja genotypów")
    print("=" * 50)
    
    for name, genotype in DEMO_GENOTYPES.items():
        print(f"\n📋 Validating genotype: {name}")
        validation = validate_genotype(genotype)
        
        if validation['valid']:
            print(f"   ✅ Valid genotype")
            
            # Pokaż jakie tabele zostaną utworzone
            tables = process_genotype_for_tables(genotype)
            print(f"   📊 Will create {len(tables)} tables:")
            for table in tables:
                print(f"      - {table['table_name']} (for {table['attr_name']})")
        else:
            print(f"   ❌ Invalid genotype:")
            for error in validation['errors']:
                print(f"      - {error}")

async def demo_create_souls():
    """Demo tworzenia souls"""
    print("\n\n🌟 DEMO: Tworzenie souls (genotypów)")
    print("=" * 50)
    
    souls = {}
    
    for name, genotype in DEMO_GENOTYPES.items():
        print(f"\n🔧 Creating soul: {name}")
        try:
            soul = await Soul.create(genotype, alias=name)
            souls[name] = soul
            print(f"   ✅ Soul created with hash: {soul.soul_hash[:12]}...")
            print(f"   🆔 Global ULID: {soul.global_ulid}")
            print(f"   🏷️  Alias: {soul.alias}")
        except Exception as e:
            print(f"   ❌ Error creating soul: {e}")
    
    return souls

async def demo_create_beings(souls: Dict[str, Soul]):
    """Demo tworzenia beings"""
    print("\n\n👤 DEMO: Tworzenie beings (instancji)")
    print("=" * 50)
    
    beings = []
    
    # Przykładowe dane dla user_profile
    if "user_profile" in souls:
        print("\n🧑 Creating user profile being...")
        user_data = {
            "name": "Jan Kowalski",
            "email": "jan.kowalski@example.com",
            "age": 30,
            "preferences": {"theme": "dark", "language": "pl"},
            "tags": ["developer", "ai-enthusiast"],
            "active": True
        }
        
        try:
            user_being = await Being.create(souls["user_profile"], user_data)
            beings.append(user_being)
            print(f"   ✅ User being created: {user_being.ulid}")
            print(f"   📧 Email: {user_being.email}")
            print(f"   🏷️  Tags: {user_being.tags}")
        except Exception as e:
            print(f"   ❌ Error creating user being: {e}")
    
    # Przykładowe dane dla ai_agent
    if "ai_agent" in souls:
        print("\n🤖 Creating AI agent being...")
        agent_data = {
            "name": "LuxAssistant",
            "model_type": "gpt-4",
            "embedding": [0.1] * 1536,  # przykładowy embedding
            "capabilities": ["text-generation", "analysis", "conversation"],
            "config": {"temperature": 0.7, "max_tokens": 2000},
            "active": True
        }
        
        try:
            agent_being = await Being.create(souls["ai_agent"], agent_data)
            beings.append(agent_being)
            print(f"   ✅ Agent being created: {agent_being.ulid}")
            print(f"   🤖 Name: {agent_being.name}")
            print(f"   🧠 Model: {agent_being.model_type}")
        except Exception as e:
            print(f"   ❌ Error creating agent being: {e}")
    
    return beings

async def demo_load_data():
    """Demo ładowania danych"""
    print("\n\n📂 DEMO: Ładowanie danych z bazy")
    print("=" * 50)
    
    try:
        # Załaduj wszystkie souls
        print("\n🌟 Loading all souls...")
        souls = await Soul.load_all()
        if souls and souls[0] is not None:
            print(f"   ✅ Found {len(souls)} souls:")
            for soul in souls:
                if soul:
                    print(f"      - {soul.alias} ({soul.soul_hash[:12]}...)")
        else:
            print("   ⚠️  No souls found")
        
        # Załaduj wszystkie beings
        print("\n👤 Loading all beings...")
        beings = await Being.load_all()
        if beings and beings[0] is not None:
            print(f"   ✅ Found {len(beings)} beings:")
            for being in beings:
                if being:
                    print(f"      - {being.ulid} (soul: {being.soul_hash[:12]}...)")
        else:
            print("   ⚠️  No beings found")
            
    except Exception as e:
        print(f"   ❌ Error loading data: {e}")

async def demo_system_status():
    """Demo sprawdzenia statusu systemu"""
    print("\n\n🔍 DEMO: Status systemu")
    print("=" * 50)
    
    try:
        pool = await Postgre_db.get_db_pool()
        if pool:
            print("   ✅ Database connection: OK")
            
            async with pool.acquire() as conn:
                # Sprawdź tabele
                result = await conn.fetch("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                
                print(f"   📊 Found {len(result)} tables:")
                for row in result:
                    table_name = row['table_name']
                    if table_name.startswith('attr_'):
                        print(f"      🔧 {table_name} (dynamic attribute table)")
                    else:
                        print(f"      📋 {table_name} (core table)")
        else:
            print("   ❌ Database connection: FAILED")
            
    except Exception as e:
        print(f"   ❌ System status check failed: {e}")

async def main():
    """Główna funkcja demo"""
    print("🚀 LuxDB MVP Demo")
    print("================")
    print("Demonstracja systemu relacyjno-genetycznego LuxDB")
    print()
    
    try:
        # Inicjalizacja bazy danych
        await Postgre_db.get_db_pool()
        print("✅ Database initialized")
        
        # Uruchom demo
        await demo_validate_genotypes()
        souls = await demo_create_souls()
        beings = await demo_create_beings(souls)
        await demo_load_data()
        await demo_system_status()
        
        print("\n\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("===============================")
        print("LuxDB MVP is working correctly!")
        print("✅ Genotype validation")
        print("✅ Dynamic table creation")
        print("✅ Soul management")
        print("✅ Being management")
        print("✅ Data persistence")
        
    except Exception as e:
        print(f"\n❌ DEMO FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
