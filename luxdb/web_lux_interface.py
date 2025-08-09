
"""
Web Interface for Lux AI Assistant
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import asyncio
from typing import List
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

@app.get("/")
async def serve_interface():
    """Serve the main Lux interface"""
    return FileResponse("static/lux_interface.html")

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
