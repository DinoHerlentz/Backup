import nextcord
import cooldowns
import io
import contextlib
import os
import json
import traceback
import asyncio
import random
import requests
import datetime
import time
import humanfriendly
import wavelink
import animec
import aiosqlite
import aiohttp
import psutil
from bs4 import BeautifulSoup
from traceback import format_exception
from aioconsole import ainput
from googlesearch import search
from imdb import IMDb
from wavelink.ext import spotify
from async_timeout import timeout
from io import BytesIO
from cooldowns import CallableOnCooldown
from nextcord.ext import commands, tasks, activities, application_checks
from nextcord.ext.application_checks import ApplicationNotOwner, ApplicationMissingPermissions, ApplicationMissingRole, ApplicationMissingAnyRole, ApplicationBotMissingPermissions, ApplicationBotMissingRole, ApplicationBotMissingAnyRole, ApplicationNSFWChannelRequired, ApplicationNoPrivateMessage, ApplicationPrivateMessageOnly
from nextcord.abc import GuildChannel
from nextcord import Interaction, SlashOption, SelectOption, ChannelType
from nextcord.abc import GuildChannel
from nextcord.ext.commands import CommandNotFound, BadArgument, MissingPermissions, MissingRequiredArgument, BotMissingPermissions, CommandOnCooldown, DisabledCommand, MemberNotFound
from config import TOKEN, API_KEY


intents = nextcord.Intents.all()
# intents.members = True
# intents.message_content = True
bot = commands.Bot(command_prefix = ".", intents = intents, case_insensitive = True)
cats = json.load(open("C:/Veldora/venv/cat_gifs.json"))
lyrics_url = "https://some-random-api.ml/lyrics?title="
snipe_message_content = None
snipe_message_author = None


# Class
class NoLyricsFound(commands.CommandError):
    pass


