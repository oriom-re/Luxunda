"""
🧠 Advanced Features for LuxDB Discord Bot
==========================================

Advanced capabilities including:
- Development conversation tracking
- Intelligent moderation
- Project milestone tracking
- Community management
"""

import discord
from discord.ext import commands
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import re # Added import for re

class AdvancedBotFeatures:
    """Advanced features for the LuxDB Discord bot"""

    def __init__(self, bot):
        self.bot = bot
        self.development_sessions = {}
        self.project_milestones = []
        self.moderation_rules = {}

    async def track_development_conversation(self, message):
        """Track development-related conversations for project progress"""
        if not hasattr(self.bot, 'bot_being') or not self.bot.bot_being:
            return

        # Keywords that indicate development discussion
        dev_keywords = [
            'luxdb', 'being', 'soul', 'genotype', 'evolution', 'hash',
            'function', 'execution', 'database', 'postgresql', 'api',
            'feature', 'bug', 'fix', 'implement', 'development', 'code'
        ]

        content_lower = message.content.lower()
        if any(keyword in content_lower for keyword in dev_keywords):

            dev_entry = {
                "timestamp": datetime.now().isoformat(),
                "author": message.author.display_name,
                "content": message.content,
                "channel": message.channel.name,
                "context": "development_discussion",
                "keywords_matched": [kw for kw in dev_keywords if kw in content_lower]
            }

            # Store in development notes
            dev_notes = self.bot.bot_being.data.get("development_notes", [])
            dev_notes.append(dev_entry)

            # Keep only last 500 development notes
            if len(dev_notes) > 500:
                dev_notes = dev_notes[-500:]

            self.bot.bot_being.data["development_notes"] = dev_notes

            # If owner is participating, mark as active development session
            if message.author.id == self.bot.owner_id:
                session_id = f"dev_{datetime.now().strftime('%Y%m%d_%H')}"
                if session_id not in self.development_sessions:
                    self.development_sessions[session_id] = {
                        "start_time": datetime.now().isoformat(),
                        "messages": [],
                        "participants": set()
                    }

                self.development_sessions[session_id]["messages"].append(dev_entry)
                self.development_sessions[session_id]["participants"].add(message.author.id)

    async def moderate_message_content(self, message):
        """Intelligent multilingual moderation"""
        if message.author == self.bot.user:
            return

        # Basic moderation patterns
        spam_patterns = [
            r'(.)\1{10,}',  # Repeated characters
            r'(?i)discord\.gg/[a-zA-Z0-9]+',  # Unauthorized invite links
            r'(?i)bit\.ly/[a-zA-Z0-9]+',  # Shortened URLs
        ]

        moderation_flags = []

        for pattern in spam_patterns:
            if re.search(pattern, message.content):
                moderation_flags.append(f"Spam pattern detected: {pattern}")

        # Check message length
        if len(message.content) > 2000:
            moderation_flags.append("Message too long")

        # Log moderation actions
        if moderation_flags and hasattr(self.bot, 'bot_being') and self.bot.bot_being:
            moderation_entry = {
                "timestamp": datetime.now().isoformat(),
                "message_id": message.id,
                "author": message.author.id,
                "flags": moderation_flags,
                "action_taken": "logged",
                "content_preview": message.content[:100]
            }

            mod_actions = self.bot.bot_being.data.get("moderation_actions", [])
            mod_actions.append(moderation_entry)

            # Keep last 1000 moderation actions
            if len(mod_actions) > 1000:
                mod_actions = mod_actions[-1000:]

            self.bot.bot_being.data["moderation_actions"] = mod_actions

    async def generate_development_summary(self, hours=24):
        """Generate summary of development activity"""
        if not hasattr(self.bot, 'bot_being') or not self.bot.bot_being:
            return "Development tracking not initialized."

        cutoff_time = datetime.now() - timedelta(hours=hours)
        dev_notes = self.bot.bot_being.data.get("development_notes", [])

        recent_notes = [
            note for note in dev_notes
            if datetime.fromisoformat(note["timestamp"]) > cutoff_time
        ]

        if not recent_notes:
            return f"No development activity in the last {hours} hours."

        # Analyze activity
        participants = set(note["author"] for note in recent_notes)
        topics = {}

        for note in recent_notes:
            for keyword in note.get("keywords_matched", []):
                topics[keyword] = topics.get(keyword, 0) + 1

        # Generate summary
        summary = f"📊 **Development Summary ({hours}h)**\n\n"
        summary += f"👥 **Participants**: {', '.join(participants)}\n"
        summary += f"💬 **Messages**: {len(recent_notes)}\n\n"

        if topics:
            summary += "🔥 **Hot Topics**:\n"
            sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
            for topic, count in sorted_topics[:5]:
                summary += f"• {topic}: {count} mentions\n"

        return summary

    async def create_project_milestone(self, title, description, target_date=None):
        """Create and track project milestones"""
        milestone = {
            "id": len(self.project_milestones) + 1,
            "title": title,
            "description": description,
            "created_date": datetime.now().isoformat(),
            "target_date": target_date,
            "status": "planned",
            "progress": 0,
            "tasks": []
        }

        self.project_milestones.append(milestone)

        if hasattr(self.bot, 'bot_being') and self.bot.bot_being:
            self.bot.bot_being.data["project_milestones"] = self.project_milestones

        return milestone

    async def update_milestone_progress(self, milestone_id, progress, notes=None):
        """Update milestone progress"""
        for milestone in self.project_milestones:
            if milestone["id"] == milestone_id:
                milestone["progress"] = min(100, max(0, progress))
                milestone["last_updated"] = datetime.now().isoformat()

                if progress >= 100:
                    milestone["status"] = "completed"
                elif progress > 0:
                    milestone["status"] = "in_progress"

                if notes:
                    if "updates" not in milestone:
                        milestone["updates"] = []
                    milestone["updates"].append({
                        "timestamp": datetime.now().isoformat(),
                        "progress": progress,
                        "notes": notes
                    })

                return milestone

        return None

