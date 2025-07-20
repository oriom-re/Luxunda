
#!/usr/bin/env python3
"""
LuxOS Kernel Main - Główny plik inicjalizacyjny systemu
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime

# Import komponentów aplikacji
from app.core.kernel import LuxOSKernel
from app.database.connection import DatabaseManager
from app.utils.fingerprint import FingerprintManager

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('luxos_kernel.log')
    ]
)

logger = logging.getLogger(__name__)

class LuxOSSystem:
    """Główna klasa systemu LuxOS"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.kernel: Optional[LuxOSKernel] = None
        self.running = False
        self.shutdown_event = asyncio.Event()
    
    async def initialize(self) -> bool:
        """Inicjalizuje cały system"""
        logger.info("🚀 Uruchamianie systemu LuxOS...")
        
        # 1. Inicjalizuj bazę danych
        if not await self.db_manager.initialize():
            logger.error("❌ Nie udało się zainicjalizować bazy danych")
            return False
        
        # 2. Utwórz kernel
        self.kernel = LuxOSKernel(self.db_manager)
        
        # 3. Inicjalizuj kernel
        if not await self.kernel.initialize():
            logger.error("❌ Nie udało się zainicjalizować kernela")
            return False
        
        logger.info("✅ System LuxOS zainicjalizowany pomyślnie")
        return True
    
    async def start(self):
        """Uruchamia system"""
        if not await self.initialize():
            logger.error("💥 Inicjalizacja systemu nie powiodła się")
            return
        
        self.running = True
        
        # Konfiguruj obsługę sygnałów
        self.setup_signal_handlers()
        
        logger.info("🌟 System LuxOS uruchomiony - kernel aktywny")
        logger.info(f"🧠 Kernel Soul ID: {self.kernel.KERNEL_SOUL_ID}")
        logger.info(f"👥 Aktywnych użytkowników: {len(self.kernel.active_users)}")
        
        try:
            # Uruchom główną pętlę kernela
            kernel_task = asyncio.create_task(self.kernel.start_main_loop())
            
            # Czekaj na sygnał zamknięcia
            await self.shutdown_event.wait()
            
            # Anuluj zadanie kernela
            kernel_task.cancel()
            
            try:
                await kernel_task
            except asyncio.CancelledError:
                pass
            
        except Exception as e:
            logger.error(f"💥 Błąd w głównej pętli systemu: {e}")
        finally:
            await self.shutdown()
    
    def setup_signal_handlers(self):
        """Konfiguruje obsługę sygnałów systemu"""
        def signal_handler(signum, frame):
            logger.info(f"🛑 Otrzymano sygnał {signum}, zamykanie systemu...")
            asyncio.create_task(self.initiate_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initiate_shutdown(self):
        """Inicjuje zamknięcie systemu"""
        self.shutdown_event.set()
    
    async def shutdown(self):
        """Zamyka system gracefully"""
        logger.info("🛑 Zamykanie systemu LuxOS...")
        
        self.running = False
        
        # Zamknij kernel
        if self.kernel:
            await self.kernel.shutdown()
        
        # Zamknij bazę danych
        if self.db_manager:
            await self.db_manager.close()
        
        logger.info("✅ System LuxOS zamknięty")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Zwraca status systemu"""
        if not self.kernel:
            return {'status': 'not_initialized'}
        
        kernel_state = self.kernel.get_kernel_state()
        
        return {
            'status': 'running' if self.running else 'stopped',
            'kernel_soul': kernel_state.kernel_soul,
            'uptime_seconds': kernel_state.uptime_seconds,
            'active_users': len(kernel_state.active_users),
            'database_type': self.db_manager.db_type,
            'started_at': kernel_state.created_at.isoformat(),
            'last_heartbeat': kernel_state.last_heartbeat.isoformat()
        }

async def main():
    """Główna funkcja uruchamiająca system"""
    logger.info("=" * 60)
    logger.info("🌟 LuxOS - System Bytów Astralnych")
    logger.info("=" * 60)
    
    # Utwórz i uruchom system
    system = LuxOSSystem()
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("⚠️ Przerwano przez użytkownika")
    except Exception as e:
        logger.error(f"💥 Nieoczekiwany błąd: {e}")
        raise
    finally:
        logger.info("👋 System LuxOS zakończony")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Program przerwany przez użytkownika")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Krytyczny błąd: {e}")
        sys.exit(1)
