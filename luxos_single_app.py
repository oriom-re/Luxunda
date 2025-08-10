
#!/usr/bin/env python3
"""
🌟 LuxOS Single File Application
Wszystko w jednym pliku - kompletny system LuxOS z interfejsem web
"""

import asyncio
import json
import os
import sys
import hashlib
import ulid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

# Web Framework
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Database
import asyncpg

# AI Integration
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# =============================================================================
# CORE DATA MODELS
# =============================================================================

@dataclass
class Soul:
    """Dusza - genotyp bytu"""
    soul_hash: str
    global_ulid: str
    alias: Optional[str] = None
    genotype: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    @classmethod
    async def create(cls, genotype: Dict[str, Any], alias: str = None) -> 'Soul':
        """Tworzy nową duszę"""
        soul_hash = hashlib.sha256(json.dumps(genotype, sort_keys=True).encode()).hexdigest()[:16]
        global_ulid = str(ulid.new())
        
        soul = cls(
            soul_hash=soul_hash,
            global_ulid=global_ulid,
            alias=alias or f"soul_{soul_hash[:8]}",
            genotype=genotype,
            created_at=datetime.now()
        )
        
        await soul.save()
        return soul
    
    async def save(self):
        """Zapisuje duszę do bazy"""
        if not db_pool:
            return
            
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO souls (soul_hash, global_ulid, alias, genotype, created_at)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (soul_hash) DO UPDATE SET
                alias = $3, genotype = $4, created_at = $5
            """, self.soul_hash, self.global_ulid, self.alias, 
                json.dumps(self.genotype), self.created_at)

@dataclass
class Being:
    """Byt - instancja duszy"""
    ulid: str
    soul_hash: str
    alias: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    async def create(cls, soul: Soul, alias: str = None, **attributes) -> 'Being':
        """Tworzy nowy byt z duszy"""
        being_ulid = str(ulid.new())
        
        being = cls(
            ulid=being_ulid,
            soul_hash=soul.soul_hash,
            alias=alias or f"being_{being_ulid[:8]}",
            data=attributes,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await being.save()
        return being
    
    async def save(self):
        """Zapisuje byt do bazy"""
        if not db_pool:
            return
            
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO beings (ulid, soul_hash, alias, data, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (ulid) DO UPDATE SET
                alias = $3, data = $4, updated_at = $6
            """, self.ulid, self.soul_hash, self.alias, 
                json.dumps(self.data), self.created_at, self.updated_at)
    
    async def get_soul(self) -> Optional[Soul]:
        """Pobiera duszę tego bytu"""
        if not db_pool:
            return None
            
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM souls WHERE soul_hash = $1
            """, self.soul_hash)
            
            if row:
                return Soul(
                    soul_hash=row['soul_hash'],
                    global_ulid=row['global_ulid'],
                    alias=row['alias'],
                    genotype=row['genotype'],
                    created_at=row['created_at']
                )
        return None

@dataclass
class Message:
    """Wiadomość w systemie"""
    ulid: str
    author_ulid: str
    content: str
    message_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    @classmethod
    async def create(cls, author_ulid: str, content: str, message_type: str = "text", **metadata) -> 'Message':
        """Tworzy nową wiadomość"""
        message_ulid = str(ulid.new())
        
        message = cls(
            ulid=message_ulid,
            author_ulid=author_ulid,
            content=content,
            message_type=message_type,
            metadata=metadata,
            created_at=datetime.now()
        )
        
        await message.save()
        return message
    
    async def save(self):
        """Zapisuje wiadomość do bazy"""
        if not db_pool:
            return
            
        async with db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO messages (ulid, author_ulid, content, message_type, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (ulid) DO UPDATE SET
                content = $3, message_type = $4, metadata = $5
            """, self.ulid, self.author_ulid, self.content, 
                self.message_type, json.dumps(self.metadata), self.created_at)

# =============================================================================
# LUX ASSISTANT
# =============================================================================

