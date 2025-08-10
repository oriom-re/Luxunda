#!/usr/bin/env python3
"""
LuxOS Frontend Server - Minimalny serwer dla samowystarczalnego frontendu
Tylko połączenie z bazą + API do scenariuszy
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

app = FastAPI(title="LuxOS Frontend API")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database connection pool
db_pool = None

class ScenarioRequest(BaseModel):
    name: str

class BeingDataRequest(BaseModel):
    being_data: Dict[str, Any]

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
            max_size=5
        )
        print("✅ Frontend Server: Połączono z bazą PostgreSQL")

        # Sprawdź czy istnieje tabela scenarios
        async with db_pool.acquire() as conn:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'scenarios'
                )
            """)

            if not exists:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS scenarios (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        data JSONB NOT NULL,
                        hash_id VARCHAR(64),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("✅ Utworzono tabelę scenarios")

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

@app.get("/api/scenarios/list")
async def list_scenarios():
    """Zwraca listę dostępnych scenariuszy"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")

    try:
        async with db_pool.acquire() as conn:
            scenarios = await conn.fetch("""
                SELECT name, hash_id, created_at, updated_at 
                FROM scenarios 
                ORDER BY name
            """)

            return {
                "scenarios": [
                    {
                        "name": s['name'],
                        "hash_id": s['hash_id'],
                        "created_at": s['created_at'].isoformat() if s['created_at'] else None,
                        "updated_at": s['updated_at'].isoformat() if s['updated_at'] else None
                    }
                    for s in scenarios
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/scenarios/{scenario_name}")
async def get_scenario(scenario_name: str):
    """Pobiera konkretny scenariusz"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")

    try:
        async with db_pool.acquire() as conn:
            scenario = await conn.fetchrow("""
                SELECT name, data, hash_id 
                FROM scenarios 
                WHERE name = $1
            """, scenario_name)

            if not scenario:
                # Spróbuj załadować z pliku scenarios/
                import os
                scenario_path = f"scenarios/{scenario_name}.scenario"
                if os.path.exists(scenario_path):
                    with open(scenario_path, 'r') as f:
                        scenario_data = json.load(f)

                    # Zapisz do bazy
                    await conn.execute("""
                        INSERT INTO scenarios (name, data, hash_id)
                        VALUES ($1, $2, $3)
                        ON CONFLICT (name) DO UPDATE SET
                        data = $2, updated_at = CURRENT_TIMESTAMP
                    """, scenario_name, json.dumps(scenario_data), f"file_{scenario_name}")

                    return {
                        "name": scenario_name,
                        "data": scenario_data,
                        "source": "file_imported"
                    }

                raise HTTPException(status_code=404, detail="Scenariusz nie znaleziony")

            return {
                "name": scenario['name'],
                "data": scenario['data'],
                "hash_id": scenario['hash_id']
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scenarios/{scenario_name}")
async def save_scenario(scenario_name: str, scenario_data: Dict[str, Any]):
    """Zapisuje scenariusz do bazy"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")

    try:
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO scenarios (name, data, hash_id, updated_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (name) DO UPDATE SET
                data = $2, hash_id = $3, updated_at = $4
            """, 
            scenario_name, 
            json.dumps(scenario_data), 
            f"frontend_{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
            datetime.now()
            )

            return {"status": "success", "scenario": scenario_name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/beings/minimal")
async def get_minimal_beings():
    """Pobiera tylko podstawowe informacje o bytach (bez pełnych danych)"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")

    try:
        async with db_pool.acquire() as conn:
            beings = await conn.fetch("""
                SELECT ulid, alias, soul_hash, created_at, updated_at,
                       (data->>'type') as being_type
                FROM beings 
                ORDER BY created_at DESC 
                LIMIT 50
            """)

            return {
                "beings": [
                    {
                        "ulid": b['ulid'],
                        "alias": b['alias'],
                        "soul_hash": b['soul_hash'],
                        "type": b['being_type'] or 'unknown',
                        "created_at": b['created_at'].isoformat() if b['created_at'] else None
                    }
                    for b in beings
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/beings/{being_ulid}")
async def get_being_full(being_ulid: str):
    """Pobiera pełne dane konkretnego bytu na żądanie"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")

    try:
        async with db_pool.acquire() as conn:
            being = await conn.fetchrow("""
                SELECT * FROM beings WHERE ulid = $1
            """, being_ulid)

            if not being:
                raise HTTPException(status_code=404, detail="Byt nie znaleziony")

            return {
                "ulid": being['ulid'],
                "alias": being['alias'],
                "soul_hash": being['soul_hash'],
                "data": being['data'],
                "created_at": being['created_at'].isoformat() if being['created_at'] else None,
                "updated_at": being['updated_at'].isoformat() if being['updated_at'] else None
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/beings")
async def create_being(request: BeingDataRequest):
    """Tworzy nowy byt w bazie"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")

    try:
        being_data = request.being_data

        async with db_pool.acquire() as conn:
            # Generuj ULID jeśli nie ma
            if 'ulid' not in being_data:
                import ulid
                being_data['ulid'] = str(ulid.new())

            await conn.execute("""
                INSERT INTO beings (ulid, soul_hash, alias, data, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
            being_data['ulid'],
            being_data.get('soul_hash', 'default_soul_hash'),
            being_data.get('alias', f"being_{being_data['ulid'][:8]}"),
            json.dumps(being_data.get('data', {})),
            datetime.now(),
            datetime.now()
            )

            return {"status": "success", "ulid": being_data['ulid']}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/souls/{soul_hash}")
async def get_soul(soul_hash: str):
    """Pobiera soul na żądanie"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")

    try:
        async with db_pool.acquire() as conn:
            soul = await conn.fetchrow("""
                SELECT * FROM souls WHERE soul_hash = $1
            """, soul_hash)

            if not soul:
                raise HTTPException(status_code=404, detail="Soul nie znaleziona")

            return {
                "soul_hash": soul['soul_hash'],
                "global_ulid": soul['global_ulid'],
                "alias": soul['alias'],
                "genotype": soul['genotype'],
                "created_at": soul['created_at'].isoformat() if soul['created_at'] else None
            }

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
            scenarios_count = await conn.fetchval("SELECT COUNT(*) FROM scenarios")

        return {
            "status": "active",
            "mode": "frontend_only",
            "beings_count": beings_count,
            "souls_count": souls_count,
            "scenarios_count": scenarios_count,
            "database": "connected"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/bios")
async def get_bios_scenario():
    """Pobiera główny BIOS systemu jako byt"""
    try:
        from luxdb.repository.soul_repository import BeingRepository
        from luxdb.models.soul import Soul
        from luxdb.models.being import Being

        # Szukaj BIOS bytów
        all_beings = await BeingRepository.get_all_beings()
        bios_beings = []

        if all_beings.get('success'):
            for being in all_beings.get('beings', []):
                if (being and 
                    hasattr(being, 'data') and 
                    being.data.get('system_type') == 'bios'):
                    bios_beings.append(being)

        # Sortuj: stabilne najpierw, potem według daty
        bios_beings.sort(key=lambda b: (
            not b.data.get('stable', False),
            -(b.created_at.timestamp() if b.created_at else 0)
        ))

        if bios_beings:
            # Zwróć najlepszy BIOS
            bios_being = bios_beings[0]
            soul = await bios_being.get_soul()

            return {
                "name": bios_being.alias,
                "ulid": bios_being.ulid,
                "stable": bios_being.data.get('stable', False),
                "version": bios_being.data.get('version', '1.0.0'),
                "genesis": soul.genotype.get('genesis', {}) if soul else {},
                "system_type": "bios"
            }
        else:
            # Utwórz domyślny BIOS jako byt
            bios_genotype = {
                "genesis": {
                    "name": "LuxOS_BIOS_Default",
                    "type": "system_bios",
                    "version": "1.0.0",
                    "description": "Domyślny BIOS systemu LuxOS",
                    "bootstrap_sequence": [
                        "init_kernel",
                        "load_communication",
                        "setup_ui",
                        "ready_state"
                    ],
                    "required_beings": [
                        {
                            "alias": "lux_assistant",
                            "type": "ai_assistant",
                            "priority": 100,
                            "critical": False
                        },
                        {
                            "alias": "kernel_core",
                            "type": "system_kernel",
                            "priority": 100,
                            "critical": True
                        }
                    ],
                    "fallback_procedure": {
                        "max_retries": 3,
                        "retry_delay": 5,
                        "emergency_mode": True
                    }
                },
                "attributes": {
                    "system_type": {"py_type": "str", "default": "bios"},
                    "stable": {"py_type": "bool", "default": True},
                    "version": {"py_type": "str", "default": "1.0.0"}
                }
            }

            # Utwórz Soul i Being
            bios_soul = await Soul.create(
                genotype=bios_genotype,
                alias="luxos_bios_default_soul"
            )

            bios_being = await Being.create(
                soul=bios_soul,
                alias="luxos_bios_default",
                attributes={
                    "system_type": "bios",
                    "stable": True,
                    "version": "1.0.0",
                    "created_by": "frontend_server"
                }
            )

            return {
                "name": bios_being.alias,
                "ulid": bios_being.ulid,
                "stable": True,
                "version": "1.0.0",
                "genesis": bios_genotype["genesis"],
                "system_type": "bios",
                "created": True
            }

    except Exception as e:
        return {
            "error": f"Błąd ładowania BIOS: {str(e)}",
            "fallback": True,
            "name": "LuxOS_BIOS_Fallback",
            "bootstrap_sequence": [
                "init_kernel",
                "load_communication", 
                "setup_ui",
                "ready_state"
            ]
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)