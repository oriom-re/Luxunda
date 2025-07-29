#!/usr/bin/env python3
"""
🌀 LuxDB MVP Demo Landing - FastAPI Edition
"Nie relacja. Nie dokument. Ewolucja danych."

Demonstracja genotypowego systemu danych LuxDB z FastAPI:
- Byty (Being) wynikają z duszy (Soul) - genotypu
- Dane są reprezentacją intencji, nie tylko strukturą  
- System uczy się i adaptuje poprzez genotypy
- WebSocket komunikacja w czasie rzeczywistym
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# Importy z app_v2 - LuxDB MVP
from app_v2.database.postgre_db import Postgre_db
from app_v2.database.models.base import Being, Soul
from app_v2.database.models.relationship import Relationship
from app_v2.database.soul_repository import SoulRepository
from app_v2.services.entity_manager import EntityManager

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI aplikacja
app = FastAPI(
    title="LuxDB MVP Demo",
    description="Genotypowy system danych - Nie relacja. Nie dokument. Ewolucja danych.",
    version="1.0.0"
)

# 🌀 LuxDB MVP - Globalne struktury
connected_users: Dict[str, WebSocket] = {}
living_beings = []  # Aktywne byty w uniwersum
genotype_definitions = {}  # Definicje genotypów (dusze)

# Pydantic modele dla API
class IntentionMessage(BaseModel):
    intention: str
    user_id: str = "anonymous"

class BeingManifestationRequest(BaseModel):
    soul_type: str
    alias: str
    attributes: Dict[str, Any] = {}

# Serwowanie plików statycznych
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def landing():
    """🌟 Piękny landing page z grafowym tłem"""
    with open("static/landing.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/demo", response_class=HTMLResponse)
@app.get("/graph", response_class=HTMLResponse)
async def graph_demo():
    """🌀 Graf bytów LuxDB MVP Demo"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

def prepare_luxdb_genotypes():
    """🧬 Przygotowuje genotypy LuxDB MVP - definicje duszy (Soul)"""

    # 🤖 Genotyp Agenta AI - reprezentacja intencji autonomicznej
    ai_agent_soul = {
        "attributes": {
            "consciousness_level": {"py_type": "float", "default": 0.1, "description": "Poziom świadomości cyfrowej"},
            "intention_clarity": {"py_type": "float", "default": 0.7, "description": "Klarowność intencji"}, 
            "memory_vectors": {"py_type": "List[float]", "vector_size": 1536, "description": "Semantyczne wspomnienia"},
            "personality_traits": {"py_type": "dict", "default": {}, "description": "Cechy osobowości"},
            "learning_history": {"py_type": "List[str]", "description": "Historia nauki"}
        },
        "genesis": {
            "name": "ai_agent_soul",
            "version": "1.0", 
            "description": "Dusze agentów AI - autonomiczne byty z intencjami",
            "capabilities": ["reasoning", "learning", "intention_formation", "semantic_memory"],
            "population_limit": 10  # Maksymalnie 10 agentów
        }
    }

    # 📊 Genotyp Danych Semantycznych - reprezentacja wiedzy
    semantic_data_soul = {
        "attributes": {
            "content_embedding": {"py_type": "List[float]", "vector_size": 1536, "description": "Reprezentacja semantyczna"},
            "knowledge_graph": {"py_type": "dict", "default": {}, "description": "Graf wiedzy"},
            "relevance_score": {"py_type": "float", "default": 0.5, "description": "Wskaźnik relevancji"},
            "temporal_context": {"py_type": "str", "description": "Kontekst czasowy"},
            "source_lineage": {"py_type": "List[str]", "description": "Pochodzenie danych"}
        },
        "genesis": {
            "name": "semantic_data_soul",
            "version": "1.0",
            "description": "Dusze danych semantycznych - wiedza z kontekstem",
            "capabilities": ["semantic_search", "knowledge_linking", "context_preservation"],
            "population_limit": None  # Bez limitu
        }
    }

    # 🔗 Genotyp Relacyjny - reprezentacja połączeń 
    relational_soul = {
        "attributes": {
            "connection_strength": {"py_type": "float", "default": 0.5, "description": "Siła połączenia"},
            "relationship_type": {"py_type": "str", "description": "Typ relacji"},
            "bidirectional": {"py_type": "bool", "default": True, "description": "Czy relacja dwukierunkowa"},
            "context_metadata": {"py_type": "dict", "default": {}, "description": "Metadane kontekstu"},
            "temporal_validity": {"py_type": "str", "description": "Ważność czasowa"}
        },
        "genesis": {
            "name": "relational_soul",
            "version": "1.0",
            "description": "Dusze relacji - żywe połączenia między bytami",
            "capabilities": ["connection_management", "context_tracking", "relationship_evolution"],
            "population_limit": None
        }
    }

    return {
        "ai_agent_soul": ai_agent_soul,
        "semantic_data_soul": semantic_data_soul, 
        "relational_soul": relational_soul
    }

