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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """):
            pass
        # dodaj indexy
        async with pool.execute("""
            CREATE INDEX IF NOT EXISTS idx_soul_genesis ON souls (genesis)
        """):
            pass

        async with pool.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id TEXT PRIMARY KEY,
                source_soul TEXT NOT NULL,
                target_soul TEXT NOT NULL,
                attributes TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """):
            pass

        await pool.commit()
    except Exception as e:
        print(f"Error setting up tables: {e}")