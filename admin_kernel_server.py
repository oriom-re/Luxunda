
#!/usr/bin/env python3
"""
⚠️  UWAGA: Ten plik jest przestarzały!
Użyj głównego punktu wejścia: python main.py

🚀 LuxOS Admin Kernel Server
Unified LuxOS System - Administrator Interface
"""

print("⚠️  UWAGA: admin_kernel_server.py jest przestarzały!")
print("✅ Użyj głównego punktu wejścia: python main.py --mode=web")
exit(1)

import asyncio
import sys
import uvicorn
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

print("🚀 Starting LuxOS Admin Kernel Server...")
print("🌟 Unified LuxOS System Entry Point")
print("=" * 60)

from luxdb.core.admin_kernel import admin_kernel

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Admin Kernel Server...")
    try:
        await admin_kernel.initialize()
        print("✅ Admin Kernel Server ready!")
        print("👑 Admin Interface available at: http://0.0.0.0:3030")
    except Exception as e:
        print(f"⚠️ Admin Kernel Server startup warning: {e}")
        print("🔄 Continuing with limited functionality...")
    yield
    # Shutdown
    print("🔄 Shutting down Admin Kernel Server...")

app = FastAPI(
    title="LuxOS Admin Kernel",
    description="Interface administratora dla systemu LuxOS Kernel",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Status endpoint"""
    return {
        "service": "LuxOS Admin Kernel",
        "version": "1.0.0",
        "status": "running",
        "kernel_active": admin_kernel.system_status["kernel_active"],
        "lux_active": admin_kernel.system_status["lux_active"],
        "connections": admin_kernel.system_status["connections"]
    }

@app.get("/admin", response_class=HTMLResponse)
async def admin_interface():
    """Interface administratora"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LuxOS Admin Kernel Interface</title>
        <meta charset="utf-8">
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #0a0a0a; color: #e0e0e0; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: linear-gradient(135deg, #1e3c72, #2a5298); padding: 20px; border-radius: 10px; margin-bottom: 20px; }
            .header h1 { margin: 0; color: white; }
            .header .status { color: #4ade80; font-weight: bold; }
            .chat-container { background: #1a1a1a; border-radius: 10px; padding: 20px; height: 500px; display: flex; flex-direction: column; border: 1px solid #333; }
            .messages { flex: 1; overflow-y: auto; padding: 10px; background: #0f0f0f; border-radius: 5px; margin-bottom: 15px; }
            .message { margin: 10px 0; padding: 10px; border-radius: 8px; }
            .admin-message { background: #1e40af; color: white; margin-left: 50px; }
            .lux-message { background: #059669; color: white; margin-right: 50px; }
            .system-message { background: #7c2d12; color: #fcd34d; text-align: center; font-style: italic; }
            .input-container { display: flex; gap: 10px; }
            .message-input { flex: 1; padding: 10px; background: #2a2a2a; border: 1px solid #404040; color: #e0e0e0; border-radius: 5px; }
            .send-btn { padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 5px; cursor: pointer; }
            .send-btn:hover { background: #1d4ed8; }
            .status-panel { background: #1a1a1a; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #333; }
            .status-item { display: inline-block; margin-right: 20px; padding: 5px 10px; background: #2a2a2a; border-radius: 5px; }
            .green { color: #4ade80; }
            .red { color: #ef4444; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 LuxOS Admin Kernel Interface</h1>
                <div class="status">System Active • Lux Ready</div>
            </div>
            
            <div class="status-panel">
                <div class="status-item">Kernel: <span id="kernel-status" class="green">Active</span></div>
                <div class="status-item">Lux: <span id="lux-status" class="green">Active</span></div>
                <div class="status-item">Connections: <span id="connections">0</span></div>
                <div class="status-item">Beings: <span id="beings-count">0</span></div>
            </div>
            
            <div class="chat-container">
                <div class="messages" id="messages"></div>
                <div class="input-container">
                    <input type="text" class="message-input" id="messageInput" placeholder="Napisz wiadomość do Lux lub komendę kernel..." onkeypress="handleKeyPress(event)">
                    <button class="send-btn" onclick="sendMessage()">Wyślij</button>
                </div>
            </div>
        </div>

        <script>
            const ws = new WebSocket(`ws://${window.location.host}/ws/admin`);
            const messagesDiv = document.getElementById('messages');
            const messageInput = document.getElementById('messageInput');
            
            ws.onopen = function(event) {
                addMessage('system', 'Połączono z Admin Kernel Interface');
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                
                if (data.type === 'system_greeting') {
                    addMessage('system', data.message);
                    updateStatus(data.kernel_status);
                } else if (data.type === 'lux_response') {
                    addMessage('lux', data.message);
                } else if (data.type === 'error') {
                    addMessage('system', data.message);
                }
            };
            
            ws.onclose = function(event) {
                addMessage('system', 'Połączenie zamknięte');
            };
            
            function sendMessage() {
                const message = messageInput.value.trim();
                if (message) {
                    // Określ typ wiadomości
                    let messageType = 'lux_chat';
                    if (message.startsWith('/')) {
                        messageType = 'kernel_command';
                    }
                    
                    ws.send(JSON.stringify({
                        type: messageType,
                        content: message
                    }));
                    
                    addMessage('admin', message);
                    messageInput.value = '';
                }
            }
            
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendMessage();
                }
            }
            
            function addMessage(sender, content) {
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${sender}-message`;
                messageDiv.innerHTML = `
                    <strong>${sender.toUpperCase()}:</strong><br>
                    ${content.replace(/\\n/g, '<br>')}
                `;
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function updateStatus(status) {
                document.getElementById('kernel-status').textContent = status.kernel_active ? 'Active' : 'Inactive';
                document.getElementById('kernel-status').className = status.kernel_active ? 'green' : 'red';
                
                document.getElementById('lux-status').textContent = status.lux_active ? 'Active' : 'Inactive';
                document.getElementById('lux-status').className = status.lux_active ? 'green' : 'red';
                
                document.getElementById('connections').textContent = status.connections;
            }
            
            // Dodaj przykładowe komendy na start
            setTimeout(() => {
                addMessage('system', `
                    💡 <strong>Dostępne komendy:</strong><br>
                    • <code>status</code> - Status systemu<br>
                    • <code>beings</code> - Lista bytów<br>
                    • <code>help</code> - Pomoc<br>
                    • <code>/restart kernel</code> - Restart kernel (komenda z /)<br>
                    • Lub pisz normalnie z Lux! 🤖
                `);
            }, 1000);
        </script>
    </body>
    </html>
    """

@app.websocket("/ws/admin")
async def websocket_admin_endpoint(websocket: WebSocket):
    """WebSocket endpoint dla administratora"""
    await admin_kernel.connect_admin(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = eval(data)  # W produkcji użyj json.loads()
            await admin_kernel.process_admin_message(websocket, message_data)
            
    except WebSocketDisconnect:
        await admin_kernel.disconnect_admin(websocket)

@app.get("/api/system/status")
async def get_system_status():
    """API endpoint dla statusu systemu"""
    status = await admin_kernel.get_system_status()
    return status["data"]

@app.get("/api/beings")
async def get_beings():
    """API endpoint dla listy bytów"""
    beings = await admin_kernel.get_beings_list()
    return beings["data"]

@app.post("/api/kernel/command")
async def execute_kernel_command(command_data: dict):
    """API endpoint dla komend kernel"""
    command = command_data.get("command", "")
    result = await admin_kernel.execute_kernel_command(command)
    return result

if __name__ == "__main__":
    print("🚀 Starting LuxOS Admin Kernel Server on port 3030...")
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=3030,
        log_level="info"
    )
