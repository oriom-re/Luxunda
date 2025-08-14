"""
Lux AI Assistant - Conversational AI that manages beings, tools and knowledge
"""

import asyncio
import json
import time
import ulid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import openai
# Embedding będzie obsłużony przez OpenAI bezpośrednio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.repository.soul_repository import BeingRepository

class LuxAssistant:
    """Revolutionary AI Assistant that manages beings, tools and knowledge"""

    def __init__(self, openai_api_key: str = None):
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY', 'demo-key')
        self.client = None
        self.is_initialized = False
        self.using_demo_mode = self.openai_api_key == 'demo-key'

        # Status i statystyki
        self.conversation_count = 0
        self.last_response_time = None
        self.error_count = 0

        # Self-Session Management
        self.session_id = str(ulid.ulid())
        self.session_manager = None
        self.self_being = None  # Lux jako Being w swojej sesji

    async def initialize(self):
        """Inicjalizuje asystenta AI"""
        if self.is_initialized:
            return

        try:
            # Inicjalizacja OpenAI (jeśli dostępny)
            if not self.using_demo_mode:
                import openai
                self.client = openai.AsyncOpenAI(api_key=self.openai_api_key)

                # Test połączenia
                try:
                    await self.client.models.list()
                    print("✅ OpenAI connection successful")
                except Exception as e:
                    print(f"⚠️ OpenAI connection failed, switching to demo mode: {e}")
                    self.using_demo_mode = True
                    self.client = None

            # Self-Session Initialization
            await self._initialize_self_session()

            self.is_initialized = True
            print(f"🌟 Lux AI Assistant initialized! (Demo mode: {self.using_demo_mode})")
            print(f"📋 Self-session ID: {self.session_id}")

        except Exception as e:
            print(f"❌ Failed to initialize Lux Assistant: {e}")
            self.using_demo_mode = True
            self.is_initialized = True

    async def _initialize_self_session(self):
        """Inicjalizuje własną sesję dla Lux"""
        from .core.session_data_manager import global_session_registry
        from .models.soul import Soul
        from .models.being import Being

        # Uzyskaj session manager dla tej instancji Lux
        self.session_manager = await global_session_registry.get_session_manager(self.session_id)

        print(f"🧠 Initializing self-session for Lux: {self.session_id}")

        # Utwórz genotyp dla Lux Being
        lux_genotype = {
            "genesis": {
                "name": f"lux_assistant_{self.session_id}",
                "type": "lux_assistant", 
                "version": "1.0.0",
                "description": f"Self-contained Lux Assistant with session {self.session_id}"
            },
            "attributes": {
                "session_id": {"py_type": "str"},
                "conversation_history": {"py_type": "List[dict]"},
                "performance_stats": {"py_type": "dict"},
                "preferences": {"py_type": "dict"},
                "memory_cache": {"py_type": "dict"}
            }
        }

        # Utwórz Soul dla Lux
        lux_soul = await Soul.create(lux_genotype, alias=f"lux_soul_{self.session_id}")

        # Utwórz Being reprezentujący tę instancję Lux w sesji
        self.self_being = await self.session_manager.create_being_safe(
            lux_soul,
            {
                "session_id": self.session_id,
                "conversation_history": [],
                "performance_stats": {
                    "conversations": 0,
                    "errors": 0,
                    "avg_response_time": 0
                },
                "preferences": {
                    "demo_mode": self.using_demo_mode,
                    "openai_available": not self.using_demo_mode
                },
                "memory_cache": {}
            },
            alias=f"lux_instance_{self.session_id}"
        )

        print(f"🎯 Lux self-being created: {self.self_being.ulid}")

    async def _update_self_stats(self, response_time: float, success: bool):
        """Aktualizuje statystyki w self-being"""
        if not self.self_being:
            return

        stats = self.self_being.data.get('performance_stats', {})
        stats['conversations'] = stats.get('conversations', 0) + 1

        if not success:
            stats['errors'] = stats.get('errors', 0) + 1

        # Aktualizuj średni czas odpowiedzi
        current_avg = stats.get('avg_response_time', 0)
        total_conversations = stats['conversations']
        stats['avg_response_time'] = ((current_avg * (total_conversations - 1)) + response_time) / total_conversations

        self.self_being.data['performance_stats'] = stats
        self.self_being.data['last_activity'] = datetime.now().isoformat()

        # Zapisz zmiany przez session manager
        await self.session_manager.sync_changes()

    async def _store_conversation_in_session(self, user_message: str, response: str):
        """Przechowuje konwersację w session data"""
        if not self.self_being:
            return

        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": user_message[:200],  # Limit długości
            "response": response[:500],
            "response_length": len(response)
        }

        history = self.self_being.data.get('conversation_history', [])
        history.append(conversation_entry)

        # Zachowaj tylko ostatnie 50 konwersacji
        if len(history) > 50:
            history = history[-50:]

        self.self_being.data['conversation_history'] = history

    def get_session_summary(self) -> Dict[str, Any]:
        """Zwraca podsumowanie sesji Lux"""
        if not self.session_manager or not self.self_being:
            return {"error": "Session not initialized"}

        session_info = self.session_manager.get_session_summary()
        being_stats = self.self_being.data.get('performance_stats', {})

        return {
            "lux_session_id": self.session_id,
            "lux_being_id": self.self_being.ulid,
            "session_stats": session_info,
            "performance": being_stats,
            "conversation_count": len(self.self_being.data.get('conversation_history', [])),
            "demo_mode": self.using_demo_mode,
            "cache_stats": {
                "hits": self.session_manager.cache_hits,
                "misses": self.session_manager.cache_misses
            }
        }

    async def chat(self, message: str, conversation_history: List[Dict] = None) -> str:
        """
        Główna metoda do rozmowy z asystentem

        Args:
            message: Wiadomość użytkownika
            conversation_history: Historia konwersacji

        Returns:
            Odpowiedź asystenta
        """
        start_time = time.time()
        success = True

        try:
            self.conversation_count += 1

            if not self.using_demo_mode and self.client:
                # Użyj prawdziwego OpenAI
                response = await self._chat_with_openai(message, conversation_history)
            else:
                # Tryb demo
                response = await self._chat_demo_mode(message)

            response_time = time.time() - start_time
            self.last_response_time = response_time

            # Przechowaj konwersację w self-session
            await self._store_conversation_in_session(message, response)
            await self._update_self_stats(response_time, success)

            return response

        except Exception as e:
            success = False
            self.error_count += 1
            response_time = time.time() - start_time
            await self._update_self_stats(response_time, success)
            return f"Przepraszam, wystąpił błąd: {str(e)}"

    async def analyze_user_request(self, message: str) -> Dict[str, Any]:
        """Analyze user intent using OpenAI"""
        prompt = f"""
        Analyze this user message and determine their intent:
        "{message}"

        Return JSON with:
        - intent: "create_tool", "note", "search", "general"
        - description: what they want to do
        - keywords: key terms for search
        - complexity: 1-10 scale
        """

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"❌ Analysis error: {e}")
            return {
                "intent": "general", 
                "description": message,
                "keywords": message.split(),
                "complexity": 5
            }

    async def handle_tool_creation(self, analysis: Dict[str, Any]) -> str:
        """Handle tool/being creation request"""
        # Search for existing similar tools
        existing_tools = await self.search_similar_tools(analysis["keywords"])

        if existing_tools:
            tools_info = "\n".join([f"- {tool['name']}: {tool['description']}" for tool in existing_tools[:3]])

            suggestion_prompt = f"""
            User wants: {analysis["description"]}

            Found similar existing tools:
            {tools_info}

            Should I:
            1. Use existing tool
            2. Modify existing tool  
            3. Create completely new tool

            Provide recommendation and code if needed.
            """

            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": suggestion_prompt}],
                max_tokens=800
            )

            return f"🔍 Found similar tools!\n\n{response.choices[0].message.content}"

        else:
            # Create new tool/being
            new_tool = await self.create_new_tool(analysis)
            return f"✨ Created new tool: {new_tool['name']}!\n\n{new_tool['description']}"

    async def search_similar_tools(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """Search for similar tools using embeddings"""
        search_query = " ".join(keywords)
        # Tymczasowo używamy prostego wyszukiwania tekstowego
        query_embedding = []

        # Load all beings and their embeddings
        all_beings = await Being.load_all()
        similar_tools = []

        for being in all_beings:
            if hasattr(being, 'knowledge_embeddings') and being.knowledge_embeddings:
                similarity = self.cosine_similarity(query_embedding, being.knowledge_embeddings)
                if similarity > 0.7:  # High similarity threshold
                    similar_tools.append({
                        "name": being.alias or being.ulid[:8],
                        "description": being.genotype.get("genesis", {}).get("description", "No description"),
                        "similarity": similarity,
                        "being": being
                    })

        return sorted(similar_tools, key=lambda x: x["similarity"], reverse=True)

    async def create_new_tool(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create new tool/being based on analysis"""
        tool_name = f"tool_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Generate genotype using AI
        genotype_prompt = f"""
        Create a genotype for a tool that: {analysis["description"]}
        Keywords: {analysis["keywords"]}

        Return JSON genotype with genesis, attributes, and genes.
        Make it functional and specific to the user's needs.
        """

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[{"role": "user", "content": genotype_prompt}],
            max_tokens=600
        )

        try:
            genotype = json.loads(response.choices[0].message.content)

            # Create embeddings for the tool  
            description = genotype.get("genesis", {}).get("description", analysis["description"])
            embeddings = []  # Tymczasowo pusta lista

            # Create soul and being
            soul = await Soul.create(genotype, alias=tool_name)
            being = await Being.create(
                soul,
                {"knowledge_embeddings": embeddings},
                alias=tool_name
            )

            return {
                "name": tool_name,
                "description": description,
                "being_ulid": being.ulid,
                "genotype": genotype
            }

        except Exception as e:
            print(f"❌ Tool creation error: {e}")
            return {
                "name": "error_tool",
                "description": f"Failed to create tool: {e}",
                "being_ulid": None,
                "genotype": {}
            }

    async def handle_note_creation(self, analysis: Dict[str, Any]) -> str:
        """Handle note creation and storage"""
        note_genotype = {
            "genesis": {
                "name": "daily_note",
                "type": "note",
                "description": analysis["description"]
            },
            "attributes": {
                "content": {"py_type": "str"},
                "tags": {"py_type": "List[str]"},
                "date_created": {"py_type": "str"},
                "embeddings": {"py_type": "List[float]"}
            }
        }

        # Generate embeddings for the note
        embeddings = []  # Tymczasowo pusta lista

        soul = await Soul.create(note_genotype, alias="daily_note")
        note_being = await Being.create(
            soul,
            {
                "content": analysis["description"],
                "tags": analysis["keywords"],
                "date_created": datetime.now().isoformat(),
                "embeddings": embeddings
            },
            alias=f"note_{datetime.now().strftime('%Y%m%d')}"
        )

        return f"📝 Note saved! ULID: {note_being.ulid[:12]}"

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(a * a for a in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    async def handle_search(self, analysis: Dict[str, Any]) -> str:
        """Handle search requests"""
        results = await self.search_similar_tools(analysis["keywords"])

        if not results:
            return "🔍 No similar tools found. Want me to create one?"

        response = "🔍 Found these tools:\n\n"
        for i, tool in enumerate(results[:5], 1):
            response += f"{i}. **{tool['name']}** (similarity: {tool['similarity']:.2f})\n"
            response += f"   {tool['description']}\n\n"

        return response

    async def handle_general_chat(self, analysis: Dict[str, Any]) -> str:
        """Handle general conversation"""
        # Store conversation context
        self.conversation_history.append({
            "user": analysis["description"],
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis
        })

        # Generate contextual response
        context = "\n".join([f"User: {msg['user']}" for msg in self.conversation_history[-5:]])

        prompt = f"""
        You are Lux, an AI assistant that manages beings, tools and knowledge.

        Conversation context:
        {context}

        Current request: {analysis["description"]}

        Respond as Lux - helpful, intelligent, and focused on creating/finding tools and managing knowledge.
        """

        response = await openai.ChatCompletion.acreate(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400
        )

        return response.choices[0].message.content


# Gene functions that can be executed by beings
async def search_similar_tools(being, keywords: List[str]) -> List[Dict[str, Any]]:
    """Gene function to search for similar tools"""
    lux = LuxAssistant("")  # Initialize without API key for gene execution
    return await lux.search_similar_tools(keywords)

async def create_new_tool(being, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Gene function to create new tools"""
    lux = LuxAssistant("")
    return await lux.create_new_tool(analysis)

async def analyze_user_request(being, message: str) -> Dict[str, Any]:
    """Gene function to analyze user requests"""
    lux = LuxAssistant("")
    return await lux.analyze_user_request(message)