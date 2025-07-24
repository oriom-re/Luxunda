
from app.genetics.gene_registry import gene
import asyncio
from typing import Any
from datetime import datetime
import json
import logging

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@gene(name="debug", description="Wyświetla komunikat debugowy", energy_cost=1)
async def debug_gene(message: str, level: str = "INFO", **context):
    """Gen debugowania - dostępny wszędzie"""
    timestamp = datetime.now().isoformat()
    debug_info = {
        'timestamp': timestamp,
        'level': level.upper(),
        'message': message,
        'context': context,
        'gene': 'debug'
    }
    
    print(f"🐛 [{level.upper()}] {timestamp}: {message}")
    if context:
        print(f"   Kontekst: {json.dumps(context, indent=2, ensure_ascii=False)}")
    
    return debug_info

@gene(name="log", description="Loguje wiadomość", energy_cost=1)
async def log_gene(message: str, level: str = "INFO"):
    """Gen logowania"""
    logger.log(getattr(logging, level.upper(), logging.INFO), message)
    return {
        'logged': True,
        'message': message,
        'level': level,
        'timestamp': datetime.now().isoformat()
    }

@gene(name="timer", description="Zarządza timerem", energy_cost=2)
async def timer_gene(action: str, timer_id: str = "default"):
    """Gen timera"""
    if not hasattr(timer_gene, 'timers'):
        timer_gene.timers = {}
    
    if action == "start":
        timer_gene.timers[timer_id] = datetime.now()
        return {'started': True, 'timer_id': timer_id}
    elif action == "stop":
        if timer_id in timer_gene.timers:
            start_time = timer_gene.timers[timer_id]
            duration = (datetime.now() - start_time).total_seconds()
            del timer_gene.timers[timer_id]
            return {'stopped': True, 'timer_id': timer_id, 'duration': duration}
        else:
            return {'error': f'Timer {timer_id} nie został uruchomiony'}
    else:
        return {'error': f'Nieznana akcja: {action}'}

print("🧬 Auto-geny załadowane pomyślnie!")

@gene(name="log", description="Zapisuje log do systemu", energy_cost=2)
async def log_gene(message: str, level: str = "INFO", save_to_file: bool = False):
    """Gen logowania - zapisuje logi"""
    timestamp = datetime.now().isoformat()
    
    # Logowanie do konsoli
    getattr(logger, level.lower(), logger.info)(f"{message}")
    
    log_entry = {
        'timestamp': timestamp,
        'level': level.upper(),
        'message': message,
        'gene': 'log'
    }
    
    if save_to_file:
        try:
            with open('gene_logs.json', 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"⚠️ Błąd zapisu do pliku: {e}")
    
    return log_entry

@gene(name="timer", description="Mierzy czas wykonania", energy_cost=1)
async def timer_gene(action: str = "start"):
    """Gen czasomierza"""
    current_time = datetime.now()
    
    if not hasattr(timer_gene, '_timers'):
        timer_gene._timers = {}
    
    if action == "start":
        timer_id = f"timer_{len(timer_gene._timers)}"
        timer_gene._timers[timer_id] = current_time
        return {
            'action': 'started',
            'timer_id': timer_id,
            'start_time': current_time.isoformat()
        }
    
    elif action == "stop":
        if not timer_gene._timers:
            return {'error': 'Brak aktywnych timerów'}
        
        # Zatrzymaj ostatni timer
        timer_id = max(timer_gene._timers.keys())
        start_time = timer_gene._timers.pop(timer_id)
        duration = (current_time - start_time).total_seconds()
        
        return {
            'action': 'stopped',
            'timer_id': timer_id,
            'duration_seconds': duration,
            'start_time': start_time.isoformat(),
            'end_time': current_time.isoformat()
        }
    
    return {'error': f'Nieznana akcja: {action}'}

@gene(name="memory", description="Zarządza pamięcią kontekstu", energy_cost=3)
async def memory_gene(action: str, key: str = None, value: Any = None):
    """Gen pamięci - przechowuje dane w kontekście"""
    if not hasattr(memory_gene, '_memory'):
        memory_gene._memory = {}
    
    if action == "set" and key:
        memory_gene._memory[key] = {
            'value': value,
            'timestamp': datetime.now().isoformat(),
            'access_count': 0
        }
        return {'action': 'set', 'key': key, 'success': True}
    
    elif action == "get" and key:
        if key in memory_gene._memory:
            memory_gene._memory[key]['access_count'] += 1
            return {
                'action': 'get',
                'key': key,
                'value': memory_gene._memory[key]['value'],
                'metadata': {
                    'timestamp': memory_gene._memory[key]['timestamp'],
                    'access_count': memory_gene._memory[key]['access_count']
                }
            }
        return {'action': 'get', 'key': key, 'error': 'Klucz nie istnieje'}
    
    elif action == "list":
        return {
            'action': 'list',
            'keys': list(memory_gene._memory.keys()),
            'total_entries': len(memory_gene._memory)
        }
    
    elif action == "clear":
        cleared_count = len(memory_gene._memory)
        memory_gene._memory.clear()
        return {'action': 'clear', 'cleared_entries': cleared_count}
    
    return {'error': f'Nieprawidłowa akcja: {action}'}

@gene(name="stats", description="Statystyki użycia genów", energy_cost=1)
async def stats_gene():
    """Gen statystyk systemu genowego"""
    from app.genetics.gene_registry import gene_registry
    
    genes_info = {}
    for gene_name in gene_registry.get_available_genes():
        info = gene_registry.get_gene_info(gene_name)
        genes_info[gene_name] = {
            'call_count': info['call_count'],
            'is_async': info['is_async'],
            'registered_at': info['registered_at']
        }
    
    return {
        'total_genes': len(genes_info),
        'genes': genes_info,
        'context': gene_registry._active_context,
        'timestamp': datetime.now().isoformat()
    }

# Automatyczne załadowanie genów przy imporcie
print("🧬 Geny automatycznie załadowane:")
print("   - debug: Wyświetla komunikaty debugowe")
print("   - log: Zapisuje logi do systemu") 
print("   - timer: Mierzy czas wykonania")
print("   - memory: Zarządza pamięcią kontekstu")
print("   - stats: Statystyki użycia genów")
