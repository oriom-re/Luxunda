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
import engineio

# Import simplified system
from luxdb.simple_api import SimpleLuxDB, SimpleEntity
from luxdb.core.deployment_manager import deployment_manager
from luxdb.core.workspace_manager import workspace_manager

# FastAPI app - configured by deployment mode
app_config = {
    "title": f"LuxDB MVP - {deployment_manager.mode.value.title()}",
    "version": "3.0.0",
    "debug": deployment_manager.get_config('debug')
}

if not deployment_manager.is_production():
    app_config["docs_url"] = "/docs"
    app_config["redoc_url"] = "/redoc"

app = FastAPI(**app_config)

# Add CORS middleware
cors_origins = ["*"] if deployment_manager.is_development() else [
    os.getenv('FRONTEND_URL', 'https://*.replit.dev'),
    os.getenv('DOMAIN_URL', 'https://*.replit.co')
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Socket.IO Configuration with better stability settings
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    logger=False,  # Disable verbose logging
    engineio_logger=False,
    ping_timeout=60,  # Increase ping timeout
    ping_interval=25,  # Ping every 25 seconds
    max_http_buffer_size=1000000,  # 1MB buffer
    transports=['websocket', 'polling'],  # Allow fallback to polling
    async_mode='asgi'
)

# Initialize Simplified LuxDB
luxdb = SimpleLuxDB()

@app.on_event("startup")
async def startup_event():
    print("🌟 Simplified LuxDB Demo started!")

    # Initialize database
    print("🔄 Inicjalizacja puli połączeń do bazy PostgreSQL...")
    try:
        db_pool = await Postgre_db.get_db_pool()
        if not db_pool:
            print("❌ Startup error: Could not initialize database pool")
            return
        print("✅ Database pool initialized successfully!")
    except Exception as e:
        print(f"❌ Startup error: {e}")
        print("⚠️ Continuing without database connection...")

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

    # Create project entity
    project = await luxdb.create_entity(
        name="LuxDB Project",
        data={
            "description": "Revolutionary genetic database",
            "status": "active",
            "version": "3.0.0"
        },
        entity_type="project"
    )

    # Create simple connections
    await luxdb.connect_entities(user.id, agent.id, "interacts_with")
    await luxdb.connect_entities(user.id, project.id, "owns")
    await luxdb.connect_entities(agent.id, project.id, "assists_with")

    print("✅ Demo entities created successfully!")

# Configure static files
app.mount("/static", StaticFiles(directory="static"), name="static")
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Socket.IO Events with improved error handling
@sio.event
async def connect(sid, environ):
    print(f"🌟 CLIENT CONNECTED: {sid}")

    try:
        # Send welcome message
        await sio.emit('demo_data', {
            'message': 'Connected to Simplified LuxDB',
            'timestamp': datetime.now().isoformat(),
            'version': '3.0.0'
        }, room=sid)

        # Auto-send initial graph data
        await request_graph_data(sid)
    except Exception as e:
        print(f"❌ Error in connect handler: {e}")

@sio.event
async def disconnect(sid):
    print(f"💔 CLIENT DISCONNECTED: {sid}")

@sio.event
async def request_graph_data(sid):
    print("📡 Fetching graph data with simple API...")
    try:
        # Pobierz dane z Simple API - używaj globalnej instancji
        graph_data = await luxdb.get_graph_data_async()
        
        # Jeśli nie ma danych, wyślij testowe
        if not graph_data.get('beings') and not graph_data.get('relationships'):
            print("📝 Sending test data as fallback...")
            test_data = {
                'beings': [
                    {
                        'id': 'demo_user',
                        'name': 'Demo User',
                        'type': 'user',
                        'x': 100,
                        'y': 100,
                        'data': {'email': 'demo@luxdb.com', 'age': 25}
                    },
                    {
                        'id': 'ai_assistant',
                        'name': 'AI Assistant', 
                        'type': 'ai_agent',
                        'x': 200,
                        'y': 150,
                        'data': {'model': 'gpt-4', 'active': True}
                    },
                    {
                        'id': 'luxdb_project',
                        'name': 'LuxDB Project',
                        'type': 'project', 
                        'x': 150,
                        'y': 200,
                        'data': {'version': '3.0.0', 'status': 'active'}
                    }
                ],
                'relationships': [
                    {
                        'id': 'rel_1',
                        'source': 'demo_user',
                        'target': 'ai_assistant',
                        'type': 'interacts_with'
                    },
                    {
                        'id': 'rel_2', 
                        'source': 'demo_user',
                        'target': 'luxdb_project',
                        'type': 'owns'
                    },
                    {
                        'id': 'rel_3',
                        'source': 'ai_assistant',
                        'target': 'luxdb_project', 
                        'type': 'assists_with'
                    }
                ]
            }
            await sio.emit('graph_data', test_data, room=sid)
        else:
            await sio.emit('graph_data', {
                'beings': graph_data.get('beings', []),
                'relationships': graph_data.get('relationships', [])
            }, room=sid)
            
        print(f"📤 Graph data sent successfully")
    except Exception as e:
        print(f"❌ Error fetching graph data: {e}")
        # Wyślij testowe dane jako fallback
        test_data = {
            'beings': [
                {
                    'id': 'error_fallback',
                    'name': 'LuxDB System',
                    'type': 'system',
                    'x': 150,
                    'y': 150,
                    'data': {'status': 'initializing', 'error': str(e)[:100]}
                }
            ],
            'relationships': []
        }
        await sio.emit('graph_data', test_data, room=sid)
        await sio.emit('error', {'message': f'Fallback data loaded due to: {str(e)}'}, room=sid)

