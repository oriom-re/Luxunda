
import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import logging

from ..database.connection import DatabaseManager
from ..beings.base_being import BaseBeing
from ..beings.agent_being import AgentBeing
from ..users.user_manager import UserManager
from ..utils.fingerprint import FingerprintManager

logger = logging.getLogger(__name__)

@dataclass
class KernelState:
    """Stan kernela systemu"""
    kernel_soul: str
    created_at: datetime
    last_heartbeat: datetime
    active_users: Set[str]
    total_beings: int
    system_health: Dict[str, float]
    uptime_seconds: float

class LuxOSKernel:
    """Główny kermel systemu LuxOS zarządzający użytkownikami i bytami"""
    
    KERNEL_SOUL_ID = "00000000-0000-0000-0000-KERNEL000001"
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.user_manager = UserManager(db_manager)
        self.fingerprint_manager = FingerprintManager()
        
        self.kernel_being: Optional[AgentBeing] = None
        self.running = False
        self.start_time = datetime.now()
        self.active_users: Set[str] = set()
        
        # Metryki systemu
        self.heartbeat_interval = 30  # sekundy
        self.cleanup_interval = 300   # 5 minut
        self.metrics = {
            'total_connections': 0,
            'active_sessions': 0,
            'beings_created': 0,
            'messages_processed': 0
        }
    
    async def initialize(self) -> bool:
        """Inicjalizuje kermel - tworzy lub ładuje z bazy"""
        try:
            logger.info("🚀 Inicjalizacja LuxOS Kernel...")
            
            # Próbuj załadować istniejący kermel
            self.kernel_being = await AgentBeing.load(self.KERNEL_SOUL_ID)
            
            if not self.kernel_being:
                # Utwórz nowy kermel
                logger.info("📱 Tworzenie nowego Kernel Being...")
                self.kernel_being = await self.create_kernel_being()
            else:
                logger.info("♻️ Załadowano istniejący Kernel Being")
                await self.update_kernel_on_restart()
            
            # Inicjalizuj menadżer użytkowników
            await self.user_manager.initialize()
            
            logger.info(f"✅ Kernel zainicjalizowany: {self.kernel_being.soul}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Błąd inicjalizacji kernela: {e}")
            return False
    
    async def create_kernel_being(self) -> AgentBeing:
        """Tworzy nowego kermel-agenta"""
        kernel_being = await AgentBeing.create(
            soul=self.KERNEL_SOUL_ID,
            genesis={
                'type': 'kernel_agent',
                'name': 'LuxOS Kernel',
                'source': 'System.Core.Kernel.Initialize()',
                'description': 'Główny kermel systemu LuxOS zarządzający użytkownikami',
                'kernel_identifier': 'luxos-main-kernel',
                'version': '1.0.0'
            },
            attributes={
                'energy_level': 10000,
                'agent_level': 100,
                'agent_permissions': {
                    'system_control': True,
                    'user_management': True,
                    'create_beings': True,
                    'modify_orbits': True,
                    'autonomous_decisions': True,
                    'database_access': True
                },
                'kernel_config': {
                    'max_users': 1000,
                    'heartbeat_interval': self.heartbeat_interval,
                    'cleanup_interval': self.cleanup_interval,
                    'auto_cleanup': True
                },
                'system_role': 'main_kernel',
                'managed_users': [],
                'system_metrics': self.metrics.copy(),
                'tags': ['kernel', 'agent', 'system', 'manager']
            },
            self_awareness={
                'trust_level': 1.0,
                'confidence': 1.0,
                'introspection_depth': 1.0,
                'self_reflection': 'I am the LuxOS Kernel, managing all system operations'
            },
            memories=[{
                'type': 'kernel_genesis',
                'data': 'System kernel initialization and first boot',
                'timestamp': datetime.now().isoformat(),
                'importance': 1.0
            }]
        )
        
        return kernel_being
    
    async def update_kernel_on_restart(self):
        """Aktualizuje kermel przy restarcie"""
        if not self.kernel_being:
            return
        
        # Aktualizuj metryki restartu
        restart_memory = {
            'type': 'system_restart',
            'data': 'Kernel restarted and reloaded from database',
            'timestamp': datetime.now().isoformat(),
            'previous_uptime': self.kernel_being.attributes.get('last_uptime', 0),
            'importance': 0.8
        }
        
        self.kernel_being.memories.append(restart_memory)
        self.kernel_being.attributes['last_restart'] = datetime.now().isoformat()
        self.kernel_being.attributes['restart_count'] = self.kernel_being.attributes.get('restart_count', 0) + 1
        
        await self.kernel_being.save()
    
    async def start_main_loop(self):
        """Uruchamia główną pętlę kernela"""
        if self.running:
            logger.warning("Kernel już działa!")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("🌟 Uruchamianie głównej pętli Kernel...")
        
        # Uruchom zadania w tle
        tasks = [
            asyncio.create_task(self.heartbeat_loop()),
            asyncio.create_task(self.cleanup_loop()),
            asyncio.create_task(self.user_management_loop()),
            asyncio.create_task(self.metrics_collection_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Błąd w głównej pętli kernela: {e}")
        finally:
            self.running = False
    
    async def heartbeat_loop(self):
        """Pętla heartbeat kernela"""
        while self.running:
            try:
                await self.send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Błąd w heartbeat: {e}")
                await asyncio.sleep(5)
    
    async def send_heartbeat(self):
        """Wysyła heartbeat i aktualizuje stan kernela"""
        if not self.kernel_being:
            return
        
        current_time = datetime.now()
        uptime = (current_time - self.start_time).total_seconds()
        
        # Aktualizuj stan kernela
        self.kernel_being.attributes.update({
            'last_heartbeat': current_time.isoformat(),
            'uptime_seconds': uptime,
            'active_users_count': len(self.active_users),
            'system_metrics': self.metrics.copy(),
            'system_health': await self.calculate_system_health()
        })
        
        await self.kernel_being.save()
        
        logger.debug(f"💓 Heartbeat: {len(self.active_users)} aktywnych użytkowników, uptime: {uptime:.0f}s")
    
    async def cleanup_loop(self):
        """Pętla czyszczenia systemu"""
        while self.running:
            try:
                await self.perform_system_cleanup()
                await asyncio.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"Błąd w cleanup: {e}")
                await asyncio.sleep(30)
    
    async def user_management_loop(self):
        """Pętla zarządzania użytkownikami"""
        while self.running:
            try:
                await self.user_manager.process_user_tasks()
                await asyncio.sleep(10)  # Częstsze sprawdzanie użytkowników
            except Exception as e:
                logger.error(f"Błąd w user management: {e}")
                await asyncio.sleep(15)
    
    async def metrics_collection_loop(self):
        """Pętla zbierania metryk"""
        while self.running:
            try:
                await self.collect_system_metrics()
                await asyncio.sleep(60)  # Co minutę
            except Exception as e:
                logger.error(f"Błąd w metrics collection: {e}")
                await asyncio.sleep(60)
    
    async def register_user_connection(self, fingerprint: str, connection_id: str) -> str:
        """Rejestruje połączenie użytkownika"""
        user_id = await self.user_manager.get_or_create_user(fingerprint)
        self.active_users.add(user_id)
        self.metrics['total_connections'] += 1
        
        logger.info(f"👤 Zarejestrowano użytkownika: {user_id[:8]}... (fingerprint: {fingerprint[:8]}...)")
        
        # Zapisz w pamięci kernela
        if self.kernel_being:
            memory = {
                'type': 'user_connection',
                'user_id': user_id,
                'fingerprint': fingerprint,
                'connection_id': connection_id,
                'timestamp': datetime.now().isoformat(),
                'importance': 0.5
            }
            self.kernel_being.memories.append(memory)
            
            # Ogranicz historię do ostatnich 100 wpisów
            if len(self.kernel_being.memories) > 100:
                self.kernel_being.memories = self.kernel_being.memories[-100:]
            
            await self.kernel_being.save()
        
        return user_id
    
    async def unregister_user_connection(self, user_id: str, connection_id: str):
        """Wyrejestrowuje połączenie użytkownika"""
        self.active_users.discard(user_id)
        
        logger.info(f"👤 Wyrejestrowano użytkownika: {user_id[:8]}...")
        
        # Zapisz w pamięci kernela
        if self.kernel_being:
            memory = {
                'type': 'user_disconnection',
                'user_id': user_id,
                'connection_id': connection_id,
                'timestamp': datetime.now().isoformat(),
                'importance': 0.3
            }
            self.kernel_being.memories.append(memory)
            await self.kernel_being.save()
    
    async def perform_system_cleanup(self):
        """Wykonuje czyszczenie systemu"""
        logger.debug("🧹 Wykonuję czyszczenie systemu...")
        
        # Wyczyść nieaktywnych użytkowników
        await self.user_manager.cleanup_inactive_users()
        
        # Aktualizuj metryki
        self.metrics['active_sessions'] = len(self.active_users)
        
        logger.debug("✅ Czyszczenie systemu zakończone")
    
    async def calculate_system_health(self) -> Dict[str, float]:
        """Oblicza zdrowie systemu"""
        return {
            'cpu_usage': 0.1,  # Placeholder
            'memory_usage': 0.2,  # Placeholder
            'database_health': 0.9,
            'user_satisfaction': 0.8,
            'kernel_stability': 1.0 if self.running else 0.0
        }
    
    async def collect_system_metrics(self):
        """Zbiera metryki systemu"""
        # Pobierz statystyki z bazy
        total_beings = await self.count_total_beings()
        
        self.metrics.update({
            'total_beings': total_beings,
            'active_sessions': len(self.active_users),
            'kernel_uptime': (datetime.now() - self.start_time).total_seconds()
        })
    
    async def count_total_beings(self) -> int:
        """Liczy wszystkie byty w systemie"""
        try:
            beings = await BaseBeing.get_all(limit=10000)
            return len(beings)
        except Exception:
            return 0
    
    async def shutdown(self):
        """Zamyka kermel gracefully"""
        logger.info("🛑 Zamykanie Kernel...")
        
        self.running = False
        
        if self.kernel_being:
            # Zapisz metryki końcowe
            shutdown_memory = {
                'type': 'kernel_shutdown',
                'data': 'Graceful kernel shutdown',
                'final_metrics': self.metrics.copy(),
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds(),
                'timestamp': datetime.now().isoformat(),
                'importance': 0.9
            }
            
            self.kernel_being.memories.append(shutdown_memory)
            self.kernel_being.attributes['last_shutdown'] = datetime.now().isoformat()
            await self.kernel_being.save()
        
        logger.info("✅ Kernel zamknięty")
    
    def get_kernel_state(self) -> KernelState:
        """Zwraca aktualny stan kernela"""
        return KernelState(
            kernel_soul=self.KERNEL_SOUL_ID,
            created_at=self.start_time,
            last_heartbeat=datetime.now(),
            active_users=self.active_users.copy(),
            total_beings=self.metrics.get('total_beings', 0),
            system_health=asyncio.create_task(self.calculate_system_health()),
            uptime_seconds=(datetime.now() - self.start_time).total_seconds()
        )
