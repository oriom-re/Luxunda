
#!/usr/bin/env python3
"""
🚀 LuxOS Kernel System Start
Entry point z nowym systemem bytów i hashów
"""

import asyncio
import uvicorn
from pathlib import Path

async def initialize_kernel():
    """Inicjalizuje Kernel System"""
    try:
        from luxdb.core.kernel_system import kernel_system
        await kernel_system.initialize("default")
        
        status = await kernel_system.get_system_status()
        print(f"📊 System Status:")
        print(f"   Scenario: {status['active_scenario']}")
        print(f"   Beings: {status['registered_beings']}")
        print(f"   Hashes: {status['loaded_hashes']}")
        
        return True
    except Exception as e:
        print(f"❌ Kernel initialization error: {e}")
        return False

def main():
    """Start the LuxOS system"""
    print("🚀 Starting LuxOS Kernel System...")
    print("=" * 60)
    
    # Initialize Kernel System
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
