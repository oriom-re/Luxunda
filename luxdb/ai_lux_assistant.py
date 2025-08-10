"""
Lux AI Assistant - Conversational AI that manages beings, tools and knowledge
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import openai
# Embedding będzie obsłużony przez OpenAI bezpośrednio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from database.soul_repository import BeingRepository

class LuxAssistant:
    """Revolutionary AI Assistant that manages beings, tools and knowledge"""

    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key
        self.kernel_being = None
        self.available_tools = {}
        self.conversation_history = [] # Przechowuje historię rozmów dla kontekstu

    async def initialize(self):
        """Initialize the Lux Assistant"""
        try:
            print("🚀 Inicjalizacja Lux Assistant...")

            # Sprawdź czy już istnieje kernel
            try:
                existing_soul = await Soul.get_by_alias("lux_main_kernel")
                if existing_soul:
                    print("✅ Używam istniejącego Lux Kernel")
                    # Załaduj istniejącego Beinga, jeśli istnieje
                    try:
                        self.kernel_being = await Being.get_by_alias("lux_main_kernel")
                    except:
                        print("⚠️ Nie znaleziono istniejącego Lux Kernel Being, ale Soul istnieje.")
                    return
            except:
                # Soul nie istnieje, będziemy go tworzyć
                pass

            # Utwórz nowy kernel
            kernel_genotype = {
                "genesis": {
                    "name": "lux_kernel", 
                    "version": "1.0.0",
                    "type": "ai_assistant"
                },
                "attributes": {
                    "status": {"py_type": "str", "default": "active"},
                    "capabilities": {"py_type": "List[str]", "default": ["chat", "analysis", "data_processing"]},
                    "memory": {"py_type": "dict", "default": {}},
                    "conversation_context": {"py_type": "dict", "default": {}} # Kontekst rozmowy
                },
                "genes": { # Dodaj geny, które będą dostępne dla jądra
                    "search_tools": "luxdb.ai_lux_assistant.search_similar_tools",
                    "create_tool": "luxdb.ai_lux_assistant.create_new_tool", 
                    "analyze_request": "luxdb.ai_lux_assistant.analyze_user_request"
                }
            }

            kernel_soul = await Soul.create(kernel_genotype, alias="lux_main_kernel")
            print("✅ Lux Kernel Soul utworzony")

            # Utwórz nowy Being dla jądra
            try:
                self.kernel_being = await Being.create(
                    kernel_soul, 
                    {"status": "initialized", "capabilities": ["chat", "analysis"]},
                    alias="lux_main_kernel"
                )
                print("✅ Lux Kernel Being utworzony")
            except Exception as e:
                print(f"⚠️ Nie udało się utworzyć Being dla Lux Kernel: {e}")

            print("🌟 Lux AI Assistant zainicjalizowany!")

        except Exception as e:
            print(f"❌ Błąd inicjalizacji Lux Assistant: {e}")
            # Nie przerywaj działania - asystent może działać bez pełnej inicjalizacji
            # W tym przypadku, jeśli inicjalizacja się nie powiedzie, kernel_being pozostanie None

    async def chat(self, user_message: str) -> str:
        """Main conversation interface"""
        print(f"👤 User: {user_message}")

        # Analizuj żądanie użytkownika
        analysis = await self.analyze_user_request(user_message)

        # Dodaj wiadomość użytkownika do historii konwersacji
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis # Zapisz analizę do kontekstu
        })

        # Przetwarzaj zgodnie z intencją
        if analysis["intent"] == "create_tool":
            return await self.handle_tool_creation(analysis)
        elif analysis["intent"] == "note":
            return await self.handle_note_creation(analysis)
        elif analysis["intent"] == "search":
            return await self.handle_search(analysis)
        else:
            return await self.handle_general_chat(analysis)

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
        query_embedding = [] # To powinno być wygenerowane przez model embeddingowy

        # Load all beings and their embeddings
        all_beings = await Being.load_all()
        similar_tools = []

        for being in all_beings:
            if hasattr(being, 'knowledge_embeddings') and being.knowledge_embeddings:
                # Załóżmy, że embedding dla zapytania jest już dostępny
                # W rzeczywistości należałoby najpierw uzyskać embedding dla zapytania
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
            embeddings = [] # Tymczasowo pusta lista - powinna być generowana przez model embeddingowy

            # Create soul and being
            soul = await Soul.create(genotype, alias=tool_name)
            being = await Being.create(
                soul,
                {"knowledge_embeddings": embeddings}, # Dodaj embeddingi do atrybutów Beinga
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
                "embeddings": {"py_type": "List[float]"} # Miejsce na embeddingi notatki
            }
        }

        # Generate embeddings for the note
        embeddings = []  # Tymczasowo pusta lista - powinna być generowana przez model embeddingowy

        soul = await Soul.create(note_genotype, alias="daily_note")
        note_being = await Being.create(
            soul,
            {
                "content": analysis["description"],
                "tags": analysis["keywords"],
                "date_created": datetime.now().isoformat(),
                "embeddings": embeddings # Zapisz embeddingi
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
        """Handle general conversation, maintaining context"""
        # Pobierz ostatnie 10 wiadomości z historii konwersacji
        recent_messages = self.conversation_history[-10:] # Ostatnie 10 wiadomości

        # Formatuj historię do promptu
        context_lines = []
        for msg in recent_messages:
            role = "User" if msg["role"] == "user" else "Lux"
            content = msg['content']
            # Jeśli chcemy uwzględnić analizę, możemy ją dodać
            # if "analysis" in msg and msg["analysis"]:
            #     content += f" (Intent: {msg['analysis'].get('intent', 'N/A')})"
            context_lines.append(f"{role}: {content}")
        
        context = "\n".join(context_lines)

        # Dodaj bieżące żądanie do kontekstu
        current_request = f"User: {analysis['description']}"

        prompt = f"""
        You are Lux, an AI assistant that manages beings, tools and knowledge.

        Conversation history (last 10 messages):
        {context}

        Current request: {current_request}

        Respond as Lux - helpful, intelligent, and focused on creating/finding tools and managing knowledge.
        """

        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400
            )
            
            ai_response = response.choices[0].message.content
            
            # Dodaj odpowiedź AI do historii konwersacji
            self.conversation_history.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().isoformat()
            })

            return ai_response

        except Exception as e:
            print(f"❌ Error in general chat: {e}")
            return "Przepraszam, wystąpił problem z przetworzeniem Twojego zapytania."


# Gene functions that can be executed by beings
# Te funkcje są przykładowe i powinny być zaimplementowane w odpowiednim miejscu, np. w pliku `genes.py` lub `luxdb.models.genes`
# Przykład inicjalizacji klasy LuxAssistant w funkcji genowej jest nieoptymalny, ale zgodny z oryginalnym kodem.
# W idealnym scenariuszu, referencja do instancji LuxAssistant byłaby przekazywana do funkcji genowych.

async def search_similar_tools(being, keywords: List[str]) -> List[Dict[str, Any]]:
    """Gene function to search for similar tools"""
    # Tworzenie nowej instancji bez klucza API jest problematyczne.
    # Powinno się używać istniejącej instancji lub przekazać klucz API.
    # Na potrzeby zgodności z oryginalnym kodem, używamy pustego klucza.
    lux = LuxAssistant("") 
    # Aby to działało, klucz API musiałby być ustawiony globalnie lub przekazany.
    # W kontekście genów, lepiej jest mieć dostęp do instancji asystenta.
    # Jeśli `being` jest instancją `Being`, która ma dostęp do `LuxAssistant`, można by to zrobić tak:
    # return await being.assistant_instance.search_similar_tools(keywords)
    return await lux.search_similar_tools(keywords)

async def create_new_tool(being, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Gene function to create new tools"""
    lux = LuxAssistant("")
    return await lux.create_new_tool(analysis)

async def analyze_user_request(being, message: str) -> Dict[str, Any]:
    """Gene function to analyze user requests"""
    lux = LuxAssistant("")
    return await lux.analyze_user_request(message)