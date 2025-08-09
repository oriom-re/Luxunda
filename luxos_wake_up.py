
#!/usr/bin/env python3
"""
🌅 LuxOS Wake Up Script - Szybkie przebudzenie systemu
"""

import asyncio
import sys
from pathlib import Path

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

from luxos_bootstrap import wake_up_luxos, luxos_bootstrap

async def main():
    """Główna funkcja wake up"""
    print("🌅 LuxOS Wake Up Procedure Starting...")
    print("=" * 50)
    
    # Wykonaj przebudzenie
    result = await wake_up_luxos()
    
    print("\n" + "=" * 50)
    print("📊 RAPORT PRZEBUDZENIA:")
    print(f"✅ Status: {'SUKCES' if result['success'] else 'CZĘŚCIOWY'}")
    print(f"🔧 Aktywne komponenty: {result['active_components']}/{result['total_components']}")
    
    if result['success']:
        print("👑 Admin Interface: http://0.0.0.0:3030")
        print("🤖 Lux gotowy do komunikacji!")
    
    # Wyświetl ostatnie logi
    print("\n📋 OSTATNIE LOGI:")
    logs = luxos_bootstrap.get_system_logs()
    for log in logs[-10:]:  # Ostatnie 10 logów
        level_symbol = {"INFO": "ℹ️", "SUCCESS": "✅", "WARN": "⚠️", "ERROR": "❌"}.get(log["level"], "📝")
        print(f"{level_symbol} [{log['component']}] {log['message']}")
    
    return result

if __name__ == "__main__":
    asyncio.run(main())
