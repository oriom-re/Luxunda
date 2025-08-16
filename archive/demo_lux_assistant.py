
#!/usr/bin/env python3
"""
🌟 Demo Lux AI Assistant - Tylko nowoczesne JSONB systemy
"""

import asyncio
import sys
from datetime import datetime
from database.postgre_db import Postgre_db
from luxdb.models.being import Being
from luxdb.core.primitive_beings import (
    PrimitiveBeingFactory, 
    DataBeing, 
    FunctionBeing, 
    MessageBeing,
    TaskBeing
)

class LuxAIAssistant:
    """
    Nowoczesny AI Assistant używający tylko JSONB
    """
    
    def __init__(self):
        self.assistant_being = None
        self.memory_being = None
        self.task_queue = []
        
    async def initialize(self):
        """Inicjalizuje AI Assistant"""
        print("🤖 Inicjalizuję Lux AI Assistant...")
        
        # Stwórz główny byt assistanta
        self.assistant_being = await PrimitiveBeingFactory.create_being(
            'data',
            alias='lux_ai_assistant',
            name='Lux AI Assistant',
            role='personal_assistant',
            capabilities=[
                'note_taking',
                'task_management', 
                'data_analysis',
                'code_generation'
            ],
            personality='helpful, intelligent, creative'
        )
        
        # Stwórz system pamięci
        self.memory_being = await PrimitiveBeingFactory.create_being(
            'data',
            alias='lux_memory_system',
            name='Memory System',
            conversations=[],
            user_preferences={},
            learned_patterns=[]
        )
        
        print(f"✅ Assistant Being: {self.assistant_being.ulid}")
        print(f"✅ Memory Being: {self.memory_being.ulid}")
        
    async def process_user_input(self, user_input: str) -> str:
        """Przetwarza wejście użytkownika"""
        print(f"\n👤 You: {user_input}")
        
        # Zapisz do pamięci konwersacji
        conversations = await self.memory_being.get_value('conversations', [])
        conversations.append({
            'timestamp': datetime.now().isoformat(),
            'user': user_input,
            'type': 'user_input'
        })
        await self.memory_being.store_value('conversations', conversations)
        
        # Analiza intencji
        intent = await self._analyze_intent(user_input)
        
        # Wybierz akcję na podstawie intencji
        response = await self._execute_intent(intent, user_input)
        
        # Zapisz odpowiedź do pamięci
        conversations.append({
            'timestamp': datetime.now().isoformat(),
            'assistant': response,
            'type': 'assistant_response',
            'intent': intent
        })
        await self.memory_being.store_value('conversations', conversations)
        
        return response
        
    async def _analyze_intent(self, user_input: str) -> str:
        """Analizuje intencję użytkownika (uproszczona wersja)"""
        input_lower = user_input.lower()
        
        if any(word in input_lower for word in ['notatka', 'zapisz', 'zapamiętaj', 'note']):
            return 'note_taking'
        elif any(word in input_lower for word in ['zadanie', 'task', 'zrób', 'wykonaj']):
            return 'task_creation'
        elif any(word in input_lower for word in ['kalkulator', 'calculator', 'oblicz']):
            return 'calculator_creation'
        elif any(word in input_lower for word in ['analiza', 'analysis', 'przeanalizuj']):
            return 'data_analysis'
        elif any(word in input_lower for word in ['pomoc', 'help', 'jak']):
            return 'help'
        else:
            return 'general_conversation'
            
    async def _execute_intent(self, intent: str, user_input: str) -> str:
        """Wykonuje akcję na podstawie intencji"""
        
        if intent == 'note_taking':
            return await self._create_note(user_input)
        elif intent == 'task_creation':
            return await self._create_task(user_input)
        elif intent == 'calculator_creation':
            return await self._create_calculator()
        elif intent == 'data_analysis':
            return await self._analyze_data(user_input)
        elif intent == 'help':
            return await self._provide_help()
        else:
            return await self._general_response(user_input)
            
    async def _create_note(self, user_input: str) -> str:
        """Tworzy notatkę"""
        note_being = await PrimitiveBeingFactory.create_being(
            'message',
            alias=f'note_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            note_type='user_note',
            content=user_input,
            created_by='lux_ai_assistant',
            tags=['note', 'user_created']
        )
        
        return f"📝 Utworzyłem notatkę: {note_being.ulid}\nTreść: {user_input}"
        
    async def _create_task(self, user_input: str) -> str:
        """Tworzy zadanie"""
        task_being = await PrimitiveBeingFactory.create_being(
            'task',
            alias=f'task_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            task_name=user_input,
            task_description=f"Zadanie utworzone z: {user_input}",
            priority='medium',
            created_by='lux_ai_assistant'
        )
        
        await task_being.create_task(user_input, f"Zadanie utworzone przez AI Assistant")
        
        return f"✅ Utworzyłem zadanie: {task_being.ulid}\nNazwa: {user_input}"
        
    async def _create_calculator(self) -> str:
        """Tworzy prosty kalkulator"""
        calc_being = await PrimitiveBeingFactory.create_being(
            'function',
            alias=f'calculator_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            name='Simple Calculator',
            description='Prosty kalkulator matematyczny'
        )
        
        calculator_code = """
def calculate(operation, a, b):
    if operation == 'add':
        return a + b
    elif operation == 'subtract':
        return a - b
    elif operation == 'multiply':
        return a * b
    elif operation == 'divide':
        return a / b if b != 0 else 'Error: Division by zero'
    else:
        return 'Error: Unknown operation'
"""
        
        await calc_being.set_function('calculate', calculator_code)
        
        return f"🧮 Utworzyłem kalkulator: {calc_being.ulid}\nMożesz teraz wykonywać operacje matematyczne!"
        
    async def _analyze_data(self, user_input: str) -> str:
        """Analizuje dane (symulacja)"""
        analysis_being = await PrimitiveBeingFactory.create_being(
            'data',
            alias=f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            analysis_type='text_analysis',
            input_text=user_input,
            word_count=len(user_input.split()),
            char_count=len(user_input),
            analysis_timestamp=datetime.now().isoformat()
        )
        
        word_count = len(user_input.split())
        char_count = len(user_input)
        
        return f"📊 Analiza tekstu:\n- Liczba słów: {word_count}\n- Liczba znaków: {char_count}\n- ID analizy: {analysis_being.ulid}"
        
    async def _provide_help(self) -> str:
        """Zapewnia pomoc"""
        return """
🌟 Lux AI Assistant - Jak mogę pomóc:

✅ Dostępne komendy:
- "Zapisz notatkę: [treść]" - Utworzę notatkę
- "Stwórz zadanie: [opis]" - Utworzę zadanie do wykonania  
- "Zbuduj kalkulator" - Utworzę prosty kalkulator
- "Przeanalizuj: [tekst]" - Przeanalizuję tekst
- "Pomoc" - Wyświetlę tę pomoc

🧬 Przykłady:
- "Potrzebuję zapisać notatkę z dzisiejszego dnia"
- "Chcę zbudować kalkulator"
- "Szukam narzędzia do analizy tekstu"
- "Stwórz mi system do zarządzania zadaniami"
        """
        
    async def _general_response(self, user_input: str) -> str:
        """Ogólna odpowiedź"""
        return f"🤔 Rozumiem, że mówisz o: '{user_input}'\n\nMogę pomóc Ci w:\n- Tworzeniu notatek\n- Zarządzaniu zadaniami\n- Budowaniu narzędzi\n- Analizie danych\n\nCo chciałbyś zrobić?"

