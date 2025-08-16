
#!/usr/bin/env python3
"""
🔧 Schema Mismatch Fix - Naprawia problem z brakującą kolumną 'data'
"""

import asyncio
import sys
from pathlib import Path

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

from luxdb.core.postgre_db import Postgre_db

async def fix_schema_mismatch():
    """Naprawia problem z niezgodnością schematu tabeli beings"""
    print("🔧 Naprawiam problem z schematem bazy danych...")
    
    try:
        pool = await Postgre_db.get_db_pool()
        if not pool:
            print("❌ Brak połączenia z bazą danych")
            return
            
        async with pool.acquire() as conn:
            
            # 1. Sprawdź aktualny schemat tabeli beings
            print("🔍 Sprawdzam aktualny schemat tabeli beings...")
            
            check_columns_query = """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'beings'
                ORDER BY ordinal_position
            """
            
            columns = await conn.fetch(check_columns_query)
            print(f"📊 Aktualne kolumny w tabeli beings:")
            for col in columns:
                print(f"   - {col['column_name']}: {col['data_type']}")
            
            # 2. Sprawdź czy kolumna 'data' istnieje
            has_data_column = any(col['column_name'] == 'data' for col in columns)
            
            if not has_data_column:
                print("❌ Kolumna 'data' nie istnieje - naprawiam schemat...")
                
                # 3. Backup istniejących danych
                print("💾 Tworzę backup istniejących danych...")
                beings_backup = await conn.fetch("SELECT * FROM beings")
                print(f"📦 Zbackupowano {len(beings_backup)} rekordów")
                
                # 4. Usuń starą tabelę beings
                print("🗑️  Usuwam starą tabelę beings...")
                await conn.execute("DROP TABLE IF EXISTS beings CASCADE")
                
                # 5. Utwórz nową tabelę z poprawnym schematem
                print("🏗️  Tworzę nową tabelę beings z JSONB...")
                await conn.execute("""
                    CREATE TABLE beings (
                        ulid CHAR(26) PRIMARY KEY,
                        soul_hash CHAR(64) NOT NULL,
                        alias VARCHAR(255),
                        data JSONB DEFAULT '{}',
                        vector_embedding vector(1536),
                        table_type VARCHAR(50) DEFAULT 'being',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (soul_hash) REFERENCES souls(soul_hash)
                    );
                """)
                
                # 6. Dodaj indeksy
                print("📊 Dodaję indeksy...")
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_beings_soul_hash ON beings (soul_hash);
                    CREATE INDEX IF NOT EXISTS idx_beings_data ON beings USING gin (data);
                    CREATE INDEX IF NOT EXISTS idx_beings_created_at ON beings (created_at);
                    CREATE INDEX IF NOT EXISTS idx_beings_updated_at ON beings (updated_at);
                    CREATE INDEX IF NOT EXISTS idx_beings_alias ON beings (alias);
                    CREATE INDEX IF NOT EXISTS idx_beings_table_type ON beings (table_type);
                """)
                
                # 7. Przywróć dane z backup'u
                print("🔄 Przywracam dane z backup'u...")
                restored_count = 0
                
                for being in beings_backup:
                    try:
                        # Konwertuj stare dane do nowego formatu JSONB
                        old_data = {}
                        for key, value in being.items():
                            if key not in ['ulid', 'soul_hash', 'alias', 'created_at', 'updated_at', 'table_type']:
                                if value is not None:
                                    old_data[key] = value
                        
                        await conn.execute("""
                            INSERT INTO beings (ulid, soul_hash, alias, data, table_type, created_at, updated_at)
                            VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        being['ulid'],
                        being['soul_hash'],
                        being.get('alias'),
                        old_data if old_data else {},
                        being.get('table_type', 'being'),
                        being.get('created_at'),
                        being.get('updated_at')
                        )
                        restored_count += 1
                        
                    except Exception as e:
                        print(f"⚠️  Błąd przywracania rekordu {being.get('ulid', 'unknown')}: {e}")
                
                print(f"✅ Przywrócono {restored_count} z {len(beings_backup)} rekordów")
                
            else:
                print("✅ Kolumna 'data' już istnieje - schemat jest poprawny!")
            
            # 8. Weryfikuj nowy schemat
            print("\n🔍 Weryfikuję nowy schemat...")
            final_columns = await conn.fetch(check_columns_query)
            
            print("📊 Finalne kolumny w tabeli beings:")
            for col in final_columns:
                print(f"   - {col['column_name']}: {col['data_type']}")
            
            beings_count = await conn.fetchval("SELECT COUNT(*) FROM beings")
            print(f"📊 Liczba rekordów w tabeli beings: {beings_count}")
            
            print("\n✅ Problem z schematem został naprawiony!")
            
    except Exception as e:
        print(f"❌ Błąd podczas naprawiania schematu: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(fix_schema_mismatch())
