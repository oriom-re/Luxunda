import os
import uvicorn
import socketio
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
from database.postgre_db import Postgre_db

# FastAPI app
app = FastAPI(title="LuxDB MVP", version="2.0.0")

# Socket.IO server z poprawną konfiguracją
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["*"],
    logger=True,
    engineio_logger=True,
    transports=['websocket', 'polling']
)

@app.on_event("startup")
async def startup_event():
    print("🌟 FastAPI server started successfully!")
    print("📡 Socket.IO server initialized")
    print("🔗 Ready to accept connections...")

@app.middleware("http")
async def log_requests(request, call_next):
    print(f"📝 Request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"✅ Response: {response.status_code}")
    return response

# Configure static files serving
app.mount("/static", StaticFiles(directory="static"), name="static")

# Integrate Socket.IO with FastAPI
socket_app = socketio.ASGIApp(sio, app)

# Konfiguracja PostgreSQL
db = Postgre_db()

@sio.event
async def connect(sid, environ):
    """Obsługa połączenia klienta"""
    print(f"🌟 CLIENT CONNECTED: {sid}")
    print(f"📡 Client info: {environ.get('HTTP_USER_AGENT', 'Unknown')}")
    print(f"🌍 Client IP: {environ.get('REMOTE_ADDR', 'Unknown')}")

    # Wyślij początkowe dane
    await sio.emit('demo_data', {
        'message': 'Połączono z LuxDB MVP',
        'timestamp': datetime.now().isoformat(),
        'server_version': '2.0.0',
        'client_id': sid
    })

    print(f"✅ Initial data sent to client {sid}")

@sio.event
async def disconnect(sid):
    """Obsługa rozłączenia klienta"""
    print(f"👋 CLIENT DISCONNECTED: {sid}")
    print(f"📊 Active connections: {len(sio.manager.rooms.get('/', {}))} ")

@sio.event
async def request_graph_data(sid):
    """Obsługa żądania danych grafu"""
    print(f"📊 Graph data requested by client: {sid}")

    # Mock data for testing
    test_data = {
        'beings': [
            {'soul_uid': 'luxdb_core', '_soul': {'genesis': {'name': 'LuxDB Core', 'type': 'system'}}},
            {'soul_uid': 'ai_agent_1', '_soul': {'genesis': {'name': 'AI Agent', 'type': 'agent'}}},
            {'soul_uid': 'relation_manager', '_soul': {'genesis': {'name': 'Relations', 'type': 'manager'}}},
            {'soul_uid': 'semantic_data_1', '_soul': {'genesis': {'name': 'Semantic Data', 'type': 'data'}}}
        ],
        'relationships': [
            {'source_soul': 'luxdb_core', 'target_soul': 'ai_agent_1', 'genesis': {'type': 'manages'}},
            {'source_soul': 'luxdb_core', 'target_soul': 'relation_manager', 'genesis': {'type': 'controls'}},
            {'source_soul': 'ai_agent_1', 'target_soul': 'semantic_data_1', 'genesis': {'type': 'processes'}}
        ]
    }

    await sio.emit('graph_data', test_data, room=sid)
    print(f"✅ Graph data sent to client {sid}")

@app.get("/")
async def main_page():
    """Główna strona z interfejsem LuxDB"""
    print("🏠 Serving main page...")
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    print("💚 Health check requested")
    return {
        "status": "healthy",
        "service": "LuxDB MVP",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify server is working"""
    print("🧪 Test endpoint called!")
    return {
        "message": "LuxDB MVP Server is working!",
        "socket_io": "enabled",
        "static_files": "mounted",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import logging

    # Konfiguracja szczegółowego logowania
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("demo_landing")

    print("🚀 Starting LuxDB MVP Demo Server...")
    print("=" * 50)
    print(f"📡 Server will be available at: http://0.0.0.0:3001")
    print(f"🌐 Access from browser: https://{os.environ.get('REPL_SLUG', 'your-repl')}-{os.environ.get('REPL_OWNER', 'username')}.replit.app")
    print(f"📊 Static files served from: /static/")
    print("=" * 50)

    # Uruchom serwer na porcie 3001 z automatycznym reloadem
    uvicorn.run(
        socket_app,
        host="0.0.0.0",
        port=3001,
        reload=False,
        log_level="debug",
        access_log=True
    )