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

# Import AI system
from ai.hybrid_ai_system import HybridAISystem

# FastAPI app
app = FastAPI(title="LuxDB MVP", version="2.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO server z poprawną konfiguracją CORS
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
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

# Initialize AI System
ai_system = HybridAISystem()

# In-memory storage for demo (in production, use proper database)
beings_data = [
    {
        "soul_uid": "soul_001",
        "_soul": {
            "genesis": {
                "name": "AI_Brain",
                "type": "intelligence"
            }
        }
    },
    {
        "soul_uid": "soul_002", 
        "_soul": {
            "genesis": {
                "name": "Data_Processor",
                "type": "processor"
            }
        }
    },
    {
        "soul_uid": "soul_003",
        "_soul": {
            "genesis": {
                "name": "Communication_Hub",
                "type": "communication"
            }
        }
    }
]

relationships_data = [
    {
        "source_soul": "soul_001",
        "target_soul": "soul_002",
        "genesis": {"type": "processes"}
    },
    {
        "source_soul": "soul_002", 
        "target_soul": "soul_003",
        "genesis": {"type": "sends_to"}
    }
]

def create_being_from_intent(intent_analysis, ai_response):
    """Create a new being based on AI analysis"""
    intent = intent_analysis.get("intent", "unknown")
    entities = intent_analysis.get("entities", [])

    # Generate unique ID
    new_id = f"soul_{len(beings_data) + 1:03d}"

    # Determine being type and name based on intent
    if intent == "create":
        being_type = "creation"
        name = f"Created_Entity_{datetime.now().strftime('%H%M%S')}"
    elif intent == "execute":
        being_type = "execution"
        name = f"Executed_Task_{datetime.now().strftime('%H%M%S')}"
    elif intent == "retrieve":
        being_type = "query"
        name = f"Query_Result_{datetime.now().strftime('%H%M%S')}"
    else:
        being_type = "interaction"
        name = f"User_Intent_{datetime.now().strftime('%H%M%S')}"

    # Extract entity names if available
    for entity in entities:
        if entity.get("type") in ["gene", "file"]:
            name = f"{entity['value'].title()}_Being"
            break

    new_being = {
        "soul_uid": new_id,
        "_soul": {
            "genesis": {
                "name": name,
                "type": being_type,
                "created_from_intent": True,
                "original_intent": intent_analysis.get("raw_input", ""),
                "ai_response": ai_response
            }
        }
    }

    return new_being

def create_relationship_to_ai_brain(new_being_id, intent):
    """Create relationship between new being and AI Brain"""
    relationship_type = "analyzed_by" if intent in ["analyze", "process"] else "created_by"

    return {
        "source_soul": "soul_001",  # AI Brain
        "target_soul": new_being_id,
        "genesis": {
            "type": relationship_type,
            "created_at": datetime.now().isoformat(),
            "automated": True
        }
    }

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
    """Obsługa żądania danych grafu - pobiera rzeczywiste dane z systemu"""
    print(f"📊 Graph data requested by client: {sid}")

    try:
        # Import system classes
        from database.models.base import Soul, Being

        # Pobierz wszystkie dusze
        souls = await Soul.load_all()
        beings = await Being.load_all()

        # 1. Tworzymy genotyp relacji
        relationship_genotype = {
            "genesis": {
                "name": "basic_relationship",
                "type": "relation",
                "doc": "Podstawowa relacja między bytami"
            },
            "attributes": {
                "source_uid": {"py_type": "str"},
                "target_uid": {"py_type": "str"},
                "relation_type": {"py_type": "str"},
                "strength": {"py_type": "float"},
                "vector_1536": {"py_type": "List[float]"},
            }
        }

        # 2. Tworzymy duszę relacji
        relationship_soul = await Soul.create(relationship_genotype, alias="basic_relation")

        # 3. Tworzymy byt relacji
        relationship_being = await Being.create(
            relationship_soul, 
            {
                "source_uid": beings[0].ulid,
                "target_uid": beings[1].ulid,
                "relation_type": "communication",
                "strength": 0.8,
                "metadata": {"timestamp": "2025-01-29", "context": "system_interaction"}
            },
            limit=None
        )

        # Formatuj dane dla grafu
        graph_data = {
            'beings': [],
            'relationships': []  # Na razie puste - dodamy gdy stworzymy prawdziwe relacje
        }

        # Dodaj dusze jako byty
        for soul in souls:
            if soul:
                graph_data['beings'].append({
                    'soul_uid': soul.soul_hash,
                    '_soul': {
                        'genesis': soul.genotype.get('genesis', {}),
                        'alias': soul.alias
                    }
                })

        # Dodaj rzeczywiste byty
        for being in beings:
            if being:
                graph_data['beings'].append({
                    'soul_uid': f"being_{being.ulid}",
                    '_soul': {
                        'genesis': being.genotype.get('genesis', {}),
                        'ulid': being.ulid
                    }
                })

        # Jeśli nie ma danych, użyj mock data z relacjami
        if not graph_data['beings']:
            graph_data = {
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

        await sio.emit('graph_data', graph_data, room=sid)
        print(f"✅ Real graph data sent to client {sid}: {len(graph_data['beings'])} beings")

    except Exception as e:
        print(f"❌ Error loading graph data: {e}")
        # Fallback do mock data
        fallback_data = {
            'beings': [
                {'soul_uid': 'error', '_soul': {'genesis': {'name': 'Błąd ładowania danych', 'type': 'error'}}}
            ],
            'relationships': []
        }
        await sio.emit('graph_data', fallback_data, room=sid)

@sio.event
async def send_intention(sid, data):
    """Handle user intention with AI processing"""
    intention = data.get('intention', '')
    print(f"📥 Received intention from {sid}: {intention}")

    try:
        # Process intention with AI system
        print(f"🤖 Processing intention with AI: {intention}")
        ai_result = await ai_system.process_request(intention, use_openai=False)

        # Extract key information
        intent_analysis = ai_result.get("final_result", {}).get("intent_analysis", {})
        intent = intent_analysis.get("intent", "unknown")
        confidence = intent_analysis.get("confidence", 0.0)

        # Create response message
        if ai_result.get("final_result", {}).get("results"):
            # If AI executed functions
            executed_functions = ai_result["final_result"]["results"]
            success_count = sum(1 for r in executed_functions if r.get("success"))
            ai_response = f"Executed {success_count} functions successfully"
        else:
            ai_response = f"Recognized intent: {intent} (confidence: {confidence:.1f})"

        # Create new being from this intention
        new_being = create_being_from_intent(intent_analysis, ai_response)
        beings_data.append(new_being)

        # Create relationship to AI Brain
        new_relationship = create_relationship_to_ai_brain(new_being["soul_uid"], intent)
        relationships_data.append(new_relationship)

        print(f"✅ Created new being: {new_being['_soul']['genesis']['name']}")

        # Prepare response
        response = {
            "status": "processed",
            "intention": intention,
            "timestamp": datetime.now().isoformat(),
            "analysis": {
                "intent": intent,
                "confidence": confidence,
                "ai_response": ai_response,
                "new_being_created": True,
                "being_name": new_being['_soul']['genesis']['name']
            },
            "ai_result": ai_result
        }

        # Send response to user
        await sio.emit('intention_response', response, room=sid)

        # Broadcast updated graph data to all clients
        graph_data = {
            "beings": beings_data,
            "relationships": relationships_data
        }
        await sio.emit('graph_data', graph_data)

        print(f"📊 Graph updated with new being and relationship")

    except Exception as e:
        print(f"❌ Error processing intention: {e}")
        error_response = {
            "status": "error",
            "intention": intention,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "analysis": "Failed to process intention"
        }
        await sio.emit('intention_response', error_response, room=sid)

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