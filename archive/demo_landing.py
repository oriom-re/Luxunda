#!/usr/bin/env python3
"""
⚠️  UWAGA: Ten plik jest przestarzały!
Użyj głównego punktu wejścia: python main.py

🚀 LuxOS Landing Server
Unified LuxOS System - Landing & Development Interface
Enhanced with reactive system and proper lifespan management
"""

print("⚠️  UWAGA: demo_landing.py jest przestarzały!")
print("✅ Użyj głównego punktu wejścia: python main.py --mode=web")
exit(1)

import asyncio
import os
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

print("🚀 Starting LuxOS Landing Server...")
print("🌟 Unified LuxOS System Entry Point")
print("=" * 60)

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
    from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.templating import Jinja2Templates
    import socketio
    import uvicorn
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("📦 Installing required packages...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi", "uvicorn", "python-socketio", "jinja2"])

    # Try importing again
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
    from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.templating import Jinja2Templates
    import socketio
    import uvicorn

# Placeholder for AI Brain and Soul/Being/MessageSimilarityService - these need actual implementation
class AIAssistant:
    async def process_user_intent(self, intention_text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        print(f"AI Brain processing: '{intention_text}' with context: {context}")
        # Simulate AI analysis
        await asyncio.sleep(0.1) 
        return {
            "status": "analyzed",
            "original_intention": intention_text,
            "keywords": intention_text.split(),
            "sentiment": "neutral",
            "confidence": 0.8,
            "related_concepts": ["connection", "entity", "communication"]
        }

class Soul:
    @staticmethod
    async def load_by_alias(alias: str):
        print(f"Soul.load_by_alias({alias}) called")
        # Simulate loading
        await asyncio.sleep(0.01)
        # Return a mock object with a soul_hash attribute
        return type('MockSoul', (object,), {'soul_hash': f'hash_for_{alias}', 'alias': alias})()

    @staticmethod
    async def create(genotype: Dict[str, Any], alias: str):
        print(f"Soul.create({genotype}, {alias}) called")
        # Simulate creation
        await asyncio.sleep(0.01)
        return type('MockSoul', (object,), {'soul_hash': f'hash_for_{alias}', 'alias': alias})()

class Being:
    def __init__(self, soul, attributes: Dict[str, Any], alias: Optional[str] = None):
        self.soul = soul
        self.attributes = attributes
        self.ulid = f"being_{datetime.now().timestamp()}" # Mock ULID

    @classmethod
    async def create(cls, soul, attributes: Dict[str, Any], alias: Optional[str] = None):
        print(f"Being.create called for alias: {alias}")
        # Simulate creation
        await asyncio.sleep(0.01)
        return cls(soul, attributes, alias)

class MessageSimilarityService:
    def __init__(self, similarity_threshold: float):
        self.similarity_threshold = similarity_threshold
        print(f"MessageSimilarityService initialized with threshold: {similarity_threshold}")

    async def compare_messages_and_create_relations(self, message_soul_hash: str) -> Dict[str, Any]:
        print(f"Comparing messages for hash: {message_soul_hash}")
        # Simulate comparison and relation creation
        await asyncio.sleep(0.1)
        created_relations = 0
        if "message_being" in message_soul_hash: # Simple simulation
            created_relations = 2
        return {'created_relations': created_relations}

# Initialize AI Brain
ai_brain = AIAssistant()


# Globalne zmienne dla zarządzania aplikacją
app_state = {
    'luxdb': None,
    'connections': set(),
    'beings_count': 0,
    'active_users': 0,
    'stats': {
        'beings': 0,
        'tables': 0,
        'connections': 0,
        'commands': 0
    },
    'reactive_components': {},
    'page_state': {
        'current_beings': [],
        'selected_nodes': [],
        'graph_data': {'beings': [], 'relationships': []},
        'ui_state': {'zoom': 1.0, 'pan': {'x': 0, 'y': 0}}
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Proper lifespan management for FastAPI"""
    print("🚀 Starting LuxDB Development Mode...")
    print("=" * 60)
    print(f"🌍 Host: 0.0.0.0:3001")
    print(f"🔧 Debug: True")
    print(f"📁 Workspace: True")
    print("=" * 60)

    try:
        # Initialize demo data instead of LuxDB for now
        await load_initial_data()

        print("✅ LuxDB System initialized successfully")

        yield

    except Exception as e:
        print(f"❌ Startup error: {e}")
        yield

    finally:
        # Cleanup
        print("🔄 Shutting down LuxDB System...")
        print("✅ Shutdown complete")

# Create Socket.IO server
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    async_mode='asgi'
)

# Create FastAPI app with lifespan
app = FastAPI(
    title="LuxDB Development Server",
    description="Reactive development server for LuxDB system",
    version="2.0.0",
    lifespan=lifespan
)

# Mount Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="static")

async def load_initial_data():
    """Load initial data and update reactive state"""
    try:
        # Create demo beings for demonstration
        demo_beings = []
        for i in range(15):
            being_data = {
                'id': f'demo_being_{i:03d}',
                'name': f'LuxDB Entity {i}',
                'type': 'entity',
                'data': {'demo_id': i, 'energy': 100.0},
                'x': 100 + (i % 5) * 150,
                'y': 150 + (i // 5) * 120
            }
            demo_beings.append(being_data)

        app_state['page_state']['current_beings'] = demo_beings
        app_state['stats']['beings'] = len(demo_beings)
        app_state['stats']['tables'] = 3

        # Update graph data
        app_state['page_state']['graph_data']['beings'] = demo_beings

        print(f"📊 Loaded {len(demo_beings)} demo beings")

    except Exception as e:
        print(f"❌ Error loading initial data: {e}")

async def broadcast_state_update(data: Dict[str, Any]):
    """Broadcast state updates to all connected clients"""
    if app_state['connections']:
        message = json.dumps(data)
        disconnected = set()

        for websocket in app_state['connections'].copy():
            try:
                await websocket.send_text(message)
            except:
                disconnected.add(websocket)

        # Clean up disconnected clients
        app_state['connections'] -= disconnected
        app_state['stats']['connections'] = len(app_state['connections'])

async def update_reactive_component(component_id: str, data: Any):
    """Update specific reactive component and broadcast"""
    app_state['reactive_components'][component_id] = data
    await broadcast_state_update({
        'type': 'component_update',
        'component_id': component_id,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Serve the main landing page"""
    try:
        return templates.TemplateResponse("funding-landing.html", {"request": request})
    except:
        # Fallback to simple landing page
        return FileResponse("static/simple-landing.html")

@app.get("/graph", response_class=HTMLResponse)
async def graph_page(request: Request):
    """Serve the reactive graph page"""
    return templates.TemplateResponse("graph.html", {"request": request})

@app.get("/landing", response_class=HTMLResponse)
async def info_page(request: Request):
    """Serve the info landing page"""
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/funding", response_class=HTMLResponse)
async def funding_page(request: Request):
    """Serve the funding landing page"""
    return templates.TemplateResponse("funding-landing.html", {"request": request})

@app.get("/api/stats")
async def get_stats():
    """Get current system statistics"""
    return JSONResponse({
        'stats': app_state['stats'],
        'timestamp': datetime.now().isoformat(),
        'active_users': app_state['active_users'],
        'page_state': app_state['page_state']
    })

@app.get("/api/beings")
async def get_beings():
    """Get all beings data"""
    beings_data = app_state['page_state']['current_beings']
    return JSONResponse({'beings': beings_data})

@app.get("/api/graph-data")
async def get_graph_data():
    """Get graph data for visualization"""
    return JSONResponse({
        'beings': app_state['page_state']['graph_data']['beings'],
        'relationships': app_state['page_state']['graph_data']['relationships']
    })

@app.post("/api/create-being")
async def create_being_endpoint(request: Request):
    """Create a new being via API"""
    try:
        data = await request.json()
        name = data.get('name', 'New Being')
        being_type = data.get('type', 'entity')

        # Create new being data
        new_being_data = {
            'id': f'being_{datetime.now().timestamp()}',
            'name': name,
            'type': being_type,
            'data': {
                'created_via': 'api',
                'created_at': datetime.now().isoformat()
            },
            'x': 100 + len(app_state['page_state']['current_beings']) * 50,
            'y': 150
        }

        app_state['page_state']['graph_data']['beings'].append(new_being_data)
        app_state['page_state']['current_beings'].append(new_being_data)
        app_state['stats']['beings'] += 1
        app_state['stats']['commands'] += 1

        # Broadcast update
        await broadcast_state_update({
            'type': 'being_created',
            'being': new_being_data,
            'stats': app_state['stats']
        })

        return JSONResponse({'success': True, 'being': new_being_data})

    except Exception as e:
        print(f"❌ Error creating being: {e}")
        return JSONResponse({'success': False, 'error': str(e)})

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle client connection"""
    print(f"🔌 Client {sid} connected")
    app_state['active_users'] += 1

    # Send initial state
    await sio.emit('initial_state', {
        'stats': app_state['stats'],
        'page_state': app_state['page_state'],
        'reactive_components': app_state['reactive_components']
    }, to=sid)

    # Broadcast user count update
    await sio.emit('user_count_update', {
        'active_users': app_state['active_users']
    })

@sio.event
async def disconnect(sid):
    """Handle client disconnection"""
    print(f"🔌 Client {sid} disconnected")
    app_state['active_users'] = max(0, app_state['active_users'] - 1)

    # Broadcast user count update
    await sio.emit('user_count_update', {
        'active_users': app_state['active_users']
    })

@sio.event
async def request_graph_data(sid):
    """Send graph data to client"""
    await sio.emit('graph_data', {
        'beings': app_state['page_state']['graph_data']['beings'],
        'relationships': app_state['page_state']['graph_data']['relationships']
    }, to=sid)

@sio.event
async def create_being(sid, data):
    """Create a new being via Socket.IO"""
    name = data.get('name', f'Being_{datetime.now().strftime("%H%M%S")}')

    new_being_data = {
        'id': f'sio_being_{datetime.now().timestamp()}',
        'name': name,
        'type': 'entity',
        'data': {
            'created_via': 'socketio',
            'created_at': datetime.now().isoformat()
        },
        'x': 100 + len(app_state['page_state']['current_beings']) * 50,
        'y': 150 + (len(app_state['page_state']['current_beings']) // 5) * 120
    }

    app_state['page_state']['graph_data']['beings'].append(new_being_data)
    app_state['page_state']['current_beings'].append(new_being_data)
    app_state['stats']['beings'] += 1
    app_state['stats']['commands'] += 1

    # Broadcast to all clients
    await sio.emit('being_created', {
        'being': new_being_data,
        'stats': app_state['stats']
    })

@sio.event
async def ping(sid):
    """Handle ping requests"""
    await sio.emit('pong', to=sid)

@sio.event
async def intention_created(sid, data):
    """Obsługa nowych intencji od użytkowników"""
    print(f"📥 Received intention: {data}")

    try:
        # Analizuj intencję przez AI Brain
        analysis = await ai_brain.process_user_intent(
            data.get('intention_text', ''),
            context=data.get('context', {})
        )

        # Emit wynik
        await sio.emit('intention_response', {
            'status': 'processed',
            'analysis': analysis,
            'original_data': data
        }, to=sid)

    except Exception as e:
        print(f"❌ Error processing intention: {e}")
        await sio.emit('intention_response', {
            'status': 'error',
            'error': str(e)
        }, to=sid)

@sio.event
async def message_being_created(sid, data):
    """Obsługa nowych bytów-wiadomości z intencjami"""
    print(f"📥 Received message being: {data['being']['intention']['type']}")

    try:
        being_data = data['being']
        connections = data.get('connections', [])

        # Zapisz byt-wiadomość do bazy
        message_soul = await Soul.load_by_alias("message_being") 
        if not message_soul:
            # Utwórz genotyp dla bytów-wiadomości
            message_genotype = {
                "genesis": {
                    "name": "message_being",
                    "type": "communication",
                    "doc": "Byt reprezentujący wiadomość z intencją"
                },
                "attributes": {
                    "text": {"py_type": "str", "table_name": "_text"},
                    "intention_type": {"py_type": "str", "table_name": "_text"},
                    "intention_confidence": {"py_type": "float", "table_name": "_numeric"},
                    "keywords": {"py_type": "list", "table_name": "_jsonb"},
                    "sentiment": {"py_type": "str", "table_name": "_text"},
                    "author": {"py_type": "str", "table_name": "_text"},
                    "metadata": {"py_type": "dict", "table_name": "_jsonb"}
                }
            }
            message_soul = await Soul.create(message_genotype, "message_being")

        # Utwórz Being
        message_being = await Being.create(message_soul, {
            "text": being_data['text'],
            "intention_type": being_data['intention']['type'],
            "intention_confidence": being_data['intention']['confidence'],
            "keywords": being_data['keywords'],
            "sentiment": being_data['sentiment'],
            "author": being_data['author'],
            "metadata": {
                "connections": connections,
                "timestamp": being_data['timestamp']
            }
        }, alias=being_data['id'])

        # Analizuj połączenia i utwórz relacje
        similarity_service = MessageSimilarityService(similarity_threshold=0.5)
        relations_result = await similarity_service.compare_messages_and_create_relations(message_soul.soul_hash)

        # Emit potwierdzenie
        await sio.emit('message_being_response', {
            'status': 'created',
            'being_id': message_being.ulid,
            'connections_created': len(connections),
            'semantic_relations': relations_result.get('created_relations', 0)
        }, to=sid)

        # Jeśli znaleziono nowe połączenia, powiadom
        if relations_result.get('created_relations', 0) > 0:
            await sio.emit('new_connection_discovered', {
                'reason': f"Znaleziono {relations_result['created_relations']} semantycznych połączeń",
                'being_id': message_being.ulid
            })

        print(f"✅ Created message being with {len(connections)} connections")

    except Exception as e:
        print(f"❌ Error processing message being: {e}")
        await sio.emit('message_being_response', {
            'status': 'error', 
            'error': str(e)
        }, to=sid)


async def create_being_via_websocket(name: str, websocket: WebSocket):
    """Create being via WebSocket and broadcast update"""
    try:
        new_being_data = {
            'id': f'ws_being_{datetime.now().timestamp()}',
            'name': name,
            'type': 'entity',
            'data': {
                'created_via': 'websocket',
                'created_at': datetime.now().isoformat()
            },
            'x': 100 + len(app_state['page_state']['current_beings']) * 50,
            'y': 150 + (len(app_state['page_state']['current_beings']) // 5) * 120
        }

        app_state['page_state']['graph_data']['beings'].append(new_being_data)
        app_state['page_state']['current_beings'].append(new_being_data)
        app_state['stats']['beings'] += 1
        app_state['stats']['commands'] += 1

        # Broadcast to all clients
        await broadcast_state_update({
            'type': 'being_created',
            'being': new_being_data,
            'stats': app_state['stats']
        })

    except Exception as e:
        await websocket.send_text(json.dumps({
            'type': 'error',
            'message': f'Error creating being: {str(e)}'
        }))

@app.get("/test-data")
async def generate_test_data():
    """Generate test data for development"""
    try:
        # Add a few more beings for testing
        test_beings = []
        for i in range(5):
            being_data = {
                'id': f'test_being_{datetime.now().timestamp()}_{i}',
                'name': f'Test Being {i}',
                'type': 'test_entity',
                'data': {'test_data': True},
                'x': 300 + i * 80,
                'y': 300
            }
            test_beings.append(being_data)

        app_state['page_state']['graph_data']['beings'].extend(test_beings)
        app_state['page_state']['current_beings'].extend(test_beings)
        app_state['stats']['beings'] += len(test_beings)
        app_state['stats']['commands'] += 1

        # Broadcast update
        await broadcast_state_update({
            'type': 'test_data_created',
            'beings': test_beings,
            'stats': app_state['stats']
        })

        return JSONResponse({
            'success': True,
            'message': f'Created {len(test_beings)} test beings',
            'beings': test_beings
        })
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        })

@app.get("/api/session")
async def get_session_info():
    """Get session information"""
    return JSONResponse({
        'session_id': 'demo_session_123',
        'user_name': 'LuxDB Developer',
        'is_admin': True,
        'created_at': datetime.now().isoformat(),
        'last_active': datetime.now().isoformat(),
        'connected': True
    })

if __name__ == "__main__":
    print("📁 Workspace synchronization enabled")
    uvicorn.run(
        socket_app,
        host="0.0.0.0",
        port=3001,
        reload=False,  # Disable reload for better lifespan handling
        log_level="info"
    )