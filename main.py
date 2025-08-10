#!/usr/bin/env python3
"""
🚀 LuxOS - Jedyny punkt wejścia dla całego systemu
"""

import asyncio
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import threading
import time

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

class LuxOSSystem:
    """Zunifikowany system LuxOS - jeden punkt wejścia dla wszystkiego"""

    def __init__(self):
        self.startup_time = datetime.now()
        self.components_active = {
            'database': False,
            'web_server': False,
            'advanced_systems': False
        }
        self.logs = []
        self.app = None  # Inicjalizacja zmiennej dla aplikacji FastAPI

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
        """Inicjalizuje bazę danych PostgreSQL"""
        self.log("INFO", "Inicjalizacja bazy PostgreSQL...", "DATABASE")

        try:
            from database.postgre_db import Postgre_db
            db_pool = await Postgre_db.get_db_pool()

            if db_pool:
                self.log("SUCCESS", "✅ Baza danych PostgreSQL zainicjalizowana", "DATABASE")

                # Test połączenia i wyświetl statystyki
                async with db_pool.acquire() as conn:
                    souls_count = await conn.fetchval("SELECT COUNT(*) FROM souls")
                    beings_count = await conn.fetchval("SELECT COUNT(*) FROM beings")
                    self.log("INFO", f"Souls w bazie: {souls_count}", "DATABASE")
                    self.log("INFO", f"Beings w bazie: {beings_count}", "DATABASE")

                self.components_active['database'] = True
                return True
            else:
                self.log("ERROR", "❌ Nie udało się połączyć z bazą danych", "DATABASE")
                return False

        except Exception as e:
            self.log("ERROR", f"❌ Błąd inicjalizacji bazy danych: {e}", "DATABASE")
            return False

    async def start_web_server(self, port: int = 5000):
        """Uruchomienie serwera web"""
        self.log("INFO", f"Uruchamianie serwera web na porcie {port}...", "WEB")

        try:
            from fastapi import FastAPI
            from fastapi.responses import HTMLResponse, JSONResponse
            from fastapi.staticfiles import StaticFiles
            import uvicorn

            self.app = FastAPI(title="LuxOS System Interface") # Przypisanie do self.app

            # Obsługa plików statycznych
            try:
                self.app.mount("/static", StaticFiles(directory="static"), name="static")
            except Exception as e:
                self.log("WARN", f"Katalog static: {e}", "WEB")

            @self.app.get("/", response_class=HTMLResponse)
            async def root():
                return f"""
                <html>
                    <head><title>LuxOS System</title></head>
                    <body>
                        <h1>🌟 LuxOS System Interface</h1>
                        <p>Status: <span style="color: green;">✅ System działa!</span></p>
                        <p>Czas uruchomienia: {self.startup_time.isoformat()}</p>
                        <p>Baza danych: {'✅ Połączona' if self.components_active['database'] else '❌ Rozłączona'}</p>

                        <h2>Dostępne endpointy:</h2>
                        <ul>
                            <li><a href="/status">/status</a> - Status systemu</li>
                            <li><a href="/docs">/docs</a> - API Documentation</li>
                            <li><a href="/beings">/beings</a> - Lista bytów</li>
                            <li><a href="/health">/health</a> - Sprawdzenie zdrowia systemu</li>
                        </ul>

                        <h2>Interfejsy:</h2>
                        <ul>
                            <li><a href="/static/landing.html">Landing Page</a></li>
                            <li><a href="/static/lux_interface.html">Lux Interface</a></li>
                            <li><a href="/static/demo_interface.html">Demo Interface</a></li>
                        </ul>
                    </body>
                </html>
                """

            @self.app.get("/status")
            async def status():
                try:
                    # Sprawdź połączenie z bazą danych bezpośrednio
                    from database.postgre_db import Postgre_db

                    db_status = "disconnected"
                    beings_count = 0
                    souls_count = 0

                    try:
                        db_pool = await Postgre_db.get_db_pool()
                        if db_pool:
                            async with db_pool.acquire() as conn:
                                # Sprawdź połączenie i pobierz statystyki
                                souls_result = await conn.fetch("SELECT COUNT(*) as count FROM souls")
                                beings_result = await conn.fetch("SELECT COUNT(*) as count FROM beings")

                                souls_count = souls_result[0]['count'] if souls_result else 0
                                beings_count = beings_result[0]['count'] if beings_result else 0
                                db_status = "connected"
                    except Exception as e:
                        self.log("WARNING", f"Database status check failed: {str(e)}", "WEB")
                        db_status = "disconnected"

                    return {
                        "status": "running" if db_status == "connected" else "error",
                        "mode": "main_system",
                        "beings_count": beings_count,
                        "souls_count": souls_count,
                        "uptime": datetime.now().isoformat(),
                        "database": db_status,
                        "service": "LuxOS Main System",
                        "lux_assistant_ready": True,
                        "specialists_available": True
                    }
                except Exception as e:
                    self.log("ERROR", f"Status endpoint error: {str(e)}", "WEB")
                    return {
                        "status": "error",
                        "error": str(e),
                        "uptime": datetime.now().isoformat(),
                        "database": "disconnected",
                        "beings_count": 0,
                        "souls_count": 0
                    }

            @self.app.get("/health")
            async def health():
                if self.components_active['database']:
                    return {"status": "healthy", "database": "connected"}
                else:
                    return {"status": "degraded", "database": "disconnected"}

            @self.app.get("/beings")
            async def list_beings():
                if not self.components_active['database']:
                    return {"error": "Database not connected"}

                try:
                    # Bezpośrednie połączenie z bazą danych bez używania BeingRepository
                    from database.postgre_db import Postgre_db

                    db_pool = await Postgre_db.get_db_pool()
                    if not db_pool:
                        return {"error": "Database pool not available"}

                    async with db_pool.acquire() as conn:
                        # Pobierz beings z bazy danych
                        beings_data = await conn.fetch("""
                            SELECT b.ulid, b.alias, b.data, b.created_at, s.alias as soul_alias
                            FROM beings b
                            LEFT JOIN souls s ON b.soul_hash = s.soul_hash
                            ORDER BY b.created_at DESC
                            LIMIT 20
                        """)

                        beings_list = []
                        for row in beings_data:
                            being_data = dict(row['data']) if row['data'] else {}
                            beings_list.append({
                                "ulid": row['ulid'],
                                "alias": row['alias'],
                                "soul_alias": row['soul_alias'],
                                "type": being_data.get('type', 'unknown'),
                                "name": being_data.get('name', 'Unnamed'),
                                "created_at": row['created_at'].isoformat() if row['created_at'] else None
                            })

                        return {"beings": beings_list, "count": len(beings_list)}

                except Exception as e:
                    self.log("ERROR", f"Error fetching beings: {str(e)}", "WEB")
                    return {"error": f"Error fetching beings: {str(e)}"}

            def run_server():
                uvicorn.run(self.app, host="0.0.0.0", port=port, log_level="info")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(2)  # Daj czas na uruchomienie

            self.log("SUCCESS", f"✅ Serwer web uruchomiony na http://0.0.0.0:{port}", "WEB")
            self.components_active['web_server'] = True
            return True

        except Exception as e:
            self.log("ERROR", f"❌ Błąd serwera web: {e}", "WEB")
            return False

    async def initialize_advanced_systems(self):
        """Inicjalizuje zaawansowane systemy (opcjonalne)"""
        self.log("INFO", "Inicjalizacja zaawansowanych systemów...", "ADVANCED")

        try:
            # Próba inicjalizacji kernel system bez problemowych zależności
            try:
                from luxdb.core.primitive_beings import PrimitiveBeingFactory

                # Test tworzenia prostego bytu
                test_being = await PrimitiveBeingFactory.create_being(
                    'message',
                    alias='system_test',
                    name='System Test Being'
                )
                await test_being.set_message('System uruchomiony poprawnie!', 'system')
                self.log("SUCCESS", f"✅ Test being utworzony: {test_being.ulid[:8]}", "ADVANCED")

            except Exception as e:
                self.log("WARN", f"Zaawansowane systemy niedostępne: {e}", "ADVANCED")
                return False

            self.components_active['advanced_systems'] = True
            return True

        except Exception as e:
            self.log("ERROR", f"❌ Błąd inicjalizacji zaawansowanych systemów: {e}", "ADVANCED")
            return False

    async def run_diagnostics(self):
        """Uruchom pełną diagnostykę systemu"""
        self.log("INFO", "🔍 Rozpoczęcie diagnostyki LuxOS...", "DIAG")

        # Test bazy danych
        db_ok = await self.initialize_database()

        # Test zaawansowanych systemów (jeśli baza działa)
        advanced_ok = False
        if db_ok:
            advanced_ok = await self.initialize_advanced_systems()

        # Podsumowanie
        self.log("INFO", "=" * 60, "DIAG")
        self.log("INFO", "📊 Wyniki diagnostyki:", "DIAG")
        self.log("SUCCESS" if db_ok else "ERROR", f"Baza danych: {'✅ OK' if db_ok else '❌ BŁĄD'}", "DIAG")
        self.log("SUCCESS" if advanced_ok else "WARN", f"Zaawansowane systemy: {'✅ OK' if advanced_ok else '⚠️ OGRANICZONE'}", "DIAG")

        if db_ok:
            self.log("SUCCESS", "🎉 System podstawowo działa!", "DIAG")
            return True
        else:
            self.log("ERROR", "❌ System ma problemy z bazą danych", "DIAG")
            return False

    async def interactive_mode(self):
        """Tryb interaktywny"""
        self.log("INFO", "🔧 Tryb interaktywny LuxOS", "INTERACTIVE")
        print("\nDostępne komendy:")
        print("  status     - Pokaż status systemu")
        print("  db         - Test bazy danych")
        print("  web        - Uruchom serwer web")
        print("  beings     - Lista bytów")
        print("  create     - Utwórz nowy byt")
        print("  help       - Pomoc")
        print("  exit       - Wyjście")

        while True:
            try:
                cmd = input("\nLuxOS> ").strip().lower().split()

                if not cmd:
                    continue

                if cmd[0] == 'exit':
                    break
                elif cmd[0] == 'status':
                    await self.show_status()
                elif cmd[0] == 'db':
                    await self.initialize_database()
                elif cmd[0] == 'web':
                    await self.start_web_server()
                    print("Serwer działa w tle. Wpisz 'exit' aby zakończyć.")
                elif cmd[0] == 'beings':
                    await self.list_beings()
                elif cmd[0] == 'create':
                    await self.create_being_interactive()
                elif cmd[0] == 'help':
                    print("Dostępne komendy: status, db, web, beings, create, exit")
                else:
                    print("Nieznana komenda. Wpisz 'help' aby zobaczyć dostępne komendy.")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Błąd: {e}")

    async def show_status(self):
        """Pokaż status systemu"""
        self.log("INFO", "📊 Status systemu LuxOS:", "STATUS")

        for component, active in self.components_active.items():
            status = "✅ Aktywny" if active else "❌ Nieaktywny"
            self.log("INFO", f"{component}: {status}", "STATUS")

        uptime = datetime.now() - self.startup_time
        self.log("INFO", f"Czas działania: {uptime}", "STATUS")

    async def list_beings(self):
        """Lista bytów w systemie"""
        if not self.components_active['database']:
            print("Baza danych nie jest połączona")
            return

        try:
            from luxdb.repository.soul_repository import BeingRepository
            result = await BeingRepository.get_all_beings(limit=10)

            if result.get('success') and result.get('beings'):
                print("\n📋 Lista bytów:")
                for being in result['beings']:
                    being_type = being.get_data('type', 'unknown')
                    created = being.created_at.strftime('%Y-%m-%d %H:%M') if being.created_at else 'unknown'
                    print(f"  {being.alias or being.ulid[:8]}: {being_type} (created: {created})")
            else:
                print("Brak bytów w systemie")
        except Exception as e:
            print(f"Błąd: {e}")

    async def create_being_interactive(self):
        """Tworzenie bytu w trybie interaktywnym"""
        if not self.components_active['database']:
            print("Baza danych nie jest połączona")
            return

        try:
            being_type = input("Typ bytu (message/data/function): ").strip()
            alias = input("Alias: ").strip()

            from luxdb.core.primitive_beings import PrimitiveBeingFactory
            being = await PrimitiveBeingFactory.create_being(
                being_type,
                alias=alias,
                name=f"Interactive {being_type}",
                created_via='interactive_mode'
            )
            print(f"✅ Utworzono byt: {being.ulid} ({being_type})")

        except Exception as e:
            print(f"Błąd tworzenia bytu: {e}")

    async def start_system(self, mode: str = "basic"):
        """Główna funkcja startowa systemu"""
        self.log("SUCCESS", "🌟 ROZPOCZĘCIE URUCHOMIENIA LUXOS SYSTEM", "MAIN")
        self.log("INFO", f"Tryb: {mode}", "MAIN")
        self.log("INFO", "=" * 60, "MAIN")

        # Zawsze inicjalizuj bazę danych
        db_success = await self.initialize_database()

        if not db_success and mode not in ["basic", "diagnostics"]:
            self.log("ERROR", "❌ Nie można kontynuować bez bazy danych", "MAIN")
            return False

        # W trybie full lub web uruchom serwer
        if mode in ["full", "web", "server"]:
            await self.start_web_server()

        # W trybie full spróbuj uruchomić zaawansowane systemy
        if mode == "full":
            await self.initialize_advanced_systems()

        # Podsumowanie
        active_count = sum(self.components_active.values())
        total_count = len(self.components_active)

        self.log("INFO", "=" * 60, "MAIN")
        if active_count == total_count:
            self.log("SUCCESS", "🎉 LUXOS SYSTEM URUCHOMIONY POMYŚLNIE!", "MAIN")
        elif active_count > 0:
            self.log("SUCCESS", f"✅ LUXOS SYSTEM URUCHOMIONY CZĘŚCIOWO ({active_count}/{total_count})", "MAIN")
        else:
            self.log("ERROR", "❌ LUXOS SYSTEM NIE URUCHOMIŁ SIĘ POPRAWNIE", "MAIN")
            return False

        if self.components_active['web_server']:
            self.log("SUCCESS", "🌐 Interfejs web: http://0.0.0.0:5000", "MAIN")

        self.log("INFO", "=" * 60, "MAIN")
        return True

