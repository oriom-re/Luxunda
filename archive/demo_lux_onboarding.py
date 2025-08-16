import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Optional, List, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import openai

# Użyj istniejącego systemu Being zamiast Message
from luxdb.models.soul import Soul  
from luxdb.models.being import Being
from luxdb.models.relationship import Relationship

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Konfiguracja OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY", "test-key")

class LuxOnboardingSystem:
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.lux_assistant_soul = None

    async def initialize(self):
        """Inicjalizuje system - tworzy lub pobiera Soul dla asystenta Lux"""
        # Pobierz lub utwórz Soul dla asystenta
        self.lux_assistant_soul = await self._get_or_create_lux_assistant_soul()
        print("🤖 Lux Assistant Soul initialized")

    async def _get_or_create_lux_assistant_soul(self) -> 'Soul':
        """Pobiera lub tworzy Soul dla asystenta Lux"""
        try:
            soul = await Soul.load_by_alias("lux_assistant")
            if soul:
                return soul
        except Exception as e:
            print(f"Error loading lux_assistant soul: {e}")
            pass

        # Utwórz nowy soul dla asystenta
        assistant_genotype = {
            "genesis": {
                "name": "lux_assistant", 
                "type": "ai_assistant",
                "doc": "Asystent Lux do onboardingu użytkowników"
            },
            "attributes": {
                "name": {"py_type": "str"},
                "role": {"py_type": "str"},
                "model": {"py_type": "str"},
                "personality": {"py_type": "str"},
                "capabilities": {"py_type": "List[str]"}
            }
        }

        try:
            return await Soul.create(assistant_genotype, alias="lux_assistant")
        except Exception as e:
            print(f"Error creating lux_assistant soul: {e}")
            raise

    async def _get_or_create_message_soul(self) -> 'Soul':
        """Pobiera lub tworzy Soul dla wiadomości (nie zmieniamy istniejący!)"""
        try:
            soul = await Soul.load_by_alias("lux_message")
            if soul:
                return soul
        except Exception as e:
            print(f"Error loading lux_message soul: {e}")
            pass

        # Tylko jeśli nie istnieje, tworzymy nowy
        message_genotype = {
            "genesis": {
                "name": "lux_message",
                "type": "message", 
                "doc": "Wiadomość w rozmowie z asystentem Lux"
            },
            "attributes": {
                "content": {"py_type": "str"},
                "role": {"py_type": "str"}, 
                "timestamp": {"py_type": "str"},
                "metadata": {"py_type": "dict"}
            }
        }

        try:
            return await Soul.create(message_genotype, alias="lux_message")
        except Exception as e:
            print(f"Error creating lux_message soul: {e}")
            raise

    async def save_message_as_being(
        self, 
        content: str,
        role: str = "user",
        author_ulid: Optional[str] = None,
        fingerprint: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> 'Being':
        """Zapisuje wiadomość jako Being + tworzy relacje osobno"""

        # Pobierz Soul dla wiadomości
        message_soul = await self._get_or_create_message_soul()

        # Dane wiadomości
        message_data = {
            "content": content,
            "role": role,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        # Utwórz Being dla wiadomości
        message_being = await Being.create(message_soul, message_data)

        # Utwórz relacje osobno (nie w Being!)
        if author_ulid:
            await Relationship.create(
                source_ulid=author_ulid,
                target_ulid=message_being.ulid,
                relation_type="authored",
                strength=1.0,
                metadata={"description": f"Author {author_ulid} wrote message"}
            )

        if fingerprint:
            await Relationship.create(
                source_ulid=fingerprint,  # fingerprint jako source
                target_ulid=message_being.ulid,
                relation_type="browser_session",
                strength=1.0,
                metadata={"description": f"Browser session {fingerprint} created message"}
            )

        return message_being

    async def get_conversation_history(self, fingerprint: str, limit: int = 10) -> List['Being']:
        """Pobiera historię konwersacji przez relacje"""

        # Znajdź wszystkie relacje dla tego fingerprint
        all_relationships = await Relationship.get_all()
        message_ulids = []

        for rel in all_relationships:
            if (rel.source_ulid == fingerprint and 
                rel.relation_type == "browser_session"):
                message_ulids.append(rel.target_ulid)

        # Pobierz wiadomości jako Being
        messages = []
        # Weź tylko ostatnie 'limit' wiadomości
        for message_ulid in message_ulids[-limit:]:
            try:
                being = await Being.load_by_ulid(message_ulid)  
                if being and getattr(being, 'role', None):  # Sprawdź czy to wiadomość i ma rolę
                    messages.append(being)
            except Exception as e:
                print(f"Error loading being with ulid {message_ulid}: {e}")

        # Sortuj chronologicznie
        messages.sort(key=lambda m: getattr(m, 'timestamp', ''), reverse=False)
        return messages

    async def generate_lux_response(self, user_message: str, fingerprint: str) -> str:
        """Generuje odpowiedź asystenta Lux"""

        # Pobierz historię konwersacji
        history = await self.get_conversation_history(fingerprint, limit=5)

        # Przygotuj kontekst dla GPT
        context_messages = []
        for msg in history:
            role = getattr(msg, 'role', 'user')
            content = getattr(msg, 'content', '')
            if content: # Dodaj tylko jeśli jest treść
                context_messages.append({"role": role, "content": content})

        # Dodaj nową wiadomość użytkownika
        if user_message:
            context_messages.append({"role": "user", "content": user_message})

        # System prompt dla Lux
        system_prompt = """Jesteś Lux - asystentem AI projektu LuxOS/Luxunda. 
        Pomagasz inwestorom, współpracownikom i osobom zainteresowanym poznać projekt.

        Odpowiadaj w języku polskim, bądź pomocny i profesjonalny.
        Jeśli ktoś pyta o szczegóły techniczne - wyjaśnij system bytów (Being) i dusz (Soul).
        Jeśli ktoś jest inwestorem - skup się na potencjale biznesowym.
        Jeśli ktoś chce współpracować - zapytaj o umiejętności i zaproponuj role."""

        try:
            # Wywołaj OpenAI API (lub mock)
            if openai.api_key != "test-key":
                response = await openai.ChatCompletion.acreate(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        *context_messages
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content
            else:
                # Mock response dla demo
                return f"Cześć! Jestem Lux 🤖 Widzę, że napisałeś: '{user_message}'. To fascynujące pytanie o LuxOS - system gdzie każdy element to Being z własną duszą (Soul). Czy chciałbyś dowiedzieć się więcej o naszej technologii, inwestycjach czy współpracy?"

        except Exception as e:
            print(f"Error generating response: {e}")
            return "Przepraszam, wystąpił problem z generowaniem odpowiedzi. Spróbuj ponownie."

    async def handle_message(self, websocket: WebSocket, data: dict):
        """Obsługuje wiadomości WebSocket"""
        try:
            message_type = data.get("type")

            if message_type == "user_message":
                content = data.get("content", "")
                fingerprint = data.get("fingerprint", "")

                # Zapisz wiadomość użytkownika jako Being
                await self.save_message_as_being(
                    content=content,
                    role="user", 
                    fingerprint=fingerprint,
                    metadata={"source": "websocket", "ip": "demo"}
                )

                # Generuj odpowiedź asystenta
                response = await self.generate_lux_response(content, fingerprint)

                # Zapisz odpowiedź asystenta jako Being
                assistant_author_ulid = self.lux_assistant_soul.ulid if self.lux_assistant_soul else None
                await self.save_message_as_being(
                    content=response,
                    role="assistant",
                    author_ulid=assistant_author_ulid,
                    fingerprint=fingerprint,
                    metadata={"source": "lux_assistant"}
                )

                # Wyślij odpowiedź
                await websocket.send_text(json.dumps({
                    "type": "assistant_response",
                    "content": response,
                    "timestamp": datetime.now().isoformat()
                }))
            elif message_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

        except WebSocketDisconnect:
            print(f"🔌 Client disconnected")
            raise # Rzuć wyjątek, aby obsługiwać disconnect w głównym bloku try-except
        except Exception as e:
            print(f"Error handling message: {e}")
            try:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"Error: {str(e)}"
                }))
            except Exception as send_e:
                print(f"Could not send error message back to client: {send_e}")


# Globalna instancja systemu
lux_system = LuxOnboardingSystem()

@app.on_event("startup")
async def startup_event():
    await lux_system.initialize()

@app.get("/", response_class=HTMLResponse)
async def get_landing():
    return FileResponse("static/luxunda_landing.html")

@app.get("/onboarding", response_class=HTMLResponse) 
async def get_onboarding():
    return FileResponse("static/lux_onboarding.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connection_id = f"conn_{len(lux_system.connections)}"
    lux_system.connections[connection_id] = websocket
    print(f"✅ Connection {connection_id} established.")

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            await lux_system.handle_message(websocket, message_data)

    except WebSocketDisconnect:
        if connection_id in lux_system.connections:
            del lux_system.connections[connection_id]
        print(f"🔌 Connection {connection_id} disconnected.")
    except Exception as e:
        print(f"❌ WebSocket error for connection {connection_id}: {e}")
        if connection_id in lux_system.connections:
            del lux_system.connections[connection_id]

if __name__ == "__main__":
    print("🚀 Starting LuxOS Unified Onboarding Assistant...")
    print("📊 Serving investors, collaborators, and curious minds")  
    print("🌐 Interface: http://0.0.0.0:5000")
    uvicorn.run(app, host="0.0.0.0", port=5000)