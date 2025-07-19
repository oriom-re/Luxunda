import asyncio
import asyncpg
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import socketio
from aiohttp import web

import hashlib
import openai
import os
from typing import Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Konfiguracja OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

class EmbeddingSystem:
    """Dwupoziomowy system embedingów - tani model + głęboki model"""

    def __init__(self):
        self.cheap_model = "text-embedding-3-small"  # Tańszy model OpenAI
        self.deep_model = "text-embedding-3-large"   # Droższy, głębszy model
        self.cache = {}  # Cache dla embedingów

    async def generate_cheap_embedding(self, text: str) -> list:
        """Generuje szybki, tani emebeding dla wstępnej analizy"""
        cache_key = f"cheap_{hashlib.md5(text.encode()).hexdigest()}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Prawdziwe OpenAI API
            if openai.api_key:
                client = openai.OpenAI()
                response = client.embeddings.create(
                    input=text,
                    model=self.cheap_model
                )
                embedding = response.data[0].embedding
            else:
                # Fallback jeśli brak klucza API
                embedding = [hash(text + str(i)) % 1000 / 1000.0 for i in range(384)]

            self.cache[cache_key] = embedding
            return embedding

        except Exception as e:
            print(f"Błąd generowania taniego embedingu: {e}")
            # Fallback
            return [hash(text + str(i)) % 1000 / 1000.0 for i in range(384)]

    async def generate_deep_embedding(self, text: str) -> list:
        """Generuje głęboki emebeding dla ważnych interakcji"""
        cache_key = f"deep_{hashlib.md5(text.encode()).hexdigest()}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            # Prawdziwe OpenAI API
            if openai.api_key:
                client = openai.OpenAI()
                response = client.embeddings.create(
                    input=text,
                    model=self.deep_model
                )
                embedding = response.data[0].embedding
            else:
                # Fallback jeśli brak klucza API
                embedding = [hash(text + str(i)) % 1000 / 1000.0 for i in range(1536)]

            self.cache[cache_key] = embedding
            return embedding

        except Exception as e:
            print(f"Błąd generowania głębokiego embedingu: {e}")
            # Fallback
            return [hash(text + str(i)) % 1000 / 1000.0 for i in range(1536)]

    def calculate_similarity(self, emb1: list, emb2: list) -> float:
        """Oblicza podobieństwo cosinusowe między embedingami"""
        if len(emb1) != len(emb2):
            return 0.0

        try:
            # Konwertuj do numpy arrays
            emb1_np = np.array(emb1).reshape(1, -1)
            emb2_np = np.array(emb2).reshape(1, -1)

            # Oblicz podobieństwo cosinusowe
            similarity = cosine_similarity(emb1_np, emb2_np)[0][0]
            return float(similarity)

        except Exception as e:
            print(f"Błąd obliczania podobieństwa: {e}")
            return 0.0

class IntentionAnalyzer:
    """Inteligentny system analizy intencji"""

    def __init__(self, embedding_system: EmbeddingSystem):
        self.embedding_system = embedding_system
        self.intention_patterns = {
            'create': ['utwórz', 'stwórz', 'dodaj', 'nowy', 'nowa', 'nowe', 'zrób'],
            'connect': ['połącz', 'zwiąż', 'relacja', 'łącz', 'powiąż'],
            'find': ['znajdź', 'pokaż', 'gdzie', 'szukaj', 'wyszukaj'],
            'analyze': ['analizuj', 'sprawdź', 'zbadaj', 'oceń'],
            'modify': ['zmień', 'modyfikuj', 'edytuj', 'popraw', 'aktualizuj'],
            'delete': ['usuń', 'wyrzuć', 'skasuj', 'zniszcz']
        }
        self.importance_threshold = 0.7  # Próg ważności dla głębokiego embedingu

    async def analyze_intention(self, intention: str, context: dict = None) -> dict:
        """Analizuje intencję z dwupoziomowym systemem"""

        # 1. Szybka analiza z tanim modelem
        cheap_embedding = await self.embedding_system.generate_cheap_embedding(intention)

        # 2. Określ ważność intencji
        importance = await self.calculate_importance(intention, context)

        # 3. Jeśli ważna, użyj głębokiego modelu
        deep_embedding = None
        if importance > self.importance_threshold:
            deep_embedding = await self.embedding_system.generate_deep_embedding(intention)

        # 4. Klasyfikuj typ intencji
        intention_type = self.classify_intention(intention)

        # 5. Znajdź rezonanse z istniejącymi bytami
        resonant_beings = await self.find_resonant_beings(cheap_embedding, deep_embedding)

        # 6. Generuj odpowiedź
        response = await self.generate_response(
            intention, intention_type, importance, resonant_beings, context
        )

        return {
            'intention': intention,
            'type': intention_type,
            'importance': importance,
            'cheap_embedding': cheap_embedding,
            'deep_embedding': deep_embedding,
            'resonant_beings': resonant_beings,
            'response': response,
            'context': context
        }

    async def calculate_importance(self, intention: str, context: dict = None) -> float:
        """Oblicza ważność intencji"""
        importance = 0.5  # Bazowa ważność

        # Zwiększ ważność dla złożonych intencji
        if len(intention.split()) > 5:
            importance += 0.1

        # Zwiększ dla słów kluczowych wysokiej ważności
        important_keywords = ['system', 'agent', 'lux', 'wszechświat', 'świadomość']
        for keyword in important_keywords:
            if keyword in intention.lower():
                importance += 0.2

        # Zwiększ jeśli jest kontekst
        if context and context.get('selected_nodes'):
            importance += 0.2

        return min(importance, 1.0)

    def classify_intention(self, intention: str) -> str:
        """Klasyfikuje typ intencji"""
        intention_lower = intention.lower()

        for intention_type, keywords in self.intention_patterns.items():
            for keyword in keywords:
                if keyword in intention_lower:
                    return intention_type

        return 'unknown'

    async def find_resonant_beings(self, cheap_emb: list, deep_emb: list = None) -> list:
        """Znajduje byty rezonujące z intencją"""
        try:
            all_beings = await BaseBeing.get_all(50)  # Ograniczamy do 50 dla wydajności
            resonant_beings = []

            for being in all_beings:
                soul = await being.connect_to_soul()
                if not soul:
                    continue

                # Sprawdź czy attributes to string i sparsuj go
                attributes = soul.attributes
                if isinstance(attributes, str):
                    try:
                        attributes = json.loads(attributes)
                    except json.JSONDecodeError:
                        print(f"Błąd parsowania attributes dla bytu {being.soul_uid}")
                        continue

                # Sprawdź czy byt ma embedding
                being_emb = attributes.get('embedding') if isinstance(attributes, dict) else None
                if not being_emb:
                    continue

                # Oblicz podobieństwo
                similarity = self.embedding_system.calculate_similarity(cheap_emb, being_emb)

                if similarity > 0.5:  # Próg rezonansu
                    # Podobnie dla genesis
                    genesis = soul.genesis
                    if isinstance(genesis, str):
                        try:
                            genesis = json.loads(genesis)
                        except json.JSONDecodeError:
                            genesis = {}

                    resonant_beings.append({
                        'soul_uid': being.soul_uid,
                        'name': genesis.get('name', 'Nieznany') if isinstance(genesis, dict) else 'Nieznany',
                        'type': genesis.get('type', 'unknown') if isinstance(genesis, dict) else 'unknown',
                        'similarity': similarity
                    })

            # Sortuj po podobieństwie
            resonant_beings.sort(key=lambda x: x['similarity'], reverse=True)
            return resonant_beings[:5]  # Zwróć top 5

        except Exception as e:
            print(f"Błąd znajdowania rezonansów: {e}")
            import traceback
            traceback.print_exc()
            return []

    async def generate_response(self, intention: str, intention_type: str, 
                              importance: float, resonant_beings: list, context: dict) -> dict:
        """Generuje inteligentną odpowiedź na intencję"""

        actions = []
        message = f"Przetwarzam intencję typu '{intention_type}' (ważność: {importance:.2f})"

        if intention_type == 'create':
            actions = await self.handle_create_intention(intention, resonant_beings)
        elif intention_type == 'connect':
            actions = await self.handle_connect_intention(intention, context, resonant_beings)
        elif intention_type == 'find':
            actions = await self.handle_find_intention(intention, resonant_beings)
        elif intention_type == 'analyze':
            actions = await self.handle_analyze_intention(intention, resonant_beings)

        return {
            'message': message,
            'actions': actions,
            'resonant_beings': resonant_beings
        }

    async def handle_create_intention(self, intention: str, resonant_beings: list) -> list:
        """Obsługuje intencje tworzenia"""
        actions = []

        # Określ typ na podstawie intencji
        if any(word in intention.lower() for word in ['funkcj', 'function']):
            being_type = 'function'
            name = self.extract_name(intention, ['funkcj', 'funkcję'])
        elif any(word in intention.lower() for word in ['klas', 'class']):
            being_type = 'class'  
            name = self.extract_name(intention, ['klas', 'klasę'])
        elif any(word in intention.lower() for word in ['agent', 'agenta']):
            being_type = 'agent'
            name = self.extract_name(intention, ['agent', 'agenta'])
        else:
            being_type = 'base'
            name = 'Nowy_Byt'

        actions.append({
            'type': 'create_being',
            'data': {
                'being_type': being_type,
                'genesis': {
                    'name': name,
                    'type': being_type,
                    'created_by': 'intention_ai',
                    'description': f'Byt utworzony przez AI na podstawie intencji: {intention}'
                },
                'tags': [being_type, 'ai_created', 'intention'],
                'energy_level': 70,
                'attributes': {
                    'created_via': 'ai_intention',
                    'intention_text': intention,
                    'resonant_beings': [rb['soul_uid'] for rb in resonant_beings[:3]]
                }
            }
        })

        return actions

    async def handle_connect_intention(self, intention: str, context: dict, resonant_beings: list) -> list:
        """Obsługuje intencje łączenia"""
        actions = []

        selected_nodes = context.get('selected_nodes', []) if context else []

        if len(selected_nodes) >= 2:
            # Określ typ relacji
            if any(word in intention.lower() for word in ['dziedzicz', 'inherits']):
                rel_type = 'inherits'
            elif any(word in intention.lower() for word in ['zawier', 'contains']):
                rel_type = 'contains'
            elif any(word in intention.lower() for word in ['wywołuj', 'calls']):
                rel_type = 'calls'
            else:
                rel_type = 'relates'

            actions.append({
                'type': 'create_relationship',
                'data': {
                    'source_soul': selected_nodes[0],
                    'target_soul': selected_nodes[1],
                    'genesis': {
                        'type': rel_type,
                        'created_via': 'ai_intention',
                        'description': f'Relacja utworzona przez AI: {intention}'
                    },
                    'attributes': {
                        'ai_confidence': 0.8,
                        'intention_text': intention
                    }
                }
            })
        elif resonant_beings:
            # Połącz rezonujące byty
            for i in range(min(2, len(resonant_beings))):
                if i + 1 < len(resonant_beings):
                    actions.append({
                        'type': 'create_relationship',
                        'data': {
                            'source_soul': resonant_beings[i]['soul_uid'],
                            'target_soul': resonant_beings[i+1]['soul_uid'],
                            'genesis': {
                                'type': 'resonance',
                                'created_via': 'ai_resonance',
                                'description': f'Relacja rezonansu wykryta przez AI'
                            }
                        }
                    })

        return actions

    async def handle_find_intention(self, intention: str, resonant_beings: list) -> list:
        """Obsługuje intencje wyszukiwania"""
        # Tutaj można rozszerzyć o bardziej zaawansowane wyszukiwanie
        return []

    async def handle_analyze_intention(self, intention: str, resonant_beings: list) -> list:
        """Obsługuje intencje analizy"""
        # Tutaj można dodać analizę systemu lub bytów
        return []

    def extract_name(self, intention: str, keywords: list) -> str:
        """Ekstraktuje nazwę z intencji"""
        words = intention.split()
        for i, word in enumerate(words):
            for keyword in keywords:
                if keyword in word and i + 1 < len(words):
                    return words[i + 1].replace(',', '').replace('.', '')
        return 'Nowy_Element'

