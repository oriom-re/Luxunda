
#!/usr/bin/env python3
"""
🚀 LuxDB Development Landing Server
Enhanced with reactive system and proper lifespan management
"""

import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
import uvicorn

from luxdb import LuxDB

# Globalne zmienne dla zarządzania aplikacją
app_state = {
    'luxdb': None,
    'connections': set(),
    'beings_count': 0,
    'active_users': 0,
    'stats': {
        'beings': 0,
        'tables': 0,
        'connections': 0,
        'commands': 0
    },
    'reactive_components': {},
    'page_state': {
        'current_beings': [],
        'selected_nodes': [],
        'graph_data': {'beings': [], 'relationships': []},
        'ui_state': {'zoom': 1.0, 'pan': {'x': 0, 'y': 0}}
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Proper lifespan management for FastAPI"""
    print("🚀 Starting LuxDB Development Mode...")
    print("=" * 60)
    print(f"🌍 Host: 0.0.0.0:3001")
    print(f"🔧 Debug: True")
    print(f"📁 Workspace: True")
    print(f"🤖 Discord: True")
    print("=" * 60)
    
    try:
        # Initialize LuxDB
        luxdb = LuxDB()
        await luxdb.connect()
        app_state['luxdb'] = luxdb
        
        # Load initial data
        await load_initial_data()
        
        print("✅ LuxDB System initialized successfully")
        
        yield
        
    except Exception as e:
        print(f"❌ Startup error: {e}")
        yield
        
    finally:
        # Cleanup
        print("🔄 Shutting down LuxDB System...")
        if app_state['luxdb']:
            await app_state['luxdb'].disconnect()
        print("✅ Shutdown complete")

# Create FastAPI app with lifespan
app = FastAPI(
    title="LuxDB Development Server",
    description="Reactive development server for LuxDB system",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="static")

async def load_initial_data():
    """Load initial data and update reactive state"""
    try:
        if app_state['luxdb']:
            # Create some demo beings
            demo_beings = []
            for i in range(15):
                being_id = f"demo_being_{i:03d}"
                being = await app_state['luxdb'].create_being(
                    'sample_entity',
                    attributes={
                        'name': f'Demo Entity {i}',
                        'type': 'entity',
                        'demo_id': i
                    },
                    ulid=being_id
                )
                demo_beings.append(being)
            
            app_state['page_state']['current_beings'] = demo_beings
            app_state['stats']['beings'] = len(demo_beings)
            app_state['stats']['tables'] = 3  # souls, beings, relationships
            
            # Update graph data
            app_state['page_state']['graph_data']['beings'] = [
                {
                    'id': being.ulid,
                    'name': being.attributes.get('name', 'Unknown'),
                    'type': 'entity',
                    'data': being.attributes,
                    'x': 100 + (i % 5) * 150,
                    'y': 150 + (i // 5) * 120
                }
                for i, being in enumerate(demo_beings)
            ]
            
            print(f"📊 Loaded {len(demo_beings)} demo beings")
            
    except Exception as e:
        print(f"❌ Error loading initial data: {e}")

async def broadcast_state_update(data: Dict[str, Any]):
    """Broadcast state updates to all connected clients"""
    if app_state['connections']:
        message = json.dumps(data)
        disconnected = set()
        
        for websocket in app_state['connections'].copy():
            try:
                await websocket.send_text(message)
            except:
                disconnected.add(websocket)
        
        # Clean up disconnected clients
        app_state['connections'] -= disconnected
        app_state['stats']['connections'] = len(app_state['connections'])

async def update_reactive_component(component_id: str, data: Any):
    """Update specific reactive component and broadcast"""
    app_state['reactive_components'][component_id] = data
    await broadcast_state_update({
        'type': 'component_update',
        'component_id': component_id,
        'data': data,
        'timestamp': datetime.now().isoformat()
    })

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Serve the main landing page"""
    return templates.TemplateResponse("funding-landing.html", {"request": request})

@app.get("/graph", response_class=HTMLResponse)
async def graph_page(request: Request):
    """Serve the reactive graph page"""
    return templates.TemplateResponse("graph.html", {"request": request})

@app.get("/api/stats")
async def get_stats():
    """Get current system statistics"""
    return JSONResponse({
        'stats': app_state['stats'],
        'timestamp': datetime.now().isoformat(),
        'active_users': app_state['active_users'],
        'page_state': app_state['page_state']
    })

@app.get("/api/beings")
async def get_beings():
    """Get all beings data"""
    beings_data = []
    if app_state['luxdb']:
        try:
            # Get fresh data from database
            beings = await app_state['luxdb'].get_all_beings()
            beings_data = [
                {
                    'id': being.ulid,
                    'name': being.attributes.get('name', 'Unknown'),
                    'type': 'entity',
                    'data': being.attributes,
                    'soul': being.soul_alias if hasattr(being, 'soul_alias') else 'sample_entity'
                }
                for being in beings
            ]
            
            # Update cached state
            app_state['page_state']['current_beings'] = beings
            app_state['stats']['beings'] = len(beings)
            
        except Exception as e:
            print(f"❌ Error fetching beings: {e}")
    
    return JSONResponse({'beings': beings_data})

@app.get("/api/graph-data")
async def get_graph_data():
    """Get graph data for visualization"""
    return JSONResponse({
        'beings': app_state['page_state']['graph_data']['beings'],
        'relationships': app_state['page_state']['graph_data']['relationships']
    })

@app.post("/api/create-being")
async def create_being_endpoint(request: Request):
    """Create a new being via API"""
    try:
        data = await request.json()
        name = data.get('name', 'New Being')
        being_type = data.get('type', 'entity')
        
        if app_state['luxdb']:
            being = await app_state['luxdb'].create_being(
                'sample_entity',
                attributes={
                    'name': name,
                    'type': being_type,
                    'created_via': 'api',
                    'created_at': datetime.now().isoformat()
                }
            )
            
            # Update reactive state
            new_being_data = {
                'id': being.ulid,
                'name': name,
                'type': being_type,
                'data': being.attributes,
                'x': 100 + len(app_state['page_state']['current_beings']) * 50,
                'y': 150
            }
            
            app_state['page_state']['graph_data']['beings'].append(new_being_data)
            app_state['stats']['beings'] += 1
            app_state['stats']['commands'] += 1
            
            # Broadcast update
            await broadcast_state_update({
                'type': 'being_created',
                'being': new_being_data,
                'stats': app_state['stats']
            })
            
            return JSONResponse({'success': True, 'being': new_being_data})
            
    except Exception as e:
        print(f"❌ Error creating being: {e}")
        return JSONResponse({'success': False, 'error': str(e)})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for reactive updates"""
    await websocket.accept()
    app_state['connections'].add(websocket)
    app_state['active_users'] += 1
    app_state['stats']['connections'] = len(app_state['connections'])
    
    print(f"👤 New connection. Active users: {app_state['active_users']}")
    
    try:
        # Send initial state
        await websocket.send_text(json.dumps({
            'type': 'initial_state',
            'stats': app_state['stats'],
            'page_state': app_state['page_state'],
            'reactive_components': app_state['reactive_components']
        }))
        
        # Broadcast user count update
        await broadcast_state_update({
            'type': 'user_count_update',
            'active_users': app_state['active_users'],
            'connections': len(app_state['connections'])
        })
        
        while True:
            # Handle incoming messages
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message['type'] == 'request_graph_data':
                await websocket.send_text(json.dumps({
                    'type': 'graph_data',
                    'beings': app_state['page_state']['graph_data']['beings'],
                    'relationships': app_state['page_state']['graph_data']['relationships']
                }))
            
            elif message['type'] == 'create_being':
                # Handle being creation via WebSocket
                name = message.get('name', f'Being_{datetime.now().strftime("%H%M%S")}')
                await create_being_via_websocket(name, websocket)
            
            elif message['type'] == 'update_ui_state':
                # Update UI state reactively
                app_state['page_state']['ui_state'].update(message.get('ui_state', {}))
                await broadcast_state_update({
                    'type': 'ui_state_update',
                    'ui_state': app_state['page_state']['ui_state']
                })
            
            elif message['type'] == 'ping':
                await websocket.send_text(json.dumps({'type': 'pong'}))
                
    except WebSocketDisconnect:
        print("👤 User disconnected")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
    finally:
        app_state['connections'].discard(websocket)
        app_state['active_users'] = max(0, app_state['active_users'] - 1)
        app_state['stats']['connections'] = len(app_state['connections'])
        
        # Broadcast user count update
        if app_state['connections']:
            await broadcast_state_update({
                'type': 'user_count_update',
                'active_users': app_state['active_users'],
                'connections': len(app_state['connections'])
            })

async def create_being_via_websocket(name: str, websocket: WebSocket):
    """Create being via WebSocket and broadcast update"""
    try:
        if app_state['luxdb']:
            being = await app_state['luxdb'].create_being(
                'sample_entity',
                attributes={
                    'name': name,
                    'type': 'entity',
                    'created_via': 'websocket',
                    'created_at': datetime.now().isoformat()
                }
            )
            
            new_being_data = {
                'id': being.ulid,
                'name': name,
                'type': 'entity',
                'data': being.attributes,
                'x': 100 + len(app_state['page_state']['current_beings']) * 50,
                'y': 150 + (len(app_state['page_state']['current_beings']) // 5) * 120
            }
            
            app_state['page_state']['graph_data']['beings'].append(new_being_data)
            app_state['stats']['beings'] += 1
            app_state['stats']['commands'] += 1
            
            # Broadcast to all clients
            await broadcast_state_update({
                'type': 'being_created',
                'being': new_being_data,
                'stats': app_state['stats']
            })
            
    except Exception as e:
        await websocket.send_text(json.dumps({
            'type': 'error',
            'message': f'Error creating being: {str(e)}'
        }))

@app.get("/test-data")
async def generate_test_data():
    """Generate test data for development"""
    try:
        if app_state['luxdb']:
            # Add a few more beings for testing
            test_beings = []
            for i in range(5):
                being = await app_state['luxdb'].create_being(
                    'sample_entity',
                    attributes={
                        'name': f'Test Being {i}',
                        'type': 'test_entity',
                        'test_data': True
                    }
                )
                test_beings.append({
                    'id': being.ulid,
                    'name': f'Test Being {i}',
                    'type': 'test_entity',
                    'data': being.attributes
                })
            
            app_state['stats']['beings'] += len(test_beings)
            app_state['stats']['commands'] += 1
            
            # Broadcast update
            await broadcast_state_update({
                'type': 'test_data_created',
                'beings': test_beings,
                'stats': app_state['stats']
            })
            
            return JSONResponse({
                'success': True,
                'message': f'Created {len(test_beings)} test beings',
                'beings': test_beings
            })
    except Exception as e:
        return JSONResponse({
            'success': False,
            'error': str(e)
        })

if __name__ == "__main__":
    print("📁 Workspace synchronization enabled")
    uvicorn.run(
        "demo_landing:app",
        host="0.0.0.0",
        port=3001,
        reload=False,  # Disable reload for better lifespan handling
        log_level="info"
    )
