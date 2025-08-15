# 📁 LuxOS Repository Structure

## 🎯 **Główna Struktura (Post-Cleanup)**

```
LuxOS/
├── luxdb/                    # 🧬 Główny moduł LuxOS
│   ├── core/                # ⚙️ Rdzeń systemu
│   │   ├── luxdb.py        # 🗄️ Główna klasa LuxDB
│   │   ├── simple_kernel.py # 🔧 Prosty kernel
│   │   ├── intelligent_kernel.py # 🧠 Inteligentny kernel
│   │   ├── postgre_db.py   # 🐘 PostgreSQL connection
│   │   └── ...
│   ├── models/             # 📊 Modele danych
│   │   ├── soul.py        # 🧬 Soul (genotyp)
│   │   └── being.py       # 🤖 Being (instancja)
│   ├── utils/             # 🛠️ Narzędzia
│   │   ├── serializer.py  # 📦 Serializacja
│   │   ├── validators.py  # ✅ Walidacja
│   │   └── language_bridge.py # 🌐 Multi-language
│   └── ...
├── static/                # 🌐 Interfejs webowy
├── tests/                 # 🧪 Testy systemowe
├── genotypes/            # 🧬 Definicje genotypów
├── legacy/               # 📚 Stare wersje (archiwum)
└── main.py              # 🚀 Główny punkt wejścia
```

## 🔄 **Migracja Importów**

Wszystkie importy używają teraz struktury `/luxdb/`:

```python
# ✅ Nowe (spójne)
from luxdb.core.luxdb import LuxDB
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.utils.serializer import GeneticResponseFormat

# ❌ Stare (usunięte)
from ai.openai_integration import ...
from core.globals import ...
from database.postgre_db import ...
```

## 🎯 **Zasady Spójności**

1. **Jeden punkt prawdy**: Wszystko w `/luxdb/`
2. **Legacy preservation**: Stare wersje w `/legacy/`
3. **Clear separation**: Tests, static, configs oddzielnie
4. **Standard imports**: Zawsze przez `/luxdb/`

---
Wygenerowano przez: cleanup_repository.py
