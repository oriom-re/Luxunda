
#!/usr/bin/env python3
"""
🚀 LuxOS Simple Start - Prosty punkt wejścia bez problemów z rekursją
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

class SimpleLuxOSStarter:
    """Prosty starter LuxOS bez problematycznych zależności"""

    def __init__(self):
        self.startup_time = datetime.now()
        self.logs = []

    def log(self, level: str, message: str):
        """Centralized logging"""
        timestamp = datetime.now().isoformat()
        colors = {"INFO": "\033[32m", "WARN": "\033[33m", "ERROR": "\033[31m", "SUCCESS": "\033[92m"}
        color = colors.get(level, "\033[0m")
        reset = "\033[0m"

        log_entry = f"{color}[{timestamp}] {level}{reset} {message}"
        self.logs.append(log_entry)
        print(log_entry)

    async def test_database_connection(self):
        """Test połączenia z bazą danych"""
        self.log("INFO", "Testowanie połączenia z bazą PostgreSQL...")
        
        try:
            from database.postgre_db import Postgre_db
            db_pool = await Postgre_db.get_db_pool()
            
            if db_pool:
                self.log("SUCCESS", "✅ Baza danych PostgreSQL działa")
                
                # Test prostego zapytania
                async with db_pool.acquire() as conn:
                    result = await conn.fetchval("SELECT COUNT(*) FROM souls")
                    self.log("INFO", f"Liczba souls w bazie: {result}")
                    
                    result = await conn.fetchval("SELECT COUNT(*) FROM beings")
                    self.log("INFO", f"Liczba beings w bazie: {result}")
                
                return True
            else:
                self.log("ERROR", "❌ Nie udało się połączyć z bazą danych")
                return False
                
        except Exception as e:
            self.log("ERROR", f"❌ Błąd bazy danych: {e}")
            return False

    async def test_simple_being_creation(self):
        """Test tworzenia prostego bytu"""
        self.log("INFO", "Testowanie tworzenia prostego bytu...")
        
        try:
            from luxdb.models.soul import Soul
            from luxdb.models.being import Being
            
            # Utwórz prostą Soul
            test_genotype = {
                "genesis": {
                    "name": "test_simple",
                    "type": "test",
                    "version": "1.0.0"
                },
                "attributes": {
                    "test_attr": {"py_type": "str"}
                }
            }
            
            soul = await Soul.create(test_genotype, alias="test_simple_soul")
            self.log("SUCCESS", f"✅ Soul utworzona: {soul.soul_hash[:8]}...")
            
            # Utwórz Being
            being = await Being.create(
                soul_hash=soul.soul_hash,
                data={"test_attr": "Hello from simple start!", "type": "test"}
            )
            self.log("SUCCESS", f"✅ Being utworzony: {being.ulid}")
            
            return True
            
        except Exception as e:
            self.log("ERROR", f"❌ Błąd tworzenia bytu: {e}")
            return False

    async def start_simple_web_server(self):
        """Uruchom prosty serwer web"""
        self.log("INFO", "Uruchamianie prostego serwera web...")
        
        try:
            from fastapi import FastAPI
            from fastapi.responses import HTMLResponse
            import uvicorn
            import threading
            import time
            
            app = FastAPI(title="LuxOS Simple Interface")
            
            @app.get("/", response_class=HTMLResponse)
            async def root():
                return """
                <html>
                    <head><title>LuxOS Simple Interface</title></head>
                    <body>
                        <h1>🌟 LuxOS Simple Interface</h1>
                        <p>Status: <span style="color: green;">✅ System działa!</span></p>
                        <p>Czas uruchomienia: """ + self.startup_time.isoformat() + """</p>
                        <h2>Dostępne endpointy:</h2>
                        <ul>
                            <li><a href="/status">/status</a> - Status systemu</li>
                            <li><a href="/docs">/docs</a> - API Documentation</li>
                        </ul>
                    </body>
                </html>
                """
            
            @app.get("/status")
            async def status():
                return {
                    "status": "running",
                    "startup_time": self.startup_time.isoformat(),
                    "system": "LuxOS Simple",
                    "database": "connected"
                }
            
            def run_server():
                uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            time.sleep(2)
            
            self.log("SUCCESS", "✅ Serwer web uruchomiony na http://0.0.0.0:5000")
            return True
            
        except Exception as e:
            self.log("ERROR", f"❌ Błąd serwera web: {e}")
            return False

    async def run_diagnostics(self):
        """Uruchom pełną diagnostykę"""
        self.log("INFO", "🔍 Rozpoczęcie diagnostyki LuxOS...")
        
        # Test bazy danych
        db_ok = await self.test_database_connection()
        
        # Test tworzenia bytu (tylko jeśli baza działa)
        being_ok = False
        if db_ok:
            being_ok = await self.test_simple_being_creation()
        
        # Podsumowanie
        self.log("INFO", "=" * 50)
        self.log("INFO", "📊 Wyniki diagnostyki:")
        self.log("SUCCESS" if db_ok else "ERROR", f"Baza danych: {'✅ OK' if db_ok else '❌ BŁĄD'}")
        self.log("SUCCESS" if being_ok else "ERROR", f"Tworzenie bytów: {'✅ OK' if being_ok else '❌ BŁĄD'}")
        
        if db_ok and being_ok:
            self.log("SUCCESS", "🎉 System podstawowo działa!")
            return True
        else:
            self.log("WARN", "⚠️ System ma problemy, ale można kontynuować")
            return False

    async def interactive_mode(self):
        """Tryb interaktywny do testowania"""
        self.log("INFO", "🔧 Tryb interaktywny - dostępne komendy:")
        print("  db     - Test bazy danych")
        print("  being  - Test tworzenia bytu")
        print("  web    - Uruchom serwer web")
        print("  status - Pokaż status")
        print("  exit   - Wyjście")
        
        while True:
            try:
                cmd = input("\nSimpleLux> ").strip().lower()
                
                if cmd == 'exit':
                    break
                elif cmd == 'db':
                    await self.test_database_connection()
                elif cmd == 'being':
                    await self.test_simple_being_creation()
                elif cmd == 'web':
                    await self.start_simple_web_server()
                    self.log("INFO", "Serwer działa w tle. Naciśnij Ctrl+C aby zatrzymać.")
                    try:
                        while True:
                            await asyncio.sleep(1)
                    except KeyboardInterrupt:
                        self.log("INFO", "Zatrzymano serwer")
                        break
                elif cmd == 'status':
                    await self.run_diagnostics()
                else:
                    print("Nieznana komenda. Dostępne: db, being, web, status, exit")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log("ERROR", f"Błąd: {e}")

async def main():
    """Główna funkcja"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LuxOS Simple Starter')
    parser.add_argument('--diagnostics', action='store_true', help='Uruchom diagnostykę')
    parser.add_argument('--interactive', action='store_true', help='Tryb interaktywny')
    parser.add_argument('--web', action='store_true', help='Uruchom serwer web')
    
    args = parser.parse_args()
    
    starter = SimpleLuxOSStarter()
    
    if args.diagnostics:
        await starter.run_diagnostics()
    elif args.interactive:
        await starter.interactive_mode()
    elif args.web:
        await starter.test_database_connection()
        await starter.start_simple_web_server()
        
        try:
            starter.log("INFO", "Serwer działa. Naciśnij Ctrl+C aby zatrzymać.")
            while True:
                await asyncio.sleep(10)
        except KeyboardInterrupt:
            starter.log("INFO", "👋 Zatrzymywanie serwera...")
    else:
        # Domyślnie uruchom diagnostykę
        success = await starter.run_diagnostics()
        
        print(f"\n🎯 Proponowane następne kroki:")
        print(f"  python simple_start.py --web          # Uruchom prosty serwer")
        print(f"  python simple_start.py --interactive  # Tryb interaktywny")

if __name__ == "__main__":
    asyncio.run(main())