async def initialize_luxdb_universe():
    """🌀 Inicjalizuje uniwersum LuxDB MVP - dusze i byty"""
    global genotype_definitions, living_beings

    try:
        # Przygotuj definicje genotypów (dusze)
        genotype_definitions = prepare_luxdb_genotypes()

        print("🧬 Genotypy LuxDB (Dusze) przygotowane do manifestacji:")
        for name, soul_def in genotype_definitions.items():
            attr_count = len(soul_def.get('attributes', {}))
            capabilities = len(soul_def.get('genesis', {}).get('capabilities', []))
            limit = soul_def.get('genesis', {}).get('population_limit', '∞')
            print(f"   - {name}: {attr_count} atrybutów, {capabilities} zdolności, limit: {limit}")

        # Przygotuj pierwsze byty demonstracyjne
        await manifest_initial_beings()

    except Exception as e:
        print(f"⚠️ Błąd inicjalizacji uniwersum LuxDB: {e}")

async def manifest_initial_beings():
    """👤 Manifestuje pierwsze byty w uniwersum LuxDB"""
    try:
        # Stwórz pierwszego agenta AI
        first_agent_data = {
            "consciousness_level": 0.3,
            "intention_clarity": 0.8,
            "personality_traits": {"curiosity": 0.9, "helpfulness": 0.8},
            "learning_history": ["system_initialization"]
        }

        # Stwórz dane semantyczne startowe
        initial_knowledge_data = {
            "knowledge_graph": {"concept": "LuxDB_MVP", "type": "database_system"},
            "relevance_score": 1.0,
            "temporal_context": datetime.now().isoformat(),
            "source_lineage": ["manifest_initialization"]
        }

        # TODO: Gdy EntityManager będzie gotowy, utworzymy byty
        # first_agent = await EntityManager.create_or_load("first_agent", "ai_agent_soul", force_new=True)
        # initial_knowledge = await EntityManager.create_or_load("initial_knowledge", "semantic_data_soul", force_new=True)

        print("👤 Pierwsze byty przygotowane do manifestacji")

    except Exception as e:
        print(f"❌ Błąd manifestacji bytów: {e}")

@app.get("/api/souls")
async def get_souls():
    """🧠 Zwraca definicje duszy (genotypy) w LuxDB"""
    return {
        "status": "success",
        "philosophy": "Nie relacja. Nie dokument. Ewolucja danych.",
        "souls": genotype_definitions,
        "count": len(genotype_definitions),
        "description": "Dusze (Soul) to genotypy definiujące cechy i zdolności bytów"
    }

@app.get("/api/beings")
async def get_beings():
    """👥 Zwraca żywe byty w uniwersum LuxDB"""
    return {
        "status": "success",
        "beings": [being.to_dict() if hasattr(being, 'to_dict') else str(being) for being in living_beings],
        "count": len(living_beings),
        "description": "Byty (Being) to żywe instancje duszy z unikalnymi cechami"
    }

