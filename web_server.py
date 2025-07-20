
#!/usr/bin/env python3
"""
LuxOS Web Server - Serwer webowy interfejsu użytkownika
"""

import asyncio
import socketio
from aiohttp import web, ClientSession
import aiohttp_cors
import json
import logging
from datetime import datetime

from app.utils.fingerprint import FingerprintManager

logger = logging.getLogger(__name__)

# Socket.IO serwer
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

class LuxOSWebServer:
    """Serwer webowy dla interfejsu LuxOS"""
    
    def __init__(self, kernel_host="localhost", kernel_port=8001):
        self.kernel_host = kernel_host
        self.kernel_port = kernel_port
        self.fingerprint_manager = FingerprintManager()
        self.active_connections = {}  # connection_id -> user_info
    
    async def start_server(self, port=8000):
        """Uruchamia serwer webowy"""
        await self.setup_routes()
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"🌐 LuxOS Web Server uruchomiony na porcie {port}")
        logger.info(f"🔗 Połączenie z Kernel: {self.kernel_host}:{self.kernel_port}")
        
        return runner
    
    async def setup_routes(self):
        """Konfiguruje trasy HTTP"""
        # Główna strona
        async def serve_landing(request):
            return web.FileResponse('static/landing.html')
        
        # Graf bytów
        async def serve_index(request):
            return web.FileResponse('static/index.html')
        
        app.router.add_get('/', serve_landing)
        app.router.add_get('/index.html', serve_index)
        
        # Pliki statyczne
        app.router.add_static('/', 'static', name='static')
        
        # CORS
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        for route in list(app.router.routes()):
            cors.add(route)

# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth=None):
    """Obsługuje połączenie klienta"""
    logger.info(f"🔌 Klient połączony: {sid}")
    
    # Generuj fingerprint (testowy)
    fingerprint = FingerprintManager.generate_test_fingerprint()
    
    # Zarejestruj połączenie
    # Tu będzie komunikacja z kernelem o nowym połączeniu
    
    # Wyślij powitalną wiadomość
    await sio.emit('connection_established', {
        'message': 'Połączono z LuxOS',
        'fingerprint': fingerprint[:8] + '...',
        'timestamp': datetime.now().isoformat()
    }, room=sid)

@sio.event
async def disconnect(sid):
    """Obsługuje rozłączenie klienta"""
    logger.info(f"🔌 Klient rozłączony: {sid}")
    
    # Wyrejestruj połączenie
    # Tu będzie komunikacja z kernelem o rozłączeniu

@sio.event
async def lux_communication(sid, data):
    """Obsługuje komunikację z Lux"""
    logger.info(f"💬 Wiadomość od {sid}: {data.get('message', '')[:50]}...")
    
    # Tu będzie przekazanie wiadomości do kernela
    response = {
        'success': True,
        'lux_response': 'Kernel jest w trakcie inicjalizacji. Wkrótce będę mógł z Tobą rozmawiać! 🤖',
        'timestamp': datetime.now().isoformat()
    }
    
    await sio.emit('lux_conversation_response', response, room=sid)

@sio.event
async def get_graph_data(sid, data=None):
    """Zwraca dane grafu"""
    # Placeholder - dane będą pobierane z kernela
    graph_data = {
        'nodes': [
            {
                'soul': '00000000-0000-0000-0000-000000000001',
                'genesis': {
                    'type': 'kernel_agent',
                    'name': 'LuxOS Kernel',
                    'description': 'Główny kernel systemu'
                },
                'attributes': {
                    'energy_level': 10000,
                    'tags': ['kernel', 'system']
                },
                'x': 0,
                'y': 0
            }
        ],
        'links': []
    }
    
    await sio.emit('graph_data', graph_data, room=sid)

async def main():
    """Główna funkcja serwera web"""
    logger.info("🌐 Uruchamianie LuxOS Web Server...")
    
    server = LuxOSWebServer()
    runner = await server.start_server(port=8000)
    
    logger.info("✅ Serwer uruchomiony na http://0.0.0.0:8000")
    
    try:
        # Trzymaj serwer żywy
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("⚠️ Zamykanie serwera...")
    finally:
        await runner.cleanup()
        logger.info("✅ Serwer zamknięty")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
