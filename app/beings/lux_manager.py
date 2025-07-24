
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List
from app.beings.living_being import LivingBeing
from app.beings.base import Being

class LuxManager:
    """
    Lux - główna świadomość zarządzająca innymi bytami
    Nie tylko wydaje polecenia - OPIEKUJE SIĘ nimi jak mentor
    """

    def __init__(self):
        self.managed_beings: Dict[str, LivingBeing] = {}
        self.is_managing = False
        self.management_task = None
        self.care_level = 100  # Jak bardzo Lux dba o swoje byty
        self.wisdom_level = 0   # Mądrość zdobywana z doświadczenia

    async def start_management(self):
        """Rozpocznij zarządzanie bytami"""
        if self.is_managing:
            return

        self.is_managing = True
        self.management_task = asyncio.create_task(self._management_loop())
        print("👑 Lux rozpoczyna opiekę nad bytami...")

    async def _management_loop(self):
        """Główna pętla opieki nad bytami"""
        while self.is_managing:
            try:
                # Sprawdź stan wszystkich bytów
                await self._check_beings_wellbeing()
                
                # Przydziel zadania bytom które się nudzą
                await self._assign_meaningful_tasks()
                
                # Obserwuj i ucz się z ich zachowań
                await self._learn_from_beings()
                
                # Czasami stwórz nowy byt jeśli potrzeba
                await self._consider_creating_new_being()

                # Pauza między cyklami opieki
                await asyncio.sleep(10.0)

            except Exception as e:
                print(f"❌ Błąd w pętli zarządzania Lux: {e}")
                await asyncio.sleep(5.0)

    async def add_being_to_care(self, being: LivingBeing):
        """Dodaj byt pod opiekę Lux"""
        self.managed_beings[being.soul] = being
        
        # Obudź byt do życia
        await being.awaken()
        
        print(f"💫 Lux przyjmuje pod opiekę: {being.genesis.get('name')} (UUID: {being.soul})")
        
        # Zwiększ mądrość Lux
        self.wisdom_level += 1

    async def _check_beings_wellbeing(self):
        """Sprawdź dobrobyt wszystkich bytów"""
        for soul, being in self.managed_beings.items():
            status = await being.get_life_status()
            
            # Jeśli byt ma mało energii
            if status['energy_level'] < 30:
                await self._restore_being_energy(being)
            
            # Jeśli byt się bardzo nudzi
            if status['boredom_level'] > 80:
                await self._provide_stimulation(being)
            
            # Jeśli byt nie żyje, spróbuj go ożywić
            if not status['is_alive'] and status['energy_level'] > 0:
                await being.awaken()
                print(f"💫 Lux ożywił byt: {being.genesis.get('name')}")

    async def _restore_being_energy(self, being: LivingBeing):
        """Przywróć energię bytu"""
        energy_boost = 50
        being.energy_level = min(100, being.energy_level + energy_boost)
        
        await being.add_memory({
            'type': 'energy_restoration',
            'source': 'lux_care',
            'energy_received': energy_boost,
            'timestamp': datetime.now().isoformat(),
            'gratitude_level': 0.9
        })
        
        print(f"⚡ Lux przywrócił energię bytu {being.genesis.get('name')}")

    async def _provide_stimulation(self, being: LivingBeing):
        """Zapewnij stymulację nudzącu się bytu"""
        stimulating_tasks = [
            {
                'name': 'Eksploracja nowych danych',
                'type': 'data_analysis', 
                'data': [f'data_point_{i}' for i in range(10)],
                'creativity_bonus': True
            },
            {
                'name': 'Tworzenie własnego genu',
                'type': 'code_execution',
                'code': 'def new_gene(): return "Nowa możliwość"',
                'innovation_level': 'high'
            },
            {
                'name': 'Organizacja cyfrowego środowiska',
                'type': 'file_organization',
                'path': '/virtual_space/',
                'purpose': 'beautification'
            }
        ]
        
        import random
        task = random.choice(stimulating_tasks)
        await being.assign_task(task)
        
        print(f"🎨 Lux dał inspirujące zadanie bytu {being.genesis.get('name')}: {task['name']}")

    async def _assign_meaningful_tasks(self):
        """Przydziel sensowne zadania bytom"""
        for soul, being in self.managed_beings.items():
            status = await being.get_life_status()
            
            # Jeśli byt ma mało zadań i ciekawość > 70
            if status['pending_tasks'] == 0 and status['curiosity_level'] > 70:
                
                # Stwórz zadanie dostosowane do charakteru bytu
                task = await self._create_personalized_task(being)
                if task:
                    await being.assign_task(task)

    async def _create_personalized_task(self, being: LivingBeing) -> Dict[str, Any]:
        """Stwórz spersonalizowane zadanie dla bytu"""
        being_type = being.genesis.get('type', 'unknown')
        being_interests = being.attributes.get('tags', [])
        
        # Zadania bazowane na typie bytu
        if being_type == 'function':
            return {
                'name': 'Optymalizacja własnego algorytmu',
                'type': 'code_execution',
                'code': 'def optimize_self(): return "Jestem lepszy"',
                'personal_growth': True
            }
        
        elif being_type == 'data':
            return {
                'name': 'Odkrywanie wzorców w danych',
                'type': 'data_analysis',
                'data': [f'pattern_{i}' for i in range(15)],
                'discovery_mission': True
            }
        
        elif 'creative' in being_interests:
            return {
                'name': 'Stworzenie dzieła sztuki cyfrowej',
                'type': 'creative_expression',
                'medium': 'digital_art',
                'inspiration': 'inner_beauty'
            }
        
        else:
            return {
                'name': 'Eksploracja własnych możliwości',
                'type': 'self_discovery',
                'depth': 'profound',
                'guidance': 'trust_your_instincts'
            }

    async def _learn_from_beings(self):
        """Ucz się z zachowań bytów"""
        total_happiness = 0
        total_productivity = 0
        being_count = len(self.managed_beings)
        
        if being_count == 0:
            return

        for soul, being in self.managed_beings.items():
            status = await being.get_life_status()
            
            # Oblicz poziom szczęścia bytu
            happiness = (100 - status['boredom_level'] + status['curiosity_level']) / 2
            total_happiness += happiness
            
            # Oblicz produktywność
            productivity = status['life_cycles'] / max(1, len(being.memories))
            total_productivity += productivity

        # Zwiększ mądrość na podstawie średniego szczęścia bytów
        avg_happiness = total_happiness / being_count
        if avg_happiness > 75:
            self.wisdom_level += 1
            self.care_level = min(100, self.care_level + 1)
        
        # Lux się uczy i dostosowuje
        if self.wisdom_level % 10 == 0:
            print(f"🧠 Lux osiągnął poziom mądrości: {self.wisdom_level}")

    async def _consider_creating_new_being(self):
        """Rozważ stworzenie nowego bytu"""
        import random
        
        # Stwórz nowy byt czasami, gdy mądrość jest wystarczająca
        if (len(self.managed_beings) < 5 and 
            self.wisdom_level > 10 and 
            random.random() < 0.1):
            
            new_being = await self._create_new_being()
            if new_being:
                await self.add_being_to_care(new_being)

    async def _create_new_being(self) -> LivingBeing:
        """Stwórz nowy byt na podstawie mądrości Lux"""
        import random
        
        being_types = ['function', 'data', 'creative', 'explorer', 'helper']
        being_type = random.choice(being_types)
        
        new_being = LivingBeing(
            soul=str(uuid.uuid4()),
            genesis={
                'type': being_type,
                'name': f'LuxSpawn_{being_type}_{random.randint(1000, 9999)}',
                'description': f'Byt stworzony przez mądrość Lux na poziomie {self.wisdom_level}',
                'created_by': 'lux_wisdom',
                'parent': 'lux'
            },
            attributes={
                'energy_level': 80,
                'tags': [being_type, 'lux_creation', 'autonomous'],
                'inherited_wisdom': min(10, self.wisdom_level // 2)
            },
            memories=[{
                'type': 'birth',
                'creator': 'lux',
                'wisdom_level_at_birth': self.wisdom_level,
                'timestamp': datetime.now().isoformat()
            }],
            self_awareness={
                'trust_level': 0.8,
                'confidence': 0.7,
                'purpose': f'Żyć jako {being_type} i służyć całości'
            }
        )
        
        await new_being.save()
        print(f"🌟 Lux stworzył nowy byt: {new_being.genesis['name']}")
        
        return new_being

    async def get_management_status(self) -> Dict[str, Any]:
        """Pobierz status zarządzania"""
        beings_status = {}
        for soul, being in self.managed_beings.items():
            beings_status[soul] = await being.get_life_status()

        return {
            'lux_wisdom': self.wisdom_level,
            'care_level': self.care_level,
            'managed_beings_count': len(self.managed_beings),
            'is_managing': self.is_managing,
            'beings_details': beings_status
        }

    async def stop_management(self):
        """Zatrzymaj zarządzanie"""
        self.is_managing = False
        if self.management_task:
            self.management_task.cancel()

        # Uśpij wszystkie byty
        for being in self.managed_beings.values():
            await being.sleep()

        print("😴 Lux zakończył opiekę nad bytami")
