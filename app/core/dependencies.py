# soul: app/core/dependencies.py

import importlib.util
import sys
import asyncio
import json
from typing import Dict, Any

_loaded_modules = {}

async def load_and_run_gen(soul: Dict[str, Any], db_pool, call_init: bool = True):
    path = soul["genesis"]["path"]
    soul_id = soul["soul"]
    module_name = soul_id.replace("/", ".").rstrip(".py")

    if soul_id in _loaded_modules:
        return _loaded_modules[soul_id]

    # 1. 🔌 Wczytaj zależności
    await load_dependencies(soul, db_pool)

    # 2. 📦 Załaduj jako moduł dynamicznie
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module

    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"❌ Błąd ładowania {soul_id}: {e}")
        return None

    _loaded_modules[soul_id] = module

    # 3. ⚙️ Inicjalizacja, jeśli funkcja lub klasa dostępna
    if call_init:
        if hasattr(module, "init"):
            await maybe_async(module.init)
        elif hasattr(module, "__call__"):
            await maybe_async(module())
    
    return module

async def maybe_async(func):
    """Wykonuje funkcję niezależnie od tego, czy jest async."""
    if asyncio.iscoroutinefunction(func):
        await func()
    else:
        func()

async def load_dependencies(soul: Dict[str, Any], db_pool):
    """Wczytuje zależności z bazy i ładuje je rekurencyjnie."""
    query = """
    SELECT target_soul, genesis FROM relationships
    JOIN souls ON relationships.target_soul = souls.soul
    WHERE source_soul = ? AND relationships.attributes LIKE '%depends_on%'
    """
    async with db_pool.execute(query, (soul["soul"],)) as cursor:
        async for row in cursor:
            target_soul, target_genesis = row
            target_soul_dict = {
                "soul": target_soul,
                "genesis": json.loads(target_genesis),
                "attributes": {},
                "memories": [],
                "self_awareness": {}
            }
            await load_and_run_gen(target_soul_dict, db_pool, call_init=True)
