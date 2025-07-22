# soul: app/core/gen_db.py

import aiosqlite
import hashlib
import json

pool = None

async def init(path="luxos.db"):
    try:
        pool = await aiosqlite.connect(path)
        await pool.execute("PRAGMA foreign_keys = ON")
        return pool
    except Exception as e:
        print(f"Error initializing database: {e}")

async def get_pool():
    global pool
    if not pool:
        pool = await init()
    return pool

async def close():
    if pool:
        await pool.close()

async def setup_sqlite_tables():
    try:
        async with pool.execute("""
            CREATE TABLE IF NOT EXISTS souls (
                soul TEXT PRIMARY KEY,
                genesis TEXT NOT NULL,
                attributes TEXT NOT NULL,
                memories TEXT NOT NULL,
                self_awareness TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """):
            pass

        async with pool.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                source_soul TEXT NOT NULL,
                target_soul TEXT NOT NULL,
                attributes TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_soul) REFERENCES souls (soul),
                FOREIGN KEY (target_soul) REFERENCES souls (soul)
            )
        """):
            pass

        await pool.commit()
    except Exception as e:
        print(f"Error setting up tables: {e}")

async def load(soul: str):
    """Ładuje byt z bazy danych"""
    async with pool.execute("SELECT * FROM souls WHERE soul = ?", (soul,)) as cursor:
        row = await cursor.fetchone()
        if row:
            return {
                "soul": row[0],
                "genesis": json.loads(row[1]),
                "attributes": json.loads(row[2]),
                "memories": json.loads(row[3]),
                "self_awareness": json.loads(row[4]),
                "created_at": row[5],
                "modified_at": row[6]
            }
        return None
    
async def save(soul_data: dict):
    """Zapisuje byt do bazy danych"""
    async with pool.execute("""
        INSERT OR REPLACE INTO souls (soul, genesis, attributes, memories, self_awareness, created_at, modified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        soul_data["soul"],
        json.dumps(soul_data["genesis"]),
        json.dumps(soul_data["attributes"]),
        json.dumps(soul_data["memories"]),
        json.dumps(soul_data["self_awareness"]),
        soul_data.get("created_at", None),
        soul_data.get("modified_at", None)
    )):
        await pool.commit()

async def save_gene(path: str, code: str, attributes: dict):
    new_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()

    async with pool.execute("""
        SELECT current_hash, genesis, attributes FROM genes WHERE path = ?
    """, (path,)) as cursor:
        row = await cursor.fetchone()

    if row and row[0] == new_hash:
        return False  # Nic nie zmieniamy, kod się nie zmienił

    if row:
        await pool.execute("""
            INSERT INTO gene_history (path, hash, genesis, attributes)
            VALUES (?, ?, ?, ?)
        """, (path, row[0], row[1], row[2]))

    await pool.execute("""
        INSERT OR REPLACE INTO genes (path, current_hash, genesis, attributes, modified_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (path, new_hash, code, json.dumps(attributes)))

    await pool.commit()
    return True