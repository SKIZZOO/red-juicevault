import asyncio
import json
import re
from urllib.parse import quote, unquote, urljoin

import aiohttp
import discord
from redbot.core import Config, commands

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None


class JuiceVault(commands.Cog):
    """24/7 JuiceVault archive player."""

    BASE_URL = "https://juicevault.xyz"
    FILES_URL = "https://juicevault.xyz/files?path=Music"
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

    async def cog_load(self):
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": "Mozilla/5.0 (compatible; Red-JuiceVault/1.0)"},
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

    def _is_audio(self, value):
        value = unquote(value).split("?", 1)[0].split("#", 1)[0].lower()
        return value.endswith(self.AUDIO_EXTENSIONS)

    def _make_url(self, value):
        value = unquote(value).strip()
        if value.startswith(("http://", "https://")):
            return value
        if value.startswith("/files?"):
            return urljoin(self.BASE_URL, value)
        value = value.lstrip("/")
        if not value.startswith("Music/"):
            value = "Music/" + value
        return f"{self.BASE_URL}/files?path={quote(value, safe='/')}"

    def _extract_json(self, obj):
        result = []
        if isinstance(obj, str):
            if self._is_audio(obj):
                result.append(self._make_url(obj))
        elif isinstance(obj, list):
            for item in obj:
                result.extend(self._extract_json(item))
        elif isinstance(obj, dict):
            for key in ("url", "href", "src", "path", "file", "filename", "name", "download", "download_url"):
                value = obj.get(key)
                if isinstance(value, str) and self._is_audio(value):
                    result.append(self._make_url(value))
            for value in obj.values():
                if isinstance(value, (dict, list)):
                    result.extend(self._extract_json(value))
        return result

    async def fetch_tracks(self):
        async with self.session.get(self.FILES_URL) as response:
            if response.status != 200:
                raise RuntimeError(f"JuiceVault HTTP {response.status}")
            content_type = response.headers.get("Content-Type", "").lower()
            text = await response.text(errors="ignore")

        urls = []
        if "json" in content_type or text.lstrip().startswith(("[", "{")):
            try:
                urls.extend(self._extract_json(json.loads(text)))
            except (json.JSONDecodeError, TypeError):
                pass

        hrefs = re.findall(r'href\s*=\s*["\']([^"\']+)["\']', text, flags=re.IGNORECASE)
        urls.extend(self._make_url(x) for x in hrefs if self._is_audio(x))
        for line in text.splitlines():
            if self._is_audio(line.strip()):
                urls.append(self._make_url(line.strip()))
        return list(dict.fromkeys(urls))

    def _ffmpeg_executable(self):
        if imageio_ffmpeg is not None:
            try:
                return imageio_ffmpeg.get_ffmpeg_exe()
            except Exception as exc:
                print(f"[JuiceVault] imageio-ffmpeg unavailable: {exc}")
        return "ffmpeg"

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
                    tracks = await self.fetch_tracks()
                    if not tracks:
                        await asyncio.sleep(30)
                        continue
                    self.queues[gid] = tracks
                try:
                    voice = await self._connect(guild, channel)
                except Exception as exc:
                    print(f"[JuiceVault] voice error: {exc}")
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
                        before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                        options="-vn",
                    )
                    if voice.is_playing():
                        voice.stop()
                    voice.play(source, after=after)
                except Exception as exc:
                    print(f"[JuiceVault] could not play {url}: {exc}")
                    await asyncio.sleep(2)
                    continue
                stop_task = asyncio.create_task(stop.wait())
                finish_task = asyncio.create_task(finished.wait())
                skip_task = asyncio.create_task(skip.wait())
                _, pending = await asyncio.wait({stop_task, finish_task, skip_task}, return_when=asyncio.FIRST_COMPLETED)
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
            await ctx.send("JuiceVault rulează deja.")
            return
        try:
            tracks = await self.fetch_tracks()
        except Exception as exc:
            await ctx.send(f"Nu pot accesa JuiceVault: `{exc}`")
            return
        if not tracks:
            await ctx.send("Nu am găsit fișiere audio în Music.")
            return
        self.queues[gid] = tracks
        self.stop_events[gid] = asyncio.Event()
        self.skip_events[gid] = asyncio.Event()
        await self.config.guild(ctx.guild).enabled.set(True)
        await self.config.guild(ctx.guild).channel_id.set(ctx.author.voice.channel.id)
        self.tasks[gid] = asyncio.create_task(self._player(ctx.guild, ctx.author.voice.channel))
        await ctx.send(f"▶️ Pornit — {len(tracks)} piese găsite.")

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
        """Reload the Music archive."""
        try:
            tracks = await self.fetch_tracks()
        except Exception as exc:
            await ctx.send(f"Refresh eșuat: `{exc}`")
            return
        if not tracks:
            await ctx.send("Nu am găsit piese.")
            return
        self.queues[ctx.guild.id] = tracks
        await ctx.send(f"🔄 Queue reîncărcat: {len(tracks)} piese.")

    @jv.command(name="status")
    async def status(self, ctx):
        """Show player status."""
        gid = ctx.guild.id
        if gid not in self.tasks:
            await ctx.send("🔴 Oprit.")
            return
        voice = ctx.guild.voice_client
        await ctx.send(f"🟢 Rulează | Voice: `{bool(voice and voice.is_connected())}` | Queue: `{len(self.queues.get(gid, []))}` | Current: `{self.current.get(gid, 'nimic')}`")
