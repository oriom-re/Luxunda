"""
LuxDB MVP Demo (FastAPI + Socket.IO)
Działa na porcie 3001 z czystą architekturą app_v2
"""

import asyncio
import uvicorn
from typing import Dict, Any, List, Optional
from datetime import datetime

# FastAPI + Socket.IO
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import socketio

# Nowa architektura z głównego poziomu
from database.postgre_db import Postgre_db
from database.soul_repository import SoulRepository
from database.models.relationship import Relationship
from services.entity_manager import EntityManager
# from services.genotype_service import GenotypService
from ai.hybrid_ai_system import HybridAISystem

# FastAPI app
app = FastAPI(title="LuxDB MVP", version="2.0.0")

# Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["*"],
    logger=False,
    engineio_logger=False
)

# Kombinuj FastAPI z Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Statyczne pliki
app.mount("/static", StaticFiles(directory="static"), name="static")

# Główne komponenty systemu
postgresql_manager: Optional[Postgre_db] = None
soul_repository: Optional[SoulRepository] = None
entity_manager: Optional[EntityManager] = None

hybrid_ai: Optional[HybridAISystem] = None

# Demo data - genotypy dusz
DEMO_GENOTYPES = {
    "ai_agent_soul": {
        "attributes": {
            "name": {"py_type": "str", "max_length": 100},
            "intelligence_level": {"py_type": "int", "min_value": 1, "max_value": 10},
            "processing_speed": {"py_type": "float", "min_value": 0.1, "max_value": 10.0},
            "memory_capacity": {"py_type": "int", "min_value": 1000, "max_value": 1000000},
            "is_active": {"py_type": "bool", "default": True}
        },
        "capabilities": {
            "think": "Proces myślenia i analizy",
            "learn": "Uczenie się z doświadczeń", 
            "communicate": "Komunikacja z innymi bytami",
            "evolve": "Ewolucja i adaptacja"
        },
        "being_limit": 10,
        "description": "Genotyp dla inteligentnych agentów AI"
    },

    "semantic_data_soul": {
        "attributes": {
            "content": {"py_type": "str", "max_length": 10000},
            "embedding": {"py_type": "List[float]", "vector_size": 1536},
            "semantic_weight": {"py_type": "float", "min_value": 0.0, "max_value": 1.0},
            "context_tags": {"py_type": "List[str]", "max_items": 20},
            "timestamp": {"py_type": "str", "format": "datetime"}
        },
        "capabilities": {
            "embed": "Tworzenie embeddings semantycznych",
            "search": "Wyszukiwanie semantyczne",
            "relate": "Tworzenie relacji semantycznych"
        },
        "being_limit": None,
        "description": "Genotyp dla danych semantycznych z AI embeddings"
    },

    "relational_soul": {
        "attributes": {
            "from_entity": {"py_type": "str", "max_length": 100},
            "to_entity": {"py_type": "str", "max_length": 100}, 
            "relation_type": {"py_type": "str", "max_length": 50},
            "strength": {"py_type": "float", "min_value": 0.0, "max_value": 1.0},
            "metadata": {"py_type": "dict", "default": {}}
        },
        "capabilities": {
            "connect": "Łączenie bytów relacjami",
            "strengthen": "Wzmacnianie relacji",
            "weaken": "Osłabianie relacji"
        },
        "being_limit": None,
        "description": "Genotyp dla relacji między bytami"
    }
}

# Demo beings - pierwsze byty do manifestacji
DEMO_BEINGS = {
    "luxdb_core": {
        "genotype": "ai_agent_soul",
        "data": {
            "name": "LuxDB Core Agent",
            "intelligence_level": 9,
            "processing_speed": 8.5,
            "memory_capacity": 500000,
            "is_active": True
        }
    },
    "semantic_data_1": {
        "genotype": "semantic_data_soul", 
        "data": {
            "content": "LuxDB to revolutionize database technology with genetic data evolution",
            "embedding": [0.1] * 1536,  # Mock embedding
            "semantic_weight": 0.95,
            "context_tags": ["database", "AI", "evolution", "genetics"],
            "timestamp": datetime.now().isoformat()
        }
    },
    "relation_manager": {
        "genotype": "relational_soul",
        "data": {
            "from_entity": "luxdb_core", 
            "to_entity": "semantic_data_1",
            "relation_type": "manages",
            "strength": 0.8,
            "metadata": {"created_by": "system", "auto_generated": True}
        }
    },
    "ai_agent_1": {
        "genotype": "ai_agent_soul",
        "data": {
            "name": "Assistant Agent Alpha",
            "intelligence_level": 7,
            "processing_speed": 6.5, 
            "memory_capacity": 250000,
            "is_active": True
        }
    }
}

