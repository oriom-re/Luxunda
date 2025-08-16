
#!/usr/bin/env python3
"""
🤖 LuxDB Discord Bot Launcher
============================

Main script to launch the complete Discord bot system
"""

import asyncio
import os
import sys
from discord_luxdb_bot import LuxDBDiscordBot
from discord_bot_advanced_features import setup_advanced_features

async def main():
    """Launch the LuxDB Discord Bot"""
    print("🚀 Starting LuxDB Discord Assistant Bot...")
    print("=" * 50)
    
    # Check for required environment variables
    if not os.getenv('DISCORD_BOT_TOKEN'):
        print("❌ Missing DISCORD_BOT_TOKEN!")
        print("\n🔧 Setup Instructions:")
        print("1. Go to Replit Secrets tab")
        print("2. Add key: DISCORD_BOT_TOKEN")
        print("3. Add value: Your Discord bot token")
        print("\n📖 How to get a Discord bot token:")
        print("1. Go to https://discord.com/developers/applications")
        print("2. Create a new application")
        print("3. Go to 'Bot' section")
        print("4. Click 'Reset Token' and copy it")
        return
    
    # Initialize bot
    bot = LuxDBDiscordBot()
    
    # Set your Discord user ID (replace with your actual ID)
    bot.owner_id = 123456789012345678  # REPLACE WITH YOUR DISCORD USER ID
    
    # Setup advanced features
    setup_advanced_features(bot)
    
    print("🔧 Bot configured with features:")
    print("  ✅ LuxDB Integration")
    print("  ✅ Multilingual Support")
    print("  ✅ Development Tracking") 
    print("  ✅ Project Management")
    print("  ✅ Intelligent Moderation")
    print("  ✅ Memory System")
    print("  ✅ Owner Representation")
    
    try:
        # Start the bot
        token = os.getenv('DISCORD_BOT_TOKEN')
        await bot.start(token)
        
    except KeyboardInterrupt:
        print("\n🛑 Bot shutdown requested")
        await bot.close()
        
    except Exception as e:
        print(f"❌ Bot error: {e}")
        await bot.close()

if __name__ == "__main__":
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 LuxDB Discord Bot stopped")
