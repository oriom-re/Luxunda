
import asyncio
import json
from datetime import datetime
from dataclasses import asdict
import socketio
from aiohttp import web
import aiohttp_cors
import logging
import os

# Import z app_v2
from app_v2.database.postgre_db import Postgre_db
from app_v2.database.models.base import Soul, Being
from app_v2.services.entity_manager import EntityManager
from app_v2.ai.hybrid_ai_system import HybridAISystem
from app_v2.genetics.decorators import gene

# Setup logger
logger = logging.getLogger(__name__)

# Socket.IO serwer dla demo
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

# System AI i manager
hybrid_ai = HybridAISystem()
entity_manager = EntityManager()

# Globalne zmienne demo
demo_world = {
    'beings': {},
    'connections': {},
    'active_users': 0
}

@sio.event
async def connect(sid, environ, auth):
    print(f"🌟 Demo user connected: {sid}")
    demo_world['active_users'] += 1
    
    # Utwórz demo being dla użytkownika
    user_soul = await entity_manager.create_soul(
        genotype_name="demo_user",
        attributes={
            'session_id': sid,
            'connected_at': datetime.now().isoformat(),
            'user_agent': environ.get('HTTP_USER_AGENT', 'Unknown'),
            'demo_participant': True
        }
    )
    
    demo_world['beings'][sid] = user_soul
    
    # Wyślij aktualny stan świata demo
    await send_demo_world_state(sid)
    
    # Powiadom innych o nowym użytkowniku
    await sio.emit('user_joined', {
        'session_id': sid[:8],
        'active_users': demo_world['active_users']
    }, skip_sid=sid)

@sio.event
async def disconnect(sid):
    print(f"👋 Demo user disconnected: {sid}")
    demo_world['active_users'] = max(0, demo_world['active_users'] - 1)
    
    if sid in demo_world['beings']:
        del demo_world['beings'][sid]
    
    await sio.emit('user_left', {
        'session_id': sid[:8],
        'active_users': demo_world['active_users']
    })

@sio.event
async def create_demo_entity(sid, data):
    """Utwórz nowy byt w świecie demo"""
    try:
        entity_type = data.get('type', 'demo_entity')
        name = data.get('name', f'Entity_{datetime.now().strftime("%H%M%S")}')
        
        # Użyj app_v2 EntityManager
        soul = await entity_manager.create_soul(
            genotype_name=entity_type,
            attributes={
                'name': name,
                'created_by': sid,
                'demo_entity': True,
                'properties': data.get('properties', {}),
                'visual': {
                    'color': data.get('color', '#00ff88'),
                    'size': data.get('size', 10),
                    'position': data.get('position', {'x': 0, 'y': 0})
                }
            }
        )
        
        # Dodaj do demo world
        demo_world['beings'][soul.soul_uid] = soul
        
        await sio.emit('entity_created', {
            'soul': soul.soul_uid,
            'name': name,
            'type': entity_type,
            'creator': sid[:8],
            'visual': soul.attributes.get('visual', {})
        })
        
        await broadcast_world_update()
        
    except Exception as e:
        await sio.emit('error', {'message': f'Błąd tworzenia bytu: {str(e)}'}, room=sid)

@sio.event
async def ai_interaction(sid, data):
    """Interakcja z systemem AI"""
    try:
        user_message = data.get('message', '')
        
        # Użyj HybridAISystem z app_v2
        response = await hybrid_ai.process_request(
            user_message, 
            context={'session_id': sid, 'demo_mode': True}
        )
        
        await sio.emit('ai_response', {
            'message': response.get('final_result', 'Brak odpowiedzi'),
            'method': response.get('method_used', 'unknown'),
            'session_id': sid[:8]
        }, room=sid)
        
    except Exception as e:
        await sio.emit('error', {'message': f'Błąd AI: {str(e)}'}, room=sid)

