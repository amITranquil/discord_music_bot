import discord
from discord.ext import commands
import yt_dlp
import asyncio
import logging
from typing import Optional, Dict

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('discord_bot')

# YT-DLP options
YDL_OPTS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'no_warnings': True,
    'extractaudio': True,
    'default_search': 'ytsearch',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'socket_timeout': 10,
}

# FFmpeg options
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -analyzeduration 0 -loglevel 0',
    'options': '-vn -bufsize 2048k'
}

class Track:
    def __init__(self, url: str, title: str):
        self.url = url
        self.title = title

class MusicQueue:
    def __init__(self):
        self.queue: list[Track] = []
        self.volume: float = 1.0
        self.now_playing: Optional[Track] = None
        self.leave_timer: Optional[asyncio.Task] = None
        self.text_channel: Optional[discord.TextChannel] = None
        self.is_leaving: bool = False

    def add(self, track: Track) -> None:
        self.queue.append(track)

    def next(self) -> Optional[Track]:
        return self.queue.pop(0) if self.queue else None

    def clear(self) -> None:
        self.queue.clear()
        self.now_playing = None

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix='!', intents=intents)

queues: Dict[int, MusicQueue] = {}

def get_queue(guild_id: int) -> MusicQueue:
    if guild_id not in queues:
        queues[guild_id] = MusicQueue()
    return queues[guild_id]

async def handle_play_error(ctx: commands.Context, error: Optional[Exception]) -> None:
    if error:
        logger.error(f"Playback error: {error}")
        await ctx.send("⚠️ An error occurred while playing the song, skipping to next...")
    await play_next(ctx)

# Yeni fonksiyon: Status güncelleme
async def update_music_status(track: Optional[Track] = None) -> None:
    if track:
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=track.title
        )
        await bot.change_presence(activity=activity)

async def play_next(ctx: commands.Context) -> None:
    queue = get_queue(ctx.guild.id)
    if queue.leave_timer:
        queue.leave_timer.cancel()
    
    if not queue.queue:
        queue.now_playing = None
        queue.leave_timer = asyncio.create_task(leave_after_timeout(ctx))
        return

    track = queue.next()
    queue.now_playing = track
    voice_client = ctx.guild.voice_client
    
    try:
        # Müzik başladığında status'ü güncelle
        await update_music_status(track)
        
        voice_client.play(
            discord.PCMVolumeTransformer(
                discord.FFmpegPCMAudio(
                    track.url,
                    **FFMPEG_OPTIONS
                ),
                volume=queue.volume
            ),
            after=lambda e: asyncio.run_coroutine_threadsafe(
                handle_play_error(ctx, e) if e else play_next(ctx), 
                bot.loop
            )
        )
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"🎶 {track.title}",
            color=0x00ff00
        )
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Playback error: {e}")
        await ctx.send(f"❌ Error playing song: {str(e)}")
        await play_next(ctx)

async def leave_after_timeout(ctx: commands.Context) -> None:
    await asyncio.sleep(30)
    if ctx.guild.voice_client:
        queue = get_queue(ctx.guild.id)
        queue.clear()
        queue.is_leaving = True
        await ctx.guild.voice_client.disconnect()
        await ctx.send("👋 Left the channel due to 30 seconds of inactivity!")

@bot.event
async def on_ready() -> None:
    logger.info(f'Bot started: {bot.user.name}')
    bot.loop.create_task(change_status())

async def change_status() -> None:
    statuses = [
        discord.Activity(type=discord.ActivityType.custom, name="custome ", state="!play for music playing 🎧"),
        discord.Activity(type=discord.ActivityType.custom, name="custom", state="!cmd for help 📋")
    ]
    while True:
        if not any(guild.voice_client and guild.voice_client.is_playing() for guild in bot.guilds):
            for status in statuses:
                await bot.change_presence(activity=status)
                await asyncio.sleep(5)
        else:
            await asyncio.sleep(5)

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState) -> None:
    if member.id == bot.user.id and before.channel and not after.channel:
        try:
            guild_id = before.channel.guild.id
            queue = get_queue(guild_id)
            
            voice_client = before.channel.guild.voice_client
            if voice_client:
                if voice_client.is_playing():
                    voice_client.stop()
                    await asyncio.sleep(0.5)
            
            queue.clear()
            if queue.leave_timer:
                queue.leave_timer.cancel()
            
            if not queue.is_leaving and queue.text_channel:
                await queue.text_channel.send("👋 Goodbye!")
            
            queue.is_leaving = False
            
        except Exception as e:
            logger.error(f"Voice state update error: {e}")
            queue = get_queue(before.channel.guild.id)
            queue.clear()
            queue.is_leaving = False

async def ensure_voice(ctx: commands.Context) -> bool:
    if not ctx.message.author.voice:
        await ctx.send("❌ You must be in a voice channel!")
        return False
        
    if not ctx.guild.voice_client:
        await ctx.message.author.voice.channel.connect()
    return True

