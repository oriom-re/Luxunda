
#!/usr/bin/env python3
"""
Demo systemu modułów - pokazuje jak tworzyć Soul z plików .module i ręcznie
"""

import asyncio
import sys
from pathlib import Path

# Dodaj ścieżkę do projektu
sys.path.append(str(Path(__file__).parent))

from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.utils.module_validator import ModuleValidator


async def demo_module_validation():
    """Demo walidacji modułów"""
    print("🔍 === DEMO WALIDACJI MODUŁÓW ===")
    
    # Waliduj przykładowy plik .module
    print("\n1. Walidacja pliku advanced_test.module")
    result = ModuleValidator.validate_file("gen_files/advanced_test.module")
    
    print(f"Plik: {result['file_path']}")
    print(f"Poprawny: {'✅' if result['valid'] else '❌'}")
    
    if result["errors"]:
        print("❌ Błędy:")
        for error in result["errors"]:
            print(f"  - {error}")
            
    if result["warnings"]:
        print("⚠️ Ostrzeżenia:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
            
    if result["info"]:
        info = result["info"]
        print(f"\n📊 Analiza:")
        print(f"  Funkcje: {len(info.get('functions', {}))}")
        print(f"  Atrybuty: {len(info.get('attributes', {}))}")
        print(f"  Ma init: {'✅' if info.get('has_init') else '❌'}")
        print(f"  Ma execute: {'✅' if info.get('has_execute') else '❌'}")
        
        if info.get('functions'):
            print("  📋 Funkcje:")
            for func_name, func_info in info['functions'].items():
                async_marker = " (async)" if func_info.get('is_async') else ""
                print(f"    - {func_name}{async_marker}")
                
        if info.get('attributes'):
            print("  🏷️ Atrybuty:")
            for attr_name, attr_info in info['attributes'].items():
                print(f"    - {attr_name}: {attr_info.get('value')}")


async def demo_create_soul_from_module_file():
    """Demo tworzenia Soul z pliku .module"""
    print("\n🧬 === DEMO TWORZENIA SOUL Z PLIKU .MODULE ===")
    
    try:
        # Utwórz Soul z pliku .module
        soul = await Soul.create_from_module_file(
            "gen_files/advanced_test.module",
            alias="advanced_test_soul"
        )
        
        print(f"✅ Utworzono Soul: {soul.alias}")
        print(f"Hash: {soul.soul_hash[:16]}...")
        print(f"Funkcje: {len(soul.list_functions())}")
        
        # Pokaż informacje o Soul
        genotype = soul.genotype
        print(f"\n📋 Informacje o genotypie:")
        print(f"  Typ: {genotype.get('genesis', {}).get('type')}")
        print(f"  Wersja: {genotype.get('genesis', {}).get('version')}")
        print(f"  Ma init: {genotype.get('genesis', {}).get('has_init')}")
        print(f"  Ma execute: {genotype.get('genesis', {}).get('has_execute')}")
        
        print(f"\n🔧 Dostępne funkcje:")
        for func_name in soul.list_functions():
            func_info = soul.get_function_info(func_name)
            if func_info:
                async_marker = " (async)" if func_info.get('is_async') else ""
                print(f"  - {func_name}{async_marker}")
        
        return soul
        
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia Soul: {e}")
        return None


async def demo_create_soul_manually():
    """Demo ręcznego tworzenia Soul z module_source"""
    print("\n🛠️ === DEMO RĘCZNEGO TWORZENIA SOUL Z MODULE_SOURCE ===")
    
    # Prosty moduł z funkcjami
    manual_module_source = '''
"""
Prosty moduł testowy utworzony ręcznie
"""

CONFIG_VALUE = "manual_test"
MAX_RETRIES = 3

def init(being_context=None):
    """Inicjalizacja modułu"""
    print(f"Manual module initialized for: {being_context.get('alias', 'unknown') if being_context else 'unknown'}")
    return {"status": "manual_init_complete", "config": CONFIG_VALUE}

def execute(data=None, **kwargs):
    """Domyślne wykonanie"""
    if not data:
        return get_status()
    return process_data(data)

def process_data(data):
    """Przetwarzanie danych"""
    return {
        "processed": True,
        "input": str(data),
        "config": CONFIG_VALUE,
        "retries": MAX_RETRIES
    }

def get_status():
    """Status modułu"""
    return {
        "status": "active",
        "config": CONFIG_VALUE,
        "max_retries": MAX_RETRIES
    }

async def async_process(data, delay=0.1):
    """Asynchroniczne przetwarzanie"""
    import asyncio
    await asyncio.sleep(delay)
    return {"async_result": data, "delay": delay}
'''
    
    try:
        # Utwórz Soul ręcznie
        soul = await Soul.create_with_manual_module(
            module_source=manual_module_source,
            alias="manual_test_soul",
            additional_metadata={
                "creator": "demo_system",
                "purpose": "testing_manual_creation"
            }
        )
        
        print(f"✅ Utworzono Soul ręcznie: {soul.alias}")
        print(f"Hash: {soul.soul_hash[:16]}...")
        print(f"Funkcje: {len(soul.list_functions())}")
        
        return soul
        
    except Exception as e:
        print(f"❌ Błąd podczas ręcznego tworzenia Soul: {e}")
        return None


async def demo_being_with_module_soul(soul):
    """Demo tworzenia i używania Being z modułowym Soul"""
    print(f"\n🤖 === DEMO BEING Z MODUŁOWYM SOUL ({soul.alias}) ===")
    
    try:
        # Utwórz Being z Soul
        being = await Being.create(
            soul=soul,
            alias=f"being_from_{soul.alias}",
            attributes={
                "test_mode": True,
                "created_by": "demo"
            }
        )
        
        print(f"✅ Utworzono Being: {being.alias}")
        print(f"Master funkcji: {being.is_function_master()}")
        
        # Test różnych wywołań
        print(f"\n🎯 Testowanie wywołań funkcji:")
        
        # 1. Wywołanie execute bez argumentów (inteligentne)
        print("\n1. Wywołanie execute() bez argumentów:")
        result = await being.execute()
        print(f"   Wynik: {result.get('data', {}).get('result')}")
        
        # 2. Wywołanie execute z danymi
        print("\n2. Wywołanie execute() z danymi:")
        result = await being.execute(data={"test": "hello world"})
        print(f"   Wynik: {result.get('data', {}).get('result')}")
        
        # 3. Wywołanie konkretnej funkcji
        print("\n3. Wywołanie konkretnej funkcji process_data:")
        result = await being.execute(function="process_data", data="test_data")
        print(f"   Wynik: {result.get('data', {}).get('result')}")
        
        # 4. Test funkcji async (jeśli istnieje)
        if 'async_process' in soul.list_functions():
            print("\n4. Wywołanie funkcji async:")
            result = await being.execute(function="async_process", data="async_test", delay=0.1)
            print(f"   Wynik: {result.get('data', {}).get('result')}")
        
        # Pokaż statystyki Being
        mastery_info = being.get_function_mastery_info()
        print(f"\n📊 Informacje o masterowaniu funkcji:")
        print(f"   Zarządzane funkcje: {mastery_info.get('managed_functions', [])}")
        print(f"   Liczba wykonań: {mastery_info.get('intelligent_executions', 0)}")
        
        return being
        
    except Exception as e:
        print(f"❌ Błąd podczas pracy z Being: {e}")
        return None


async def main():
    """Główna funkcja demo"""
    print("🚀 === DEMO SYSTEMU MODUŁÓW LUXDB ===")
    
    # 1. Walidacja modułów
    await demo_module_validation()
    
    # 2. Tworzenie Soul z pliku .module
    module_soul = await demo_create_soul_from_module_file()
    
    # 3. Ręczne tworzenie Soul
    manual_soul = await demo_create_soul_manually()
    
    # 4. Testy z Being
    if module_soul:
        await demo_being_with_module_soul(module_soul)
        
    if manual_soul:
        await demo_being_with_module_soul(manual_soul)
    
    print("\n✅ === DEMO ZAKOŃCZONE ===")


if __name__ == "__main__":
    asyncio.run(main())
