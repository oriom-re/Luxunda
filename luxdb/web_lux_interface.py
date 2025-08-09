"""
Web Interface for Lux AI Assistant
"""

from fastapi import FastAPI, Request, WebSocket, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import asyncio
from luxdb.ai_lux_assistant import LuxAssistant
from luxdb.core.session_assistant import session_manager, SessionManager
from database.postgre_db import Postgre_db
import os
import hashlib

app = FastAPI(title="Lux AI Assistant Web Interface")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global Session Manager
session_manager = SessionManager()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize Lux on startup"""
    global lux_assistant

    await Postgre_db.initialize()

    api_key = os.getenv("OPENAI_API_KEY", "demo-key")
    lux_assistant = LuxAssistant(api_key)
    await lux_assistant.initialize()

    print("🌟 Lux AI Assistant Web Interface started!")

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
    from .core.auth_session import auth_manager

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
    """WebSocket endpoint for Session-based Lux conversations"""
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
        manager.disconnect(websocket)
        # Session will be cleaned up automatically by TTL

    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        await websocket.close()

# API Endpoints dla systemu komunikacji

@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Endpoint logowania"""
    from .core.auth_session import auth_manager

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
    from .core.auth_session import auth_manager

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

@app.post("/api/events/send")
async def send_event(request: EventRequest, session_data: dict = Depends(verify_token)):
    """Endpoint wysyłania eventów z frontendu"""
    from ..models.event import Event

    try:
        # Sprawdź czy user_ulid się zgadza
        if request.user_ulid != session_data["user_ulid"]:
            raise HTTPException(status_code=403, detail="Unauthorized user_ulid")

        # Utwórz event
        event = await Event.create_event(
            "frontend_event",
            {
                "event_type": request.event_type,
                "user_ulid": request.user_ulid,
                "payload": request.payload,
                "session_id": session_data["session_id"]
            }
        )

        return JSONResponse({
            "success": True,
            "event_id": event.ulid,
            "message": "Event sent successfully"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Send event error: {str(e)}"
        }, status_code=500)

@app.post("/api/events/poll")
async def poll_events(request: PollRequest, session_data: dict = Depends(verify_token)):
    """Endpoint pollowania eventów dla frontendu"""
    from ..models.event import Event

    try:
        # Sprawdź czy connection_ulid należy do sesji
        if request.connection_ulid != session_data["connection_ulid"]:
            raise HTTPException(status_code=403, detail="Unauthorized connection_ulid")

        # Pobierz eventy dla tego connection
        all_events = await Event.get_all()
        connection_events = []

        for event in all_events:
            payload = getattr(event, 'payload', {})
            if (payload.get('target_connection') == request.connection_ulid and
                event.event_type == 'frontend_message'):

                # Sprawdź czy to nowy event
                if not request.last_event_id or event.ulid > request.last_event_id:
                    connection_events.append({
                        "id": event.ulid,
                        "event_type": event.event_type,
                        "message_data": payload.get('message_data', {}),
                        "created_at": getattr(event, 'created_at', None)
                    })

        # Sortuj po czasie utworzenia
        connection_events.sort(key=lambda e: e.get('created_at', ''))

        return JSONResponse({
            "success": True,
            "events": connection_events[-10:],  # Ostatnie 10 eventów
            "count": len(connection_events)
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Poll events error: {str(e)}"
        }, status_code=500)

@app.post("/api/connection/heartbeat")
async def connection_heartbeat(request: HeartbeatRequest, session_data: dict = Depends(verify_token)):
    """Endpoint heartbeat dla połączenia"""
    from .core.auth_session import auth_manager

    try:
        # Sprawdź czy connection_ulid należy do sesji
        if request.connection_ulid != session_data["connection_ulid"]:
            raise HTTPException(status_code=403, detail="Unauthorized connection_ulid")

        # Aktualizuj heartbeat
        await auth_manager.update_connection_heartbeat(request.connection_ulid)

        return JSONResponse({
            "success": True,
            "message": "Heartbeat updated"
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Heartbeat error: {str(e)}"
        }, status_code=500)

@app.get("/api/user/events")
async def get_user_events(limit: int = 50, session_data: dict = Depends(verify_token)):
    """Endpoint pobierania eventów użytkownika"""
    from .core.auth_session import auth_manager

    try:
        user_events = await auth_manager.get_user_events(session_data["user_ulid"], limit)

        events_data = []
        for event in user_events:
            events_data.append({
                "id": event.ulid,
                "event_type": event.event_type,
                "payload": getattr(event, 'payload', {}),
                "progress": getattr(event, 'progress', 0),
                "status": getattr(event, 'status', 'unknown'),
                "created_at": getattr(event, 'created_at', None)
            })

        return JSONResponse({
            "success": True,
            "events": events_data,
            "count": len(events_data)
        })

    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": f"Get events error: {str(e)}"
        }, status_code=500)

@app.get("/api/tools")
async def get_available_tools():
    """Get list of available tools/beings"""
    from luxdb.models.being import Being

    all_beings = await Being.load_all()
    tools = []

    for being in all_beings:
        tools.append({
            "ulid": being.ulid,
            "alias": being.alias,
            "type": being.genotype.get("genesis", {}).get("type", "unknown"),
            "description": being.genotype.get("genesis", {}).get("description", "No description")
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)