@app.on_event("startup")
async def startup():
    """Inicjalizacja aplikacji"""
    global postgresql_manager, soul_repository, entity_manager, genotype_service, hybrid_ai

    print("🌀 Uruchamianie LuxDB MVP Demo (FastAPI)...")
    print("   'Nie relacja. Nie dokument. Ewolucja danych.'")

    try:
        # Inicjalizacja PostgreSQL
        postgresql_manager = Postgre_db()
        await postgresql_manager.initialize()
        soul_repository = SoulRepository(postgresql_manager)
        entity_manager = EntityManager(soul_repository)
        genotype_service = GenotypService(soul_repository)

        # Inicjalizacja AI (bez OpenAI key = tylko AI Brain)
        hybrid_ai = HybridAISystem()

    except Exception as e:
        print(f"❌ Błąd inicjalizacji PostgreSQL: {e}")
        # Kontynuuj bez bazy danych w trybie demo

    # Przygotuj demo genotypy
    print("🧬 Genotypy LuxDB (Dusze) przygotowane do manifestacji:")
    for soul_name, genotype in DEMO_GENOTYPES.items():
        attrs_count = len(genotype["attributes"])
        caps_count = len(genotype["capabilities"])  
        limit = genotype.get("being_limit", "None")
        print(f"   - {soul_name}: {attrs_count} atrybutów, {caps_count} zdolności, limit: {limit}")

    print("👤 Pierwsze byty przygotowane do manifestacji")
    print("✨ LuxDB MVP Demo (FastAPI) gotowy!")
    print("🧬 Genotypowy model danych aktywny")
    print("👥 Uniwersum bytów gotowe do eksploracji") 
    print("🔗 System relacji i intencji działa")
    print("📡 WebSocket komunikacja dostępna na /ws")

@app.get("/")
async def root():
    """Główna strona z interfejsem LuxDB"""
    return FileResponse('static/index.html')

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "LuxDB MVP działa poprawnie",
        "version": "2.0.0",
        "database": "connected" if postgresql_manager else "demo_mode",
        "ai_system": "active" if hybrid_ai else "disabled"
    }

@app.get("/api/genotypes")
async def get_genotypes():
    """Pobierz dostępne genotypy (dusze)"""
    return {
        "genotypes": DEMO_GENOTYPES,
        "count": len(DEMO_GENOTYPES)
    }

@app.get("/api/beings")
async def get_beings():
    """Pobierz manifestowane byty"""
    return {
        "beings": DEMO_BEINGS,
        "count": len(DEMO_BEINGS)
    }

@app.get("/api/universe-stats")
async def get_universe_stats():
    """Statystyki wszechświata LuxDB"""
    return {
        "souls_count": len(DEMO_GENOTYPES),
        "beings_count": len(DEMO_BEINGS),
        "relations_count": sum(1 for being in DEMO_BEINGS.values() 
                             if being["genotype"] == "relational_soul"),
        "active_agents": sum(1 for being in DEMO_BEINGS.values()
                           if being["genotype"] == "ai_agent_soul" 
                           and being["data"].get("is_active", False)),
        "system_status": "evolutionary"
    }

# Socket.IO Events
@sio.event
async def connect(sid, environ):
    """Klient połączył się"""
    print(f"🌟 Połączono z demo server (app_v2)")
    await sio.emit('connected', {
        'message': '🌟 Połączono z wszechświatem LuxOS',
        'universe_status': 'active',
        'genetic_system': 'online'
    }, room=sid)

@sio.event
async def disconnect(sid):
    """Klient rozłączył się"""
    print(f"👋 Rozłączono z demo server")

