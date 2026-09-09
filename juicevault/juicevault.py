import asyncio
import json
from urllib.parse import quote

import aiohttp
import discord
from redbot.core import Config, commands

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None


class JuiceVault(commands.Cog):
    """24/7 JuiceVault archive player using the public JuiceVault API."""

    API_BASE = "https://api.juicevault.xyz"
    MUSIC_LIST_URL = f"{API_BASE}/music/list"
    AUDIO_EXTENSIONS = (".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac", ".webm")

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=918273645, force_registration=True)
        self.config.register_guild(enabled=False, channel_id=None)
        self.session = None
        self.tasks = {}
        self.stop_events = {}
        self.skip_events = {}
        self.queues = {}
        self.current = {}
        self.last_error = {}

    async def cog_load(self):
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": "Red-JuiceVault/1.0"},
            timeout=aiohttp.ClientTimeout(total=30),
        )
        self.bot.loop.create_task(self._restore_players())

    async def cog_unload(self):
        for guild_id in list(self.tasks):
            await self._stop(guild_id)
        if self.session:
            await self.session.close()

    async def _restore_players(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(2)
        for guild_id, settings in (await self.config.all_guilds()).items():
            if not settings.get("enabled") or not settings.get("channel_id"):
                continue
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                continue
            channel = guild.get_channel(settings["channel_id"])
            if not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
                continue
            if guild_id not in self.tasks:
                self.stop_events[guild_id] = asyncio.Event()
                self.skip_events[guild_id] = asyncio.Event()
                self.tasks[guild_id] = asyncio.create_task(self._player(guild, channel))

    def _ffmpeg_executable(self):
        if imageio_ffmpeg is not None:
            try:
                return imageio_ffmpeg.get_ffmpeg_exe()
            except Exception as exc:
                print(f"[JuiceVault] imageio-ffmpeg unavailable: {exc}")
        return "ffmpeg"

    def _stream_url(self, song_id):
        return f"{self.API_BASE}/music/stream/{quote(str(song_id), safe='')}"

    async def fetch_tracks(self):
        """Load the complete public JuiceVault song index."""
        async with self.session.get(self.MUSIC_LIST_URL) as response:
            text = await response.text(errors="ignore")
            if response.status != 200:
                try:
                    payload = json.loads(text)
                    detail = payload.get("error", text[:200]) if isinstance(payload, dict) else text[:200]
                except json.JSONDecodeError:
                    detail = text[:200]
                raise RuntimeError(f"JuiceVault API HTTP {response.status}: {detail}")

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("JuiceVault API returned invalid JSON") from exc

        songs = payload.get("songs") if isinstance(payload, dict) else None
        if not isinstance(songs, list):
            raise RuntimeError("JuiceVault API response has no songs list")

        tracks = []
        for song in songs:
            if not isinstance(song, dict):
                continue
            song_id = song.get("id")
            file_name = str(song.get("file_name", ""))
            if not song_id or not file_name.lower().split("?", 1)[0].endswith(self.AUDIO_EXTENSIONS):
                continue
            tracks.append(self._stream_url(song_id))

        return list(dict.fromkeys(tracks))

    async def _connect(self, guild, channel):
        voice = guild.voice_client
        if voice and voice.is_connected():
            if voice.channel.id != channel.id:
                await voice.move_to(channel)
            return voice
        return await channel.connect(reconnect=True, timeout=30)

    async def _disconnect(self, guild):
        voice = guild.voice_client
        if voice:
            try:
                if voice.is_playing():
                    voice.stop()
                await voice.disconnect(force=True)
            except Exception:
                pass

    async def _stop(self, guild_id):
        if guild_id in self.stop_events:
            self.stop_events[guild_id].set()
        if guild_id in self.skip_events:
            self.skip_events[guild_id].set()
        task = self.tasks.pop(guild_id, None)
        if task and task is not asyncio.current_task():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.queues.pop(guild_id, None)
        self.current.pop(guild_id, None)
        self.last_error.pop(guild_id, None)
        guild = self.bot.get_guild(guild_id)
        if guild:
            await self._disconnect(guild)

    async def _player(self, guild, channel):
        gid = guild.id
        stop = self.stop_events[gid]
        skip = self.skip_events[gid]
        try:
            while not stop.is_set():
                if not self.queues.get(gid):
                    try:
                        tracks = await self.fetch_tracks()
                    except Exception as exc:
                        self.last_error[gid] = f"API: {exc}"
                        print(f"[JuiceVault] API error: {exc}")
                        await asyncio.sleep(30)
                        continue
                    if not tracks:
                        self.last_error[gid] = "API nu a returnat piese audio"
                        await asyncio.sleep(30)
                        continue
                    self.queues[gid] = tracks

                try:
                    voice = await self._connect(guild, channel)
                except Exception as exc:
                    self.last_error[gid] = f"Voice: {type(exc).__name__}: {exc}"
                    print(f"[JuiceVault] voice error: {type(exc).__name__}: {exc}")
                    await asyncio.sleep(10)
                    continue

                url = self.queues[gid].pop(0)
                self.current[gid] = url
                finished = asyncio.Event()

                def after(error):
                    if error:
                        print(f"[JuiceVault] playback error: {error}")
                    self.bot.loop.call_soon_threadsafe(finished.set)

                try:
                    source = discord.FFmpegPCMAudio(
                        self._ffmpeg_executable(),
                        url,
                        before_options='-user_agent "Red-JuiceVault/1.0" -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                        options="-vn",
                    )
                    if voice.is_playing():
                        voice.stop()
                    voice.play(source, after=after)
                    self.last_error.pop(gid, None)
                except Exception as exc:
                    self.last_error[gid] = f"Playback: {type(exc).__name__}: {exc}"
                    print(f"[JuiceVault] could not play {url}: {type(exc).__name__}: {exc}")
                    await asyncio.sleep(2)
                    continue

                stop_task = asyncio.create_task(stop.wait())
                finish_task = asyncio.create_task(finished.wait())
                skip_task = asyncio.create_task(skip.wait())
                _, pending = await asyncio.wait(
                    {stop_task, finish_task, skip_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()

                if stop.is_set():
                    break
                if skip.is_set():
                    skip.clear()
                    if voice.is_playing():
                        voice.stop()
        except asyncio.CancelledError:
            pass
        finally:
            await self._disconnect(guild)
            self.current.pop(gid, None)

    @commands.group(name="jv", invoke_without_command=True)
    @commands.guild_only()
    async def jv(self, ctx):
        """JuiceVault commands."""
        await ctx.send("`jv start` `jv stop` `jv skip` `jv refresh` `jv status`")

    @jv.command(name="start")
    async def start(self, ctx):
        """Start continuous playback."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Intră mai întâi într-un voice channel.")
            return
        gid = ctx.guild.id
        if gid in self.tasks:
            voice = ctx.guild.voice_client
            if voice and voice.is_connected():
                await ctx.send("JuiceVault rulează deja și sunt în voice.")
            else:
                self.tasks.pop(gid, None)
                await self.config.guild(ctx.guild).enabled.set(False)
                await ctx.send("Playerul era blocat fără conexiune voice. Am resetat starea; rulează din nou `jv start`.")
            return
        try:
            tracks = await self.fetch_tracks()
        except Exception as exc:
            await ctx.send(f"Nu pot accesa JuiceVault API: `{exc}`")
            return
        if not tracks:
            await ctx.send("JuiceVault API nu a returnat piese audio.")
            return

        # Verify Discord voice connection BEFORE telling the user that playback started.
        try:
            voice = await self._connect(ctx.guild, ctx.author.voice.channel)
        except Exception as exc:
            self.last_error[gid] = f"Voice: {type(exc).__name__}: {exc}"
            await ctx.send(f"❌ Nu pot intra în voice: `{type(exc).__name__}: {exc}`")
            return

        self.queues[gid] = tracks
        self.stop_events[gid] = asyncio.Event()
        self.skip_events[gid] = asyncio.Event()
        await self.config.guild(ctx.guild).enabled.set(True)
        await self.config.guild(ctx.guild).channel_id.set(ctx.author.voice.channel.id)
        self.tasks[gid] = asyncio.create_task(self._player(ctx.guild, ctx.author.voice.channel))
        await ctx.send(f"▶️ Pornit — {len(tracks)} piese găsite prin JuiceVault API. Sunt în `{voice.channel.name}`.")

    @jv.command(name="stop")
    async def stop(self, ctx):
        """Stop playback."""
        await self.config.guild(ctx.guild).enabled.set(False)
        if ctx.guild.id not in self.tasks:
            await ctx.send("JuiceVault nu rulează.")
            return
        await self._stop(ctx.guild.id)
        await ctx.send("⏹️ Oprit.")

    @jv.command(name="skip")
    async def skip(self, ctx):
        """Skip current track."""
        event = self.skip_events.get(ctx.guild.id)
        if not event:
            await ctx.send("Playerul nu rulează.")
            return
        event.set()
        voice = ctx.guild.voice_client
        if voice and voice.is_playing():
            voice.stop()
        await ctx.send("⏭️ Următoarea piesă.")

    @jv.command(name="refresh")
    async def refresh(self, ctx):
        """Reload the JuiceVault API song index."""
        try:
            tracks = await self.fetch_tracks()
        except Exception as exc:
            await ctx.send(f"Refresh eșuat: `{exc}`")
            return
        if not tracks:
            await ctx.send("JuiceVault API nu a returnat piese.")
            return
        self.queues[ctx.guild.id] = tracks
        await ctx.send(f"🔄 Queue reîncărcat: {len(tracks)} piese.")

    @jv.command(name="status")
    async def status(self, ctx):
        """Show player status."""
        gid = ctx.guild.id
        if gid not in self.tasks:
            error = self.last_error.get(gid)
            if error:
                await ctx.send(f"🔴 Oprit. Ultima eroare: `{error}`")
            else:
                await ctx.send("🔴 Oprit.")
            return
        voice = ctx.guild.voice_client
        await ctx.send(
            f"🟢 Rulează | Voice: `{bool(voice and voice.is_connected())}` | "
            f"Queue: `{len(self.queues.get(gid, []))}` | Current: `{self.current.get(gid, 'nimic')}` | "
            f"Error: `{self.last_error.get(gid, 'none')}`"
        )