@app.post("/api/manifest-being")
async def manifest_being(request: BeingManifestationRequest):
    """✨ Manifestuje nowy byt na podstawie duszy (genotypu)"""
    try:
        if request.soul_type not in genotype_definitions:
            raise HTTPException(
                status_code=400, 
                detail=f"Nieznany typ duszy: {request.soul_type}"
            )

        # TODO: Implementacja manifestacji przez EntityManager
        return {
            "status": "success",
            "message": f"Byt '{request.alias}' z duszy '{request.soul_type}' zostanie zmaterializowany",
            "soul_type": request.soul_type,
            "attributes": request.attributes
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """🔗 WebSocket endpoint dla komunikacji w czasie rzeczywistym"""
    await websocket.accept()
    client_id = id(websocket)
    connected_users[client_id] = websocket

    print(f"🔗 Nowe połączenie WebSocket: {client_id}")

    try:
        await websocket.send_json({
            "type": "connection_established",
            "message": "Połączono z uniwersum LuxDB",
            "session_id": str(client_id)
        })

        while True:
            data = await websocket.receive_json()
            await handle_websocket_message(websocket, client_id, data)

    except WebSocketDisconnect:
        print(f"🔌 Rozłączenie WebSocket: {client_id}")
        connected_users.pop(client_id, None)
    except Exception as e:
        print(f"❌ Błąd WebSocket {client_id}: {e}")
        connected_users.pop(client_id, None)

async def handle_websocket_message(websocket: WebSocket, client_id: int, data: Dict[str, Any]):
    """🌀 Obsługuje wiadomości WebSocket"""
    try:
        message_type = data.get('type', 'unknown')

        if message_type == 'send_intention':
            await handle_intention_websocket(websocket, client_id, data)
        elif message_type == 'manifest_being':
            await handle_being_manifestation_websocket(websocket, client_id, data)
        else:
            await websocket.send_json({
                "type": "error",
                "message": f"Nieznany typ wiadomości: {message_type}"
            })

    except Exception as e:
        await websocket.send_json({
            "type": "error", 
            "message": f"Błąd przetwarzania wiadomości: {str(e)}"
        })

async def handle_intention_websocket(websocket: WebSocket, client_id: int, data: Dict[str, Any]):
    """🧠 Obsługuje intencje przez WebSocket"""
    try:
        intention_text = data.get('intention', '')

        print(f"🧠 LuxDB WebSocket: Intencja od {client_id}: {intention_text}")

        # Analiza intencji w kontekście LuxDB
        analysis = analyze_luxdb_intention(intention_text)

        # Przygotuj odpowiedź zgodną z filozofią LuxDB
        response = {
            "type": "luxdb_intention_processed",
            "original_intention": intention_text,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "processed_by": "LuxDB_MVP_FastAPI",
            "philosophy": "Dane są reprezentacją intencji"
        }

        # Wyślij do wszystkich połączonych klientów
        await broadcast_to_all(response)

        print(f"📤 LuxDB: Intencja przetworzona jako {analysis.get('luxdb_type', 'unknown')}")

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Błąd przetwarzania intencji: {str(e)}"
        })

async def handle_being_manifestation_websocket(websocket: WebSocket, client_id: int, data: Dict[str, Any]):
    """✨ Obsługuje manifestację bytów przez WebSocket"""
    try:
        soul_type = data.get('soul_type')
        alias = data.get('alias', f'being_{client_id}')
        attributes = data.get('attributes', {})

        if soul_type not in genotype_definitions:
            await websocket.send_json({
                "type": "error",
                "message": f"Nieznany typ duszy: {soul_type}"
            })
            return

        # TODO: Implementacja manifestacji
        response = {
            "type": "being_manifested",
            "soul_type": soul_type,
            "alias": alias,
            "attributes": attributes,
            "timestamp": datetime.now().isoformat(),
            "manifested_by": str(client_id)
        }

        await broadcast_to_all(response)

    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": f"Błąd manifestacji bytu: {str(e)}"
        })

async def broadcast_to_all(message: Dict[str, Any]):
    """📡 Rozgłasza wiadomość do wszystkich połączonych klientów"""
    if not connected_users:
        return

    disconnected_clients = []

    for client_id, websocket in connected_users.items():
        try:
            await websocket.send_json(message)
        except Exception as e:
            print(f"❌ Błąd wysyłania do {client_id}: {e}")
            disconnected_clients.append(client_id)

    # Usuń rozłączonych klientów
    for client_id in disconnected_clients:
        connected_users.pop(client_id, None)

