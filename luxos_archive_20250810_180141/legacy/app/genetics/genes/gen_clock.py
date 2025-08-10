
import asyncio
from datetime import datetime
from typing import Dict, Any

class GenClock:
    """Wewnętrzny zegar do wywołań cyklicznych"""
    
    __gene_metadata__ = {
        'name': 'gen_clock',
        'description': 'Wewnętrzny zegar do wywołań cyklicznych',
        'version': '1.0.0',
        'compatible_types': ['agent', 'task', 'scenario'],
        'tags': ['time', 'scheduler', 'automation'],
        'energy_cost': 5,
        'dependencies': []
    }
    
    def __init__(self, being_soul: str):
        self.being_soul = being_soul
        self.is_running = False
        self.intervals = {}
        self.tasks = {}
    
    async def start_interval(self, name: str, callback, interval_seconds: float):
        """Uruchamia cykliczne wywołanie funkcji"""
        if name in self.tasks:
            await self.stop_interval(name)
        
        async def interval_task():
            while name in self.intervals and self.intervals[name]:
                try:
                    await callback()
                    await asyncio.sleep(interval_seconds)
                except Exception as e:
                    print(f"⏰ Błąd w intervallu {name}: {e}")
                    break
        
        self.intervals[name] = True
        self.tasks[name] = asyncio.create_task(interval_task())
        print(f"⏰ Uruchomiono interval '{name}' co {interval_seconds}s dla bytu {self.being_soul}")
    
    async def stop_interval(self, name: str):
        """Zatrzymuje cykliczne wywołanie"""
        if name in self.intervals:
            self.intervals[name] = False
        
        if name in self.tasks:
            self.tasks[name].cancel()
            del self.tasks[name]
            print(f"⏹️ Zatrzymano interval '{name}' dla bytu {self.being_soul}")
    
    async def get_current_time(self) -> Dict[str, Any]:
        """Zwraca aktualny czas"""
        now = datetime.now()
        return {
            'timestamp': now.isoformat(),
            'unix_timestamp': now.timestamp(),
            'formatted': now.strftime('%Y-%m-%d %H:%M:%S'),
            'gene_source': 'gen_clock'
        }
    
    async def schedule_once(self, callback, delay_seconds: float):
        """Planuje jednorazowe wykonanie funkcji po opóźnieniu"""
        async def delayed_task():
            await asyncio.sleep(delay_seconds)
            try:
                await callback()
            except Exception as e:
                print(f"⏰ Błąd w zaplanowanym zadaniu: {e}")
        
        task = asyncio.create_task(delayed_task())
        print(f"⏰ Zaplanowano zadanie za {delay_seconds}s dla bytu {self.being_soul}")
        return task
    
    def stop_all(self):
        """Zatrzymuje wszystkie intervale"""
        for name in list(self.intervals.keys()):
            asyncio.create_task(self.stop_interval(name))
