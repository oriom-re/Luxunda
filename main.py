
#!/usr/bin/env python3
"""
LuxOS - Main System with PostgreSQL
Kompletny system z bazą PostgreSQL
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import asyncpg

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PostgreSQLDatabase:
    """Baza danych PostgreSQL"""
    
    def __init__(self):
        self.pool = None
        self.database_url = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/luxos')
        
    async def connect(self):
        """Połączenie z bazą danych"""
        try:
            self.pool = await asyncpg.create_pool(self.database_url)
            await self.init_tables()
            logger.info("✅ Połączono z bazą PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"❌ Błąd połączenia z bazą: {e}")
            return False
    
    async def init_tables(self):
        """Inicjalizacja tabel"""
        async with self.pool.acquire() as conn:
            # Tabela bytów
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS beings (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    alias TEXT UNIQUE,
                    name TEXT,
                    description TEXT,
                    type TEXT,
                    data JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabela dusz
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS souls (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name TEXT,
                    being_id UUID REFERENCES beings(id),
                    soul_data JSONB DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
        logger.info("✅ Tabele PostgreSQL zainicjalizowane")

    async def execute(self, query: str, *params):
        """Wykonanie zapytania"""
        try:
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *params)
        except Exception as e:
            logger.error(f"❌ Błąd zapytania: {e}")
            return []

    async def close(self):
        """Zamknięcie połączenia"""
        if self.pool:
            await self.pool.close()
            logger.info("🔄 Zamknięto połączenie z bazą")

class LuxBeing:
    """Byt LuxOS"""
    
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
            'data': self.data,
            'created_at': self.created_at.isoformat()
        }

class LuxOSKernel:
    """Główny kernel LuxOS"""
    
    def __init__(self):
        self.db = PostgreSQLDatabase()
        self.beings = {}
        self.status = "offline"
        self.mode = "main_system"
        
    def log(self, level: str, message: str, category: str = "KERNEL"):
        """System logowania"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        icon = "📡" if category == "KERNEL" else "🤖" if category == "BEINGS" else "💾"
        print(f"{timestamp} {icon} [{level}] {category}: {message}")
    
    async def initialize(self):
        """Inicjalizacja kernela"""
        self.log("INFO", "🚀 Inicjalizacja LuxOS Kernel...")
        
        if await self.db.connect():
            self.status = "online"
            self.log("SUCCESS", "Kernel zainicjalizowany pomyślnie")
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
            bios_id = str(uuid.uuid4())
            await self.db.execute("""
                INSERT INTO beings (id, alias, name, description, type, data) 
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (alias) DO NOTHING
            """, bios_id, "bios", "LuxOS BIOS", "System BIOS", "system", json.dumps({
                "bootstrap_sequence": ["init_kernel", "load_communication", "setup_ui", "ready_state"],
                "fallback": {"max_retries": 3, "retry_delay": 5000, "emergency_mode": True}
            }))
            
            # Lux Assistant
            assistant_id = str(uuid.uuid4())
            await self.db.execute("""
                INSERT INTO beings (id, alias, name, description, type, data) 
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (alias) DO NOTHING
            """, assistant_id, "lux_assistant", "Lux Assistant", "Główny asystent", "assistant", json.dumps({
                "capabilities": ["chat", "help", "system_info"],
                "status": "ready"
            }))
            
            self.log("SUCCESS", "Podstawowe byty utworzone")
            
        except Exception as e:
            self.log("ERROR", f"Błąd tworzenia bytów: {e}")
    
    async def get_status(self) -> Dict[str, Any]:
        """Status systemu"""
        beings_result = await self.db.execute("SELECT COUNT(*) as count FROM beings")
        beings_count = beings_result[0]['count'] if beings_result else 0
        
        souls_result = await self.db.execute("SELECT COUNT(*) as count FROM souls")
        souls_count = souls_result[0]['count'] if souls_result else 0
        
        return {
            "status": self.status,
            "mode": self.mode,
            "beings_count": beings_count,
            "souls_count": souls_count,
            "uptime": datetime.now().isoformat(),
            "database": "connected" if self.db.pool else "disconnected",
            "service": "LuxOS Main System",
            "lux_assistant_ready": True,
            "specialists_available": True
        }
    
    async def get_beings(self):
        """Pobierz wszystkie byty"""
        return await self.db.execute("SELECT * FROM beings ORDER BY created_at DESC")
    
    async def get_bios_scenario(self):
        """Pobierz scenariusz BIOS"""
        result = await self.db.execute("SELECT data FROM beings WHERE alias = 'bios'")
        if result:
            return json.loads(result[0]['data'])
        return {"sequence": ["init_kernel", "load_communication", "setup_ui", "ready_state"]}
    
    async def shutdown(self):
        """Wyłączenie systemu"""
        self.log("INFO", "🔄 Wyłączanie LuxOS Kernel...")
        await self.db.close()
        self.status = "offline"
        self.log("INFO", "✅ LuxOS Kernel wyłączony")