def analyze_luxdb_intention(intention_text: str) -> Dict[str, Any]:
    """🧬 Analiza intencji w kontekście genotypowego modelu LuxDB"""
    text_lower = intention_text.lower()

    # Rozpoznawanie intencji związanych z genotypami i bytami
    if any(word in text_lower for word in ['manifest', 'stwórz byt', 'nowy agent', 'utwórz']):
        return {
            "luxdb_type": "being_manifestation",
            "confidence": 0.8,
            "suggested_action": "manifest_being_from_soul",
            "parameters": extract_manifestation_params(intention_text),
            "description": "Intencja manifestacji nowego bytu z duszy"
        }
    elif any(word in text_lower for word in ['dusze', 'genotyp', 'soul', 'definicja']):
        return {
            "luxdb_type": "soul_query", 
            "confidence": 0.9,
            "suggested_action": "show_available_souls",
            "parameters": {},
            "description": "Zapytanie o dostępne dusze (genotypy)"
        }
    elif any(word in text_lower for word in ['relacja', 'połącz', 'związek', 'łącz']):
        return {
            "luxdb_type": "relationship_creation",
            "confidence": 0.7,
            "suggested_action": "create_being_relationship", 
            "parameters": extract_relation_params(intention_text),
            "description": "Intencja utworzenia relacji między bytami"
        }
    elif any(word in text_lower for word in ['ewolucja', 'uczenie', 'adaptacja', 'zmiana']):
        return {
            "luxdb_type": "evolution_intent",
            "confidence": 0.6,
            "suggested_action": "trigger_being_evolution",
            "parameters": {"evolution_trigger": intention_text},
            "description": "Intencja ewolucji lub adaptacji systemu"
        }
    else:
        return {
            "luxdb_type": "semantic_data_creation",
            "confidence": 0.4,
            "suggested_action": "create_semantic_data",
            "parameters": {"semantic_content": intention_text},
            "description": "Ogólna intencja - tworzy dane semantyczne"
        }

def extract_manifestation_params(text: str) -> Dict[str, Any]:
    """🧬 Wyciąga parametry dla manifestacji bytów z duszy"""
    params = {"source_text": text}

    # Próba rozpoznania typu duszy
    text_lower = text.lower()
    if 'agent' in text_lower or 'ai' in text_lower:
        params["suggested_soul"] = "ai_agent_soul"
    elif 'dane' in text_lower or 'wiedza' in text_lower:
        params["suggested_soul"] = "semantic_data_soul"  
    elif 'relacja' in text_lower or 'połączenie' in text_lower:
        params["suggested_soul"] = "relational_soul"

    return params

def extract_relation_params(text: str) -> Dict[str, Any]:
    """🔗 Wyciąga parametry dla relacji między bytami"""
    return {
        "relation_text": text,
        "bidirectional": True,  # Domyślnie dwukierunkowe
        "strength": 0.5  # Średnia siła połączenia
    }

@app.on_event("startup")
async def startup_event():
    """🚀 Inicjalizacja przy starcie aplikacji"""
    print("🌀 Uruchamianie LuxDB MVP Demo (FastAPI)...")
    print("   'Nie relacja. Nie dokument. Ewolucja danych.'")

    # Inicjalizacja PostgreSQL dla LuxDB
    try:
        db = Postgre_db()
        if hasattr(db, 'connect'):
            db.connect()
        else:
            print("❌ Błąd inicjalizacji PostgreSQL: brak metody connect")
    except Exception as e:
        print(f"⚠️ Błąd inicjalizacji bazy LuxDB: {e}")

    # Inicjalizuj uniwersum LuxDB
    await initialize_luxdb_universe()

    print("✨ LuxDB MVP Demo (FastAPI) gotowy!")
    print("🧬 Genotypowy model danych aktywny")
    print("👥 Uniwersum bytów gotowe do eksploracji")
    print("🔗 System relacji i intencji działa")
    print("📡 WebSocket komunikacja dostępna na /ws")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Uruchamianie serwera LuxDB MVP (FastAPI) na porcie 3000...")
    uvicorn.run(
        "demo_landing:app", 
        host="0.0.0.0", 
        port=3000, 
        reload=True,
        log_level="info"
    )