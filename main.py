import discord
from discord.ext import commands
import yt_dlp as youtube_dl
import asyncio
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

# Configuración inicial
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Eliminar el comando de ayuda predeterminado para usar uno personalizado
bot.remove_command("help")

# Configuración ultra optimizada de YouTube-DL
ydl_opts = {
    'format': 'bestaudio/best',
    'cookiefile': 'cookies.txt',
    'quiet': True,
    'no_warnings': True,
    'noplaylist': True,
    'ignoreerrors': True,
    'socket_timeout': 5,
    'source_address': '0.0.0.0',
    'nocheckcertificate': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

# Configuración de Spotify
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

class MusicPlayer:
    def __init__(self):
        self.queue = []
        self.voice_client = None
        self.ydl = youtube_dl.YoutubeDL(ydl_opts)
        self.lock = asyncio.Lock()

    async def play_next(self, ctx):
        async with self.lock:
            if not self.queue or not self.voice_client:
                return

            try:
                song = self.queue.pop(0)
                
                # Extraer información del audio (optimizado)
                info = await asyncio.to_thread(
                    self.ydl.extract_info,
                    song['url'],
                    download=False
                )
                
                if 'entries' in info:
                    info = info['entries'][0]
                
                audio_url = info['url']
                duration = info.get('duration', 0)
                mins, secs = divmod(int(duration), 60) if duration else (0, 0)
                formatted_duration = f"{mins}:{secs:02d}" if duration else "Desconocida"

                # Embed de reproducción
                embed = discord.Embed(
                    title="🎵 𝘓𝘪𝘴𝘵𝘦𝘯𝘪𝘯𝘨 𝘕𝘰𝘸",
                    description=f"{info['title']}",
                    color=0x5e05ef
                )
                embed.set_thumbnail(url=info.get('thumbnail', 'https://i.imgur.com/undefined.png'))
                embed.add_field(name="𝘋𝘶𝘳𝘢𝘵𝘪𝘰𝘯", value=formatted_duration, inline=True)
                embed.add_field(name="𝘙𝘦𝘲𝘶𝘦𝘴𝘵𝘦𝘥 𝘣𝘺", value=ctx.author.mention, inline=True)
                
                await ctx.send(embed=embed, ephemeral=True)

                # Configuración definitiva de FFmpeg
                self.voice_client.play(
                    discord.FFmpegPCMAudio(
                        audio_url,
                        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin",
                        options="-vn -loglevel error"
                    ),
                    after=lambda e: asyncio.run_coroutine_threadsafe(
                        self.play_next(ctx), 
                        bot.loop
                    )
                )

            except Exception as e:
                print(f"Error: {e}")
                await ctx.send("✘ 𝘛𝘩𝘦𝘳𝘦'𝘴 𝘴𝘰𝘮𝘦𝘵𝘩𝘪𝘯𝘨 𝘸𝘳𝘰𝘯𝘨 𝘸𝘪𝘵𝘩 𝘵𝘩𝘪𝘴 𝘴𝘰𝘯𝘨.. 𝘚𝘬𝘪𝘱𝘱𝘪𝘯𝘨...", ephemeral=True)
                await self.play_next(ctx)

player = MusicPlayer()

async def process_spotify(url: str):
    try:
        if "track" in url:
            track = await asyncio.to_thread(
                sp.track,
                url.split("track/")[1].split("?")[0]
            )
            return [{
                'title': f"{track['name']} - {track['artists'][0]['name']}",
                'url': f"ytsearch:{item['track']['name']} {item['track']['artists'][0]['name']} audio oficial"
            }]
        
        elif "playlist" in url:
            results = await asyncio.to_thread(
                sp.playlist_tracks,
                url.split("playlist/")[1].split("?")[0]
            )
            return [{
                'title': f"{item['track']['name']} - {item['track']['artists'][0]['name']}",
                'url': f"ytsearch:{item['track']['name']} {item['track']['artists'][0]['name']} audio oficial"
            } for item in results['items'][:10]]
    
    except Exception as e:
        print(f"Spotify Error: {e}")
        return None

@bot.command(name="ap", help="Anteiku Play - Reproduce música (5 resultados). Uso: !ap <busqueda o link>")
async def anteiku_play(ctx, *, query):
    await ctx.defer(ephemeral=True)
    
    if not ctx.author.voice:
        return await ctx.send("☹︎ 𝘎𝘦𝘵 𝘪𝘯 𝘢 𝘷𝘰𝘪𝘤𝘦 𝘤𝘩𝘢𝘯𝘯𝘦𝘭 𝘧𝘪𝘳𝘴𝘵.", ephemeral=True)
    
    if not player.voice_client:
        player.voice_client = await ctx.author.voice.channel.connect()
    elif ctx.author.voice.channel != player.voice_client.channel:
        return await ctx.send("☹︎ 𝘐𝘮 𝘪𝘯 𝘢𝘯𝘰𝘵𝘩𝘦𝘳 𝘤𝘩𝘢𝘯𝘯𝘦𝘭, 𝘪 𝘤𝘢𝘯𝘵 𝘣𝘦 𝘪𝘯 𝘵𝘸𝘰 𝘱𝘭𝘢𝘤𝘦𝘴 𝘢𝘵 𝘵𝘩𝘦 𝘴𝘢𝘮𝘦 𝘵𝘪𝘮𝘦.. 𝘧𝘰𝘳 𝘯𝘰𝘸..", ephemeral=True)

    try:
        if "spotify.com" in query:
            tracks = await process_spotify(query)
            if not tracks:
                return await ctx.send("☹︎ 𝘚𝘰𝘮𝘦𝘵𝘩𝘪𝘯𝘨 𝘸𝘦𝘯𝘵 𝘸𝘳𝘰𝘯𝘨 𝘸𝘪𝘵𝘩 𝘚𝘱𝘰𝘵𝘪𝘧𝘺, 𝘵𝘳𝘺 𝘢𝘨𝘢𝘪𝘯.", ephemeral=True)
            
            player.queue.extend(tracks)
            await ctx.send(f"♬ Added  {len(tracks)} 𝘴𝘰𝘯𝘨𝘴 𝘧𝘳𝘰𝘮 𝘢 𝘱𝘳𝘦𝘵𝘵𝘺 𝘱𝘭𝘢𝘺𝘭𝘪𝘴𝘵.", ephemeral=True)
            if not player.voice_client.is_playing():
                await player.play_next(ctx)
            return

        # Búsqueda optimizada con caché
        with youtube_dl.YoutubeDL({'quiet': True, 'format': 'bestaudio'}) as ydl:
            info = await asyncio.to_thread(
                ydl.extract_info,
                f"ytsearch5:{query}",
                download=False,
                process=False  # Acelerar búsqueda
            )
            results = list(info['entries'])[:5]

        # Sistema de botones reactivo
        class SongMenu(discord.ui.View):
            def __init__(self, results):
                super().__init__(timeout=15)
                self.results = results
                self.choice = None
                
                for i in range(5):
                    btn = discord.ui.Button(
                        label=str(i+1),
                        style=discord.ButtonStyle.primary,
                        row=0 if i < 3 else 1
                    )
                    btn.callback = self.create_callback(i)
                    self.add_item(btn)

            def create_callback(self, index):
                async def button_handler(interaction):
                    await interaction.response.defer(ephemeral=True)
                    self.choice = index
                    self.stop()
                return button_handler

        view = SongMenu(results)
        embed = discord.Embed(title="🎵 𝘈𝘯𝘵𝘦𝘪𝘬𝘶 𝘚𝘦𝘢𝘳𝘤𝘩: 𝘗𝘪𝘤𝘬 𝘢 𝘚𝘰𝘯𝘨, 𝘢𝘯𝘥 𝘥𝘰𝘯'𝘵 𝘣𝘦 𝘴𝘩𝘺", color=0x5e05ef)
        for i, song in enumerate(results):
            duration = song.get('duration', 0)
            mins, secs = divmod(int(duration), 60) if duration else (0, 0)
            link = song.get('webpage_url', song.get('url', ''))
            embed.add_field(
                name=f"{i+1}. {song['title'][:35]}...",
                value=f"⏱︎{mins}:{secs:02d} |",
                inline=False
            )
        
        msg = await ctx.send(embed=embed, view=view, ephemeral=True)
        await view.wait()

        if view.choice is not None and 0 <= view.choice < len(results):
            selected = results[view.choice]
            await msg.edit(content="𝘓𝘰𝘢𝘥𝘪𝘯𝘨 𝘺𝘰𝘶𝘳 𝘴𝘰𝘯𝘨...", embed=None, view=None)
        else:
            selected = results[0]
            await msg.edit(content="♬ 𝘗𝘪𝘤𝘬𝘪𝘯𝘨 𝘵𝘩𝘦 𝘧𝘪𝘳𝘴𝘵 𝘳𝘦𝘴𝘶𝘭𝘵...", embed=None, view=None)

        player.queue.append({
            'title': selected['title'],
            'url': selected['url']
        })
        
        if not player.voice_client.is_playing():
            await player.play_next(ctx)

    except Exception as e:
        print(f"Error crítico: {e}")
        await ctx.send("✘ 𝘚𝘰𝘮𝘦𝘵𝘩𝘪𝘯𝘨 𝘸𝘦𝘯𝘵 𝘸𝘳𝘰𝘯𝘨, 𝘵𝘳𝘺 𝘢𝘨𝘢𝘪𝘯.", ephemeral=True)

@bot.command(name="skip", help="Salta la canción en reproducción. Uso: !skip")
async def skip(ctx):
    if player.voice_client and player.voice_client.is_playing():
        player.voice_client.stop()
        await ctx.send("❯❯❯ 𝘉𝘺𝘦, 𝘣𝘺𝘦 𝘴𝘰𝘯𝘨..", ephemeral=True)
    else:
        await ctx.send("✘ 𝘛𝘩𝘦𝘳𝘦'𝘴 𝘯𝘰 𝘴𝘰𝘯𝘨 𝘱𝘭𝘢𝘺𝘪𝘯𝘨 𝘳𝘯..", ephemeral=True)

@bot.command(name="stop", help="Detiene la reproducción y desconecta al bot. Uso: !stop")
async def stop(ctx):
    if player.voice_client:
        player.queue.clear()
        await player.voice_client.disconnect()
        player.voice_client = None
        await ctx.send("■ 𝘗𝘭𝘢𝘺𝘣𝘢𝘤𝘬 𝘚𝘵𝘰𝘱𝘱𝘦𝘥, 𝘺𝘰𝘶'𝘳𝘦 𝘴𝘶𝘤𝘩 𝘢 𝘮𝘰𝘯𝘴𝘵𝘦𝘳. 𝘓𝘐𝘚𝘛𝘌𝘕 𝘜𝘕𝘙𝘈𝘝𝘌𝘓 𝘕𝘖𝘞!", ephemeral=True)
    else:
        await ctx.send("☹︎ 𝘐𝘮 𝘯𝘰𝘵 𝘤𝘰𝘯𝘯𝘦𝘤𝘵𝘦𝘥.", ephemeral=True)

@bot.command(name="help", help="Muestra la lista de comandos y su uso. Uso: !help")
async def help_command(ctx):
    embed = discord.Embed(
        title="Ayuda - Comandos del Bot",
        description="Aquí tienes la lista de comandos y su uso:",
        color=0x5e05ef # Morado oscuro
    )
    embed.add_field(name="!ap <busqueda o link>", 
                    value="Reproduce música. Compatible con Spotify, Youtube y SoundCloud.\nEjemplo: !ap Never Gonna Give You Up", 
                    inline=False)
    embed.add_field(name="!skip", 
                    value="Salta la canción en reproducción.\nEjemplo: !skip", 
                    inline=False)
    embed.add_field(name="!stop", 
                    value="Detiene la reproducción y desconecta al bot.\nEjemplo: !stop", 
                    inline=False)
    embed.add_field(name="!help", 
                    value="Muestra este mensaje de ayuda.\nEjemplo: !help", 
                    inline=False)
    await ctx.send(embed=embed)

# Manejador global de errores
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound) or isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("✘ 𝘐𝘯𝘤𝘰𝘳𝘳𝘦𝘤𝘵 𝘊𝘰𝘮𝘮𝘢𝘯𝘥.  𝘶𝘴𝘦 !𝘩𝘦𝘭𝘱 𝘵𝘰 𝘴𝘦𝘦 𝘵𝘩𝘦 𝘭𝘪𝘴𝘵 𝘰𝘧 𝘵𝘩𝘦 𝘤𝘰𝘮𝘮𝘢𝘯𝘥𝘴.")
    else:
        print(f"Error en {ctx.command}: {error}")
        await ctx.send("✘ 𝘚𝘰𝘮𝘦𝘵𝘩𝘪𝘯𝘨 𝘏𝘢𝘱𝘱𝘦𝘯𝘦𝘥, 𝘜𝘴𝘦 !𝘩𝘦𝘭𝘱 𝘵𝘰 𝘴𝘦𝘦 𝘵𝘩𝘦 𝘭𝘪𝘴𝘵 𝘰𝘧 𝘵𝘩𝘦 𝘤𝘰𝘮𝘮𝘢𝘯𝘥𝘴.")

@bot.event
async def on_ready():
    print(f"✅ Anteiku Music operativo como {bot.user}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)