
"""
LuxOS Simple System - Jeden system zamiast wielu warstw
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

class SimpleLuxOS:
    """Jeden prosty system - bez nadmiernych warstw"""
    
    def __init__(self):
        self.app = FastAPI(title="Simple LuxOS")
        self.db_pool = None
        self.beings_cache = {}
        self.souls_cache = {}
        self.status = {
            "mode": "simple",
            "started_at": datetime.now().isoformat(),
            "beings_count": 0,
            "souls_count": 0
        }
        self._setup_routes()
    
    def _setup_routes(self):
        """Proste trasy - bez skomplikowanych warstw"""
        
        # Statyczne pliki
        self.app.mount("/static", StaticFiles(directory="static"), name="static")
        
        # Główna strona
        @self.app.get("/")
        async def index():
            return HTMLResponse("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Simple LuxOS</title>
                <style>
                    body { 
                        font-family: Arial; 
                        padding: 20px; 
                        max-width: 800px; 
                        margin: 0 auto; 
                    }
                    .status { 
                        background: #f0f8ff; 
                        padding: 15px; 
                        border-radius: 5px; 
                        margin: 20px 0; 
                    }
                    .count { 
                        font-size: 24px; 
                        font-weight: bold; 
                        color: #2196F3; 
                    }
                </style>
            </head>
            <body>
                <h1>🌟 Simple LuxOS</h1>
                <p>Prosty system bez zbędnych warstw zarządzania</p>
                
                <div class="status">
                    <h3>Status systemu:</h3>
                    <p>✅ System aktywny</p>
                    <p>✅ Baza PostgreSQL połączona</p>
                    <p>✅ Tryb: <span class="count">Simple</span></p>
                    
                    <h3>Statystyki:</h3>
                    <p>Byty: <span class="count" id="beings">-</span></p>
                    <p>Dusze: <span class="count" id="souls">-</span></p>
                </div>
                
                <h3>API:</h3>
                <ul>
                    <li><a href="/api/status">Status systemu</a></li>
                    <li><a href="/api/beings">Lista bytów</a></li>
                    <li><a href="/api/souls">Lista dusz</a></li>
                </ul>
                
                <script>
                    async function updateStats() {
                        try {
                            const response = await fetch('/api/status');
                            const data = await response.json();
                            document.getElementById('beings').textContent = data.beings_count || 0;
                            document.getElementById('souls').textContent = data.souls_count || 0;
                        } catch (e) {
                            console.error('Błąd pobierania stats:', e);
                        }
                    }
                    
                    updateStats();
                    setInterval(updateStats, 5000);
                </script>
            </body>
            </html>
            """)
        
        # API - proste endpointy
        @self.app.get("/api/status")
        async def get_status():
            await self._update_counts()
            return JSONResponse(self.status)
        
        @self.app.get("/api/beings")
        async def get_beings():
            if not self.db_pool:
                return JSONResponse({"error": "Database not connected"}, status_code=500)
            
            try:
                async with self.db_pool.acquire() as conn:
                    # Proste zapytanie - bez skomplikowanych warstw
                    rows = await conn.fetch("SELECT ulid, alias, created_at FROM beings LIMIT 50")
                    beings = [dict(row) for row in rows]
                    return JSONResponse({"beings": beings, "count": len(beings)})
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.app.get("/api/souls")
        async def get_souls():
            if not self.db_pool:
                return JSONResponse({"error": "Database not connected"}, status_code=500)
            
            try:
                async with self.db_pool.acquire() as conn:
                    # Proste zapytanie - bez skomplikowanych warstw
                    rows = await conn.fetch("SELECT soul_hash, alias, created_at FROM souls LIMIT 50")
                    souls = [dict(row) for row in rows]
                    return JSONResponse({"souls": souls, "count": len(souls)})
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)
        
        @self.app.post("/api/beings/create")
        async def create_being(data: Dict[str, Any]):
            """Proste tworzenie bytu - bez skomplikowanych managerów"""
            if not self.db_pool:
                raise HTTPException(status_code=500, detail="Database not connected")
            
            try:
                alias = data.get("alias", "simple_being")
                being_data = data.get("data", {})
                
                async with self.db_pool.acquire() as conn:
                    # Proste INSERT - bez warstw abstrakcji
                    ulid = f"being_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    await conn.execute("""
                        INSERT INTO beings (ulid, alias, data, created_at, updated_at)
                        VALUES ($1, $2, $3, NOW(), NOW())
                    """, ulid, alias, json.dumps(being_data))
                    
                return JSONResponse({"success": True, "ulid": ulid, "alias": alias})
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
    
    async def start_database(self):
        """Proste połączenie z bazą - bez warstw abstrakcji"""
        try:
            # Prosta konfiguracja - bez deployment managera
            db_config = {
                'host': 'localhost',
                'port': 5432,
                'database': 'luxdb_dev',
                'user': 'postgres',
                'password': 'password'
            }
            
            self.db_pool = await asyncpg.create_pool(**db_config, min_size=2, max_size=10)
            
            # Upewnij się że tabele istnieją - prosta wersja
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS beings (
                        ulid VARCHAR(50) PRIMARY KEY,
                        alias VARCHAR(255),
                        soul_hash VARCHAR(255),
                        data JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS souls (
                        soul_hash VARCHAR(255) PRIMARY KEY,
                        alias VARCHAR(255),
                        genotype JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
            
            print("✅ Simple Database: Połączono z PostgreSQL")
            await self._update_counts()
            
        except Exception as e:
            print(f"❌ Database Error: {e}")
            self.db_pool = None
    
    async def _update_counts(self):
        """Aktualizuj liczniki - prosto"""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.acquire() as conn:
                beings_count = await conn.fetchval("SELECT COUNT(*) FROM beings")
                souls_count = await conn.fetchval("SELECT COUNT(*) FROM souls")
                
                self.status.update({
                    "beings_count": beings_count or 0,
                    "souls_count": souls_count or 0,
                    "database": "connected",
                    "last_update": datetime.now().isoformat()
                })
        except Exception as e:
            print(f"⚠️ Count update error: {e}")
            self.status.update({
                "database": "error",
                "last_error": str(e)
            })
    
    async def start_server(self, port: int = 5000):
        """Uruchom serwer - bez skomplikowanych workflow"""
        print(f"🚀 Starting Simple LuxOS on port {port}")
        
        # Połącz z bazą
        await self.start_database()
        
        # Uruchom serwer
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=port,
            log_level="info"
        )
        
        server = uvicorn.Server(config)
        await server.serve()

# Funkcja do uruchamiania
async def main():
    """Główna funkcja - prosta i jasna"""
    simple_luxos = SimpleLuxOS()
    await simple_luxos.start_server(port=5000)

if __name__ == "__main__":
    asyncio.run(main())
