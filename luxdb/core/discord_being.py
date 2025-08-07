
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
        embed.add_field(name="Response", value=f"Reply with: `@{being_ulid} your response`", inline=False)
        
        # Wyślij embed
        await channel.send(embed=embed)
        
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
