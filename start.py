#!/usr/bin/env python3
"""
🚀 LuxOS Kernel System Start
Entry point z nowym systemem bytów i hashów
"""

import asyncio
import uvicorn
from pathlib import Path
import os
import sys

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

async def initialize_kernel():
    """Inicjalizuje Kernel System"""
    try:
        from luxdb.core.kernel_system import kernel_system
        from luxdb.core.module_system import module_watcher
        from luxdb.core.json_kernel_runner import json_kernel_runner

        print("🚀 Inicjalizacja LuxOS Kernel System...")
        print("=" * 60)

        # Sprawdź czy jest plik konfiguracji JSON
        scenarios_dir = Path("scenarios")
        if scenarios_dir.exists():
            config_files = list(scenarios_dir.glob("*.json"))
            # Znajdź pierwszy plik konfiguracyjny JSON (nie .scenario)
            json_config = next((f for f in config_files if not f.name.endswith(".scenario")), None)

            if json_config:
                print(f"📋 Found JSON config: {json_config}")
                success = await json_kernel_runner.run_from_config(str(json_config))
                if success:
                    print("✅ System uruchomiony z konfiguracji JSON")
                    return True

        # Standardowy tryb kernel
        print("📦 Skanowanie i rejestracja modułów...")
        modules = await module_watcher.scan_and_register_all()

        print("🔗 Tworzenie relacji między modułami...")
        await module_watcher.create_module_relationships()

        # Inicjalizuj kernel
        await kernel_system.initialize("advanced")

        # Wyświetl statystyki
        stats = module_watcher.get_module_stats()
        print(f"📊 Statystyki modułów:")
        print(f"  - Zarejestrowane moduły: {stats['total_modules']}")
        print(f"  - Całkowity rozmiar: {stats['total_size_bytes']} bajtów")
        print(f"  - Typy modułów: {stats['module_types']}")
        
        status = await kernel_system.get_system_status()
        print(f"📊 System Status:")
        print(f"   Scenario: {status['active_scenario']}")
        print(f"   Beings: {status['registered_beings']}")
        print(f"   Hashes: {status['loaded_hashes']}")

        print("✅ LuxOS Kernel System zainicjalizowany")
        return True
    except ImportError as e:
        print(f"❌ Kernel initialization error: {e}")
        print("⚠️ Kernel nie uruchomiony, kontynuuję bez...")
        return False
    except Exception as e:
        print(f"❌ Kernel initialization error: {e}")
        return False

def main():
    """Start the LuxOS system with bootstrap option"""
    print("🚀 Starting LuxOS System...")
    print("=" * 60)

    # Check if user wants full bootstrap
    if "--bootstrap" in sys.argv or "--wake-up" in sys.argv:
        print("🌅 Launching full LuxOS Bootstrap procedure...")
        try:
            from luxos_bootstrap import wake_up_luxos
            result = asyncio.run(wake_up_luxos())
            
            if result["success"]:
                print("🎯 Bootstrap complete! Admin ready at http://0.0.0.0:3030")
                # Keep main process alive
                import time
                try:
                    while True:
                        time.sleep(30)
                except KeyboardInterrupt:
                    print("\n👋 LuxOS shutting down...")
                return
            else:
                print("⚠️ Bootstrap partial success, continuing with standard startup...")
        except Exception as e:
            print(f"❌ Bootstrap error: {e}, falling back to standard startup...")

    # Standard startup procedure
    kernel_ready = asyncio.run(initialize_kernel())

    if not kernel_ready:
        print("⚠️ Kernel nie uruchomiony, kontynuuję bez...")

    # Check if demo_landing.py exists and try to run it
    if Path("demo_landing.py").exists():
        print("📁 Found demo_landing.py - starting with Kernel integration...")
        try:
            # Import and run demo_landing
            uvicorn.run(
                "demo_landing:socket_app",
                host="0.0.0.0",
                port=3001,
                reload=False,
                log_level="info"
            )
        except Exception as e:
            print(f"❌ Error with demo_landing: {e}")
            fallback_server()
    else:
        print("📁 demo_landing.py not found - starting fallback...")
        fallback_server()

def fallback_server():
    """Simple fallback HTTP server"""
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    import os

    os.chdir("static") if Path("static").exists() else None

    class CustomHandler(SimpleHTTPRequestHandler):
        def end_headers(self):
            self.send_header('Access-Control-Allow-Origin', '*')
            super().end_headers()

    print("🌐 Starting simple HTTP server on port 3001...")
    server = HTTPServer(("0.0.0.0", 3001), CustomHandler)
    print("✅ Server running at http://0.0.0.0:3001")
    server.serve_forever()

if __name__ == "__main__":
    main()