import asyncio
import json
import os
import random
import re
import shutil
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

    VIP_USER_IDS = {612747552999211011, 340511257067257857}
    VIP_VIDEO_URL = "https://www.youtube.com/watch?v=7uNd46F3Ubs"
    VIP_START_OFFSET = 4.0
    VIP_PLAY_DURATION = 6.0
    VIP_DELAY_SECONDS = 3.0
    VIP_AUDIO_SLICED = os.path.join(tempfile.gettempdir(), "juicevault_vip_sliced_6s.mp3")
    VIP_AUDIO_RAW = os.path.join(tempfile.gettempdir(), "juicevault_vip_raw.mp3")
    VIP_COOLDOWN_SECONDS = 25.0

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
        self.current_files = {}
        self.last_error = {}
        self.search_results = {}
        self.failure_counts = {}
        self.seek_events = {}
        self.seek_targets = {}
        self.pause_after_seek = {}
        self.play_positions = {}
        self.effects = {}
        self.web_remote = None
        self._prefetched = {}
        self._prefetch_tasks = {}
        self._categories_cache = None
        self._categories_cache_time = 0.0
        self._tracks_cache = {}
        self._preserved_files = set()
        self._vip_cooldowns = {}
        self._vip_cache_task = None

    async def cog_load(self):
        await self._ensure_session()
        self.restore_task = asyncio.create_task(self._restore_players())
        self._vip_cache_task = asyncio.create_task(self._ensure_vip_audio())

    async def cog_unload(self):
        if self._vip_cache_task and not self._vip_cache_task.done():
            self._vip_cache_task.cancel()
        if self.restore_task:
            self.restore_task.cancel()
            try:
                await self.restore_task
            except asyncio.CancelledError:
                pass
            self.restore_task = None
        self._cleanup_prefetch()
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
        now = time.monotonic()
        if category in self._tracks_cache:
            cache_time, cached_tracks = self._tracks_cache[category]
            if now - cache_time < 300:  # 5 minute in-memory cache
                return list(cached_tracks)

        if category in self.CATEGORY_URLS:
            tracks = await self._fetch_tracks_from_url(self.CATEGORY_URLS[category])
        else:
            tracks = await self._fetch_tracks_from_url(self.MUSIC_LIST_URL)

        if tracks:
            self._tracks_cache[category] = (now, list(tracks))
        return tracks

    async def get_categories(self):
        now = time.monotonic()
        if self._categories_cache and (now - self._categories_cache_time < 600):
            return dict(self._categories_cache)

        counts = {}
        tracks = await self.fetch_tracks()
        counts["all"] = len(tracks)
        session_count = 0
        for track in tracks:
            category = self._category_name(track.get("category"))
            if category != "all":
                counts[category] = counts.get(category, 0) + 1
            if bool(track.get("is_session_edit")):
                session_count += 1
        if session_count:
            counts["session edits"] = session_count

        missing = [name for name, url in self.CATEGORY_URLS.items() if name != "cut" and counts.get(name, 0) == 0]
        if missing:
            tasks = [self._fetch_tracks_from_url(self.CATEGORY_URLS[name]) for name in missing]
            try:
                results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=2.5)
                for name, res in zip(missing, results):
                    if isinstance(res, list) and res:
                        counts[name] = len(res)
            except Exception:
                pass
        if "cuts" in counts:
            counts["cut"] = counts.pop("cuts")
        if "stem" in counts and "stems" not in counts:
            counts["stems"] = counts.pop("stem")
        self._categories_cache = dict(counts)
        self._categories_cache_time = now
        return dict(counts)

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
            await asyncio.sleep(0.02)
        return True

    def _cleanup_prefetch(self):
        for path in list(self._prefetched.values()):
            self._remove_file(path)
        self._prefetched.clear()
        for task in list(self._prefetch_tasks.values()):
            task.cancel()
        self._prefetch_tasks.clear()

    def _trigger_next_prefetch(self, gid):
        next_track = None
        if self.manual_queues.get(gid):
            next_track = self.manual_queues[gid][0]
        elif self.queues.get(gid):
            next_track = self.queues[gid][0]
        if next_track and not next_track.get("_external") and next_track.get("url"):
            url = next_track["url"]
            if url not in self._prefetched and url not in self._prefetch_tasks:
                self._prefetch_tasks[url] = asyncio.create_task(self._do_prefetch(next_track))

    async def _do_prefetch(self, track):
        url = track.get("url")
        try:
            path = await self._download_track(dict(track, _skip_cache=True))
            if url and path and os.path.isfile(path):
                self._prefetched[url] = path
            return path
        except Exception:
            return None
        finally:
            if url:
                self._prefetch_tasks.pop(url, None)

    async def _download_track(self, track):
        cached = track.get("_cached_file")
        if cached and os.path.isfile(cached) and os.path.getsize(cached) > 1024:
            return cached

        url = track.get("url")
        skip_cache = track.get("_skip_cache", False)
        if not skip_cache and url:
            if url in self._prefetched:
                path = self._prefetched.pop(url)
                if os.path.isfile(path) and os.path.getsize(path) > 1024:
                    return path
            if url in self._prefetch_tasks:
                task = self._prefetch_tasks.pop(url)
                try:
                    path = await task
                    if path and os.path.isfile(path) and os.path.getsize(path) > 1024:
                        return path
                except Exception:
                    pass

        await self._ensure_session()
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=15, sock_read=30)
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
                chunk_size = getattr(self, "DOWNLOAD_CHUNK_SIZE", 256 * 1024)
                async for chunk in response.content.iter_chunked(chunk_size):
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
            if "juicevault_soundboard" in path or "juicevault_vip" in path:
                return
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
        eff = str(effect or "none").casefold().replace("-", " ").replace("_", " ").strip()
        if eff in ("flat", "off", "normal", "none", "original"):
            key = "none"
        elif "night" in eff:
            key = "nightcore"
        elif "slow" in eff:
            key = "slowed"
        elif "8d" in eff:
            key = "8d"
        elif "sub" in eff or "virtual" in eff:
            key = "virtual bass"
        elif "wide" in eff or "stereo" in eff:
            key = "wide"
        elif "echo" in eff or "reverb" in eff:
            key = "echo"
        elif "bass" in eff:
            key = "bass"
        else:
            key = "none"

        filters = {
            "none": "aresample=48000:async=1",
            "bass": "bass=g=11:f=110:w=0.6,aresample=48000:async=1",
            "8d": "apulsator=mode=sine:hz=0.12:amount=0.95,extrastereo=m=1.8,aresample=48000:async=1",
            "nightcore": "asetrate=48000*1.22,aresample=48000,atempo=1.0,aresample=48000:async=1",
            "slowed": "asetrate=48000*0.86,aresample=48000,atempo=1.0,aresample=48000:async=1",
            "echo": "aecho=0.8:0.85:60:0.35,aresample=48000:async=1",
            "wide": "extrastereo=m=2.2,aresample=48000:async=1",
            "virtual bass": "bass=g=16:f=55:w=0.5,equalizer=f=35:width_type=h:width=40:g=10,aresample=48000:async=1",
        }
        return filters.get(key, filters["none"])

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
        self.current_files.pop(guild_id, None)
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
                    skip.clear()
                    self.skip_counts[gid] = 0
                    self.play_positions.pop(gid, None)
                    continue
                if seek.is_set():
                    seek.clear()
                    target = max(0.0, float(self.seek_targets.pop(gid, 0.0)))
                    current = self.current.get(gid)
                    if current:
                        self.manual_queues.setdefault(gid, []).insert(0, dict(current, _jv_seek_copy=True, _cached_file=self.current_files.get(gid)))
                    self.play_positions[gid] = target
                    continue
                if self.manual_queues.get(gid):
                    track = self.manual_queues[gid].pop(0)
                    source_type = "external" if track.get("_external") else "manual"
                else:
                    track = self.queues[gid].pop(0)
                    source_type = "normal"
                self.current[gid] = track
                if track.get("_resume_position") is not None:
                    start_offset = max(0.0, float(track.pop("_resume_position")))
                    if not track.pop("_resume_was_playing", True):
                        if not hasattr(self, "pause_after_seek"):
                            self.pause_after_seek = {}
                        self.pause_after_seek[gid] = True
                else:
                    start_offset = max(0.0, float(self.play_positions.get(gid, 0.0)))
                self.play_positions[gid] = start_offset
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
                    self.current_files[gid] = local_path
                    log_file = tempfile.NamedTemporaryFile(mode="w+b", suffix=".juicevault-ffmpeg.log", delete=False)
                    def after(error):
                        if error:
                            playback_error["value"] = error
                            print(f"[JuiceVault] playback worker error: {type(error).__name__}: {error}")
                        self.bot.loop.call_soon_threadsafe(finished.set)
                    before = "-nostdin -probesize 32k -analyzeduration 0"
                    clip_start = track.get("_clip_start")
                    if clip_start is not None and not track.get("_is_pre_sliced", False):
                        start_offset = max(0.0, float(clip_start))
                    if start_offset > 0.05:
                        before = f"-nostdin -ss {start_offset:.3f} -probesize 32k -analyzeduration 0"
                    effect = self.effects.get(gid, "none")
                    options = f"-vn -af {self._effect_filter(effect)}"
                    if track.get("_clip_duration"):
                        options += f" -t {float(track['_clip_duration']):.3f}"
                    source = discord.FFmpegPCMAudio(local_path, executable=self._ffmpeg_executable(), before_options=before, options=options, stderr=log_file)
                    voice.play(source, after=after)
                    voice._jv_started_at = time.monotonic()
                    self.play_positions[gid] = start_offset
                    if self.pause_after_seek.pop(gid, False) and voice.is_playing():
                        voice.pause()
                    self._trigger_next_prefetch(gid)
                    if hasattr(self, "web_remote") and self.web_remote:
                        asyncio.create_task(self.web_remote.broadcast_state(gid))
                    ui = self.bot.get_cog("JuiceVaultUI")
                    if ui:
                        asyncio.create_task(ui.update_panel(gid))
                except Exception as exc:
                    self.last_error[gid] = f"Playback: {type(exc).__name__}: {exc}"
                    if log_file:
                        try:
                            log_file.close()
                        except OSError:
                            pass
                    self.current_files.pop(gid, None)
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
                explicit_skip = skip.is_set() or (skip_task in done)
                explicit_seek = seek.is_set() or (seek_task in done)
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
                if not explicit_seek:
                    self.current_files.pop(gid, None)
                    if local_path and local_path not in getattr(self, "_preserved_files", set()):
                        self._remove_file(local_path)
                    elif local_path:
                        self._preserved_files.discard(local_path)
                if stop.is_set() or self.tasks.get(gid) is not task:
                    if explicit_seek:
                        self.current_files.pop(gid, None)
                        self._remove_file(local_path)
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
                        self.manual_queues.setdefault(gid, []).insert(0, dict(current, _jv_seek_copy=True, _cached_file=local_path))
                    continue
                if explicit_skip:
                    skip.clear()
                    self.play_positions.pop(gid, None)
                    count = max(1, min(int(self.skip_counts.pop(gid, 1)), 100))
                    # The skipped track is already finished. Drop additional tracks only if count > 1:
                    if count > 1:
                        for _ in range(min(count - 1, len(self.queues.get(gid, [])))):
                            if self.queues.get(gid):
                                self.queues[gid].pop(0)
                    self.failure_counts[gid] = 0
                    continue
                if playback_error["value"] is not None:
                    self.failure_counts[gid] = self.failure_counts.get(gid, 0) + 1
                    err = playback_error["value"]
                    print(f"[JuiceVault] playback worker error on {self._track_text(track)}: {err}")
                    self.last_error[gid] = f"Playback: {err}"
                    if source_type != "external":
                        target = self.manual_queues if source_type == "manual" else self.queues
                        target.setdefault(gid, []).insert(0, track)
                    await asyncio.sleep(self.FAILURE_BACKOFF_SECONDS)
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
        if guild_id not in self.tasks or not event or not voice or not (voice.is_playing() or voice.is_paused()) or event.is_set():
            return False
        self.skip_counts[guild_id] = max(1, min(int(count), 100))
        event.set()
        voice.stop()
        return True

    async def _request_seek(self, guild_id, delta=0.0, target_position=None):
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
        duration = self._parse_duration(current.get("length"))
        if target_position is not None:
            target = max(0.0, float(target_position))
        else:
            base = float(self.play_positions.get(guild_id, 0.0))
            started = getattr(voice, "_jv_started_at", None)
            if started is not None and voice.is_playing() and not voice.is_paused():
                base += max(0.0, time.monotonic() - started)
            target = max(0.0, base + float(delta))
        if duration is not None:
            target = min(target, max(0.0, duration - 0.25))
        if not hasattr(self, "pause_after_seek"):
            self.pause_after_seek = {}
        self.pause_after_seek[guild_id] = bool(voice.is_paused())
        self.seek_targets[guild_id] = target
        self.play_positions[guild_id] = target
        event.set()
        voice.stop()
        return target

    async def _ensure_vip_audio(self):
        if os.path.isfile(self.VIP_AUDIO_SLICED) and os.path.getsize(self.VIP_AUDIO_SLICED) > 1024:
            return self.VIP_AUDIO_SLICED, True
        if os.path.isfile(self.VIP_AUDIO_RAW) and os.path.getsize(self.VIP_AUDIO_RAW) > 1024:
            return self.VIP_AUDIO_RAW, False

        def _do_download():
            try:
                from .external_search_patch import _download_with_ytdlp
                tempdir = tempfile.mkdtemp(prefix="juicevault-vip-")
                try:
                    downloaded = _download_with_ytdlp(self.VIP_VIDEO_URL, tempdir)
                    if downloaded and os.path.isfile(downloaded) and os.path.getsize(downloaded) > 1024:
                        ffmpeg_bin = self._ffmpeg_executable()
                        sliced_target = os.path.join(tempdir, "vip_sliced.mp3")
                        slice_cmd = [
                            ffmpeg_bin,
                            "-y",
                            "-ss", str(self.VIP_START_OFFSET),
                            "-t", str(self.VIP_PLAY_DURATION),
                            "-i", downloaded,
                            "-vn",
                            "-acodec", "libmp3lame",
                            "-b:a", "192k",
                            sliced_target,
                        ]
                        try:
                            import subprocess
                            sub_res = subprocess.run(
                                slice_cmd,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                                timeout=15,
                            )
                            if sub_res.returncode == 0 and os.path.isfile(sliced_target) and os.path.getsize(sliced_target) > 512:
                                shutil.copyfile(sliced_target, self.VIP_AUDIO_SLICED)
                                return self.VIP_AUDIO_SLICED, True
                        except Exception as slice_err:
                            print(f"[JuiceVault] VIP ffmpeg slice notice: {slice_err}")

                        shutil.copyfile(downloaded, self.VIP_AUDIO_RAW)
                        return self.VIP_AUDIO_RAW, False
                finally:
                    shutil.rmtree(tempdir, ignore_errors=True)
            except Exception as exc:
                print(f"[JuiceVault] VIP audio cache error: {exc}")
                return None, False

        return await asyncio.to_thread(_do_download)

    async def _trigger_vip_join(self, guild, member, target_channel_id):
        # 3-second delay from when VIP joins
        await asyncio.sleep(self.VIP_DELAY_SECONDS)

        gid = guild.id
        voice = guild.voice_client
        if not voice or not voice.is_connected() or gid not in self.tasks:
            return

        # Check if member is still connected to the voice channel where bot is playing
        current_ch = getattr(getattr(member, "voice", None), "channel", None)
        if not current_ch or current_ch.id != voice.channel.id or current_ch.id != target_channel_id:
            return

        current = self.current.get(gid)
        if current and current.get("_is_vip"):
            return

        vip_audio_res = await self._ensure_vip_audio()
        vip_audio = vip_audio_res[0] if isinstance(vip_audio_res, tuple) else vip_audio_res
        is_pre_sliced = vip_audio_res[1] if isinstance(vip_audio_res, tuple) else False

        if not vip_audio or not os.path.isfile(vip_audio):
            print(f"[JuiceVault] VIP audio not available for member {member.id}.")
            return

        if not hasattr(self, "_preserved_files"):
            self._preserved_files = set()

        was_playing = bool(voice.is_playing() and not voice.is_paused())
        current_pos = 0.0
        local_path = self.current_files.get(gid)

        if current and not current.get("_is_vip") and not current.get("_is_soundboard"):
            base = float(self.play_positions.get(gid, 0.0))
            started = getattr(voice, "_jv_started_at", None)
            if started is not None and was_playing:
                base += max(0.0, time.monotonic() - started)
            current_pos = base

            if local_path and os.path.isfile(local_path):
                self._preserved_files.add(local_path)

            resume_track = dict(
                current,
                _jv_seek_copy=True,
                _cached_file=local_path,
                _resume_position=current_pos,
                _resume_was_playing=was_playing,
            )
            self.manual_queues.setdefault(gid, []).insert(0, resume_track)

        vip_track = {
            "id": f"vip:clip:{int(time.time())}",
            "title": "VIP Greeting",
            "artist": f"VIP: {member.display_name}",
            "length": "0:06",
            "file_name": "vip_clip.mp3",
            "_cached_file": vip_audio,
            "_is_vip": True,
            "_is_soundboard": True,
            "_sound_color": "#ff4d4f",
            "_clip_start": self.VIP_START_OFFSET,
            "_clip_duration": self.VIP_PLAY_DURATION,
            "_is_pre_sliced": is_pre_sliced,
            "url": self.VIP_VIDEO_URL,
        }

        self.manual_queues.setdefault(gid, []).insert(0, vip_track)
        self.play_positions[gid] = 0.0
        if not hasattr(self, "pause_after_seek"):
            self.pause_after_seek = {}
        self.pause_after_seek[gid] = False

        if voice.is_playing() or voice.is_paused():
            voice.stop()
        else:
            skip_evt = self.skip_events.get(gid)
            if skip_evt:
                skip_evt.set()

        if hasattr(self, "web_remote") and self.web_remote:
            asyncio.create_task(self.web_remote.broadcast_state(gid))
        ui = self.bot.get_cog("JuiceVaultUI")
        if ui:
            asyncio.create_task(ui.update_panel(gid))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if getattr(member, "bot", False):
            return
        if member.id not in self.VIP_USER_IDS:
            return
        if before.channel == after.channel or after.channel is None:
            return

        guild = member.guild
        gid = guild.id
        voice = guild.voice_client

        if not voice or not voice.is_connected() or voice.channel != after.channel:
            return
        if gid not in self.tasks or self.tasks[gid].done():
            return

        now = time.monotonic()
        if now - self._vip_cooldowns.get(member.id, 0.0) < self.VIP_COOLDOWN_SECONDS:
            return
        self._vip_cooldowns[member.id] = now

        target_channel_id = after.channel.id
        asyncio.create_task(self._trigger_vip_join(guild, member, target_channel_id))

    @commands.group(name="jv", invoke_without_command=True)
    @commands.guild_only()
    async def jv(self, ctx):
        await ctx.send("`4jv start` `4jv stop` `4jv skip` `4jv skip10` `4jv shuffle` `4jv categories` `4jv category <name>` `4jv search <name>` `4jv play <name>` `4jv refresh` `4jv status` `4jv remote`")

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
        self._cleanup_prefetch()
        self._trigger_next_prefetch(ctx.guild.id)
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
        q_clean = query.strip()
        is_external = (
            q_clean.startswith(("http://", "https://", "www."))
            or "youtube.com" in q_clean.lower()
            or "youtu.be" in q_clean.lower()
            or "soundcloud.com" in q_clean.lower()
            or "bandcamp.com" in q_clean.lower()
        )
        if is_external:
            if gid not in self.tasks:
                await ctx.send("The player is not running. Use `4jv start` first.")
                return
            try:
                from .external_search_patch import _extract_search, _source_name, _format_seconds
                info = await asyncio.to_thread(_extract_search, q_clean)
                if info.get("_is_playlist"):
                    entries = info.get("entries") or []
                    if not entries:
                        await ctx.send("No playable tracks found in playlist.")
                        return
                    self.manual_queues.setdefault(gid, []).extend(entries)
                    pl_title = str(info.get("title") or "Playlist").strip()
                    await ctx.send(f"Added external playlist: **{pl_title}** ({len(entries)} tracks) to Requested.")
                    if hasattr(self, "web_remote") and self.web_remote:
                        asyncio.create_task(self.web_remote.broadcast_state(gid))
                    ui = self.bot.get_cog("JuiceVaultUI")
                    if ui:
                        asyncio.create_task(ui.update_panel(gid))
                    return
                else:
                    title = str(info.get("title") or info.get("fulltitle") or q_clean).strip()
                    artist = str(info.get("artist") or info.get("uploader") or info.get("channel") or "Unknown artist").strip()
                    source = str(info.get("_source") or _source_name(info)).strip()
                    url = info.get("webpage_url") or info.get("original_url") or info.get("url")
                    dur = info.get("length") or info.get("duration_string") or _format_seconds(info.get("duration")) or "—"
                    track = {
                        "id": f"external:{info.get('id') or abs(hash(q_clean))}",
                        "title": title,
                        "artist": artist,
                        "length": dur,
                        "file_name": f"external-{info.get('id') or 'track'}.webm",
                        "url": url,
                        "_external": True,
                        "_source": source,
                        "_webpage_url": url,
                        "_query": q_clean,
                    }
                    if info.get("cover_url"):
                        track["cover_url"] = info["cover_url"]
                    self.manual_queues.setdefault(gid, []).append(track)
                    await ctx.send(f"Added external track to Requested: **{title}** (`{source}`)")
                    if hasattr(self, "web_remote") and self.web_remote:
                        asyncio.create_task(self.web_remote.broadcast_state(gid))
                    ui = self.bot.get_cog("JuiceVaultUI")
                    if ui:
                        asyncio.create_task(ui.update_panel(gid))
                    return
            except Exception as exc:
                await ctx.send(f"Failed to load external audio: `{exc}`")
                return

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
        await ctx.send(f"Added to Requested: **{self._track_text(track)}**")

    @commands.guild_only()
    @commands.command(name="lyrics")
    async def global_lyrics(self, ctx):
        """View lyrics options for the currently playing song."""
        await self._lyrics_command(ctx)

    @jv.command(name="lyrics")
    async def jv_lyrics(self, ctx):
        """View lyrics options for the currently playing song."""
        await self._lyrics_command(ctx)

    async def _lyrics_command(self, ctx):
        track = self.current.get(ctx.guild.id)
        if not track:
            await ctx.send("No track is currently playing.")
            return
        ui = self.bot.get_cog("JuiceVaultUI")
        panel = getattr(ui, "panel", None) or ui
        from .eq_ui_patch import JuiceVaultLyricsChoiceView
        view = JuiceVaultLyricsChoiceView(panel, ctx.guild.id, track, ctx.channel)
        await ctx.send(embed=view.build_embed(), view=view)

    @jv.command(name="refresh")
    async def refresh(self, ctx):
        self._categories_cache = None
        self._tracks_cache.clear()
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

    @jv.group(name="remote", aliases=["web", "phone"], invoke_without_command=True)
    async def remote(self, ctx):
        """View your mobile phone web remote link and scannable QR code."""
        if getattr(self, "web_remote", None):
            await self.web_remote.send_remote_embed(ctx)
        else:
            await ctx.send("JuiceVault Web Remote is not loaded.")

    @remote.command(name="port")
    async def remote_port(self, ctx, port: int):
        """Change the web remote server port (default: 8088)."""
        if not (1 <= port <= 65535):
            await ctx.send("Port must be between 1 and 65535.")
            return
        if getattr(self, "web_remote", None):
            await self.web_remote.config.port.set(port)
            await self.web_remote.start_server()
            await ctx.send(f"✅ Web Remote port set to `{port}` and server restarted.")
        else:
            await ctx.send("JuiceVault Web Remote is not loaded.")

    @remote.command(name="token")
    async def remote_token(self, ctx, *, new_token: str = None):
        """View or regenerate the secret auth token for mobile pairing."""
        if getattr(self, "web_remote", None):
            if new_token:
                clean = new_token.strip()
                await self.web_remote.config.token.set(clean)
                await ctx.send(f"✅ Auth token updated to `{clean}`.")
            else:
                token = await self.web_remote.config.token()
                await ctx.send(f"🔑 Current secret auth token: ||`{token}`||")
        else:
            await ctx.send("JuiceVault Web Remote is not loaded.")

    @remote.command(name="url")
    async def remote_url(self, ctx, *, custom_url: str = None):
        """Set a custom public domain or tunnel URL (e.g. https://juice.example.com)."""
        if getattr(self, "web_remote", None):
            if custom_url and custom_url.lower() != "clear":
                clean = custom_url.strip().rstrip("/")
                await self.web_remote.config.custom_url.set(clean)
                await ctx.send(f"✅ Custom URL set to: `{clean}`")
            else:
                await self.web_remote.config.custom_url.set(None)
                await ctx.send("✅ Custom URL cleared. Using local network IP.")
        else:
            await ctx.send("JuiceVault Web Remote is not loaded.")

    @remote.command(name="tunnel")
    async def remote_tunnel(self, ctx, action: str = "start"):
        """Spawn a zero-config Cloudflare Quick Tunnel for free HTTPS with trusted SSL.
        
        Usage:
        4jv remote tunnel         -> Start Cloudflare HTTPS tunnel
        4jv remote tunnel stop    -> Stop Cloudflare HTTPS tunnel
        """
        if not getattr(self, "web_remote", None):
            await ctx.send("JuiceVault Web Remote is not loaded.")
            return

        if action.lower() in ("stop", "close", "off"):
            await self.web_remote.stop_cloudflare_tunnel()
            await ctx.send("⏹️ Cloudflare Quick Tunnel stopped. Reverted to standard IP access.")
            return

        async with ctx.typing():
            try:
                msg = await ctx.send("⏳ Initiating Cloudflare Quick Tunnel (obtaining trusted HTTPS domain)…")
                tunnel_url = await self.web_remote.start_cloudflare_tunnel()
                await msg.delete()
                await self.web_remote.send_remote_embed(ctx)
            except Exception as exc:
                await ctx.send(f"❌ Failed to start Cloudflare tunnel: `{exc}`")

    @remote.command(name="https")
    async def remote_https(self, ctx, state: str = "on"):
        """Enable or disable direct HTTPS using an auto-generated self-signed SSL certificate.
        
        Usage:
        4jv remote https on       -> Auto-generate SSL cert & run HTTPS on your port
        4jv remote https off      -> Revert to plain HTTP
        """
        if not getattr(self, "web_remote", None):
            await ctx.send("JuiceVault Web Remote is not loaded.")
            return

        from redbot.core.data_manager import cog_data_path
        data_dir = cog_data_path(raw_name="JuiceVault")
        cert_path = str(data_dir / "juicevault_cert.pem")
        key_path = str(data_dir / "juicevault_key.pem")

        if state.lower() in ("off", "disable", "stop", "clear"):
            await self.web_remote.config.ssl_cert.set(None)
            await self.web_remote.config.ssl_key.set(None)
            await self.web_remote.start_server()
            port = await self.web_remote.config.port()
            await ctx.send(f"✅ HTTPS disabled. Web remote is running plain HTTP on port `{port}`.")
            return

        if not (os.path.isfile(cert_path) and os.path.isfile(key_path)):
            created = self.web_remote.generate_self_signed_cert(cert_path, key_path)
            if not created:
                await ctx.send("❌ Could not auto-generate SSL certificate. Use `4jv remote tunnel` for free 1-click Cloudflare HTTPS!")
                return

        await self.web_remote.config.ssl_cert.set(cert_path)
        await self.web_remote.config.ssl_key.set(key_path)
        await self.web_remote.start_server()
        port = await self.web_remote.config.port()
        await ctx.send(f"🔒 **HTTPS Enabled!** Auto-generated self-signed SSL certificate and restarted server on port `{port}`.")
        await self.web_remote.send_remote_embed(ctx)

    @remote.command(name="ssl")
    async def remote_ssl(self, ctx, cert_path: str = None, key_path: str = None):
        """Configure custom SSL certificate for direct HTTPS, or pass 'clear' to disable."""
        if getattr(self, "web_remote", None):
            if cert_path and cert_path.lower() == "clear":
                await self.web_remote.config.ssl_cert.set(None)
                await self.web_remote.config.ssl_key.set(None)
                await self.web_remote.start_server()
                await ctx.send("✅ SSL certificate cleared. Running plain HTTP.")
                return

            if not cert_path or not key_path:
                cert = await self.web_remote.config.ssl_cert()
                key = await self.web_remote.config.ssl_key()
                if cert and key:
                    await ctx.send(f"🔒 SSL currently active:\n• Cert: `{cert}`\n• Key: `{key}`\nUse `4jv remote ssl clear` to reset.")
                else:
                    await ctx.send("🔒 SSL not configured. Provide paths: `4jv remote ssl <cert_path> <key_path>` or use `4jv remote tunnel` for instant zero-config HTTPS.")
                return

            import os
            if not os.path.isfile(cert_path):
                await ctx.send(f"❌ Certificate file not found: `{cert_path}`")
                return
            if not os.path.isfile(key_path):
                await ctx.send(f"❌ Private key file not found: `{key_path}`")
                return

            await self.web_remote.config.ssl_cert.set(cert_path)
            await self.web_remote.config.ssl_key.set(key_path)
            await self.web_remote.start_server()
            port = await self.web_remote.config.port()
            await ctx.send(f"✅ SSL configured! Restarted server with HTTPS on port `{port}`.")
        else:
            await ctx.send("JuiceVault Web Remote is not loaded.")

    @remote.command(name="restart")
    async def remote_restart(self, ctx):
        """Restart the web remote server."""
        if getattr(self, "web_remote", None):
            await self.web_remote.start_server()
            await ctx.send("🔄 Web remote server restarted.")
        else:
            await ctx.send("JuiceVault Web Remote is not loaded.")

    @remote.command(name="toggle")
    async def remote_toggle(self, ctx):
        """Enable or disable the web remote server."""
        if getattr(self, "web_remote", None):
            current = await self.web_remote.config.enabled()
            new_state = not current
            await self.web_remote.config.enabled.set(new_state)
            if new_state:
                await self.web_remote.start_server()
                await ctx.send("▶️ Web remote server enabled and started.")
            else:
                await self.web_remote.stop_server()
                await ctx.send("⏹️ Web remote server disabled.")
        else:
            await ctx.send("JuiceVault Web Remote is not loaded.")
