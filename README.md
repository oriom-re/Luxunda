
# LuxDB - Genetic Database Library

## 🧬 "Nie relacja. Nie dokument. Ewolucja danych."

LuxDB to rewolucyjna biblioteka bazy danych oparta na koncepcji genotypów i bytów (beings). Zamiast tradycyjnych tabel i dokumentów, LuxDB używa żywych struktur danych, które mogą ewoluować i adaptować się.

## 🚀 Instalacja

### Z GitHub (Replit)
```bash
git clone https://github.com/yourusername/luxdb.git
cd luxdb
pip install -e .
```

### Wymagania
- Python 3.11+
- PostgreSQL (lub Neon.tech)
- asyncpg
- ulid-py

## 📖 Szybki Start

### 1. Konfiguracja połączenia z bazą

```python
import asyncio
from luxdb import LuxDB, Soul, Being

# Inicjalizacja LuxDB
async def main():
    # Konfiguracja PostgreSQL
    db = LuxDB(
        host='your-host',
        port=5432,
        user='your-user',
        password='your-password',
        database='your-database'
    )
    
    await db.initialize()
```

### 2. Definiowanie genotypu (struktury danych)

```python
# Definicja genotypu użytkownika
user_genotype = {
    "genesis": {
        "name": "user_profile",
        "version": "1.0",
        "description": "Profil użytkownika z embeddings"
    },
    "attributes": {
        "name": {"py_type": "str", "max_length": 100},
        "email": {"py_type": "str", "unique": True},
        "age": {"py_type": "int", "min_value": 0},
        "preferences": {"py_type": "dict"},
        "embedding": {"py_type": "List[float]", "vector_size": 1536},
        "active": {"py_type": "bool", "default": True}
    }
}

# Utworzenie Soul (szablonu)
user_soul = await Soul.create(user_genotype, alias="user_profile")
```

### 3. Tworzenie bytów (instancji danych)

```python
# Dane użytkownika
user_data = {
    "name": "Jan Kowalski",
    "email": "jan@example.com",
    "age": 30,
    "preferences": {"theme": "dark", "language": "pl"},
    "embedding": [0.1, 0.2, 0.3] * 512,  # 1536 wymiarów
    "active": True
}

# Utworzenie Being (instancji)
user_being = await Being.create(user_soul, user_data)
print(f"Utworzono użytkownika: {user_being.ulid}")
```

### 4. Wczytywanie danych

```python
# Wczytanie po ULID
user = await Being.load_by_ulid("01HZ123456789ABCDEF...")

# Wczytanie wszystkich bytów dla danego genotypu
all_users = await Being.load_all_by_soul_hash(user_soul.soul_hash)

# Wczytanie po aliasie Soul
user_soul = await Soul.load_by_alias("user_profile")
```

## 🏗️ Zaawansowane funkcje

### Dynamiczne tabele
LuxDB automatycznie tworzy tabele PostgreSQL na podstawie genotypu:
- `attr_text` - atrybuty tekstowe
- `attr_int` - liczby całkowite  
- `attr_float` - liczby rzeczywiste
- `attr_boolean` - wartości logiczne
- `attr_jsonb` - struktury złożone
- `attr_vector_1536` - embeddings AI

### Relacje między bytami

```python
from luxdb.models import Relationship

# Tradycyjna relacja (MVP)
relationship = await Relationship.create(
    source_ulid=user1.ulid,
    target_ulid=user2.ulid,
    relation_type="friendship",
    strength=0.8,
    metadata={"since": "2025-01-01"}
)

# Przyszłość: Relacje jako żywe byty
relation_genotype = {
    "genesis": {"name": "friendship_relation"},
    "attributes": {
        "source_uid": {"py_type": "str"},
        "target_uid": {"py_type": "str"},
        "strength": {"py_type": "float"},
        "shared_interests": {"py_type": "List[str]"}
    }
}
```

### Embeddings i AI