@sio.event
async def request_graph_data(sid, data=None):
    """Żądanie danych grafu"""
    print("📡 Żądanie danych grafu...")

    # Przygotuj nodes (byty)
    nodes = []
    for being_id, being_data in DEMO_BEINGS.items():
        genotype = being_data["genotype"]
        node = {
            "id": being_id,
            "type": genotype,
            "label": being_data["data"].get("name", being_id),
            "genotype": genotype,
            "size": 20 if genotype == "ai_agent_soul" else 15,
            "color": {
                "ai_agent_soul": "#00ff88",
                "semantic_data_soul": "#ff6b6b", 
                "relational_soul": "#4ecdc4"
            }.get(genotype, "#888888")
        }
        nodes.append(node)

    # Przygotuj edges (relacje)
    edges = []
    for being_id, being_data in DEMO_BEINGS.items():
        if being_data["genotype"] == "relational_soul":
            data = being_data["data"]
            edge = {
                "source": data["from_entity"],
                "target": data["to_entity"], 
                "type": data["relation_type"],
                "strength": data["strength"],
                "width": max(1, data["strength"] * 5)
            }
            edges.append(edge)

    # Dodaj przykładowe edges między agentami
    edges.extend([
        {"source": "luxdb_core", "target": "ai_agent_1", "type": "collaborates", "strength": 0.7, "width": 3},
        {"source": "ai_agent_1", "target": "semantic_data_1", "type": "processes", "strength": 0.6, "width": 3}
    ])

    graph_data = {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "nodes_count": len(nodes),
            "edges_count": len(edges),
            "genotypes_count": len(DEMO_GENOTYPES)
        }
    }

    await sio.emit('graph_data', graph_data, room=sid)

@sio.event
async def send_intention(sid, data):
    """Przetwórz intencję użytkownika"""
    intention = data.get('intention', '').strip()

    if not intention:
        await sio.emit('intention_response', {
            'success': False,
            'message': 'Intencja nie może być pusta'
        }, room=sid)
        return

    print(f"💫 Otrzymano intencję: {intention}")

    # Proces hybrydowy AI jeśli dostępny
    if hybrid_ai:
        try:
            result = await hybrid_ai.process_request(intention, use_openai=False)

            await sio.emit('intention_response', {
                'success': True,
                'message': 'Intencja przetworzona przez LuxOS AI Brain',
                'intention': intention,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }, room=sid)

        except Exception as e:
            await sio.emit('intention_response', {
                'success': False, 
                'message': f'Błąd przetwarzania intencji: {str(e)}',
                'intention': intention
            }, room=sid)
    else:
        # Fallback response
        await sio.emit('intention_response', {
            'success': True,
            'message': f'Intencja "{intention}" została zaakceptowana przez wszechświat LuxDB',
            'intention': intention,
            'note': 'Demo mode - pełne przetwarzanie wymaga konfiguracji AI',
            'timestamp': datetime.now().isoformat()
        }, room=sid)

@sio.event 
async def lux_chat(sid, data):
    """Chat z Lux AI"""
    message = data.get('message', '').strip()

    if not message:
        await sio.emit('lux_response', {
            'success': False,
            'message': 'Wiadomość nie może być pusta'
        }, room=sid)
        return

    print(f"💬 Lux Chat: {message}")

    # Process przez hybrid AI
    if hybrid_ai:
        try:
            result = await hybrid_ai.process_request(message, use_openai=False)

            response_text = "Rozumiem Twoją wiadomość. " + result.get("final_result", {}).get("summary", "Przetwarzam dalej...")

            await sio.emit('lux_response', {
                'success': True,
                'message': response_text,
                'original_message': message,
                'ai_result': result,
                'timestamp': datetime.now().isoformat()
            }, room=sid)

        except Exception as e:
            await sio.emit('lux_response', {
                'success': False,
                'message': f'Błąd w komunikacji z Lux: {str(e)}',
                'original_message': message
            }, room=sid)
    else:
        # Fallback Lux response
        responses = [
            f"🌟 Lux tutaj! Rozumiem: '{message}'. Analizuję w kontekście wszechświata LuxDB...",
            f"💫 Interesujące pytanie! '{message}' - pozwól mi przeanalizować to genetycznie...", 
            f"🧬 Widzę potencjał ewolucyjny w: '{message}'. System LuxDB eksploruje możliwości...",
            f"✨ Twoja intencja '{message}' rezonuje z kwantową strukturą danych. Procesuję..."
        ]

        import random
        response = random.choice(responses)

        await sio.emit('lux_response', {
            'success': True,
            'message': response,
            'original_message': message,
            'mode': 'demo',
            'timestamp': datetime.now().isoformat()
        }, room=sid)

if __name__ == "__main__":
    print("🚀 Uruchamianie serwera LuxDB MVP (FastAPI + Socket.IO) na porcie 3001...")
    print("🌐 URL: http://0.0.0.0:3001")

    uvicorn.run(
        socket_app,
        host="0.0.0.0", 
        port=3001,
        log_level="info"
    )