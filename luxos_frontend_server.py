#!/usr/bin/env python3
"""
LuxOS Frontend Server - Minimalny serwer dla samowystarczalnego frontendu
Tylko połączenie z bazą + API do scenariuszy
"""

import asyncio
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncpg
import os # Added for os.listdir

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

@app.get("/admin")
async def admin_panel():
    """Panel administracyjny systemu"""
    return FileResponse("static/admin-panel.html")

@app.get("/admin/scenarios")
async def admin_scenarios():
    """Interfejs zarządzania scenariuszami UI"""
    return FileResponse("static/admin-scenarios.html")

@app.get("/api/admin/ui-scenarios")
async def get_ui_scenarios():
    """Pobiera wszystkie scenariusze UI z bazy"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")

    try:
        async with db_pool.acquire() as conn:
            ui_scenarios = await conn.fetch("""
                SELECT * FROM beings 
                WHERE data->>'type' = 'ui_scenario'
                ORDER BY created_at DESC
            """)

            return {
                "scenarios": [
                    {
                        "ulid": s['ulid'],
                        "alias": s['alias'],
                        "name": s['data'].get('name', s['alias']),
                        "route": s['data'].get('route', '/'),
                        "html_content": s['data'].get('html_content', ''),
                        "css_content": s['data'].get('css_content', ''),
                        "js_content": s['data'].get('js_content', ''),
                        "active": s['data'].get('active', False),
                        "created_at": s['created_at'].isoformat() if s['created_at'] else None
                    }
                    for s in ui_scenarios
                ]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/ui-scenarios")
async def create_ui_scenario(scenario_data: Dict[str, Any]):
    """Tworzy nowy scenariusz UI jako byt"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")

    try:
        import ulid
        scenario_ulid = str(ulid.new())

        ui_data = {
            "type": "ui_scenario",
            "name": scenario_data.get("name", "New UI Scenario"),
            "route": scenario_data.get("route", "/"),
            "html_content": scenario_data.get("html_content", ""),
            "css_content": scenario_data.get("css_content", ""),
            "js_content": scenario_data.get("js_content", ""),
            "active": scenario_data.get("active", False),
            "description": scenario_data.get("description", ""),
            "created_by": "admin_panel"
        }

        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO beings (ulid, soul_hash, alias, data, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """,
            scenario_ulid,
            "ui_scenario_soul",
            scenario_data.get("alias", f"ui_scenario_{scenario_ulid[:8]}"),
            json.dumps(ui_data),
            datetime.now(),
            datetime.now()
            )

            return {"status": "success", "ulid": scenario_ulid, "message": "Scenariusz UI utworzony"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/admin/ui-scenarios/{scenario_ulid}")
async def update_ui_scenario(scenario_ulid: str, scenario_data: Dict[str, Any]):
    """Aktualizuje istniejący scenariusz UI"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")

    try:
        async with db_pool.acquire() as conn:
            # Pobierz istniejący scenariusz
            existing = await conn.fetchrow("""
                SELECT data FROM beings WHERE ulid = $1 AND data->>'type' = 'ui_scenario'
            """, scenario_ulid)

            if not existing:
                raise HTTPException(status_code=404, detail="Scenariusz UI nie znaleziony")

            # Aktualizuj dane
            current_data = existing['data']
            current_data.update({
                "name": scenario_data.get("name", current_data.get("name")),
                "route": scenario_data.get("route", current_data.get("route")),
                "html_content": scenario_data.get("html_content", current_data.get("html_content")),
                "css_content": scenario_data.get("css_content", current_data.get("css_content")),
                "js_content": scenario_data.get("js_content", current_data.get("js_content")),
                "active": scenario_data.get("active", current_data.get("active")),
                "description": scenario_data.get("description", current_data.get("description")),
                "updated_by": "admin_panel"
            })

            await conn.execute("""
                UPDATE beings 
                SET data = $1, updated_at = $2 
                WHERE ulid = $3
            """, json.dumps(current_data), datetime.now(), scenario_ulid)

            return {"status": "success", "message": "Scenariusz UI zaktualizowany"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/admin/ui-scenarios/{scenario_ulid}")
async def delete_ui_scenario(scenario_ulid: str):
    """Usuwa scenariusz UI"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")

    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM beings 
                WHERE ulid = $1 AND data->>'type' = 'ui_scenario'
            """, scenario_ulid)

            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="Scenariusz UI nie znaleziony")

            return {"status": "success", "message": "Scenariusz UI usunięty"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ui/{route:path}")
async def serve_dynamic_ui(route: str):
    """Serwuje dynamiczne UI na podstawie scenariuszy z bazy"""
    if not db_pool:
        raise HTTPException(status_code=500, detail="Brak połączenia z bazą")

    try:
        async with db_pool.acquire() as conn:
            # Znajdź aktywny scenariusz dla tej ścieżki
            scenario = await conn.fetchrow("""
                SELECT data FROM beings 
                WHERE data->>'type' = 'ui_scenario' 
                AND data->>'route' = $1 
                AND (data->>'active')::boolean = true
                ORDER BY updated_at DESC
                LIMIT 1
            """, f"/{route}")

            if not scenario:
                # Spróbuj znaleźć domyślny scenariusz
                scenario = await conn.fetchrow("""
                    SELECT data FROM beings 
                    WHERE data->>'type' = 'ui_scenario' 
                    AND data->>'route' = '/' 
                    AND (data->>'active')::boolean = true
                    ORDER BY updated_at DESC
                    LIMIT 1
                """)

            if not scenario:
                raise HTTPException(status_code=404, detail="Brak aktywnego scenariusza UI dla tej ścieżki")

            scenario_data = scenario['data']

            # Generuj pełną stronę HTML
            html_content = f"""
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{scenario_data.get('name', 'LuxOS UI')}</title>
    <style>
        {scenario_data.get('css_content', '')}
    </style>
</head>
<body>
    {scenario_data.get('html_content', '<h1>Brak zawartości</h1>')}

    <script>
        {scenario_data.get('js_content', '')}
    </script>
</body>
</html>"""

            return HTMLResponse(content=html_content)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/api/scenarios")
async def get_scenarios():
    """Endpoint do pobierania scenariuszy"""
    try:
        scenarios = []
        for file in os.listdir("scenarios"):
            if file.endswith(".json"):
                with open(f"scenarios/{file}", "r", encoding="utf-8") as f:
                    scenario = json.load(f)
                    scenario["id"] = file.replace(".json", "")
                    scenarios.append(scenario)

        return {"scenarios": scenarios}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading scenarios: {str(e)}")

@app.get("/api/status")
async def get_status():
    """Status endpoint dla frontendu"""
    return {
        "status": "ok",
        "service": "LuxOS Frontend Server",
        "lux_assistant_ready": True,
        "specialists_available": True
    }

@app.get("/api/beings/specialists")
async def get_specialist_beings():
    """Pobiera listę bytów specjalistów"""
    try:
        from luxdb.models.soul import Soul
        from luxdb.models.being import Being

        # Znajdź souls oznaczone jako specjaliści
        # Assuming Soul.get_all() fetches all souls and we filter here
        # If Soul.get_all() is not available, this part needs to be adapted
        # For now, we'll simulate it if it doesn't exist, or assume it works
        
        # Placeholder if Soul.get_all() doesn't exist in your setup
        # You might need to query the database directly for souls with specialist genotype
        all_souls = []
        if hasattr(Soul, 'get_all'):
            all_souls = await Soul.get_all()
        else:
            # Mock or direct DB query if get_all is not a method
            if db_pool:
                async with db_pool.acquire() as conn:
                    rows = await conn.fetch("SELECT * FROM souls")
                    # This part assumes Soul class can be instantiated from DB rows
                    # You might need a helper function or adapt it
                    for row in rows:
                        # Mocking Soul instantiation for demonstration
                        mock_soul = Soul(soul_hash=row['soul_hash'], alias=row['alias'], genotype=row['genotype'])
                        all_souls.append(mock_soul)
            else:
                print("DB pool not available to fetch souls")


        specialists = []

        for soul in all_souls:
            if soul.genotype.get("genesis", {}).get("type") == "specialist":
                specialists.append({
                    "soul_hash": soul.soul_hash,
                    "alias": soul.alias,
                    "specialization": soul.genotype.get("specialization", "general"),
                    "functions": list(soul.genotype.get("functions", {}).keys())
                })

        return specialists
    except Exception as e:
        print(f"Error getting specialists: {e}")
        return []

@app.post("/api/lux/message")
async def process_lux_message(request: dict):
    """Endpoint do przetwarzania wiadomości przez Lux z łańcuchem specjalistów"""
    try:
        message = request.get("message", "")
        use_specialists = request.get("use_specialists", True)

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        # Import locally to avoid circular imports or direct dependency issues
        # Assuming luxdb.core.session_assistant and luxdb.models.soul, luxdb.models.being are correctly set up
        try:
            from luxdb.core.session_assistant import session_manager
            from luxdb.models.soul import Soul
            from luxdb.models.being import Being
        except ImportError as e:
            print(f"Could not import Lux dependencies: {e}. Ensure luxdb is installed and accessible.")
            raise HTTPException(status_code=500, detail="Internal Lux dependency error")


        # Get or create main Lux assistant
        # This function needs to be defined or available in session_manager
        # Assuming it returns an object that has a 'process_message' method and 'get_soul' method
        lux_assistant = await session_manager.get_or_create_lux_assistant()

        if use_specialists:
            # Process with specialist chain
            response = await process_with_specialist_chain(message, lux_assistant)
        else:
            # Direct processing
            response = await lux_assistant.process_message(message)

        return {
            "response": response,
            "specialists_used": getattr(lux_assistant, 'last_specialists_used', []),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"Error in Lux message processing: {e}")
        # Provide a more informative error for debugging
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

async def process_with_specialist_chain(message: str, lux_assistant):
    """Przetwarza wiadomość przez łańcuch specjalistów"""
    try:
        # Ensure dependencies are available within this function scope as well
        from luxdb.models.soul import Soul
        from luxdb.models.being import Being

        # Reset specialists used for this turn
        lux_assistant.last_specialists_used = []

        # Get Lux's soul to access its genesis and functions
        lux_soul = await lux_assistant.get_soul()
        if not lux_soul:
            print("Lux soul not found, falling back to direct processing.")
            return await lux_assistant.process_message(message)

        # Get available functions from Lux's genesis
        # The genotype structure might vary, assuming 'functions' is a dict where keys are function names
        available_functions = lux_soul.genotype.get("functions", {})
        
        if not available_functions:
            print("No functions defined for Lux, falling back to direct processing.")
            return await lux_assistant.process_message(message)

        # Try to match message to appropriate specialist function
        matched_function_name = await match_message_to_function(message, available_functions)

        if matched_function_name:
            print(f"Matched message to function: {matched_function_name}")
            # Execute the function which should delegate to specialist logic
            # Assuming the Soul object has an `execute_function` method that takes function name and message
            # and returns a dict like `{"success": True, "data": {"result": "..."}}`
            result = await lux_soul.execute_function(matched_function_name, message)

            if result.get("success"):
                # If function succeeded, use its result
                specialist_response = result["data"]["result"]
                lux_assistant.last_specialists_used.append(matched_function_name)
                print(f"Specialist '{matched_function_name}' executed successfully.")

                # Let Lux formulate final response based on specialist input
                # Assuming `formulate_response` method exists on the assistant
                final_response = await lux_assistant.formulate_response(message, specialist_response)
                return final_response
            else:
                print(f"Specialist function '{matched_function_name}' failed: {result.get('error', 'Unknown error')}")
        else:
            print("No suitable specialist function matched, falling back to direct processing.")

        # Fallback to direct processing if no specialist was matched or if it failed
        return await lux_assistant.process_message(message)

    except Exception as e:
        print(f"Error in specialist chain processing: {e}")
        # Attempt to use the assistant's default message processing if chain fails
        try:
            return await lux_assistant.process_message(message)
        except:
            return f"An error occurred while processing your request with specialists, and direct processing also failed: {str(e)}"

async def match_message_to_function(message: str, available_functions: dict) -> Optional[str]:
    """Dopasowuje wiadomość do odpowiedniej funkcji specjalisty"""
    message_lower = message.lower()

    # Define keywords for different specialist functions
    # This mapping should ideally be part of the specialist's definition (e.g., in genotype)
    # For now, we use a hardcoded mapping.
    function_keywords = {
        "technical_help": ["kod", "bug", "błąd", "programowanie", "python", "javascript", "debug"],
        "data_analysis": ["dane", "analiza", "statystyki", "wykres", "raport", "tabela"],
        "creative_writing": ["napisz", "utwórz", "opowieść", "artykuł", "tekst", "wiersz", "opowiadanie"],
        "math_help": ["oblicz", "matematyka", "równanie", "procent", "suma", "różnica", "iloczyn"],
        "general_query": ["co", "jak", "dlaczego", "gdzie", "kiedy", "kim", "czy"] # General questions
    }

    matched_function = None

    # Iterate through defined specialist functions and their keywords
    for func_name, keywords in function_keywords.items():
        # Check if the function name exists in Lux's available functions
        if func_name in available_functions:
            # Check if any keyword from the list is present in the user's message
            if any(keyword in message_lower for keyword in keywords):
                matched_function = func_name
                break # Use the first matched function

    # If no specific function matched, try to find a general purpose one or fallback
    if not matched_function:
        # If a "general_query" type function is available, use it as a fallback
        if "general_query" in available_functions:
            matched_function = "general_query"
        # As a last resort, if any function is available, return the first one
        elif available_functions:
            matched_function = next(iter(available_functions.keys()))

    return matched_function

@app.post("/api/chat")
async def chat_with_lux(request: Request):
    """Endpoint do komunikacji z asystentem Lux z kontekstem ostatnich 10 wiadomości"""
    try:
        data = await request.json()
        message = data.get("message", "")
        fingerprint = data.get("fingerprint", "anonymous")

        if not message:
            return JSONResponse({"error": "Message is required"}, status_code=400)

        # Pobierz lub utwórz sesję dla użytkownika
        session_id = request.headers.get("session-id")

        # Import session_manager locally
        try:
            from luxdb.core.session_assistant import session_manager
        except ImportError:
            return JSONResponse({"error": "Lux session manager not found."}, status_code=500)

        try:
            if session_id:
                assistant = await session_manager.get_session(session_id)
                if not assistant:
                    # Utwórz nową sesję jeśli nie istnieje
                    assistant = await session_manager.create_session(fingerprint)
                    session_id = assistant.session.session_id
            else:
                # Utwórz nową sesję
                assistant = await session_manager.create_session(fingerprint)
                session_id = assistant.session.session_id

            # Przetwórz wiadomość z kontekstem
            response = await assistant.process_message(message)

            return JSONResponse({
                "response": response,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "context_loaded": True
            })

        except Exception as e:
            print(f"❌ Błąd sesji asystenta: {e}")
            # Fallback - użyj globalnego asystenta
            try:
                global_lux = await session_manager.get_global_lux()
                if global_lux:
                    response = await global_lux.chat(message) # Assuming global_lux has a 'chat' method
                    return JSONResponse({
                        "response": response,
                        "session_id": None,
                        "timestamp": datetime.now().isoformat(),
                        "context_loaded": False,
                        "fallback": True
                    })
            except Exception as global_e:
                print(f"❌ Błąd globalnego asystenta: {global_e}")
                pass # Continue to ultimate fallback

            # Ostateczny fallback
            return JSONResponse({
                "response": f"Cześć! Otrzymałem twoją wiadomość: '{message}'. System jest w trybie ograniczonym.",
                "session_id": None,
                "timestamp": datetime.now().isoformat(),
                "context_loaded": False,
                "fallback": True
            })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)