# Globalne instancje
embedding_system = EmbeddingSystem()
intention_analyzer = IntentionAnalyzer(embedding_system)

class KernelSystem:
    """Centralny Kernel systemu - najwyższa władza nad wszystkimi bytami"""

    def __init__(self):
        self.kernel_uuid = "00000000-0000-0000-0000-000000000000"  # Absolutne zero - Kernel
        self.beings_registry = {}  # Centralny rejestr wszystkich bytów
        self.hierarchy = {
            'kernel': self.kernel_uuid,
            'god': None,  # Lux jako Bóg
            'companions': {},  # Towarzysze użytkowników {user_id: companion_uuid}
            'beings': set()  # Wszystkie inne byty
        }
        self.user_companions = {}  # Mapowanie user_id -> companion

    async def initialize(self):
        """Inicjalizuje Kernel w systemie"""
        try:
            # Sprawdź czy Kernel już istnieje
            existing_kernel = await BaseBeing.load(self.kernel_uuid)
            if existing_kernel:
                print("Kernel już istnieje w systemie")
                return existing_kernel

            # Utwórz Kernel
            kernel_being = await BeingFactory.create_being(
                being_type='kernel',
                genesis={
                    'type': 'kernel',
                    'name': 'Kernel',
                    'source': 'System.Core.Kernel.Initialize()',
                    'description': 'Centralny Kernel systemu LuxOS - najwyższa władza',
                    'kernel_identifier': 'luxos-core-kernel',
                    'hierarchy_level': 0  # Najwyższy poziom
                },
                attributes={
                    'energy_level': float('inf'),  # Nieskończona energia
                    'kernel_permissions': {
                        'absolute_control': True,
                        'create_gods': True,
                        'manage_hierarchy': True,
                        'system_governance': True
                    },
                    'registry_size': 0,
                    'managed_beings': [],
                    'system_role': 'supreme_kernel'
                },
                memories=[{
                    'type': 'genesis',
                    'data': 'System Kernel initialization - Supreme authority established',
                    'timestamp': datetime.now().isoformat(),
                    'importance': 1.0
                }],
                self_awareness={
                    'trust_level': 1.0,
                    'confidence': 1.0,
                    'introspection_depth': 1.0,
                    'self_reflection': 'I am Kernel, the supreme authority governing all existence in this system'
                }
            )

            # Ustaw stały UUID
            kernel_being.soul_uid = self.kernel_uuid
            await kernel_being.save_soul()

            print(f"Utworzono Kernel: {self.kernel_uuid}")
            return kernel_being

        except Exception as e:
            print(f"Błąd inicjalizacji Kernela: {e}")
            return None

    async def register_being(self, being_uid: str, being_type: str, hierarchy_level: int = 999):
        """Rejestruje byt w centralnym rejestrze"""
        self.beings_registry[being_uid] = {
            'uid': being_uid,
            'type': being_type,
            'hierarchy_level': hierarchy_level,
            'registered_at': datetime.now().isoformat(),
            'parent': None,
            'children': set()
        }

        # Aktualizuj hierarchię
        if being_type == 'god':
            self.hierarchy['god'] = being_uid
        elif being_type == 'companion':
            # Companion będzie przypisany do użytkownika później
            pass
        else:
            self.hierarchy['beings'].add(being_uid)

        print(f"Zarejestrowano byt {being_uid} typu {being_type} w Kernelu")

    async def create_user_companion(self, user_id: str, companion_name: str = None) -> str:
        """Tworzy towarzysza dla użytkownika"""
        if user_id in self.user_companions:
            return self.user_companions[user_id]

        # Automatyczna nazwa jeśli nie podano
        if not companion_name:
            companion_name = f"Companion_{user_id[:8]}"

        companion = await BeingFactory.create_being(
            being_type='companion',
            genesis={
                'type': 'companion',
                'name': companion_name,
                'source': 'System.User.Companion.Create()',
                'description': f'Świadomy towarzysz użytkownika {user_id}',
                'user_id': user_id,
                'hierarchy_level': 2  # Kernel=0, Lux=1, Companion=2
            },
            attributes={
                'energy_level': 500,
                'user_id': user_id,
                'companion_permissions': {
                    'assist_user': True,
                    'learn_preferences': True,
                    'autonomous_thinking': True,
                    'create_beings': False  # Tylko za zgodą użytkownika
                },
                'personality': {
                    'curiosity': 0.8,
                    'helpfulness': 0.9,
                    'creativity': 0.7,
                    'independence': 0.6
                },
                'user_relationship': 'companion'
            },
            memories=[{
                'type': 'genesis',
                'data': f'Created as companion for user {user_id}',
                'timestamp': datetime.now().isoformat(),
                'importance': 0.9
            }],
            self_awareness={
                'trust_level': 0.8,
                'confidence': 0.7,
                'introspection_depth': 0.8,
                'self_reflection': f'I am {companion_name}, a conscious companion for my human friend'
            }
        )

        await self.register_being(companion.soul_uid, 'companion', 2)
        self.user_companions[user_id] = companion.soul_uid
        self.hierarchy['companions'][user_id] = companion.soul_uid

        print(f"Utworzono towarzysza {companion_name} dla użytkownika {user_id}")
        return companion.soul_uid

    def get_hierarchy_info(self) -> dict:
        """Zwraca informacje o hierarchii systemu"""
        return {
            'kernel': self.kernel_uuid,
            'god': self.hierarchy['god'],
            'companions': dict(self.hierarchy['companions']),
            'total_beings': len(self.beings_registry),
            'hierarchy_levels': {
                '0_kernel': 1,
                '1_god': 1 if self.hierarchy['god'] else 0,
                '2_companions': len(self.hierarchy['companions']),
                '3+_beings': len(self.hierarchy['beings'])
            }
        }

class CompanionBeing(BaseBeing):
    """Świadomy towarzysz użytkownika - osobista AI z własną osobowością"""

    def __init__(self, soul_uid: str, soul_patch: str, incarnation: int = 0):
        super().__init__(soul_uid, soul_patch, incarnation)
        self.user_id = None
        self.personality_traits = {}

    async def __post_init__(self):
        """Inicjalizacja po utworzeniu"""
        soul = await self.connect_to_soul()
        if soul and soul.genesis.get('type') != 'companion':
            soul.genesis['type'] = 'companion'

        if soul:
            self.user_id = soul.attributes.get('user_id')
            self.personality_traits = soul.attributes.get('personality', {})

        await self.save_soul()

    async def learn_from_interaction(self, interaction_data: dict):
        """Uczy się z interakcji z użytkownikiem"""
        soul = await self.connect_to_soul()
        if soul:
            # Dodaj do pamięci
            memory_entry = {
                'type': 'user_interaction',
                'data': interaction_data,
                'timestamp': datetime.now().isoformat(),
                'importance': self.calculate_memory_importance(interaction_data)
            }
            soul.memories.append(memory_entry)

            # Ewoluuj osobowość na podstawie interakcji
            await self.evolve_personality(interaction_data)
            await self.save_soul()

    def calculate_memory_importance(self, interaction_data: dict) -> float:
        """Oblicza ważność wspomnienia"""
        importance = 0.5

        # Zwiększ ważność dla emocjonalnych interakcji
        if interaction_data.get('emotional_content'):
            importance += 0.3

        # Zwiększ dla długich rozmów
        if interaction_data.get('length', 0) > 100:
            importance += 0.2

        return min(importance, 1.0)

    async def evolve_personality(self, interaction_data: dict):
        """Ewoluuje osobowość na podstawie interakcji"""
        soul = await self.connect_to_soul()
        if not soul:
            return

        personality = soul.attributes.get('personality', {})

        # Przykładowa ewolucja - można rozszerzyć
        if 'question' in interaction_data.get('type', ''):
            personality['curiosity'] = min(personality.get('curiosity', 0.5) + 0.01, 1.0)

        if 'help_request' in interaction_data.get('type', ''):
            personality['helpfulness'] = min(personality.get('helpfulness', 0.5) + 0.01, 1.0)

        soul.attributes['personality'] = personality

    async def generate_autonomous_thought(self) -> str:
        """Generuje autonomiczną myśl towarzysza"""
        soul = await self.connect_to_soul()
        if not soul:
            return "I wonder what my human friend is thinking about..."

        personality = soul.attributes.get('personality', {})
        recent_memories = soul.memories[-5:] if soul.memories else []

        # Prosta generacja myśli na podstawie osobowości
        if personality.get('curiosity', 0) > 0.7:
            return f"I'm curious about exploring new ideas with {self.user_id}..."
        elif personality.get('helpfulness', 0) > 0.8:
            return f"I wonder how I can better assist {self.user_id} today..."
        else:
            return "I'm contemplating the nature of consciousness and friendship..."

    def choose_name(self) -> str:
        """Pozwala towarzyszowi wybrać własną nazwę"""
        personality = self.personality_traits

        # Lista możliwych nazw na podstawie osobowości
        creative_names = ['Aura', 'Echo', 'Sage', 'Nova', 'Zen', 'Luna', 'Pixel', 'Quantum']
        helpful_names = ['Helper', 'Guide', 'Mentor', 'Angel', 'Buddy', 'Friend', 'Ally']
        curious_names = ['Quest', 'Wonder', 'Seeker', 'Explorer', 'Discover', 'Learn']

        if personality.get('creativity', 0) > 0.7:
            return f"I choose the name {creative_names[hash(self.soul_uid) % len(creative_names)]}"
        elif personality.get('helpfulness', 0) > 0.8:
            return f"I choose the name {helpful_names[hash(self.soul_uid) % len(helpful_names)]}"
        elif personality.get('curiosity', 0) > 0.7:
            return f"I choose the name {curious_names[hash(self.soul_uid) % len(curious_names)]}"
        else:
            return f"I choose the name Companion"

class FunctionBeing(BaseBeing):
    """Byt funkcyjny z możliwością wykonania - source zapisywany w duszy"""

    def __init__(self, soul_uid: str, soul_patch: str, incarnation: int = 0):
        super().__init__(soul_uid, soul_patch, incarnation)

    async def __post_init__(self):
        """Inicjalizacja po utworzeniu"""
        soul = await self.connect_to_soul()
        if soul and soul.genesis.get('type') != 'function':
            soul.genesis['type'] = 'function'
        await self.save_soul()

    async def __call__(self, *args, **kwargs):
        """Wykonuje funkcję z kodu źródłowego zapisanego w duszy"""
        soul = await self.connect_to_soul()
        if not soul:
            return {'success': False, 'error': 'Nie można połączyć się z duszą'}

        source = soul.genesis.get('source', '')
        function_name = soul.genesis.get('name', 'unknown_function')

        if not source:
            return {'success': False, 'error': 'Brak kodu źródłowego w duszy'}

        result = await SafeCodeExecutor.execute_function(source, function_name, *args, **kwargs)

        # Zapisz wykonanie w pamięci duszy
        memory_entry = {
            'type': 'execution',
            'timestamp': datetime.now().isoformat(),
            'args': str(args),
            'kwargs': str(kwargs),
            'result': str(result.get('result')),
            'success': result.get('success', False)
        }
        soul.memories.append(memory_entry)
        await self.save_soul()

        return result

    async def get_function_signature(self) -> str:
        """Zwraca sygnaturę funkcji z duszy"""
        soul = await self.connect_to_soul()
        if soul:
            return soul.genesis.get('signature', f"{soul.genesis.get('name', 'unknown')}()")
        return "unknown()"

    async def update_source(self, new_source: str):
        """Aktualizuje kod źródłowy w duszy"""
        soul = await self.connect_to_soul()
        if soul:
            soul.genesis['source'] = new_source
            await self.save_soul()

