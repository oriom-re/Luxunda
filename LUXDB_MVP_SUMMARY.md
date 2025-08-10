# LuxDB MVP - System Relacyjno-Genetyczny

## 🚀 Stan Projektu: **DZIAŁAJĄCY MVP**

### ✅ Co działa:
1. **Walidacja genotypów** - system sprawdza poprawność definicji typów
2. **Dynamiczne generowanie tabel PostgreSQL** - na podstawie genotypu
3. **Soul management** - tworzenie i zarządzanie genotypami
4. **Being management** - tworzenie instancji na podstawie genotypów
5. **Persistence** - zapis i odczyt z bazy PostgreSQL
6. **Type mapping** - automatyczne mapowanie typów Python na SQL

### 🔧 Architektura Systemu:

#### Główne komponenty:
- **`parser_table.py`** - Parser genotypów i generator SQL
- **`soul_repository.py`** - Repository pattern dla operacji na danych
- **`being.py`** - Klasy Soul i Being
- **`postgre_db.py`** - Zarządzanie połączeniem z PostgreSQL

#### Przepływ danych:
```
Genotype → Parser → SQL Tables → PostgreSQL
     ↓
Soul (szablon) → Being (instancja) → Tabele dynamiczne
```

### 📊 Obsługiwane typy danych:
- `str` → `VARCHAR/TEXT`
- `int` → `INTEGER`
- `float` → `FLOAT`
- `bool` → `BOOLEAN`
- `dict` → `JSONB`
- `List[str]` → `JSONB`
- `List[float]` → `VECTOR` (dla embeddings)

### 🗄️ Struktura bazy danych:

#### Tabele główne:
- **`souls`** - przechowuje genotypy (szablony)
- **`beings`** - przechowuje instancje bytów

#### Tabele dynamiczne:
- **`attr_text`** - atrybuty tekstowe
- **`attr_int`** - atrybuty liczbowe całkowite
- **`attr_float`** - atrybuty liczbowe rzeczywiste
- **`attr_boolean`** - atrybuty logiczne
- **`attr_jsonb`** - atrybuty złożone (obiekty, listy)
- **`attr_vector_1536`** - embeddings (1536 wymiarów)

### 💡 Kluczowe innowacje:

1. **Genetyczny system typów** - genotypy definiują strukturę danych
2. **Dynamiczne tabele** - automatyczne tworzenie tabel na podstawie genotypu
3. **Type safety** - walidacja typów na poziomie Pythona i SQL
4. **Vector support** - natywne wsparcie dla embeddings AI
5. **Repository pattern** - czysta separacja logiki biznesowej od bazy danych

### 🧪 Przykład użycia:

```python
# 1. Definicja genotypu
genotype = {
    "attributes": {
        "name": {"py_type": "str", "max_length": 100},
        "embedding": {"py_type": "List[float]", "vector_size": 1536},
        "active": {"py_type": "bool", "default": True}
    }
}

# 2. Utworzenie soul (szablonu)
soul = await Soul.create(genotype, alias="user_profile")

# 3. Utworzenie being (instancji)
data = {"name": "Jan", "embedding": [0.1]*1536, "active": True}
being = await Being.create(soul, data)

# 4. Automatyczne utworzenie tabel w PostgreSQL i zapis danych
```

### ⚡ Performance Features:
- Connection pooling
- Indeksy automatyczne
- JSONB dla złożonych struktur
- Vector operations dla AI

### 🔒 Security Features:
- Type validation
- SQL injection protection (parametrized queries)
- Schema validation

### 🚧 Następne kroki:
1. Dodanie relacji między beings
2. Implementacja zapytań semantycznych
3. Optymalizacja wydajności
4. Więcej typów danych
5. Migracje schematów

---

**LuxDB MVP jest gotowy do użycia w projektach wymagających dynamicznych struktur danych z type safety!** 🎉
