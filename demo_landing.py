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
from database.models.base import Soul, Being
from database.models.relationship import Relationship
from database.soul_repository import SoulRepository, BeingRepository
from services.message_similarity_service import MessageSimilarityService

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
    transports=['websocket', 'polling'],
    ping_timeout=60,
    ping_interval=25
)

@app.on_event("startup")
async def startup_event():
    print("🌟 FastAPI server started successfully!")
    print("📡 Socket.IO server initialized")

    # Initialize database connection and tables
    print("🗄️ Initializing database...")
    try:
        # Get database pool - this will initialize everything
        pool = await Postgre_db.get_db_pool()
        # Assign pool to db instance for compatibility
        db.pool = pool
        print("✅ Database connection established")
        print("✅ Database tables verified")

        # Load some sample data if needed
        souls = await Soul.load_all()
        beings = await Being.load_all()
        print(f"📊 Loaded {len(souls)} souls and {len(beings)} beings")

        # Check if we already have demo data (limit creation to prevent endless beings)
        demo_beings_count = 0
        for being in beings:
            # Count beings that look like demo entities
            if hasattr(being, 'alias') and being.alias == "sample_entity":
                demo_beings_count += 1
        
        # If no souls exist or we have very few demo beings, create some sample data
        if len(souls) == 0 or demo_beings_count < 5:
            print("📝 Creating limited sample data...")

            # Create or get sample soul/genotype
            sample_soul = None
            for soul in souls:
                if soul.alias == "sample_entity":
                    sample_soul = soul
                    break
            
            if not sample_soul:
                sample_genotype = {
                    "genesis": {
                        "name": "sample_entity",
                        "type": "entity",
                        "doc": "Sample entity for demo"
                    },
                    "attributes": {
                        "name": {"py_type": "str", "table_name": "_text"},
                        "energy": {"py_type": "float", "table_name": "_numeric"},
                        "active": {"py_type": "bool", "table_name": "_boolean"}
                    }
                }

                sample_soul = await Soul.create(sample_genotype, alias="sample_entity")
                print(f"✅ Created sample soul: {sample_soul.alias}")

            # Create only a few sample beings if we don't have enough (using limit parameter)
            beings_to_create = max(0, 3 - demo_beings_count)
            for i in range(beings_to_create):
                being = await Being.create(
                    sample_soul,
                    {
                        "name": f"Entity_{demo_beings_count + i + 1}",
                        "energy": float(50 + (demo_beings_count + i) * 10),
                        "active": True
                    },
                    limit=10  # Wykorzystanie parametru limit - maksymalnie 10 beings na soul
                )
                print(f"✅ Created sample being: {being.ulid}")
        else:
            print(f"ℹ️  Demo data already exists ({demo_beings_count} demo beings found), skipping creation")

    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        import traceback
        traceback.print_exc()

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
similarity_service = MessageSimilarityService()
print("🤖 Hybrid AI System initialized")
print("🔍 Message Similarity Service initialized")

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

def serialize_for_json(obj):
    """Helper function to serialize datetime objects"""
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    else:
        return str(obj)

