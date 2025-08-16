
#!/usr/bin/env python3
"""
Demo skomplikowanych bytów z genami w LuxDB
"""

import asyncio
import sys
import os

# Dodaj ścieżkę do modułów
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def main():
    """Uruchom demo złożonych bytów"""
    
    print("🚀 LuxDB - Demo skomplikowanych bytów z genami")
    print("=" * 50)
    
    try:
        # Zaimportuj i uruchom przykłady
        from examples.complex_being_example import main as run_complex_demo
        await run_complex_demo()
        
    except ImportError as e:
        print(f"❌ Błąd importu: {e}")
        print("Upewnij się, że wszystkie moduły są dostępne")
    except Exception as e:
        print(f"❌ Błąd podczas wykonywania demo: {e}")

if __name__ == "__main__":
    asyncio.run(main())