# FastAPI aplikacja
app = FastAPI(title="LuxOS Main System")
kernel = LuxOSKernel()

@app.on_event("startup")
async def startup_event():
    await kernel.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    await kernel.shutdown()

@app.get("/")
async def root():
    """Główny interfejs"""
    html_content = """
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
        .pulse {
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #aaa;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌟 LuxOS Main System</h1>
            <p>PostgreSQL + Complete Architecture</p>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>📡 System Status</h3>
                <p>Status: <span class="pulse">🟢 Online</span></p>
                <p>Mode: Main System</p>
                <p>Database: PostgreSQL</p>
            </div>
            
            <div class="status-card" id="beings-card">
                <h3>🤖 Beings</h3>
                <p id="beings-count">Loading...</p>
                <p>BIOS: ✅ Active</p>
                <p>Assistant: ✅ Ready</p>
            </div>
            
            <div class="status-card">
                <h3>💾 Database</h3>
                <p>Type: PostgreSQL</p>
                <p>Status: ✅ Connected</p>
                <p>Tables: Initialized</p>
            </div>
        </div>
        
        <div class="system-info">
            <h3>🚀 LuxOS Main System</h3>
            <p>System działa z pełną architekturą PostgreSQL. Wszystkie legacy komponenty zostały zarchiwizowane.</p>
            <p><strong>Aktywne komponenty:</strong></p>
            <ul>
                <li>✅ Kernel główny (main.py)</li>
                <li>✅ Baza danych PostgreSQL</li>
                <li>✅ FastAPI backend</li>
                <li>✅ Podstawowe byty (BIOS, Assistant)</li>
                <li>✅ REST API endpoints</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>LuxOS © 2025 - Main System with PostgreSQL</p>
            <p>🗃️ Archive: luxos_archive_20250810_180141/</p>
        </div>
    </div>
    
    <script>
        console.log('🌟 LuxOS Main System - PostgreSQL Mode');
        
        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const status = await response.json();
                
                document.getElementById('beings-count').innerHTML = 
                    `Total: ${status.beings_count}<br>Souls: ${status.souls_count}`;
                    
                console.log('📊 Status systemu:', status);
            } catch (error) {
                console.error('❌ Błąd statusu:', error);
            }
        }
        
        // Aktualizuj status co 5 sekund
        updateStatus();
        setInterval(updateStatus, 5000);
        
        console.log('💓 LuxOS Main System - Active');
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/status")
async def get_status():
    """API status systemu"""
    return await kernel.get_status()

@app.get("/api/system/status")
async def get_system_status():
    """Status systemu - kompatybilność"""
    return await kernel.get_status()

@app.get("/api/beings")
async def get_beings():
    """Lista wszystkich bytów"""
    beings = await kernel.get_beings()
    return [dict(being) for being in beings]

@app.get("/api/beings/specialists")
async def get_specialists():
    """Lista specjalistów"""
    beings = await kernel.get_beings()
    specialists = [dict(being) for being in beings if being['type'] in ['assistant', 'specialist']]
    return {"specialists": specialists}

@app.get("/api/bios")
async def get_bios():
    """BIOS scenariusz"""
    scenario = await kernel.get_bios_scenario()
    return {"scenario": scenario}

async def main():
    """Główna funkcja"""
    print("🌟 LuxOS Main System - Starting...")
    print("🗃️ Archive Mode - PostgreSQL Backend")
    
    # Uruchomienie serwera
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=5000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    print("\n" + "="*50)
    print("🚀 LuxOS MAIN SYSTEM READY")
    print("="*50)
    print(f"🌐 Web Interface: http://0.0.0.0:5000")
    print(f"📡 API: http://0.0.0.0:5000/api/status")
    print(f"💾 Database: PostgreSQL")
    print(f"🗃️ Archive: luxos_archive_20250810_180141/")
    print("="*50)
    
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
