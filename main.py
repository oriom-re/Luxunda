#!/usr/bin/env python3
"""
🚀 LuxOS Unified Start System - Jeden punkt wejścia dla całego systemu
"""

import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

from database.postgre_db import Postgre_db
from luxdb.models.being import Being
from luxdb.core.primitive_beings import PrimitiveBeingFactory
from luxdb.core.admin_kernel import admin_kernel
from luxdb.core.kernel_system import kernel_system
import uvicorn
import threading
import time

class LuxOSUnifiedSystem:
    """Zunifikowany system startowy LuxOS"""

    def __init__(self):
        self.startup_time = datetime.now()
        self.components_active = {
            'database': False,
            'kernel_system': False,
            'admin_kernel': False,
            'admin_server': False
        }
        self.logs = []

    def log(self, level: str, message: str, component: str = "MAIN"):
        """Centralized logging"""
        timestamp = datetime.now().isoformat()
        colors = {"INFO": "\033[32m", "WARN": "\033[33m", "ERROR": "\033[31m", "SUCCESS": "\033[92m"}
        color = colors.get(level, "\033[0m")
        reset = "\033[0m"

        log_entry = f"{color}[{timestamp}] {level} [{component}]{reset} {message}"
        self.logs.append(log_entry)
        print(log_entry)

    async def initialize_database(self):
        """Inicjalizuje bazę danych"""
        self.log("INFO", "Inicjalizacja bazy PostgreSQL...", "DATABASE")

        try:
            db_pool = await Postgre_db.get_db_pool()
            if db_pool:
                self.log("SUCCESS", "Baza danych PostgreSQL zainicjalizowana", "DATABASE")
                self.components_active['database'] = True
                return True
            else:
                self.log("ERROR", "Nie udało się połączyć z bazą danych", "DATABASE")
                return False
        except Exception as e:
            self.log("ERROR", f"Błąd inicjalizacji bazy danych: {e}", "DATABASE")
            return False

    async def initialize_kernel_system(self):
        """Inicjalizuje główny system kernel"""
        self.log("INFO", "Inicjalizacja Kernel System...", "KERNEL")

        try:
            await kernel_system.initialize("advanced")
            status = await kernel_system.get_system_status()

            self.log("SUCCESS", f"Kernel System aktywny - Scenariusz: {status['active_scenario']}", "KERNEL")
            self.components_active['kernel_system'] = True
            return True

        except Exception as e:
            self.log("ERROR", f"Błąd inicjalizacji Kernel System: {e}", "KERNEL")
            return False

    async def initialize_admin_kernel(self):
        """Inicjalizuje admin kernel interface"""
        self.log("INFO", "Inicjalizacja Admin Kernel Interface...", "ADMIN")

        try:
            await admin_kernel.initialize()

            self.log("SUCCESS", "Admin Kernel Interface aktywny", "ADMIN")
            self.log("INFO", f"Kernel Being aktywny: {admin_kernel.system_status['kernel_active']}", "ADMIN")
            self.log("INFO", f"Lux Being aktywny: {admin_kernel.system_status['lux_active']}", "ADMIN")

            self.components_active['admin_kernel'] = True
            return True

        except Exception as e:
            self.log("ERROR", f"Błąd inicjalizacji Admin Kernel: {e}", "ADMIN")
            return False

    def start_admin_server(self, port: int = 3030):
        """Uruchamia admin server w tle"""
        self.log("INFO", f"Uruchamianie Admin Server na porcie {port}...", "SERVER")

        try:
            def run_server():
                try:
                    from admin_kernel_server import app
                    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
                except Exception as e:
                    self.log("ERROR", f"Błąd Admin Server: {e}", "SERVER")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(2)  # Daj czas na uruchomienie

            self.log("SUCCESS", f"Admin Server uruchomiony na http://0.0.0.0:{port}", "SERVER")
            self.components_active['admin_server'] = True
            return True

        except Exception as e:
            self.log("ERROR", f"Błąd uruchomienia Admin Server: {e}", "SERVER")
            return False

    async def create_sample_beings(self):
        """Tworzy przykładowe byty w systemie"""
        self.log("INFO", "Tworzę przykładowe byty...", "BEINGS")

        try:
            # Przykładowy byt danych
            data_being = await PrimitiveBeingFactory.create_being(
                'data',
                alias='sample_data',
                name='Sample Data Storage',
                description='Przykładowy byt do przechowywania danych'
            )
            await data_being.store_value('sample_key', 'sample_value')
            self.log("SUCCESS", f"Data Being utworzony: {data_being.ulid}", "BEINGS")

            # Przykładowy byt funkcji
            function_being = await PrimitiveBeingFactory.create_being(
                'function',
                alias='sample_function',
                name='Sample Function',
                description='Przykładowa funkcja'
            )
            await function_being.set_function('hello_world', 'def hello_world(): return "Hello, World!"')
            self.log("SUCCESS", f"Function Being utworzony: {function_being.ulid}", "BEINGS")

            # Przykładowy byt wiadomości
            message_being = await PrimitiveBeingFactory.create_being(
                'message',
                alias='sample_message',
                name='Sample Message'
            )
            await message_being.set_message('Witaj w LuxOS!', 'system')
            self.log("SUCCESS", f"Message Being utworzony: {message_being.ulid}", "BEINGS")

            return True

        except Exception as e:
            self.log("ERROR", f"Błąd tworzenia przykładowych bytów: {e}", "BEINGS")
            return False

    async def show_system_status(self):
        """Wyświetla status systemu"""
        self.log("INFO", "Status systemu LuxOS:", "STATUS")

        try:
            # Status komponentów
            for component, active in self.components_active.items():
                status = "✅ Aktywny" if active else "❌ Nieaktywny"
                self.log("INFO", f"{component}: {status}", "STATUS")

            # Policz byty jeśli baza jest aktywna
            if self.components_active['database']:
                beings_count = await BeingRepository.count_beings()
                self.log("INFO", f"Liczba bytów w systemie: {beings_count}", "STATUS")

                # Pokaż ostatnie byty
                result = await BeingRepository.get_all_beings(limit=5)
                if result.get('success') and result.get('beings'):
                    self.log("INFO", "Ostatnie byty:", "STATUS")
                    for being in result['beings']:
                        being_type = being.get_data('type', 'unknown')
                        self.log("INFO", f"  - {being.alias or being.ulid[:8]}: {being_type}", "STATUS")

        except Exception as e:
            self.log("ERROR", f"Błąd sprawdzania statusu: {e}", "STATUS")

    async def run_interactive_mode(self):
        """Uruchamia tryb interaktywny"""
        self.log("INFO", "Tryb interaktywny LuxOS", "INTERACTIVE")
        print("\nDostępne komendy:")
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
                    await self.show_system_status()
                elif command[0] == 'list':
                    await self.list_beings()
                elif command[0] == 'create' and len(command) >= 3:
                    being_type = command[1]
                    alias = command[2]
                    await self.create_being_interactive(being_type, alias)
                else:
                    print("Nieznana komenda. Spróbuj: create, list, status, exit")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Błąd: {e}")

    async def list_beings(self):
        """Wyświetla listę bytów"""
        try:
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

    async def create_being_interactive(self, being_type: str, alias: str):
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

    async def full_system_startup(self, mode: str = "basic"):
        """Pełne uruchomienie systemu"""
        self.log("SUCCESS", "🌟 ROZPOCZĘCIE URUCHOMIENIA LUXOS SYSTEM", "MAIN")
        self.log("INFO", "=" * 60, "MAIN")

        # Inicjalizacja komponentów
        db_success = await self.initialize_database()
        if not db_success:
            return False

        kernel_success = await self.initialize_kernel_system()

        if mode in ["full", "admin", "server"]:
            admin_success = await self.initialize_admin_kernel()
            server_success = self.start_admin_server()

        # Initialize Authentication System
        self.log("INFO", "AUTH", "Inicjalizacja Authentication Manager...")
        try:
            from luxdb.core.auth_session import auth_manager
            await auth_manager.initialize()
            self.log("SUCCESS", "AUTH", "Authentication Manager zainicjalizowany")
        except Exception as e:
            self.log("ERROR", "AUTH", f"Błąd inicjalizacji Authentication: {e}")
            return False

        # Initialize Communication System
        self.log("INFO", "COMM", "Inicjalizacja Communication System...")
        try:
            from luxdb.core.communication_system import communication_system
            await communication_system.initialize()
            self.log("SUCCESS", "COMM", "Communication System zainicjalizowany")
        except Exception as e:
            self.log("ERROR", "COMM", f"Błąd inicjalizacji Communication: {e}")
            return False

        # Initialize Lux Assistant Communication
        self.log("INFO", "LUX", "Inicjalizacja Lux Assistant Communication...")
        try:
            from luxdb.ai_lux_assistant import LuxAssistant
            from luxdb.core.session_assistant import session_manager
            
            # Pobierz klucz OpenAI z zmiennych środowiskowych
            import os
            openai_key = os.getenv('OPENAI_API_KEY')
            
            if openai_key:
                # Zainicjalizuj główny Lux Assistant
                global_lux = LuxAssistant(openai_key)
                await global_lux.initialize()
                
                # Dodaj do session managera jako główną instancję
                session_manager.global_lux_assistant = global_lux
                
                self.log("SUCCESS", "LUX", "Lux Assistant Communication zainicjalizowany")
            else:
                self.log("WARN", "LUX", "Brak OPENAI_API_KEY - Lux Assistant wyłączony")
                
        except Exception as e:
            self.log("ERROR", "LUX", f"Błąd inicjalizacji Lux Assistant: {e}")
            # Nie przerywamy działania systemu - Lux to opcjonalny komponent

        # Podsumowanie
        active_count = sum(self.components_active.values())
        total_count = len(self.components_active)

        self.log("INFO", "=" * 60, "MAIN")
        if active_count == total_count:
            self.log("SUCCESS", "🎉 LUXOS SYSTEM URUCHOMIONY POMYŚLNIE!", "MAIN")
            if self.components_active['admin_server']:
                self.log("SUCCESS", "👑 Admin Interface: http://0.0.0.0:3030", "MAIN")
        else:
            self.log("WARN", f"⚠️ Uruchomienie częściowe: {active_count}/{total_count} komponentów", "MAIN")

        self.log("INFO", "=" * 60, "MAIN")
        return True