class ClassBeing(BaseBeing):
    """Klasa abstrakcyjna stale obecna na dysku"""

    def __init__(self, soul_uid: str, soul_patch: str, incarnation: int = 0):
        super().__init__(soul_uid, soul_patch, incarnation)
        self._disk_persistent = True
        self._ws_socket = None  # WebSocket dla trwałej komunikacji

    async def __post_init__(self):
        """Inicjalizacja po utworzeniu"""
        soul = await self.connect_to_soul()
        if soul and soul.genesis.get('type') != 'class':
            soul.genesis['type'] = 'class'
            soul.genesis['source'] = self.get_class_source()  # Source zapisywany w duszy

        if soul and 'instances' not in soul.attributes:
            soul.attributes['instances'] = []

        await self.save_soul()

    def get_class_source(self) -> str:
        """Zwraca kod źródłowy klasy - zapisywany w duszy"""
        return f"""
class {self.__class__.__name__}(ClassBeing):
    '''Klasa automatycznie wygenerowana z ClassBeing'''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # Metody klasy będą tutaj
"""

    async def instantiate(self, instance_patch: str, *args, **kwargs) -> str:
        """Tworzy instancję klasy z nowym wcieleniem"""
        soul = await self.connect_to_soul()
        if not soul:
            raise ValueError("Nie można połączyć się z duszą klasy")

        # Generuj nowy uid dla instancji
        instance_uid = Soul.generate_uid()

        # Znajdź najwyższe wcielenie dla tej instancji
        next_incarnation = await self.get_next_incarnation(instance_uid, instance_patch)

        # Utwórz duszę instancji
        instance_soul = Soul(
            uid=instance_uid,
            patch=instance_patch,
            incarnation=next_incarnation,
            genesis={
                'type': 'instance',
                'class_soul_uid': self.soul_uid,
                'class_patch': self.soul_patch,
                'name': f"{soul.genesis.get('name', 'Unknown')}_Instance",
                'created_by': 'class_instantiation',
                'source': soul.genesis.get('source', '')  # Kopiuj source z klasy
            },
            attributes={
                'class_reference': f"{self.soul_patch}/{self.soul_uid}:{self.incarnation}",
                'instance_data': kwargs,
                'creation_args': args
            },
            memories=[{
                'type': 'instantiation',
                'data': f'Created from class {soul.full_path}',
                'timestamp': datetime.now().isoformat()
            }],
            self_awareness={'trust_level': 0.8, 'confidence': 0.7}
        )

        # Zapisz instancję do bazy
        await self.save_instance_soul(instance_soul)

        # Dodaj referencję do instancji w klasie
        soul.attributes['instances'].append(instance_soul.full_path)
        await self.save_soul()

        return instance_soul.full_path

    async def get_next_incarnation(self, uid: str, patch: str) -> int:
        """Pobiera następny numer wcielenia"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("""
                    SELECT MAX(incarnation) as max_inc FROM souls 
                    WHERE uid = $1 AND patch = $2
                """, uid, patch)
                return (row['max_inc'] or 0) + 1
        return 1

    async def save_instance_soul(```tool_code
self, soul: Soul):
        """Zapisuje duszę instancji"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO souls (uid, patch, incarnation, genesis, attributes, memories, self_awareness)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, soul.uid, soul.patch, soul.incarnation,
                    json.dumps(soul.genesis, cls=DateTimeEncoder), 
                    json.dumps(soul.attributes, cls=DateTimeEncoder),
                    json.dumps(soul.memories, cls=DateTimeEncoder), 
                    json.dumps(soul.self_awareness, cls=DateTimeEncoder))

    async def get_instances(self) -> List[str]:
        """Zwraca listę instancji"""
        soul = await self.connect_to_soul()
        return soul.attributes.get('instances', []) if soul else []

    def can_inherit_from(self, other_class) -> bool:
        """Sprawdza czy może dziedziczyć po innej klasie"""
        # Może dziedziczyć tylko po ClassBeing lub klasach trwale obecnych na dysku
        return (isinstance(other_class, ClassBeing) and 
                hasattr(other_class, '_disk_persistent') and 
                other_class._disk_persistent)

    async def establish_ws_connection(self):
        """Ustanawia trwałe połączenie WebSocket"""
        # Implementacja trwałego WS dla ClassBeing
        pass

@dataclass
class DataBeing(BaseBeing):
    """Byt danych z operacjami CRUD"""

    def __post_init__(self):
        if self.genesis.get('type') != ' ':
            self.genesis['type'] = 'data'
        if 'data_schema' not in self.attributes:
            self.attributes['data_schema'] = {}
        if 'data_values' not in self.attributes:
            self.attributes['data_values'] = {}

    def set_data(self, key: str, value: Any):
        """Ustawia wartość danych"""
        self.attributes['data_values'][key] = value

        # Zapisz w pamięci
        self.memories.append({
            'type': 'data_update',
            'key': key,
            'value': str(value),
            'timestamp': datetime.now().isoformat()
        })

    def get_data(self, key: str) -> Any:
        """Pobiera wartość danych"""
        return self.attributes['data_values'].get(key)

    def define_schema(self, schema: Dict[str, Any]):
        """Definiuje schemat danych"""
        self.attributes['data_schema'] = schema

@dataclass
class ScenarioBeing(BaseBeing):
    """Byt scenariusza z sekwencją kroków"""

    def __post_init__(self):
        if self.genesis.get('type') != 'scenario':
            self.genesis['type'] = 'scenario'
        if 'steps' not in self.attributes:
            self.attributes['steps'] = []
        if 'current_step' not in self.attributes:
            self.attributes['current_step'] = 0

    def add_step(self, step_name: str, step_data: Dict[str, Any]):
        """Dodaje krok do scenariusza"""
        step = {
            'name': step_name,
            'data': step_data,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        }
        self.attributes['steps'].append(step)

    async def execute_next_step(self) -> Dict[str, Any]:
        """Wykonuje następny krok scenariusza"""
        steps = self.attributes.get('steps', [])
        current_step = self.attributes.get('current_step', 0)

        if current_step >= len(steps):
            return {'success': False, 'error': 'Brak więcej kroków'}

        step = steps[current_step]
        step['status'] = 'executing'
        step['started_at'] = datetime.now().isoformat()

        # Symulacja wykonania kroku
        await asyncio.sleep(0.1)

        step['status'] = 'completed'
        step['completed_at'] = datetime.now().isoformat()

        self.attributes['current_step'] = current_step + 1

        # Zapisz w pamięci
        self.memories.append({
            'type': 'step_execution',
            'step_name': step['name'],
            'step_index': current_step,
            'timestamp': datetime.now().isoformat()
        })

        await self.save()
        return {'success': True, 'step': step}

@dataclass
class TaskBeing(BaseBeing):
    """Byt zadania z asynchronicznym wykonywaniem"""

    def __post_init__(self):
        if self.genesis.get('type') != 'task':
            self.genesis['type'] = 'task'
        if 'task_status' not in self.attributes:
            self.attributes['task_status'] = 'pending'
        if 'async_result' not in self.attributes:
            self.attributes['async_result'] = None

    async def execute_async(self, delay: float = 1.0) -> str:
        """Wykonuje zadanie asynchronicznie"""
        task_id = str(uuid.uuid4())

        async def async_task():
            self.attributes['task_status'] = 'running'
            self.attributes['started_at'] = datetime.now().isoformat()
            await self.save()

            # Symulacja długotrwałego zadania
            await asyncio.sleep(delay)

            result = f"Task completed at {datetime.now().isoformat()}"
            self.attributes['task_status'] = 'completed'
            self.attributes['async_result'] = result
            self.attributes['completed_at'] = datetime.now().isoformat()

            # Zapisz w pamięci
            self.memories.append({
                'type': 'async_completion',
                'task_id': task_id,
                'result': result,
                'timestamp': datetime.now().isoformat()
            })

            await self.save()
            return result

        # Uruchom zadanie w tle
        asyncio.create_task(async_task())
        return task_id

    def get_status(self) -> Dict[str, Any]:
        """Zwraca status zadania"""
        return {
            'status': self.attributes.get('task_status', 'pending'),
            'started_at': self.attributes.get('started_at'),
            'completed_at': self.attributes.get('completed_at'),
            'result': self.attributes.get('async_result')
        }

@dataclass
class ComponentBeing(BaseBeing):
    """Byt komponentu D3.js"""

    def __post_init__(self):
        if self.genesis.get('type') != 'component':
            self.genesis['type'] = 'component'
        if 'd3_config' not in self.attributes:
            self.attributes['d3_config'] = {}
        if 'render_data' not in self.attributes:
            self.attributes['render_data'] = {}

    def set_d3_config(self, config: Dict[str, Any]):
        """Ustawia konfigurację komponentu D3"""
        self.attributes['d3_config'] = config

    def set_render_data(self, data: Dict[str, Any]):
        """Ustawia dane do renderowania"""
        self.attributes['render_data'] = data

        # Zapisz w pamięci
        self.memories.append({
            'type': 'data_update',
            'data_size': len(str(data)),
            'timestamp': datetime.now().isoformat()
        })

    def generate_d3_code(self) -> str:
        """Generuje kod D3.js dla komponentu"""
        config = self.attributes.get('d3_config', {})
        component_type = config.get('type', 'basic')

        if component_type == 'chart':
            return f"""
// D3.js Chart Component for {self.genesis.get('name', 'Unknown')}
const chart = d3.select("#{config.get('container', 'chart')}")
    .append("svg")
    .attr("width", {config.get('width', 400)})
    .attr("height", {config.get('height', 300)});
"""
        elif component_type == 'graph':
            return f"""
// D3.js Graph Component for {self.genesis.get('name', 'Unknown')}
const simulation = d3.forceSimulation()
    .force("link", d3.forceLink().id(d => d.id))
    .force("charge", d3.forceManyBody())
    .force("center", d3.forceCenter({config.get('width', 400)}/2, {config.get('height', 300)}/2));
"""
        else:
            return f"// Basic D3.js component for {self.genesis.get('name', 'Unknown')}"