@bot.command(name='play', aliases=['p'])
async def play(ctx: commands.Context, *, query: str) -> None:
    if not await ensure_voice(ctx):
        return

    queue = get_queue(ctx.guild.id)
    queue.text_channel = ctx.channel
    if queue.leave_timer:
        queue.leave_timer.cancel()
        queue.leave_timer = None

    async with ctx.typing():
        try:
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                if not query.startswith('http'):
                    query = f"ytsearch:{query}"
                info = ydl.extract_info(query, download=False)
                
                track_data = info['entries'][0] if 'entries' in info else info
                track = Track(track_data['url'], track_data['title'])
                
                queue.add(track)
                
                if not ctx.guild.voice_client.is_playing():
                    await play_next(ctx)
                else:
                    embed = discord.Embed(
                        title="📝 Added to Queue",
                        description=f"🎵 {track.title}",
                        color=0x00ff00
                    )
                    await ctx.send(embed=embed)
                    
        except Exception as e:
            logger.error(f"Error details: {str(e)}")
            await ctx.send(f"❌ An error occurred: {str(e)}")

@bot.command(name='skip', aliases=['s'])
async def skip(ctx: commands.Context) -> None:
    if not ctx.guild.voice_client or not ctx.guild.voice_client.is_playing():
        await ctx.send("⚠️ No song is currently playing!")
        return
    
    await ctx.send("⏭️ Skipped the song!")
    ctx.guild.voice_client.stop()

@bot.command(name='queue', aliases=['q'])
async def show_queue(ctx: commands.Context) -> None:
    queue = get_queue(ctx.guild.id)
    if not queue.now_playing and not queue.queue:
        await ctx.send("📪 Queue is empty!")
        return

    embed = discord.Embed(title="🎵 Music Queue", color=0x00ff00)
    
    if queue.now_playing:
        embed.add_field(name="▶️ Now Playing:", value=queue.now_playing.title, inline=False)
    
    if queue.queue:
        queue_list = "\n".join([f"{i+1}. {track.title}" for i, track in enumerate(queue.queue)])
        embed.add_field(name="📝 Up Next:", value=queue_list, inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='volume', aliases=['v'])
async def volume(ctx: commands.Context, volume: int) -> None:
    if not ctx.guild.voice_client:
        await ctx.send("❌ Bot is not in a voice channel!")
        return
        
    if not 0 <= volume <= 100:
        await ctx.send("⚠️ Volume must be between 0 and 100!")
        return

    queue = get_queue(ctx.guild.id)
    queue.volume = volume / 100
    if ctx.guild.voice_client.source:
        ctx.guild.voice_client.source.volume = queue.volume
    
    await ctx.send(f"🔊 Volume set to {volume}%")

@bot.command(name='clear', aliases=['c'])
async def clear(ctx: commands.Context) -> None:
    queue = get_queue(ctx.guild.id)
    queue.clear()
    if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
        ctx.guild.voice_client.stop()
    await ctx.send("🗑️ Queue cleared!")

@bot.command(name='leave', aliases=['l'])
async def leave(ctx: commands.Context) -> None:
    if ctx.guild.voice_client:
        queue = get_queue(ctx.guild.id)
        queue.clear()
        if queue.leave_timer:
            queue.leave_timer.cancel()
        queue.is_leaving = True
        await ctx.guild.voice_client.disconnect()
        await ctx.send("👋 Goodbye!")

@bot.command(name='pause', aliases=['ps'])
async def pause(ctx: commands.Context) -> None:
    if ctx.guild.voice_client and ctx.guild.voice_client.is_playing():
        ctx.guild.voice_client.pause()
        await ctx.send("⏸️ Music paused")
    else:
        await ctx.send("⚠️ No song is currently playing!")

@bot.command(name='resume', aliases=['r'])
async def resume(ctx: commands.Context) -> None:
    if ctx.guild.voice_client and ctx.guild.voice_client.is_paused():
        ctx.guild.voice_client.resume()
        await ctx.send("▶️ Music resumed")
    else:
        await ctx.send("⚠️ No song is paused!")

@bot.command(name='now', aliases=['n'])
async def now_playing(ctx: commands.Context) -> None:
    queue = get_queue(ctx.guild.id)
    if queue.now_playing:
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=queue.now_playing.title,
            color=0x00ff00
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("⚠️ No song is currently playing!")

@bot.command(name='commands', aliases=['cmd'])
async def commands_list(ctx: commands.Context) -> None:
    embed = discord.Embed(
        title="🤖 Bot Commands",
        color=0x00ff00,
        description="Here are all available commands and their shortcuts:"
    )
    
    commands_list = {
        "🎵 Music Playback": [
            ("!play [song/url] (!p)", "Play music (URL or name)"),
            ("!pause (!ps)", "Pause the music"),
            ("!resume (!r)", "Resume the music"),
        ],
        "📝 Queue Management": [
            ("!queue (!q)", "Show song queue"),
            ("!skip (!s)", "Skip current song"),
            ("!clear (!c)", "Clear the queue"),
        ],
        "⚙️ Controls": [
            ("!volume [0-100] (!v)", "Adjust volume"),
            ("!now (!n)", "Show current song"),
            ("!leave (!l)", "Leave channel"),
        ]
    }
    
    for category, commands in commands_list.items():
        field_value = "\n".join([f"`{cmd}` - {desc}" for cmd, desc in commands])
        embed.add_field(name=category, value=field_value, inline=False)

    await ctx.send(embed=embed)

# Start the bot
if __name__ == "__main__":
    try:
        bot.run('your_bot_token')
    except Exception as e:
        logger.critical(f'Failed to start bot: {str(e)}')