class ControlPanel(nextcord.ui.View):
    def __init__(self, vc, ctx: commands.Context):
        super().__init__()
        self.vc = vc
        self.ctx = ctx
    
    
    @nextcord.ui.button(label = "Resume/Pause", style = nextcord.ButtonStyle.blurple)
    async def resume_and_pause(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.ctx.author:
            return await interaction.user.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        if self.vc.is_paused():
            await self.vc.resume()
            await interaction.message.edit(content = "Resumed", view = self)
        
        else:
            await self.vc.pause()
            await interaction.message.edit(content = "Paused", view = self)
    
    
    @nextcord.ui.button(label = "Queue", style = nextcord.ButtonStyle.blurple)
    async def queue(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.ctx.author:
            return await interaction.response.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        button.disabled = True
        
        if self.vc.queue.is_empty:
            return await interaction.response.send_message("The queue is empty.", ephemeral = True)
        
        em = nextcord.Embed(title = "Queue")
        queue = self.vc.queue.copy()
        songCount = 0
        
        for song in queue:
            songCount += 1
            em.add_field(name = f"Queue number {str(songCount)}", value = f"{song}", inline = False)
        
        await interaction.message.edit(embed = em, view = self)
    
    
    """
    @nextcord.ui.button(label = "Skip", style = nextcord.ButtonStyle.blurple)
    async def skip(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.ctx.author:
            return await interaction.response.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        button.disabled = True
        
        if self.vc.queue.is_empty and not self.vc.is_playing():
            return await interaction.response.send_message("The queue is empty.", ephemeral = True)
        
        try:
            next_song = self.vc.queue.get()
            await self.vc.play(next_song)
            
            await interaction.message.edit(content = f"Now playing -> `{next_song}`", view = self)
        
        except Exception:
            return await interaction.response.send_message("The queue is empty.", ephemeral = True)
    """
    
    
    @nextcord.ui.button(label = "Disconnect", style = nextcord.ButtonStyle.red)
    async def disconnect(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.ctx.author:
            return await interaction.response.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = True
        
        await self.vc.disconnect()
        await interaction.message.edit(content = "Successfully left the voice channel.", view = self)


class ControlPanelII(nextcord.ui.View):
    def __init__(self, vc, interaction: Interaction):
        super().__init__()
        self.vc = vc
        self.interaction = interaction
    
    
    @nextcord.ui.button(label = "Resume/Pause", style = nextcord.ButtonStyle.blurple)
    async def resume_and_pause(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.interaction.user:
            return await interaction.user.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        if self.vc.is_paused():
            await self.vc.resume()
            await interaction.message.edit(content = "Resumed", view = self)
        
        else:
            await self.vc.pause()
            await interaction.message.edit(content = "Paused", view = self)
    
    
    @nextcord.ui.button(label = "Queue", style = nextcord.ButtonStyle.blurple)
    async def queue(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.interaction.user:
            return await interaction.response.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        button.disabled = True
        
        if self.vc.queue.is_empty:
            return await interaction.response.send_message("The queue is empty.", ephemeral = True)
        
        em = nextcord.Embed(title = "Queue")
        queue = self.vc.queue.copy()
        songCount = 0
        
        for song in queue:
            songCount += 1
            em.add_field(name = f"Queue number {str(songCount)}", value = f"{song}", inline = False)
        
        await interaction.message.edit(embed = em, view = self)
    
    
    """
    @nextcord.ui.button(label = "Skip", style = nextcord.ButtonStyle.blurple)
    async def skip(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.interaction.user:
            return await interaction.response.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = False
        
        button.disabled = True
        
        
        if self.vc.queue.is_empty and not self.vc.is_playing():
            return await interaction.response.send_message("The queue is empty.", ephemeral = True)
        
        try:
            next_song = self.vc.queue.get()
            await self.vc.play(next_song)
            
            await interaction.message.edit(content = f"Now playing -> `{next_song}`", view = self)
        
        except Exception:
            return await interaction.response.send_message("The queue is empty.", ephemeral = True)
    """
    
    
    @nextcord.ui.button(label = "Disconnect", style = nextcord.ButtonStyle.red)
    async def disconnect(self, button: nextcord.ui.Button, interaction: Interaction):
        if not interaction.user == self.interaction.user:
            return await interaction.response.send_message("This panel isn't yours.", ephemeral = True)
        
        for child in self.children:
            child.disabled = True
        
        await self.vc.disconnect()
        await interaction.message.edit(content = "Successfully left the voice channel.", view = self)


class Embed(nextcord.ui.Modal):
    def __init__(self):
        super().__init__("Embed Maker")

        self.emTitle = nextcord.ui.TextInput(label = "Embed Title", min_length = 2, max_length = 124, required = True, placeholder = "Enter Embed Title")
        self.add_item(self.emTitle)

        self.emDesc = nextcord.ui.TextInput(label = "Embed Description", min_length = 5, max_length = 4000, required = True, placeholder = "Enter Embed Description", style = nextcord.TextInputStyle.paragraph)
        self.add_item(self.emDesc)

    async def callback(self, interaction: Interaction) -> None:
        title = self.emTitle.value
        desc = self.emDesc.value

        em = nextcord.Embed(title = title, description = desc)
        em.timestamp = datetime.datetime.utcnow()
        
        return await interaction.response.send_message(embed = em)


# Function
def clean_code(content):
    if content.startswith("```") and content.endswith("```"):
        return "\n".join(content.split("\n")[1:])[:-3]
    
    else:
        return content


def is_me():
    def predicate(interaction: Interaction):
        return interaction.user.id == 55058884670678630
    
    return application_checks.check(predicate)


# Event Decorator
@bot.event
async def on_ready():
    await bot.change_presence(status = nextcord.Status.idle, activity = nextcord.Game(".help"))
    print("We have logged in as {0.user}".format(bot))

    # Music
    bot.loop.create_task(node_connect())


@bot.event
async def on_reaction_add(reaction, user):
    if str(reaction.emoji) == "🗑️":
        await nextcord.Message.delete(reaction.message)


@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f"Node {node.identifier} is ready.")

async def node_connect():
    await bot.wait_until_ready()
    node: wavelink.Node = wavelink.Node(uri = 'http://lavalink.clxud.pro:2333', password = "youshallnotpass")
    node = wavelink.NodePool.get_node()
    await wavelink.NodePool.connect(client = bot, nodes = [node])
    
    # await wavelink.NodePool.create_node(bot = bot, host = "lavalinkinc.invalid-studios.com", password = "invaliduser", https = True, spotify_client = spotify.SpotifyClient(client_id = "975981c3179a436883021b5ac45f352f", client_secret = "8aa73f51cebf4c1e924303e3558ea6fa"))

@bot.event
async def on_wavelink_track_end(player: wavelink.Player, track: wavelink.YouTubeTrack, reason):
    try:
        ctx = player.ctx
        vc: player = ctx.voice_client
    
    except nextcord.HTTPException:
        interaction = player.interaction
        vc: player = interaction.guild.voice_client
    
    if vc.loop:
        return await vc.play(track)
    
    elif vc.queue.is_empty:
        return await vc.disconnect()

    
    try:
        next_song = vc.queue.get()
        await vc.play(next_song)
    
    except wavelink.errors.QueueEmpty:
        pass

    try:
        await ctx.send(f"Now playing -> `{next_song.title}`")
    
    except nextcord.HTTPException:
        await interaction.send(f"Now playing -> `{next_song.title}`")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.reply("This command is still on cooldown. Try again in `{:2f}` second(s).".format(error.retry_after), mention_author = False)


@bot.event
async def on_application_command_error(interaction: Interaction, error):
    if isinstance(error, application_checks.ApplicationNotOwner):
        await interaction.send("This command is restricted for bot owners only.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationMissingPermissions):
        await interaction.send("Missing required permission.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationMissingRole):
        await interaction.send("Missing role.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationMissingAnyRole):
        await interaction.send("Missing any role.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationBotMissingPermissions):
        await interaction.send("Bot missing permissions.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationBotMissingRole):
        await interaction.send("Bot missing role.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationBotMissingAnyRole):
        await interaction.send("Bot missing any role.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationNSFWChannelRequired):
        await interaction.send("NSFW channel required.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationNoPrivateMessage):
        await interaction.send("No private message.", ephemeral = True)

    elif isinstance(error, application_checks.ApplicationPrivateMessageOnly):
        await interaction.send("Private message only.", ephemeral = True)

    error = getattr(error, "original", error)

    if isinstance(error, CallableOnCooldown):
        await interaction.send(f"This command is still on cooldown. Try again in `{error.retry_after}` second(s).", ephemeral = True)


"""
@bot.event
async def on_message(message):
    username = str(message.author).split("#")[0]
    user_message = str(message.content)
    channel = str(message.channel.name)
    guild = str(message.guild.name)
    guild_id = str(message.guild.id)
    
    print(f"{username} : {user_message} ({channel}) ({guild}) ({guild_id})")
"""


@bot.event
async def on_message_delete(message):
    global snipe_message_content
    global snipe_message_author

    snipe_message_content = message.content
    snipe_message_author = message.author.name
    
    await asyncio.sleep(60)
    
    snipe_message_author = None
    snipe_message_content = None


# Group Command
@bot.group(invoke_without_command = True)
async def cat(ctx: commands.Context):
    return


# Music Command
@bot.command(name = "panel", description = "Control the music with button interaction")
async def panel(ctx: commands.Context):
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.chanel.connect(cls = wavelink.Player)
    
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.", mention_author = False)
    
    else:
        vc: wavelink.Player = ctx.voice_client
    
    em = nextcord.Embed(title = "Music Panel", description = "Control the music with button interaction")
    view = ControlPanel(vc, ctx)
    
    await ctx.send(embed = em, view = view)


@bot.slash_command(name = "panel", description = "Control the music with button interaction")
async def panel(interaction: Interaction):
    if not interaction.guild.voice_client:
        vc: wavelink.Player = await interaction.user.voice.channel.connect(cls = wavelink.Player)
    
    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)
    
    else:
        vc: wavelink.Player = interaction.guild.voice_client
    
    em = nextcord.Embed(title = "Music Panel", description = "Control the music with button interaction")
    view = ControlPanelII(vc, interaction)
    
    await interaction.send(embed = em, view = view)


@bot.command(name = "play", description = "Play a music", aliases = ['p'])
async def play(ctx: commands.Context, *, query: wavelink.YouTubeTrack):
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls = wavelink.Player)
    
    elif not getattr(ctx.author.voice, "channel", None):
        await ctx.reply("You aren't connected to the voice channel.")
    
    else:
        vc: wavelink.Player = ctx.voice_client
    
    if vc.queue.is_empty and not vc.is_playing():
        await vc.play(query)
        await ctx.send(f"Now playing -> `{query.title}`")
    
    else:
        await vc.queue.put_wait(query)
        await ctx.send(f"Added `{query.title}` to the queue.")
    
    vc.ctx = ctx
    setattr(vc, "loop", False)

@bot.slash_command(name = "play", description = "Play a music in a voice channel")
async def play(interaction: Interaction, channel: GuildChannel = SlashOption(channel_types=[ChannelType.voice], description = "Select voice channel"), query: str = SlashOption(description = "Enter music name")):
    query = await wavelink.YouTubeTrack.search(query = query, return_first = True)

    if not interaction.guild.voice_client:
        vc: wavelink.Player = await channel.connect(cls = wavelink.Player)
    
    elif not getattr(interaction.user.voice, "channel", None):
        await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    if vc.queue.is_empty and not vc.is_playing():
        await vc.play(query)
        await interaction.send(f"Now playing -> `{query.title}`")

    else:
        await vc.queue.put_wait(query)
        await interaction.send(f"Added `{query.title}` to the queue.")

    vc.interaction = interaction
    setattr(vc, "loop", False)


@bot.command(name = "spotifyplay", description = "Play a music from spotify", aliases = ['spotify', 'sp', 'splay'])
async def spotifyplay(ctx: commands.Context, *, url: str):
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls = wavelink.Player)
    
    elif not getattr(ctx.voice.author, "channel", None):
        await ctx.reply("You aren't connected to the voice channel.")
    
    else:
        vc: wavelink.Player = ctx.voice_client
    
    if vc.queue.is_empty and not vc.is_playing():
        try:
            decodeURL = spotify.decode_url(url)
            track = await spotify.SpotifyTrack.search(query = decodeURL['id'], return_first = True)

            await vc.play(track)
            await ctx.send(f"Now playing -> `{track.title}`")
        
        except Exception as err:
            await ctx.reply("Please insert a spotify song URL.")
            print(err)
    
    else:
        await vc.queue.put_wait(track)
        await ctx.send(f"Added `{track.title}` to the queue.")
    
    vc.ctx = ctx

    if vc.loop:
        return
    
    setattr(vc, "loop", False)


@bot.slash_command(name = "spotifyplay", description = "Play a song from spotify")
async def splay(interaction: Interaction, *, url: str):
    if not interaction.guild.voice_client:
        vc: wavelink.Player = await interaction.user.voice.channel.connect(cls = wavelink.Player)
    
    elif not getattr(interaction.user.voice, "channel", None):
        await interaction.send("You aren't connected to the voice channel.", ephemeral = True)
    
    else:
        vc: wavelink.Player = interaction.guild.voice_client
    
    if vc.queue.is_empty and not vc.is_playing():
        try:
            decodeURL = spotify.decode_url(url)
            track = await spotify.SpotifyTrack.search(query = decodeURL['id'], return_first = True)

            await vc.play(track)
            await interaction.send(f"Now playing -> `{track.title}`")
        
        except Exception as err:
            await interaction.send("Please insert a spotify song URL.")
            print(err)
    
    else:
        await vc.queue.put_wait(track)
        await interaction.send(f"Now playing -> `{track.title}`")
    
    vc.interaction = interaction

    if vc.loop:
        return
    
    setattr(vc, "loop", False)


@bot.command(name = "pause", description = "Pause current playing music")
async def pause(ctx: commands.Context):
    if not ctx.voice_client:
        await ctx.reply("I'm not in a voice channel.")

    elif not getattr(ctx.author.voice, "channel", None):
        await ctx.reply("You aren't connected to the voice channel.")

    else:
        vc: wavelink.Player = ctx.voice_client

    await vc.pause()
    await ctx.reply("Successfully paused the music.")


@bot.slash_command(name = "pause", description = "Pause current playing music")
async def pause(interaction: Interaction):
    if not interaction.guild.voice_client:
        await interaction.send("I'm not in the voice channel.", ephemeral = True)
    
    elif not getattr(interaction.user.voice, "channel", None):
        await interaction.send("You aren't connected to the voice channel.", ephemeral = True)
    
    else:
        vc: wavelink.Player = interaction.guild.voice_client

    await vc.pause()
    await interaction.send("Successfully paused the music.")


@bot.command(name = "resume", description = "Resume current paused music", aliases = ['r'])
async def resume(ctx: commands.Context):
    if not ctx.voice_client:
        await ctx.reply("I'm not in a voice channel.")

    elif not getattr(ctx.author.voice, "channel", None):
        await ctx.reply("You aren't connected to the voice channel.")

    else:
        vc: wavelink.Player = ctx.voice_client

    await vc.resume()
    await ctx.reply("Successfully resumed the music.")


@bot.slash_command(name = "resume", description = "Resume current paused music")
async def resume(interaction: Interaction):
    if not interaction.guild.voice_client:
        await interaction.send("I'm not in the voice channel.", ephemeral = True)
    
    elif not getattr(interaction.user.voice, "channel", None):
        await interaction.send("You aren't connected to the voice channel.", ephemeral = True)
    
    else:
        vc: wavelink.Player = interaction.guild.voice_client

    await vc.resume()
    await interaction.send("Successfully resumed the music.")


@bot.command(name = "stop", description = "stop current playing music", aliases = ['s'])
async def stop(ctx: commands.Context):
    if not ctx.voice_client:
        await ctx.reply("I'm not in a voice channel.")

    elif not getattr(ctx.author.voice, "channel", None):
        await ctx.reply("You aren't connected to the voice channel.")

    else:
        vc: wavelink.Player = ctx.voice_client

    await vc.stop()
    await ctx.reply("Successfully stop the music")


@bot.slash_command(name = "stop", description = "Stop current playing music")
async def stop(interaction: Interaction):
    if not interaction.guild.voice_client:
        await interaction.send("I'm not connected to the voice channel.", ephemeral = True)
    
    elif not getattr(interaction.user.voice, "channel", None):
        await interaction.send("You aren't connected to the voice channel.", ephemeral = True)
    
    else:
        vc: wavelink.Player = interaction.guild.voice_client

    await vc.stop()
    await interaction.send("Successfully stop the music.")


@bot.command(name = "disconnect", description = "Disconnect the bot from the voice channel", aliases = ['dc'])
@commands.has_permissions(administrator = True)
async def disconnect(ctx: commands.Context):
    if not getattr(ctx.author.voice, "channel", None):
        await ctx.reply("You aren't connected to the voice channel.")

    else:
        vc: wavelink.Player = ctx.voice_client

    await vc.disconnect()
    await ctx.reply("Successfully left the voice channel")


@bot.slash_command(name = "disconnect", description = "Disconnect the bot from the voice channel.")
@application_checks.has_permissions(administrator = True)
async def disconnect(interaction: Interaction):
    if not getattr(interaction.user.voice, "channel", None):
        await interaction.send("You aren't connected to the voice channel.", ephemeral = True)
    
    else:
        vc: wavelink.Player = interaction.guild.voice_client

    await vc.disconnect()
    await interaction.send("Successfully left the voice channel.")


@bot.command(name = "loop", description = "Toggle music loop")
async def loop(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.reply("I'm not in a voice channel.")
    
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.")
    
    else:
        vc: wavelink.Player = ctx.voice_client

    try:
        vc.loop ^= True
    
    except Exception:
        setattr(vc, "loop", False)

    if vc.loop:
        await ctx.reply("Music loop has been enabled.")
    
    else:
        await ctx.reply("Music loop has been disabled.")


@bot.slash_command(name = "loop", description = "Toggle music loop")
async def loop(interaction: Interaction):
    if not interaction.guild.voice_client:
        return await interaction.send("I'm not in a voice channel.", ephemeral = True)
    
    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.send("You aren't connected to the voice channel.", ephemeral = True)

    else:
        vc: wavelink.Player = interaction.guild.voice_client

    try:
        vc.loop ^= True
    
    except Exception:
        setattr(vc, "loop", False)

    if vc.loop:
        await interaction.send("Music loop has been enabled.")
    
    else:
        await interaction.send("Music loop has been disabled.")


@bot.command(name = "queue", description = "Shows music queue", aliases = ['q'])
async def queue(ctx: commands.Context):
    if not ctx.voice_client:
        await ctx.reply("I'm not in a voice channel.")
    
    elif not getattr(ctx.author.voice, "channel", None):
        await ctx.reply("You aren't connected to the voice channel.")

    else:
        vc: wavelink.Player = ctx.voice_client

    if vc.queue.is_empty:
        await ctx.reply("The queue is empty.")
    
    else:
        em = nextcord.Embed(title = "Queue")
        queue = vc.queue.copy()
        song_count = 0
    
        for song in queue:
            song_count += 1
            em.add_field(name = f"Queue Number {str(song_count)}", value = f"{song}")
    
        await ctx.send(embed = em)


@bot.slash_command(name = "queue", description = "Shows music queue")
async def queue(interaction: Interaction):
    if not interaction.guild.voice_client:
        await interaction.send("I'm not connected to the voice channel.", ephemeral = True)
    
    elif not getattr(interaction.user.voice, "channel", None):
        await interaction.send("You aren't connected to the voice channel.", ephemeral = True)
    
    else:
        vc: wavelink.Player = interaction.guild.voice_client

    if vc.queue.is_empty:
        await interaction.send("Queue is empty.")
    
    else:
        em = nextcord.Embed(title = "Queue")
        queue = vc.queue.copy()
        song_count = 0

        for song in queue:
            song_count += 1
            em.add_field(name = f"Queue Number {str(song_count)}", value = f"{song}")

        await interaction.send(embed = em)


@bot.command(name = "volume", description = "Change music volume")
async def volume(ctx: commands.Context, volume: int):
    if not ctx.voice_client:
        return await ctx.reply("I'm not in the voice channel.")
    
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.")
    
    else:
        vc: wavelink.Player = ctx.voice_client
    
    if volume > 100:
        return await ctx.reply("Max volume is 100.")
    
    elif volume < 0:
        return await ctx.reply("Min volume is 0.")
    
    await ctx.send(f"Successfully changed music volume to `{volume}%`")
    return await vc.set_volume(volume)

@bot.command(name = "nowplaying", description = "Shows current playing music info", aliases = ['np', 'cp', 'currentplay', 'currentplaying'])
async def nowplaying(ctx: commands.Context):
    if not ctx.voice_client:
        await ctx.reply("I'm not in the voice channel.")
    
    elif not getattr(ctx.author.voice, "channel", None):
        await ctx.reply("You aren't connected to the voice channel.")

    else:
        vc: wavelink.Player = ctx.voice_client

    if not vc.is_playing():
        await ctx.reply("There is no current playing music.")
    
    else:
        em = nextcord.Embed(title = f"Now Playing -> {vc.track.title}", description = f"Artist : {vc.track.author}")
        em.add_field(name = "Duration", value = f"`{str(datetime.timedelta(seconds=vc.track.length))}`")
        em.add_field(name = "Song Info", value = f"Song URL : [Click Here]({str(vc.track.uri)})")
        await ctx.send(embed = em)


@bot.slash_command(name = "nowplaying", description = "Shows current playing music info")
async def nowplaying(interaction: Interaction):
    if not interaction.guild.voice_client:
        await interaction.send("I'm not in the voice channel.", ephemeral = True)
    
    elif not getattr(interaction.user.voice, "channel", None):
        await interaction.send("You aren't connected to the voice channel.", ephemeral = True)
    
    else:
        vc: wavelink.Player = interaction.guild.voice_client

    if not vc.is_playing():
        await interaction.send("There is no current playing music.")
    
    else:
        em = nextcord.Embed(title = f"Now Playing -> {vc.track.title}", description = f"Artist : {vc.track.author}")
        em.add_field(name = "Duration", value = f"`{str(datetime.timedelta(seconds=vc.track.length))}`")
        em.add_field(name = "Song Info", value = f"Song URL : [Click Here]({str(vc.track.uri)})")
        await interaction.send(embed = em)


@bot.command(name = "lyrics", description = "Get the current playing music lyrics", aliases = ["l"])
async def lyrics(ctx: commands.Context):
    if not ctx.voice_client:
        return await ctx.reply("I'm not in the voice channel.")
    
    elif not getattr(ctx.author.voice, "channel", None):
        return await ctx.reply("You aren't connected to the voice channel.")
    
    else:
        vc: wavelink.Player = ctx.voice_client

    song = vc.track.title

    async with ctx.typing():
        async with aiohttp.request("GET", lyrics_url + song, headers = {}) as r:
            if not 200 <= r.status <= 299:
                raise NoLyricsFound
    
            data = await r.json()

            await ctx.send(f"<{data['links']['genius']}>")

            
            if len(data['lyrics']) > 2000:
                await ctx.send(f"<{data['links']['genius']}>")
            
            em = nextcord.Embed(title = data['title'], description = data['lyrics'])
            em.set_thumbnail(url = data['thumbnail']['genius'])
            em.set_author(name = data['author'])
            em.timestamp = ctx.message.created_at
    
            await ctx.send(embed = em)


@bot.slash_command(name = "lyrics", description = "Get the current playing music lyrics")
async def lyrics(interaction: Interaction):
    if not interaction.guild.voice_client:
        return await interaction.reply("I'm not in the voice channel.")
    
    elif not getattr(interaction.user.voice, "channel", None):
        return await interaction.reply("You aren't connected to the voice channel.")
    
    else:
        vc: wavelink.Player = interaction.guild.voice_client

    song = vc.track.title

    async with interaction.channel.typing():
        async with aiohttp.request("GET", lyrics_url + song, headers = {}) as r:
            if not 200 <= r.status <= 299:
                raise NoLyricsFound
    
            data = await r.json()

            await interaction.send(f"<{data['links']['genius']}>")

            
            if len(data['lyrics']) > 2000:
                await interaction.send(f"<{data['links']['genius']}>")
            
            em = nextcord.Embed(title = data['title'], description = data['lyrics'])
            em.set_thumbnail(url = data['thumbnail']['genius'])
            em.set_author(name = data['author'])
            em.timestamp = datetime.datetime.utcnow()
    
            await interaction.send(embed = em)


# Help Command
"""
@bot.command(description = "Get some informations about the bot command", aliases = ['.', 'halp'])
async def help(ctx):
    em = nextcord.Embed(title = "Commands (.)")

    for command in bot.walk_commands():
        description = command.description

        if not description or description is None or description == "":
            description = "No Description Provided."
        
        em.add_field(name = f"`{command.name}{command.signature if command.signature is not None else ''}`", value = description)
    
    await ctx.send(embed = em)
"""


# Basic Command
@bot.command(name = "ping", description = "Shows bot latency")
async def ping(ctx: commands.Context):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")


@bot.slash_command(name = "ping", description = "Shows bot latency")
async def ping(interaction: Interaction):
    await interaction.send(f"Pong! {round(bot.latency * 1000)}ms")


# Moderation Command
@bot.command(name = "purge", description = "Clear a message", aliases = ['clear', 'cls'])
@commands.has_permissions(manage_messages = True)
async def purge(ctx: commands.Context, amount, arg: str = None):
    await ctx.message.delete()
    await ctx.channel.purge(limit = int(amount))


@bot.command(name = "snipe", description = "Snipe latest deleted message in a channel")
async def snipe(ctx: commands.Context):
    if snipe_message_content == None:
        await ctx.reply("There's nothing to snipe")

    else:
        em = nextcord.Embed(title = f"Last deleted message in #{ctx.channel.name}", description = f"{snipe_message_content}")
        em.set_footer(text = f"Sniped by {ctx.author} | Deleted by {snipe_message_author}", icon_url = ctx.author.avatar.url)
        em.timestamp = ctx.message.created_at

        await ctx.send(embed = em)


@bot.slash_command(name = "snipe", description = "Snipe latest deleted message in a channel")
async def snipe(interaction: Interaction):
    if snipe_message_content == None:
        await interaction.send("There's nothing to snipe")

    else:
        em = nextcord.Embed(title = f"Last deleted message in #{interaction.channel.name}", description = f"{snipe_message_content}")
        em.set_footer(text = f"Sniped by {interaction.user} | Deleted by {snipe_message_author}", icon_url = interaction.user.avatar.url)
        em.timestamp = datetime.datetime.utcnow()

        await interaction.send(embed = em)


# Testing Command
@bot.command()
async def weather(ctx: commands.Context, *, city):
    url = "https://api.weatherapi.com/v1/current.json"
    
    params = {
        "key": "73602374fbea4e7fbeb135655231903",
        "q": city,
        
    }
    
    async with aiohttp.ClientSession() as ses:
        async with ses.get(url, params = params) as res:
            data = await res.json()
            
            location = data['location']['name']
            temp_c = data['current']['temp_c']
            temp_f = data['current']['temp_f']
            humidity = data['current']['humidity']
            wind_kph = data['current']['wind_kph']
            wind_mph = data['current']['wind_mph']
            condition = data['current']['condition']['text']
            image_url = "http" + data['current']['condition']['icon']
            
            em = nextcord.Embed(title = f"{location} Weather Information", description = f"Current condition in `{location}` is `{condition}`")
            # em.set_thumbnail(url = image_url)
            em.add_field(name = "Temperature", value = f"C : {temp_c}°C | F : {temp_f}°F", inline = False)
            em.add_field(name = "Humidity", value = f"{humidity}", inline = False)
            em.add_field(name = "Wind Speed", value = f"KPH : {wind_kph} | MPH : {wind_mph}", inline = False)
            
            await ctx.send(embed = em)


@bot.command()
async def gpt(ctx: commands.Context, *, prompt: str):
    async with aiohttp.ClientSession() as session:
        payload = {
            "model": "text-davinci-003",
            "prompt": prompt,
            "temperature": 0.5,
            "max_tokens": 50,
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "best_of": 1,
        }
        
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        async with session.post("https://api.openapi.com/v1/completions", json = payload, headers = headers) as resp:
            response = await resp.json()
            
            em = nextcord.Embed(title = "Chat GPT's Response : ", description = response['choices'][0]['text'])
            await ctx.reply(embed = em)


@bot.command()
async def capybara(ctx: commands.Context):
    res = requests.get("https://api.capy.lol/v1/capybara?json=true")
    r = res.json()['data']['url']
    await ctx.send(r)


@bot.command()
async def status(ctx: commands.Context, member: nextcord.User = None):
    if member == None:
        member = ctx.author
    
    if member.activities[1].name == None:
        await ctx.send("This user has no status activities")
    else:
        await ctx.send(member.activities[1].name)


"""
@bot.command()
async def ci(ctx: commands.Context, channel: nextcord.TextChannel):
    em = nextcord.Embed(title = f"Channel Info - {channel}")
    em.add_field(name = "ID", description = channel.id, inline = False)
    em.add_field(name = "Topic", value = f"{channel.topic if channel.topic else None}", inline = False)
    em.add_field(name = "Position", value = channel.position, inline = False)
    em.add_field(name = "Slowmode", value = f"{channel.slowmode_delay}s", inline = False)
    em.add_field(name = "News Channel", value = channel.is_nsfw, inline = False)
    em.add_field(name = "News Channel", value = channel.is_news(), inline = False)
    em.add_field(name = "Created At", value = channel.created_at, inline = False)
    em.add_field(name = "Permissions Synced", value = channel.permissions_synced, inline = False)
    
    await ctx.send(embed = em)
"""


@bot.command(aliases = ['color'])
async def invis(ctx: commands.Context):
    em = nextcord.Embed(title = "Title", description = "Description", color = 0x36393E)
    await ctx.send(embed = em)


@bot.command(name = "robbo", description = "Bot")
async def robbo(ctx: commands.Context):
    bots = [bot.mention for bot in ctx.guild.members if bot.bot]
    
    await ctx.send(", ".join(bots))


@bot.command(name = "google", description = "Search anything in google", aliases = ['find'])
async def google(ctx: commands.Context, *, query):
    await ctx.reply(f"Searching **{query}**...")
    
    async with ctx.typing():
        for j in search(query, tld = "co.in", num = 1, stop = 1, pause = 2):
            await ctx.send(f"{j}")


@bot.slash_command(name = "google", description = "Search anything in google")
async def google(interaction: Interaction, *, query):
    await interaction.send(f"Searching **{query}**...")
    
    async with interaction.channel.typing():
        for j in search(query, tld = "co.in", num = 1, stop = 1, pause = 2):
            await interaction.send(f"{j}")


@bot.user_command(name = "Test")
async def test(interaction: Interaction, member: nextcord.Member):
    await interaction.send(f"Hello {member.mention} (from {interaction.user.mention})")


@cat.command(name = "image", description = "Get some random cute cat pictures")
async def image(ctx: commands.Context):
    r = requests.get("https://aws.random.cat/meow")
    res = r.json()['file']
    await ctx.send(res)


@cat.command(name = "gif", description = "Get some random cat GIFs")
async def gif(ctx: commands.Context):
    async def dropdown_callback(interaction):
        for value in dropdown.values:
            await ctx.send(random.choice(cats[value]))
    
    op1 = SelectOption(label = "GIF", value = "gif", description = "Random cat GIFs")
    op2 = SelectOption(label = "Play", value = "play", description = "Random playing cat GIFs")
    op3 = SelectOption(label = "Eat", value = "eat", description = "Random eating cat GIFs")
    op4 = SelectOption(label = "Sleep", value = "sleep", description = "Random sleeping cat GIFs")
    dropdown = nextcord.ui.Select(placeholder = "Choose any", options = [op1, op2, op3, op4], max_values = 4)
    
    dropdown.callback = dropdown_callback
    view = nextcord.ui.View(timeout = None)
    view.add_item(dropdown)
    
    await ctx.send("Here's some of the cat GIFs.", view = view)


# Owner Command
@bot.command(name = "eval", description = "Run python code (owner only)", aliases = ["e"])
@commands.is_owner()
async def eval(ctx: commands.Context, *, code):
    code = clean_code(code)
    str_obj = io.StringIO()

    try:
        with contextlib.redirect_stdout(str_obj):
            exec(code)

    except Exception as e:
        em = nextcord.Embed(title = "❌ Error ❌", description = "```py\n" + "".join(format_exception(e.__class__, e, e.__traceback__)) + "```", color = nextcord.Color.red())
        return await ctx.send(embed = em)

    await ctx.send(f"```py\n{str_obj.getvalue()}```")


bot.run(TOKEN)
# bot.run("ODgyMDk3OTg4MTE2Mjk5ODE2.GoECA6.2mzDke45892afo-68CzwYZQOBrFpi8UgWO-st4")