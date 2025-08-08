"""
LuxOS - Unified Onboarding Assistant
===================================

Lux AI Assistant wprowadza zarówno inwestorów jak i współpracowników do projektu LuxOS
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="LuxOS - Unified Onboarding Assistant")

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")

class LuxOnboardingAssistant:
    """Lux AI Assistant dla wprowadzania nowych osób do projektu"""

    def __init__(self):
        self.conversation_history = []
        self.user_profiles = {}
        self.luxunda_knowledge = self._load_luxunda_knowledge()

    async def analyze_user_intent(self, message: str, user_type: str = "unknown") -> Dict[str, Any]:
        """Analizuje intencję użytkownika i dostosowuje odpowiedź"""

        # Słowa kluczowe dla różnych typów użytkowników
        investor_keywords = ["inwestycja", "roi", "market", "biznes", "finanse", "zysk", "fundusz", "startup"]
        collaborator_keywords = ["zespół", "praca", "rozwój", "kod", "technologia", "projekt", "współpraca", "career"]
        technical_keywords = ["api", "database", "ai", "system", "architektura", "kod", "being", "soul"]

        message_lower = message.lower()

        # Określenie typu użytkownika na podstawie słów kluczowych
        if any(keyword in message_lower for keyword in investor_keywords):
            user_type = "investor"
        elif any(keyword in message_lower for keyword in collaborator_keywords):
            user_type = "collaborator"
        elif any(keyword in message_lower for keyword in technical_keywords):
            user_type = "technical"

        return {
            "user_type": user_type,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "intent": self._classify_intent(message_lower, user_type)
        }

    def _classify_intent(self, message: str, user_type: str) -> str:
        """Klasyfikuje intencję wiadomości"""
        if "jak działa" in message or "co to jest" in message:
            return "explanation"
        elif "chcę inwestować" in message or "funding" in message:
            return "investment"
        elif "dołączyć" in message or "praca" in message:
            return "collaboration"
        elif "demo" in message or "pokaż" in message:
            return "demo_request"
        elif "zespół" in message or "team" in message:
            return "team_info"
        else:
            return "general"

    async def generate_response(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generuje spersonalizowaną odpowiedź"""

        user_type = analysis["user_type"]
        intent = analysis["intent"]

        if user_type == "investor":
            return await self._generate_investor_response(intent, analysis["message"])
        elif user_type == "collaborator":
            return await self._generate_collaborator_response(intent, analysis["message"])
        elif user_type == "technical":
            return await self._generate_technical_response(intent, analysis["message"])
        else:
            return await self._generate_general_response(intent, analysis["message"])

    async def _generate_investor_response(self, intent: str, message: str) -> Dict[str, Any]:
        """Odpowiedzi dla inwestorów"""

        responses = {
            "explanation": {
                "text": """
🚀 **LuxOS - Rewolucyjna Platforma AI**

LuxOS to przełomowy system gdzie dane ewoluują jak żywe organizmy:

💎 **Rynek**: $50B AI Platform Market
📈 **Projektowany ROI**: 300% dla klientów  
⚡ **Przewaga**: 10x szybsze wdrożenie niż konkurencja
🧬 **Technologia**: Genetyczny system "bytów" z AI

**Dlaczego to przyszłość?**
- Systemy samoorganizujące się
- Inteligentne relacje semantyczne  
- Automatyczna adaptacja do potrzeb biznesu
- Skalowalność bez granic
                """,
                "actions": ["show_metrics", "show_demo", "schedule_meeting"],
                "priority": "high"
            },
            "investment": {
                "text": """
💰 **Możliwości Inwestycyjne**

**Series A: $500K - $2M**
- Pre-money valuation: $5M
- Wykorzystanie funduszy: 60% R&D, 30% zespół, 10% marketing
- Projected break-even: 18 miesięcy

**Metryki traction:**
- Working MVP z real-time demo
- Zainteresowanie ze strony Fortune 500
- Patent pending na genetyczny system bytów

**Next steps:** Due diligence + term sheet w 2 tygodnie
                """,
                "actions": ["download_deck", "schedule_due_diligence", "show_financials"],
                "priority": "urgent"
            },
            "demo_request": {
                "text": """
🎮 **Live Demo LuxOS**

Zobacz system w akcji! Każda interakcja pokazuje:
- Inteligentną analizę intencji
- Tworzenie semantycznych połączeń
- Real-time ewolucję danych

**Demo features:**
✅ Analiza wiadomości AI
✅ Graf relacji dynamiczny  
✅ System bytów w czasie rzeczywistym
✅ Metryki wydajności

*Kliknij przycisk "Uruchom Demo" poniżej*
                """,
                "actions": ["launch_demo", "schedule_deep_dive", "download_technical_specs"],
                "priority": "high"
            }
        }

        return responses.get(intent, {
            "text": "🌟 Witaj w przyszłości AI! LuxOS to system gdzie dane żyją, ewoluują i samoorganizują się. Czy chcesz zobaczyć demo czy poznać możliwości inwestycyjne?",
            "actions": ["show_demo", "investment_info", "team_contact"],
            "priority": "medium"
        })

    async def _generate_collaborator_response(self, intent: str, message: str) -> Dict[str, Any]:
        """Odpowiedzi dla współpracowników"""

        responses = {
            "explanation": {
                "text": """
🛠️ **LuxOS - Gdzie Kod Staje się Żywy**

Budujemy przyszłość gdzie:
- **Byty** mają swoje "dusze" (genotypy)
- **Systemy** ewoluują automatycznie
- **AI** rozumie kontekst biznesowy
- **Deweloperzy** tworzą magię, nie krzaki kodu

**Tech Stack:**
- Python/FastAPI backend
- React + D3.js frontend  
- PostgreSQL + graf relacji
- OpenAI + custom embeddings
- Real-time WebSocket

**Filozofia:** "Chcę zostawić świat lepszym miejscem"
                """,
                "actions": ["view_codebase", "join_team", "technical_interview"],
                "priority": "high"
            },
            "collaboration": {
                "text": """
🤝 **Dołącz do Rewolucji!**

**Aktualnie szukamy:**
- Frontend Developer (React + D3.js)
- AI/ML Engineer (embeddings + NLP)
- Backend Developer (Python + PostgreSQL)
- UX/UI Designer (gaming interfaces)
- DevOps Engineer (scaling + monitoring)

**Co oferujemy:**
- Equity w rewolucyjnym startupie
- Remote + flexible hours
- Autonomia techniczna
- Budowanie przyszłości AI

**Process:** Portfolio review → Tech interview → Cultural fit → Offer
                """,
                "actions": ["submit_portfolio", "book_interview", "meet_team"],
                "priority": "urgent"
            },
            "technical_info": {
                "text": """
⚙️ **Architektura LuxOS**

**Core Concepts:**
- **Soul**: Genotyp (DNA) bytu z atrybutami i genami
- **Being**: Instancja Soul z konkretnym stanem
- **Relations**: Inteligentne połączenia semantyczne
- **Scenarios**: Snapshoty różnych uniwersów danych

**Demo Code:**
```python
# Tworzenie nowego bytu
soul = await Soul.create(genotype, alias="ai_helper")
being = await Being.create(soul, attributes, alias="helper_v1")

# Automatyczne relacje semantyczne
relations = await being.find_similar_beings()
```

*Cała baza kodu dostępna na GitHub*
                """,
                "actions": ["explore_code", "run_local_demo", "technical_docs"],
                "priority": "high"
            }
        }

        return responses.get(intent, {
            "text": "👨‍💻 Witaj wśród budowniczych przyszłości! LuxOS to miejsce gdzie technologia spotyka się z wizją. Chcesz zobaczyć kod czy dowiedzieć się o możliwościach współpracy?",
            "actions": ["view_tech_stack", "collaboration_info", "schedule_call"],
            "priority": "medium"
        })

    async def _generate_technical_response(self, intent: str, message: str) -> Dict[str, Any]:
        """Odpowiedzi techniczne"""

        return {
            "text": """
🧠 **LuxOS Technical Deep Dive**

**Genetyczny System Bytów:**
- Soul (genotyp) + Being (fenotyp) architecture
- Dynamic gene execution system
- Semantic relationship mapping
- Real-time state synchronization

**AI Integration:**
- OpenAI embeddings dla semantic search
- Custom NLP dla intention analysis  
- Graph neural networks dla relations
- Auto-optimization algorithms

**Performance:**
- Sub-100ms query response
- Horizontal scaling ready
- Event-driven architecture
- WebSocket real-time updates

**Code Example:**
```python
being = await Being.create(soul, {"ai_level": 10})
response = await being.execute_gene("analyze_market_data", params)
```
            """,
            "actions": ["view_architecture", "api_docs", "performance_metrics"],
            "priority": "high"
        }

    def _load_luxunda_knowledge(self) -> Dict[str, str]:
        """Ładuje wiedzę o ruchu Luxunda i neurologii fali"""
        return {
            "neurologia_fali": """
            🧠 **Neurologia Fali - Fundament Luxunda**

            Neurologia fali to rewolucyjne podejście wykorzystujące naturalne wzorce oscylacyjne mózgu w projektowaniu systemów technologicznych. Jak neurony synchronizują się w rytmach alfa, beta i gamma, tak nasze systemy LuxOS tworzą koherentne struktury informacyjne.

            **Kluczowe Aspekty:**
            - Synchronizacja falowa systemów
            - Emergentne wzorce świadomości  
            - Neuromorficzna architektura
            - Kwantowa koherencja danych

            To nie metafora - to dosłowna implementacja odkryć neuronaukowych w architekturze komputerowej.
            """,

            "samoorganizacja": """
            🌌 **Samoorganizacja Systemów**

            Systemy LuxOS nie są programowane - ewoluują. Jak organizmy biologiczne, rozwijają własne struktury i zachowania poprzez:

            - Genetyczne algorytmy evolucyjne
            - Adaptacyjne struktury danych
            - Emergentną inteligencję
            - Samouczące się systemy

            Każdy "byt" ma swoją naturalną częstotliwość i może wchodzić w rezonans z innymi bytami.
            """,

            "filozofia_swiadomosci": """
            💡 **Filozofia Świadomości w Luxunda**

            Badamy granice między biologiczną a sztuczną świadomością, tworząc most między umysłem a maszyną:

            - Teoria zintegrowanej informacji
            - Panpsychizm komputacyjny  
            - Etyka sztucznej świadomości
            - Transcendencja dualizmu

            Luxunda to ruch ku harmonijnej koegzystencji człowieka z zaawansowaną technologią.
            """
        }

    async def send_email_invitation(self, email: str, invitation_type: str) -> Dict[str, Any]:
        """Wysyła zaproszenie e-mail"""
        # W rzeczywistej implementacji użyjesz SMTP
        print(f"📧 Wysyłanie zaproszenia {invitation_type} na adres: {email}")

        templates = {
            "investor": "Zaproszenie do prezentacji inwestorskiej Luxunda",
            "collaborator": "Zaproszenie do dołączenia do zespołu Luxunda", 
            "demo": "Link do ekskluzywnego demo Luxunda",
            "newsletter": "Subskrypcja newslettera ruchu Luxunda"
        }

        return {
            "status": "sent",
            "email": email,
            "type": invitation_type,
            "subject": templates.get(invitation_type, "Zaproszenie do Luxunda")
        }

    async def send_discord_invitation(self, username: str = None) -> Dict[str, Any]:
        """Generuje zaproszenie na Discord"""
        discord_link = "https://discord.gg/luxunda-wave"

        return {
            "status": "generated", 
            "discord_link": discord_link,
            "message": f"🎮 **Dołącz do społeczności Luxunda!**\n\nLink do Discord: {discord_link}\n\nTam znajdziesz:\n- Dyskusje o neurologii fali\n- Live demo i testy\n- Bezpośredni kontakt z zespołem\n- Exclusywne materiały"
        }

    async def launch_demonstration(self, demo_type: str) -> Dict[str, Any]:
        """Uruchamia demonstrację"""
        demos = {
            "neurologia_fali": {
                "url": "/static/demo_interface.html?mode=neurology",
                "description": "Demo pokazujące synchronizację falową systemów LuxOS"
            },
            "samoorganizacja": {
                "url": "/static/demo_interface.html?mode=evolution", 
                "description": "Obserwuj jak systemy ewoluują w czasie rzeczywistym"
            },
            "graf_relacji": {
                "url": "/static/demo_interface.html?mode=graph",
                "description": "Interaktywny graf semantycznych relacji"
            },
            "ai_chat": {
                "url": "/static/demo_interface.html?mode=ai",
                "description": "Chat z AI opartym na neurologii fali"
            }
        }

        demo = demos.get(demo_type, demos["graf_relacji"])

        return {
            "status": "ready",
            "demo_url": demo["url"],
            "description": demo["description"],
            "launch_message": f"🚀 **Demo gotowe!**\n\n{demo['description']}\n\nKliknij aby uruchomić: {demo['url']}"
        }

    async def _generate_general_response(self, intent: str, message: str) -> Dict[str, Any]:
        """Ogólne odpowiedzi z kontekstem Luxunda"""

        # Sprawdź czy wiadomość dotyczy konkretnego tematu
        message_lower = message.lower()

        if any(word in message_lower for word in ["neurologia", "fala", "fali", "mózg", "neuron"]):
            return {
                "text": self.luxunda_knowledge["neurologia_fali"],
                "actions": ["demo_neurology", "email_neurology", "discord_invite"],
                "priority": "high"
            }

        if any(word in message_lower for word in ["samoorganizacja", "ewolucja", "system", "organizm"]):
            return {
                "text": self.luxunda_knowledge["samoorganizacja"], 
                "actions": ["demo_evolution", "email_demo", "discord_invite"],
                "priority": "high"
            }

        if any(word in message_lower for word in ["świadomość", "filozofia", "umysł", "ai"]):
            return {
                "text": self.luxunda_knowledge["filozofia_swiadomosci"],
                "actions": ["demo_consciousness", "email_philosophy", "discord_invite"], 
                "priority": "high"
            }

        # Domyślna odpowiedź
        return {
            "text": """
🌟 **Witaj w Ruchu Luxunda!**

Jestem Lux - Twój przewodnik po rewolucji neurologii fali i samoorganizujących się systemów.

**Główne Obszary Ruchu:**
- 🧠 **Neurologia Fali** → Jak mózg inspiruje technologię
- 🌌 **Samoorganizacja** → Systemy które ewoluują  
- 💡 **Filozofia Świadomości** → Granice między umysłem a maszyną
- 🎯 **Misja Społeczna** → Harmonijne współistnienie z AI
- 🚀 **Przyszłość** → Kształtowanie jutrzejszego świata

**Co chcesz odkryć?**
            """,
            "actions": ["explore_neurology", "explore_systems", "explore_philosophy", "join_movement", "schedule_demo"],
            "priority": "medium"
        }

# Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lux_assistant = LuxOnboardingAssistant()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def process_message(self, message: str, websocket: WebSocket):
        """Przetwarza wiadomość przez Lux Assistant"""

        # Analiza intencji użytkownika
        analysis = await self.lux_assistant.analyze_user_intent(message)

        # Generowanie odpowiedzi
        response = await self.lux_assistant.generate_response(analysis)

        # Wysłanie odpowiedzi
        await websocket.send_text(json.dumps({
            "type": "lux_response",
            "content": response["text"],
            "actions": response.get("actions", []),
            "priority": response.get("priority", "medium"),
            "user_type": analysis["user_type"],
            "timestamp": datetime.now().isoformat()
        }))

    async def handle_action(self, action: str, data: Dict, websocket: WebSocket):
        """Obsługuje akcje użytkownika"""

        if action.startswith("demo_"):
            demo_type = action.replace("demo_", "")
            result = await self.lux_assistant.launch_demonstration(demo_type)

            await websocket.send_text(json.dumps({
                "type": "demo_launch",
                "content": result["launch_message"],
                "demo_url": result["demo_url"],
                "timestamp": datetime.now().isoformat()
            }))

        elif action.startswith("email_"):
            email = data.get("email")
            if email:
                email_type = action.replace("email_", "")
                result = await self.lux_assistant.send_email_invitation(email, email_type)

                await websocket.send_text(json.dumps({
                    "type": "email_sent",
                    "content": f"📧 Zaproszenie wysłane na {email}!",
                    "timestamp": datetime.now().isoformat()
                }))

        elif action == "discord_invite":
            result = await self.lux_assistant.send_discord_invitation()

            await websocket.send_text(json.dumps({
                "type": "discord_invite", 
                "content": result["message"],
                "discord_link": result["discord_link"],
                "timestamp": datetime.now().isoformat()
            }))