class LuxAssistant:
    """Główny asystent AI systemu"""
    
    def __init__(self, openai_key: str = None):
        self.openai_key = openai_key
        self.client = None
        self.system_prompt = """Jesteś Lux - zaawansowany asystent AI systemu LuxOS. 
        System LuxOS to rewolucyjna platforma oparta na bytach (Beings) i duszach (Souls).
        Każdy byt ma swoją duszę zawierającą genotyp - przepis na zachowanie.
        Pomagasz użytkownikom w zarządzaniu systemem, tworzeniu nowych bytów i analizie danych."""
        
        if openai_key and HAS_OPENAI:
            self.client = openai.AsyncOpenAI(api_key=openai_key)
    
    async def process_message(self, message: str, context: List[str] = None) -> str:
        """Przetwarza wiadomość użytkownika"""
        if not self.client:
            return self._fallback_response(message)
        
        try:
            messages = [{"role": "system", "content": self.system_prompt}]
            
            if context:
                context_text = "\n".join(context[-10:])  # Ostatnie 10 wiadomości
                messages.append({"role": "system", "content": f"Kontekst rozmowy:\n{context_text}"})
            
            messages.append({"role": "user", "content": message})
            
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI Error: {e}")
            return self._fallback_response(message)
    
    def _fallback_response(self, message: str) -> str:
        """Odpowiedź fallback gdy OpenAI nie działa"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['pomoc', 'help', 'jak']):
            return """🌟 Witaj w LuxOS! Mogę Ci pomóc z:
            
• Tworzeniem nowych bytów i dusz
• Przeglądaniem istniejących bytów
• Analizą danych w systemie
• Wyjaśnianiem koncepcji LuxOS

Napisz co Cię interesuje! 😊"""
        
        elif any(word in message_lower for word in ['byt', 'being', 'stwórz', 'utwórz']):
            return """🔧 Aby stworzyć nowy byt:
1. Zdefiniuj genotyp (duszę) z właściwościami
2. Utwórz instancję bytu z tej duszy  
3. Dodaj atrybuty specyficzne dla instancji

Czy chcesz żebym pomógł Ci stworzyć konkretny byt?"""
        
        elif any(word in message_lower for word in ['lista', 'pokaż', 'jakie']):
            return """📋 Mogę pokazać Ci:
• Listę wszystkich bytów w systemie
• Dostępne dusze (genotypy)
• Ostatnie wiadomości
• Status systemu

Co Cię interesuje?"""
        
        else:
            return f"""💭 Otrzymałem: "{message}"

