
#!/usr/bin/env python3
"""
🚀 LuxOS Modern Start Script - Tylko nowoczesne JSONB systemy
"""

import asyncio
import sys
import argparse
from database.postgre_db import Postgre_db
from luxdb.models.being import Being
from luxdb.core.primitive_beings import PrimitiveBeingFactory

async def initialize_database():
    """Inicjalizuje bazę danych"""
    print("🔄 Inicjalizacja bazy PostgreSQL...")
    
    if not await Postgre_db.initialize_pool():
        print("❌ Nie udało się połączyć z bazą danych")
        return False
    
    print("✅ Baza danych PostgreSQL zainicjalizowana")
    return True

async def create_sample_beings():
    """Tworzy przykładowe byty w systemie"""
    print("🧬 Tworzę przykładowe byty...")
    
    # Przykładowy byt danych
    data_being = await PrimitiveBeingFactory.create_being(
        'data',
        alias='sample_data',
        name='Sample Data Storage',
        description='Przykładowy byt do przechowywania danych'
    )
    await data_being.store_value('sample_key', 'sample_value')
    print(f"📦 Data Being: {data_being.ulid}")
    
    # Przykładowy byt funkcji
    function_being = await PrimitiveBeingFactory.create_being(
        'function',
        alias='sample_function',
        name='Sample Function',
        description='Przykładowa funkcja'
    )
    await function_being.set_function('hello_world', 'def hello_world(): return "Hello, World!"')
    print(f"⚙️ Function Being: {function_being.ulid}")
    
    # Przykładowy byt wiadomości
    message_being = await PrimitiveBeingFactory.create_being(
        'message',
        alias='sample_message',
        name='Sample Message'
    )
    await message_being.set_message('Witaj w LuxOS!', 'system')
    print(f"💌 Message Being: {message_being.ulid}")
    
    print("✅ Przykładowe byty utworzone")

async def show_system_status():
    """Wyświetla status systemu"""
    print("\n📊 Status systemu LuxOS:")
    
    try:
        # Sprawdź połączenie z bazą
        pool = await Postgre_db.get_db_pool()
        if pool:
            print("✅ Baza danych: Połączona")
            
            # Policz byty
            from luxdb.repository.soul_repository import BeingRepository
            beings_count = await BeingRepository.count_beings()
            print(f"🧬 Liczba bytów: {beings_count}")
            
            # Pokaż ostatnie byty
            result = await BeingRepository.get_all_beings(limit=5)
            if result.get('success') and result.get('beings'):
                print("📋 Ostatnie byty:")
                for being in result['beings'][:5]:
                    being_type = being.get_data('type', 'unknown')
                    print(f"   - {being.alias or being.ulid[:8]}: {being_type}")
            
        else:
            print("❌ Baza danych: Brak połączenia")
            
    except Exception as e:
        print(f"❌ Błąd sprawdzania statusu: {e}")

async def run_interactive_mode():
    """Uruchamia tryb interaktywny"""
    print("\n🎮 Tryb interaktywny LuxOS")
    print("Dostępne komendy:")
    print("  create <type> <alias> - Tworzy nowy byt")
    print("  list - Wyświetla wszystkie byty")
    print("  status - Wyświetla status systemu")
    print("  exit - Wychodzi z trybu interaktywnego")
    
    while True:
        try:
            command = input("\nLuxOS> ").strip().split()
            
            if not command:
                continue
            
            if command[0] == 'exit':
                break
            elif command[0] == 'status':
                await show_system_status()
            elif command[0] == 'list':
                await list_beings()
            elif command[0] == 'create' and len(command) >= 3:
                being_type = command[1]
                alias = command[2]
                await create_being_interactive(being_type, alias)
            else:
                print("Nieznana komenda. Spróbuj: create, list, status, exit")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Błąd: {e}")

async def list_beings():
    """Wyświetla listę bytów"""
    try:
        from luxdb.repository.soul_repository import BeingRepository
        result = await BeingRepository.get_all_beings(limit=20)
        
        if result.get('success') and result.get('beings'):
            print("\n📋 Lista bytów:")
            for being in result['beings']:
                being_type = being.get_data('type', 'unknown')
                created = being.created_at.strftime('%Y-%m-%d %H:%M') if being.created_at else 'unknown'
                print(f"  {being.alias or being.ulid[:8]}: {being_type} (created: {created})")
        else:
            print("Brak bytów w systemie")
            
    except Exception as e:
        print(f"Błąd listowania bytów: {e}")

async def create_being_interactive(being_type: str, alias: str):
    """Tworzy byt w trybie interaktywnym"""
    try:
        being = await PrimitiveBeingFactory.create_being(
            being_type,
            alias=alias,
            name=f"Interactive {being_type}",
            created_via='interactive_mode'
        )
        print(f"✅ Utworzono byt: {being.ulid} ({being_type})")
        
    except Exception as e:
        print(f"Błąd tworzenia bytu: {e}")

async def main():
    """Główna funkcja startowa"""
    parser = argparse.ArgumentParser(description='LuxOS Modern System Starter')
    parser.add_argument('--bootstrap', action='store_true', help='Tworzy przykładowe byty')
    parser.add_argument('--interactive', action='store_true', help='Tryb interaktywny')
    parser.add_argument('--status', action='store_true', help='Wyświetla status systemu')
    
    args = parser.parse_args()
    
    print("🌟 LuxOS Modern System")
    print("====================")
    
    # Inicjalizacja bazy danych
    if not await initialize_database():
        sys.exit(1)
    
    # Wykonaj odpowiednią akcję
    if args.bootstrap:
        await create_sample_beings()
    elif args.status:
        await show_system_status()
    elif args.interactive:
        await show_system_status()
        await run_interactive_mode()
    else:
        # Domyślnie pokaż status
        await show_system_status()
        print("\nUżyj --help aby zobaczyć dostępne opcje")

if __name__ == "__main__":
    asyncio.run(main())
