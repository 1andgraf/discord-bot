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
import random
import speech_recognition as sr

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
        # ✅ If already connected to the right channel, reuse vc without reconnecting

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{TTS_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVEN_LABS_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "text": message,
            "voice_settings": {"stability": 0.0, "similarity_boost": 1.0},
            "format": "wav"
        }

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
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    roles = [role.name for role in member.roles if role.name != "@everyone"]
    embed = discord.Embed(title=f"User Info: {member}", color=discord.Color.blue())
    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Roles", value=", ".join(roles) if roles else "None", inline=False)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else discord.Embed.Empty)
    await ctx.send(embed=embed)

@bot.command()
async def serverinfo(ctx):
    guild = ctx.guild
    roles = [role.name for role in guild.roles if role.name != "@everyone"]
    embed = discord.Embed(title=f"Server Info: {guild.name}", color=discord.Color.green())
    embed.add_field(name="ID", value=guild.id, inline=False)
    embed.add_field(name="Member Count", value=guild.member_count, inline=False)
    embed.add_field(name="Roles", value=", ".join(roles) if roles else "None", inline=False)
    embed.set_thumbnail(url=guild.icon.url if guild.icon else discord.Embed.Empty)
    await ctx.send(embed=embed)

@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="Poll", description=question, color=discord.Color.orange())
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")

@bot.command()
async def meme(ctx):
    import requests

    subreddit = "memes"
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50"
    headers = {"User-Agent": "DiscordBot"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        posts = [post for post in data["data"]["children"] if not post["data"]["over_18"]]
        if posts:
            post = random.choice(posts)["data"]
            embed = discord.Embed(title=post["title"], url=f"https://reddit.com{post['permalink']}")
            embed.set_image(url=post["url"])
            await ctx.send(embed=embed)
        else:
            await ctx.send("Couldn't find a meme right now.")
    else:
        await ctx.send("Failed to fetch memes.")

@bot.command()
async def r(ctx, start: int, end: int):
    if start > end:
        await ctx.send("Start must be less than or equal to end.")
        return
    result = random.randint(start, end)
    await ctx.send(f"🎲 {ctx.author.mention} rolled the dice: {result}")

@bot.command()
async def define(ctx, *, word):
    import requests

    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        try:
            # Get first definition of the first meaning
            definition = data[0]['meanings'][0]['definitions'][0]['definition']
            example = data[0]['meanings'][0]['definitions'][0].get('example', None)

            embed = discord.Embed(title=f"Definition: {word}", color=discord.Color.blue())
            embed.add_field(name="Definition", value=definition, inline=False)
            if example:
                embed.add_field(name="Example", value=example, inline=False)
            await ctx.send(embed=embed)
        except (KeyError, IndexError):
            await ctx.send(f"Could not parse definition for '{word}'.")
    else:
        await ctx.send(f"Word '{word}' not found in dictionary.")

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


@bot.command()
async def join(ctx):
    """Bot joins voice channel and listens for spoken commands starting with 'Fabio'."""
    if not ctx.author.voice:
        await ctx.send("You need to be in a voice channel!")
        return

    channel = ctx.author.voice.channel
    vc = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if vc is None or not vc.is_connected():
        vc = await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)

    await ctx.send("Fabio is now listening... Be quiet")

    recognizer = sr.Recognizer()
    mic = sr.Microphone()  # For local testing; Discord voice frames require decoding Opus

    async def speech_loop():
        while vc.is_connected():
            # Placeholder: capture audio from Discord is needed here
            # Currently using local microphone for demo purposes
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                try:
                    audio = recognizer.listen(source, phrase_time_limit=5)
                    text = recognizer.recognize_google(audio)
                    
                    
                    if text.lower().startswith("fabio") or text.lower().startswith("unicorn") or text.lower().startswith("fabo"):
                        command_text = text[5:].strip()
                        await ctx.send(f"Detected: `{command_text}`")
                        
                        if command_text.lower() == "hello" or command_text.lower() == "rn hello":
                            await say(ctx, message="hello my little friend!!!!! wanna flakes or something??")
                        if command_text.lower() == "flakes" or command_text.lower() == "rn flakes":
                            await say(ctx, message="oh shit, these flakes are only mine, he he")
                        if command_text.lower() == "say" or command_text.lower() == "rn say":
                            await say(ctx, message="What should I say?")

                            def capture_followup():
                                recognizer = sr.Recognizer()
                                with sr.Microphone() as source:  # ✅ new instance, no nesting
                                    recognizer.adjust_for_ambient_noise(source)
                                    audio1 = recognizer.listen(source, timeout=3, phrase_time_limit=7)
                                    return recognizer.recognize_google(audio1)

                            try:
                                text1 = await asyncio.to_thread(capture_followup)
                                await ctx.send(f"Detected: `{text1}`")
                                await say(ctx, message=text1)
                            except sr.WaitTimeoutError:
                                await ctx.send("I didn’t hear anything.")
                            except sr.UnknownValueError:
                                await ctx.send("I couldn’t understand what you said.")
                            except sr.RequestError as e:
                                await ctx.send(f"Speech recognition failed: {e}")
                        if command_text.lower() == "leave" or command_text.lower() == "rn leave" or command_text.lower() == "rn leaf" or command_text.lower() == "rn live":
                                if vc and vc.is_connected():
                                    await vc.disconnect()
                                else:
                                    await ctx.send("I'm not in a voice channel.")
                            
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except sr.RequestError as e:
                    await ctx.send(f"Speech recognition failed: {e}")
            await asyncio.sleep(0.1)

    asyncio.create_task(speech_loop())

bot.run(BOT_TOKEN)