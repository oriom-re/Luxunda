
"""
Genotyp z genami do operacji matematycznych
"""

from app.genetics.gene_registry import gene
from datetime import datetime
import math

@gene(name="calculate", description="Uniwersalny kalkulator genetyczny")
def calculate(expression: str):
    """Gen uniwersalnego kalkulatora"""
    try:
        # Bezpieczne obliczenia - tylko podstawowe operacje
        allowed_names = {
            k: v for k, v in math.__dict__.items() if not k.startswith("__")
        }
        allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})
        
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        
        return {
            'expression': expression,
            'result': result,
            'success': True,
            'gene': 'calculate',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'expression': expression,
            'error': str(e),
            'success': False,
            'gene': 'calculate',
            'timestamp': datetime.now().isoformat()
        }

@gene(name="fibonacci", description="Generuje liczby Fibonacciego")
def fibonacci(n: int):
    """Gen generujący ciąg Fibonacciego"""
    if n <= 0:
        return {'numbers': [], 'count': 0, 'gene': 'fibonacci'}
    
    fib_sequence = []
    a, b = 0, 1
    
    for i in range(n):
        fib_sequence.append(a)
        a, b = b, a + b
    
    return {
        'numbers': fib_sequence,
        'count': n,
        'last_number': fib_sequence[-1] if fib_sequence else 0,
        'gene': 'fibonacci',
        'timestamp': datetime.now().isoformat()
    }

@gene(name="prime_check", description="Sprawdza czy liczba jest pierwsza")
def prime_check(number: int):
    """Gen sprawdzający liczby pierwsze"""
    if number < 2:
        return {
            'number': number,
            'is_prime': False,
            'reason': 'Number less than 2',
            'gene': 'prime_check'
        }
    
    for i in range(2, int(math.sqrt(number)) + 1):
        if number % i == 0:
            return {
                'number': number,
                'is_prime': False,
                'divisor': i,
                'gene': 'prime_check'
            }
    
    return {
        'number': number,
        'is_prime': True,
        'gene': 'prime_check'
    }

@gene(name="statistics", description="Oblicza podstawowe statystyki dla listy liczb")
def statistics(numbers: list):
    """Gen statystyk matematycznych"""
    if not numbers:
        return {'error': 'Empty list provided', 'gene': 'statistics'}
    
    numbers = [float(x) for x in numbers]  # Konwertuj na float
    
    mean = sum(numbers) / len(numbers)
    sorted_nums = sorted(numbers)
    n = len(numbers)
    
    # Mediana
    if n % 2 == 0:
        median = (sorted_nums[n//2 - 1] + sorted_nums[n//2]) / 2
    else:
        median = sorted_nums[n//2]
    
    # Odchylenie standardowe
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    std_dev = math.sqrt(variance)
    
    return {
        'count': len(numbers),
        'sum': sum(numbers),
        'mean': mean,
        'median': median,
        'min': min(numbers),
        'max': max(numbers),
        'variance': variance,
        'std_deviation': std_dev,
        'gene': 'statistics',
        'timestamp': datetime.now().isoformat()
    }

# Inicjalizacja genotypu
async def init():
    """Inicjalizacja genotypu matematycznego"""
    print("🧬 Inicjalizacja genotypu: Math Operations")
    print("🔢 Dostępne geny: calculate, fibonacci, prime_check, statistics")
    return {
        'genotype': 'math_operations_genotype',
        'genes_count': 4,
        'initialized': True,
        'capabilities': ['calculation', 'sequences', 'prime_numbers', 'statistics']
    }

__genotype_info__ = {
    'name': 'Math Operations Genotype',
    'version': '1.0.0',
    'description': 'Genotyp z podstawowymi operacjami matematycznymi',
    'author': 'LuxOS Genetic System',
    'genes': ['calculate', 'fibonacci', 'prime_check', 'statistics'],
    'category': 'mathematics'
}