🤖 System LuxOS działa! Mogę pomóc Ci z zarządzaniem bytami, duszami i danymi.
Napisz 'pomoc' aby zobaczyć co potrafię."""

# =============================================================================
# SESSION MANAGER
# =============================================================================

class SessionManager:
    """Zarządza sesjami użytkowników"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.global_lux = None
    
    async def initialize(self):
        """Inicjalizuje manager sesji"""
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            self.global_lux = LuxAssistant(openai_key)
    
    async def create_session(self, fingerprint: str) -> str:
        """Tworzy nową sesję"""
        session_id = str(ulid.new())
        
        self.sessions[session_id] = {
            'fingerprint': fingerprint,
            'created_at': datetime.now(),
            'messages': [],
            'assistant': LuxAssistant(os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
        }
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Pobiera sesję"""
        return self.sessions.get(session_id)
    
    async def add_message(self, session_id: str, author: str, content: str):
        """Dodaje wiadomość do sesji"""
        if session_id in self.sessions:
            self.sessions[session_id]['messages'].append({
                'author': author,
                'content': content,
                'timestamp': datetime.now().isoformat()
            })
            
            # Zachowaj tylko ostatnie 20 wiadomości
            if len(self.sessions[session_id]['messages']) > 20:
                self.sessions[session_id]['messages'] = self.sessions[session_id]['messages'][-20:]

# =============================================================================
# DATABASE SETUP
# =============================================================================

db_pool = None

async def init_database():
    """Inicjalizuje bazę danych"""
    global db_pool
    
    try:
        db_pool = await asyncpg.create_pool(
            host='ep-odd-tooth-a2zcp5by-pooler.eu-central-1.aws.neon.tech',
            port=5432,
            user='neondb_owner',
            password='npg_aY8K9pijAnPI',
            database='neondb',
            min_size=1,
            max_size=10
        )
        
        # Stwórz tabele jeśli nie istnieją
        async with db_pool.acquire() as conn:
            # Tabela souls
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS souls (
                    soul_hash VARCHAR(64) PRIMARY KEY,
                    global_ulid VARCHAR(26) UNIQUE NOT NULL,
                    alias VARCHAR(255),
                    genotype JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela beings
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS beings (
                    ulid VARCHAR(26) PRIMARY KEY,
                    soul_hash VARCHAR(64) REFERENCES souls(soul_hash),
                    alias VARCHAR(255),
                    data JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela messages
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    ulid VARCHAR(26) PRIMARY KEY,
                    author_ulid VARCHAR(26),
                    content TEXT NOT NULL,
                    message_type VARCHAR(50) DEFAULT 'text',
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela relationships
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    id SERIAL PRIMARY KEY,
                    source_ulid VARCHAR(26) NOT NULL,
                    target_ulid VARCHAR(26) NOT NULL,
                    relation_type VARCHAR(100) NOT NULL,
                    metadata JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            print("✅ Baza danych zainicjalizowana")
            return True
            
    except Exception as e:
        print(f"❌ Błąd bazy danych: {e}")
        return False

# =============================================================================
# WEB APPLICATION
# =============================================================================

# Global session manager
session_manager = SessionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Uruchamianie LuxOS Single App...")
    
    # Inicjalizuj bazę danych
    await init_database()
    
    # Inicjalizuj session manager
    await session_manager.initialize()
    
    # Stwórz podstawowe dusze i byty
    await create_initial_data()
    
    print("✅ LuxOS Single App gotowa!")
    
    yield
    
    # Shutdown
    if db_pool:
        await db_pool.close()
        print("🔄 Zamknięto połączenie z bazą")

app = FastAPI(title="LuxOS Single App", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# API MODELS
# =============================================================================

class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    fingerprint: Optional[str] = "anonymous"

class CreateBeingRequest(BaseModel):
    genotype: Dict[str, Any]
    alias: Optional[str] = None
    attributes: Dict[str, Any] = {}

class CreateSoulRequest(BaseModel):
    genotype: Dict[str, Any]
    alias: Optional[str] = None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def create_initial_data():
    """Tworzy podstawowe dane w systemie"""
    try:
        # Dusza Lux Assistant
        lux_genotype = {
            "genesis": {
                "name": "LuxAssistant",
                "type": "ai_assistant", 
                "version": "1.0.0",
                "description": "Główny asystent AI systemu LuxOS"
            },
            "attributes": {
                "intelligence": {"py_type": "int", "default": 90},
                "friendliness": {"py_type": "int", "default": 95},
                "expertise": {"py_type": "list", "default": ["luxos", "ai", "database"]}
            },
            "functions": {
                "chat": {
                    "description": "Rozmawia z użytkownikiem",
                    "parameters": ["message", "context"]
                },
                "analyze_system": {
                    "description": "Analizuje stan systemu",
                    "parameters": ["query_type"]
                }
            }
        }
        
        lux_soul = await Soul.create(lux_genotype, "lux_assistant_soul")
        lux_being = await Being.create(lux_soul, "lux_assistant", 
                                      status="active", role="main_assistant")
        
        # Dusza dla zwykłych użytkowników
        user_genotype = {
            "genesis": {
                "name": "HumanUser",
                "type": "human_user",
                "version": "1.0.0",
                "description": "Użytkownik systemu LuxOS"
            },
            "attributes": {
                "access_level": {"py_type": "str", "default": "user"},
                "preferences": {"py_type": "dict", "default": {}}
            }
        }
        
        user_soul = await Soul.create(user_genotype, "human_user_soul")
        
        print("✅ Utworzono podstawowe dane systemu")
        
    except Exception as e:
        print(f"⚠️ Błąd tworzenia danych: {e}")

# =============================================================================
# WEB ROUTES
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Główna strona aplikacji"""
    return HTMLResponse(content="""
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LuxOS Single App</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 3rem;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .subtitle {
            font-size: 1.2rem;
            opacity: 0.9;
            margin-top: 10px;
        }
        
        .features {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .feature {
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .feature h3 {
            margin-top: 0;
            color: #ffd700;
        }
        
        .chat-section {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .chat-messages {
            height: 300px;
            overflow-y: auto;
            background: rgba(0,0,0,0.2);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
        }
        
        .message {
            margin-bottom: 10px;
            padding: 8px 12px;
            border-radius: 8px;
        }
        
        .message.user {
            background: rgba(102, 126, 234, 0.3);
            margin-left: 20px;
        }
        
        .message.assistant {
            background: rgba(118, 75, 162, 0.3);
            margin-right: 20px;
        }
        
        .chat-input {
            display: flex;
            gap: 10px;
        }
        
        .chat-input input {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255,255,255,0.2);
            color: white;
            font-size: 16px;
        }
        
        .chat-input input::placeholder {
            color: rgba(255,255,255,0.7);
        }
        
        .chat-input button {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            background: #ffd700;
            color: #333;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .chat-input button:hover {
            transform: scale(1.05);
        }
        
        .status {
            text-align: center;
            margin-top: 20px;
            padding: 10px;
            background: rgba(0,255,0,0.2);
            border-radius: 8px;
        }
        
        .api-links {
            margin-top: 30px;
            text-align: center;
        }
        
        .api-links a {
            color: #ffd700;
            text-decoration: none;
            margin: 0 15px;
            padding: 8px 16px;
            border: 1px solid #ffd700;
            border-radius: 5px;
            transition: all 0.3s;
        }
        
        .api-links a:hover {
            background: #ffd700;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌟 LuxOS Single App</h1>
            <div class="subtitle">Kompletny system w jednym pliku</div>
        </div>
        
        <div class="features">
            <div class="feature">
                <h3>🧬 Dusze & Byty</h3>
                <p>System oparty na genotypach (dusze) i ich instancjach (byty). Każdy byt ma swoją unikalną duszę definiującą jego zachowanie.</p>
            </div>
            
            <div class="feature">
                <h3>🤖 AI Assistant</h3>
                <p>Zintegrowany asystent Lux pomaga w zarządzaniu systemem, analizie danych i komunikacji z bytami.</p>
            </div>
            
            <div class="feature">
                <h3>💾 PostgreSQL</h3>
                <p>Pełna integracja z bazą danych PostgreSQL dla trwałego przechowywania danych i relacji.</p>
            </div>
            
            <div class="feature">
                <h3>🚀 Jedna aplikacja</h3>
                <p>Wszystko w jednym pliku - łatwe uruchomienie, deploy i zarządzanie. Idealne do demo i rozwoju.</p>
            </div>
        </div>
        
        <div class="chat-section">
            <h3>💬 Porozmawiaj z Lux</h3>
            <div class="chat-messages" id="chatMessages">
                <div class="message assistant">
                    🌟 Witaj! Jestem Lux - asystent systemu LuxOS. Jak mogę Ci pomóc?
                </div>
            </div>
            <div class="chat-input">
                <input type="text" id="messageInput" placeholder="Napisz wiadomość..." onkeypress="handleKeyPress(event)">
                <button onclick="sendMessage()">Wyślij</button>
            </div>
        </div>
        
        <div class="status" id="status">
            ✅ System LuxOS działa poprawnie
        </div>
        
        <div class="api-links">
            <a href="/api/beings">📋 Byty</a>
            <a href="/api/souls">🧬 Dusze</a>
            <a href="/api/messages">💬 Wiadomości</a>
            <a href="/api/status">📊 Status</a>
        </div>
    </div>

    <script>
        let sessionId = null;
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Dodaj wiadomość użytkownika
            addMessage(message, 'user');
            input.value = '';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: message,
                        session_id: sessionId,
                        fingerprint: 'web_demo_user'
                    })
                });
                
                const data = await response.json();
                
                if (data.session_id) {
                    sessionId = data.session_id;
                }
                
                // Dodaj odpowiedź asystenta
                addMessage(data.response, 'assistant');
                
            } catch (error) {
                addMessage('❌ Błąd komunikacji z serwerem', 'assistant');
            }
        }
        
        function addMessage(content, type) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}`;
            messageDiv.textContent = content;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        // Sprawdź status systemu
        async function checkStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();
                
                const statusDiv = document.getElementById('status');
                if (data.status === 'ok') {
                    statusDiv.innerHTML = `✅ System działa | Byty: ${data.beings_count || 0} | Dusze: ${data.souls_count || 0}`;
                } else {
                    statusDiv.innerHTML = '⚠️ Problem z systemem';
                }
            } catch (error) {
                document.getElementById('status').innerHTML = '❌ Brak połączenia';
            }
        }
        
        // Sprawdź status co 30 sekund
        setInterval(checkStatus, 30000);
        checkStatus();
    </script>
</body>
</html>
    """)

@app.post("/api/chat")
async def chat_endpoint(request: ChatMessage):
    """Endpoint do rozmowy z asystentem"""
    try:
        # Pobierz lub utwórz sesję
        session_id = request.session_id
        if not session_id:
            session_id = await session_manager.create_session(request.fingerprint)
        
        session = await session_manager.get_session(session_id)
        if not session:
            session_id = await session_manager.create_session(request.fingerprint)
            session = await session_manager.get_session(session_id)
        
        # Pobierz kontekst z sesji
        context = [f"{msg['author']}: {msg['content']}" for msg in session['messages'][-10:]]
        
        # Przetwórz wiadomość
        assistant = session.get('assistant') or session_manager.global_lux
        if assistant:
            response = await assistant.process_message(request.message, context)
        else:
            response = "System działa w trybie ograniczonym. OpenAI API nie jest skonfigurowane."
        
        # Dodaj wiadomości do sesji
        await session_manager.add_message(session_id, "user", request.message)
        await session_manager.add_message(session_id, "assistant", response)
        
        # Zapisz wiadomości do bazy
        if db_pool:
            user_message = await Message.create("user", request.message, "text", session_id=session_id)
            assistant_message = await Message.create("assistant", response, "text", session_id=session_id)
        
        return {
            "response": response,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            content={"error": f"Błąd przetwarzania: {str(e)}"},
            status_code=500
        )

@app.get("/api/status")
async def status_endpoint():
    """Status systemu"""
    try:
        beings_count = 0
        souls_count = 0
        messages_count = 0
        
        if db_pool:
            async with db_pool.acquire() as conn:
                beings_count = await conn.fetchval("SELECT COUNT(*) FROM beings")
                souls_count = await conn.fetchval("SELECT COUNT(*) FROM souls")
                messages_count = await conn.fetchval("SELECT COUNT(*) FROM messages")
        
        return {
            "status": "ok",
            "app": "LuxOS Single App",
            "database": "connected" if db_pool else "disconnected",
            "beings_count": beings_count,
            "souls_count": souls_count,
            "messages_count": messages_count,
            "openai": "configured" if os.getenv('OPENAI_API_KEY') else "not configured",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "error": str(e)},
            status_code=500
        )

