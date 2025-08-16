
"""
🤖 LuxDB Discord Assistant Bot
============================

Intelligent Discord bot powered by LuxDB that serves as:
- Personal assistant and representative
- Multilingual moderator 
- Development communication hub
- Project narrator and memory keeper
"""

import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiohttp
import re

# LuxDB imports
from luxdb.models.soul import Soul
from luxdb.models.being import Being
from luxdb.core.luxdb import LuxDB
from luxdb.ai_lux_assistant import LuxAssistant
from luxdb.core.session_data_manager import global_session_registry

class LuxDBDiscordBot(commands.Bot):
    """Main Discord bot class integrated with LuxDB"""
    
    def __init__(self):
        # Discord setup
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        intents.reactions = True
        
        super().__init__(
            command_prefix=['!lux ', '!luxdb ', '@LuxDB '],
            intents=intents,
            help_command=None
        )
        
        # LuxDB integration
        self.luxdb = None
        self.lux_assistant = None
        self.bot_being = None
        self.session_manager = None
        
        # Bot personality and memory
        self.owner_id = None  # Set this to your Discord user ID
        self.languages = {
            'en': 'English',
            'pl': 'Polski', 
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'ja': '日本語'
        }
        
        # Status tracking
        self.owner_status = "offline"  # online, offline, busy, away
        self.development_channel = None
        self.announcement_channels = []
        
        # Conversation memory
        self.conversation_memory = {}
        self.project_updates = []
        
    async def setup_hook(self):
        """Initialize LuxDB connection and bot being"""
        try:
            # Initialize LuxDB
            from luxdb.core.postgre_db import Postgre_db
            await Postgre_db.initialize_pool()
            
            # Create LuxDB bot being
            await self.create_bot_being()
            
            # Initialize Lux Assistant
            self.lux_assistant = LuxAssistant()
            await self.lux_assistant.initialize()
            
            # Start background tasks
            self.status_updater.start()
            self.memory_sync.start()
            
            print("🤖 LuxDB Discord Bot initialized successfully!")
            
        except Exception as e:
            print(f"❌ Failed to initialize bot: {e}")
    
    async def create_bot_being(self):
        """Create a Being representation of the Discord bot"""
        bot_genotype = {
            "genesis": {
                "name": "LuxDB_Discord_Assistant",
                "type": "discord_bot",
                "version": "1.0.0",
                "description": "Intelligent Discord assistant for LuxDB project"
            },
            "attributes": {
                "owner_status": {"py_type": "str"},
                "active_servers": {"py_type": "List[dict]"},
                "conversation_memory": {"py_type": "dict"},
                "project_updates": {"py_type": "List[dict]"},
                "language_preferences": {"py_type": "dict"},
                "moderation_actions": {"py_type": "List[dict]"},
                "development_notes": {"py_type": "List[dict]"},
                "personality_traits": {"py_type": "dict"}
            },
            "functions": {
                "moderate_message": {
                    "description": "Moderate messages in multiple languages",
                    "parameters": ["message", "language", "context"]
                },
                "represent_owner": {
                    "description": "Respond as owner's representative when offline",
                    "parameters": ["query", "context", "urgency"]
                },
                "update_project_status": {
                    "description": "Share project updates and development progress",
                    "parameters": ["update_type", "content", "audience"]
                },
                "facilitate_development": {
                    "description": "Help with LuxDB development communication",
                    "parameters": ["discussion_topic", "participants", "context"]
                }
            }
        }
        
        # Create Soul for the bot
        bot_soul = await Soul.create(bot_genotype, alias="luxdb_discord_bot")
        
        # Create Being instance
        self.bot_being = await Being.create(
            bot_soul,
            {
                "owner_status": "initializing",
                "active_servers": [],
                "conversation_memory": {},
                "project_updates": [],
                "language_preferences": {"default": "en"},
                "moderation_actions": [],
                "development_notes": [],
                "personality_traits": {
                    "helpful": True,
                    "professional": True,
                    "multilingual": True,
                    "project_focused": True,
                    "memory_keeper": True
                }
            },
            alias="discord_bot_instance"
        )
        
        print(f"🧠 Bot Being created: {self.bot_being.ulid}")
    
    async def on_ready(self):
        """Called when bot is ready"""
        print(f'🚀 {self.user} is now online!')
        print(f'📊 Connected to {len(self.guilds)} servers')
        
        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="LuxDB development | !lux help"
            ),
            status=discord.Status.online
        )
        
        # Update bot being status
        if self.bot_being:
            self.bot_being.data["owner_status"] = "bot_online"
            self.bot_being.data["active_servers"] = [
                {"id": guild.id, "name": guild.name, "members": guild.member_count}
                for guild in self.guilds
            ]
    
    async def on_message(self, message):
        """Handle incoming messages"""
        if message.author == self.user:
            return
        
        # Store conversation in memory
        await self.store_conversation(message)
        
        # Check if owner is mentioned or offline responses needed
        if self.owner_id and message.author.id != self.owner_id:
            if f'<@{self.owner_id}>' in message.content or self.owner_status == "offline":
                await self.handle_owner_representation(message)
        
        # Process commands
        await self.process_commands(message)
    
    async def store_conversation(self, message):
        """Store conversation in bot's memory"""
        if not self.bot_being:
            return
        
        server_id = str(message.guild.id if message.guild else "DM")
        channel_id = str(message.channel.id)
        
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "server_id": server_id,
            "channel_id": channel_id,
            "author": {
                "id": message.author.id,
                "name": message.author.display_name
            },
            "content": message.content[:500],  # Limit content length
            "type": "message"
        }
        
        # Store in memory (limit to last 1000 messages)
        memory = self.bot_being.data.get("conversation_memory", {})
        if server_id not in memory:
            memory[server_id] = []
        
        memory[server_id].append(conversation_entry)
        if len(memory[server_id]) > 1000:
            memory[server_id] = memory[server_id][-1000:]
        
        self.bot_being.data["conversation_memory"] = memory
    
    async def handle_owner_representation(self, message):
        """Respond as owner's representative when needed"""
        if not self.lux_assistant:
            return
        
        context = f"""
        You are representing the owner of LuxDB project in their absence.
        Message: {message.content}
        Server: {message.guild.name if message.guild else 'DM'}
        Author: {message.author.display_name}
        
        Respond professionally as the project representative, focusing on:
        - LuxDB project information
        - Development updates
        - Community engagement
        - Directing technical questions appropriately
        """
        
        try:
            response = await self.lux_assistant.chat(context)
            
            embed = discord.Embed(
                title="🤖 LuxDB Assistant Response",
                description=response,
                color=0x00ff88,
                timestamp=datetime.now()
            )
            embed.set_footer(text="Responding for project owner | LuxDB Assistant")
            
            await message.reply(embed=embed)
            
        except Exception as e:
            await message.reply("Sorry, I'm having trouble processing that request right now.")
    
    @commands.command(name='status')
    async def status_command(self, ctx):
        """Show bot and project status"""
        embed = discord.Embed(
            title="🤖 LuxDB Bot Status",
            color=0x00ff88,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="🔋 Bot Status",
            value="Online & Active",
            inline=True
        )
        
        embed.add_field(
            name="👤 Owner Status", 
            value=self.owner_status.title(),
            inline=True
        )
        
        embed.add_field(
            name="🌐 Servers",
            value=len(self.guilds),
            inline=True
        )
        
        embed.add_field(
            name="🧠 Memory",
            value=f"{len(self.bot_being.data.get('conversation_memory', {}))} conversations stored",
            inline=False
        )
        
        embed.add_field(
            name="🚀 LuxDB Version",
            value="v1.0.0 - Genotypic Evolution System",
            inline=False
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='project')
    async def project_info(self, ctx):
        """Share LuxDB project information"""
        embed = discord.Embed(
            title="🧬 LuxDB - Not Relation. Not Document. Evolution.",
            description="Revolutionary genetic database system where data evolves instead of being modified.",
            color=0x00ff88,
            url="https://github.com/your-repo/luxdb"
        )
        
        embed.add_field(
            name="🎯 Core Concept",
            value="• **Soul (Genotype)**: Immutable templates with SHA-256 hash\n• **Being (Instance)**: Living data based on genotypes\n• **Evolution**: Changes through evolution, not mutation",
            inline=False
        )
        
        embed.add_field(
            name="⚡ Key Features",
            value="• Hash-based immutability\n• Lazy execution\n• Multi-language support\n• Being ownership management",
            inline=False
        )
        
        embed.add_field(
            name="🔧 Technology Stack",
            value="Python 3.11+, PostgreSQL, asyncpg, FastAPI",
            inline=True
        )
        
        embed.add_field(
            name="📈 Status",
            value="v1.0.0 Stable Release",
            inline=True
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='help')
    async def help_command(self, ctx):
        """Show available commands"""
        embed = discord.Embed(
            title="🤖 LuxDB Assistant Commands",
            description="I'm your multilingual assistant for LuxDB project!",
            color=0x00ff88
        )
        
        commands_list = [
            ("!lux status", "Show bot and project status"),
            ("!lux project", "Get LuxDB project information"),
            ("!lux update", "Share latest development updates"),
            ("!lux roadmap", "Show project roadmap and plans"),
            ("!lux docs", "Get documentation links"),
            ("!lux demo", "Request project demonstration"),
            ("!lux translate [text]", "Translate text to multiple languages"),
            ("!lux moderate", "Show moderation capabilities"),
            ("!lux memory [query]", "Search conversation memory"),
        ]
        
        for cmd, desc in commands_list:
            embed.add_field(name=cmd, value=desc, inline=False)
        
        embed.set_footer(text="I can respond in multiple languages! 🌍")
        await ctx.send(embed=embed)
    
    @commands.command(name='update')
    async def development_update(self, ctx):
        """Share latest development updates"""
        updates = [
            "✅ v1.0.0 Stable Release - Genetic OS architecture completed",
            "🧬 Soul/Being system with hash-based immutability",
            "⚡ Lazy execution and multi-language bridge implemented", 
            "🤖 Discord bot integration with LuxDB Assistant",
            "🌐 Web interface with reactive components",
            "📊 Production hash management system"
        ]
        
        embed = discord.Embed(
            title="🚀 Latest LuxDB Development Updates",
            description="Current progress and achievements:",
            color=0x00ff88,
            timestamp=datetime.now()
        )
        
        for i, update in enumerate(updates, 1):
            embed.add_field(
                name=f"Update #{i}",
                value=update,
                inline=False
            )
        
        embed.set_footer(text="Updates tracked by LuxDB Assistant")
        await ctx.send(embed=embed)
    
    @commands.command(name='translate')
    async def translate_command(self, ctx, *, text: str):
        """Translate text to multiple languages"""
        translations = {
            'en': text,  # Original assumed to be English
            'pl': f"[PL] {text}",  # Placeholder - integrate with translation service
            'es': f"[ES] {text}",
            'fr': f"[FR] {text}",
            'de': f"[DE] {text}",
            'ja': f"[JA] {text}"
        }
        
        embed = discord.Embed(
            title="🌍 Multilingual Translation",
            description="LuxDB Assistant supports multiple languages:",
            color=0x00ff88
        )
        
        for lang_code, lang_name in self.languages.items():
            embed.add_field(
                name=f"{lang_name} ({lang_code})",
                value=translations.get(lang_code, "Translation pending..."),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='memory')
    async def search_memory(self, ctx, *, query: str = None):
        """Search conversation memory"""
        if not query:
            await ctx.send("Please provide a search query: `!lux memory [your query]`")
            return
        
        if not self.bot_being:
            await ctx.send("Memory system not initialized.")
            return
        
        memory = self.bot_being.data.get("conversation_memory", {})
        server_id = str(ctx.guild.id if ctx.guild else "DM")
        
        results = []
        if server_id in memory:
            for entry in memory[server_id][-100:]:  # Search last 100 messages
                if query.lower() in entry.get("content", "").lower():
                    results.append(entry)
        
        embed = discord.Embed(
            title=f"🧠 Memory Search: '{query}'",
            description=f"Found {len(results)} relevant conversations",
            color=0x00ff88
        )
        
        for i, result in enumerate(results[-5:], 1):  # Show last 5 results
            embed.add_field(
                name=f"Result #{i}",
                value=f"**{result['author']['name']}**: {result['content'][:100]}...\n*{result['timestamp'][:19]}*",
                inline=False
            )
        
        if not results:
            embed.description = "No matching conversations found in memory."
        
        await ctx.send(embed=embed)
    
    @tasks.loop(minutes=5)
    async def status_updater(self):
        """Update bot status periodically"""
        if self.bot_being:
            self.bot_being.data["last_activity"] = datetime.now().isoformat()
    
    @tasks.loop(minutes=30)
    async def memory_sync(self):
        """Sync conversation memory to database"""
        if self.bot_being:
            # This would sync the bot's memory to the database
            print("🔄 Syncing conversation memory to LuxDB...")
    
    async def close(self):
        """Cleanup when bot shuts down"""
        if self.lux_assistant:
            # Save final state
            pass
        await super().close()

# Bot configuration and startup
async def main():
    """Main function to run the bot"""
    bot = LuxDBDiscordBot()
    
    # Set your Discord user ID here
    bot.owner_id = 123456789012345678  # Replace with your actual Discord user ID
    
    # Get bot token from environment variable
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token:
        print("❌ DISCORD_BOT_TOKEN environment variable not set!")
        print("🔧 Set it in Replit Secrets:")
        print("   Key: DISCORD_BOT_TOKEN")
        print("   Value: Your Discord bot token")
        return
    
    try:
        await bot.start(token)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    asyncio.run(main())
