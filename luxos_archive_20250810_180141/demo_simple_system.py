#!/usr/bin/env python3
"""
🚀 LuxOS Demo System
Unified LuxOS System - Simple Demo Interface
Tradycyjna baza danych + symulacja systemu bytowego
"""

import asyncio
import json
import sqlite3
import uuid
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

print("🚀 Starting LuxOS Demo System...")
print("🌟 Unified LuxOS System Entry Point")
print("=" * 60)

# ===== TRADYCYJNE MODELE DANYCH =====

@dataclass
class Message:
    id: str
    author: str
    text: str
    intention_type: str
    intention_confidence: float
    keywords: List[str]
    sentiment: str
    timestamp: str
    metadata: Dict[str, Any]

@dataclass
class Interaction:
    id: str
    user_id: str
    message_id: str
    interaction_type: str  # "interested", "feedback", "support"
    content: str
    timestamp: str

@dataclass
class Connection:
    id: str
    source_id: str
    target_id: str
    connection_type: str
    strength: float
    reason: str
    timestamp: str

# ===== BAZA DANYCH =====

class SimpleDatabase:
    def __init__(self, db_path: str = "demo_system.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Inicjalizuje tradycyjne tabele SQL"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Tabela wiadomości
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                author TEXT NOT NULL,
                text TEXT NOT NULL,
                intention_type TEXT,
                intention_confidence REAL,
                keywords TEXT, -- JSON array
                sentiment TEXT,
                timestamp TEXT,
                metadata TEXT -- JSON object
            )
        """)

        # Tabela interakcji
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                content TEXT,
                timestamp TEXT,
                FOREIGN KEY (message_id) REFERENCES messages (id)
            )
        """)

        # Tabela połączeń
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS connections (
                id TEXT PRIMARY KEY,
                source_id TEXT NOT NULL,
                target_id TEXT NOT NULL,
                connection_type TEXT NOT NULL,
                strength REAL,
                reason TEXT,
                timestamp TEXT
            )
        """)

        conn.commit()
        conn.close()

    def save_message(self, message: Message) -> bool:
        """Zapisuje wiadomość do bazy"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO messages 
                (id, author, text, intention_type, intention_confidence, keywords, sentiment, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                message.id, message.author, message.text, message.intention_type,
                message.intention_confidence, json.dumps(message.keywords),
                message.sentiment, message.timestamp, json.dumps(message.metadata)
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Błąd zapisu wiadomości: {e}")
            return False

    def save_interaction(self, interaction: Interaction) -> bool:
        """Zapisuje interakcję do bazy"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO interactions 
                (id, user_id, message_id, interaction_type, content, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                interaction.id, interaction.user_id, interaction.message_id,
                interaction.interaction_type, interaction.content, interaction.timestamp
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Błąd zapisu interakcji: {e}")
            return False

    def save_connection(self, connection: Connection) -> bool:
        """Zapisuje połączenie do bazy"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO connections 
                (id, source_id, target_id, connection_type, strength, reason, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                connection.id, connection.source_id, connection.target_id,
                connection.connection_type, connection.strength, connection.reason, connection.timestamp
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"❌ Błąd zapisu połączenia: {e}")
            return False

    def get_all_messages(self) -> List[Message]:
        """Pobiera wszystkie wiadomości"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM messages ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()

        messages = []
        for row in rows:
            messages.append(Message(
                id=row[0], author=row[1], text=row[2], intention_type=row[3],
                intention_confidence=row[4], keywords=json.loads(row[5]),
                sentiment=row[6], timestamp=row[7], metadata=json.loads(row[8])
            ))

        return messages

    def get_all_connections(self) -> List[Connection]:
        """Pobiera wszystkie połączenia"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM connections ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()

        connections = []
        for row in rows:
            connections.append(Connection(
                id=row[0], source_id=row[1], target_id=row[2],
                connection_type=row[3], strength=row[4], reason=row[5], timestamp=row[6]
            ))

        return connections

# ===== SYMULATOR SYSTEMU BYTOWEGO =====

class LuxOSSimulator:
    """Symuluje zachowanie systemu bytowego LuxOS"""

    def __init__(self):
        self.intention_types = [
            "question", "suggestion", "problem", "idea", "support_request",
            "feedback", "collaboration", "research", "development", "innovation"
        ]
        self.sentiments = ["positive", "neutral", "negative", "excited", "concerned"]

    def analyze_intention(self, text: str) -> Dict[str, Any]:
        """Symuluje analizę intencji przez AI"""
        text_lower = text.lower()

        # Prosta heurystyka do symulacji AI
        if any(word in text_lower for word in ["jak", "dlaczego", "co", "kiedy", "gdzie"]):
            intention = "question"
            confidence = 0.85
        elif any(word in text_lower for word in ["sugeruję", "proponuję", "może", "warto"]):
            intention = "suggestion"
            confidence = 0.78
        elif any(word in text_lower for word in ["problem", "błąd", "nie działa", "pomoc"]):
            intention = "problem"
            confidence = 0.82
        elif any(word in text_lower for word in ["pomysł", "idea", "innowacja", "nowe"]):
            intention = "idea"
            confidence = 0.75
        elif any(word in text_lower for word in ["współpraca", "razem", "zespół", "partnerstwo"]):
            intention = "collaboration"
            confidence = 0.80
        elif any(word in text_lower for word in ["inwestor", "finansowanie", "seed", "fundusz"]):
            intention = "investment_request"
            confidence = 0.88
        elif any(word in text_lower for word in ["developer", "programista", "dołączyć", "praca"]):
            intention = "recruitment"
            confidence = 0.85
        elif any(word in text_lower for word in ["optymalizacja", "wydajność", "cache", "zapytania"]):
            intention = "optimization"
            confidence = 0.79
        elif any(word in text_lower for word in ["integracja", "api", "crm", "salesforce"]):
            intention = "integration"
            confidence = 0.83
        elif any(word in text_lower for word in ["ci/cd", "aws", "pipeline", "wdrożenie"]):
            intention = "devops"
            confidence = 0.77
        elif any(word in text_lower for word in ["code review", "architektura", "mikroserwisy"]):
            intention = "code_review"
            confidence = 0.81
        else:
            intention = "general"
            confidence = 0.60

        # Analiza sentymentu
        positive_words = ["świetnie", "super", "doskonale", "rewelacyjne", "kocham", "podoba"]
        negative_words = ["źle", "kiepsko", "problem", "błąd", "nie lubię", "frustruje"]

        if any(word in text_lower for word in positive_words):
            sentiment = "positive"
        elif any(word in text_lower for word in negative_words):
            sentiment = "negative"
        else:
            sentiment = "neutral"

        # Ekstraktowanie słów kluczowych
        stop_words = {"i", "a", "o", "w", "na", "z", "do", "że", "się", "to", "jest", "nie", "z", "w", "na", "do", "dla", "jak"}
        words = text_lower.split()
        keywords = [word for word in words if len(word) > 3 and word not in stop_words][:5]

        return {
            "intention_type": intention,
            "confidence": confidence,
            "sentiment": sentiment,
            "keywords": keywords
        }

    def find_semantic_connections(self, new_message: Message, existing_messages: List[Message]) -> List[Dict[str, Any]]:
        """Symuluje znajdowanie semantycznych połączeń między wiadomościami"""
        connections = []

        for existing_msg in existing_messages[-10:]:  # Sprawdź ostatnie 10 wiadomości
            if existing_msg.id == new_message.id:
                continue

            # Podobieństwo słów kluczowych
            common_keywords = set(new_message.keywords) & set(existing_msg.keywords)
            keyword_similarity = len(common_keywords) / max(len(new_message.keywords), 1)

            # Podobieństwo intencji
            intention_similarity = 1.0 if new_message.intention_type == existing_msg.intention_type else 0.3

            # Całkowita siła połączenia
            total_strength = (keyword_similarity * 0.7) + (intention_similarity * 0.3)

            if total_strength > 0.4:  # Próg podobieństwa
                reason = f"Podobne słowa kluczowe: {list(common_keywords)}" if common_keywords else "Podobna intencja"
                connections.append({
                    "source_id": new_message.id,
                    "target_id": existing_msg.id,
                    "strength": total_strength,
                    "reason": reason
                })

        return connections

# ===== FASTAPI APLIKACJA =====

app = FastAPI(title="LuxOS Demo System")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Globalne instancje
db = SimpleDatabase()
simulator = LuxOSSimulator()
connected_clients = []

@app.get("/")
async def index():
    """Landing page główna"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LuxOS Demo System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a2e; color: white; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { color: #00ff88; }
            .demo-links { margin: 20px 0; }
            .demo-links a { 
                display: inline-block; 
                margin: 10px 15px 10px 0; 
                padding: 10px 20px; 
                background: #0066cc; 
                color: white; 
                text-decoration: none; 
                border-radius: 5px; 
            }
            .demo-links a:hover { background: #0088ff; }
            .investor-link {
                background: linear-gradient(135deg, #00ff88, #00ccff) !important;
                color: #000 !important;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🧬 LuxOS Demo System</h1>
            <p>System samoorganizujących się intencji AI</p>

            <div class="demo-links">
                <a href="/static/investor_demo.html" class="investor-link">💰 Investor Demo</a>
                <a href="/static/demo_interface.html">🚀 Live Demo</a>
                <a href="/static/recruitment_landing.html">👥 Rekrutacja</a>
                <a href="/api/stats">📊 System Stats</a>
            </div>

            <h3>Status systemu:</h3>
            <div id="system-status">
                <p>✅ WebSocket Server: Aktywny</p>
                <p>✅ AI System: Gotowy</p>
                <p>✅ Graf intencji: Online</p>
            </div>
        </div>
    </body>
    </html>
    """)

