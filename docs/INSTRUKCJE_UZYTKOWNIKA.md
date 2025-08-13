
# 🧬 Instrukcje Użytkownika: Soul, Being i Intelligent Kernel

## Przegląd Systemu

LuxOS wykorzystuje trzy kluczowe komponenty:
- **Soul** - genotyp/szablon (niezmienne DNA)
- **Being** - instancja bytu (żywy obiekt)
- **Intelligent Kernel** - inteligentny zarządca systemu

## 1. 🧬 Soul (Genotyp) - Tworzenie Szablonów

### Podstawowe tworzenie Soul

```python
from luxdb.models.soul import Soul

# 1. Prosty genotyp
genotype = {
    "genesis": {
        "name": "calculator_soul",
        "type": "calculator",
        "version": "1.0.0",
        "description": "Kalkulator matematyczny"
    },
    "attributes": {
        "precision": {"py_type": "int", "default": 2},
        "mode": {"py_type": "str", "default": "standard"}
    }
}

# Tworzenie Soul
calculator_soul = await Soul.create(genotype, alias="calculator")
```

### Soul z funkcjami (module_source)

```python
# Genotyp z wbudowanymi funkcjami
advanced_genotype = {
    "genesis": {
        "name": "smart_calculator",
        "type": "advanced_calculator", 
        "version": "1.0.0"
    },
    "attributes": {
        "last_result": {"py_type": "float", "default": 0.0},
        "operation_count": {"py_type": "int", "default": 0}
    },
    "module_source": '''
def init(being_context=None):
    """Inicjalizacja kalkulatora"""
    print(f"Calculator {being_context.get('alias')} initialized")
    return {
        "ready": True,
        "suggested_persistence": True  # Zaleca zapisanie Being
    }

def execute(request=None, being_context=None):
    """Główna funkcja wykonawcza"""
    if not request:
        return {"status": "ready", "available_operations": ["add", "multiply"]}
    
    operation = request.get('operation')
    if operation == 'add':
        return add_numbers(request.get('a', 0), request.get('b', 0), being_context)
    elif operation == 'multiply':
        return multiply_numbers(request.get('a', 1), request.get('b', 1), being_context)
    
    return {"error": "Unknown operation"}

def add_numbers(a, b, being_context=None):
    """Dodawanie liczb"""
    result = a + b
    
    # Aktualizuj statystyki Being
    if being_context and being_context.get('data'):
        being_context['data']['last_result'] = result
        being_context['data']['operation_count'] = being_context['data'].get('operation_count', 0) + 1
    
    return {"result": result, "operation": "addition"}

def multiply_numbers(a, b, being_context=None):
    """Mnożenie liczb"""
    result = a * b
    
    if being_context and being_context.get('data'):
        being_context['data']['last_result'] = result
        being_context['data']['operation_count'] = being_context['data'].get('operation_count', 0) + 1
    
    return {"result": result, "operation": "multiplication"}
'''
}

# Tworzenie zaawansowanej Soul
smart_soul = await Soul.create(advanced_genotype, alias="smart_calculator")
```

### Operacje na Soul

```python
# Pobieranie Soul
soul = await Soul.get_by_alias("calculator")
soul = await Soul.get_by_hash("abc123...")

# Lista funkcji
functions = soul.list_functions()
print(f"Dostępne funkcje: {functions}")

# Informacje o funkcjach
visibility_info = soul.get_function_visibility_info()
print(visibility_info)

# Wszystkie Soul
all_souls = await Soul.get_all()
```

## 2. 🤖 Being (Instancja) - Żywe Obiekty

### Tworzenie Being

```python
from luxdb.models.being import Being

# 1. Podstawowe tworzenie z atrybutami
being = await Being.create(
    soul=calculator_soul,
    alias="my_calculator", 
    attributes={
        "precision": 3,
        "mode": "scientific"
    },
    persistent=True  # Zapisz do bazy danych
)

# 2. Tymczasowe Being (bez zapisu do bazy)
temp_being = await Being.create(
    soul=calculator_soul,
    persistent=False
)

# 3. Get or Create pattern
being = await Being.get_or_create(
    soul=calculator_soul,
    alias="shared_calculator",
    unique_by="alias"  # Jeden Being per alias
)
```

