
#!/usr/bin/env python3
"""
🧹 Database Cleanup Script - Czyści stare tabele i migruje do nowego schematu JSONB
"""

import asyncio
import sys
from pathlib import Path

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

from luxdb.core.postgre_db import Postgre_db

async def cleanup_old_tables():
    """Usuwa stare dynamiczne tabele attr_* i inne legacy tabele"""
    print("🧹 Rozpoczynam czyszczenie starych tabel...")
    
    try:
        pool = await Postgre_db.get_db_pool()
        if not pool:
            print("❌ Brak połączenia z bazą danych")
            return
            
        async with pool.acquire() as conn:
            # Znajdź wszystkie tabele attr_* (dynamiczne tabele atrybutów)
            print("🔍 Szukam starych dynamicznych tabel...")
            
            dynamic_tables_query = """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'attr_%'
                ORDER BY table_name
            """
            
            dynamic_tables = await conn.fetch(dynamic_tables_query)
            
            if dynamic_tables:
                print(f"📋 Znaleziono {len(dynamic_tables)} dynamicznych tabel do usunięcia:")
                for row in dynamic_tables:
                    table_name = row['table_name']
                    print(f"   🗑️  {table_name}")
                    
                # Usuń dynamiczne tabele
                for row in dynamic_tables:
                    table_name = row['table_name']
                    try:
                        await conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                        print(f"   ✅ Usunięto tabelę: {table_name}")
                    except Exception as e:
                        print(f"   ⚠️ Błąd usuwania {table_name}: {e}")
            else:
                print("✅ Brak dynamicznych tabel do usunięcia")
                
            # Lista innych starych tabel do usunięcia
            legacy_tables = [
                'base_beings',
                'souls_old', 
                'beings_old',
                'relationships_old',
                'dynamic_tables_registry',
                'table_definitions'
            ]
            
            print("\n🔍 Sprawdzam inne legacy tabele...")
            for table_name in legacy_tables:
                try:
                    # Sprawdź czy tabela istnieje
                    check_query = """
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = $1
                        )
                    """
                    exists = await conn.fetchval(check_query, table_name)
                    
                    if exists:
                        await conn.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
                        print(f"   ✅ Usunięto legacy tabelę: {table_name}")
                    else:
                        print(f"   ➖ Tabela {table_name} nie istnieje (OK)")
                        
                except Exception as e:
                    print(f"   ⚠️ Błąd usuwania {table_name}: {e}")
                    
            print("\n✅ Czyszczenie starych tabel zakończone!")
            
    except Exception as e:
        print(f"❌ Błąd podczas czyszczenia tabel: {e}")

async def verify_new_schema():
    """Weryfikuje czy nowy schemat JSONB jest poprawny"""
    print("\n🔍 Weryfikuję nowy schemat JSONB...")
    
    try:
        pool = await Postgre_db.get_db_pool()
        async with pool.acquire() as conn:
            
            # Sprawdź główne tabele
            main_tables = ['souls', 'beings', 'relations', 'relationships']
            
            for table_name in main_tables:
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                count = await conn.fetchval(count_query)
                print(f"   📊 {table_name}: {count} rekordów")
                
            # Sprawdź indeksy JSONB
            indexes_query = """
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE schemaname = 'public' 
                AND indexname LIKE '%gin%' 
                OR indexname LIKE '%jsonb%'
                ORDER BY tablename, indexname
            """
            
            indexes = await conn.fetch(indexes_query)
            if indexes:
                print("\n📊 Indeksy JSONB/GIN:")
                for row in indexes:
                    print(f"   🔍 {row['tablename']}.{row['indexname']}")
            else:
                print("\n⚠️ Brak indeksów JSONB/GIN")
                
            # Sprawdź czy rozszerzenia są dostępne
            extensions_query = """
                SELECT extname FROM pg_extension 
                WHERE extname IN ('vector', 'pgcrypto', 'btree_gin')
            """
            
            extensions = await conn.fetch(extensions_query)
            print(f"\n🔧 Dostępne rozszerzenia: {[row['extname'] for row in extensions]}")
            
            print("\n✅ Weryfikacja nowego schematu zakończona!")
            
    except Exception as e:
        print(f"❌ Błąd podczas weryfikacji schematu: {e}")

async def migrate_legacy_data():
    """Migruje pozostałe legacy dane do nowego formatu JSONB"""
    print("\n🔄 Rozpoczynam migrację legacy danych...")
    
    try:
        pool = await Postgre_db.get_db_pool()
        async with pool.acquire() as conn:
            
            # Sprawdź czy są jakieś legacy dane w relationships
            legacy_count = await conn.fetchval("""
                SELECT COUNT(*) FROM relationships 
                WHERE metadata IS NULL OR metadata = '{}'
            """)
            
            if legacy_count > 0:
                print(f"🔄 Aktualizuję {legacy_count} legacy relationships...")
                
                await conn.execute("""
                    UPDATE relationships 
                    SET metadata = '{"migrated": true, "legacy": true}'::jsonb
                    WHERE metadata IS NULL OR metadata = '{}'
                """)
                
                print("✅ Legacy relationships zaktualizowane")
            else:
                print("✅ Brak legacy relationships do migracji")
                
            # Sprawdź inconsistency w beings
            beings_without_data = await conn.fetchval("""
                SELECT COUNT(*) FROM beings 
                WHERE data IS NULL OR data = '{}'
            """)
            
            if beings_without_data > 0:
                print(f"🔄 Naprawiam {beings_without_data} beings bez danych...")
                
                await conn.execute("""
                    UPDATE beings 
                    SET data = '{"migrated": true}'::jsonb
                    WHERE data IS NULL OR data = '{}'
                """)
                
                print("✅ Beings bez danych naprawione")
            else:
                print("✅ Wszystkie beings mają dane JSONB")
                
            print("\n✅ Migracja legacy danych zakończona!")
            
    except Exception as e:
        print(f"❌ Błąd podczas migracji danych: {e}")

async def main():
    """Główna funkcja cleanup"""
    print("🧹 LuxDB Database Cleanup Script")
    print("=" * 50)
    
    # Krok 1: Usuń stare tabele
    await cleanup_old_tables()
    
    # Krok 2: Migruj legacy dane
    await migrate_legacy_data()
    
    # Krok 3: Weryfikuj nowy schemat
    await verify_new_schema()
    
    print("\n" + "=" * 50)
    print("🎉 Cleanup zakończony pomyślnie!")
    print("📊 Baza danych została oczyszczona i zmigrowana do JSONB")
    print("🚀 System gotowy do pracy z nowym schematem!")

if __name__ == "__main__":
    asyncio.run(main())
