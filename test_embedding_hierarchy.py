
import asyncio
from app.genetics.embedding_gene import EmbeddingGene
from app.beings.being_factory import BeingFactory
from app.genetics.base_gene import GeneActivationContext
from datetime import datetime

async def test_embedding_hierarchy():
    print("🧬 Test systemu hierarchicznych embeddingów")
    
    # Utwórz byt z dużym kodem
    function_being = await BeingFactory.create_being(
        being_type='function',
        genesis={
            'type': 'function',
            'name': 'ComplexCalculator',
            'source': '''
class ComplexCalculator:
    """Kalkulator do złożonych obliczeń matematycznych"""
    
    def __init__(self):
        self.history = []
        self.precision = 10
    
    def calculate_fibonacci(self, n):
        """Oblicz n-ty element ciągu Fibonacciego"""
        if n <= 1:
            return n
        
        a, b = 0, 1
        for i in range(2, n + 1):
            a, b = b, a + b
        
        self.history.append(f"fibonacci({n}) = {b}")
        return b
    
    def calculate_prime_factors(self, num):
        """Znajdź wszystkie czynniki pierwsze liczby"""
        factors = []
        d = 2
        
        while d * d <= num:
            while num % d == 0:
                factors.append(d)
                num //= d
            d += 1
        
        if num > 1:
            factors.append(num)
        
        self.history.append(f"prime_factors = {factors}")
        return factors
    
    def get_statistics(self):
        """Zwróć statystyki obliczeń"""
        return {
            'total_calculations': len(self.history),
            'history': self.history[-5:],  # ostatnie 5
            'precision': self.precision
        }
            ''',
            'created_by': 'test'
        },
        attributes={'energy_level': 100}
    )
    
    print(f"✅ Utworzono byt funkcji: {function_being.soul}")
    
    # Utwórz i aktywuj EmbeddingGene
    embedding_gene = EmbeddingGene()
    context = GeneActivationContext(
        activator_soul=function_being.soul,
        activation_time=datetime.now(),
        activation_params={'models': ['ada2', 'multilingual']}
    )
    
    print("🧠 Aktywacja EmbeddingGene...")
    await embedding_gene.activate(function_being, context)
    
    # Test 1: Utwórz główny embedding
    print("📊 Tworzę główny embedding bytu...")
    result = await embedding_gene.express({'action': 'create_embedding'})
    print(f"Embedding utworzony: {len(function_being.attributes.get('embeddings', {}))}")
    
    # Test 2: Dekompozycja hierarchiczna
    print("\n🔍 Rozpoczynam dekompozycję hierarchiczną (głębokość 3)...")
    decomposition = await embedding_gene.express({
        'action': 'decompose',
        'depth': 3
    })
    
    print(f"📈 Wyniki dekompozycji:")
    print(f"  - Rodzic: {decomposition['parent_soul']}")
    print(f"  - Całkowita liczba utworzonych fragmentów: {decomposition['total_created']}")
    print(f"  - Liczba dzieci na poziomie 1: {len(decomposition['children'])}")
    
    # Pokaż szczegóły fragmentów
    for i, child in enumerate(decomposition['children'][:3]):  # Pierwsze 3
        print(f"\n  Fragment {i+1}:")
        print(f"    - Soul: {child['soul'][:8]}...")
        print(f"    - Typ: {child['type']}")
        print(f"    - Podobieństwo do rodzica: {child['embedding_similarity']:.3f}")
        print(f"    - Preview: {child['content_preview']}")
        print(f"    - Podfragmentów: {len(child['children'])}")
    
    # Test 3: Sprawdź hierarchię w bazie
    print("\n🗄️ Sprawdzam utworzone byty w bazie...")
    from app.beings.base import BaseBeing, Relationship
    
    all_beings = await BaseBeing.get_all(50)
    fragments = [b for b in all_beings if b.genesis.get('type') == 'fragment']
    
    print(f"Znaleziono {len(fragments)} fragmentów w bazie")
    
    # Sprawdź relacje
    all_relations = await Relationship.get_all(50)
    decomposition_relations = [r for r in all_relations if r.genesis.get('type') == 'decomposition']
    
    print(f"Znaleziono {len(decomposition_relations)} relacji dekompozycji")
    
    # Test 4: Test autonomii genu
    print("\n🚀 Test autonomii genu...")
    for i in range(10):
        await embedding_gene.evolve_autonomy({
            'autonomy_boost': 5,
            'experience_type': 'successful_decomposition'
        })
    
    print(f"Poziom autonomii: {embedding_gene.autonomy_level}/100")
    
    if await embedding_gene.can_become_independent():
        print("🎯 Gen może stać się niezależną istotą!")
        independent_being = await embedding_gene.spawn_independent_being()
        if independent_being:
            print(f"✨ Utworzono niezależny byt: {independent_being.soul}")
        else:
            print("❌ Nie udało się utworzyć niezależnego bytu")
    else:
        print("⏳ Gen jeszcze nie jest wystarczająco autonomiczny")
    
    print("\n🎉 Test zakończony pomyślnie!")
    return True

if __name__ == "__main__":
    asyncio.run(test_embedding_hierarchy())
