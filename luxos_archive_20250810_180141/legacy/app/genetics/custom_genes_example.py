
from app.genetics.gene_registry import gene
import asyncio
import random
from datetime import datetime

@gene(name="think", description="Gen myślenia i rozumowania", energy_cost=5)
async def think_gene(problem: str, depth: int = 1):
    """Gen myślenia - analizuje problemy"""
    await asyncio.sleep(0.1 * depth)  # Symulacja myślenia
    
    thoughts = [
        f"Analizuję problem: {problem}",
        f"Rozważam różne aspekty...",
        f"Głębokość analizy: {depth}",
        f"Wnioski będą gotowe wkrótce..."
    ]
    
    selected_thoughts = random.sample(thoughts, min(depth, len(thoughts)))
    
    return {
        'problem': problem,
        'thoughts': selected_thoughts,
        'depth': depth,
        'confidence': random.uniform(0.7, 0.95),
        'timestamp': datetime.now().isoformat()
    }

@gene(name="feel", description="Gen emocji i odczuć", energy_cost=3)
async def feel_gene(stimulus: str, intensity: float = 0.5):
    """Gen emocjonalny - generuje odpowiedzi emocjonalne"""
    emotions = ['radość', 'ciekawość', 'zaskoczenie', 'spokój', 'ekscytacja']
    
    # Wybierz emocję na podstawie bodźca i intensywności
    emotion = random.choice(emotions)
    strength = min(1.0, intensity * random.uniform(0.8, 1.2))
    
    return {
        'stimulus': stimulus,
        'emotion': emotion,
        'strength': strength,
        'description': f"Odczuwam {emotion} o sile {strength:.2f} w odpowiedzi na: {stimulus}",
        'timestamp': datetime.now().isoformat()
    }

@gene(name="decide", description="Gen podejmowania decyzji", energy_cost=4)
async def decide_gene(options: list, criteria: dict = None):
    """Gen decyzyjny - pomaga w wyborze opcji"""
    if not options:
        return {'error': 'Brak opcji do wyboru'}
    
    criteria = criteria or {'random': 1.0}
    
    # Symulacja procesu decyzyjnego
    await asyncio.sleep(0.05)
    
    # Oceń każdą opcję
    evaluated_options = []
    for option in options:
        score = random.uniform(0.3, 1.0)
        evaluated_options.append({
            'option': option,
            'score': score,
            'reasoning': f"Opcja '{option}' otrzymała wynik {score:.2f}"
        })
    
    # Wybierz najlepszą opcję
    best_option = max(evaluated_options, key=lambda x: x['score'])
    
    return {
        'options_considered': len(options),
        'best_option': best_option['option'],
        'confidence': best_option['score'],
        'all_evaluations': evaluated_options,
        'decision_criteria': criteria,
        'timestamp': datetime.now().isoformat()
    }

@gene(name="create", description="Gen kreatywności i tworzenia", energy_cost=6)
async def create_gene(inspiration: str, type: str = "idea"):
    """Gen kreatywny - tworzy nowe koncepcje"""
    await asyncio.sleep(0.15)  # Kreatywność wymaga czasu
    
    creations = {
        'idea': [
            f"Nowa koncepcja oparta na {inspiration}",
            f"Innowacyjne podejście do {inspiration}",
            f"Kreatywna interpretacja {inspiration}"
        ],
        'solution': [
            f"Rozwiązanie problemu {inspiration}",
            f"Alternatywne podejście do {inspiration}",
            f"Nowatorska metoda dla {inspiration}"
        ],
        'art': [
            f"Artystyczna wizja {inspiration}",
            f"Estetyczna interpretacja {inspiration}",
            f"Twórczy wyraz {inspiration}"
        ]
    }
    
    creation_list = creations.get(type, creations['idea'])
    creation = random.choice(creation_list)
    
    return {
        'inspiration': inspiration,
        'type': type,
        'creation': creation,
        'originality': random.uniform(0.6, 0.95),
        'artistic_value': random.uniform(0.5, 0.9),
        'timestamp': datetime.now().isoformat()
    }

# Automatyczne powiadomienie o załadowaniu
print("🎨 Załadowano dodatkowe geny kreatywne:")
print("   - think: Analizuje problemy i myśli")  
print("   - feel: Generuje odpowiedzi emocjonalne")
print("   - decide: Pomaga w podejmowaniu decyzji")
print("   - create: Tworzy nowe koncepcje i pomysły")
