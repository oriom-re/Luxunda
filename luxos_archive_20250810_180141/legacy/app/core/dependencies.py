# soul: app/core/dependencies.py

import importlib.util
import sys
import asyncio
import json
from typing import Dict, Any
from app.core.gen_loader_from_file import get_soul_by_name

_loaded_modules = {}

async def load_and_run_gen(module_name, call_init: bool = True):
    soul = await get_soul_by_name(module_name)
    if not soul:
        print(f"❌ Nie znaleziono duszy dla nazwy: {module_name}")
        return None
    print(f"🔍 Ładowanie modułu {module_name} {soul['genesis'].get('name')}")
    if module_name in _loaded_modules:
        return _loaded_modules[module_name]

    # 1. 🔌 Wczytaj zależności
    # await load_dependencies(soul, db_pool)

    # 2. 📦 Załaduj jako moduł dynamicznie z kodu
    try:
        # Tworzymy specyfikację modułu z kodu źródłowego
        spec = importlib.util.spec_from_loader(
            module_name, 
            loader=None, 
            origin="virtual"
        )
        if not spec:
            print(f"❌ Nie udało się utworzyć specyfikacji dla modułu: {module_name}")
            return None
        
        # Tworzymy moduł z specyfikacji
        module = importlib.util.module_from_spec(spec)
        
        # Dodajemy moduł do sys.modules przed wykonaniem kodu
        sys.modules[module_name] = module
        
        # Wykonujemy kod źródłowy w kontekście modułu
        exec(soul['genesis']['code'], module.__dict__)
        
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia modułu {module_name}: {e}")
        # Usuń moduł z sys.modules jeśli wystąpił błąd
        if module_name in sys.modules:
            del sys.modules[module_name]
        return None

    _loaded_modules[module_name] = module

    # 3. ⚙️ Inicjalizacja, jeśli funkcja lub klasa dostępna
    if call_init:
        if hasattr(module, "init"):
            await maybe_async(module.init)
            print(f"✅ Inicjalizacja modułu {module_name} zakończona.")
        elif hasattr(module, "__call__"):
            await maybe_async(module())
            print(f"✅ Wywołanie modułu {module_name} zakończone.")
    
    return module

async def maybe_async(func):
    """Wykonuje funkcję niezależnie od tego, czy jest async."""
    if asyncio.iscoroutinefunction(func):
        await func()
    else:
        func()

async def load_dependencies(soul: Dict[str, Any], db_pool):
    """Wczytuje zależności z bazy i ładuje je rekurencyjnie."""
    if not soul.get("genesis", {}).get("dependencies"):
        print(f"🔍 Brak zależności dla {soul['genesis'].get('name')}")
        return
    query = """
    SELECT target_uid, genesis FROM relationships
    JOIN souls ON relationships.target_uid = souls.uid
    WHERE source_uid = ? AND relationships.attributes LIKE '%depends_on%'
    """
    print(f"🔍 Wczytywanie zależności dla {soul['genesis'].get('name')}")
    async with db_pool.execute(query, (soul.get("uid"),)) as cursor:
        async for row in cursor:
            target_uid, target_genesis = row
            target_uid_dict = {
                "soul": target_uid,
                "genesis": json.loads(target_genesis),
                "attributes": {},
                "memories": [],
                "self_awareness": {}
            }
            await load_and_run_gen(target_uid_dict, db_pool, call_init=True)
