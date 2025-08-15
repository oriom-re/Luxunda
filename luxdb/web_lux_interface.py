"""
Web Interface for Lux AI Assistant
"""

from fastapi import FastAPI, Request, WebSocket, HTTPException, Depends, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="static")
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import os
from typing import Optional
import asyncio
from datetime import datetime
from luxdb.core.globals import Globals
from luxdb.core.postgre_db import Postgre_db
from luxdb.core.system_manager import system_manager
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.ai_lux_assistant import LuxAssistant
import hashlib

app = FastAPI(title="Lux AI Assistant Web Interface")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global Session Manager - będzie zaimportowany z session_data_manager
session_manager = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

async def initialize_lux_assistant():
    """Initialize Lux Assistant with system context"""
    global lux_assistant
    api_key = os.getenv("OPENAI_API_KEY", "demo-key")
    lux_assistant = LuxAssistant(api_key)
    await lux_assistant.initialize()

@app.on_event("startup")
async def startup_event():
    """Initialize unified system"""
    try:
        # Initialize unified system manager
        await system_manager.initialize_system(
            kernel_type="simple",  # Start with simple kernel for web
            load_genotypes=True
        )

        # Initialize OpenAI connection test
        try:
            import openai
            openai.api_key = os.getenv('OPENAI_API_KEY')
            print("✅ OpenAI connection successful")
        except Exception as e:
            print(f"⚠️ OpenAI connection warning: {e}")

        # Initialize Lux Assistant with unified system
        await initialize_lux_assistant()

        print("🌟 Lux AI Assistant Web Interface started!")

    except Exception as e:
        print(f"❌ Startup error: {e}")

# Pydantic models
class LoginRequest(BaseModel):
    username: str
    password: str
    fingerprint: str

class EventRequest(BaseModel):
    event_type: str
    user_ulid: str
    payload: Dict[str, Any]

class PollRequest(BaseModel):
    connection_ulid: str
    last_event_id: Optional[str] = None

class HeartbeatRequest(BaseModel):
    connection_ulid: str

# Security
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from luxdb.core.auth_session import auth_manager

    token = credentials.credentials
    session_data = await auth_manager.validate_session(token)

    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return session_data

@app.get("/")
async def root(request: Request):
    """Strona główna z interfejsem Lux"""
    return templates.TemplateResponse("lux_interface.html", {"request": request})

