
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Callable
import traceback

class GenExecutor:
    """Uruchamia funkcje/geny z kolejki"""
    
    __gene_metadata__ = {
        'name': 'gen_executor',
        'description': 'Uruchamia funkcje/geny z kolejki',
        'version': '1.0.0',
        'compatible_types': ['agent', 'task', 'executor'],
        'tags': ['execution', 'queue', 'processing'],
        'energy_cost': 10,
        'dependencies': []
    }
    
    def __init__(self, being_soul: str):
        self.being_soul = being_soul
        self.task_queue = asyncio.Queue()
        self.is_running = False
        self.execution_history = []
        self.max_concurrent_tasks = 5
        self.current_tasks = set()
    
    async def start_executor(self):
        """Uruchamia executor zadań"""
        if self.is_running:
            return
            
        self.is_running = True
        asyncio.create_task(self._execution_worker())
        print(f"⚙️ Executor uruchomiony dla bytu {self.being_soul}")
    
    async def _execution_worker(self):
        """Pracownik wykonujący zadania z kolejki"""
        while self.is_running:
            try:
                if len(self.current_tasks) < self.max_concurrent_tasks:
                    task_data = await asyncio.wait_for(
                        self.task_queue.get(),
                        timeout=1.0
                    )
                    
                    # Utwórz zadanie wykonania
                    execution_task = asyncio.create_task(
                        self._execute_task(task_data)
                    )
                    self.current_tasks.add(execution_task)
                    
                    # Usuń zadanie z listy po zakończeniu
                    execution_task.add_done_callback(
                        lambda t: self.current_tasks.discard(t)
                    )
                else:
                    # Czekaj aż zwolni się miejsce
                    await asyncio.sleep(0.1)
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"⚙️ Błąd w executorze: {e}")
    
    async def _execute_task(self, task_data: Dict[str, Any]):
        """Wykonuje pojedyncze zadanie"""
        task_id = task_data.get('id', 'unknown')
        task_type = task_data.get('type', 'function')
        
        execution_record = {
            'task_id': task_id,
            'type': task_type,
            'started_at': datetime.now().isoformat(),
            'being_soul': self.being_soul,
            'status': 'running'
        }
        
        try:
            if task_type == 'function':
                result = await self._execute_function(task_data)
            elif task_type == 'gene_method':
                result = await self._execute_gene_method(task_data)
            elif task_type == 'code':
                result = await self._execute_code(task_data)
            else:
                raise ValueError(f"Nieznany typ zadania: {task_type}")
            
            execution_record.update({
                'status': 'completed',
                'result': result,
                'completed_at': datetime.now().isoformat(),
                'success': True
            })
            
            print(f"✅ Zadanie {task_id} wykonane pomyślnie")
            
        except Exception as e:
            execution_record.update({
                'status': 'failed',
                'error': str(e),
                'traceback': traceback.format_exc(),
                'completed_at': datetime.now().isoformat(),
                'success': False
            })
            
            print(f"❌ Zadanie {task_id} zakończone błędem: {e}")
        
        finally:
            self.execution_history.append(execution_record)
            # Zachowaj tylko ostatnie 100 rekordów
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
    
    async def _execute_function(self, task_data: Dict[str, Any]):
        """Wykonuje funkcję"""
        func = task_data.get('function')
        args = task_data.get('args', [])
        kwargs = task_data.get('kwargs', {})
        
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    async def _execute_gene_method(self, task_data: Dict[str, Any]):
        """Wykonuje metodę genu"""
        gene_instance = task_data.get('gene_instance')
        method_name = task_data.get('method_name')
        args = task_data.get('args', [])
        kwargs = task_data.get('kwargs', {})
        
        method = getattr(gene_instance, method_name)
        
        if asyncio.iscoroutinefunction(method):
            return await method(*args, **kwargs)
        else:
            return method(*args, **kwargs)
    
    async def _execute_code(self, task_data: Dict[str, Any]):
        """Wykonuje kod w kontrolowanym środowisku"""
        code = task_data.get('code')
        context = task_data.get('context', {})
        
        # Bezpieczne wykonanie kodu
        safe_globals = {
            '__builtins__': {
                'print': print,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'dict': dict,
                'list': list,
                'tuple': tuple,
                'datetime': datetime,
                'json': json
            }
        }
        
        safe_globals.update(context)
        
        exec(code, safe_globals)
        return safe_globals.get('result', 'Kod wykonany')
    
    async def queue_task(self, task_data: Dict[str, Any]) -> str:
        """Dodaje zadanie do kolejki"""
        task_id = task_data.get('id', f"task_{datetime.now().timestamp()}")
        task_data['id'] = task_id
        
        if not self.is_running:
            await self.start_executor()
        
        await self.task_queue.put(task_data)
        print(f"📋 Zadanie {task_id} dodane do kolejki")
        return task_id
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Zwraca status kolejki zadań"""
        return {
            'queue_size': self.task_queue.qsize(),
            'running_tasks': len(self.current_tasks),
            'max_concurrent': self.max_concurrent_tasks,
            'total_executed': len(self.execution_history),
            'is_running': self.is_running,
            'gene_source': 'gen_executor'
        }
    
    def stop_executor(self):
        """Zatrzymuje executor"""
        self.is_running = False
        # Anuluj wszystkie bieżące zadania
        for task in self.current_tasks:
            task.cancel()
        print(f"⚙️ Executor zatrzymany dla bytu {self.being_soul}")
