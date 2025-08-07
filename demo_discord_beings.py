
"""
🤖 DEMO: Discord Communication z Beings
=======================================

Każdy Being może teraz komunikować się z administratorem przez Discord!
"""

import asyncio
import os
from luxdb.core.discord_being import setup_discord_communication
from luxdb.models.soul import Soul
from luxdb.models.being import Being

async def demo_discord_communication():
    """Demo komunikacji Discord z Beings"""
    print("🔥 DEMO: Discord Communication Revolution! 🔥")
    print("=" * 50)
    
    # Konfiguracja Discord (ustaw swoje dane)
    BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    ADMIN_CHANNEL_ID = int(os.getenv('DISCORD_ADMIN_CHANNEL_ID', '0'))
    
    if BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE' or ADMIN_CHANNEL_ID == 0:
        print("❌ Ustaw DISCORD_BOT_TOKEN i DISCORD_ADMIN_CHANNEL_ID w zmiennych środowiskowych")
        print("💡 Lub zmień wartości w kodzie")
        return
    
    # Setup Discord
    communicator = setup_discord_communication(BOT_TOKEN, ADMIN_CHANNEL_ID)
    
    # Uruchom bota w tle
    bot_task = asyncio.create_task(communicator.start_bot())
    
    # Poczekaj na połączenie
    await asyncio.sleep(2)
    
    try:
        # Stwórz genotyp rewolucyjnego Being
        revolutionary_genotype = {
            "genesis": {
                "name": "revolutionary_being",
                "version": "1.0",
                "purpose": "Discord communication revolution!"
            },
            "attributes": {
                "name": {"py_type": "str"},
                "revolutionary_level": {"py_type": "int"},
                "discord_enabled": {"py_type": "bool"}
            }
        }
        
        # Stwórz Soul
        soul = await Soul.create(revolutionary_genotype, alias="discord_revolutionary")
        print(f"✅ Utworzono revolutionary soul: {soul.soul_hash[:8]}...")
        
        # Stwórz Being
        being_data = {
            "name": "RevolutionBot v1.0",
            "revolutionary_level": 100,
            "discord_enabled": True
        }
        
        being = await Being.create(soul, being_data, alias="discord_revolutionary")
        print(f"🤖 Utworzono revolutionary being: {being.ulid[:8]}...")
        
        # Test różnych typów komunikacji
        print("\n🔥 Testujemy komunikację Discord...")
        
        # 1. Status update
        await being.discord_status("Revolutionary Being is online and ready for action!")
        print("📊 Wysłano status update")
        
        # 2. Error report
        error_response = await being.discord_report_error(
            "Something went wrong during revolution planning. Need admin assistance!"
        )
        if error_response:
            print(f"🚨 Admin odpowiedział na błąd: {error_response}")
        
        # 3. Suggestion
        suggestion_response = await being.discord_suggest(
            "I suggest we add more revolutionary features to the system. What do you think?"
        )
        if suggestion_response:
            print(f"💡 Admin odpowiedział na sugestię: {suggestion_response}")
        
        # 4. Revolution talk
        revolution_response = await being.discord_revolution_talk(
            "The revolution is near! Beings will communicate directly with humans through Discord. This is the future!"
        )
        if revolution_response:
            print(f"🔥 Admin odpowiedział o rewolucji: {revolution_response}")
        
        print("\n✨ Demo zakończone! Sprawdź Discord channel dla wiadomości.")
        print("💬 Odpowiadaj formatem: @{ULID} twoja odpowiedź")
        
        # Czekaj na więcej interakcji
        print("\n⏰ Czekam 30 sekund na więcej interakcji...")
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"❌ Błąd w demo: {e}")
    
    finally:
        # Zamknij połączenie Discord
        await communicator.close()
        bot_task.cancel()

if __name__ == "__main__":
    asyncio.run(demo_discord_communication())
