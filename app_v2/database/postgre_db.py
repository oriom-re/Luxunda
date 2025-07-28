
db_pool = None

class Postgre_db:
    """Klasa do zarządzania połączeniem z bazą danych PostgreSQL"""
    
    @staticmethod
    async def get_db_pool():
        """Zwraca pulę połączeń do bazy danych PostgreSQL"""
        global db_pool
        if db_pool is None:
            print("🔄 Inicjalizacja puli połączeń do bazy PostgreSQL...")
            from asyncpg import create_pool
            db_pool = await create_pool(
                host='ep-odd-tooth-a2zcp5by-pooler.eu-central-1.aws.neon.tech',
                port=5432,
                user='neondb_owner',
                password='npg_aY8K9pijAnPI',
                database='neondb',
                min_size=1,
                max_size=5,
                server_settings={
                    'statement_cache_size': '0'  # Wyłącz cache statementów
                }
            )
            await Postgre_db.setup_tables()  # Upewnij się, że tabele są utworzone
            print("✅ Pula połączeń do bazy PostgreSQL zainicjalizowana")
        return db_pool
    
    @staticmethod
    async def setup_tables():
        """Tworzy tabele w PostgreSQL"""
        global db_pool
        if not db_pool:
            print("❌ Baza danych nie jest zainicjalizowana")
            return
        
        try:
            async with db_pool.acquire() as conn:

                await conn.execute("""
                        CREATE EXTENSION IF NOT EXISTS vector;
                        CREATE EXTENSION IF NOT EXISTS pgcrypto;
                """)

                await conn.execute("""  
                        CREATE TABLE IF NOT EXISTS souls (
                            soul_hash CHAR(64) PRIMARY KEY,
                            global_ulid CHAR(26) NOT NULL,
                            alias VARCHAR(255),
                            genotype JSONB NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        -- usuń wyzwalacz
                        DROP TRIGGER IF EXISTS trg_generate_soul_hash ON souls;
                                   
                        -- usuń funkcje
                        DROP FUNCTION IF EXISTS generate_soul_hash();
                        
                                   
                        -- indexy
                        CREATE INDEX IF NOT EXISTS idx_souls_genotype ON souls USING gin (genotype);
                        CREATE INDEX IF NOT EXISTS idx_souls_alias ON souls (alias);
                        CREATE INDEX IF NOT EXISTS idx_souls_created_at ON souls (created_at);
                """)

                await conn.execute("""
                        CREATE TABLE IF NOT EXISTS beings (
                            ulid CHAR(26) PRIMARY KEY,
                            soul_hash CHAR(64) NOT NULL,
                            alias VARCHAR(255),
                            FOREIGN KEY (soul_hash) REFERENCES souls(soul_hash),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                        -- indexy
                        CREATE INDEX IF NOT EXISTS idx_beings_soul_hash ON beings (soul_hash);
                        CREATE INDEX IF NOT EXISTS idx_beings_created_at ON beings (created_at);
                """)

                await conn.execute("""
                        CREATE TABLE IF NOT EXISTS _varchar_255_not_null (
                            being_ulid CHAR(26) NOT NULL,
                            key TEXT NOT NULL,
                            value VARCHAR(255) NOT NULL,
                            PRIMARY KEY (being_ulid, key),
                            FOREIGN KEY (being_ulid) REFERENCES beings(ulid)
                        );
                """)
                await conn.execute("""
                        CREATE TABLE IF NOT EXISTS _varchar_255 (
                            being_ulid CHAR(26) NOT NULL,
                            key TEXT NOT NULL,
                            value VARCHAR(255) NOT NULL,
                            PRIMARY KEY (being_ulid, key),
                            FOREIGN KEY (being_ulid) REFERENCES beings(ulid)
                        );
                """)
                await conn.execute("""
                        CREATE TABLE IF NOT EXISTS _ulid (
                            being_ulid CHAR(26) NOT NULL,
                            key TEXT NOT NULL,
                            key VARCHAR(255) NOT NULL,
                            value UUID NOT NULL,
                            PRIMARY KEY (being_ulid, key),
                            FOREIGN KEY (being_ulid) REFERENCES beings(ulid)
                        );
                """)
                await conn.execute("""
                        CREATE TABLE IF NOT EXISTS _jsonb (
                            being_ulid CHAR(26) NOT NULL,
                            key TEXT NOT NULL,
                            key VARCHAR(255) NOT NULL,
                            value JSONB,
                            PRIMARY KEY (being_ulid, key),
                            FOREIGN KEY (being_ulid) REFERENCES beings(ulid)
                        );
                """)
                await conn.execute("""
                        CREATE TABLE IF NOT EXISTS _vector_1536 (
                            being_ulid CHAR(26) NOT NULL,
                            key TEXT NOT NULL,
                            key VARCHAR(255) NOT NULL,
                            PRIMARY KEY (being_ulid, key),
                            FOREIGN KEY (being_ulid) REFERENCES beings(ulid)
                        );
                """)
                await conn.execute("""
                        CREATE TABLE IF NOT EXISTS _boolean (
                            being_ulid CHAR(26) NOT NULL,
                            key TEXT NOT NULL,
                            key VARCHAR(255) NOT NULL,
                            value BOOLEAN DEFAULT TRUE,
                            PRIMARY KEY (being_ulid, key),
                            FOREIGN KEY (being_ulid) REFERENCES beings(ulid)
                        );
                """)
                await conn.execute("""
                        CREATE TABLE IF NOT EXISTS _text (
                            being_ulid CHAR(26) NOT NULL,
                            key TEXT NOT NULL,
                            value TEXT,
                            PRIMARY KEY (being_ulid, key),
                            FOREIGN KEY (being_ulid) REFERENCES beings(ulid)
                        );

                """)
                await conn.execute("""
                        CREATE TABLE IF NOT EXISTS _text_not_null (
                            being_ulid CHAR(26) NOT NULL,
                            key TEXT NOT NULL,
                            key VARCHAR(255) NOT NULL,
                            value TEXT NOT NULL,
                            PRIMARY KEY (being_ulid, key),
                            FOREIGN KEY (being_ulid) REFERENCES beings(ulid)
                        );

                    """)
            
            # 
            #     await conn.execute("""
            #         CREATE TABLE IF NOT EXISTS souls (
            #             uid UUID PRIMARY KEY,
            #             global_uid UUID NOT NULL,
            #             alias VARCHAR(255),
            #             genotype_hex TEXT NOT NULL,
            #             genotype JSONB NOT NULL,
            #             attributes JSONB NOT NULL,
            #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            #         )
            #     """)
                
            #     await conn.execute("""
            #         CREATE TABLE IF NOT EXISTS relationships (
            #             uid UUID PRIMARY KEY,
            #             global_uid UUID NOT NULL,
            #             alias VARCHAR(255),
            #             genotype_hex TEXT NOT NULL,
            #             genotype JSONB NOT NULL,
            #             source_uid UUID NOT NULL,
            #             target_uid UUID NOT NULL,
            #             attributes JSONB NOT NULL,
            #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #             FOREIGN KEY (source_uid) REFERENCES souls(uid),
            #             FOREIGN KEY (target_uid) REFERENCES souls(uid)
            #         )
            #     """)

            #     await conn.execute("""
            #         CREATE TABLE IF NOT EXISTS varchar_255 (
            #             uid UUID PRIMARY KEY,
            #             value VARCHAR(255)
            #         )
            #         CREATE TABLE IF NOT EXISTS text_not_null (
            #             uid UUID PRIMARY KEY,
            #             value TEXT NOT NULL
            #         )
            #         CREATE TABLE uid_not_null (
            #             uid UUID PRIMARY KEY,
            #             value UUID NOT NULL REFERENCES souls(uid)
            #         )
            #     """)

            #     await conn.execute("""
            #         CREATE TABLE IF NOT EXISTS relationships (
            #             uid UUID PRIMARY KEY,
            #             global_uid UUID NOT NULL,
                        
            #             alias VARCHAR(255),
            #             genotype_hex TEXT NOT NULL,           -- unikalny hash "genotypu"
            #             genotype JSONB NOT NULL,              -- pełen opis intencji, np. {"type": "message->author"}
                        
            #             source_uid UUID NOT NULL,
            #             target_uid UUID NOT NULL,
                        
            #             attributes JSONB NOT NULL,            -- dane np. {"result": "success", "feedback": "ok"}
            #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            #             FOREIGN KEY (source_uid) REFERENCES souls(uid),
            #             FOREIGN KEY (target_uid) REFERENCES souls(uid)
            #         );
            #     """)

            #     # tabela embenddingów
            #     await conn.execute("""
            #         CREATE TABLE IF NOT EXISTS embeddings (
            #             uid UUID PRIMARY KEY,
            #             global_uid UUID NOT NULL,
            #             being_uid UUID NOT NULL,
            #             ada2 VECTOR(1536) NOT NULL,
            #             embedding JSONB NOT NULL,
            #             created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #             FOREIGN KEY (being_uid) REFERENCES souls(uid)
            #         )
            #     """)

                # await conn.execute("""
                #     -- to robisz raz w bazie
                #     DROP VIEW IF EXISTS thread_view;
                #     -- Tworzenie widoku dla relacji wątków
                #     CREATE VIEW thread_view AS
                #     SELECT m.*, r.attributes->>'type' AS type, r.source_uid AS thread_id
                #     FROM souls m
                #     JOIN relationships r ON m.uid = r.target_uid
                #     ORDER BY m.created_at;
                # """)
        
                # Indeksy
                # await conn.execute("CREATE INDEX IF NOT EXISTS idx_souls_genesis ON souls USING gin (genesis)")
                # await conn.execute("CREATE INDEX IF NOT EXISTS idx_souls_attributes ON souls USING gin (attributes)")
                # await conn.execute("CREATE INDEX IF NOT EXISTS idx_souls_memories ON souls USING gin (memories)")
                # await conn.execute("CREATE INDEX IF NOT EXISTS idx_souls_self_awareness ON souls USING gin (self_awareness)")

                # await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_attributes ON relationships USING gin (attributes)")
                # await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships (source_uid)")
                # await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships (target_uid)") 
                print("✅ Tabele PostgreSQL utworzone")
        except Exception as e:
            print(f"❌ Błąd tworzenia tabel PostgreSQL: {e}")


# CREATE OR REPLACE FUNCTION generate_soul_hash() RETURNS trigger AS $$
# BEGIN
#     NEW.soul_hash := encode(digest(NEW.genotype::text, 'sha256'), 'hex');
#     RETURN NEW;
# END;
# $$ LANGUAGE plpgsql;

# CREATE OR REPLACE TRIGGER trg_generate_soul_hash
# BEFORE INSERT ON souls
# FOR EACH ROW
# EXECUTE FUNCTION generate_soul_hash();