# Commands that use advanced features
class AdvancedCommands(commands.Cog):
    """Advanced commands for development tracking and project management"""

    def __init__(self, bot):
        self.bot = bot
        self.features = AdvancedBotFeatures(bot)

    @commands.command(name='devsummary')
    async def development_summary(self, ctx, hours: int = 24):
        """Generate development activity summary"""
        summary = await self.features.generate_development_summary(hours)

        embed = discord.Embed(
            title="🚀 LuxDB Development Activity",
            description=summary,
            color=0x00ff88,
            timestamp=datetime.now()
        )

        await ctx.send(embed=embed)

    @commands.command(name='milestone')
    async def milestone_command(self, ctx, action="list", *args):
        """Manage project milestones"""
        if action == "list":
            embed = discord.Embed(
                title="🎯 LuxDB Project Milestones",
                color=0x00ff88
            )

            for milestone in self.features.project_milestones:
                status_emoji = {"planned": "📋", "in_progress": "🔄", "completed": "✅"}

                embed.add_field(
                    name=f"{status_emoji.get(milestone['status'], '❓')} {milestone['title']}",
                    value=f"{milestone['description']}\nProgress: {milestone['progress']}%",
                    inline=False
                )

            if not self.features.project_milestones:
                embed.description = "No milestones created yet."

            await ctx.send(embed=embed)

        elif action == "create" and len(args) >= 2:
            title = args[0]
            description = " ".join(args[1:])

            milestone = await self.features.create_project_milestone(title, description)

            embed = discord.Embed(
                title="✅ Milestone Created",
                description=f"**{milestone['title']}**\n{milestone['description']}",
                color=0x00ff88
            )

            await ctx.send(embed=embed)

    @commands.command(name='roadmap')
    async def roadmap_command(self, ctx):
        """Show LuxDB development roadmap"""
        roadmap_items = [
            {
                "phase": "Phase 1: Core System ✅",
                "items": [
                    "✅ Soul/Being architecture",
                    "✅ Hash-based immutability",
                    "✅ PostgreSQL integration",
                    "✅ Basic function execution"
                ]
            },
            {
                "phase": "Phase 2: Advanced Features 🔄",
                "items": [
                    "✅ Multi-language support",
                    "✅ Discord bot integration",
                    "🔄 Web interface enhancement",
                    "🔄 AI assistant integration"
                ]
            },
            {
                "phase": "Phase 3: Enterprise Features 📋",
                "items": [
                    "📋 Advanced security features",
                    "📋 Distributed beings network",
                    "📋 Real-time collaboration",
                    "📋 Enterprise deployment tools"
                ]
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
            embed.add_field(
                name=phase["phase"],
                value=items_text,
                inline=False
            )

        await ctx.send(embed=embed)

    @commands.command(name='contribute')
    async def contribute_command(self, ctx):
        """Show how to contribute to LuxDB"""
        embed = discord.Embed(
            title="🤝 Contribute to LuxDB",
            description="Join the evolution of database technology!",
            color=0x00ff88
        )

        embed.add_field(
            name="💻 Development",
            value="• Submit bug reports\n• Propose new features\n• Write documentation\n• Create examples",
            inline=False
        )

        embed.add_field(
            name="🧪 Testing",
            value="• Test new features\n• Report issues\n• Validate use cases\n• Performance testing",
            inline=False
        )

        embed.add_field(
            name="📚 Documentation",
            value="• Improve existing docs\n• Create tutorials\n• Write guides\n• Translate content",
            inline=False
        )

        embed.add_field(
            name="🌍 Community",
            value="• Help other users\n• Share your projects\n• Organize events\n• Spread the word",
            inline=False
        )

        embed.set_footer(text="Every contribution helps LuxDB evolve!")
        await ctx.send(embed=embed)

# Helper function to set up event handlers
def setup_event_handlers(bot):
    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        # Instantiate AdvancedBotFeatures to use its methods
        features = AdvancedBotFeatures(bot)
        await features.track_development_conversation(message)
        await features.moderate_message_content(message)

        # Ensure that command processing also happens
        await bot.process_commands(message)


# Function to setup advanced features, now using bot's setup_hook for async cog loading
def setup_advanced_features(bot):
    """Setup advanced Discord bot features"""
    print("🔧 Setting up advanced Discord bot features...")

    # Store the original setup_hook if it exists
    original_setup_hook = getattr(bot, 'setup_hook', None)

    async def enhanced_setup_hook():
        # Run original setup hook if it exists
        if original_setup_hook:
            await original_setup_hook()

        # Add the cog
        await bot.add_cog(AdvancedCommands(bot))
        print("✅ Advanced commands cog loaded")

    # Replace setup hook to include cog addition
    bot.setup_hook = enhanced_setup_hook

    # Setup event handlers
    setup_event_handlers(bot)

    print("✅ Advanced features configured")