### Wykonywanie funkcji przez Being

```python
# 1. Konkretna funkcja
result = await being.execute_soul_function(
    "add_numbers", 
    a=10, 
    b=20
)
print(result['data']['result'])  # 30

# 2. Inteligentne wykonanie (Being wybiera funkcję)
result = await being.execute(data={"operation": "multiply", "a": 5, "b": 6})

# 3. Domyślna funkcja execute
result = await being.execute({"operation": "add", "a": 100, "b": 200})
```

### Zarządzanie Being

```python
# Sprawdź czy Being jest masterem funkcji
if being.is_function_master():
    print("Being zarządza swoimi funkcjami")
    
    # Informacje o masterowaniu
    mastery_info = being.get_function_mastery_info()
    print(f"Zarządza {mastery_info['function_count']} funkcjami")

# Ręczna inicjalizacja
init_result = await being.init()

# Ewolucja Being
evolution_result = await being.request_evolution(
    evolution_trigger="high_usage",
    new_capabilities={"advanced_math": True}
)

# Sprawdź możliwości ewolucji  
can_evolve = await being.can_evolve()
```

## 3. 🧠 Intelligent Kernel - Zarządca Systemu

### Inicjalizacja i podstawy

```python
from luxdb.core.intelligent_kernel import intelligent_kernel

# Kernel inicjalizuje się automatycznie przy starcie
kernel_being = await intelligent_kernel.initialize()

# Status systemu
status = await intelligent_kernel.get_system_status()
print(f"Aliases: {status['aliases_count']}")
print(f"Managed beings: {status['managed_beings_count']}")
```

### Registry aliasów (kluczowa funkcjonalność)

```python
# Rejestracja aliasu dla Soul
await intelligent_kernel.register_alias_mapping("calc_v1", soul.soul_hash)

# Pobieranie hash dla aliasu
result = await intelligent_kernel.get_current_hash_for_alias("calc_v1")
if result['found']:
    print(f"Hash: {result['soul_hash']}")

# Tworzenie Being przez alias (DELEGACJA!)
being = await intelligent_kernel.create_being_by_alias(
    "calc_v1", 
    {"precision": 5}, 
    persistent=True
)
```

### Automatyczna delegacja

```python
# To jest KLUCZOWE! 
# Jeśli wywołasz Being.create() tylko z aliasem, automatycznie deleguje do Kernel

# Automatyczna delegacja do Kernel
auto_being = await Being.create(
    alias="calc_v1",  # TYLKO alias, bez soul
    attributes={"mode": "expert"}
)
# Kernel automatycznie znajdzie Soul po aliasie i utworzy Being
```

## 4. 📝 Kompletny Przykład Użycia

