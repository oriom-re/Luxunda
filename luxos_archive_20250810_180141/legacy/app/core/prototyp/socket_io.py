# soul: app/gens/gen_socketio.py

import socketio
import asyncio

sio = socketio.AsyncServer(async_mode='asgi')
app = socketio.ASGIApp(sio)

# Dynamiczna rejestracja eventów
event_handlers = {}

def register_event(event_name: str, handler):
    """Rejestruje handler do eventu."""
    event_handlers[event_name] = handler

@sio.event
async def connect(sid, environ):
    print(f"🔌 [SocketIO] Połączono: {sid}")

@sio.event
async def disconnect(sid):
    print(f"❌ [SocketIO] Rozłączono: {sid}")


@sio.on("*")  # przechwytuje wszystkie eventy
async def handle_any_event(sid, data):
    event_name = data.get("event")
    payload = data.get("payload")

    if event_name in event_handlers:
        response = await maybe_async(event_handlers[event_name](sid, payload))
    else:
        response = {"error": f"Nieznane zdarzenie: {event_name}"}

    await sio.emit("response", response, to=sid)

async def maybe_async(func):
    return await func if asyncio.iscoroutine(func) else func

async def init():
    print("⚡ [gen_socketio] SocketIO aktywne na porcie 8765")

def get_app():
    return app

def get_socket():
    return sio

def use(event_name: str, handler):
    register_event(event_name, handler)
