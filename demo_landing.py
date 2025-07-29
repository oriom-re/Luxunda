#!/usr/bin/env python3
"""
🌀 LuxDB MVP Demo Landing
"Nie relacja. Nie dokument. Ewolucja danych."

Demonstracja genotypowego systemu danych LuxDB:
- Byty (Being) wynikają z duszy (Soul) - genotypu
- Dane są reprezentacją intencji, nie tylko strukturą  
- System uczy się i adaptuje poprzez genotypy
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import socketio
from flask import Flask, render_template_string, jsonify, request
from flask_socketio import SocketIO, emit

# Importy z app_v2 - LuxDB MVP
from app_v2.database.postgre_db import Postgre_db
from app_v2.database.models.base import Being, Soul
from app_v2.database.models.relationship import Relationship
from app_v2.database.soul_repository import SoulRepository
from app_v2.services.entity_manager import EntityManager

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'luxdb_mvp_demo_key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# 🌀 LuxDB MVP - Globalne struktury
connected_users = set()
living_beings = []  # Aktywne byty w uniwersum
genotype_definitions = {}  # Definicje genotypów (dusze)

@app.route('/')
def index():
    """🌀 Główna strona LuxDB MVP Demo"""
    return app.send_static_file('index.html')

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

@app.route('/api/souls')
def get_souls():
    """🧠 Zwraca definicje duszy (genotypy) w LuxDB"""
    return jsonify({
        "status": "success",
        "philosophy": "Nie relacja. Nie dokument. Ewolucja danych.",
        "souls": genotype_definitions,
        "count": len(genotype_definitions),
        "description": "Dusze (Soul) to genotypy definiujące cechy i zdolności bytów"
    })

@app.route('/api/beings')
def get_beings():
    """👥 Zwraca żywe byty w uniwersum LuxDB"""
    return jsonify({
        "status": "success",
        "beings": [being.to_dict() if hasattr(being, 'to_dict') else str(being) for being in living_beings],
        "count": len(living_beings),
        "description": "Byty (Being) to żywe instancje duszy z unikalnymi cechami"
    })

@app.route('/api/manifest-being', methods=['POST'])
def manifest_being():
    """✨ Manifestuje nowy byt na podstawie duszy (genotypu)"""
    try:
        data = request.get_json()
        soul_type = data.get('soul_type')
        being_alias = data.get('alias')
        attributes = data.get('attributes', {})

        if not soul_type or soul_type not in genotype_definitions:
            return jsonify({
                "status": "error", 
                "message": f"Nieznany typ duszy: {soul_type}"
            }), 400

        # TODO: Implementacja manifestacji przez EntityManager
        return jsonify({
            "status": "success",
            "message": f"Byt '{being_alias}' z duszy '{soul_type}' zostanie zmaterializowany",
            "soul_type": soul_type,
            "attributes": attributes
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """🔗 Obsługuje nowe połączenia WebSocket"""
    connected_users.add(request.sid)
    print(f"🔗 Nowe połączenie: {request.sid}")
    emit('connection_established', {
        'message': 'Połączono z uniwersum LuxDB',
        'session_id': request.sid
    })

@socketio.on('disconnect')
def handle_disconnect():
    """🔌 Obsługuje rozłączenia WebSocket"""
    connected_users.discard(request.sid)
    print(f"🔌 Rozłączenie: {request.sid}")

@socketio.on('send_intention')
def handle_intention(data):
    """🌀 Obsługuje intencje w uniwersum LuxDB - dane jako reprezentacja intencji"""
    try:
        intention_text = data.get('intention', '')
        user_id = data.get('user_id', 'anonymous') 

        print(f"🧠 LuxDB: Intencja od {user_id}: {intention_text}")

        # Analiza intencji w kontekście LuxDB
        analysis = analyze_luxdb_intention(intention_text)

        # Przygotuj odpowiedź zgodną z filozofią LuxDB
        response = {
            "type": "luxdb_intention_processed",
            "original_intention": intention_text,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "processed_by": "LuxDB_MVP",
            "philosophy": "Dane są reprezentacją intencji"
        }

        # Wyślij do wszystkich w uniwersum
        emit('luxdb_response', response, broadcast=True)

        print(f"📤 LuxDB: Intencja przetworzona jako {analysis.get('luxdb_type', 'unknown')}")

    except Exception as e:
        print(f"❌ Błąd przetwarzania intencji LuxDB: {e}")
        emit('error', {'message': str(e)})

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

# 🌀 Uruchom LuxDB MVP Demo
if __name__ == '__main__':
    print("🌀 Uruchamianie LuxDB MVP Demo Landing...")
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
    asyncio.run(initialize_luxdb_universe())

    print("✨ LuxDB MVP Demo uruchomiony na http://0.0.0.0:3000")
    print("🧬 Genotypowy model danych aktywny")
    print("👥 Uniwersum bytów gotowe do eksploracji")
    print("🔗 System relacji i intencji działa")

    # Uruchom serwer
    socketio.run(app, host='0.0.0.0', port=3000, debug=False)