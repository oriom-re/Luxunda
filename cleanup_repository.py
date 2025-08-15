
#!/usr/bin/env python3
"""
🧹 LuxOS Repository Cleanup Script
Usuwa zduplikowane i przestarzałe pliki, zachowując spójność struktury
"""

import os
import shutil
from pathlib import Path

# Katalogi do przeniesienia do legacy (jeśli nie są już tam)
LEGACY_DIRS = [
    'ai',      # Stara wersja AI - nowa w luxdb/
    'core',    # Stary core - nowy w luxdb/core/
    'database', # Stara baza - nowa w luxdb/core/
    'genes',   # Stare genes - nowe w luxdb/utils/
    'clients', # Stari klienci - nowi w luxdb/
]

# Pliki do usunięcia (duplikaty/przestarzałe)
FILES_TO_CLEAN = [
    'demo_system.db',
    'luxos.db',
    'test_soul_hash_duplication.py',  # Stary test
]

def move_to_legacy(dir_name):
    """Move directory to legacy if exists and not already there"""
    if os.path.exists(dir_name) and not os.path.exists(f"legacy/{dir_name}"):
        print(f"📦 Moving {dir_name} to legacy/")
        shutil.move(dir_name, f"legacy/{dir_name}")
        return True
    return False

def cleanup_files():
    """Remove duplicate/outdated files"""
    removed_count = 0
    for file_path in FILES_TO_CLEAN:
        if os.path.exists(file_path):
            print(f"🗑️ Removing {file_path}")
            os.remove(file_path)
            removed_count += 1
    return removed_count

def create_structure_doc():
    """Create documentation of new repository structure"""
    structure_doc = """# 📁 LuxOS Repository Structure

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
"""
    
    with open("REPOSITORY_STRUCTURE.md", "w", encoding="utf-8") as f:
        f.write(structure_doc)
    print("📋 Created REPOSITORY_STRUCTURE.md")

def main():
    """Main cleanup function"""
    print("🧹 Starting LuxOS Repository Cleanup...")
    
    # Move old directories to legacy
    moved_count = 0
    for dir_name in LEGACY_DIRS:
        if move_to_legacy(dir_name):
            moved_count += 1
    
    # Remove duplicate files
    removed_count = cleanup_files()
    
    # Create structure documentation
    create_structure_doc()
    
    print(f"\n✨ Cleanup completed!")
    print(f"📦 Moved {moved_count} directories to legacy")
    print(f"🗑️ Removed {removed_count} duplicate files")
    print(f"📋 Created structure documentation")
    print(f"\n🎯 Repository is now consistent and clean!")

if __name__ == "__main__":
    main()
