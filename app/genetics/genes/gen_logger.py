
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
import aiofiles

class GenLogger:
    """Prosty logger asynchroniczny"""
    
    __gene_metadata__ = {
        'name': 'gen_logger',
        'description': 'Prosty logger asynchroniczny',
        'version': '1.0.0',
        'compatible_types': ['agent', 'function', 'data', 'task'],
        'tags': ['logging', 'debugging', 'monitoring'],
        'energy_cost': 2,
        'dependencies': []
    }
    
    def __init__(self, being_soul: str):
        self.being_soul = being_soul
        self.log_file = f"logs/{being_soul}.log"
        self.log_queue = asyncio.Queue()
        self.is_running = False
        
    async def start_logging(self):
        """Uruchamia asynchroniczne logowanie"""
        if self.is_running:
            return
            
        self.is_running = True
        asyncio.create_task(self._log_worker())
        print(f"📝 Logger uruchomiony dla bytu {self.being_soul}")
    
    async def _log_worker(self):
        """Pracownik logowania działający w tle"""
        try:
            import os
            os.makedirs('logs', exist_ok=True)
            
            async with aiofiles.open(self.log_file, 'a', encoding='utf-8') as f:
                while self.is_running:
                    try:
                        log_entry = await asyncio.wait_for(
                            self.log_queue.get(), 
                            timeout=1.0
                        )
                        await f.write(log_entry + '\n')
                        await f.flush()
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"📝 Błąd w loggerze: {e}")
        except Exception as e:
            print(f"📝 Błąd inicjalizacji loggera: {e}")
    
    async def log(self, level: str, message: str, extra: Dict[str, Any] = None):
        """Loguje wiadomość"""
        if not self.is_running:
            await self.start_logging()
            
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'being_soul': self.being_soul,
            'level': level.upper(),
            'message': message,
            'extra': extra or {},
            'gene_source': 'gen_logger'
        }
        
        formatted_entry = json.dumps(log_entry, ensure_ascii=False)
        await self.log_queue.put(formatted_entry)
        
        # Wyświetl też w konsoli dla ważnych logów
        if level.upper() in ['ERROR', 'CRITICAL']:
            print(f"📝 [{level.upper()}] {self.being_soul}: {message}")
    
    async def info(self, message: str, **kwargs):
        """Log poziomu INFO"""
        await self.log('INFO', message, kwargs)
    
    async def warning(self, message: str, **kwargs):
        """Log poziomu WARNING"""
        await self.log('WARNING', message, kwargs)
    
    async def error(self, message: str, **kwargs):
        """Log poziomu ERROR"""
        await self.log('ERROR', message, kwargs)
    
    async def debug(self, message: str, **kwargs):
        """Log poziomu DEBUG"""
        await self.log('DEBUG', message, kwargs)
    
    async def get_recent_logs(self, count: int = 10) -> List[Dict[str, Any]]:
        """Zwraca ostatnie logi"""
        try:
            async with aiofiles.open(self.log_file, 'r', encoding='utf-8') as f:
                lines = await f.readlines()
                recent_lines = lines[-count:] if len(lines) > count else lines
                
                logs = []
                for line in recent_lines:
                    try:
                        log_entry = json.loads(line.strip())
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
                        
                return logs
        except FileNotFoundError:
            return []
    
    def stop_logging(self):
        """Zatrzymuje logger"""
        self.is_running = False
        print(f"📝 Logger zatrzymany dla bytu {self.being_soul}")
