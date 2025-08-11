#!/usr/bin/env python3
"""
🌟 LuxOS Core - Prosty system Soul + Being

Podstawa:
- Soul: Niezmienny genotyp (szablon)  
- Being: Instancja Soul (fenotyp)
- Wszystko inne to Being (events, messages, relations)
- Async bez własnej pętli - listener steruje cyklem
"""

import sys
import asyncio
import argparse
from typing import Dict, Any
from datetime import datetime

# Core imports
from luxdb.core.globals import Globals
from database.postgre_db import Postgre_db
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.web_lux_interface import create_app

VERSION = "2.0.0-minimal"
SYSTEM_NAME = "LuxOS Minimal"

async def init_minimal_system() -> Dict[str, Any]:
    """Inicjalizuje minimalny system Soul + Being"""
    print(f"\n🚀 {SYSTEM_NAME} v{VERSION}")

    try:
        # Połączenie z bazą
        print("📊 PostgreSQL...")
        pool = await Postgre_db.get_db_pool()
        if not pool:
            raise Exception("Database connection failed")

        # Test operacji
        souls = await Soul.get_all()
        beings = await Being.get_all()

        return {
            "status": "operational",
            "souls_count": len(souls),
            "beings_count": len(beings),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}

async def run_web_mode():
    """Serwer webowy"""
    status = await init_minimal_system()
    if status.get("status") != "operational":
        print("❌ Cannot start server")
        return

    app = create_app()
    app.config['SYSTEM_STATUS'] = status

    print("🚀 Server: http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)

async def show_status():
    """Status systemu"""
    status = await init_minimal_system()
    print(f"📊 Status: {status.get('status')}")
    print(f"🧬 Souls: {status.get('souls_count', 0)}")
    print(f"🤖 Beings: {status.get('beings_count', 0)}")

def main():
    parser = argparse.ArgumentParser(description=f'{SYSTEM_NAME} v{VERSION}')
    parser.add_argument('--mode', choices=['web'], default='web')
    parser.add_argument('--status', action='store_true')

    args = parser.parse_args()

    try:
        if args.status:
            asyncio.run(show_status())
        else:
            asyncio.run(run_web_mode())
    except KeyboardInterrupt:
        print("\n👋 Interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()