@sio.event
async def ping(sid):
    """Handle ping from client to keep connection alive"""
    await sio.emit('pong', {'timestamp': datetime.now().isoformat()}, room=sid)

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
        "mode": deployment_manager.mode.value,
        "entities": len(await luxdb.query_entities()) if luxdb else 0,
        "workspace_enabled": deployment_manager.should_enable_feature('workspace')
    }

@app.get("/api/workspace/changes")
async def get_workspace_changes(limit: int = 50):
    """Get recent workspace changes"""
    if not deployment_manager.should_enable_feature('workspace'):
        return {"error": "Workspace disabled in production"}
    
    return {
        "changes": workspace_manager.get_changes(limit),
        "total": len(workspace_manager.changes_log)
    }

@app.get("/api/workspace/being/{being_ulid}")
async def get_being_workspace(being_ulid: str):
    """Get files created by specific being"""
    if not deployment_manager.should_enable_feature('workspace'):
        return {"error": "Workspace disabled in production"}
    
    return {
        "being_ulid": being_ulid,
        "files": workspace_manager.get_being_files(being_ulid)
    }

@app.post("/api/workspace/create_file")
async def create_workspace_file(request: Request):
    """Create file in workspace"""
    if not deployment_manager.should_enable_feature('workspace'):
        return {"error": "Workspace disabled in production"}
    
    data = await request.json()
    file_path = await workspace_manager.create_file(
        being_ulid=data.get('being_ulid'),
        filename=data.get('filename'),
        content=data.get('content'),
        file_type=data.get('file_type', 'py')
    )
    
    # Notify via socket
    await sio.emit('workspace_change', {
        'action': 'file_created',
        'being_ulid': data.get('being_ulid'),
        'file_path': file_path
    })
    
    return {
        "success": True,
        "file_path": file_path,
        "message": "File created in workspace"
    }

@app.get("/test")
async def test():
    return {"message": "Hello from LuxDB Demo!"}

@app.get("/test-data")
async def test_data():
    """Endpoint testowy z przykładowymi danymi"""
    test_data = {
        "nodes": [
            {"id": "test1", "label": "Test Node 1", "type": "test", "data": {"value": 1}},
            {"id": "test2", "label": "Test Node 2", "type": "test", "data": {"value": 2}},
            {"id": "test3", "label": "Test Node 3", "type": "test", "data": {"value": 3}}
        ],
        "links": [
            {"source": "test1", "target": "test2", "type": "test_relation"},
            {"source": "test2", "target": "test3", "type": "test_relation"}
        ]
    }
    await sio.emit('graph_data', test_data)
    return test_data

if __name__ == "__main__":
    config = deployment_manager.get_config()
    
    print(f"🚀 Starting LuxDB {deployment_manager.mode.value.title()} Mode...")
    print("=" * 60)
    print(f"🌍 Host: {config['host']}:{config['port']}")
    print(f"🔧 Debug: {config['debug']}")
    print(f"📁 Workspace: {config['workspace_enabled']}")
    print(f"🤖 Discord: {config['discord_enabled']}")
    print("=" * 60)

    # Setup workspace sync callback for Socket.IO
    if deployment_manager.should_enable_feature('workspace'):
        async def workspace_sync_callback(change):
            await sio.emit('workspace_sync', change)
        
        workspace_manager.add_sync_callback(workspace_sync_callback)
        print("📁 Workspace synchronization enabled")

    uvicorn.run(
        socket_app,
        host=config['host'],
        port=config['port'],
        log_level=config['log_level'].lower(),
        reload=config.get('hot_reload', False)
    )