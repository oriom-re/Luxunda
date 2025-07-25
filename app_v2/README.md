# app_v2/README.md

# LuxOS app_v2 - Clean Architecture

Struktura systemu z czystą architekturą i komunikacją między bytami.

## Struktura katalogów

```
app_v2/
├── beings/           # Byty w systemie
│   ├── base.py       # Podstawowa klasa Being + Relationship
│   └── genotype.py   # Klasa Genotype z systemem komunikacji
├── core/             # Podstawowe funkcjonalności
│   ├── communication.py      # System komunikacji i rozpoznawanie intencji
│   └── module_registry.py    # Rejestracja modułów z plików
├── services/         # Logika biznesowa
│   ├── entity_manager.py     # Zarządzanie bytami (create_or_load)
│   ├── dependency_service.py # Zarządzanie zależnościami
│   └── genotype_service.py   # Serwis genotypów
├── database/         # Warstwa dostępu do danych
│   └── soul_repository.py    # Repository pattern dla souls
├── gen_files/        # Pliki modułów .module
│   └── test_logger.module    # Przykładowy moduł
└── main_test.py      # Testy systemu
```

## Kluczowe koncepty

### 1. Separacja odpowiedzialności
- **beings/**: Logika biznesowa bytów
- **core/**: Podstawowe mechanizmy systemu
- **services/**: Wysokopoziomowa logika biznesowa
- **database/**: Dostęp do danych (Repository pattern)

### 2. System komunikacji
Wszystkie operacje przez jeden punkt wejścia: `entity.execute(content)`

```python
# Tworzenie bytu
result = await lux.execute({
    "command": "create",
    "alias": "logger", 
    "template": "test_logger"
})

# Komunikacja między bytami
result = await lux.execute("send to logger hello world")

# Wykonywanie funkcji
result = await lux.execute("execute log test message")
```

### 3. Rozpoznawanie intencji
System automatycznie rozpoznaje intencje na podstawie treści:
- `create_entity`: create, spawn, new, make
- `load_entity`: load, get, find, retrieve
- `execute_function`: execute, run, call, invoke
- `communicate`: send, tell, message, notify
- `query_data`: query, search, list, show

### 4. Zarządzanie bytami
- `create_or_load(alias, template, force_new=False)` - inteligentne tworzenie/ładowanie
- Cache aktywnych bytów
- Automatyczne zapisywanie do bazy danych

### 5. Pamięć i logowanie
- `remember(key, value)` - zapisywanie w pamięci bytu
- `recall(key)` - odczytywanie z pamięci
- `log(message, level)` - logowanie z kontekstem bytu

## Uruchomienie testów

```bash
cd /home/runner/workspace
python app_v2/main_test.py
```

## Przyszłe rozszerzenia

1. **Prawdziwa baza danych** - zamiana mock repository na PostgreSQL/SQLite
2. **Bezpieczeństwo** - system uprawnień dla bytów
3. **Wersjonowanie** - zarządzanie wersjami genotypów
4. **AI Integration** - rozpoznawanie intencji przez AI
5. **Web UI** - interfejs webowy do zarządzania bytami
