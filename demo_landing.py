import os
import uvicorn
import socketio
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from database.postgre_db import Postgre_db
import asyncio
import json
from fastapi import Request
from fastapi.responses import HTMLResponse

# Import simplified system
from luxdb.simple_api import SimpleLuxDB, SimpleEntity

# FastAPI app
app = FastAPI(title="LuxDB MVP - Simplified", version="3.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False
)

# Initialize Simplified LuxDB
luxdb = SimpleLuxDB()

@app.on_event("startup")
async def startup_event():
    print("🌟 Simplified LuxDB Demo started!")

    # Initialize database
    try:
        pool = await Postgre_db.get_db_pool()
        print("✅ Database connection established")

        # Create some demo entities using simple API
        print("📝 Creating demo entities with simple API...")

        # Create user entity
        user = await luxdb.create_entity(
            name="Demo User",
            data={
                "email": "demo@luxdb.com",
                "age": 25,
                "preferences": ["AI", "databases", "graphs"]
            },
            entity_type="user"
        )

        # Create AI agent entity  
        agent = await luxdb.create_entity(
            name="AI Assistant", 
            data={
                "model": "gpt-4",
                "capabilities": ["analysis", "generation", "reasoning"],
                "active": True
            },
            entity_type="ai_agent"
        )

        # Create simple connection
        await luxdb.connect_entities(user.id, agent.id, "interacts_with")

        print("✅ Demo entities created successfully!")

    except Exception as e:
        print(f"❌ Startup error: {e}")

# Configure static files
app.mount("/static", StaticFiles(directory="static"), name="static")
socket_app = socketio.ASGIApp(sio, app)

@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"🌟 CLIENT CONNECTED: {sid}")
    await sio.emit('demo_data', {
        'message': 'Connected to Simplified LuxDB',
        'timestamp': datetime.now().isoformat(),
        'version': '3.0.0'
    })

@sio.event
async def request_graph_data(sid):
    """Send graph data using simple API"""
    try:
        print("📡 Fetching graph data with simple API...")

        # Get all entities and connections using simple API
        entities = await luxdb.query_entities()
        graph_data = await luxdb.get_graph_data()

        print(f"📤 Sending simplified graph data: {len(entities)} entities")
        await sio.emit('graph_data', graph_data, room=sid)

    except Exception as e:
        print(f"❌ Error getting graph data: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@app.post("/api/create_entity")
async def create_entity_endpoint(request: Request):
    """Simple endpoint to create entities"""
    try:
        data = await request.json()
        entity = await luxdb.create_entity(
            name=data.get('name'),
            data=data.get('data', {}),
            entity_type=data.get('type', 'entity')
        )

        # Notify graph update
        await sio.emit('graph_data_updated')

        return {
            "success": True,
            "entity": entity.to_dict(),
            "message": f"Entity '{entity.name}' created successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/connect_entities")  
async def connect_entities_endpoint(request: Request):
    """Simple endpoint to connect entities"""
    try:
        data = await request.json()
        await luxdb.connect_entities(
            data.get('entity1_id'),
            data.get('entity2_id'), 
            data.get('relation_type', 'connected')
        )

        await sio.emit('graph_data_updated')

        return {
            "success": True,
            "message": "Entities connected successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/")
async def main_page():
    return FileResponse("static/index.html")

@app.get("/graph")  
async def graph_page():
    return FileResponse('static/graph.html')

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "Simplified LuxDB",
        "version": "3.0.0",
        "entities": len(await luxdb.query_entities()) if luxdb else 0
    }

if __name__ == "__main__":
    print("🚀 Starting Simplified LuxDB Demo...")
    print("=" * 50)
    print("✨ Now with intuitive API!")
    print("📡 Much simpler entity management")  
    print("🎯 Easy graph synchronization")
    print("=" * 50)

    uvicorn.run(socket_app, host="0.0.0.0", port=3001, log_level="info")