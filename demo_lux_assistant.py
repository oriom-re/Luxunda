
#!/usr/bin/env python3
"""
🚀 LuxOS AI Assistant Demo
Unified LuxOS System - AI Assistant Interface
"""

import asyncio
import os
import sys
from pathlib import Path

# Dodaj główny katalog do ścieżki Python
sys.path.insert(0, str(Path(__file__).parent))

print("🚀 Starting LuxOS AI Assistant...")
print("🌟 Unified LuxOS System Entry Point")
print("=" * 60)

from luxdb.ai_lux_assistant import LuxAssistant
from database.postgre_db import Postgre_db

async def main():
    print("🚀 Starting Lux AI Assistant Demo")
    print("=" * 50)
    
    # Initialize database
    await Postgre_db.initialize()
    
    # Get OpenAI API key (you'll need to set this)
    api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
    
    # Initialize Lux
    lux = LuxAssistant(api_key)
    await lux.initialize()
    
    print("\n🌟 Lux is ready! Try these examples:")
    print("- 'Potrzebuję zapisać notatkę z dzisiejszego dnia'")
    print("- 'Chcę zbudować kalkulator'") 
    print("- 'Szukam narzędzia do analizy tekstu'")
    print("- 'Stwórz mi system do zarządzania zadaniami'")
    print()
    
    while True:
        try:
            user_input = input("👤 You: ")
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Do widzenia!")
                break
            
            if user_input.strip():
                response = await lux.chat(user_input)
                print(f"🤖 Lux: {response}")
                print()
                
        except KeyboardInterrupt:
            print("\n👋 Do widzenia!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
