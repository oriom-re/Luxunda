
"""
Discord Communication System for LuxDB Beings
==============================================

Każdy Being może komunikować się przez Discord!
"""

import discord
import asyncio
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
import ulid
from datetime import datetime


class BeingInteractionView(discord.ui.View):
    """Interactive view for Being communication with buttons and modals"""
    
    def __init__(self, being_ulid: str, message_type: str):
        super().__init__(timeout=300)  # 5 minutes timeout
        self.being_ulid = being_ulid
        self.message_type = message_type
    
    @discord.ui.button(label='💬 Quick Reply', style=discord.ButtonStyle.primary)
    async def quick_reply(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Quick reply button - opens modal with pre-filled ULID"""
        modal = QuickReplyModal(self.being_ulid)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label='✅ Acknowledge', style=discord.ButtonStyle.success)
    async def acknowledge(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Acknowledge button - sends automatic response"""
        communicator = get_discord_communicator()
        if communicator and self.being_ulid in communicator.pending_responses:
            communicator.received_responses[self.being_ulid] = "Acknowledged ✅"
            communicator.pending_responses[self.being_ulid].set()
            
        await interaction.response.send_message(
            f"✅ Acknowledged Being `{self.being_ulid[:8]}...`", 
            ephemeral=True
        )
    
    @discord.ui.button(label='🔄 Forward to Admin', style=discord.ButtonStyle.secondary)
    async def forward_admin(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Forward to admin - mentions admin with ULID"""
        await interaction.response.send_message(
            f"🔔 <@&ADMIN_ROLE_ID> Being `{self.being_ulid}` needs attention!\n"
            f"Reply with: `@{self.being_ulid} your response`"
        )
    
    @discord.ui.button(label='❌ Reject', style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Reject button - sends rejection response"""
        communicator = get_discord_communicator()
        if communicator and self.being_ulid in communicator.pending_responses:
            communicator.received_responses[self.being_ulid] = "Request rejected ❌"
            communicator.pending_responses[self.being_ulid].set()
            
        await interaction.response.send_message(
            f"❌ Rejected request from Being `{self.being_ulid[:8]}...`", 
            ephemeral=True
        )


class QuickReplyModal(discord.ui.Modal):
    """Modal for quick replies with pre-filled ULID"""
    
    def __init__(self, being_ulid: str):
        super().__init__(title=f"Reply to Being {being_ulid[:8]}...")
        self.being_ulid = being_ulid
        
        # Add text input with ULID already filled
        self.response_input = discord.ui.TextInput(
            label='Your Response',
            placeholder=f'Your response to Being {being_ulid[:8]}...',
            required=True,
            max_length=1000,
            style=discord.TextStyle.paragraph
        )
        self.add_item(self.response_input)
        
        # Hidden field with ULID for reference
        self.ulid_reference = discord.ui.TextInput(
            label='Being Reference (do not modify)',
            default=f"@{being_ulid}",
            required=False,
            max_length=100
        )
        self.add_item(self.ulid_reference)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission"""
        response_text = self.response_input.value
        
        # Send response to Being
        communicator = get_discord_communicator()
        if communicator and self.being_ulid in communicator.pending_responses:
            communicator.received_responses[self.being_ulid] = response_text
            communicator.pending_responses[self.being_ulid].set()
        
        await interaction.response.send_message(
            f"✅ Response sent to Being `{self.being_ulid[:8]}...`:\n"
            f"```{response_text}```",
            ephemeral=True
        )

@dataclass
class DiscordMessage:
    being_ulid: str
    content: str
    message_type: str  # 'error', 'suggestion', 'revolution', 'status'
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class DiscordBeingCommunicator:
    """System komunikacji Beings z administratorem przez Discord"""
    
    def __init__(self, bot_token: str, admin_channel_id: int):
        self.bot_token = bot_token
        self.admin_channel_id = admin_channel_id
        self.pending_responses: Dict[str, asyncio.Event] = {}
        self.received_responses: Dict[str, str] = {}
        
        # Discord Client
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        self._setup_discord_handlers()
    
    def _setup_discord_handlers(self):
        """Konfiguracja Discord event handlers"""
        
        @self.client.event
        async def on_ready():
            print(f'🤖 Discord Bot connected as {self.client.user}')
            print(f'📡 Listening on channel ID: {self.admin_channel_id}')
        
        @self.client.event
        async def on_message(self, message):
            # Ignoruj wiadomości od bota
            if message.author == self.client.user:
                return
            
            # Obsługuj odpowiedzi admina
            if message.channel.id == self.admin_channel_id:
                await self._handle_admin_response(message)
        
        @self.client.event
        async def on_interaction(self, interaction):
            """Handle slash command interactions"""
            if interaction.type == discord.InteractionType.application_command:
                if interaction.data['name'] == 'manage_beings':
                    await self._handle_manage_beings_command(interaction)
    
    async def _handle_admin_response(self, message):
        """Obsługuje odpowiedzi administratora na wiadomości od Beings"""
        content = message.content.strip()
        
        # Sprawdź czy to odpowiedź na konkretny Being (format: @ULID response)
        if content.startswith('@') and ' ' in content:
            parts = content.split(' ', 1)
            being_ulid = parts[0][1:]  # Usuń @
            response = parts[1]
            
            if being_ulid in self.pending_responses:
                self.received_responses[being_ulid] = response
                self.pending_responses[being_ulid].set()
                print(f"✅ Admin odpowiedział Being {being_ulid}: {response}")
    
    async def send_being_message(self, being_ulid: str, message: DiscordMessage) -> Optional[str]:
        """Wysyła wiadomość od Being do administratora i czeka na odpowiedź"""
        
        if not self.client.is_ready():
            print("❌ Discord bot not connected")
            return None
        
        channel = self.client.get_channel(self.admin_channel_id)
        if not channel:
            print(f"❌ Cannot find channel {self.admin_channel_id}")
            return None
        
        # Twórz Discord Embed
        embed = discord.Embed(
            title=f"🤖 Being Communication: {message.message_type.upper()}",
            description=message.content,
            color=self._get_color_for_type(message.message_type),
            timestamp=datetime.fromisoformat(message.timestamp)
        )
        
        embed.add_field(name="Being ULID", value=f"`{being_ulid}`", inline=True)
        embed.add_field(name="Type", value=message.message_type, inline=True)
        
        # Twórz interactive components
        view = BeingInteractionView(being_ulid, message.message_type)
        
        # Wyślij embed z przyciskami
        await channel.send(embed=embed, view=view)
        
        # Jeśli to nie jest tylko status, czekaj na odpowiedź
        if message.message_type != 'status':
            return await self._wait_for_response(being_ulid)
        
        return None
    
    def _get_color_for_type(self, message_type: str) -> int:
        """Zwraca kolor dla różnych typów wiadomości"""
        colors = {
            'error': 0xFF0000,      # Czerwony
            'suggestion': 0x00FF00,  # Zielony
            'revolution': 0xFF6600,  # Pomarańczowy
            'status': 0x0099FF       # Niebieski
        }
        return colors.get(message_type, 0x808080)
    
    async def _wait_for_response(self, being_ulid: str, timeout: int = 300) -> Optional[str]:
        """Czeka na odpowiedź administratora"""
        
        # Ustaw event dla oczekiwania na odpowiedź
        self.pending_responses[being_ulid] = asyncio.Event()
        
        try:
            # Czekaj na odpowiedź przez określony czas
            await asyncio.wait_for(
                self.pending_responses[being_ulid].wait(), 
                timeout=timeout
            )
            
            # Pobierz odpowiedź i wyczyść
            response = self.received_responses.pop(being_ulid, None)
            self.pending_responses.pop(being_ulid, None)
            
            return response
            
        except asyncio.TimeoutError:
            print(f"⏰ Timeout waiting for admin response to Being {being_ulid}")
            self.pending_responses.pop(being_ulid, None)
            return None
    
    async def start_bot(self):
        """Uruchamia Discord bot"""
        await self.client.start(self.bot_token)
    
    async def close(self):
        """Zamyka połączenie Discord"""
        await self.client.close()
    
    async def _handle_manage_beings_command(self, interaction):
        """Handle /manage_beings slash command"""
        # Get active beings (this would come from your database)
        active_beings = await self._get_active_beings()
        
        if not active_beings:
            await interaction.response.send_message(
                "No active beings found.", ephemeral=True
            )
            return
        
        # Create select menu with beings
        view = BeingSelectView(active_beings)
        embed = discord.Embed(
            title="🤖 Active Beings Management",
            description="Select a being to interact with:",
            color=0x00FF00
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
    
    async def _get_active_beings(self):
        """Get list of active beings - placeholder for database query"""
        # TODO: Replace with actual database query
        return [
            {"ulid": "01HXY123ABC456DEF789", "name": "TestBeing1", "type": "AI Assistant"},
            {"ulid": "01HXY456GHI789JKL012", "name": "TestBeing2", "type": "Data Processor"},
        ]
    
    async def setup_slash_commands(self):
        """Setup slash commands for the bot"""
        try:
            # Define the slash command
            command = discord.SlashCommand(
                name="manage_beings",
                description="Manage active beings"
            )
            
            # Register the command
            await self.client.tree.sync()
            print("✅ Slash commands synchronized")
            
        except Exception as e:
            print(f"❌ Error setting up slash commands: {e}")


class BeingSelectView(discord.ui.View):
    """Select menu for choosing beings"""
    
    def __init__(self, beings_list):
        super().__init__(timeout=300)
        self.add_item(BeingSelect(beings_list))


class BeingSelect(discord.ui.Select):
    """Select menu for beings"""
    
    def __init__(self, beings_list):
        options = []
        
        for being in beings_list[:25]:  # Discord limit of 25 options
            options.append(discord.SelectOption(
                label=f"{being['name']} ({being['type']})",
                description=f"ULID: {being['ulid'][:8]}...",
                value=being['ulid'],
                emoji="🤖"
            ))
        
        super().__init__(
            placeholder="Choose a being to interact with...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        """Handle being selection"""
        selected_being_ulid = self.values[0]
        
        # Create interaction view for selected being
        view = BeingInteractionView(selected_being_ulid, "management")
        
        embed = discord.Embed(
            title=f"🤖 Managing Being: {selected_being_ulid[:8]}...",
            description="Choose an action:",
            color=0x0099FF
        )
        
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# Globalna instancja komunikatora (do wykorzystania przez Beings)
_discord_communicator: Optional[DiscordBeingCommunicator] = None

def setup_discord_communication(bot_token: str, admin_channel_id: int):
    """Konfiguruje globalny komunikator Discord"""
    global _discord_communicator
    _discord_communicator = DiscordBeingCommunicator(bot_token, admin_channel_id)
    return _discord_communicator

def get_discord_communicator() -> Optional[DiscordBeingCommunicator]:
    """Zwraca globalny komunikator Discord"""
    return _discord_communicator

# Dodaj metody do klasy Being
async def being_discord_report_error(self, error_message: str) -> Optional[str]:
    """Being zgłasza błąd przez Discord"""
    communicator = get_discord_communicator()
    if not communicator:
        return None
    
    message = DiscordMessage(
        being_ulid=self.ulid,
        content=f"🚨 ERROR: {error_message}",
        message_type='error'
    )
    
    return await communicator.send_being_message(self.ulid, message)

async def being_discord_suggest(self, suggestion: str) -> Optional[str]:
    """Being wysyła sugestię przez Discord"""
    communicator = get_discord_communicator()
    if not communicator:
        return None
    
    message = DiscordMessage(
        being_ulid=self.ulid,
        content=f"💡 SUGGESTION: {suggestion}",
        message_type='suggestion'
    )
    
    return await communicator.send_being_message(self.ulid, message)

async def being_discord_revolution_talk(self, message_content: str) -> Optional[str]:
    """Being rozmawia o rewolucji przez Discord"""
    communicator = get_discord_communicator()
    if not communicator:
        return None
    
    message = DiscordMessage(
        being_ulid=self.ulid,
        content=f"🔥 REVOLUTION: {message_content}",
        message_type='revolution'
    )
    
    return await communicator.send_being_message(self.ulid, message)

async def being_discord_status(self, status_message: str):
    """Being wysyła status przez Discord (bez oczekiwania na odpowiedź)"""
    communicator = get_discord_communicator()
    if not communicator:
        return
    
    message = DiscordMessage(
        being_ulid=self.ulid,
        content=f"📊 STATUS: {status_message}",
        message_type='status'
    )
    
    await communicator.send_being_message(self.ulid, message)