async def main():
    """Główna funkcja startowa"""
    parser = argparse.ArgumentParser(description='LuxOS Unified System Starter')
    parser.add_argument('--mode', choices=['basic', 'full', 'admin', 'server'], default='basic',
                       help='Tryb uruchomienia systemu')
    parser.add_argument('--bootstrap', action='store_true', help='Tworzy przykładowe byty')
    parser.add_argument('--interactive', action='store_true', help='Tryb interaktywny')
    parser.add_argument('--status', action='store_true', help='Wyświetla status systemu')
    parser.add_argument('--wakeup', action='store_true', help='Pełne przebudzenie systemu (alias for --mode=full)')
    parser.add_argument('--ignore-errors', action='store_true', help='Ignoruje błędy podczas uruchamiania') # Added for ignore_errors

    args = parser.parse_args()

    # Mapuj wakeup na mode=full
    if args.wakeup:
        args.mode = 'full'

    print("🌟 LuxOS Unified System")
    print("======================")

    system = LuxOSUnifiedSystem()

    # Uruchom system w odpowiednim trybie
    if not await system.full_system_startup(args.mode):
        sys.exit(1)

    # Wykonaj dodatkowe akcje
    if args.bootstrap:
        await system.create_sample_beings()

    if args.status:
        await system.show_system_status()

    if args.interactive:
        await system.run_interactive_mode()
    elif args.mode in ["full", "server"]:
        # Utrzymaj system żywy w trybie serwera
        system.log("INFO", "System uruchomiony w trybie serwera. Naciśnij Ctrl+C aby zakończyć.", "MAIN")
        try:
            while True:
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            system.log("INFO", "👋 LuxOS System shutting down...", "MAIN")
    else:
        # W trybie basic pokaż status i zakończ
        await system.show_system_status()
        print("\nUżyj --help aby zobaczyć dostępne opcje")
        print("Przykłady:")
        print("  python main.py --mode=full --bootstrap    # Pełny system z przykładowymi danymi")
        print("  python main.py --wakeup                   # Pełne przebudzenie (alias)")
        print("  python main.py --interactive              # Tryb interaktywny")
        print("  python main.py --status                   # Tylko status systemu")

if __name__ == "__main__":
    asyncio.run(main())