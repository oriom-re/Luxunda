
#!/usr/bin/env python3
"""
🚀 LuxOS Quick Start
Simple entry point that works
"""

import asyncio
import uvicorn
from pathlib import Path

def main():
    """Start the LuxOS system"""
    print("🚀 Starting LuxOS...")
    print("=" * 50)
    
    # Check if demo_landing.py exists and try to run it
    if Path("demo_landing.py").exists():
        print("📁 Found demo_landing.py - starting FastAPI server...")
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