```python
# Genotyp z embeddings
ai_genotype = {
    "attributes": {
        "content": {"py_type": "str"},
        "embedding": {"py_type": "List[float]", "vector_size": 1536},
        "similarity_threshold": {"py_type": "float", "default": 0.8}
    }
}

# Automatyczne wyszukiwanie semantyczne (w przyszłości)
similar_content = await Being.find_similar_by_embedding(
    embedding=query_embedding,
    threshold=0.7,
    soul_hash=content_soul.soul_hash
)
```

## 📊 Przykłady użycia

### E-commerce z LuxDB

```python
# Genotyp produktu
product_genotype = {
    "genesis": {"name": "product", "version": "1.0"},
    "attributes": {
        "name": {"py_type": "str"},
        "price": {"py_type": "float"},
        "category": {"py_type": "str"},
        "tags": {"py_type": "List[str]"},
        "description_embedding": {"py_type": "List[float]", "vector_size": 1536}
    }
}

# Genotyp zamówienia
order_genotype = {
    "genesis": {"name": "order", "version": "1.0"},
    "attributes": {
        "customer_id": {"py_type": "str"},
        "total_amount": {"py_type": "float"},
        "items": {"py_type": "List[dict]"},
        "status": {"py_type": "str", "default": "pending"}
    }
}
```

### System zarządzania treścią

```python
# Genotyp artykułu
article_genotype = {
    "genesis": {"name": "article", "version": "1.0"},
    "attributes": {
        "title": {"py_type": "str"},
        "content": {"py_type": "str"},
        "author_id": {"py_type": "str"},
        "tags": {"py_type": "List[str]"},
        "publish_date": {"py_type": "str"},
        "content_embedding": {"py_type": "List[float]", "vector_size": 1536}
    }
}
```

## 🔧 API Reference

### Soul (Genotyp)
- `Soul.create(genotype, alias)` - tworzy nowy genotyp
- `Soul.load_by_alias(alias)` - ładuje genotyp po aliasie
- `Soul.load_all()` - ładuje wszystkie genotypy

### Being (Byt/Instancja)
- `Being.create(soul, data)` - tworzy nową instancję
- `Being.load_by_ulid(ulid)` - ładuje po ULID
- `Being.load_all_by_soul_hash(hash)` - ładuje wszystkie instancje genotypu

### Relationship (Relacje)
- `Relationship.create(source, target, type, strength, metadata)` - tworzy relację
- `Relationship.get_by_being(being_ulid)` - pobiera relacje bytu
- `Relationship.get_all()` - pobiera wszystkie relacje

## 🌟 Kluczowe cechy

### ✅ Gotowe funkcje (MVP)
- [x] Genotypowy model danych
- [x] Dynamiczne tabele PostgreSQL
- [x] Type safety z walidacją
- [x] ULID jako identyfikatory
- [x] Repository pattern
- [x] Podstawowe relacje
- [x] Vector embeddings (1536D)

### 🚧 W rozwoju
- [ ] Zaawansowane zapytania semantyczne
- [ ] Automatyczna ewolucja genotypów
- [ ] Plugin system
- [ ] Advanced query language
- [ ] Distributed beings

## 🔒 Bezpieczeństwo
- Parametrized queries (ochrona przed SQL injection)
- Type validation na poziomie Pythona i SQL
- Schema validation
- Connection pooling

## 📈 Wydajność
- Connection pooling z asyncpg
- Automatyczne indeksy
- JSONB dla złożonych struktur
- Vector operations zoptymalizowane dla AI

## 🤝 Wsparcie i rozwój

LuxDB to biblioteka open-source. Więcej informacji:
- [Dokumentacja](./documentation.md)
- [Przykłady](./examples/)
- [Issues](https://github.com/yourusername/luxdb/issues)

## 📄 Licencja

MIT License - szczegóły w pliku LICENSE

---

*LuxDB - gdzie dane żyją, uczą się i ewoluują! 🧬*
