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
from luxdb.core.session_data_manager import SessionDataManager
from luxdb.ai_lux_assistant import LuxAssistant
from luxdb.core.session_data_manager import global_session_registry
import ulid

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
        self.owner_id = int(os.getenv('DISCORD_USER_ID', 0)) if os.getenv('DISCORD_USER_ID') else None
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
            # Initialize database
            try:
                pool = await Postgre_db.get_db_pool()
                if pool:
                    print("✅ Database initialized for Discord bot")
                else:
                    print("❌ Failed to get database pool")
                    return
            except Exception as db_e:
                print(f"❌ Failed to initialize bot: {db_e}")
                return

            # Create bot being
            print("🔍 DEBUG: Starting bot being creation...")
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
        # Genotype for Discord bot - CORRECT STRUCTURE
        bot_genotype = {
            "genesis": {
                "name": "Discord Bot Assistant",
                "version": "1.0.0",
                "type": "assistant",
                "description": "LuxDB Discord Bot with advanced features"
            },
            "attributes": {
                "name": {
                    "py_type": "str",
                    "description": "Bot instance name",
                    "max_length": 100
                },
                "description": {
                    "py_type": "str",
                    "description": "Bot description",
                    "max_length": 500
                },
                "features": {
                    "py_type": "dict",
                    "description": "Bot feature configuration"
                },
                "status": {
                    "py_type": "str",
                    "description": "Current bot status",
                    "max_length": 50
                },
                "created_at": {
                    "py_type": "str",
                    "description": "Creation timestamp"
                }
            }
        }

        # Initialize being data with proper structure
        bot_features = {
            "helpful": True,
            "professional": True,
            "memory_focused": True,
            "development_oriented": True,
            "multilingual": True
        }

        # Prepare being data as a dictionary - ACCORDING TO GENOTYPE
        bot_attributes = {
            "name": "Discord Bot Instance",
            "description": "LuxDB Discord Bot Assistant",
            "features": bot_features,
            "status": "active",
            "created_at": datetime.now().isoformat()
        }

        # Create Soul for the bot
        try:
            print("🔍 DEBUG: Creating bot soul...")
            print(f"🔍 DEBUG: bot_genotype type: {type(bot_genotype)}")
            bot_soul = await Soul.create(bot_genotype, alias="discord_bot_soul")
            print(f"✅ Created Discord bot soul: {bot_soul.soul_hash[:8]}...")
            print(f"🔍 DEBUG: bot_soul type: {type(bot_soul)}")
            print(f"🔍 DEBUG: bot_attributes type: {type(bot_attributes)}")
            print(f"🔍 DEBUG: bot_attributes content: {bot_attributes}")

            # Use get_or_create with max_instances=1 for singleton behavior
            print("🔍 DEBUG: Calling Being.get_or_create...")
            self.bot_being = await Being.get_or_create(
                soul=bot_soul,
                alias="discord_bot_singleton",
                attributes=bot_attributes,
                max_instances=1  # Limit to one active Discord bot Being per soul
            )
            print(f"🔍 DEBUG: bot_being result type: {type(self.bot_being)}")

            if self.bot_being:
                # Initialize additional data (conversation memory, performance stats)
                if not hasattr(self.bot_being, 'data') or not self.bot_being.data:
                    self.bot_being.data = {}

                # Update with extended data
                self.bot_being.data.update({
                    "conversation_history": [],
                    "performance_stats": {
                        "messages_processed": 0,
                        "commands_executed": 0,
                        "errors_encountered": 0,
                        "uptime_start": datetime.now().isoformat()
                    },
                    "bot_config": {
                        "languages": list(self.languages.keys()),
                        "moderation_enabled": True,
                        "memory_limit": 1000
                    },
                    "memory": {
                        "recent_messages": [],
                        "development_notes": [],
                        "moderation_actions": []
                    },
                    "bot_ulid": self.bot_being.ulid
                })

                print(f"✅ Discord bot being ready: {self.bot_being.ulid}")
            else:
                print("❌ Failed to create/get bot being")

        except Exception as e:
            import traceback
            print(f"❌ Error creating Discord bot being: {e}")
            print(f"🔍 DEBUG: Full traceback:")
            print(traceback.format_exc())
            # Fallback - try to load existing bot being
            try:
                existing_soul = await Soul.get_by_alias("discord_bot_soul")
                if existing_soul:
                    beings_for_soul = await Being.get_by_soul_hash(existing_soul.soul_hash)
                    if beings_for_soul:
                        self.bot_being = beings_for_soul[0]  # First Being from this exact Soul
                        print(f"✅ Loaded existing Discord bot being: {self.bot_being.ulid}")
                    else:
                        print("❌ Could not load existing Discord bot being - no beings found for soul.")
                        self.bot_being = None
                else:
                    print("❌ Could not load existing Discord bot being - soul not found.")
                    self.bot_being = None
            except Exception as load_error:
                print(f"❌ Error loading existing being: {load_error}")
                self.bot_being = None

        if self.bot_being:
            print(f"🧠 Bot Being initialized: {self.bot_being.ulid}")
        else:
            print("❌ Failed to initialize bot being.")


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
            self.bot_being.data["status"] = "bot_online"
            self.bot_being.data["active_servers"] = [
                {"id": guild.id, "name": guild.name, "members": guild.member_count}
                for guild in self.guilds
            ]

    async def on_message(self, message):
        """Handle incoming messages with intelligent intent detection"""
        if message.author == self.user:
            return

        # Store conversation in memory
        await self.store_conversation(message)

        # Check if bot is mentioned or message contains LuxDB-related keywords
        bot_mentioned = self.user in message.mentions
        luxdb_keywords = ['lux', 'luxdb', 'status', 'projekt', 'rozwój', 'project', 'development']
        contains_keywords = any(keyword.lower() in message.content.lower() for keyword in luxdb_keywords)

        if bot_mentioned or contains_keywords or self.owner_status == "offline":
            await self.handle_intelligent_response(message)

        # Still process traditional commands for backwards compatibility
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

    async def handle_intelligent_response(self, message):
        """Handle message with intelligent intent detection and function execution"""
        if not self.lux_assistant:
            await message.reply("🤖 LuxDB Assistant is not available right now.")
            return

        # Prepare context for LuxAssistant
        context = f"""
        You are LuxDB Discord Assistant. Analyze this message and determine the user's intent.

        Message: {message.content}
        Server: {message.guild.name if message.guild else 'DM'}
        Author: {message.author.display_name}
        Bot mentioned: {self.user in message.mentions}

        Available functions you can call:
        - show_status: Show bot and project status
        - project_info: Share LuxDB project information
        - development_update: Share latest development updates
        - show_help: Show available capabilities
        - translate_text: Translate text to multiple languages
        - search_memory: Search conversation memory
        - show_roadmap: Show project roadmap
        - moderate_content: Check content for moderation

        Analyze the intent and respond naturally while calling appropriate functions if needed.
        If user asks about status, project, development, help, translation, memory, roadmap - use the corresponding function.
        """

        try:
            # Use LuxAssistant to determine intent and generate response
            response = await self.lux_assistant.chat(context)

            # Detect function calls from the response
            detected_functions = await self.detect_and_execute_functions(message, response)

            # If no specific functions were called, send the response directly
            if not detected_functions:
                embed = discord.Embed(
                    title="🧠 LuxDB Intelligence",
                    description=response,
                    color=0x00ff88,
                    timestamp=datetime.now()
                )
                embed.set_footer(text="Powered by LuxDB Assistant")
                await message.reply(embed=embed)

        except Exception as e:
            await message.reply("🔧 I'm experiencing some technical difficulties. Please try again later.")

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

    async def detect_and_execute_functions(self, message, response):
        """Detect intent from message content and execute appropriate functions"""
        content_lower = message.content.lower()
        executed_functions = []

        # Intent detection patterns
        if any(word in content_lower for word in ['status', 'stan', 'jak się masz', 'how are you']):
            await self.execute_status_function(message)
            executed_functions.append('status')

        elif any(word in content_lower for word in ['projekt', 'project', 'luxdb', 'o projekcie', 'about']):
            await self.execute_project_info_function(message)
            executed_functions.append('project_info')

        elif any(word in content_lower for word in ['aktualizacje', 'updates', 'rozwój', 'development', 'postęp', 'progress']):
            await self.execute_development_update_function(message)
            executed_functions.append('development_update')

        elif any(word in content_lower for word in ['plan', 'roadmap', 'mapa', 'przyszłość', 'future']):
            await self.execute_roadmap_function(message)
            executed_functions.append('roadmap')

        elif any(word in content_lower for word in ['pomoc', 'help', 'co potrafisz', 'what can you do']):
            await self.execute_help_function(message)
            executed_functions.append('help')

        elif any(word in content_lower for word in ['przetłumacz', 'translate', 'tłumaczenie']):
            # Extract text to translate
            text_to_translate = message.content
            for prefix in ['przetłumacz', 'translate']:
                if prefix in content_lower:
                    text_to_translate = message.content.split(prefix, 1)[-1].strip()
                    break
            await self.execute_translate_function(message, text_to_translate)
            executed_functions.append('translate')

        elif any(word in content_lower for word in ['pamięć', 'memory', 'szukaj', 'search', 'znajdź']):
            # Extract search query
            query = message.content
            for prefix in ['pamięć', 'memory', 'szukaj', 'search', 'znajdź']:
                if prefix in content_lower:
                    query = message.content.split(prefix, 1)[-1].strip()
                    break
            await self.execute_memory_search_function(message, query)
            executed_functions.append('memory_search')

        return executed_functions

    async def execute_status_function(self, message):
        """Execute status function"""
        embed = discord.Embed(
            title="🤖 LuxDB Bot Status",
            color=0x00ff88,
            timestamp=datetime.now()
        )

        embed.add_field(name="🔋 Bot Status", value="Online & Active", inline=True)
        embed.add_field(name="👤 Owner Status", value=self.owner_status.title(), inline=True)
        embed.add_field(name="🌐 Servers", value=len(self.guilds), inline=True)

        if self.bot_being:
            memory_count = len(self.bot_being.data.get('conversation_memory', {}))
            embed.add_field(name="🧠 Memory", value=f"{memory_count} conversations stored", inline=False)

        embed.add_field(name="🚀 LuxDB Version", value="v1.0.0 - Genotypic Evolution System", inline=False)

        await message.reply(embed=embed)

    async def execute_project_info_function(self, message):
        """Execute project info function"""
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

        await message.reply(embed=embed)

    async def execute_development_update_function(self, message):
        """Execute development update function"""
        updates = [
            "✅ v1.0.0 Stable Release - Genetic OS architecture completed",
            "🧬 Soul/Being system with hash-based immutability",
            "⚡ Lazy execution and multi-language bridge implemented",
            "🤖 Discord bot with intelligent intent detection",
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
            embed.add_field(name=f"Update #{i}", value=update, inline=False)

        embed.set_footer(text="Updates tracked by LuxDB Assistant")
        await message.reply(embed=embed)

    async def execute_roadmap_function(self, message):
        """Execute roadmap function"""
        roadmap_items = [
            {
                "phase": "Phase 1: Core System ✅",
                "items": ["✅ Soul/Being architecture", "✅ Hash-based immutability", "✅ PostgreSQL integration", "✅ Basic function execution"]
            },
            {
                "phase": "Phase 2: Advanced Features 🔄",
                "items": ["✅ Multi-language support", "✅ Discord bot integration", "🔄 AI assistant enhancement", "🔄 Web interface expansion"]
            },
            {
                "phase": "Phase 3: Enterprise Features 📋",
                "items": ["📋 Advanced security features", "📋 Distributed beings network", "📋 Real-time collaboration", "📋 Enterprise deployment tools"]
            }
        ]

        embed = discord.Embed(
            title="🗺️ LuxDB Development Roadmap",
            description="Current development phases and progress",
            color=0x00ff88,
            timestamp=datetime.now()
        )

        for phase in roadmap_items:
            items_text = "\n".join(phase["items"])
            embed.add_field(name=phase["phase"], value=items_text, inline=False)

        await message.reply(embed=embed)

    async def execute_help_function(self, message):
        """Execute help function"""
        embed = discord.Embed(
            title="🧠 LuxDB Intelligent Assistant",
            description="I understand natural language! Just talk to me about:",
            color=0x00ff88
        )

        capabilities = [
            ("📊 Status", "Ask about my status or the project status"),
            ("🧬 Project Info", "Ask about LuxDB, the project, or how it works"),
            ("🚀 Development", "Ask about updates, progress, or development"),
            ("🗺️ Roadmap", "Ask about plans, roadmap, or future features"),
            ("🌍 Translation", "Ask me to translate text to multiple languages"),
            ("🧠 Memory", "Ask me to search through our conversation history"),
            ("💬 Natural Chat", "Just talk to me naturally - I'll understand!")
        ]

        for capability, description in capabilities:
            embed.add_field(name=capability, value=description, inline=False)

        embed.set_footer(text="No need for exact commands - I understand context! 🤖")
        await message.reply(embed=embed)

    async def execute_translate_function(self, message, text):
        """Execute translate function"""
        if not text or text == message.content:
            await message.reply("Please tell me what text you'd like me to translate!")
            return

        translations = {
            'en': text,  # Original
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

        await message.reply(embed=embed)

    async def execute_memory_search_function(self, message, query):
        """Execute memory search function"""
        if not query or query == message.content:
            await message.reply("Please tell me what you'd like me to search for in our conversation history!")
            return

        if not self.bot_being:
            await message.reply("Memory system not initialized.")
            return

        memory = self.bot_being.data.get("conversation_memory", {})
        server_id = str(message.guild.id if message.guild else "DM")

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

        await message.reply(embed=embed)

    @commands.command(name='help')
    async def help_command(self, ctx):
        """Legacy command - redirect to intelligent help"""
        await self.execute_help_function(ctx.message)

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
            self.bot_being.data["status"] = "bot_online"
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