```python
import asyncio
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.intelligent_kernel import intelligent_kernel

async def demo_complete_system():
    """Kompletny przykład użycia systemu"""
    
    # 1. Tworzenie Soul z funkcjami
    genotype = {
        "genesis": {
            "name": "task_manager",
            "type": "productivity_tool",
            "version": "1.0.0"
        },
        "attributes": {
            "tasks": {"py_type": "list", "default": []},
            "completed": {"py_type": "int", "default": 0}
        },
        "module_source": '''
def init(being_context=None):
    print(f"Task Manager {being_context.get('alias')} ready")
    return {"ready": True, "suggested_persistence": True}

def execute(request=None, being_context=None):
    action = request.get('action') if request else None
    
    if action == 'add_task':
        return add_task(request.get('task'), being_context)
    elif action == 'complete_task':
        return complete_task(request.get('task_id'), being_context)
    elif action == 'list_tasks':
        return list_tasks(being_context)
    
    return {"status": "ready", "available_actions": ["add_task", "complete_task", "list_tasks"]}

def add_task(task, being_context):
    tasks = being_context['data'].get('tasks', [])
    tasks.append({"id": len(tasks), "task": task, "done": False})
    being_context['data']['tasks'] = tasks
    return {"success": True, "task_added": task, "total_tasks": len(tasks)}

def complete_task(task_id, being_context):
    tasks = being_context['data'].get('tasks', [])
    if task_id < len(tasks):
        tasks[task_id]['done'] = True
        completed = being_context['data'].get('completed', 0) + 1
        being_context['data']['completed'] = completed
        return {"success": True, "task_completed": tasks[task_id]['task']}
    return {"success": False, "error": "Task not found"}

def list_tasks(being_context):
    tasks = being_context['data'].get('tasks', [])
    return {"tasks": tasks, "total": len(tasks), "completed": being_context['data'].get('completed', 0)}
'''
    }
    
    # 2. Utworzenie Soul
    task_soul = await Soul.create(genotype, alias="task_manager")
    
    # 3. Rejestracja w Kernel
    await intelligent_kernel.register_alias_mapping("tm_v1", task_soul.soul_hash)
    
    # 4. Tworzenie Being przez Kernel (automatyczna delegacja)
    task_being = await Being.create(
        alias="tm_v1",  # Kernel automatycznie znajdzie Soul
        attributes={"user_id": "user_123"}
    )
    
    # 5. Używanie Being
    # Dodawanie zadania
    result = await task_being.execute({
        "action": "add_task",
        "task": "Napisać dokumentację"
    })
    print(f"Dodano zadanie: {result['data']['task_added']}")
    
    # Dodanie kolejnego zadania
    await task_being.execute({
        "action": "add_task", 
        "task": "Przetestować system"
    })
    
    # Zakończenie zadania
    await task_being.execute({
        "action": "complete_task",
        "task_id": 0
    })
    
    # Lista zadań
    tasks_result = await task_being.execute({"action": "list_tasks"})
    print(f"Zadania: {tasks_result['data']['tasks']}")
    print(f"Zakończone: {tasks_result['data']['completed']}")
    
    # 6. Status Kernel
    kernel_status = await intelligent_kernel.get_system_status()
    print(f"Kernel zarządza {kernel_status['managed_beings_count']} beings")

# Uruchomienie
asyncio.run(demo_complete_system())
```

## 5. 🔥 Najważniejsze Wzorce

### Wzorzec 1: Soul → Being → Wykonanie
```python
# Tradycyjny sposób
soul = await Soul.create(genotype, alias="worker")
being = await Being.create(soul=soul, alias="my_worker")
result = await being.execute_soul_function("work", task="important")
```

### Wzorzec 2: Alias → Kernel → Being (ZALECANY!)
```python
# Nowoczesny sposób przez Kernel
await intelligent_kernel.register_alias_mapping("worker_v1", soul.soul_hash)
being = await Being.create(alias="worker_v1")  # Automatyczna delegacja!
result = await being.execute({"task": "important"})
```

### Wzorzec 3: Function Master Pattern
```python
# Being z init() staje się masterem swoich funkcji
smart_being = await Being.create(soul=smart_soul, alias="smart_one")
# Automatycznie wywołuje init() i staje się masterem

# Inteligentne wykonanie
result = await smart_being.execute(data={"complex": "request"})
# Being sam wybiera najlepszą funkcję
```

## 6. ⚡ Quick Start

```python
# 1. Minimum do rozpoczęcia
genotype = {
    "genesis": {"name": "hello", "type": "greeter", "version": "1.0"},
    "module_source": '''
def init(being_context=None):
    return {"ready": True}

def execute(request=None, being_context=None):
    name = request.get('name', 'World') if request else 'World'
    return {"greeting": f"Hello, {name}!"}
'''
}

# 2. Utwórz i użyj
soul = await Soul.create(genotype, alias="greeter")
being = await Being.create(soul=soul, alias="my_greeter")
result = await being.execute({"name": "LuxOS"})
print(result['data']['greeting'])  # "Hello, LuxOS!"
```

## 7. 🔧 Debugging i Monitoring

```python
# Status Soul
info = soul.get_function_visibility_info()
print(f"Funkcje publiczne: {info['functions']['public']['names']}")

# Status Being  
mastery = being.get_function_mastery_info()
print(f"Wykonań: {mastery['intelligent_executions']}")

# Status Kernel
system_status = await intelligent_kernel.get_system_status()
print(f"Aliasy: {system_status['registry_mappings']}")
```

Ten dokument zawiera wszystkie niezbędne informacje do pracy z systemem LuxOS przez Intelligent Kernel. Kluczem jest zrozumienie wzorca Soul → Being → Kernel i wykorzystanie automatycznej delegacji przez aliasy.
