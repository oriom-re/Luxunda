
#!/usr/bin/env python3
"""
Minimalny serwer Python dla API bazy danych - tylko połączenie z PostgreSQL
"""

import asyncio
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncpg

app = FastAPI(title="LuxOS Frontend Database API")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database connection pool
db_pool = None

class QueryRequest(BaseModel):
    sql: str
    params: List[Any] = []

class SaveRequest(BaseModel):
    data: Dict[str, Any]

@app.on_event("startup")
async def startup():
    global db_pool
    try:
        db_pool = await asyncpg.create_pool(
            host='ep-odd-tooth-a2zcp5by-pooler.eu-central-1.aws.neon.tech',
            port=5432,
            user='neondb_owner',
            password='npg_aY8K9pijAnPI',
            database='neondb',
            min_size=1,
            max_size=3
        )
        print("✅ Połączono z bazą PostgreSQL")
    except Exception as e:
        print(f"❌ Błąd połączenia z bazą: {e}")

@app.on_event("shutdown")
async def shutdown():
    global db_pool
    if db_pool:
        await db_pool.close()

@app.get("/")
async def serve_frontend():
    """Serwuje główny interfejs frontend"""
    return FileResponse("static/luxos-frontend-interface.html")

@app.post("/api/db/query")
async def execute_query(request: QueryRequest):
    """Wykonuje zapytanie SQL"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")
    
    try:
        async with db_pool.acquire() as conn:
            if request.sql.strip().upper().startswith('SELECT'):
                rows = await conn.fetch(request.sql, *request.params)
                return [dict(row) for row in rows]
            else:
                result = await conn.execute(request.sql, *request.params)
                return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/db/beings")
async def save_being(request: SaveRequest):
    """Zapisuje byt do bazy"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")
    
    try:
        async with db_pool.acquire() as conn:
            # Sprawdź czy byt już istnieje
            existing = await conn.fetchrow(
                "SELECT ulid FROM beings WHERE ulid = $1", 
                request.data.get('ulid')
            )
            
            if existing:
                # Update
                await conn.execute(
                    """
                    UPDATE beings 
                    SET data = $2, updated_at = $3 
                    WHERE ulid = $1
                    """,
                    request.data.get('ulid'),
                    json.dumps(request.data.get('data', {})),
                    datetime.now()
                )
            else:
                # Insert
                await conn.execute(
                    """
                    INSERT INTO beings (ulid, soul_hash, alias, data, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    request.data.get('ulid'),
                    request.data.get('soul_hash', 'default_soul_hash'),
                    request.data.get('alias', 'unnamed_being'),
                    json.dumps(request.data.get('data', {})),
                    datetime.now(),
                    datetime.now()
                )
                
            return {"status": "success", "ulid": request.data.get('ulid')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/db/souls")
async def save_soul(request: SaveRequest):
    """Zapisuje soul do bazy"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")
    
    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO souls (soul_hash, global_ulid, alias, genotype, created_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (soul_hash) DO UPDATE SET
                    genotype = $4, updated_at = CURRENT_TIMESTAMP
                """,
                request.data.get('soul_hash'),
                request.data.get('global_ulid'),
                request.data.get('alias'),
                json.dumps(request.data.get('genotype', {})),
                datetime.now()
            )
            
            return {"status": "success", "soul_hash": request.data.get('soul_hash')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/status")
async def get_system_status():
    """Zwraca status systemu"""
    if not db_pool:
        return {"status": "error", "message": "Brak połączenia z bazą"}
    
    try:
        async with db_pool.acquire() as conn:
            beings_count = await conn.fetchval("SELECT COUNT(*) FROM beings")
            souls_count = await conn.fetchval("SELECT COUNT(*) FROM souls")
            
        return {
            "status": "active",
            "beings_count": beings_count,
            "souls_count": souls_count,
            "database": "connected",
            "frontend_mode": True
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
