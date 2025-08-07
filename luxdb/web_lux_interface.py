
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
from database.postgre_db import Postgre_db
import os

app = FastAPI(title="Lux AI Assistant Web Interface")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global Lux instance
lux_assistant = None

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
    """WebSocket endpoint for Lux conversations"""
    await manager.connect(websocket)
    
    # Send welcome message
    await websocket.send_text(json.dumps({
        "type": "system",
        "message": "🌟 Witaj! Jestem Lux - Twój AI asystent do zarządzania bytami i narzędziami!",
        "timestamp": "now"
    }))
    
    try:
        while True:
            # Receive user message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "user_message":
                user_message = message_data["message"]
                
                # Send thinking indicator
                await websocket.send_text(json.dumps({
                    "type": "thinking",
                    "message": "🤔 Lux myśli...",
                }))
                
                # Process with Lux
                response = await lux_assistant.chat(user_message)
                
                # Send Lux response
                await websocket.send_text(json.dumps({
                    "type": "lux_response", 
                    "message": response,
                    "timestamp": "now"
                }))
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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
