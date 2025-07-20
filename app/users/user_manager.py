
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import uuid
import logging

from ..beings.base_being import BaseBeing
from ..beings.agent_being import AgentBeing
from ..database.connection import DatabaseManager

logger = logging.getLogger(__name__)

class UserManager:
    """Menedżer użytkowników systemu"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_agents: Dict[str, AgentBeing] = {}  # user_id -> agent
        self.user_sessions: Dict[str, dict] = {}      # user_id -> session_data
        self.inactive_threshold = timedelta(hours=24)
    
    async def initialize(self):
        """Inicjalizuje menedżer użytkowników"""
        logger.info("👥 Inicjalizacja User Manager...")
        
        # Załaduj aktywnych użytkowników z bazy
        await self.load_existing_users()
        
        logger.info(f"✅ User Manager zainicjalizowany: {len(self.user_agents)} użytkowników")
    
    async def get_or_create_user(self, fingerprint: str) -> str:
        """Pobiera lub tworzy użytkownika na podstawie fingerprint"""
        # Sprawdź czy użytkownik już istnieje
        user_id = await self.find_user_by_fingerprint(fingerprint)
        
        if not user_id:
            # Utwórz nowego użytkownika
            user_id = await self.create_new_user(fingerprint)
        else:
            # Aktualizuj sesję istniejącego użytkownika
            await self.update_user_session(user_id)
        
        return user_id
    
    async def find_user_by_fingerprint(self, fingerprint: str) -> Optional[str]:
        """Znajduje użytkownika po fingerprint"""
        try:
            # Wyszukaj w bazie danych bytów z typem 'user_agent'
            beings = await BaseBeing.get_all(limit=1000)
            
            for being in beings:
                if (being.genesis.get('type') == 'user_agent' and
                    being.attributes.get('fingerprint') == fingerprint):
                    return being.soul
            
            return None
        except Exception as e:
            logger.error(f"Błąd wyszukiwania użytkownika: {e}")
            return None
    
    async def create_new_user(self, fingerprint: str) -> str:
        """Tworzy nowego użytkownika"""
        user_id = str(uuid.uuid4())
        
        logger.info(f"👤 Tworzenie nowego użytkownika: {user_id[:8]}...")
        
        # Utwórz agenta użytkownika
        user_agent = await AgentBeing.create(
            soul=user_id,
            genesis={
                'type': 'user_agent',
                'name': f'User Agent {fingerprint[:8]}',
                'description': f'Agent zarządzający użytkownikiem z fingerprint {fingerprint}',
                'created_by': 'kernel_user_manager',
                'version': '1.0.0'
            },
            attributes={
                'energy_level': 500,
                'agent_level': 5,
                'fingerprint': fingerprint,
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'session_count': 1,
                'user_preferences': {},
                'managed_beings': [],
                'active_projects': [],
                'tags': ['user_agent', 'active']
            },
            self_awareness={
                'trust_level': 0.7,
                'confidence': 0.6,
                'introspection_depth': 0.5,
                'self_reflection': f'I manage user with fingerprint {fingerprint[:8]}...'
            },
            memories=[{
                'type': 'user_creation',
                'data': f'Created for fingerprint {fingerprint}',
                'timestamp': datetime.now().isoformat(),
                'importance': 1.0
            }]
        )
        
        # Zarejestruj w pamięci
        self.user_agents[user_id] = user_agent
        self.user_sessions[user_id] = {
            'fingerprint': fingerprint,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'session_count': 1,
            'active': True
        }
        
        return user_id
    
    async def update_user_session(self, user_id: str):
        """Aktualizuje sesję użytkownika"""
        if user_id not in self.user_agents:
            # Załaduj użytkownika z bazy
            user_agent = await AgentBeing.load(user_id)
            if user_agent:
                self.user_agents[user_id] = user_agent
        
        # Aktualizuj sesję
        if user_id in self.user_sessions:
            self.user_sessions[user_id]['last_activity'] = datetime.now()
            self.user_sessions[user_id]['session_count'] += 1
        else:
            # Odtwórz sesję z danych agenta
            user_agent = self.user_agents.get(user_id)
            if user_agent:
                self.user_sessions[user_id] = {
                    'fingerprint': user_agent.attributes.get('fingerprint', 'unknown'),
                    'created_at': datetime.fromisoformat(user_agent.attributes.get('created_at', datetime.now().isoformat())),
                    'last_activity': datetime.now(),
                    'session_count': user_agent.attributes.get('session_count', 0) + 1,
                    'active': True
                }
        
        # Zapisz w agencie użytkownika
        user_agent = self.user_agents.get(user_id)
        if user_agent:
            user_agent.attributes['last_activity'] = datetime.now().isoformat()
            user_agent.attributes['session_count'] = self.user_sessions[user_id]['session_count']
            
            memory = {
                'type': 'session_update',
                'data': f'Session updated, count: {self.user_sessions[user_id]["session_count"]}',
                'timestamp': datetime.now().isoformat(),
                'importance': 0.3
            }
            user_agent.memories.append(memory)
            
            await user_agent.save()
    
    async def load_existing_users(self):
        """Ładuje istniejących użytkowników z bazy"""
        try:
            beings = await BaseBeing.get_all(limit=1000)
            
            for being in beings:
                if being.genesis.get('type') == 'user_agent':
                    # Sprawdź czy użytkownik był aktywny ostatnio
                    last_activity_str = being.attributes.get('last_activity')
                    if last_activity_str:
                        last_activity = datetime.fromisoformat(last_activity_str)
                        if datetime.now() - last_activity < self.inactive_threshold:
                            # Załaduj jako AgentBeing
                            user_agent = await AgentBeing.load(being.soul)
                            if user_agent:
                                self.user_agents[being.soul] = user_agent
                                
                                self.user_sessions[being.soul] = {
                                    'fingerprint': being.attributes.get('fingerprint', 'unknown'),
                                    'created_at': datetime.fromisoformat(being.attributes.get('created_at', datetime.now().isoformat())),
                                    'last_activity': last_activity,
                                    'session_count': being.attributes.get('session_count', 0),
                                    'active': False  # Nie jest połączony
                                }
            
            logger.info(f"Załadowano {len(self.user_agents)} użytkowników z bazy")
            
        except Exception as e:
            logger.error(f"Błąd ładowania użytkowników: {e}")
    
    async def process_user_tasks(self):
        """Przetwarza zadania użytkowników"""
        for user_id, user_agent in self.user_agents.items():
            try:
                # Sprawdź czy użytkownik ma zadania do przetworzenia
                await self.process_user_orbital_tasks(user_id, user_agent)
                
            except Exception as e:
                logger.error(f"Błąd przetwarzania zadań użytkownika {user_id[:8]}...: {e}")
    
    async def process_user_orbital_tasks(self, user_id: str, user_agent: AgentBeing):
        """Przetwarza zadania orbitalne użytkownika"""
        # Znajdź wszystkie orbital tasks użytkownika
        managed_beings = user_agent.attributes.get('managed_beings', [])
        
        for being_id in managed_beings:
            try:
                being = await BaseBeing.load(being_id)
                if being and being.genesis.get('type') == 'orbital_task':
                    # Sprawdź czy nadszedł czas na cykl
                    # Implementacja będzie dodana w kolejnym pliku
                    pass
                    
            except Exception as e:
                logger.error(f"Błąd przetwarzania orbital task {being_id}: {e}")
    
    async def cleanup_inactive_users(self):
        """Czyści nieaktywnych użytkowników"""
        inactive_users = []
        current_time = datetime.now()
        
        for user_id, session in self.user_sessions.items():
            if current_time - session['last_activity'] > self.inactive_threshold:
                inactive_users.append(user_id)
        
        for user_id in inactive_users:
            logger.info(f"🧹 Czyszczenie nieaktywnego użytkownika: {user_id[:8]}...")
            
            # Oznacz jako nieaktywny ale nie usuwaj z bazy
            if user_id in self.user_agents:
                user_agent = self.user_agents[user_id]
                user_agent.attributes['tags'] = [t for t in user_agent.attributes.get('tags', []) if t != 'active']
                user_agent.attributes['tags'].append('inactive')
                await user_agent.save()
                
                del self.user_agents[user_id]
            
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
    
    def get_user_count(self) -> int:
        """Zwraca liczbę aktywnych użytkowników"""
        return len(self.user_agents)
    
    def get_active_users(self) -> List[str]:
        """Zwraca listę aktywnych użytkowników"""
        return list(self.user_agents.keys())