@sio.event
async def request_graph_data(sid):
    """Endpoint do żądania aktualnych danych grafu"""
    try:
        print("📡 Otrzymano żądanie danych grafu")

        # Pobierz dane z bazy - dodaj souls do grafu
        souls = await Soul.load_all()
        
        # Try to load beings with better error handling
        beings_result = await Being.load_all()
        if isinstance(beings_result, dict) and not beings_result.get("success", False):
            print(f"❌ Failed to load beings: {beings_result.get('error', 'Unknown error')}")
            beings = []
        elif isinstance(beings_result, dict):
            beings = beings_result.get("beings", [])
        else:
            # beings_result is a list directly
            beings = beings_result if beings_result else []
            
        relationships = await Relationship.get_all()  # Stara tabela relationships

        # Pobierz nowe dedykowane relacje
        from database.models.relation import Relation
        relations = await Relation.load_all()

        print(f"🔍 Pobrano z bazy: {len(souls)} souls, {len(beings)} beings, {len(relationships)} relationships, {len(relations)} relations")
        print(f"🔍 Souls loaded: {souls is not None}")
        print(f"🔍 Beings loaded: {beings is not None} (count: {len(beings) if beings else 0})")
        print(f"🔍 First few beings: {[b.ulid[:8] + '...' if hasattr(b, 'ulid') else str(type(b)) for b in beings[:3]] if beings else 'No beings'}")

        # Przygotuj dane grafu - DODAJ souls i relations jako osobne kategorie
        graph_data = {
            'souls': [soul.to_dict() for soul in souls] if souls else [],  # NOWE: dodaj souls
            'beings': [being.to_dict() for being in beings],
            'relationships': [rel.to_dict() for rel in relationships],
            'relations': [rel.to_dict() for rel in relations]  # Nowe dedykowane relacje
        }

        print(f"✅ Przygotowano dane grafu: {len(beings)} beings, {len(relationships)} relationships, {len(relations)} relations")

        # Serialize all data to ensure JSON compatibility
        serialized_graph_data = serialize_for_json(graph_data)

        print(f"📤 Wysyłam dane do klienta {sid}: {len(serialized_graph_data.get('beings', []))} beings, {len(serialized_graph_data.get('relationships', []))} relationships, {len(serialized_graph_data.get('relations', []))} relations")

        await sio.emit('graph_data', serialized_graph_data, room=sid)

    except Exception as e:
        print(f"❌ Błąd podczas pobierania danych grafu: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

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

@app.post("/api/send_message")
async def send_message(message: dict):
    """Endpoint do wysyłania wiadomości do AI"""
    try:
        content = message.get("message", "")
        if not content:
            return {"error": "Brak treści wiadomości"}

        # Przetwórz wiadomość przez AI Brain
        response = await ai_system.process_message(content)

        return {
            "response": response.get("response", "Brak odpowiedzi"),
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
    except Exception as e:
        print(f"Error in send_message: {e}")
        return {"error": str(e)}

@app.post("/api/compare_messages")
async def compare_messages_similarity(request: dict):
    """Endpoint do porównywania podobieństwa wiadomości i tworzenia relacji"""
    try:
        soul_hash = request.get("soul_hash")
        threshold = request.get("threshold", 0.7)

        if not soul_hash:
            return {"error": "Brak soul_hash"}

        # Ustaw próg podobieństwa
        similarity_service.set_similarity_threshold(threshold)

        # Porównaj wiadomości i stwórz relacje
        result = await similarity_service.compare_messages_and_create_relations(soul_hash)

        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error in compare_messages_similarity: {e}")
        return {"error": str(e)}

@app.get("/api/similar_messages/{message_ulid}")
async def get_similar_messages(message_ulid: str, limit: int = 5):
    """Endpoint do pobierania wiadomości podobnych do danej"""
    try:
        similar = await similarity_service.get_similar_messages(message_ulid, limit)
        return {
            "status": "success",
            "similar_messages": similar,
            "count": len(similar)
        }
    except Exception as e:
        print(f"Error in get_similar_messages: {e}")
        return {"error": str(e)}

@app.post("/api/similarity/detect")
async def detect_similarity():
    """Wykrywa podobieństwa między wiadomościami i tworzy relacje"""
    try:
        result = await similarity_service.detect_and_create_relations()
        await sio.emit('graph_data_updated')  # Powiadom o aktualizacji
        return result
    except Exception as e:
        print(f"❌ Błąd podczas wykrywania podobieństw: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/relationships")
async def create_relationship(request: Request):
    """Tworzy nową relację między beings"""
    try:
        data = await request.json()
        source_ulid = data.get('source_ulid')
        target_ulid = data.get('target_ulid')
        relation_type = data.get('relation_type', 'connection')
        strength = data.get('strength', 1.0)
        metadata = data.get('metadata', {})

        if not source_ulid or not target_ulid:
            return {"success": False, "error": "source_ulid i target_ulid są wymagane"}

        from database.models.relationship import Relationship
        relationship = await Relationship.create(
            source_ulid=source_ulid,
            target_ulid=target_ulid,
            relation_type=relation_type,
            strength=strength,
            metadata=metadata
        )

        # Powiadom klientów o nowej relacji
        await sio.emit('graph_data_updated')

        return {
            "success": True,
            "relationship": relationship.to_dict(),
            "message": f"Utworzono relację {relation_type} między {source_ulid} a {target_ulid}"
        }

    except Exception as e:
        print(f"❌ Błąd podczas tworzenia relacji: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/relations")
async def create_relation(request: Request):
    """Tworzy nową dedykowaną relację"""
    try:
        data = await request.json()
        source_ulid = data.get('source_ulid')
        target_ulid = data.get('target_ulid')
        relation_type = data.get('relation_type', 'connection')
        strength = data.get('strength', 1.0)
        metadata = data.get('metadata', {})

        if not source_ulid or not target_ulid:
            return {"success": False, "error": "source_ulid i target_ulid są wymagane"}

        from database.models.relation import Relation
        relation = await Relation.create(
            source_ulid=source_ulid,
            target_ulid=target_ulid,
            relation_type=relation_type,
            strength=strength,
            metadata=metadata
        )

        # Powiadom klientów o nowej relacji
        await sio.emit('graph_data_updated')

        return {
            "success": True,
            "relation": relation.to_dict(),
            "message": f"Utworzono relację {relation_type} między {source_ulid} a {target_ulid}"
        }

    except Exception as e:
        print(f"❌ Błąd podczas tworzenia relacji: {e}")
        return {"success": False, "error": str(e)}


@app.get("/")
async def main_page():
    """Główna strona z interfejsem LuxDB"""
    print("🏠 Serving main page...")
    return FileResponse("static/index.html")

@app.get("/graph")
async def graph_page():
    """Strona z grafem"""
    return FileResponse('static/graph.html')

@app.get("/admin")
async def admin_page():
    """Panel administracyjny bazy danych"""
    return FileResponse('static/database-admin.html')

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

@app.get("/api/db-status")
async def database_status():
    """Database status endpoint"""
    try:
        from database.models.base import Soul, Being
        souls = await Soul.load_all()
        beings = await Being.load_all()

        async with db.pool.acquire() as conn:
            relations = await conn.fetch("SELECT COUNT(*) as count FROM relationships")
            relations_count = relations[0]['count'] if relations else 0
            
            # Dodaj licznik dla nowych relacji
            from database.models.relation import Relation
            new_relations = await conn.fetch("SELECT COUNT(*) as count FROM relations")
            new_relations_count = new_relations[0]['count'] if new_relations else 0

        return {
            "status": "connected",
            "souls_count": len(souls),
            "beings_count": len(beings),
            "relationships_count": relations_count,
            "relations_count": new_relations_count, # Nowy licznik
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
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

@app.post("/admin/cleanup_demo_beings")
async def cleanup_demo_beings():
    """Czyści nadmiar demo beings, zostawia tylko pierwsze 5"""
    try:
        beings = await Being.load_all()
        demo_beings = [b for b in beings if hasattr(b, 'alias') and b.alias == "sample_entity"]
        
        if len(demo_beings) <= 5:
            return {"message": f"Only {len(demo_beings)} demo beings found, no cleanup needed"}
        
        # Tu można dodać logikę usuwania nadmiaru beings
        # Na razie tylko informujemy o ilości
        return {
            "message": f"Found {len(demo_beings)} demo beings. Cleanup logic would remove {len(demo_beings) - 5} beings",
            "total_beings": len(beings),
            "demo_beings": len(demo_beings)
        }
    except Exception as e:
        return {"error": str(e)}

@app.post("/test/create_sample_relations")
async def create_sample_relations():
    """Stwórz przykładowe relacje między beings"""
    try:
        beings = await Being.load_all()
        if len(beings) < 2:
            return {"error": "Potrzeba co najmniej 2 beings"}

        from database.models.relationship import Relationship
        from database.models.relation import Relation

        # Stwórz 3 przykładowe relacje (stary typ)
        rel1 = await Relationship.create(
            source_ulid=beings[0].ulid,
            target_ulid=beings[1].ulid,
            relation_type="similarity",
            strength=0.9
        )

        if len(beings) >= 3:
            rel2 = await Relationship.create(
                source_ulid=beings[1].ulid,
                target_ulid=beings[2].ulid,
                relation_type="connection",
                strength=0.7
            )

            rel3 = await Relationship.create(
                source_ulid=beings[0].ulid,
                target_ulid=beings[2].ulid,
                relation_type="dependency",
                strength=0.5
            )

        # Stwórz 3 przykładowe relacje (nowy typ)
        rel4 = await Relation.create(
            source_ulid=beings[0].ulid,
            target_ulid=beings[1].ulid,
            relation_type="interacts_with",
            strength=0.8
        )

        if len(beings) >= 3:
            rel5 = await Relation.create(
                source_ulid=beings[1].ulid,
                target_ulid=beings[2].ulid,
                relation_type="supports",
                strength=0.6
            )

            rel6 = await Relation.create(
                source_ulid=beings[0].ulid,
                target_ulid=beings[2].ulid,
                relation_type="depends_on",
                strength=0.4
            )

        # Powiadom klientów
        await sio.emit('graph_data_updated')

        return {"success": True, "message": "Utworzono przykładowe relacje"}

    except Exception as e:
        print(f"❌ Błąd podczas tworzenia relacji: {e}")
        return {"success": False, "error": str(e)}

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
        log_level="info",
        access_log=False
    )