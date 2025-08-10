
#!/usr/bin/env python3
"""
LuxOS - Standalone Main System
Uproszczony system działający bez zewnętrznych modułów
"""

import os
import sys
import asyncio
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
import logging

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleDatabase:
    """Prosta baza danych SQLite"""
    
    def __init__(self, db_path: str = "luxos_main.db"):
        self.db_path = db_path
        self.connection = None
        
    async def connect(self):
        """Połączenie z bazą danych"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            await self.init_tables()
            logger.info("✅ Połączono z bazą danych SQLite")
            return True
        except Exception as e:
            logger.error(f"❌ Błąd połączenia z bazą: {e}")
            return False
    
    async def init_tables(self):
        """Inicjalizacja tabel"""
        cursor = self.connection.cursor()
        
        # Tabela bytów (beings)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS beings (
                id TEXT PRIMARY KEY,
                alias TEXT UNIQUE,
                name TEXT,
                description TEXT,
                type TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela dusz (souls)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS souls (
                id TEXT PRIMARY KEY,
                name TEXT,
                being_id TEXT,
                soul_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (being_id) REFERENCES beings (id)
            )
        """)
        
        self.connection.commit()
        logger.info("✅ Tabele zainicjalizowane")

    async def execute(self, query: str, params: tuple = ()):
        """Wykonanie zapytania"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"❌ Błąd zapytania: {e}")
            return []

    async def close(self):
        """Zamknięcie połączenia"""
        if self.connection:
            self.connection.close()
            logger.info("🔄 Zamknięto połączenie z bazą")

class SimpleBeing:
    """Prosty byt LuxOS"""
    
    def __init__(self, id: str, alias: str, name: str, description: str = "", being_type: str = "basic"):
        self.id = id
        self.alias = alias
        self.name = name
        self.description = description
        self.type = being_type
        self.data = {}
        self.created_at = datetime.now()
    
    def to_dict(self):
        return {
            'id': self.id,
            'alias': self.alias,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'data': json.dumps(self.data),
            'created_at': self.created_at.isoformat()
        }

class LuxOSKernel:
    """Główny kernel LuxOS"""
    
    def __init__(self):
        self.db = SimpleDatabase()
        self.beings = {}
        self.status = "offline"
        self.mode = "standalone"
        
    def log(self, level: str, message: str, category: str = "KERNEL"):
        """Prosty system logowania"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        icon = "📡" if category == "KERNEL" else "🤖" if category == "BEINGS" else "💾"
        print(f"{timestamp} {icon} [{level}] {category}: {message}")
    
    async def initialize(self):
        """Inicjalizacja kernela"""
        self.log("INFO", "🚀 Inicjalizacja LuxOS Kernel...")
        
        # Połączenie z bazą
        if await self.db.connect():
            self.status = "online"
            self.log("SUCCESS", "Kernel zainicjalizowany pomyślnie")
            
            # Utworzenie podstawowych bytów
            await self.create_basic_beings()
            
            return True
        else:
            self.status = "error"
            self.log("ERROR", "Błąd inicjalizacji kernela")
            return False
    
    async def create_basic_beings(self):
        """Tworzenie podstawowych bytów"""
        self.log("INFO", "🤖 Tworzenie podstawowych bytów...")
        
        try:
            # BIOS Being
            bios_being = SimpleBeing(
                id=str(uuid.uuid4()),
                alias="bios",
                name="LuxOS BIOS",
                description="System BIOS dla LuxOS",
                being_type="system"
            )
            
            bios_being.data = {
                "bootstrap_sequence": ["init_kernel", "load_communication", "setup_ui", "ready_state"],
                "fallback": {
                    "max_retries": 3,
                    "retry_delay": 5000,
                    "emergency_mode": True
                }
            }
            
            await self.save_being(bios_being)
            self.beings[bios_being.alias] = bios_being
            self.log("SUCCESS", f"BIOS Being utworzony: {bios_being.id}")
            
            # Lux Assistant Being
            assistant_being = SimpleBeing(
                id=str(uuid.uuid4()),
                alias="lux_assistant",
                name="Lux Assistant",
                description="Główny asystent LuxOS",
                being_type="assistant"
            )
            
            assistant_being.data = {
                "capabilities": ["chat", "help", "system_info"],
                "status": "ready"
            }
            
            await self.save_being(assistant_being)
            self.beings[assistant_being.alias] = assistant_being
            self.log("SUCCESS", f"Lux Assistant utworzony: {assistant_being.id}")
            
        except Exception as e:
            self.log("ERROR", f"Błąd tworzenia bytów: {e}")
    
    async def save_being(self, being: SimpleBeing):
        """Zapisanie bytu do bazy"""
        query = """
            INSERT OR REPLACE INTO beings 
            (id, alias, name, description, type, data) 
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            being.id, being.alias, being.name, 
            being.description, being.type, json.dumps(being.data)
        )
        await self.db.execute(query, params)
    
    async def get_status(self) -> Dict[str, Any]:
        """Status systemu"""
        beings_count = len(self.beings)
        
        return {
            "status": self.status,
            "mode": self.mode,
            "beings_count": beings_count,
            "uptime": datetime.now().isoformat(),
            "database": "connected" if self.db.connection else "disconnected"
        }
    
    async def shutdown(self):
        """Wyłączenie systemu"""
        self.log("INFO", "🔄 Wyłączanie LuxOS Kernel...")
        await self.db.close()
        self.status = "offline"
        self.log("INFO", "✅ LuxOS Kernel wyłączony")

class LuxOSWebServer:
    """Prosty serwer HTTP dla LuxOS"""
    
    def __init__(self, kernel: LuxOSKernel, port: int = 5000):
        self.kernel = kernel
        self.port = port
    
    def create_html_interface(self) -> str:
        """Tworzenie prostego interfejsu HTML"""
        return """