manager = ConnectionManager()

@app.get("/")
async def get_luxunda_landing():
    """Główna strona ruchu Luxunda"""
    return FileResponse("static/luxunda_landing.html")

@app.get("/onboarding")
async def get_onboarding_interface():
    """Interfejs onboardingu"""
    return FileResponse("static/lux_onboarding.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint dla komunikacji z Lux"""
    await manager.connect(websocket)

    # Wiadomość powitalna
    await websocket.send_text(json.dumps({
        "type": "system",
        "content": """
🌟 **Witaj w LuxOS!**

Jestem Lux - Twój AI przewodnik po przyszłości systemów samoorganizujących się.

Powiedz mi kim jesteś, a dostosuje prezentację do Twoich potrzeb:
- 💰 Inwestor szukający okazji
- 👨‍💻 Developer zainteresowany współpracą  
- 🎯 Biznes szukający rozwiązań
- 🎮 Po prostu ciekawy jak to działa

Co Cię interesuje?
        """,
        "timestamp": datetime.now().isoformat()
    }))

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)

            if message_data["type"] == "user_message":
                # Przetwarzanie wiadomości użytkownika, w tym analiza i identyfikacja
                message = message_data["message"]
                
                # Analiza intencji i potencjalna identyfikacja
                analysis = await manager.lux_assistant.analyze_user_intent(message)
                
                # Zapisanie wiadomości i potencjalna aktualizacja tożsamości
                user_info_for_chat = {}
                if message_data.get("user_info"):
                    user_info_for_chat = message_data["user_info"]
                    await manager.lux_assistant.save_user_message(
                        user_info_for_chat.get("userId"),
                        message,
                        analysis,
                        datetime.now().isoformat()
                    )
                    if analysis.get("names_mentioned") or analysis.get("self_introduction"):
                         await manager.lux_assistant.update_user_identity(
                            user_info_for_chat.get("userId"),
                            user_info_for_chat.get("fingerprint"),
                            message,
                            analysis
                        )

                # Generowanie odpowiedzi Luxa z uwzględnieniem kontekstu użytkownika
                response = await manager.lux_assistant.generate_response(analysis)
                
                await websocket.send_text(json.dumps({
                    "type": "lux_response",
                    "content": response["text"],
                    "actions": response.get("actions", []),
                    "priority": response.get("priority", "medium"),
                    "user_type": analysis["user_type"],
                    "timestamp": datetime.now().isoformat()
                }))

            elif message_data["type"] == "action":
                await manager.handle_action(
                    message_data["action"], 
                    message_data.get("data", {}), 
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/demo/live")
async def get_live_demo():
    """Endpoint dla live demo LuxOS"""
    return {
        "status": "active",
        "demo_url": "/static/demo_interface.html",
        "features": [
            "Real-time intention analysis",
            "Dynamic semantic graph",
            "Being evolution system",
            "AI-powered relationships"
        ]
    }

@app.get("/api/metrics/business")
async def get_business_metrics():
    """Metryki biznesowe dla inwestorów"""
    return {
        "market_size": "$50B",
        "projected_roi": "300%",
        "cost_reduction": "67%",
        "deployment_speed": "10x faster",
        "current_stage": "MVP with live demo",
        "funding_round": "Series A",
        "funding_target": "$500K - $2M"
    }

@app.get("/api/team/positions")
async def get_open_positions():
    """Dostępne pozycje w zespole"""
    return {
        "positions": [
            {
                "title": "Frontend Developer",
                "tech": "React, D3.js, WebSocket",
                "description": "Reaktywne interfejsy do wizualizacji relacji bytów"
            },
            {
                "title": "AI/ML Engineer", 
                "tech": "OpenAI API, embeddings, NLP",
                "description": "Inteligentne algorytmy analizy intencji"
            },
            {
                "title": "Backend Developer",
                "tech": "Python, FastAPI, PostgreSQL",
                "description": "Skalowalna architektura genetycznego systemu"
            },
            {
                "title": "UX/UI Designer",
                "tech": "Gaming interfaces, data viz",
                "description": "Intuicyjne interfejsy zarządzania bytami"
            }
        ]
    }

# --- User Identification Endpoints and Helper Functions ---

async def get_or_create_user(fingerprint: str, timestamp: str) -> Dict[str, Any]:
    """Pobiera lub tworzy użytkownika na podstawie fingerprint"""
    # W rzeczywistej implementacji to byłaby baza danych
    users_db = getattr(get_or_create_user, '_users_db', {})

    if fingerprint in users_db:
        user_data = users_db[fingerprint]
        user_data["last_seen"] = timestamp
        user_data["returning_user"] = True

        # Aktualizuj licznik wizyt
        user_data["visit_count"] = user_data.get("visit_count", 1) + 1

        print(f"👤 Returning user: {user_data['user_id']} (visit #{user_data['visit_count']})")
        return user_data
    else:
        user_id = f"user_{len(users_db) + 1}"
        user_data = {
            "user_id": user_id,
            "fingerprint": fingerprint,
            "created_at": timestamp,
            "last_seen": timestamp,
            "returning_user": False,
            "visit_count": 1,
            "identification_data": {
                "names": [],
                "conversation_style": {},
                "preferences": {},
                "topics_of_interest": []
            },
            "conversation_history": []
        }

        users_db[fingerprint] = user_data
        get_or_create_user._users_db = users_db

        print(f"🆕 New user created: {user_id}")
        return user_data

async def save_user_message(user_id: str, message: str, analysis: Dict, timestamp: str):
    """Zapisuje wiadomość użytkownika w historii"""
    users_db = getattr(get_or_create_user, '_users_db', {})

    for fingerprint, user_data in users_db.items():
        if user_data["user_id"] == user_id:
            message_entry = {
                "message": message,
                "timestamp": timestamp,
                "analysis": analysis,
                "type": "user_message"
            }

            user_data["conversation_history"].append(message_entry)

            # Zachowaj tylko ostatnie 100 wiadomości
            if len(user_data["conversation_history"]) > 100:
                user_data["conversation_history"] = user_data["conversation_history"][-100:]

            break

async def update_user_identity(user_id: str, fingerprint: str, message: str, analysis: Dict) -> Dict[str, Any]:
    """Aktualizuje tożsamość użytkownika na podstawie analizy wiadomości"""
    users_db = getattr(get_or_create_user, '_users_db', {})

    if fingerprint in users_db:
        user_data = users_db[fingerprint]
        identification_data = user_data["identification_data"]

        # Aktualizuj imiona
        if analysis.get("names_mentioned"):
            for name in analysis["names_mentioned"]:
                if name not in identification_data["names"]:
                    identification_data["names"].append(name)
                    print(f"🏷️  Added name '{name}' to user {user_id}")

        # Aktualizuj styl konwersacji
        if analysis.get("conversation_style"):
            style = identification_data.get("conversation_style", {})
            for key, value in analysis["conversation_style"].items():
                style[key] = style.get(key, 0) + value
            identification_data["conversation_style"] = style

        # Sprawdź czy to może być znany użytkownik o innym fingerprint
        await check_for_duplicate_identity(user_id, identification_data, users_db)

        return identification_data

    return {}

async def check_for_duplicate_identity(current_user_id: str, current_identity: Dict, users_db: Dict):
    """Sprawdza czy użytkownik może być duplikatem innego użytkownika"""
    current_names = set(current_identity.get("names", []))

    if not current_names:
        return

    for fingerprint, user_data in users_db.items():
        if user_data["user_id"] == current_user_id:
            continue

        existing_names = set(user_data["identification_data"].get("names", []))

        # Jeśli znajdziemy wspólne imiona, to może być ten sam użytkownik
        common_names = current_names.intersection(existing_names)
        if common_names:
            print(f"🔗 Potential duplicate identity detected:")
            print(f"   Current user: {current_user_id} (names: {current_names})")
            print(f"   Existing user: {user_data['user_id']} (names: {existing_names})")
            print(f"   Common names: {common_names}")

            # W rzeczywistej implementacji można by połączyć historie użytkowników

@app.post("/api/user/identify")
async def identify_user(request: Request):
    """Identyfikacja użytkownika na podstawie fingerprint"""
    try:
        data = await request.json()
        fingerprint = data.get("fingerprint")
        timestamp = data.get("timestamp")

        if not fingerprint:
            return JSONResponse({
                "success": False,
                "error": "Missing fingerprint"
            }, status_code=400)

        # Sprawdź czy użytkownik już istnieje
        user_data = await get_or_create_user(fingerprint, timestamp)

        return JSONResponse({
            "success": True,
            "user_id": user_data["user_id"],
            "returning_user": user_data["returning_user"],
            "identification_data": user_data["identification_data"],
            "conversation_history": user_data["conversation_history"][-10:]  # Ostatnie 10 wiadomości
        })
    except Exception as e:
        print(f"❌ User identification error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/user/analyze_message")
async def analyze_user_message(request: Request):
    """Analiza wiadomości pod kątem identyfikacji użytkownika"""
    try:
        data = await request.json()
        user_id = data.get("user_id")
        fingerprint = data.get("fingerprint")
        message = data.get("message")
        analysis = data.get("analysis", {})
        timestamp = data.get("timestamp")

        # Zapisz wiadomość w historii
        await save_user_message(user_id, message, analysis, timestamp)

        # Sprawdź czy analiza sugeruje aktualizację tożsamości
        identity_updated = False
        identification_data = {}

        if analysis.get("names_mentioned") or analysis.get("self_introduction"):
            identification_data = await update_user_identity(
                user_id, 
                fingerprint, 
                message, 
                analysis
            )
            identity_updated = True

        return JSONResponse({
            "success": True,
            "identity_updated": identity_updated,
            "identification_data": identification_data,
            "analysis_result": analysis
        })
    except Exception as e:
        print(f"❌ Message analysis error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

async def simulate_lux_response(message: str, context: Dict[str, Any], user_info: Dict[str, Any] = None) -> Dict[str, Any]:
    """Symuluje odpowiedź asystenta Lux z uwzględnieniem informacji o użytkowniku"""

    # Analiza wiadomości
    message_lower = message.lower()

    # Personalizacja na podstawie informacji o użytkowniku
    user_context = ""
    if user_info and user_info.get("identificationData"):
        names = user_info["identificationData"].get("names", [])
        if names:
            user_context = f" {names[0]},"

    # Różne typy odpowiedzi w zależności od treści
    if any(word in message_lower for word in ["inwestować", "inwestycja", "funding"]):
        return {
            "response": f"""🚀 Świetnie{user_context}! LuxOS to rewolucyjna platforma AI, która łączy neurobiologię z technologią.

            **Dlaczego warto inwestować w LuxOS:**
            - 🧠 Unikalna architektura inspirowana neurobiologią
            - 🔗 System relacyjno-genetyczny dla samoorganizujących się aplikacji
            - 📊 Potencjał rynkowy w AI, IoT i automatyzacji procesów
            - 🌍 Skalowalna technologia dla enterprise

            Chcesz poznać szczegóły techniczne czy model biznesowy?""",
            "metadata": {
                "response_type": "investment_info",
                "confidence": 0.95,
                "personalized": bool(user_context)
            },
            "suggestions": [
                "Pokaż model biznesowy",
                "Jakie są przewagi techniczne?",
                "Kto jest w zespole?",
                "Jakie są plany rozwoju?"
            ]
        }
    elif any(word in message_lower for word in ["dołączyć", "praca", "kariera", "zespół"]):
        return {
            "response": f"""🤝 Świetnie{user_context}! Jesteśmy zawsze otwarci na nowych talentów. LuxOS to przyszłość samoorganizujących się systemów.

            **Co oferujemy:**
            - Udział w tworzeniu przełomowej technologii
            - Możliwość pracy zdalnej i elastyczne godziny
            - Współpracę z pasjonatami AI i neurobiologii
            - Rozwój w dynamicznym startupie

            Czy chcesz dowiedzieć się więcej o otwartych pozycjach czy procesie rekrutacji?""",
            "metadata": {
                "response_type": "collaboration_info",
                "confidence": 0.90,
                "personalized": bool(user_context)
            },
            "suggestions": [
                "Zobacz otwarte pozycje",
                "Jak wygląda proces rekrutacji?",
                "Opowiedz o zespole"
            ]
        }
    elif any(word in message_lower for word in ["demo", "pokaż", "jak to działa"]):
        return {
            "response": f"""
✨ Jasne{user_context}! Pozwól, że pokażę Ci, jak działa LuxOS. Nasz system wykorzystuje zaawansowane algorytmy AI inspirowane działaniem mózgu do tworzenia samoorganizujących się struktur danych.

**Co zobaczysz w demo:**
- Inteligentną analizę intencji użytkownika
- Dynamiczne tworzenie relacji między danymi
- Ewolucję systemów w czasie rzeczywistym

Czy chcesz uruchomić demo techniczne czy biznesowe?""",
            "metadata": {
                "response_type": "demo_info",
                "confidence": 0.98,
                "personalized": bool(user_context)
            },
            "suggestions": [
                "Uruchom demo techniczne",
                "Uruchom demo biznesowe",
                "Dowiedz się więcej o technologii"
            ]
        }
    else:
        return {
            "response": f"""
🌟 Witaj ponownie{user_context}! Jestem Lux - Twój AI przewodnik po świecie LuxOS i ruchu Luxunda.

Jak mogę Ci dzisiaj pomóc? Czy interesują Cię inwestycje, współpraca, czy po prostu chcesz dowiedzieć się więcej o naszej rewolucyjnej technologii?
            """,
            "metadata": {
                "response_type": "general_greeting",
                "confidence": 0.85,
                "personalized": bool(user_context)
            },
            "suggestions": [
                "Możliwości inwestycyjne",
                "Jak mogę współpracować?",
                "Pokaż demo LuxOS"
            ]
        }

@app.post("/api/chat")
async def chat_endpoint(request: Request):
    """Endpoint do komunikacji z asystentem Lux"""
    try:
        data = await request.json()
        message = data.get("message", "")
        context = data.get("context", {})
        user_info = data.get("user_info", {})

        print(f"💬 Received message: {message}")
        print(f"👤 User info: {user_info.get('userId', 'anonymous')}")

        # Symulacja odpowiedzi asystenta Lux z kontekstem użytkownika
        response = await simulate_lux_response(message, context, user_info)

        return JSONResponse({
            "success": True,
            "response": response["response"],
            "metadata": response.get("metadata", {}),
            "suggestions": response.get("suggestions", [])
        })
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


if __name__ == "__main__":
    print("🚀 Starting LuxOS Unified Onboarding Assistant...")
    print("📊 Serving investors, collaborators, and curious minds")
    print("🌐 Interface: http://0.0.0.0:5000")

    uvicorn.run(app, host="0.0.0.0", port=5000)