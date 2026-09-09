import asyncio
import json
import os
import random
import tempfile
import time
from urllib.parse import quote

import aiohttp
import discord
from redbot.core import Config, commands

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None


class JuiceVault(commands.Cog):
    """24/7 JuiceVault archive player."""

    API_BASE = "https://api.juicevault.xyz"
    MUSIC_LIST_URL = f"{API_BASE}/music/list"
    CATEGORY_URLS = {
        "instrumentals": f"{API_BASE}/music/instrumentals/list",
        "remasters": f"{API_BASE}/music/remasters/list",
        "stems": f"{API_BASE}/music/stems/list",
        "released": f"{API_BASE}/music/released/list",
        "cuts": f"{API_BASE}/music/cuts/list",
        "cut": f"{API_BASE}/music/cuts/list",
    }
    AUDIO_EXTENSIONS = (".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac", ".webm")
    FAILURE_BACKOFF_SECONDS = 8
    MAX_CONSECUTIVE_FAILURES = 3
    VOICE_STOP_TIMEOUT = 5.0
    DOWNLOAD_CHUNK_SIZE = 256 * 1024

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=918273645, force_registration=True)
        self.config.register_guild(enabled=False, channel_id=None, category="all")
        self.session = None
        self.tasks = {}
        self.restore_task = None
        self.stop_events = {}
        self.skip_events = {}
        self.skip_counts = {}
        self.queues = {}
        self.manual_queues = {}
        self.current = {}
        self.last_error = {}
        self.search_results = {}
        self.failure_counts = {}
        self.seek_events = {}
        self.seek_targets = {}
        self.play_positions = {}
        self.effects = {}

    async def cog_load(self):
        await self._ensure_session()
        self.restore_task = asyncio.create_task(self._restore_players())

    async def cog_unload(self):
        if self.restore_task:
            self.restore_task.cancel()
            try:
                await self.restore_task
            except asyncio.CancelledError:
                pass
            self.restore_task = None
        for guild_id in list(self.tasks):
            await self._stop(guild_id)
        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "Red-JuiceVault/1.2"},
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self.session

    async def _restore_players(self):
        try:
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
                if guild_id in self.tasks:
                    continue
                self.stop_events[guild_id] = asyncio.Event()
                self.skip_events[guild_id] = asyncio.Event()
                self.seek_events[guild_id] = asyncio.Event()
                self.skip_counts[guild_id] = 0
                self.manual_queues[guild_id] = []
                self.effects[guild_id] = "none"
                self.tasks[guild_id] = asyncio.create_task(self._player(guild, channel))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[JuiceVault] restore error: {type(exc).__name__}: {exc}")

    def _ffmpeg_executable(self):
        if imageio_ffmpeg is not None:
            try:
                return imageio_ffmpeg.get_ffmpeg_exe()
            except Exception:
                pass
        return "ffmpeg"

    def _stream_url(self, song_id):
        return f"{self.API_BASE}/music/stream/{quote(str(song_id), safe='')}"

    @staticmethod
    def _track_text(track):
        if not track:
            return "Untitled track"
        artist = str(track.get("artist") or "").strip()
        title = str(track.get("title") or track.get("name") or "").strip()
        filename = str(track.get("file_name") or "").strip()
        if artist and title:
            label = f"{artist} — {title}"
        else:
            label = title or filename or "Untitled track"
        if filename and filename.casefold() not in label.casefold():
            label += f" [{filename}]"
        return label

    @staticmethod
    def _search_text(track):
        return " ".join(str(track.get(k) or "") for k in ("title", "name", "artist", "file_name", "category")).casefold()

    @staticmethod
    def _category_name(value):
        value = str(value or "all").strip().casefold()
        return value or "all"

    @classmethod
    def _category_key(cls, value):
        value = cls._category_name(value)
        return "".join(ch for ch in value if ch.isalnum())

    @classmethod
    def _resolve_category(cls, tracks, requested):
        requested = cls._category_name(requested)
        if requested == "all":
            return "all"
        categories = []
        seen = set()
        for track in tracks:
            category = cls._category_name(track.get("category"))
            if category not in seen:
                seen.add(category)
                categories.append(category)
        if requested in seen:
            return requested
        requested_key = cls._category_key(requested)
        for category in categories:
            if cls._category_key(category) == requested_key:
                return category
        fuzzy = [category for category in categories if requested_key and requested_key in cls._category_key(category)]
        if len(fuzzy) == 1:
            return fuzzy[0]
        return requested

    def _filter_tracks(self, tracks, category):
        category = self._resolve_category(tracks, category)
        if category == "all":
            return list(tracks)
        wanted = self._category_key(category)
        return [track for track in tracks if self._category_key(track.get("category")) == wanted]

    async def _fetch_tracks_from_url(self, url):
        await self._ensure_session()
        async with self.session.get(url) as response:
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
        tracks, seen = [], set()
        for song in songs:
            if not isinstance(song, dict):
                continue
            song_id = song.get("id")
            filename = str(song.get("file_name") or "")
            if not song_id or not filename.lower().split("?", 1)[0].endswith(self.AUDIO_EXTENSIONS):
                continue
            song_id = str(song_id)
            if song_id in seen:
                continue
            seen.add(song_id)
            track = dict(song)
            track["id"] = song_id
            track["url"] = self._stream_url(song_id)
            tracks.append(track)
        return tracks

    async def fetch_tracks(self, category=None):
        category = self._category_name(category)
        if category in self.CATEGORY_URLS:
            return await self._fetch_tracks_from_url(self.CATEGORY_URLS[category])
        return await self._fetch_tracks_from_url(self.MUSIC_LIST_URL)

    async def get_categories(self):
        counts = {}
        for track in await self.fetch_tracks():
            category = self._category_name(track.get("category"))
            counts[category] = counts.get(category, 0) + 1
        for name, url in self.CATEGORY_URLS.items():
            if name != "cut":
                try:
                    dedicated = await self._fetch_tracks_from_url(url)
                    if dedicated:
                        counts[name] = len(dedicated)
                except Exception as exc:
                    print(f"[JuiceVault] category endpoint {name} failed: {exc}")
        if "cuts" in counts:
            counts["cut"] = counts.pop("cuts")
        return counts

    async def categories(self):
        return await self.get_categories()

    async def _connect(self, guild, channel):
        voice = guild.voice_client
        if voice and voice.is_connected():
            if voice.channel.id != channel.id:
                await voice.move_to(channel)
            return voice
        return await channel.connect(reconnect=True, timeout=30)

    async def _wait_for_voice_idle(self, voice):
        if not voice:
            return True
        deadline = time.monotonic() + self.VOICE_STOP_TIMEOUT
        while voice.is_playing() or voice.is_paused():
            if time.monotonic() >= deadline:
                return False
            await asyncio.sleep(0.1)
        return True

    async def _download_track(self, track):
        await self._ensure_session()
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=30)
        suffix = os.path.splitext(str(track.get("file_name") or ".mp3"))[1] or ".mp3"
        if suffix.lower() not in self.AUDIO_EXTENSIONS:
            suffix = ".mp3"
        handle = tempfile.NamedTemporaryFile(mode="w+b", suffix=f".juicevault{suffix}", delete=False)
        path = handle.name
        try:
            async with self.session.get(track["url"], timeout=timeout) as response:
                if response.status != 200:
                    body = await response.text(errors="ignore")
                    raise RuntimeError(f"JuiceVault stream HTTP {response.status}: {body[:200]}")
                async for chunk in response.content.iter_chunked(self.DOWNLOAD_CHUNK_SIZE):
                    if chunk:
                        handle.write(chunk)
            handle.close()
            return path
        except Exception:
            try:
                handle.close()
            except OSError:
                pass
            self._remove_file(path)
            raise

    @staticmethod
    def _remove_file(path):
        if path:
            try:
                os.remove(path)
            except OSError:
                pass

    @staticmethod
    def _parse_duration(value):
        try:
            text = str(value or "").strip()
            if ":" in text:
                parts = [int(float(part)) for part in text.split(":")]
                total = 0
                for part in parts:
                    total = total * 60 + part
                return float(total)
            return float(text)
        except (TypeError, ValueError):
            return None

    def _effect_filter(self, effect):
        effect = str(effect or "none").casefold()
        filters = {
            "none": "aresample=async=1:first_pts=0",
            "bass": "bass=g=8:f=100,aresample=async=1:first_pts=0",
            "8d": "apulsator=hz=0.08:amount=1:offset_l=0:offset_r=0.5,haas=left_delay=2:right_delay=2,aresample=async=1:first_pts=0",
            "nightcore": "asetrate=44100*1.12,aresample=44100,atempo=1.0,aresample=async=1:first_pts=0",
            "slowed": "asetrate=44100*0.88,aresample=44100,atempo=1.0,aresample=async=1:first_pts=0",
            "echo": "aecho=0.8:0.88:700:0.25,aresample=async=1:first_pts=0",
            "wide": "stereotools=mlev=0.015:mpan=1,aresample=async=1:first_pts=0",
            "virtual bass": "virtualbass=cutoff=120:strength=2,aresample=async=1:first_pts=0",
        }
        return filters.get(effect, filters["none"])

    async def _disconnect(self, guild):
        voice = guild.voice_client
        if voice:
            try:
                if voice.is_playing() or voice.is_paused():
                    voice.stop()
                await self._wait_for_voice_idle(voice)
                await voice.disconnect(force=True)
            except Exception:
                pass

    async def _stop(self, guild_id):
        if guild_id in self.stop_events:
            self.stop_events[guild_id].set()
        if guild_id in self.skip_events:
            self.skip_events[guild_id].set()
        if guild_id in self.seek_events:
            self.seek_events[guild_id].set()
        task = self.tasks.pop(guild_id, None)
        if task and task is not asyncio.current_task():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        self.queues.pop(guild_id, None)
        self.manual_queues.pop(guild_id, None)
        self.current.pop(guild_id, None)
        self.search_results.pop(guild_id, None)
        self.last_error.pop(guild_id, None)
        self.failure_counts.pop(guild_id, None)
        self.skip_counts.pop(guild_id, None)
        self.seek_events.pop(guild_id, None)
        self.seek_targets.pop(guild_id, None)
        self.play_positions.pop(guild_id, None)
        self.effects.pop(guild_id, None)
        guild = self.bot.get_guild(guild_id)
        if guild:
            await self._disconnect(guild)

    async def _player(self, guild, channel):
        gid = guild.id
        task = asyncio.current_task()
        if self.tasks.get(gid) is not task:
            return
        stop = self.stop_events[gid]
        skip = self.skip_events[gid]
        seek = self.seek_events.setdefault(gid, asyncio.Event())
        self.manual_queues.setdefault(gid, [])
        self.effects.setdefault(gid, "none")
        try:
            while not stop.is_set():
                if self.tasks.get(gid) is not task:
                    return
                if not self.queues.get(gid):
                    try:
                        category = await self.config.guild(guild).category()
                        tracks = await self.fetch_tracks(category)
                        if category not in self.CATEGORY_URLS:
                            tracks = self._filter_tracks(tracks, category)
                        if not tracks:
                            self.last_error[gid] = f"Category `{category}` has no tracks."
                            await asyncio.sleep(15)
                            continue
                        self.queues[gid] = tracks
                    except Exception as exc:
                        self.last_error[gid] = f"API: {exc}"
                        print(f"[JuiceVault] API error: {exc}")
                        await asyncio.sleep(15)
                        continue
                try:
                    voice = await self._connect(guild, channel)
                except Exception as exc:
                    self.last_error[gid] = f"Voice: {type(exc).__name__}: {exc}"
                    print(f"[JuiceVault] voice error: {type(exc).__name__}: {exc}")
                    await asyncio.sleep(10)
                    continue
                if self.tasks.get(gid) is not task:
                    return
                if voice.is_playing() or voice.is_paused():
                    await asyncio.sleep(0.2)
                    continue
                if skip.is_set():
                    count = max(1, min(int(self.skip_counts.get(gid, 1)), 100))
                    skip.clear()
                    self.skip_counts[gid] = 0
                    self.play_positions.pop(gid, None)
                    for _ in range(min(count, len(self.queues.get(gid, [])))):
                        self.queues[gid].pop(0)
                    continue
                if seek.is_set():
                    seek.clear()
                    target = max(0.0, float(self.seek_targets.pop(gid, 0.0)))
                    current = self.current.get(gid)
                    if current:
                        self.manual_queues.setdefault(gid, []).insert(0, dict(current, _jv_seek_copy=True))
                    self.play_positions[gid] = target
                    continue
                if self.manual_queues.get(gid):
                    track = self.manual_queues[gid].pop(0)
                    source_type = "external" if track.get("_external") else "manual"
                else:
                    track = self.queues[gid].pop(0)
                    source_type = "normal"
                self.current[gid] = track
                start_offset = max(0.0, float(self.play_positions.pop(gid, 0.0)))
                duration = self._parse_duration(track.get("length"))
                if duration is not None:
                    start_offset = min(start_offset, max(0.0, duration - 0.25))
                started_at = time.monotonic()
                finished = asyncio.Event()
                playback_error = {"value": None}
                local_path = None
                log_file = None
                try:
                    local_path = await self._download_track(track)
                    log_file = tempfile.NamedTemporaryFile(mode="w+b", suffix=".juicevault-ffmpeg.log", delete=False)
                    def after(error):
                        if error:
                            playback_error["value"] = error
                            print(f"[JuiceVault] playback worker error: {type(error).__name__}: {error}")
                        self.bot.loop.call_soon_threadsafe(finished.set)
                    before = "-nostdin"
                    if start_offset > 0.05:
                        before = f"-nostdin -ss {start_offset:.3f}"
                    effect = self.effects.get(gid, "none")
                    options = f"-vn -af {self._effect_filter(effect)}"
                    source = discord.FFmpegPCMAudio(local_path, executable=self._ffmpeg_executable(), before_options=before, options=options, stderr=log_file)
                    voice.play(source, after=after)
                    voice._jv_started_at = time.monotonic()
                    self.play_positions[gid] = start_offset
                except Exception as exc:
                    self.last_error[gid] = f"Playback: {type(exc).__name__}: {exc}"
                    if log_file:
                        try:
                            log_file.close()
                        except OSError:
                            pass
                    self._remove_file(local_path)
                    if source_type == "external":
                        print(f"[JuiceVault] dropping unavailable external track {self._track_text(track)}: {type(exc).__name__}: {exc}")
                    else:
                        target = self.manual_queues if source_type == "manual" else self.queues
                        target.setdefault(gid, []).insert(0, track)
                    await asyncio.sleep(self.FAILURE_BACKOFF_SECONDS)
                    continue
                stop_task = asyncio.create_task(stop.wait())
                finish_task = asyncio.create_task(finished.wait())
                skip_task = asyncio.create_task(skip.wait())
                seek_task = asyncio.create_task(seek.wait())
                done, pending = await asyncio.wait({stop_task, finish_task, skip_task, seek_task}, return_when=asyncio.FIRST_COMPLETED)
                for p in pending:
                    p.cancel()
                explicit_skip = skip_task in done and skip.is_set()
                explicit_seek = seek_task in done and seek.is_set()
                elapsed = time.monotonic() - started_at
                self.play_positions[gid] = start_offset + max(0.0, elapsed)
                if explicit_skip or explicit_seek:
                    if voice.is_playing() or voice.is_paused():
                        voice.stop()
                    await self._wait_for_voice_idle(voice)
                else:
                    await self._wait_for_voice_idle(voice)
                if log_file:
                    try:
                        log_file.flush()
                        log_file.close()
                    except OSError:
                        pass
                self._remove_file(local_path)
                if stop.is_set() or self.tasks.get(gid) is not task:
                    return
                if explicit_seek:
                    seek.clear()
                    current = self.current.get(gid)
                    duration = self._parse_duration(current.get("length") if current else None)
                    current_pos = self.play_positions.get(gid, 0.0)
                    target = float(self.seek_targets.pop(gid, current_pos))
                    if duration is not None:
                        target = min(target, max(0.0, duration - 0.25))
                    target = max(0.0, target)
                    self.play_positions[gid] = target
                    if current:
                        self.manual_queues.setdefault(gid, []).insert(0, dict(current, _jv_seek_copy=True))
                    continue
                if explicit_skip:
                    skip.clear()
                    self.play_positions.pop(gid, None)
                    count = max(1, min(int(self.skip_counts.pop(gid, 1)), 100))
                    for _ in range(min(count, len(self.queues.get(gid, [])))):
                        self.queues[gid].pop(0)
                    self.failure_counts[gid] = 0
                    continue
                if playback_error["value"] or elapsed < 4.0:
                    self.failure_counts[gid] = self.failure_counts.get(gid, 0) + 1
                    if source_type == "external":
                        print(f"[JuiceVault] external track ended early; returning to JuiceVault queue: {self._track_text(track)}")
                        self.last_error[gid] = f"External track stopped after {elapsed:.1f}s; returning to JuiceVault."
                    else:
                        target = self.manual_queues if source_type == "manual" else self.queues
                        target.setdefault(gid, []).insert(0, track)
                        self.last_error[gid] = f"FFmpeg: track stopped after {elapsed:.1f}s."
                    await asyncio.sleep(30 if self.failure_counts[gid] >= self.MAX_CONSECUTIVE_FAILURES else self.FAILURE_BACKOFF_SECONDS)
                    if self.failure_counts[gid] >= self.MAX_CONSECUTIVE_FAILURES:
                        self.failure_counts[gid] = 0
                    continue
                self.play_positions.pop(gid, None)
                self.failure_counts[gid] = 0
                self.last_error.pop(gid, None)
                try:
                    del voice._jv_started_at
                except AttributeError:
                    pass
        except asyncio.CancelledError:
            raise
        finally:
            if self.tasks.get(gid) is task:
                await self._disconnect(guild)
                self.current.pop(gid, None)

    async def _request_skip(self, guild_id, count=1):
        guild = self.bot.get_guild(guild_id)
        voice = guild.voice_client if guild else None
        event = self.skip_events.get(guild_id)
        if guild_id not in self.tasks or not event or not voice or not voice.is_playing() or event.is_set():
            return False
        self.skip_counts[guild_id] = max(1, min(int(count), 100))
        event.set()
        voice.stop()
        return True

    async def _request_seek(self, guild_id, delta):
        guild = self.bot.get_guild(guild_id)
        voice = guild.voice_client if guild else None
        event = self.seek_events.get(guild_id)
        current = self.current.get(guild_id)
        if guild_id not in self.tasks or not event or not voice or not current:
            return None
        if not (voice.is_playing() or voice.is_paused()):
            return None
        if event.is_set():
            return None
        base = float(self.play_positions.get(guild_id, 0.0))
        started = getattr(voice, "_jv_started_at", None)
        if started is not None and voice.is_playing() and not voice.is_paused():
            base += max(0.0, time.monotonic() - started)
        duration = self._parse_duration(current.get("length"))
        target = max(0.0, base + float(delta))
        if duration is not None:
            target = min(target, max(0.0, duration - 0.25))
        self.seek_targets[guild_id] = target
        event.set()
        voice.stop()
        return target

    @commands.group(name="jv", invoke_without_command=True)
    @commands.guild_only()
    async def jv(self, ctx):
        await ctx.send("`4jv start` `4jv stop` `4jv skip` `4jv skip10` `4jv shuffle` `4jv categories` `4jv category <name>` `4jv search <name>` `4jv play <name>` `4jv refresh` `4jv status`")

    @jv.command(name="start")
    async def start(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Join a voice channel first.")
            return
        gid = ctx.guild.id
        if gid in self.tasks:
            voice = ctx.guild.voice_client
            if voice and voice.is_connected():
                await ctx.send("JuiceVault is already running.")
                return
            await self._stop(gid)
        category = await self.config.guild(ctx.guild).category()
        try:
            tracks = await self.fetch_tracks(category)
            if category not in self.CATEGORY_URLS:
                tracks = self._filter_tracks(tracks, category)
        except Exception as exc:
            await ctx.send(f"Unable to access the JuiceVault API: `{exc}`")
            return
        if not tracks:
            await ctx.send(f"Category `{category}` has no tracks.")
            return
        try:
            voice = await self._connect(ctx.guild, ctx.author.voice.channel)
        except Exception as exc:
            await ctx.send(f"❌ Unable to join voice: `{type(exc).__name__}: {exc}`")
            return
        self.queues[gid] = tracks
        self.manual_queues[gid] = []
        self.stop_events[gid] = asyncio.Event()
        self.skip_events[gid] = asyncio.Event()
        self.seek_events[gid] = asyncio.Event()
        self.skip_counts[gid] = 0
        self.failure_counts[gid] = 0
        self.seek_targets.pop(gid, None)
        self.play_positions.pop(gid, None)
        self.effects[gid] = "none"
        await self.config.guild(ctx.guild).enabled.set(True)
        await self.config.guild(ctx.guild).channel_id.set(ctx.author.voice.channel.id)
        self.tasks[gid] = asyncio.create_task(self._player(ctx.guild, ctx.author.voice.channel))
        await ctx.send(f"▶️ Started — `{len(tracks)}` tracks, category `{category}`. Connected to `{voice.channel.name}`.")

    @jv.command(name="stop")
    async def stop(self, ctx):
        await self.config.guild(ctx.guild).enabled.set(False)
        if ctx.guild.id not in self.tasks:
            await ctx.send("JuiceVault is not running.")
            return
        await self._stop(ctx.guild.id)
        await ctx.send("⏹️ Stopped.")

    @jv.command(name="skip", aliases=["next"])
    async def skip(self, ctx):
        if await self._request_skip(ctx.guild.id, 1):
            await ctx.send("⏭️ Skipped 1 track.")
        else:
            await ctx.send("No track is playing, or a skip is already in progress.")

    @jv.command(name="skip10")
    async def skip10(self, ctx):
        if await self._request_skip(ctx.guild.id, 10):
            await ctx.send("⏩ Skipped 10 tracks.")
        else:
            await ctx.send("No track is playing, or a skip is already in progress.")

    @jv.command(name="shuffle")
    async def shuffle(self, ctx):
        queue = self.queues.get(ctx.guild.id)
        if not queue:
            await ctx.send("The queue is empty.")
            return
        random.shuffle(queue)
        await ctx.send(f"🔀 Queue shuffled — `{len(queue)}` tracks.")

    @jv.command(name="categories")
    async def categories_cmd(self, ctx):
        try:
            counts = await self.get_categories()
        except Exception as exc:
            await ctx.send(f"Unable to load categories: `{exc}`")
            return
        lines = [f"**all** — {sum(counts.values())}"]
        lines.extend(f"**{name}** — {count}" for name, count in sorted(counts.items()))
        await ctx.send("🎚️ JuiceVault categories:\n" + "\n".join(lines[:50]))

    @jv.command(name="category")
    async def category(self, ctx, *, category: str):
        category = self._category_name(category)
        try:
            tracks = await self.fetch_tracks(category)
            if category not in self.CATEGORY_URLS:
                resolved = self._resolve_category(tracks, category)
                tracks = self._filter_tracks(tracks, resolved)
            else:
                resolved = category
        except Exception as exc:
            await ctx.send(f"Unable to access the API: `{exc}`")
            return
        if category != "all" and not tracks:
            await ctx.send(f"Category `{category}` does not exist or has no tracks.")
            return
        await self.config.guild(ctx.guild).category.set(resolved)
        if ctx.guild.id in self.tasks:
            self.queues[ctx.guild.id] = tracks
            self.failure_counts[ctx.guild.id] = 0
        await ctx.send(f"🎚️ Category set to **{resolved}** — `{len(tracks)}` tracks.")

    @jv.command(name="search")
    async def search(self, ctx, *, query: str):
        try:
            tracks = await self.fetch_tracks()
        except Exception as exc:
            await ctx.send(f"Search failed: `{exc}`")
            return
        matches = [track for track in tracks if query.casefold().strip() in self._search_text(track)][:10]
        if not matches:
            await ctx.send("No matches found.")
            return
        self.search_results[ctx.guild.id] = matches
        await ctx.send("🔎 JuiceVault search results:\n" + "\n".join(f"**{i}.** {self._track_text(track)} `[{self._category_name(track.get('category'))}]`" for i, track in enumerate(matches, 1)))

    @jv.command(name="play")
    async def play(self, ctx, *, query: str):
        gid = ctx.guild.id
        matches = self.search_results.get(gid, [])
        track = None
        try:
            index = int(query.strip())
        except ValueError:
            index = None
        if index is not None and 1 <= index <= len(matches):
            track = matches[index - 1]
        else:
            try:
                tracks = await self.fetch_tracks()
            except Exception as exc:
                await ctx.send(f"Search failed: `{exc}`")
                return
            candidates = [item for item in tracks if query.casefold().strip() in self._search_text(item)]
            track = candidates[0] if candidates else None
        if not track:
            await ctx.send("Track not found. Use `4jv search <name>`.")
            return
        if gid not in self.tasks:
            await ctx.send("The player is not running. Use `4jv start` first.")
            return
        self.manual_queues.setdefault(gid, []).append(track)
        await ctx.send(f"🎵 Added to Requested: **{self._track_text(track)}**")

    @jv.command(name="refresh")
    async def refresh(self, ctx):
        category = await self.config.guild(ctx.guild).category()
        try:
            filtered = await self.fetch_tracks(category)
            if category not in self.CATEGORY_URLS:
                filtered = self._filter_tracks(filtered, category)
        except Exception as exc:
            await ctx.send(f"Refresh failed: `{exc}`")
            return
        if not filtered:
            await ctx.send(f"Category `{category}` has no tracks.")
            return
        self.queues[ctx.guild.id] = filtered
        self.failure_counts[ctx.guild.id] = 0
        await ctx.send(f"🔄 Refresh — `{len(filtered)}` tracks in `{category}`.")

    @jv.command(name="status")
    async def status(self, ctx):
        gid = ctx.guild.id
        category = await self.config.guild(ctx.guild).category()
        voice = ctx.guild.voice_client
        current = self.current.get(gid)
        queue_size = len(self.queues.get(gid, []))
        manual_size = len(self.manual_queues.get(gid, []))
        error = self.last_error.get(gid)
        lines = [
            f"**Player:** {'ON' if gid in self.tasks else 'OFF'}",
            f"**Voice:** {voice.channel.name if voice and voice.is_connected() else 'not connected'}",
            f"**Category:** `{category}`",
            f"**Now Playing:** {self._track_text(current) if current else 'nothing'}",
            f"**Queue:** `{queue_size}`",
            f"**Requested:** `{manual_size}`",
            f"**Effect:** `{self.effects.get(gid, 'none')}`",
        ]
        if error:
            lines.append(f"**Last Error:** `{error}`")
        await ctx.send("\n".join(lines))
