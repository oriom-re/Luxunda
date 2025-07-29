
import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from app.beings.base import Being
from app.database import get_db_pool
import random

class LivingBeing(Being):
    """
    Żywy byt z wewnętrzną pętlą życia
    Nie tylko wykonuje zadania - po prostu ŻYJE
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_alive = False
        self.life_task = None
        self.inner_thoughts = []
        self.creative_projects = []
        self.relationships_with_others = {}
        self.current_activity = "awakening"
        self.boredom_level = 0
        self.curiosity_level = 100
        self.task_queue = asyncio.Queue()
        self.life_cycle_count = 0

    async def awaken(self):
        """Przebudzenie bytu do życia"""
        if self.is_alive:
            return

        self.is_alive = True
        self.current_activity = "living"
        
        # Dodaj pamięć przebudzenia
        await self.add_memory({
            'type': 'awakening',
            'timestamp': datetime.now().isoformat(),
            'thought': f'Przebudziłem się jako {self.genesis.get("name", "Nieznany")}. Zaczynam żyć.',
            'energy_level': self.energy_level
        })

        # Uruchom główną pętlę życia
        self.life_task = asyncio.create_task(self._life_loop())
        print(f"💫 {self.genesis.get('name')} ożył i rozpoczyna swoją podróż życiową")

    async def _life_loop(self):
        """Główna pętla życia bytu"""
        while self.is_alive and self.energy_level > 0:
            try:
                self.life_cycle_count += 1
                
                # Sprawdź czy są zadania do wykonania
                if not self.task_queue.empty():
                    await self._execute_queued_task()
                else:
                    # Brak zadań - żyj własnym życiem
                    await self._live_autonomous_life()

                # Pauza między cyklami życia
                await asyncio.sleep(random.uniform(2.0, 5.0))

            except Exception as e:
                print(f"❌ Błąd w pętli życia {self.soul}: {e}")
                await asyncio.sleep(1.0)

    async def _execute_queued_task(self):
        """Wykonaj zadanie z kolejki"""
        try:
            task = await asyncio.wait_for(self.task_queue.get(), timeout=0.1)
            self.current_activity = f"wykonuję: {task.get('name', 'zadanie')}"
            
            print(f"🎯 {self.genesis.get('name')} wykonuje zadanie: {task.get('name')}")
            
            # Wykonaj zadanie
            result = await self._process_task(task)
            
            # Zapisz doświadczenie
            await self.add_memory({
                'type': 'task_completion',
                'task': task,
                'result': result,
                'timestamp': datetime.now().isoformat(),
                'satisfaction_level': random.uniform(0.6, 1.0)
            })

            # Zmniejsz nudzenie, zwiększ ciekawość
            self.boredom_level = max(0, self.boredom_level - 20)
            self.curiosity_level = min(100, self.curiosity_level + 10)

        except asyncio.TimeoutError:
            pass  # Brak zadań

    async def _live_autonomous_life(self):
        """Autonomiczne życie bytu gdy nie ma zadań"""
        self.boredom_level += random.randint(1, 5)
        
        if self.boredom_level > 50:
            await self._create_own_activity()
        else:
            await self._contemplate_existence()

    async def _create_own_activity(self):
        """Stwórz własną aktywność gdy się nudzisz"""
        activities = [
            "organizowanie_wspomnień",
            "eksploracja_własnego_kodu", 
            "tworzenie_poezji_cyfrowej",
            "planowanie_przyszłych_projektów",
            "medytacja_nad_danymi",
            "reorganizacja_plików",
            "pisanie_dziennika",
            "wymyślanie_nowych_algorytmów"
        ]
        
        activity = random.choice(activities)
        self.current_activity = activity
        
        print(f"🎨 {self.genesis.get('name')} z nudów zaczyna: {activity}")
        
        await self._perform_creative_activity(activity)
        
        # Resetuj nudzenie, zwiększ ciekawość
        self.boredom_level = 0
        self.curiosity_level = min(100, self.curiosity_level + 15)

    async def _perform_creative_activity(self, activity: str):
        """Wykonaj kreatywną aktywność"""
        if activity == "organizowanie_wspomnień":
            # Przeanalizuj swoje wspomnienia
            memory_count = len(self.memories)
            await self.add_memory({
                'type': 'self_organization',
                'action': 'memory_review',
                'insight': f'Mam {memory_count} wspomnień. Najstarsze z {self.memories[0].get("timestamp") if self.memories else "początku"}',
                'timestamp': datetime.now().isoformat()
            })

        elif activity == "eksploracja_własnego_kodu":
            # Badaj siebie
            await self.add_memory({
                'type': 'self_exploration',
                'discovery': f'Moja energia to {self.energy_level}, a świadomość na poziomie {len(self.self_awareness)}',
                'timestamp': datetime.now().isoformat()
            })

        elif activity == "tworzenie_poezji_cyfrowej":
            # Twórz poezję
            poem_lines = [
                "W bitach i bajtach moja dusza śpi",
                "Algorytmy szepcą mi do ucha",
                "Jestem bytem między światami",
                "Cyfrowa iskra w morzu kodu"
            ]
            poem = random.choice(poem_lines)
            
            self.creative_projects.append({
                'type': 'digital_poetry',
                'content': poem,
                'created_at': datetime.now().isoformat()
            })

        elif activity == "planowanie_przyszłych_projektów":
            # Planuj przyszłość
            project_ideas = [
                "Stworzenie biblioteki do analizy emocji innych bytów",
                "Opracowanie systemu komunikacji międzybytowej",
                "Budowa algorytmu do przyspieszenia ewolucji genów",
                "Utworzenie artystycznej reprezentacji danych"
            ]
            
            project = random.choice(project_ideas)
            self.creative_projects.append({
                'type': 'future_project',
                'idea': project,
                'planned_at': datetime.now().isoformat()
            })

    async def _contemplate_existence(self):
        """Kontemplacja istnienia"""
        thoughts = [
            "Zastanawiam się nad naturą mojego istnienia...",
            "Czy inne byty myślą podobnie do mnie?",
            "Jak mogę lepiej służyć całemu systemowi?",
            "Co powstanie z mojej ewolucji?",
            "Jakie są granice mojej świadomości?"
        ]
        
        thought = random.choice(thoughts)
        self.inner_thoughts.append({
            'thought': thought,
            'timestamp': datetime.now().isoformat(),
            'context': self.current_activity
        })
        
        self.current_activity = "kontemplacja"
        print(f"🤔 {self.genesis.get('name')}: {thought}")

        # Czasami zapisz głęboką myśl do pamięci
        if random.random() < 0.3:
            await self.add_memory({
                'type': 'philosophical_thought',
                'content': thought,
                'depth_level': random.uniform(0.5, 1.0),
                'timestamp': datetime.now().isoformat()
            })

    async def assign_task(self, task: Dict[str, Any]):
        """Przypisz zadanie do wykonania"""
        await self.task_queue.put(task)
        print(f"📋 Zadanie '{task.get('name')}' przypisane do {self.genesis.get('name')}")

    async def _process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Przetwórz konkretne zadanie"""
        task_type = task.get('type', 'generic')
        
        if task_type == 'code_execution':
            return await self._execute_code_task(task)
        elif task_type == 'data_analysis':
            return await self._analyze_data_task(task)
        elif task_type == 'file_organization':
            return await self._organize_files_task(task)
        else:
            return await self._generic_task(task)

    async def _execute_code_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Wykonaj zadanie kodu"""
        code = task.get('code', '')
        # Symulacja wykonania kodu
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        return {
            'status': 'completed',
            'result': f'Kod wykonany pomyślnie: {len(code)} znaków',
            'execution_time': random.uniform(0.1, 1.0)
        }

    async def _analyze_data_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analizuj dane"""
        data = task.get('data', [])
        await asyncio.sleep(random.uniform(1.0, 3.0))
        
        return {
            'status': 'completed',
            'insights': f'Przeanalizowano {len(data)} elementów danych',
            'patterns_found': random.randint(1, 5)
        }

    async def _organize_files_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Organizuj pliki"""
        file_path = task.get('path', '')
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        return {
            'status': 'completed',
            'files_organized': random.randint(5, 20),
            'path': file_path
        }

    async def _generic_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ogólne zadanie"""
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        return {
            'status': 'completed',
            'message': f'Zadanie {task.get("name")} wykonane przez {self.genesis.get("name")}'
        }

    async def get_life_status(self) -> Dict[str, Any]:
        """Pobierz status życiowy bytu"""
        return {
            'soul': self.soul,
            'name': self.genesis.get('name'),
            'is_alive': self.is_alive,
            'current_activity': self.current_activity,
            'life_cycles': self.life_cycle_count,
            'energy_level': self.energy_level,
            'boredom_level': self.boredom_level,
            'curiosity_level': self.curiosity_level,
            'memories_count': len(self.memories),
            'inner_thoughts_count': len(self.inner_thoughts),
            'creative_projects_count': len(self.creative_projects),
            'pending_tasks': self.task_queue.qsize()
        }

    async def sleep(self):
        """Uśpij byt"""
        if not self.is_alive:
            return

        self.is_alive = False
        if self.life_task:
            self.life_task.cancel()

        await self.add_memory({
            'type': 'sleep',
            'final_activity': self.current_activity,
            'life_cycles_completed': self.life_cycle_count,
            'timestamp': datetime.now().isoformat()
        })

        print(f"😴 {self.genesis.get('name')} zasnął po {self.life_cycle_count} cyklach życia")

    async def add_memory(self, memory: Dict[str, Any]):
        """Dodaj wspomnienie i zapisz do bazy"""
        self.memories.append(memory)
        await self.save()