@app.get("/demo")
async def demo():
    """Interfejs demo systemu"""
    with open("static/demo_interface.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint dla real-time komunikacji"""
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        # Wyślij istniejące dane przy połączeniu
        messages = db.get_all_messages()
        connections = db.get_all_connections()

        await websocket.send_json({
            "type": "initial_data",
            "messages": [asdict(msg) for msg in messages],
            "connections": [asdict(conn) for conn in connections]
        })

        while True:
            data = await websocket.receive_json()

            if data["type"] == "new_message":
                await handle_new_message(data["content"], websocket)
            elif data["type"] == "new_interaction":
                await handle_new_interaction(data["content"], websocket)

    except WebSocketDisconnect:
        connected_clients.remove(websocket)

async def handle_new_message(content: Dict[str, Any], websocket: WebSocket):
    """Obsługuje nową wiadomość"""
    # Analiza intencji przez symulator
    analysis = simulator.analyze_intention(content["text"])

    # Tworzenie wiadomości
    message = Message(
        id=str(uuid.uuid4()),
        author=content["author"],
        text=content["text"],
        intention_type=analysis["intention_type"],
        intention_confidence=analysis["confidence"],
        keywords=analysis["keywords"],
        sentiment=analysis["sentiment"],
        timestamp=datetime.now().isoformat(),
        metadata={
            "demo_mode": True,
            "analyzed_by": "LuxOS_Simulator"
        }
    )

    # Zapisz do bazy
    db.save_message(message)

    # Znajdź semantyczne połączenia
    existing_messages = db.get_all_messages()
    semantic_connections = simulator.find_semantic_connections(message, existing_messages)

    # Zapisz połączenia
    saved_connections = []
    for conn_data in semantic_connections:
        connection = Connection(
            id=str(uuid.uuid4()),
            source_id=conn_data["source_id"],
            target_id=conn_data["target_id"],
            connection_type="semantic_similarity",
            strength=conn_data["strength"],
            reason=conn_data["reason"],
            timestamp=datetime.now().isoformat()
        )
        db.save_connection(connection)
        saved_connections.append(connection)

    # Powiadom wszystkich klientów
    response = {
        "type": "new_message_processed",
        "message": asdict(message),
        "new_connections": [asdict(conn) for conn in saved_connections],
        "connections_count": len(saved_connections)
    }

    for client in connected_clients:
        try:
            await client.send_json(response)
        except:
            pass

async def handle_new_interaction(content: Dict[str, Any], websocket: WebSocket):
    """Obsługuje nową interakcję"""
    interaction = Interaction(
        id=str(uuid.uuid4()),
        user_id=content["user_id"],
        message_id=content["message_id"],
        interaction_type=content["interaction_type"],
        content=content.get("content", ""),
        timestamp=datetime.now().isoformat()
    )

    db.save_interaction(interaction)

    # Powiadom wszystkich klientów
    response = {
        "type": "new_interaction",
        "interaction": asdict(interaction)
    }

    for client in connected_clients:
        try:
            await client.send_json(response)
        except:
            pass

@app.get("/api/stats")
async def get_stats():
    """API endpoint ze statystykami systemu"""
    messages = db.get_all_messages()
    connections = db.get_all_connections()

    intention_stats = {}
    for msg in messages:
        intention_stats[msg.intention_type] = intention_stats.get(msg.intention_type, 0) + 1

    return {
        "total_messages": len(messages),
        "total_connections": len(connections),
        "intention_distribution": intention_stats,
        "avg_connection_strength": sum(conn.strength for conn in connections) / max(len(connections), 1),
        "last_update": datetime.now().isoformat()
    }

if __name__ == "__main__":
    print("🚀 Uruchamiam LuxOS Demo System...")
    print("📊 Tradycyjna baza danych + Symulacja systemu bytowego")
    print("🌐 Interfejs: http://0.0.0.0:5000")

    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")