<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LuxOS - Main System</title>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: linear-gradient(135deg, #1e3c72, #2a5298);
            color: #fff;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(0,0,0,0.3);
            border-radius: 15px;
            padding: 30px;
            backdrop-filter: blur(10px);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #00ff88;
            font-size: 2.5em;
            margin: 0;
            text-shadow: 0 0 20px #00ff88;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid rgba(0,255,136,0.3);
        }
        .status-card h3 {
            color: #00ff88;
            margin-top: 0;
        }
        .system-info {
            background: rgba(0,0,0,0.2);
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #00ff88;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #aaa;
        }
        .pulse {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌟 LuxOS Main System</h1>
            <p>Standalone Kernel - Simplified Architecture</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>📡 System Status</h3>
                <p>Status: <span class="pulse">🟢 Online</span></p>
                <p>Mode: Standalone</p>
                <p>Kernel: Active</p>
            </div>
            
            <div class="status-card">
                <h3>🤖 Beings</h3>
                <p>Total: 2</p>
                <p>BIOS: ✅ Active</p>
                <p>Assistant: ✅ Ready</p>
            </div>
            
            <div class="status-card">
                <h3>💾 Database</h3>
                <p>Type: SQLite</p>
                <p>Status: ✅ Connected</p>
                <p>Tables: Initialized</p>
            </div>
        </div>
        
        <div class="system-info">
            <h3>🚀 LuxOS Standalone</h3>
            <p>Wszystkie komponenty zostały pomyślnie zarchiwizowane. System działa teraz w trybie standalone z uproszczoną architekturą.</p>
            <p><strong>Aktywne komponenty:</strong></p>
            <ul>
                <li>✅ Kernel główny (main.py)</li>
                <li>✅ Baza danych SQLite</li>
                <li>✅ Podstawowe byty (BIOS, Assistant)</li>
                <li>✅ Interfejs webowy</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>LuxOS © 2025 - Simplified & Clean Architecture</p>
            <p>🗃️ Archive: luxos_archive_20250810_180141/</p>
        </div>
    </div>
    
    <script>
        console.log('🌟 LuxOS Frontend System - Standalone Mode');
        console.log('📦 All legacy components archived successfully');
        console.log('🚀 Running clean main.py only');
        
        // Proste sprawdzenie statusu
        setInterval(() => {
            console.log('💓 LuxOS Heartbeat - System Active');
        }, 30000);
    </script>
</body>
</html>
        """
    
    async def start_server(self):
        """Uruchomienie serwera"""
        try:
            # Używamy prostego serwera HTTP
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import threading
            
            class LuxOSHandler(BaseHTTPRequestHandler):
                def do_GET(self):
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    html = self.server.luxos_server.create_html_interface()
                    self.wfile.write(html.encode())
                
                def log_message(self, format, *args):
                    # Wyłączenie domyślnych logów HTTP
                    pass
            
            httpd = HTTPServer(('0.0.0.0', self.port), LuxOSHandler)
            httpd.luxos_server = self
            
            def run_server():
                httpd.serve_forever()
            
            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()
            
            logger.info(f"🌐 LuxOS Server uruchomiony na porcie {self.port}")
            logger.info(f"🔗 URL: http://0.0.0.0:{self.port}")
            
            return httpd
            
        except Exception as e:
            logger.error(f"❌ Błąd uruchomienia serwera: {e}")
            return None

async def main():
    """Główna funkcja LuxOS"""
    print("🌟 LuxOS Main System - Starting...")
    print("📦 Clean Architecture - Archive Mode")
    
    # Inicjalizacja kernela
    kernel = LuxOSKernel()
    
    if await kernel.initialize():
        # Uruchomienie serwera web
        web_server = LuxOSWebServer(kernel)
        httpd = await web_server.start_server()
        
        if httpd:
            print("\n" + "="*50)
            print("🚀 LuxOS SYSTEM READY")
            print("="*50)
            print(f"🌐 Web Interface: http://0.0.0.0:5000")
            print(f"📊 Status: {kernel.status}")
            print(f"🤖 Beings: {len(kernel.beings)}")
            print(f"🗃️ Archive: luxos_archive_20250810_180141/")
            print("="*50)
            print("Press Ctrl+C to stop")
            
            try:
                # Utrzymanie działania
                while True:
                    await asyncio.sleep(1)
                    
            except KeyboardInterrupt:
                print("\n🔄 Shutting down LuxOS...")
                await kernel.shutdown()
                print("✅ LuxOS stopped cleanly")
        else:
            print("❌ Nie udało się uruchomić serwera web")
            await kernel.shutdown()
    else:
        print("❌ Nie udało się zainicjalizować kernela")

if __name__ == "__main__":
    asyncio.run(main())