@app.get("/login")
async def login_page(request: Request):
    """Strona logowania"""
    with open("static/login-interface.html", "r", encoding="utf-8") as f:
        content = f.read()
    return HTMLResponse(content=content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication with heartbeat support"""
    await manager.connect(websocket)

    # Initialize session
    user_session = None

    try:
        # First message should contain user identification
        data = await websocket.receive_text()
        init_data = json.loads(data)

        if init_data.get("type") == "init_session":
            # Create user fingerprint
            user_info = init_data.get("user_info", {})
            fingerprint_data = f"{user_info.get('user_agent', '')}{user_info.get('screen_resolution', '')}{user_info.get('timezone', '')}"
            user_fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()

            # Create session assistant
            user_session = await session_manager.create_session(
                user_fingerprint=user_fingerprint,
                user_ulid=user_info.get("user_ulid"),
                ttl_minutes=30
            )

            # Send welcome with context
            context = await user_session.build_conversation_context()
            await websocket.send_text(json.dumps({
                "type": "system",
                "message": f"🌟 Witaj! Jestem Lux - Twój kontekstowy asystent!\n\nTwoja sesja: {user_session.session.session_id[:8]}...\nAktywne projekty: {', '.join(user_session.session.project_tags) if user_session.session.project_tags else 'Brak'}",
                "session_context": context,
                "timestamp": "now"
            }))
        elif init_data.get('type') == 'ping':
            await websocket.send_text(json.dumps({
                'type': 'pong',
                'timestamp': init_data.get('timestamp'),
                'server_time': datetime.now().isoformat()
            }))
            return # Pong handled, don't proceed further in this loop
        elif init_data.get('type') == 'connection':
            print(f"🔗 Client connected: {init_data.get('fingerprint', 'unknown')}")
            await websocket.send_text(json.dumps({
                'type': 'connection_ack',
                'status': 'connected',
                'server_time': datetime.now().isoformat()
            }))
            return # Connection ack handled, don't proceed further in this loop
        else:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Proszę zainicjalizować sesję"
            }))
            return

        # Main conversation loop
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data.get('type') == 'ping':
                await websocket.send_text(json.dumps({
                    'type': 'pong',
                    'timestamp': message_data.get('timestamp'),
                    'server_time': datetime.now().isoformat()
                }))
                continue

            # Handle connection info (if client reconnects or sends it again)
            if message_data.get('type') == 'connection':
                print(f"🔗 Client connected: {message_data.get('fingerprint', 'unknown')}")
                await websocket.send_text(json.dumps({
                    'type': 'connection_ack',
                    'status': 'connected',
                    'server_time': datetime.now().isoformat()
                }))
                continue


            if message_data["type"] == "user_message":
                user_message = message_data["message"]

                # Send thinking indicator with context
                await websocket.send_text(json.dumps({
                    "type": "thinking",
                    "message": f"🤔 Analizuję w kontekście {len(user_session.session.active_events)} aktywnych eventów...",
                }))

                # Process with Session Assistant
                response = await user_session.process_message(user_message)

                # Send contextual response
                context = await user_session.build_conversation_context()
                await websocket.send_text(json.dumps({
                    "type": "lux_response",
                    "message": response,
                    "session_context": context,
                    "active_projects": list(user_session.session.project_tags),
                    "recent_activity": user_session.get_recent_actions_summary(),
                    "timestamp": "now"
                }))

            elif message_data["type"] == "user_action":
                # Track user action as event
                action_data = message_data.get("action", {})
                await user_session.track_event_from_frontend(action_data)

                await websocket.send_text(json.dumps({
                    "type": "action_tracked",
                    "message": f"Akcja {action_data.get('type', 'unknown')} została zarejestrowana"
                }))

    except WebSocketDisconnect:
        print("🔌 WebSocket disconnected normally")
        manager.disconnect(websocket)
        # Session will be cleaned up automatically by TTL

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)
        # Consider sending an error message to the client before closing if possible
        try:
            await websocket.send_text(json.dumps({
                'type': 'error',
                'message': f'Server error: {str(e)}',
                'timestamp': datetime.now().isoformat()
            }))
            await websocket.close()
        except:
            pass # Ignore errors during closing

# Helper function to process websocket messages (moved from main loop for clarity)
async def process_websocket_message(message_data: Dict[str, Any]):
    """Processes a message received from the WebSocket client."""
    # This function would contain the logic to handle different message types
    # For now, it's a placeholder. The original code's logic is integrated above.
    # If this function were to be used, it would need access to user_session.
    # For demonstration, we'll return a dummy response.
    # In a real scenario, you'd pass user_session to this function.

    # Placeholder for actual message processing logic.
    # The logic from the original websocket_endpoint is now directly in the endpoint.
    # If this function were to be called, it would need access to `user_session`.
    # Example:
    # if message_data["type"] == "user_message":
    #     user_message = message_data["message"]
    #     response = await user_session.process_message(user_message)
    #     context = await user_session.build_conversation_context()
    #     return {
    #         "type": "lux_response",
    #         "message": response,
    #         "session_context": context,
    #         "active_projects": list(user_session.session.project_tags),
    #         "recent_activity": user_session.get_recent_actions_summary(),
    #         "timestamp": "now"
    #     }
    raise NotImplementedError("Message processing logic needs to be implemented or integrated.")


# API Endpoints dla systemu komunikacji

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Endpoint logowania"""
    from luxdb.core.auth_session import auth_manager

    try:
        session_data = await auth_manager.authenticate_user(
            request.username,
            request.password,
            request.fingerprint
        )

        if session_data:
            return JSONResponse({
                "success": True,
                "session": session_data,
                "message": "Authentication successful"
            })
        else:
            return JSONResponse({
                "success": False,
                "message": "Invalid credentials"
            }, status_code=401)

    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Authentication error: {str(e)}"
        }, status_code=500)

@app.post("/api/auth/logout")
async def logout(session_data: dict = Depends(verify_token)):
    """Endpoint wylogowania"""
    from luxdb.core.auth_session import auth_manager

    try:
        await auth_manager.invalidate_session(session_data["session_id"])
        return JSONResponse({
            "success": True,
            "message": "Logged out successfully"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Logout error: {str(e)}"
        }, status_code=500)

