import discord
if not discord.opus.is_loaded():
    discord.opus.load_opus("/opt/homebrew/opt/opus/lib/libopus.dylib")
from discord.ext import commands
import requests
import io
import tempfile
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
print(discord.opus.is_loaded()) 
from pydub import AudioSegment
from discord import Embed

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
TTS_VOICE_ID = os.getenv("TTS_VOICE_ID")

intents = discord.Intents.default()
intents.members = True
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix="^", intents=intents, help_command=None)

def elevenlabs_tts(text):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{TTS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {"text": text, "voice_settings": {"stability":0.0,"similarity_boost":1.0}, "format": "wav"}
    response = requests.post(url, headers=headers, json=data)
    return io.BytesIO(response.content)

@bot.command()
async def say(ctx, *, message):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if vc is None or not vc.is_connected():
            vc = await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{TTS_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVEN_LABS_API_KEY,
            "Content-Type": "application/json"
        }
        data = {"text": message, "voice_settings": {"stability":0.0,"similarity_boost":1.0}, "format": "wav"}
        response = requests.post(url, headers=headers, json=data)
        if response.status_code != 200:
            await ctx.send(f"Failed to generate speech: {response.status_code} {response.text}")
            return
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("audio"):
            await ctx.send("Received unexpected audio format.")
            return
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav_file:
            temp_wav_file.write(response.content)
            temp_wav_file_path = temp_wav_file.name
        audio_source = discord.FFmpegPCMAudio(temp_wav_file_path)
        vc.play(audio_source)
        while vc.is_playing():
            await asyncio.sleep(0.1)
        os.remove(temp_wav_file_path)
    else:
        await ctx.send("You need to be in a voice channel!")
        
@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if vc is None or not vc.is_connected():
            await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)
    else:
        await ctx.send("You need to be in a voice channel!")

    
def elevenlabs_tts_to_wav(text: str) -> str:

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{TTS_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_LABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {"text": text, "voice_settings": {"stability":0.0,"similarity_boost":1.0}}

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"Eleven Labs TTS failed: {response.text}")

    mp3_bytes = io.BytesIO(response.content)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
        audio = AudioSegment.from_file(mp3_bytes, format="mp3")
        audio.export(tmp_wav.name, format="wav")
        return tmp_wav.name

@bot.command()
async def leave(ctx):
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc and vc.is_connected():
        await vc.disconnect()
    else:
        await ctx.send("I'm not in a voice channel.")
        
@bot.command()
async def help(ctx):
    embed = Embed(title="Fabio Bot Commands", color=discord.Color.green())
    embed.add_field(name="^say <message>", value="Converts text to speech and plays it in your voice channel", inline=False)
    embed.add_field(name="^join", value="Bot joins your current voice channel", inline=False)
    embed.add_field(name="^leave", value="Bot leaves the voice channel", inline=False)
    embed.add_field(name="^m <song name>", value="Plays music from YouTube (adds to queue if something is already playing)", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def m(ctx, *, query):
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel!")
        return

    channel = ctx.author.voice.channel
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc is None or not vc.is_connected():
        vc = await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)

    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "quiet": True,
        "default_search": "ytsearch",
        "extract_flat": False, 
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        if "entries" in info:
            info = info["entries"][0]
        url = info["url"]
        title = info.get("title")

    if not hasattr(vc, 'queue'):
        vc.queue = []
    if not hasattr(vc, 'last_now_playing_msg'):
        vc.last_now_playing_msg = None

    async def send_now_playing(title, url):
        if vc.last_now_playing_msg:
            try:
                await vc.last_now_playing_msg.delete()
            except Exception:
                pass
        embed = discord.Embed(title="Now Playing", description=f"[{title}]({url})", color=discord.Color.purple())
        embed.set_footer(text="Fabio 🎵")
        msg = await ctx.send(embed=embed, view=MusicControlView(vc, url))
        vc.last_now_playing_msg = msg

    def play_next(error):
        if error:
            print(f"Error in playback: {error}")
        if vc.queue:
            next_url, next_title = vc.queue.pop(0)
            ffmpeg_options = {
                "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                "options": "-vn",
            }
            audio_source = discord.FFmpegPCMAudio(next_url, **ffmpeg_options)
            vc.play(audio_source, after=lambda e: play_next(e))
            vc.current_title = next_title
            asyncio.create_task(send_now_playing(next_title, next_url))
        else:
            vc.current_title = None
            asyncio.create_task(ctx.send("No more songs in queue.", ephemeral=True))

    class MusicControlView(discord.ui.View):
        def __init__(self, voice_client, url):
            super().__init__()
            self.voice_client = voice_client
            self.url = url
            self.playing = True

        @discord.ui.button(label="Play", style=discord.ButtonStyle.green)
        async def play_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.guild != ctx.guild:
                await interaction.response.send_message("This button is not for this guild.", ephemeral=True)
                return
            if not self.playing:
                await interaction.response.defer()
                ffmpeg_options = {
                    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                    "options": "-vn",
                }
                audio_source = discord.FFmpegPCMAudio(self.url, **ffmpeg_options)
                self.voice_client.play(audio_source, after=lambda e: self._after_play(e))
                self.playing = True
            else:
                await interaction.response.send_message("Audio is already playing.", ephemeral=True)

        def _after_play(self, error):
            if error:
                print(f"Error in playback: {error}")
            self.playing = False

        @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
        async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.guild != ctx.guild:
                await interaction.response.send_message("This button is not for this guild.", ephemeral=True)
                return
            if self.playing:
                await interaction.response.defer()
                self.voice_client.stop()
                self.playing = False
            else:
                await interaction.response.send_message("No audio is playing.", ephemeral=True)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.blurple)
        async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.guild != ctx.guild:
                await interaction.response.send_message("This button is not for this guild.", ephemeral=True)
                return
            if self.playing:
                if hasattr(self.voice_client, 'queue') and self.voice_client.queue:
                    await interaction.response.defer()
                    self.voice_client.stop()
                    play_next(None)
                else:
                    await interaction.response.send_message("No more songs in queue.", ephemeral=True)
            else:
                await interaction.response.send_message("No audio is playing to skip.", ephemeral=True)

        @discord.ui.button(label="Leave", style=discord.ButtonStyle.grey)
        async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.guild != ctx.guild:
                await interaction.response.send_message("This button is not for this guild.", ephemeral=True)
                return
            if self.voice_client and self.voice_client.is_connected():
                await interaction.response.defer()
                if hasattr(self.voice_client, 'last_now_playing_msg') and self.voice_client.last_now_playing_msg:
                    try:
                        await self.voice_client.last_now_playing_msg.delete()
                    except Exception:
                        pass
                await self.voice_client.disconnect()
                self.playing = False
            else:
                await interaction.response.send_message("I'm not connected to a voice channel.", ephemeral=True)

    if vc.is_playing() or vc.is_paused():
        vc.queue.append((url, title))
        await ctx.send(f"Added to queue: {title}", ephemeral=True)
    else:
        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }
        audio_source = discord.FFmpegPCMAudio(url, **ffmpeg_options)
        vc.play(audio_source, after=play_next)
        vc.current_title = title
        await send_now_playing(title, url)
        
bot.run(BOT_TOKEN)