async def main():
    """Główna funkcja aplikacji"""
    parser = argparse.ArgumentParser(description='LuxOS - Unified System')
    parser.add_argument('--mode', choices=['basic', 'web', 'full', 'server'], default='web',
                       help='Tryb uruchomienia systemu (domyślny: web)')
    parser.add_argument('--diagnostics', action='store_true', help='Uruchom diagnostykę systemu')
    parser.add_argument('--interactive', action='store_true', help='Tryb interaktywny')
    parser.add_argument('--status', action='store_true', help='Pokaż tylko status')

    args = parser.parse_args()

    print("🌟 LuxOS - Unified System")
    print("=========================")

    system = LuxOSSystem()

    # Tryb diagnostyczny
    if args.diagnostics:
        success = await system.run_diagnostics()
        sys.exit(0 if success else 1)

    # Tryb tylko status
    if args.status:
        await system.initialize_database()
        await system.show_status()
        return

    # Tryb interaktywny
    if args.interactive:
        await system.initialize_database()
        await system.interactive_mode()
        return

    # Standardowe uruchomienie systemu
    success = await system.start_system(args.mode)

    if not success:
        sys.exit(1)

    # W trybach z serwerem, utrzymaj system żywy
    if args.mode in ["web", "full", "server"]:
        system.log("INFO", "System uruchomiony. Naciśnij Ctrl+C aby zakończyć.", "MAIN")
        try:
            while True:
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            system.log("INFO", "👋 Zamykanie LuxOS System...", "MAIN")
    else:
        # W trybie basic pokaż instrukcje
        print(f"\nSystem uruchomiony w trybie: {args.mode}")
        print("Dostępne opcje:")
        print("  python main.py --mode=web        # Serwer web (domyślny)")
        print("  python main.py --mode=full       # Pełny system")
        print("  python main.py --diagnostics     # Diagnostyka")
        print("  python main.py --interactive     # Tryb interaktywny")
        print("  python main.py --status          # Status systemu")

if __name__ == "__main__":
    asyncio.run(main())