@app.get("/api/tools")
async def get_available_tools():
    """Get list of available tools/beings"""
    all_beings = await Being.get_all()
    tools = []

    for being in all_beings:
        # Get soul to access genotype
        soul = await being.get_soul()
        genotype = soul.genotype if soul else {}

        tools.append({
            "ulid": being.ulid,
            "alias": being.alias,
            "type": genotype.get("genesis", {}).get("type", "unknown"),
            "description": genotype.get("genesis", {}).get("description", "No description")
        })

    return {"tools": tools}

@app.get("/api/search")
async def search_tools(query: str):
    """Search for tools by query"""
    if not lux_assistant:
        return {"error": "Lux not initialized"}

    keywords = query.split()
    results = await lux_assistant.search_similar_tools(keywords)

    return {"results": results}

@app.get("/api/access/zones")
async def get_access_zones(request: Request):
    """Pobiera wszystkie strefy dostępu"""
    try:
        from luxdb.core.access_control import access_controller

        zones_data = {}
        for zone_id, zone in access_controller.zones.items():
            zones_data[zone_id] = zone.to_dict()

        return {"zones": zones_data}
    except Exception as e:
        return {"error": f"Error getting zones: {str(e)}"}

@app.get("/api/access/summary")
async def get_access_summary(request: Request):
    """Pobiera podsumowanie dostępów dla użytkownika"""
    try:
        # Pobierz token z nagłówka
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {"error": "Authorization required"}

        token = auth_header[7:]

        # Waliduj sesję
        from luxdb.core.auth_session import auth_manager
        session_data = await auth_manager.validate_session(token)
        if not session_data:
            return {"error": "Invalid session"}

        # Pobierz podsumowanie dostępów
        summary = auth_manager.get_user_access_summary(session_data["user_ulid"])
        return {"access_summary": summary}

    except Exception as e:
        return {"error": f"Error getting access summary: {str(e)}"}

@app.post("/api/beings/create_secured")
async def create_secured_being(request: Request):
    """Tworzy nowy byt z kontrolą dostępu"""
    try:
        # Pobierz token z nagłówka
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return {"error": "Authorization required"}

        token = auth_header[7:]

        # Waliduj sesję
        from luxdb.core.auth_session import auth_manager
        session_data = await auth_manager.validate_session(token)
        if not session_data:
            return {"error": "Invalid session"}

        # Pobierz dane z requestu
        data = await request.json()
        soul_alias = data.get("soul_alias")
        being_data = data.get("data", {})
        access_level = data.get("access_level", "authenticated")
        alias = data.get("alias")
        ttl_hours = data.get("ttl_hours")

        if not soul_alias:
            return {"error": "soul_alias is required"}

        # Pobierz Soul
        soul = await Soul.get_by_alias(soul_alias)
        if not soul:
            return {"error": f"Soul with alias '{soul_alias}' not found"}

        # Utwórz zabezpieczony byt
        being = await auth_manager.create_secured_being(
            user_ulid=session_data["user_ulid"],
            soul=soul,
            data=being_data,
            access_level=access_level,
            alias=alias,
            ttl_hours=ttl_hours
        )

        return {
            "success": True,
            "being": being.to_dict(),
            "message": f"Secured being created in {access_level} zone"
        }

    except Exception as e:
        return {"error": f"Error creating secured being: {str(e)}"}

@app.get("/api/beings/by_zone/{zone_id}")
async def get_beings_by_zone(request: Request):
    """Pobiera byty z określonej strefy dostępu"""
    try:
        zone_id = request.path_params.get("zone_id")

        # Pobierz token z nagłówka (opcjonalnie)
        auth_header = request.headers.get('Authorization', '')
        user_ulid = None
        user_session = None

        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            from luxdb.core.auth_session import auth_manager
            session_data = await auth_manager.validate_session(token)
            if session_data:
                user_ulid = session_data["user_ulid"]
                user_session = session_data

        # Pobierz byty ze strefy
        beings = await Being.get_by_access_zone(zone_id, user_ulid, user_session)

        beings_data = []
        for being in beings:
            being_dict = being.to_dict()
            # Dodaj informacje o Soul
            soul = await being.get_soul()
            if soul:
                being_dict["_soul"] = {
                    "soul_hash": soul.soul_hash,
                    "alias": soul.alias,
                    "genotype": soul.genotype
                }
            beings_data.append(being_dict)

        return {
            "zone_id": zone_id,
            "beings": beings_data,
            "total": len(beings_data)
        }

    except Exception as e:
        return {"error": f"Error getting beings by zone: {str(e)}"}


if __name__ == "__main__":
    import asyncio
    from hypercorn.config import Config
    from hypercorn.asyncio import serve
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)