@sio.event
async def manage_demo_tables(sid, data):
    """Zarządzanie tabelami w demo"""
    try:
        action = data.get('action')  # 'create', 'drop', 'list'
        table_name = data.get('table_name')
        
        db = Postgre_db()
        
        if action == 'create' and table_name:
            # Utwórz prostą tabelę demo
            query = f"""
            CREATE TABLE IF NOT EXISTS demo_{table_name} (
                id SERIAL PRIMARY KEY,
                data JSONB,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            await db.execute_query(query)
            
            await sio.emit('table_created', {
                'table_name': f'demo_{table_name}',
                'creator': sid[:8]
            })
            
        elif action == 'list':
            # Lista tabel demo
            tables = await db.get_demo_tables()
            await sio.emit('tables_list', {'tables': tables}, room=sid)
        
        await broadcast_world_update()
        
    except Exception as e:
        await sio.emit('error', {'message': f'Błąd zarządzania tabelami: {str(e)}'}, room=sid)

@sio.event
async def execute_demo_command(sid, data):
    """Wykonaj komendę w świecie demo"""
    try:
        command = data.get('command', '')
        args = data.get('args', [])
        
        result = await process_demo_command(command, args, sid)
        
        await sio.emit('command_result', {
            'command': command,
            'result': result,
            'executor': sid[:8]
        }, room=sid)
        
        # Broadcastuj zmianę do wszystkich
        await broadcast_world_update()
        
    except Exception as e:
        await sio.emit('error', {'message': f'Błąd komendy: {str(e)}'}, room=sid)

async def process_demo_command(command, args, session_id):
    """Przetwórz komendy demo"""
    if command == 'spawn':
        # Stwórz nowy byt
        entity_type = args[0] if args else 'basic'
        soul = await entity_manager.create_soul(
            genotype_name=entity_type,
            attributes={
                'spawned_by': session_id,
                'command_created': True
            }
        )
        return f"Utworzono byt: {soul.soul_uid}"
        
    elif command == 'connect':
        # Połącz byty
        if len(args) >= 2:
            source, target = args[0], args[1]
            # Logika łączenia bytów
            return f"Połączono {source} z {target}"
            
    elif command == 'list':
        # Lista bytów w świecie
        beings_list = [
            f"{soul_id[:8]}..." for soul_id in demo_world['beings'].keys()
        ]
        return f"Byty w świecie: {', '.join(beings_list)}"
        
    return f"Nieznana komenda: {command}"

async def send_demo_world_state(sid):
    """Wyślij aktualny stan świata demo"""
    world_state = {
        'beings': len(demo_world['beings']),
        'active_users': demo_world['active_users'],
        'connections': len(demo_world['connections']),
        'timestamp': datetime.now().isoformat()
    }
    
    await sio.emit('world_state', world_state, room=sid)

async def broadcast_world_update():
    """Rozgłoś aktualizację świata do wszystkich użytkowników"""
    world_state = {
        'beings': len(demo_world['beings']),
        'active_users': demo_world['active_users'],
        'connections': len(demo_world['connections']),
        'timestamp': datetime.now().isoformat()
    }
    
    await sio.emit('world_updated', world_state)

# HTTP Routes
async def serve_demo_landing(request):
    return web.FileResponse('static/funding-landing.html')

async def serve_support_form(request):
    return web.FileResponse('static/support-form.html')

async def serve_github_info(request):
    return web.FileResponse('static/github-info.html')

async def api_demo_status(request):
    """API endpoint dla statusu demo"""
    status = {
        'active_users': demo_world['active_users'],
        'beings_count': len(demo_world['beings']),
        'connections_count': len(demo_world['connections']),
        'uptime': datetime.now().isoformat(),
        'app_v2_status': 'active'
    }
    return web.json_response(status)

async def init_demo_app():
    """Inicjalizacja aplikacji demo"""
    
    # HTTP routes
    app.router.add_get('/', serve_demo_landing)
    app.router.add_get('/funding', serve_demo_landing)
    app.router.add_get('/support', serve_support_form)
    app.router.add_get('/github', serve_github_info)
    app.router.add_get('/api/status', api_demo_status)
    
    # Serwowanie plików statycznych
    app.router.add_static('/static', 'static', name='static')
    
    # CORS
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    
    # Dodaj CORS do API
    for route in list(app.router.routes()):
        if hasattr(route, 'resource') and route.resource.canonical.startswith('/api/'):
            cors.add(route)

async def main():
    print("🚀 Uruchamianie LuxOS Demo Landing (app_v2)...")
    
    # Inicjalizacja app_v2 komponentów
    await hybrid_ai.initialize()
    await entity_manager.initialize()
    
    # Inicjalizacja aplikacji
    await init_demo_app()
    
    # Start serwera
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 3000)
    await site.start()
    
    print("✨ Demo Landing uruchomiony na http://0.0.0.0:3000")
    print("📊 Wykorzystuje architekturę app_v2")
    print("🌍 Świat demo gotowy do współdzielenia przez użytkowników")
    
    # Trzymaj serwer żywy
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    asyncio.run(main())