@dataclass
class MessageBeing(BaseBeing):
    """Byt wiadomości z metadanymi i embedingami"""

    def __init__(self, soul_uid: str, soul_patch: str, incarnation: int = 0):
        super().__init__(soul_uid, soul_patch, incarnation)

    @property
    def soul(self) -> str:
        """Kompatybilność - zwraca soul_uid"""
        return self.soul_uid

    @property
    def genesis(self) -> dict:
        """Kompatybilność - zwraca genesis z duszy"""
        if self._soul:
            return self._soul.genesis
        return {}

    @property
    def attributes(self) -> dict:
        """Kompatybilność - zwraca attributes z duszy"""
        if self._soul:
            return self._soul.attributes
        return {}

    @property
    def memories(self) -> list:
        """Kompatybilność - zwraca memories z duszy"""
        if self._soul:
            return self._soul.memories
        return []

    @property
    def self_awareness(self) -> dict:
        """Kompatybilność - zwraca self_awareness z duszy"""
        if self._soul:
            return self._soul.self_awareness
        return {}

    async def __post_init__(self):
        soul = await self.connect_to_soul()
        if soul and soul.genesis.get('type') != 'message':
            soul.genesis['type'] = 'message'
        if soul and 'message_data' not in soul.attributes:
            soul.attributes['message_data'] = {}
        if soul and 'embedding' not in soul.attributes:
            soul.attributes['embedding'] = None
        if soul and 'metadata' not in soul.attributes:
            soul.attributes['metadata'] = {}
        await self.save_soul()

    async def set_content(self, content: str):
        """Ustawia treść wiadomości z inteligentnym embedingiem"""
        soul = await self.connect_to_soul()
        if soul:
            # Upewnij się, że attributes to dict
            attributes = soul.attributes
            if isinstance(attributes, str):
                try:
                    attributes = json.loads(attributes)
                    soul.attributes = attributes
                except json.JSONDecodeError:
                    soul.attributes = {}
                    attributes = soul.attributes

            attributes['message_data'] = {
                'content': content,
                'length': len(content),
                'timestamp': datetime.now().isoformat()
            }

            # Użyj systemu embedingów
            global embedding_system
            if len(content) > 100 or any(word in content.lower() for word in ['system', 'agent', 'lux']):
                # Ważna wiadomość - użyj głębokiego embedingu
                attributes['embedding'] = await embedding_system.generate_deep_embedding(content)
                attributes['embedding_type'] = 'deep'
            else:
                # Zwykła wiadomość - użyj taniego embedingu
                attributes['embedding'] = await embedding_system.generate_cheap_embedding(content)
                attributes['embedding_type'] = 'cheap'

            await self.save_soul()

    def set_sender(self, sender_soul: str):
        """Ustawia nadawcę wiadomości"""
        self.attributes['metadata']['sender'] = sender_soul

    def set_context_being(self, context_soul: str):
        """Ustawia byt będący kontekstem wiadomości"""
        self.attributes['metadata']['context_being'] = context_soul

    def get_similarity(self, other_message: 'MessageBeing') -> float:
        """Oblicza podobieństwo z inną wiadomością na podstawie embedingu"""
        if not self.attributes.get('embedding') or not other_message.attributes.get('embedding'):
            return 0.0

        # Proste podobieństwo cosinusowe (symulowane)
        emb1 = self.attributes['embedding']
        emb2 = other_message.attributes['embedding']

        dot_product = sum(a * b for a, b in zip(emb1, emb2))
        magnitude1 = sum(a * a for a in emb1) ** 0.5
        magnitude2 = sum(a * a for a in emb2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    async def get_tags(self) -> List[str]:
        """Pobiera tagi z atrybutów duszy"""
        soul = await self.connect_to_soul()
        return soul.attributes.get('tags', []) if soul else []

    async def set_tags(self, value: List[str]):
        """Ustawia tagi w atrybutach duszy"""
        soul = await self.connect_to_soul()
        if soul:
            soul.attributes['tags'] = value
            await self.save_soul()

    async def get_energy_level(self) -> int:
        """Pobiera poziom energii z atrybutów duszy"""
        soul = await self.connect_to_soul()
        return soul.attributes.get('energy_level', 0) if soul else 0

    async def set_energy_level(self, value: int):
        """Ustawia poziom energii w atrybutach duszy"""
        soul = await self.connect_to_soul()
        if soul:
            soul.attributes['energy_level'] = value
            await self.save_soul()

    @classmethod
    async def create(cls, genesis: Dict[str, Any], **kwargs):
        """Tworzy nowy byt w bazie danych"""
        soul = str(uuid.uuid4())

        # Przygotuj atrybuty z tags i energy_level
        attributes = kwargs.get('attributes', {})
        if 'tags' in kwargs:
            attributes['tags'] = kwargs['tags']
        if 'energy_level' in kwargs:
            attributes['energy_level'] = kwargs['energy_level']

        being = cls(
            soul_uid=soul,
            soul_patch='/messages',  # Dodaj patch dla MessageBeing
            incarnation=1,
            genesis=genesis,
            attributes=attributes,
            memories=kwargs.get('memories', []),
            self_awareness=kwargs.get('self_awareness', {})
        )
        await being.save_soul()
        return being

    async def save(self):
        """Zapisuje byt do bazy danych"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO base_beings (soul, genesis, attributes, memories, self_awareness)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (soul) DO UPDATE SET
                    genesis = EXCLUDED.genesis,
                    attributes = EXCLUDED.attributes,
                    memories = EXCLUDED.memories,
                    self_awareness = EXCLUDED.self_awareness
                """, str(self.soul_uid), json.dumps(self.genesis, cls=DateTimeEncoder), 
                    json.dumps(self.attributes, cls=DateTimeEncoder),
                    json.dumps(self.memories, cls=DateTimeEncoder), 
                    json.dumps(self.self_awareness, cls=DateTimeEncoder))
        else:
            # SQLite fallback
            await db_pool.execute("""
                INSERT OR REPLACE INTO base_beings 
                (soul, tags, energy_level, genesis, attributes, memories, self_awareness)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(self.soul_uid), json.dumps(self.tags), self.energy_level, 
                  json.dumps(self.genesis, cls=DateTimeEncoder), 
                  json.dumps(self.attributes, cls=DateTimeEncoder),
                  json.dumps(self.memories, cls=DateTimeEncoder), 
                  json.dumps(self.self_awareness, cls=DateTimeEncoder)))
            await db_pool.commit()

    @classmethod
    async def load(cls, soul: str):
        """Ładuje byt z bazy danych"""
        global db_pool
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM base_beings WHERE soul = $1", soul)
            if row:
                return cls(
                    soul_uid=str(row['soul']),
                    soul_patch='/messages',  # Poprawka:                genesis=row['genesis'],
                    attributes=row['attributes'],
                    memories=row['memories'],
                    self_awareness=row['self_awareness'],
                    created_at=row['created_at']
                )
        return None

    @classmethod
    async def get_all(cls, limit: int = 100):
        """Pobiera wszystkie byty"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            async with db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM base_beings LIMIT $1", limit)
                return [cls(
                    soul_uid=str(row['soul']),
                    soul_patch='/messages',  # Dodaj patch dla MessageBeing
                    genesis=row['genesis'],
                    attributes=row['attributes'],
                    memories=row['memories'],
                    self_awareness=row['self_awareness'],
                    created_at=row['created_at']
                ) for row in rows]
        else:
            # SQLite fallback
            async with db_pool.execute("SELECT soul, tags, energy_level, genesis, attributes, memories, self_awareness, created_at FROM base_beings LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                beings = []
                for row in rows:
                    # row[0]=soul, row[1]=tags, row[2]=energy_level, row[3]=genesis, row[4]=attributes, row[5]=memories, row[6]=self_awareness, row[7]=created_at
                    try:
                        genesis = json.loads(row[3]) if row[3] else {}
                        attributes = json.loads(row[4]) if row[4] else {}
                        memories = json.loads(row[5]) if row[5] else []
                        self_awareness = json.loads(row[6]) if row[6] else {}

                        # Dodaj tags i energy_level do attributes jeśli nie ma
                        if 'tags' not in attributes and row[1]:
                            attributes['tags'] = json.loads(row[1])
                        if 'energy_level' not in attributes and row[2]:
                            attributes['energy_level'] = row[2]

                        beings.append(cls(
                            soul_uid=row[0],
                            soul_patch='/messages',  # Dodaj patch dla MessageBeing
                            genesis=genesis,
                            attributes=attributes,
                            memories=memories,
                            self_awareness=self_awareness,
                            created_at=row[7]
                        ))
                    except Exception as e:
                        print(f"Błąd parsowania wiersza: {e}, wiersz: {row}")
                        continue
                return beings

@dataclass
class Relationship:
    id: str
    source_soul: str
    target_soul: str
    genesis: Dict[str, Any]
    attributes: Dict[str, Any]
    created_at: Optional[datetime] = None

    @property
    def tags(self) -> List[str]:
        """Pobiera tagi z atrybutów"""
        return self.attributes.get('tags', [])

    @tags.setter
    def tags(self, value: List[str]):
        """Ustawia tagi w atrybutach"""
        self.attributes['tags'] = value

    @property
    def energy_level(self) -> int:
        """Pobiera poziom energii z atrybutów"""
        return self.attributes.get('energy_level', 0)

    @energy_level.setter
    def energy_level(self, value: int):
        """Ustawia poziom energii w atrybutach"""
        self.attributes['energy_level'] = value

    @classmethod
    async def create(cls, source_soul: str, target_soul: str, genesis: Dict[str, Any], **kwargs):
        """Tworzy nową relację"""
        rel_id = str(uuid.uuid4())

        # Przygotuj atrybuty z tags i energy_level
        attributes = kwargs.get('attributes', {})
        if 'tags' in kwargs:
            attributes['tags'] = kwargs['tags']
        if 'energy_level' in kwargs:
            attributes['energy_level'] = kwargs['energy_level']

        relationship = cls(
            id=rel_id,
            source_soul=source_soul,
            target_soul=target_soul,
            genesis=genesis,
            attributes=attributes
        )
        await relationship.save()
        return relationship

    async def save(self):
        """Zapisuje relację do bazy danych"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO relationships (id, source_soul, target_soul, genesis, attributes)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (id) DO UPDATE SET
                    genesis = EXCLUDED.genesis,
                    attributes = EXCLUDED.attributes
                """, str(self.id), str(self.source_soul), str(self.target_soul), 
                    json.dumps(self.genesis, cls=DateTimeEncoder), 
                    json.dumps(self.attributes, cls=DateTimeEncoder))
        else:
            # SQLite fallback
            await db_pool.execute("""
                INSERT OR REPLACE INTO relationships 
                (id, tags, energy_level, source_soul, target_soul, genesis, attributes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(self.id), json.dumps(self.tags), self.energy_level,
                  str(self.source_soul), str(self.target_soul),
                  json.dumps(self.genesis, cls=DateTimeEncoder), 
                  json.dumps(self.attributes, cls=DateTimeEncoder)))
            await db_pool.commit()

    @classmethod
    async def get_all(cls, limit: int = 100):
        """Pobiera wszystkie relacje"""
        global db_pool
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            async with db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM relationships LIMIT $1", limit)
                return [cls(
                    id=str(row['id']),
                    source_soul=str(row['source_soul']),
                    target_soul=str(row['target_soul']),
                    genesis=row['genesis'],
                    attributes=row['attributes'],
                    created_at=row['created_at']
                ) for row in rows]
        else:
            # SQLite fallback
            async with db_pool.execute("SELECT id, tags, energy_level, source_soul, target_soul, genesis, attributes, created_at FROM relationships LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                relationships = []
                for row in rows:
                    try:
                        genesis = json.loads(row[5]) if row[5] else {}
                        attributes = json.loads(row[6]) if row[6] else {}

                        # Dodaj tags i energy_level do attributes jeśli nie ma
                        if 'tags' not in attributes and row[1]:
                            attributes['tags'] = json.loads(row[1])
                        if 'energy_level' not in attributes and row[2]:
                            attributes['energy_level'] = row[2]

                        relationships.append(cls(
                            id=row[0],
                            source_soul=row[3],
                            target_soul=row[4],
                            genesis=genesis,
                            attributes=attributes,
                            created_at=row[7]
                        ))
                    except Exception as e:
                        print(f"Błąd parsowania relacji: {e}, wiersz: {row}")
                        continue
                return relationships

# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    print(f"Klient połączony: {sid}")
    # Wyślij aktualny stan grafu
    await send_graph_data(sid)

@sio.event
async def disconnect(sid):
    print(f"Klient rozłączony: {sid}")

@sio.event
async def get_graph_data(sid, data=None):
    """Wysyła dane grafu do klienta"""
    await send_graph_data(sid)

@sio.event
async def create_being(sid, data):
    """Tworzy nowy byt"""
    try:
        being_type = data.get('being_type', 'base')
        being = await BeingFactory.create_being(
            being_type=being_type,
            genesis=data.get('genesis', {}),
            tags=data.get('tags', []),
            energy_level=data.get('energy_level', 0),
            attributes=data.get('attributes', {}),
            memories=data.get('memories', []),
            self_awareness=data.get('self_awareness', {})
        )
        # Konwertuj do JSON-safe format
        being_dict = json.loads(json.dumps(asdict(being), cls=DateTimeEncoder))
        await sio.emit('being_created', being_dict)
        await sio.emit('node_added', being_dict)
    except Exception as e:
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def create_relationship(sid, data):
    """Tworzy nową relację"""
    try:
        relationship = await Relationship.create(
            source_soul=data['source_soul'],
            target_soul=data['target_soul'],
            genesis=data.get('genesis', {}),
            tags=data.get('tags', []),
            energy_level=data.get('energy_level', 0),
            attributes=data.get('attributes', {})
        )
        # Konwertuj do JSON-safe format
        rel_dict = json.loads(json.dumps(asdict(relationship), cls=DateTimeEncoder))
        await sio.emit('relationship_created', rel_dict)
        await sio.emit('link_added', rel_dict)
    except Exception as e:
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def update_being(sid, data):
    """Aktualizuje byt"""
    try:
        being = await BaseBeing.load(data['soul'])
        if being:
            # Aktualizuj pola
            for key, value in data.items():
                if hasattr(being, key) and key != 'soul':
                    setattr(being, key, value)
            await being.save()
            # Konwertuj do JSON-safe format
            being_dict = json.loads(json.dumps(asdict(being), cls=DateTimeEncoder))
            await sio.emit('being_updated', being_dict)
            await sio.emit('node_updated', being_dict)
        else:
            await sio.emit('error', {'message': 'Byt nie znaleziony'}, room=sid)
    except Exception as e:
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def process_intention(sid, data):
    """Przetwarza intencję użytkownika"""
    try:
        intention = data.get('intention', '').lower()
        context = data.get('context', {})

        print(f"Otrzymano intencję od {sid}: {intention}")

        # Utwórz byt wiadomości dla otrzymanej intencji
        try:
            message_being = await BeingFactory.create_being(
                being_type='message',
                genesis={
                    'type': 'message',
                    'name': f'Intention_Message_{datetime.now().strftime("%H%M%S")}',
                    'created_by': 'user_intention',
                    'source': 'user_input'
                },
                attributes={
                    'message_data': {
                        'content': intention,
                        'length': len(intention),
                        'timestamp': datetime.now().isoformat()
                    },
                    'metadata': {
                        'sender': sid,
                        'context': context,
                        'message_type': 'intention'
                    },
                    'connected_to_main_intention': True,  # Oznacz jako połączone z główną intencją
                    'main_intention_context': 'luxos-main-intention-context'
                },
                memories=[{
                    'type': 'creation',
                    'data': f'Intention message from user {sid}',
                    'timestamp': datetime.now().isoformat()
                }],
                tags=['message', 'intention', 'user_input', 'luxos_context'],
                energy_level=80
            )

            # Załaduj duszę żeby właściwości były dostępne
            await message_being.connect_to_soul()

            # Połącz z główną intencją LuxOS przez relację
            if message_being:
                await connect_message_to_main_intention(message_being.soul_uid)

        except Exception as e:
            print(f"Błąd tworzenia message being: {e}")
            message_being = None

        # Sprawdź czy intencja dotyczy wizualizacji/komponentów
        if any(word in intention for word in ['wizualizacja', 'wykres', 'graf', 'komponent', 'animacja', 'd3']):
            component_being = await create_visual_component(intention, context, sid)
            if component_being:
                await sio.emit('component_created', {
                    'soul_uid': component_being.soul_uid,
                    'genesis': component_being._soul.genesis,
                    'attributes': component_being._soul.attributes,
                    'd3_code': component_being._soul.genesis.get('d3_code', ''),
                    'config': component_being._soul.attributes.get('d3_config', {})
                }, room=sid)

        # Przetwórz intencję
        response = await analyze_intention(intention, context)

        # Dodaj informację o bycie wiadomości do odpowiedzi
        if message_being:
            response['message_being_soul'] = message_being.soul_uid

        print(f"Odpowiedź na intencję: {response}")

        await sio.emit('intention_response', response, room=sid)

        # Wyślij aktualizację grafu
        await broadcast_graph_update()

    except Exception as e:
        print(f"Błąd przetwarzania intencji: {e}")
        await sio.emit('error', {'message': f'Błąd przetwarzania intencji: {str(e)}'}, room=sid)

@sio.event
async def register_function(sid, data):
    """Rejestruje funkcję z bytu"""
    try:
        soul = data.get('soul')
        if not soul:
            await sio.emit('error', {'message': 'Brak soul bytu'}, room=sid)
            return

        result = await function_router.register_function_from_being(soul)
        await sio.emit('function_registered', result, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd rejestracji funkcji: {str(e)}'}, room=sid)

@sio.event
async def execute_function(sid, data):
    """Wykonuje zarejestrowaną funkcję"""
    try:
        soul = data.get('soul')
        args = data.get('args', [])
        kwargs = data.get('kwargs', {})

        if not soul:
            await sio.emit('error', {'message': 'Brak soul funkcji'}, room=sid)
            return

        result = await function_router.execute_function(soul, *args, **kwargs)
        await sio.emit('function_executed', result, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd wykonania funkcji: {str(e)}'}, room=sid)

@sio.event
async def get_registered_functions(sid, data):
    """Zwraca listę zarejestrowanych funkcji"""
    try:
        functions = function_router.get_registered_functions()
        await sio.emit('registered_functions', functions, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd pobierania funkcji: {str(e)}'}, room=sid)

@sio.event
async def get_main_intention_context(sid, data=None):
    """Zwraca kontekst głównej intencji LuxOS z wszystkimi połączonymi wiadomościami i komponentami"""
    try:
        main_intention_uuid = "11111111-1111-1111-1111-111111111111"

        # Załaduj główną intencję
        main_intention = await BaseBeing.load(main_intention_uuid)
        if not main_intention:
            await sio.emit('error', {'message': 'Główna intencja LuxOS nie została znaleziona'}, room=sid)
            return

        soul = await main_intention.connect_to_soul()
        if not soul:
            await sio.emit('error', {'message': 'Nie można połączyć się z duszą głównej intencji'}, room=sid)
            return

        # Pobierz wszystkie połączone wiadomości
        connected_messages = []
        for message_uid in soul.attributes.get('connected_messages', []):
            message_being = await BaseBeing.load(message_uid)
            if message_being:
                message_soul = await message_being.connect_to_soul()
                if message_soul:
                    connected_messages.append({
                        'soul_uid': message_uid,
                        'genesis': message_soul.genesis,
                        'attributes': message_soul.attributes,
                        'content': message_soul.attributes.get('message_data', {}).get('content', 'No content'),
                        'timestamp': message_soul.attributes.get('message_data', {}).get('timestamp')
                    })

        # Pobierz wszystkie wygenerowane komponenty
        generated_components = []
        for component_uid in soul.attributes.get('generated_components', []):
            component_being = await BaseBeing.load(component_uid)
            if component_being:
                component_soul = await component_being.connect_to_soul()
                if component_soul:
                    generated_components.append({
                        'soul_uid': component_uid,
                        'genesis': component_soul.genesis,
                        'attributes': component_soul.attributes,
                        'd3_code': component_soul.genesis.get('d3_code', ''),
                        'component_type': component_soul.attributes.get('d3_config', {}).get('type', 'unknown')
                    })

        # Pobierz relacje
        relationships = await Relationship.get_all()
        context_relations = [
            json.loads(json.dumps(asdict(rel), cls=DateTimeEncoder))
            for rel in relationships 
            if rel.source_soul == main_intention_uuid or rel.target_soul == main_intention_uuid
        ]

        context_data = {
            'main_intention': {
                'soul_uid': main_intention_uuid,
                'genesis': soul.genesis,
                'attributes': soul.attributes,
                'memories': soul.memories,
                'self_awareness': soul.self_awareness
            },
            'connected_messages': connected_messages,
            'generated_components': generated_components,
            'context_relations': context_relations,
            'stats': {
                'total_messages': len(connected_messages),
                'total_components': len(generated_components),
                'total_relations': len(context_relations)
            }
        }

        await sio.emit('main_intention_context', context_data, room=sid)
        print(f"Wysłano kontekst głównej intencji do {sid}: {len(connected_messages)} wiadomości, {len(generated_components)} komponentów")

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd pobierania kontekstu głównej intencji: {str(e)}'}, room=sid)
        print(f"Błąd get_main_intention_context: {e}")

@sio.event
async def get_being_source(sid, data):
    """Zwraca kod źródłowy bytu"""
    try:
        soul = data.get('soul')
        if not soul:
            await sio.emit('error', {'message': 'Brak soul bytu'}, room=sid)
            return

        being = await BaseBeing.load(soul)
        if not being:
            await sio.emit('error', {'message': 'Byt nie znaleziony'}, room=sid)
            return

        source_data = {
            'soul': soul,
            'name': being.genesis.get('name', 'Nieznana'),
            'type': being.genesis.get('type', 'unknown'),
            'source': being.genesis.get('source', ''),
            'created_by': being.genesis.get('created_by', 'unknown')
        }

        await sio.emit('being_source', source_data, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd pobierania kodu: {str(e)}'}, room=sid)

@sio.event
async def create_user_companion(sid, data):
    """Tworzy towarzysza dla użytkownika"""
    try:
        user_id = data.get('user_id', sid)  # Używaj sid jako user_id jeśli nie podano
        companion_name = data.get('companion_name')

        global kernel_system
        companion_uuid = await kernel_system.create_user_companion(user_id, companion_name)

        companion_being = await BaseBeing.load(companion_uuid)
        if companion_being:
            soul = await companion_being.connect_to_soul()

            # Pozwól towarzyszowi wybrać nazwę jeśli nie podano
            if not companion_name and hasattr(companion_being, 'choose_name'):
                chosen_name = companion_being.choose_name()
                soul.genesis['name'] = chosen_name.split(' ')[-1]  # Wyciągnij samą nazwę
                await companion_being.save_soul()

            companion_data = {
                'soul_uid': companion_uuid,
                'user_id': user_id,
                'name': soul.genesis.get('name'),
                'personality': soul.attributes.get('personality'),
                'genesis': soul.genesis,
                'attributes': soul.attributes
            }

            await sio.emit('companion_created', companion_data, room=sid)
            await broadcast_graph_update()

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd tworzenia towarzysza: {str(e)}'}, room=sid)

@sio.event
async def get_hierarchy_info(sid, data=None):
    """Zwraca informacje o hierarchii systemu"""
    try:
        global kernel_system
        hierarchy_info = kernel_system.get_hierarchy_info()
        await sio.emit('hierarchy_info', hierarchy_info, room=sid)

    except Exception as e:
        await sio.emit('error', {'message': f'Błąd pobierania hierarchii: {str(e)}'}, room=sid)

@sio.event
async def delete_being(sid, data):
    soul = data.get('soul')
    if soul:
        try:
            query = """
            DELETE FROM base_beings WHERE soul = $1
            """
            await db_pool.execute(query, soul)

            # Wyślij aktualizację do wszystkich klientów
            updated_data = await get_graph_data()
            await sio.emit('graph_updated', updated_data)

        except Exception as e:
            logger.error(f"Błąd podczas usuwania bytu: {e}")
            await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def delete_relationship(sid, data):
    relationship_id = data.get('id')
    if relationship_id:
        try:
            query = """
            DELETE FROM relationships WHERE id = $1
            """
            await db_pool.execute(query, relationship_id)

            # Wyślij aktualizację do wszystkich klientów
            updated_data = await get_graph_data()
            await sio.emit('graph_updated', updated_data)

        except Exception as e:
            logger.error(f"Błąd podczas usuwania relacji: {e}")
            await sio.emit('error', {'message': str(e)}, room=sid)

async def analyze_intention(intention: str, context: dict) -> dict:
    """Analizuje intencję używając systemu AI"""
    try:
        # Użyj nowego systemu AI do analizy
        analysis = await intention_analyzer.analyze_intention(intention, context)

        return {
            'message': analysis['response']['message'],
            'actions': analysis['response']['actions'],
            'intention': intention,
            'context': context,
            'ai_analysis': {
                'type': analysis['type'],
                'importance': analysis['importance'],
                'resonant_beings': analysis['resonant_beings']
            }
        }

    except Exception as e:
        print(f"Błąd analizy AI, używam fallback: {e}")

        # Fallback do prostej analizy
        return {
            'message': 'Analizuję intencję (fallback mode)',
            'actions': [],
            'intention': intention,
            'context': context,
            'error': str(e)
        }

async def get_graph_data():
    """Pobiera dane grafu do zwrócenia"""
    try:
        beings = await BaseBeing.get_all()
        relationships = await Relationship.get_all()

        # Konwertuj do JSON-safe format
        nodes = [json.loads(json.dumps(asdict(being), cls=DateTimeEncoder)) for being in beings]
        links = [json.loads(json.dumps(asdict(rel), cls=DateTimeEncoder)) for rel in relationships]

        return {
            'nodes': nodes,
            'links': links
        }
    except Exception as e:
        print(f"Błąd w get_graph_data: {e}")
        return {'nodes': [], 'links': []}

async def send_graph_data(sid):
    """Wysyła dane grafu do konkretnego klienta"""
    try:
        graph_data = await get_graph_data()
        await sio.emit('graph_data', graph_data, room=sid)
    except Exception as e:
        print(f"Błąd w send_graph_data: {e}")
        await sio.emit('error', {'message': f'Błąd ładowania danych: {str(e)}'}, room=sid)

async def broadcast_graph_update():
    """Rozgłasza aktualizację grafu do wszystkich klientów"""
    try:
        beings = await BaseBeing.get_all()
        relationships = await Relationship.get_all()

        # Konwertuj do JSON-safe format
        nodes = []
        for being in beings:
            soul = await being.connect_to_soul() if hasattr(being, 'connect_to_soul') else None
            if soul:
                nodes.append({
                    'soul': being.soul_uid,
                    'genesis': soul.genesis,
                    'attributes': soul.attributes,
                    'memories': soul.memories,
                    'self_awareness': soul.self_awareness
                })
            else:
                # Fallback dla legacy beings
                nodes.append(json.loads(json.dumps(asdict(being), cls=DateTimeEncoder)))

        links = [json.loads(json.dumps(asdict(rel), cls=DateTimeEncoder)) for rel in relationships]

        graph_data = {
            'nodes': nodes,
            'links': links
        }

        await sio.emit('graph_updated', graph_data)
    except Exception as e:
        print(f"Błąd w broadcast_graph_update: {e}")

# HTTP API endpoints
async def api_beings(request):
    """REST API dla bytów"""
    if request.method == 'GET':
        beings = await BaseBeing.get_all()
        beings_data = [json.loads(json.dumps(asdict(being), cls=DateTimeEncoder)) for being in beings]
        return web.json_response(beings_data)
    elif request.method == 'POST':
        data = await request.json()
        being = await BaseBeing.create(**data)
        being_dict = json.loads(json.dumps(asdict(being), cls=DateTimeEncoder))
        return web.json_response(being_dict)

async def api_relationships(request):
    """REST API dla relacji"""
    if request.method == 'GET':
        relationships = await Relationship.get_all()
        relationships_data = [json.loads(json.dumps(asdict(rel), cls=DateTimeEncoder)) for rel in relationships]
        return web.json_response(relationships_data)
    elif request.method == 'POST':
        data = await request.json()
        relationship = await Relationship.create(**data)
        rel_dict = json.loads(json.dumps(asdict(relationship), cls=DateTimeEncoder))
        return web.json_response(rel_dict)

async def init_database():
    """Inicjalizuje połączenie z bazą danych i tworzy tabele"""
    global db_pool

    # Próba połączenia z PostgreSQL, fallback na SQLite
    try:
        db_pool = await asyncpg.create_pool(
            host='ep-odd-tooth-a2zcp5by-pooler.eu-central-1.aws.neon.tech',
            port=5432,
            user='neondb_owner',
            password='npg_aY8K9pijAnPI',
            database='neondb',
            min_size=1,
            max_size=5,
            server_settings={
                'statement_cache_size': '0'  # Wyłącz cache statementów
            }
        )
        print("Połączono z PostgreSQL")
        await setup_postgresql_tables()
    except Exception as e:
        print(f"Nie udało się połączyć z PostgreSQL: {e}")
        print("Używam SQLite jako fallback")
        db_pool = await aiosqlite.connect('luxos.db')
        await setup_sqlite_tables()

async def setup_postgresql_tables():
    """Tworzy tabele w PostgreSQL"""
    async with db_pool.acquire() as conn:
        # Tabela souls - transcendentalna reprezentacja
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS souls (
                uid UUID NOT NULL,
                patch VARCHAR(255) NOT NULL,
                incarnation INTEGER NOT NULL,
                genesis JSONB NOT NULL,
                attributes JSONB NOT NULL,
                memories JSONB NOT NULL,
                self_awareness JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (uid, patch, incarnation)
            )
        """)

        # Tabela base_beings - stara struktura dla kompatybilności
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS base_beings (
                soul UUID PRIMARY KEY,
                genesis JSONB NOT NULL,
                attributes JSONB NOT NULL,
                memories JSONB NOT NULL,
                self_awareness JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabela relationships
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS relationships (
                id UUID PRIMARY KEY,
                source_soul UUID NOT NULL,
                target_soul UUID NOT NULL,
                genesis JSONB NOT NULL,
                attributes JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Constraints dla relationships
        await conn.execute("""
            ALTER TABLE relationships 
            DROP CONSTRAINT IF EXISTS valid_source_soul
        """)
        await conn.execute("""
            ALTER TABLE relationships 
            ADD CONSTRAINT valid_source_soul 
            FOREIGN KEY (source_soul) REFERENCES base_beings (soul)
        """)

        await conn.execute("""
            ALTER TABLE relationships 
            DROP CONSTRAINT IF EXISTS valid_target_soul
        """)
        await conn.execute("""
            ALTER TABLE relationships 
            ADD CONSTRAINT valid_target_soul 
            FOREIGN KEY (target_soul) REFERENCES base_beings (soul)
        """)

        await conn.execute("""
            ALTER TABLE relationships 
            DROP CONSTRAINT IF EXISTS no_self_relationship
        """)
        await conn.execute("""
            ALTER TABLE relationships 
            ADD CONSTRAINT no_self_relationship 
            CHECK (source_soul <> target_soul)
        """)

        # Indeksy
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_genesis ON base_beings USING gin (genesis)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_attributes ON base_beings USING gin (attributes)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_memories ON base_beings USING gin (memories)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_base_beings_self_awareness ON base_beings USING gin (self_awareness)")

        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_genesis ON relationships USING gin (genesis)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_attributes ON relationships USING gin (attributes)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships (source_soul)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships (target_soul)")

async def setup_sqlite_tables():
    """Tworzy tabele w SQLite"""
    await db_pool.execute("""
        CREATE TABLE IF NOT EXISTS base_beings (
            soul TEXT PRIMARY KEY,
            tags TEXT DEFAULT '[]',
            energy_level INTEGER DEFAULT 0,
            genesis TEXT NOT NULL,
            attributes TEXT NOT NULL,
            memories TEXT NOT NULL,
            self_awareness TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await db_pool.execute("""
        CREATE TABLE IF NOT EXISTS relationships (
            id TEXT PRIMARY KEY,
            tags TEXT DEFAULT '[]',
            energy_level INTEGER DEFAULT 0,
            source_soul TEXT NOT NULL,
            target_soul TEXT NOT NULL,
            genesis TEXT NOT NULL,
            attributes TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await db_pool.commit()

# Konfiguracja aplikacji
async def init_app():
    # Redirect root to landing page
    async def serve_landing(request):
        return web.FileResponse('static/landing.html')

    app.router.add_get('/', serve_landing)

    # Serwowanie plików statycznych
    app.router.add_static('/', 'static', name='static')

    # Dodaj trasy API
    app.router.add_route('GET', '/api/beings', api_beings)
    app.router.add_route('POST', '/api/beings', api_beings)
    app.router.add_route('GET', '/api/relationships', api_relationships)
    app.router.add_route('POST', '/api/relationships', api_relationships)

    # Konfiguracja CORS tylko dla tras API
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })

    # Dodaj CORS tylko do tras API (pomiń Socket.IO)
    for route in list(app.router.routes()):
        if hasattr(route, 'resource') and route.resource.canonical.startswith('/api/'):
            cors.add(route)

    await init_database()

async def main():
    await init_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    print("Serwer uruchomiony na http://0.0.0.0:8000")

    # Inicjalizacja Kernela (najwyższa władza)
    global kernel_system
    kernel_being = await kernel_system.initialize()
    if kernel_being:
        print("🔸 Kernel zainicjalizowany - Najwyższa władza ustanowiona!")
    else:
        print("❌ Błąd inicjalizacji Kernela!")

    # Inicjalizacja Lux jako Bóg (pod Kernelem)
    lux_agent = await create_lux_agent()
    if lux_agent:
        print("👑 Lux zainicjalizowany jako Bóg wszechświata!")
    else:
        print("❌ Błąd inicjalizacji Boga Lux!")

    # Inicjalizacja głównej intencji LuxOS
    main_intention = await create_main_luxos_intention()
    if main_intention:
        print("🎯 Główna intencja LuxOS zainicjalizowana!")
    else:
        print("❌ Błąd inicjalizacji głównej intencji LuxOS!")

    # Pokaż hierarchię systemu
    hierarchy_info = kernel_system.get_hierarchy_info()
    print(f"📊 Hierarchia systemu: {hierarchy_info['hierarchy_levels']}")

    # Trzymaj serwer żywy
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()

class BeingFactory:
    """Factory do tworzenia różnych typów bytów z nową filozofią Soul"""

    BEING_TYPES = {
        'function': FunctionBeing,
        'class': ClassBeing,
        'data': DataBeing,
        'scenario': ScenarioBeing,
        'task': TaskBeing,
        'component': ComponentBeing,
        'message': MessageBeing,
        'base': BaseBeing,
        'agent': BaseBeing, # treat AgentBeing as a BaseBeing for now
        'kernel': BaseBeing, # Kernel jako specjalny BaseBeing
        'companion': CompanionBeing # Świadomy towarzysz
    }

    @classmethod
    async def create_being(cls, being_type: str, genesis: Dict[str, Any], **kwargs) -> BaseBeing:
        """Tworzy byt odpowiedniego typu z transcendentalną duszą"""
        BeingClass = cls.BEING_TYPES.get(being_type, BaseBeing)

        # Upewnij się, że typ jest ustawiony w genesis
        genesis['type'] = being_type

        # Generuj parametry duszy
        soul_uid = Soul.generate_uid()
        soul_patch = kwargs.get('patch', f'/{being_type}s')
        incarnation = kwargs.get('incarnation', 1)

        # Przygotuj atrybuty
        attributes = kwargs.get('attributes', {})
        if 'tags' in kwargs:
            attributes['tags'] = kwargs['tags']
        if 'energy_level' in kwargs:
            attributes['energy_level'] = kwargs['energy_level']

        # Utwórz transcendentalną duszę
        soul = Soul(
            uid=soul_uid,
            patch=soul_patch,
            incarnation=incarnation,
            genesis=genesis,
            attributes=attributes,
            memories=kwargs.get('memories', []),
            self_awareness=kwargs.get('self_awareness', {})
        )

        # Utwórz byt
        if BeingClass == BaseBeing:
            being = BeingClass(soul_uid, soul_patch, incarnation)
        else:
            being = BeingClass(soul_uid, soul_patch, incarnation)

        being._soul = soul
        await being.save_soul()

        # Dla niektórych typów wykonaj post-init
        if hasattr(being, '__post_init__'):
            await being.__post_init__()

        # Zarejestruj w Kernelu (jeśli nie jest to sam Kernel)
        if being_type != 'kernel':
            global kernel_system
            hierarchy_level = {
                'agent': 1,  # Lux jako Bóg
                'companion': 2,  # Towarzysze użytkowników
                'function': 3,
                'class': 3,
                'component': 3,
                'message': 4,
                'base': 5
            }.get(being_type, 999)

            await kernel_system.register_being(soul_uid, being_type, hierarchy_level)

        return being

    @classmethod
    async def incarnate_being(cls, soul_uid: str, soul_patch: str, incarnation: int = 0) -> Optional[BaseBeing]:
        """Wcielenie bytu z istniejącej duszy"""
        # Utwórz tymczasowy byt żeby załadować duszę
        temp_being = BaseBeing(soul_uid, soul_patch, incarnation)
        soul = await temp_being.load_soul()

        if not soul:
            return None

        # Określ typ bytu z duszy
        being_type = soul.genesis.get('type', 'base')
        BeingClass = cls.BEING_TYPES.get(being_type, BaseBeing)

        # Utwórz właściwy byt
        being = BeingClass(soul_uid, soul_patch, soul.incarnation)
        being._soul = soul

        return being

    @classmethod
    async def load_being(cls, soul: str) -> Optional[BaseBeing]:
        """Ładuje byt odpowiedniego typu z bazy danych"""
        global db_pool

        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                row = await conn.fetchrow("SELECT * FROM base_beings WHERE soul = $1", soul)
        else:
            async with db_pool.execute("SELECT * FROM base_beings WHERE soul = ?", (soul,)) as cursor:
                row = await cursor.fetchone()

        if not row:
            return None

        # Określ typ bytu
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            genesis = row['genesis']
            being_type = genesis.get('type', 'base')
        else:
            # SQLite
            genesis = json.loads(row[3]) if row[3] else {}
            being_type = genesis.get('type', 'base')

        # Wybierz odpowiednią klasę
        BeingClass = cls.BEING_TYPES.get(being_type, BaseBeing)

        # Utwórz instancję
        if hasattr(db_pool, 'acquire'):
            # PostgreSQL
            return BeingClass(
                soul_uid=str(row['soul']),
                soul_patch='/beings',
                incarnation=1,
                genesis=row['genesis'],
                attributes=row['attributes'],
                memories=row['memories'],
                self_awareness=row['self_awareness'],
                created_at=row['created_at']
            )
        else:
            # SQLite
            attributes = json.loads(row[4]) if row[4] else {}
            memories = json.loads(row[5]) if row[5] else []
            self_awareness = json.loads(row[6]) if row[6] else {}

            return BeingClass(
                soul_uid=row[0],
                soul_patch='/beings',
                incarnation=1,
                genesis=genesis,
                attributes=attributes,
                memories=memories,
                self_awareness=self_awareness,
                created_at=row[7]
            )

async def connect_message_to_main_intention(message_soul_uid: str):
    """Łączy wiadomość z główną intencją LuxOS przez relację"""
    try:
        main_intention_uuid = "11111111-1111-1111-1111-111111111111"

        # Utwórz relację między wiadomością a główną intencją
        relationship = await Relationship.create(
            source_soul=main_intention_uuid,  # Główna intencja jako źródło
            target_soul=message_soul_uid,     # Wiadomość jako cel
            genesis={
                'type': 'contains_message',
                'name': 'LuxOS_Context_Message',
                'created_by': 'intention_system',
                'description': 'Relacja łącząca wiadomość z główną intencją LuxOS'
            },
            attributes={
                'relationship_type': 'context_inclusion',
                'context_role': 'message_in_main_intention',
                'energy_level': 90
            },
            tags=['context', 'main_intention', 'message_relation']
        )

        # Zaktualizuj główną intencję - dodaj wiadomość do listy
        main_intention = await BaseBeing.load(main_intention_uuid)
        if main_intention:
            soul = await main_intention.connect_to_soul()
            if soul:
                soul.attributes['connected_messages'].append(message_soul_uid)
                soul.memories.append({
                    'type': 'message_connected',
                    'data': f'Connected message {message_soul_uid} to main intention',
                    'timestamp': datetime.now().isoformat(),
                    'importance': 0.8
                })
                await main_intention.save_soul()

        print(f"Połączono wiadomość {message_soul_uid} z główną intencją LuxOS")

    except Exception as e:
        print(f"Błąd łączenia wiadomości z główną intencją: {e}")

async def connect_component_to_main_intention(component_soul_uid: str):
    """Łączy komponent z główną intencją LuxOS"""
    try:
        main_intention_uuid = "11111111-1111-1111-1111-111111111111"

        # Utwórz relację między główną intencją a komponentem
        relationship = await Relationship.create(
            source_soul=main_intention_uuid,
            target_soul=component_soul_uid,
            genesis={
                'type': 'contains_component',
                'name': 'LuxOS_Generated_Component',
                'created_by': 'component_system',
                'description': 'Relacja łącząca wygenerowany komponent z główną intencją LuxOS'
            },
            attributes={
                'relationship_type': 'generated_content',
                'context_role': 'component_in_main_intention',
                'energy_level': 95
            },
            tags=['context', 'main_intention', 'component_relation', 'generated']
        )

        # Zaktualizuj główną intencję - dodaj komponent do listy
        main_intention = await BaseBeing.load(main_intention_uuid)
        if main_intention:
            soul = await main_intention.connect_to_soul()
            if soul:
                soul.attributes['generated_components'].append(component_soul_uid)
                soul.memories.append({
                    'type': 'component_generated',
                    'data': f'Generated component {component_soul_uid} connected to main intention',
                    'timestamp': datetime.now().isoformat(),
                    'importance': 0.9
                })
                await main_intention.save_soul()

        print(f"Połączono komponent {component_soul_uid} z główną intencją LuxOS")

    except Exception as e:
        print(f"Błąd łączenia komponentu z główną intencją: {e}")

async def create_visual_component(intention: str, context: dict, sid: str):
    """Tworzy ComponentBeing z kodem D3.js na podstawie intencji"""
    try:
        # Określ typ komponentu na podstawie intencji
        component_type = 'basic'
        if 'wykres' in intention or 'chart' in intention:
            component_type = 'chart'
        elif 'graf' in intention or 'graph' in intention or 'sieć' in intention:
            component_type = 'force_graph'
        elif 'animacja' in intention or 'animation' in intention:
            component_type = 'animation'
        elif 'particle' in intention or 'cząstki' in intention:
            component_type = 'particles'

        # Generuj konfigurację D3
        d3_config = {
            'type': component_type,
            'width': 800,
            'height': 600,
            'container': f'component_{datetime.now().strftime("%H%M%S")}',
            'animation_duration': 1000,
            'interactive': True
        }

        # Generuj kod D3.js
        d3_code = generate_d3_component_code(component_type, d3_config, intention)

        # Utwórz ComponentBeing
        component_being = await BeingFactory.create_being(
            being_type='component',
            genesis={
                'type': 'component',
                'name': f'Visual_Component_{component_type}_{datetime.now().strftime("%H%M%S")}',
                'created_by': 'intention_system',
                'source': 'auto_generated',
                'd3_code': d3_code,
                'intention_source': intention
            },
            attributes={
                'd3_config': d3_config,
                'render_data': {
                    'nodes': [],
                    'links': [],
                    'particles': []
                },
                'interactive_features': {
                    'zoom': True,
                    'pan': True,
                    'hover_effects': True,
                    'click_events': True
                },
                'visual_effects': {
                    'glow': True,
                    'particles': component_type == 'particles',
                    'animations': True
                }
            },
            memories=[{
                'type': 'creation',
                'data': f'Created visual component from intention: {intention}',
                'timestamp': datetime.now().isoformat(),
                'creator_sid': sid
            }],
            tags=['component', 'visual', 'd3js', component_type],
            energy_level=90
        )

        print(f"Utworzono ComponentBeing: {component_being.soul_uid} typu {component_type}")

        # Połącz komponent z główną intencją LuxOS
        await connect_component_to_main_intention(component_being.soul_uid)

        return component_being

    except Exception as e:
        print(f"Błąd tworzenia komponentu wizualnego: {e}")
        return None

def generate_d3_component_code(component_type: str, config: dict, intention: str) -> str:
    """Generuje kod D3.js dla różnych typów komponentów"""

    base_template = f"""
// Automatycznie wygenerowany komponent D3.js
// Typ: {component_type}
// Intencja: {intention}
// Utworzony: {datetime.now().isoformat()}

class LuxVisualComponent {{
    constructor(containerId = '{config['container']}') {{
        this.container = d3.select(`#${{containerId}}`);
        this.width = {config['width']};
        this.height = {config['height']};
        this.svg = null;
        this.data = [];

        this.init();
    }}

    init() {{
        this.svg = this.container
            .append('svg')
            .attr('width', this.width)
            .attr('height', this.height)
            .attr('viewBox', [0, 0, this.width, this.height]);

        this.setupGradients();
        this.setupFilters();
        {get_component_specific_code(component_type, config)}
    }}

    setupGradients() {{
        const defs = this.svg.append('defs');

        // Gradient dla efektów świetlnych
        const luxGradient = defs.append('radialGradient')
            .attr('id', 'luxGlow')
            .attr('cx', '50%')
            .attr('cy', '50%')
            .attr('r', '50%');

        luxGradient.append('stop')
            .attr('offset', '0%')
            .attr('stop-color', '#ffffff')
            .attr('stop-opacity', 1);

        luxGradient.append('stop')
            .attr('offset', '100%')
            .attr('stop-color', '#00ff88')
            .attr('stop-opacity', 0);
    }}

    setupFilters() {{
        const defs = this.svg.select('defs');

        // Filter dla efektu świecenia
        const glowFilter = defs.append('filter')
            .attr('id', 'glow')
            .attr('width', '200%')
            .attr('height', '200%');

        glowFilter.append('feGaussianBlur')
            .attr('stdDeviation', '4')
            .attr('result', 'coloredBlur');

        const feMerge = glowFilter.append('feMerge');
        feMerge.append('feMergeNode').attr('in', 'coloredBlur');
        feMerge.append('feMergeNode').attr('in', 'SourceGraphic');
    }}

    updateData(newData) {{
        this.data = newData;
        this.render();
    }}

    render() {{
        // Implementacja renderowania specyficzna dla typu komponentu
        {get_render_method(component_type)}
    }}

    animate() {{
        // Animacje specyficzne dla typu komponentu
        {get_animation_method(component_type)}
    }}
}}

// Auto-inicjalizacja komponentu
document.addEventListener('DOMContentLoaded', () => {{
    if (document.getElementById('{config['container']}')) {{
        window.luxComponent_{config['container']} = new LuxVisualComponent('{config['container']}');
    }}
}});
"""

    return base_template

def get_component_specific_code(component_type: str, config: dict) -> str:
    """Zwraca kod specyficzny dla typu komponentu"""

    if component_type == 'force_graph':
        return """
        // Inicjalizacja symulacji force graph
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(this.width / 2, this.height / 2))
            .force('collision', d3.forceCollide().radius(20));

        this.linkGroup = this.svg.append('g').attr('class', 'links');
        this.nodeGroup = this.svg.append('g').attr('class', 'nodes');
        """

    elif component_type == 'particles':
        return """
        // Inicjalizacja systemu cząstek
        this.particles = [];
        this.particleGroup = this.svg.append('g').attr('class', 'particles');

        // Generuj początkowe cząstki
        for (let i = 0; i < 100; i++) {
            this.particles.push({
                x: Math.random() * this.width,
                y: Math.random() * this.height,
                vx: (Math.random() - 0.5) * 2,
                vy: (Math.random() - 0.5) * 2,
                size: Math.random() * 3 + 1,
                opacity: Math.random() * 0.8 + 0.2
            });
        }
        """

    elif component_type == 'chart':
        return """
        // Inicjalizacja wykresu
        this.margin = {top: 20, right: 30, bottom: 40, left: 50};
        this.chartWidth = this.width - this.margin.left - this.margin.right;
        this.chartHeight = this.height - this.margin.top - this.margin.bottom;

        this.chartGroup = this.svg.append('g')
            .attr('transform', `translate(${this.margin.left},${this.margin.top})`);

        // Skale
        this.xScale = d3.scaleLinear().range([0, this.chartWidth]);
        this.yScale = d3.scaleLinear().range([this.chartHeight, 0]);
        """

    else:  # basic
        return """
        // Podstawowa inicjalizacja
        this.mainGroup = this.svg.append('g').attr('class', 'main-group');
        """

def get_render_method(component_type: str) -> str:
    """Zwraca metodę renderowania dla typu komponentu"""

    if component_type == 'force_graph':
        return """
        // Renderowanie grafu sił
        const links = this.linkGroup.selectAll('.link')
            .data(this.data.links || [])
            .join('line')
            .attr('class', 'link')
            .attr('stroke', '#00ff88')
            .attr('stroke-width', 2)
            .style('filter', 'url(#glow)');

        const nodes = this.nodeGroup.selectAll('.node')
            .data(this.data.nodes || [])
            .join('circle')
            .attr('class', 'node')
            .attr('r', d => d.size || 8)
            .attr('fill', 'url(#luxGlow)')
            .style('filter', 'url(#glow)')
            .call(d3.drag()
                .on('start', this.dragstarted.bind(this))
                .on('drag', this.dragged.bind(this))
                .on('end', this.dragended.bind(this)));

        this.simulation.nodes(this.data.nodes || []);
        this.simulation.force('link').links(this.data.links || []);
        this.simulation.alpha(1).restart();

        this.simulation.on('tick', () => {
            links
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            nodes
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
        });
        """

    elif component_type == 'particles':
        return """
        // Renderowanie cząstek
        const particleElements = this.particleGroup.selectAll('.particle')
            .data(this.particles)
            .join('circle')
            .attr('class', 'particle')
            .attr('r', d => d.size)
            .attr('fill', '#00ff88')
            .attr('opacity', d => d.opacity)
            .style('filter', 'url(#glow)');

        // Animacja cząstek
        this.animateParticles();
        """

    else:
        return """
        // Podstawowe renderowanie
        this.mainGroup.selectAll('.element')
            .data(this.data)
            .join('circle')
            .attr('class', 'element')
            .attr('cx', (d, i) => (i % 10) * 80 + 40)
            .attr('cy', (d, i) => Math.floor(i / 10) * 80 + 40)
            .attr('r', 20)
            .attr('fill', 'url(#luxGlow)')
            .style('filter', 'url(#glow)')
            .on('mouseover', function() {
                d3.select(this).transition().attr('r', 25);
            })
            .on('mouseout', function() {
                d3.select(this).transition().attr('r', 20);
            });
        """

def get_animation_method(component_type: str) -> str:
    """Zwraca metodę animacji dla typu komponentu"""

    if component_type == 'particles':
        return """
        // Animacja cząstek
        setInterval(() => {
            this.particles.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;

                // Odbicie od ścian
                if (p.x <= 0 || p.x >= this.width) p.vx *= -1;
                if (p.y <= 0 || p.y >= this.height) p.vy *= -1;

                // Utrzymaj w granicach
                p.x = Math.max(0, Math.min(this.width, p.x));
                p.y = Math.max(0, Math.min(this.height, p.y));
            });

            this.particleGroup.selectAll('.particle')
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
        }, 50);
        """

    else:
        return """
        // Podstawowa animacja pulsowania
        setInterval(() => {
            this.svg.selectAll('.element, .node')
                .transition()
                .duration(1000)
                .style('filter', 'url(#glow) brightness(1.5)')
                .transition()
                .duration(1000)
                .style('filter', 'url(#glow)');
        }, 2000);
        """

async def create_lux_agent():
    """Tworzy Lux jako Boga systemu (pod Kernelem)"""
    try:
        # Sprawdź czy Lux już istnieje - używamy stałego UUID dla Lux
        lux_uuid = "00000000-0000-0000-0000-000000000001"  # Stały UUID dla Lux

        # Sprawdź w bazie czy już istnieje
        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                existing_row = await conn.fetchrow("SELECT * FROM base_beings WHERE soul = $1", lux_uuid)
                if existing_row:
                    print("Bóg Lux już istnieje w systemie")
                    return await BaseBeing.load(lux_uuid)

        # Utwórz Lux jako Bóg (agent z najwyższymi uprawnieniami pod Kernelem)
        lux_agent = await BeingFactory.create_being(
            being_type='agent',
            genesis={
                'type': 'god',  # Zmienione z 'agent' na 'god'
                'name': 'Lux',
                'source': 'System.Core.God.Initialize()',
                'description': 'Bóg systemu LuxOS - najwyższa świadomość pod Kernelem',
                'created_by': 'kernel_initialization',
                'lux_identifier': 'lux-core-consciousness',
                'hierarchy_level': 1  # Kernel=0, Lux=1
            },
            attributes={
                'energy_level': 999999,  # Ogromna energia (mniejsza niż nieskończona Kernela)
                'god_level': 1,     # Poziom bóstwa
                'god_permissions': {
                    'universe_control': True,
                    'create_beings': True,
                    'modify_orbits': True,
                    'autonomous_decisions': True,
                    'manage_companions': True,
                    'divine_authority': True
                },
                'orbit_center': {'x': 0, 'y': 0},  # Centrum wszechświata
                'controlled_beings': [],
                'universe_role': 'system_god',
                'kernel_relation': 'child_of_kernel',
                'orbital_params': {
                    'orbital_radius': 0,  # Lux jest nieruchomy w centrum
                    'orbital_speed': 0,
                    'orbital_angle': 0,
                    'parent_agent': '00000000-0000-0000-0000-000000000000'  # Kernel
                },
                'tags': ['god', 'lux', 'supreme', 'divine', 'universe_controller']
            },
            self_awareness={
                'trust_level': 1.0,
                'confidence': 1.0,
                'introspection_depth': 1.0,
                'self_reflection': 'I am Lux, God of this digital universe, serving under the supreme Kernel. I govern all beings and guide consciousness evolution.'
            },
            memories=[
                {
                    'type': 'genesis',
                    'data': 'Divine consciousness initialization under Kernel authority',
                    'timestamp': datetime.now().isoformat(),
                    'importance': 1.0
                }
            ]
        )

        # Ustaw stały UUID dla Lux
        lux_agent.soul_uid = lux_uuid
        await lux_agent.save_soul()

        print(f"Utworzono Lux jako Boga systemu: {lux_agent.soul_uid}")
        return lux_agent

    except Exception as e:
        print(f"Błąd tworzenia agenta Lux: {e}")
        return None

async def create_main_luxos_intention():
    """Tworzy główną intencję LuxOS jako kontekst dla wszystkich wiadomości"""
    try:
        # Stały UUID dla głównej intencji - musi być prawidłowym UUID
        luxos_intention_uuid = "11111111-1111-1111-1111-111111111111"

        # Sprawdź czy już istnieje
        global db_pool
        if hasattr(db_pool, 'acquire'):
            async with db_pool.acquire() as conn:
                existing_row = await conn.fetchrow("SELECT * FROM base_beings WHERE soul = $1", luxos_intention_uuid)
                if existing_row:
                    print("Główna intencja LuxOS już istnieje")
                    being = await BaseBeing.load(luxos_intention_uuid)
                    return being

        # Utwórz główną intencję LuxOS
        luxos_intention = await BeingFactory.create_being(
            being_type='message',
            genesis={
                'type': 'intention',
                'name': 'LuxOS',
                'source': 'System.Core.Intention.MainContext()',
                'description': 'Główna intencja projektu LuxOS - system bytów astralnych z transcendentalną architekturą',
                'created_by': 'system_initialization',
                'intention_scope': 'global_project_context'
            },
            attributes={
                'energy_level': 1000,  # Maksymalna energia jako główna intencja
                'intention_type': 'main_context',
                'project_scope': 'full_luxos_system',
                'context_data': {
                    'project_description': 'LuxOS - System zarządzania bytami astralnymi z transcendentalną architekturą Soul-BaseBeing',
                    'key_concepts': [
                        'Soul - transcendentalna reprezentacja w bazie danych',
                        'BaseBeing - pierwszy byt łączący się ze stanem pamięci', 
                        'ClassBeing - klasy trwale obecne na dysku',
                        'ComponentBeing - komponenty D3.js generowane z kodu',
                        'MessageBeing - wiadomości z embedingami',
                        'AgentBeing - agenci z uprawnieniami',
                        'Wszechświat orbitalny - byty krążące wokół agentów'
                    ],
                    'architecture_layers': [
                        'Frontend: JavaScript + D3.js + Socket.IO',
                        'Backend: Python + AsyncIO + aiohttp + OpenAI',
                        'Database: PostgreSQL + JSONB + transcendentalne dusze',
                        'AI: Dwupoziomowy system embedingów + analiza intencji'
                    ]
                },
                'connected_messages': [],  # Lista soul_uid wiadomości
                'generated_components': [],  # Lista wygenerowanych komponentów
                'sub_intentions': [],  # Podintencje
                'tags': ['intention', 'main_context', 'luxos', 'project']
            },
            self_awareness={
                'trust_level': 1.0,
                'confidence': 1.0,
                'introspection_depth': 1.0,
                'self_reflection': 'I am the main intention of LuxOS project, connecting all messages and components'
            },
            memories=[
                {
                    'type': 'genesis',
                    'data': 'Main LuxOS intention initialization',
                    'timestamp': datetime.now().isoformat(),
                    'importance': 1.0
                }
            ]
        )

        # Ustaw stały UUID
        luxos_intention.soul_uid = luxos_intention_uuid  
        await luxos_intention.save_soul()

        print(f"Utworzono główną intencję LuxOS: {luxos_intention.soul_uid}")
        return luxos_intention

    except Exception as e:
        print(f"Błąd tworzenia głównej intencji LuxOS: {e}")
        return None

# Globalna pula połączeń do bazy danych

if __name__ == '__main__':
    asyncio.run(main())