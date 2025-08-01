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
        return obj

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

        # Pobierz relacje podobieństwa - szukaj souls z aliasem zawierającym 'relation'
        relation_souls = [s for s in souls if s.alias and 'relation' in s.alias.lower()]
        print(f"🔗 Znaleziono {len(relation_souls)} souls relacji")
        for rs in relation_souls:
            print(f"   - Soul relacji: {rs.alias} (hash: {rs.soul_hash})")

        for rel_soul in relation_souls:
            # Pobierz beings (relacje) dla tej soul
            relation_beings = await Being.load_all_by_soul_hash(rel_soul.soul_hash)
            print(f"📋 Soul {rel_soul.alias} ma {len(relation_beings)} beings")
            
            if not relation_beings:
                print(f"⚠️ Brak beings dla soul relacji {rel_soul.alias}")
                continue

            for rel_being in relation_beings:
                # Pobierz wszystkie atrybuty being'a i wyprintuj je dla debugowania
                all_attrs = {}
                
                # Sprawdź wszystkie tabele atrybutów
                from database.postgre_db import Postgre_db
                db_pool = await Postgre_db.get_db_pool()
                
                if db_pool:
                    async with db_pool.acquire() as conn:
                        # Sprawdź tabele z atrybutami - używamy jsonb zamiast json
                        for table_suffix in ['_text', '_int', '_float', '_boolean', '_jsonb']:
                            table_name = f"attr{table_suffix}"
                            try:
                                query = f"""
                                    SELECT key, value 
                                    FROM {table_name} 
                                    WHERE being_ulid = $1
                                """
                                rows = await conn.fetch(query, rel_being.ulid)
                                for row in rows:
                                    all_attrs[row['key']] = row['value']
                            except Exception as e:
                                print(f"⚠️ Błąd czytania tabeli {table_name}: {e}")
                
                print(f"🔍 Being {rel_being.ulid} atrybuty: {all_attrs}")
                
                # Również spróbuj metody get_attributes (teraz async)
                being_attrs = await rel_being.get_attributes()
                print(f"🔍 Being {rel_being.ulid} przez get_attributes(): {being_attrs}")
                
                # Użyj atrybutów z bezpośredniego zapytania lub z metody
                final_attrs = {**being_attrs, **all_attrs}  # all_attrs ma priorytet
                
                print(f"🔍 Final attrs dla {rel_being.ulid}: {final_attrs}")
                
                source_uid = final_attrs.get('source_uid')
                target_uid = final_attrs.get('target_uid')

                if source_uid and target_uid:
                    # Znajdź beings które są źródłem i celem
                    source_being = next((b for b in all_beings if b.ulid == source_uid), None)
                    target_being = next((b for b in all_beings if b.ulid == target_uid), None)

                    if source_being and target_being:
                        relationship_data = {
                            "ulid": rel_being.ulid,
                            "source_soul": source_being.soul_hash,
                            "target_soul": target_being.soul_hash,
                            "source_uid": source_uid, 
                            "target_uid": target_uid,
                            "relation_type": final_attrs.get('relation_type', 'similarity'),
                            "strength": float(final_attrs.get('strength', 0.7)),
                            "metadata": serialize_for_json(final_attrs.get('metadata', {})),
                            "genesis": {
                                "type": rel_soul.genotype.get("genesis", {}).get("type", "relation"),
                                "name": rel_soul.alias
                            }
                        }
                        graph_data["relationships"].append(relationship_data)
                        print(f"✅ Dodano relację: {source_uid} -> {target_uid} ({final_attrs.get('relation_type', 'similarity')})")
                    else:
                        print(f"⚠️ Nie znaleziono bytów dla relacji: {source_uid} -> {target_uid}")
                        if not source_being:
                            print(f"   Brak source being: {source_uid}")
                        if not target_being:
                            print(f"   Brak target being: {target_uid}")
                else:
                    print(f"⚠️ Being {rel_being.ulid} nie ma source_uid/target_uid")

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