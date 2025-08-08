
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
                await manager.process_message(message_data["message"], websocket)
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

if __name__ == "__main__":
    print("🚀 Starting LuxOS Unified Onboarding Assistant...")
    print("📊 Serving investors, collaborators, and curious minds")
    print("🌐 Interface: http://0.0.0.0:5000")
    
    uvicorn.run(app, host="0.0.0.0", port=5000)
