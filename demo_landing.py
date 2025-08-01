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
    transports=['websocket', 'polling']
)

@app.on_event("startup")
async def startup_event():
    print("🌟 FastAPI server started successfully!")
    print("📡 Socket.IO server initialized")
    
    # Initialize database connection and tables
    print("🗄️ Initializing database...")
    try:
        await db.initialize()
        print("✅ Database connection established")
        
        # Get the database pool and ensure tables exist
        pool = await Postgre_db.get_db_pool()
        print("✅ Database tables verified")
        
        # Load some sample data if needed
        souls = await Soul.load_all()
        beings = await Being.load_all()
        print(f"📊 Loaded {len(souls)} souls and {len(beings)} beings")
        
        # If no data exists, create some sample beings
        if len(souls) == 0:
            print("📝 Creating sample data...")
            
            # Create sample soul/genotype
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
            
            # Create sample beings
            for i in range(3):
                being = await Being.create(
                    sample_soul,
                    {
                        "name": f"Entity_{i+1}",
                        "energy": float(50 + i * 10),
                        "active": True
                    }
                )
                print(f"✅ Created sample being: {being.ulid}")
        
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

        # Pobierz wszystkie souls
        souls = await Soul.load_all()
        print(f"📊 Znaleziono {len(souls)} souls")

        # Pobierz wszystkie beings
        all_beings = await Being.load_all()
        print(f"📊 Znaleziono {len(all_beings)} beings")

        # Przygotuj dane dla frontendu
        graph_data = {
            "beings": [],
            "relationships": []
        }

        # Dodaj beings do grafu
        for being in all_beings:
            # Znajdź odpowiadającą soul
            soul = next((s for s in souls if s.soul_hash == being.soul_hash), None)

            being_data = {
                "ulid": being.ulid,
                "soul_uid": being.soul_hash,
                "_soul": {
                    "genesis": soul.genotype.get("genesis", {}) if soul else {},
                    "alias": soul.alias if soul else None
                },
                "created_at": being.created_at.isoformat() if being.created_at else None,
                "attributes": serialize_for_json(await being.get_attributes())
            }
            graph_data["beings"].append(being_data)

        # Pobierz relacje bezpośrednio z bazy danych
        try:
            async with db.pool.acquire() as conn:
                relationships_rows = await conn.fetch("SELECT * FROM relationships ORDER BY created_at DESC")
                print(f"🔗 Znaleziono {len(relationships_rows)} relacji w tabeli relationships")

                for row in relationships_rows:
                    relationship_data = {
                        'id': row['id'],
                        'source_uid': row['source_ulid'],  # Changed to match frontend expectations
                        'target_uid': row['target_ulid'],  # Changed to match frontend expectations
                        'source': row['source_ulid'],
                        'target': row['target_ulid'],
                        'relation_type': row['relation_type'],
                        'type': row['relation_type'],
                        'strength': float(row['strength']) if row['strength'] else 1.0,
                        'metadata': dict(row['metadata']) if row['metadata'] else {}
                    }
                    graph_data["relationships"].append(relationship_data)
                    print(f"🔗 Relacja: {row['source_ulid']} → {row['target_ulid']} ({row['relation_type']})")

                # Jeśli nie ma relacji, stwórz przykładowe
                if len(relationships_rows) == 0 and len(all_beings) >= 2:
                    print("📝 Tworzę przykładowe relacje między beings...")
                    beings_list = list(all_beings)
                    
                    # Stwórz relacje bezpośrednio w bazie
                    await conn.execute("""
                        INSERT INTO relationships (source_ulid, target_ulid, relation_type, strength, metadata)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (source_ulid, target_ulid, relation_type) DO NOTHING
                    """, beings_list[0].ulid, beings_list[1].ulid, "connection", 0.8, 
                         {"auto_created": True, "reason": "demo"})
                    
                    if len(beings_list) >= 3:
                        await conn.execute("""
                            INSERT INTO relationships (source_ulid, target_ulid, relation_type, strength, metadata)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (source_ulid, target_ulid, relation_type) DO NOTHING
                        """, beings_list[1].ulid, beings_list[2].ulid, "similarity", 0.7,
                             {"auto_created": True, "reason": "demo"})

                    # Przeładuj relacje
                    relationships_rows = await conn.fetch("SELECT * FROM relationships ORDER BY created_at DESC")
                    graph_data["relationships"] = []  # Clear and reload
                    
                    for row in relationships_rows:
                        relationship_data = {
                            'id': row['id'],
                            'source_uid': row['source_ulid'],
                            'target_uid': row['target_ulid'], 
                            'source': row['source_ulid'],
                            'target': row['target_ulid'],
                            'relation_type': row['relation_type'],
                            'type': row['relation_type'],
                            'strength': float(row['strength']) if row['strength'] else 1.0,
                            'metadata': dict(row['metadata']) if row['metadata'] else {}
                        }
                        graph_data["relationships"].append(relationship_data)

                    print(f"✅ Utworzono {len(relationships_rows)} przykładowych relacji")

        except Exception as e:
            print(f"❌ Błąd podczas ładowania relacji: {e}")
            import traceback
            traceback.print_exc()
            # Kontynuuj bez relacji

        print(f"✅ Przygotowano dane grafu: {len(graph_data['beings'])} beings, {len(graph_data['relationships'])} relationships")

        # Serialize all data to ensure JSON compatibility
        serialized_graph_data = serialize_for_json(graph_data)

        print(f"📤 Wysyłam dane do klienta {sid}: {len(serialized_graph_data.get('beings', []))} beings, {len(serialized_graph_data.get('relationships', []))} relationships")

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

@app.post("/test/create_sample_relations")
async def create_sample_relations():
    """Stwórz przykładowe relacje między beings"""
    try:
        beings = await Being.load_all()
        if len(beings) < 2:
            return {"error": "Potrzeba co najmniej 2 beings"}

        from database.models.relationship import Relationship

        # Stwórz 3 przykładowe relacje
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
        log_level="debug",
        access_log=True
    )