async def main():
    """Główna funkcja demo"""
    print("🚀 Starting LuxOS AI Assistant...")
    
    # Inicjalizacja bazy danych
    print("🔄 Inicjalizacja puli połączeń do bazy PostgreSQL...")
    if not await Postgre_db.initialize_pool():
        print("❌ Nie udało się połączyć z bazą danych")
        return
    
    print("✅ PostgreSQL połączenie zainicjalizowane")
    
    # Inicjalizacja assistanta
    assistant = LuxAIAssistant()
    await assistant.initialize()
    
    print("🌟 Lux AI Assistant initialized!")
    print("\n🌟 Lux is ready! Try these examples:")
    print("- 'Potrzebuję zapisać notatkę z dzisiejszego dnia'")
    print("- 'Chcę zbudować kalkulator'")
    print("- 'Szukam narzędzia do analizy tekstu'")
    print("- 'Stwórz mi system do zarządzania zadaniami'")
    
    # Główna pętla interakcji
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye', 'wyjście']:
                print("👋 Do widzenia!")
                break
                
            if not user_input:
                continue
                
            response = await assistant.process_user_input(user_input)
            print(f"\n🤖 Lux: {response}")
            
        except KeyboardInterrupt:
            print("\n👋 Do widzenia!")
            break
        except Exception as e:
            print(f"❌ Błąd: {e}")

if __name__ == "__main__":
    asyncio.run(main())