@app.get("/api/beings")
async def get_beings():
    """Pobiera listę bytów"""
    try:
        if not db_pool:
            return {"beings": []}
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT b.*, s.alias as soul_alias, s.genotype
                FROM beings b
                LEFT JOIN souls s ON b.soul_hash = s.soul_hash
                ORDER BY b.created_at DESC
                LIMIT 50
            """)
            
            beings = []
            for row in rows:
                beings.append({
                    "ulid": row['ulid'],
                    "alias": row['alias'],
                    "soul_hash": row['soul_hash'],
                    "soul_alias": row['soul_alias'],
                    "data": row['data'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })
            
            return {"beings": beings}
            
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.get("/api/souls")
async def get_souls():
    """Pobiera listę dusz"""
    try:
        if not db_pool:
            return {"souls": []}
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM souls
                ORDER BY created_at DESC
                LIMIT 50
            """)
            
            souls = []
            for row in rows:
                souls.append({
                    "soul_hash": row['soul_hash'],
                    "global_ulid": row['global_ulid'],
                    "alias": row['alias'],
                    "genotype": row['genotype'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })
            
            return {"souls": souls}
            
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.get("/api/messages")
async def get_messages():
    """Pobiera ostatnie wiadomości"""
    try:
        if not db_pool:
            return {"messages": []}
        
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM messages
                ORDER BY created_at DESC
                LIMIT 100
            """)
            
            messages = []
            for row in rows:
                messages.append({
                    "ulid": row['ulid'],
                    "author_ulid": row['author_ulid'],
                    "content": row['content'],
                    "message_type": row['message_type'],
                    "metadata": row['metadata'],
                    "created_at": row['created_at'].isoformat() if row['created_at'] else None
                })
            
            return {"messages": messages}
            
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.post("/api/souls")
async def create_soul_endpoint(request: CreateSoulRequest):
    """Tworzy nową duszę"""
    try:
        soul = await Soul.create(request.genotype, request.alias)
        
        return {
            "success": True,
            "soul": {
                "soul_hash": soul.soul_hash,
                "global_ulid": soul.global_ulid,
                "alias": soul.alias,
                "genotype": soul.genotype
            }
        }
        
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

@app.post("/api/beings")
async def create_being_endpoint(request: CreateBeingRequest):
    """Tworzy nowy byt"""
    try:
        # Najpierw utwórz duszę
        soul = await Soul.create(request.genotype, f"{request.alias}_soul" if request.alias else None)
        
        # Potem utwórz byt
        being = await Being.create(soul, request.alias, **request.attributes)
        
        return {
            "success": True,
            "being": {
                "ulid": being.ulid,
                "soul_hash": being.soul_hash,
                "alias": being.alias,
                "data": being.data
            },
            "soul": {
                "soul_hash": soul.soul_hash,
                "alias": soul.alias
            }
        }
        
    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("🌟 Uruchamianie LuxOS Single App...")
    print("📋 Wszystko w jednym pliku!")
    print("🌐 Dostępne na: http://0.0.0.0:5000")
    print("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )
