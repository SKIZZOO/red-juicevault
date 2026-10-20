import asyncio
import json
import os
import random
import re
import shutil
import tempfile
import time
import warnings
from urllib.parse import quote

# Suppress Python 3.11/3.12/3.13 deprecation warnings from legacy audio libraries like speech_recognition/aifc
warnings.filterwarnings("ignore", category=DeprecationWarning, module=r".*speech_recognition.*")
warnings.filterwarnings("ignore", message=r".*aifc.*", category=DeprecationWarning)

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
    VIP_DELAY_SECONDS = 0.5
    VIP_AUDIO_SLICED = os.path.join(tempfile.gettempdir(), "juicevault_vip_sliced_6s.wav")
    VIP_AUDIO_RAW = os.path.join(tempfile.gettempdir(), "juicevault_vip_raw.mp3")
    VIP_COOLDOWN_SECONDS = 20.0

    SKIZZOO_VIDEO_URL = "https://www.youtube.com/watch?v=QeX0wYlnUt0"
    SKIZZOO_START_OFFSET = 1.0
    SKIZZOO_PLAY_DURATION = 5.0  # From 1st second until sec 6 in the video -> 5 seconds duration
    SKIZZOO_DELAY_SECONDS = 0.5
    SKIZZOO_AUDIO_SLICED = os.path.join(tempfile.gettempdir(), "juicevault_skizzoo_entrance_5s.wav")
    SKIZZOO_AUDIO_RAW = os.path.join(tempfile.gettempdir(), "juicevault_skizzoo_raw.mp3")
    SKIZZOO_COOLDOWN_SECONDS = 20.0

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=918273645, force_registration=True)
        self.config.register_guild(
            enabled=False,
            channel_id=None,
            category="all",
            last_track=None,
            last_position=0.0,
            voice_commands_enabled=True,
            learned_wake_words=[],
            learned_song_queries={},
            saved_session=None,
        )
        self.config.register_global(
            groq_api_key=None,
        )
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
        self._last_played_files = {}
        self._last_played_tracks = {}
        self._last_positions = {}
        self.last_error = {}
        self.search_results = {}
        self.failure_counts = {}
        self.seek_events = {}
        self.seek_targets = {}
        self.pause_after_seek = {}
        self.play_positions = {}
        self.effects = {}
        self.loops = {}
        self.history = {}
        self.history_pos = {}
        self.web_remote = None
        self._prefetched = {}
        self._prefetch_tasks = {}
        self._categories_cache = None
        self._categories_cache_time = 0.0
        self._tracks_cache = {}
        self._preserved_files = set()
        self._vip_cooldowns = {}
        self._vip_cache_task = None
        self._skizzoo_cooldowns = {}
        self._skizzoo_cache_task = None
        self._groq_api_key = None

    async def cog_load(self):
        await self._ensure_session()
        self.restore_task = asyncio.create_task(self._restore_players())
        self._vip_cache_task = asyncio.create_task(self._ensure_vip_audio())
        self._skizzoo_cache_task = asyncio.create_task(self._ensure_skizzoo_audio())

    async def cog_unload(self):
        if self._skizzoo_cache_task and not self._skizzoo_cache_task.done():
            self._skizzoo_cache_task.cancel()
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

        # Preserve active playback sessions across cog updates, reloads, and bot restarts
        if not hasattr(self.bot, "_jv_data"):
            self.bot._jv_data = {}
        saved_sessions = self.bot._jv_data.setdefault("saved_sessions", {})
        preserved_files = self.bot._jv_data.setdefault("preserved_files", set())

        for gid in list(self.tasks):
            try:
                guild = self.bot.get_guild(gid)
                voice = guild.voice_client if guild else None
                cur_track = self.current.get(gid)
                # Accurately compute dynamic elapsed playback position
                cur_pos = self.get_position(gid)
                res_track = None
                if cur_track:
                    res_track = dict(cur_track)
                    res_track["_resume_position"] = cur_pos
                    res_track["_resume_was_playing"] = bool(voice and (voice.is_playing() or not voice.is_paused()))
                    # Preserve local cached audio file so resume doesn't need to re-download
                    cur_file = self.current_files.get(gid)
                    if cur_file and os.path.isfile(cur_file):
                        res_track["_cached_file"] = cur_file
                        self._preserved_files.add(cur_file)
                        preserved_files.add(cur_file)

                # Determine target voice channel
                target_chid = None
                if voice and voice.channel:
                    target_chid = voice.channel.id
                if not target_chid and guild:
                    try:
                        target_chid = await self.config.guild(guild).channel_id()
                    except Exception:
                        pass

                session_dict = {
                    "channel_id": target_chid,
                    "current_track": res_track,
                    "queue": list(self.queues.get(gid, [])),
                    "manual_queue": list(self.manual_queues.get(gid, [])),
                    "loop": getattr(self, "loops", {}).get(gid, "off"),
                    "effects": self.effects.get(gid, "none"),
                    "position": cur_pos,
                    "history": list(self.history.get(gid, [])),
                    "saved_at": time.time(),
                }
                saved_sessions[gid] = session_dict

                # Also persist to config so cold bot restarts also resume!
                if guild:
                    try:
                        await self.config.guild(guild).enabled.set(True)
                        if target_chid:
                            await self.config.guild(guild).channel_id.set(target_chid)
                        if res_track:
                            clean_t = self._clean_track_for_config(res_track)
                            await self.config.guild(guild).last_track.set(clean_t)
                            await self.config.guild(guild).last_position.set(float(cur_pos))
                        clean_session = {
                            "channel_id": target_chid,
                            "current_track": self._clean_track_for_config(res_track) if res_track else None,
                            "queue": [self._clean_track_for_config(t) for t in self.queues.get(gid, []) if isinstance(t, dict)],
                            "manual_queue": [self._clean_track_for_config(t) for t in self.manual_queues.get(gid, []) if isinstance(t, dict)],
                            "loop": session_dict["loop"],
                            "effects": session_dict["effects"],
                            "position": float(cur_pos),
                            "history": [self._clean_track_for_config(t) for t in self.history.get(gid, []) if isinstance(t, dict)],
                            "saved_at": session_dict["saved_at"],
                        }
                        await self.config.guild(guild).saved_session.set(clean_session)
                    except Exception as cfg_err:
                        print(f"[JuiceVault] Error saving session to config for guild {gid}: {cfg_err}")

                # Clean up voice recognition sink on this voice client so the new cog can attach cleanly
                try:
                    from .voice_recognition import _active_sinks
                    sink = _active_sinks.pop(gid, None)
                    if sink and hasattr(sink, "cleanup"):
                        sink.cleanup()
                    if voice and hasattr(voice, "is_listening") and voice.is_listening():
                        voice.stop_listening()
                except Exception:
                    pass
            except Exception as e:
                print(f"[JuiceVault] Error saving session for guild {gid}: {e}")

        for guild_id in list(self.tasks):
            try:
                # Disconnect=False keeps the Discord voice connection open across reloads for instant, gapless resume!
                await self._stop(guild_id, disconnect=False)
            except Exception as e:
                print(f"[JuiceVault] Error stopping guild {guild_id}: {e}")
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
            await asyncio.sleep(1.5)
            saved_sessions = getattr(self.bot, "_jv_data", {}).get("saved_sessions", {})
            all_guild_configs = await self.config.all_guilds()

            # Discover all guilds that need playback restoration:
            candidate_guild_ids = set(saved_sessions.keys())
            for gid, settings in all_guild_configs.items():
                if settings.get("enabled") or settings.get("saved_session"):
                    candidate_guild_ids.add(gid)

            for guild in self.bot.guilds:
                if guild.voice_client and guild.voice_client.channel:
                    candidate_guild_ids.add(guild.id)

            for guild_id in candidate_guild_ids:
                if guild_id in self.tasks:
                    continue
                guild = self.bot.get_guild(guild_id)
                if guild is None:
                    continue

                settings = all_guild_configs.get(guild_id, {})
                saved = saved_sessions.pop(guild_id, None)
                if not saved and settings.get("saved_session"):
                    saved = settings.get("saved_session")
                if settings.get("saved_session"):
                    asyncio.create_task(self.config.guild(guild).saved_session.set(None))

                channel = None
                voice = guild.voice_client
                if voice and voice.channel:
                    channel = voice.channel
                elif saved and saved.get("channel_id"):
                    channel = guild.get_channel(saved["channel_id"])
                elif settings.get("channel_id"):
                    channel = guild.get_channel(settings["channel_id"])

                if not channel or not isinstance(channel, (discord.VoiceChannel, discord.StageChannel)):
                    continue

                self.stop_events[guild_id] = asyncio.Event()
                self.skip_events[guild_id] = asyncio.Event()
                self.seek_events[guild_id] = asyncio.Event()
                self.skip_counts[guild_id] = 0

                if saved:
                    self.queues[guild_id] = list(saved.get("queue") or [])
                    mq = list(saved.get("manual_queue") or [])
                    cur_t = saved.get("current_track")
                    pos = float(saved.get("position", 0.0))

                    if cur_t:
                        cur_t = dict(cur_t)
                        if cur_t.get("_resume_position") is None:
                            cur_t["_resume_position"] = pos
                        mq.insert(0, cur_t)
                        self.play_positions[guild_id] = pos
                    elif pos > 0:
                        self.play_positions[guild_id] = pos

                    self.manual_queues[guild_id] = mq
                    self.effects[guild_id] = saved.get("effects", "none")
                    self.loops[guild_id] = saved.get("loop", "off")
                    self.history[guild_id] = list(saved.get("history") or [])
                else:
                    self.manual_queues[guild_id] = []
                    self.effects[guild_id] = "none"

                await self.config.guild(guild).enabled.set(True)
                await self.config.guild(guild).channel_id.set(channel.id)

                self.tasks[guild_id] = asyncio.create_task(self._player(guild, channel))
                print(f"[JuiceVault Restore] ✅ Restored playback for {guild.name} in '{channel.name}' from position {self.play_positions.get(guild_id, 0.0):.1f}s")
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

    @staticmethod
    def _jv_cache_path(url: str) -> str:
        import hashlib, tempfile as _tmp
        safe = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(_tmp.gettempdir(), "juicevault_track_cache", f"tracks_{safe}.json")

    def _jv_write_cache(self, url: str, tracks: list) -> None:
        try:
            import time as _time
            path = self._jv_cache_path(url)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"saved_at": _time.time(), "url": url, "tracks": tracks}, f)
            os.replace(tmp, path)
        except Exception as exc:
            print(f"[JuiceVault] cache write failed: {exc}")

    def _jv_read_cache(self, url: str):
        import time as _time
        try:
            path = self._jv_cache_path(url)
            if not os.path.isfile(path):
                return None
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tracks = data.get("tracks")
            if isinstance(tracks, list) and tracks:
                age_h = (_time.time() - float(data.get("saved_at", 0))) / 3600
                print(f"[JuiceVault] Offline cache: {len(tracks)} tracks for {url} (cached {age_h:.1f}h ago)")
                return tracks
        except Exception as exc:
            print(f"[JuiceVault] cache read failed: {exc}")
        return None

    async def _fetch_tracks_from_url(self, url):
        await self._ensure_session()
        # ── Try live API ──
        try:
            async with self.session.get(url) as response:
                text = await response.text(errors="ignore")
                status = response.status
        except Exception as exc:
            cached = self._jv_read_cache(url)
            if cached is not None:
                return cached
            err_msg = f"{type(exc).__name__}" + (f": {exc}" if str(exc).strip() else "")
            print(f"[JuiceVault] Network error fetching {url}: {err_msg}")
            raise RuntimeError(
                "JuiceVault API is unreachable and no offline cache is available. "
                "Please wait for the server to come back online."
            ) from exc

        if status != 200:
            if status >= 500 or status in (408, 429):
                # Server outage / Cloudflare tunnel down — try disk cache
                cached = self._jv_read_cache(url)
                if cached is not None:
                    return cached
                print(f"[JuiceVault] API returned HTTP {status} for {url}, and no offline cache was found.")
                raise RuntimeError(
                    f"JuiceVault API is temporarily down (HTTP {status}). "
                    "No offline cache is available yet — please wait for the server to recover."
                )
            # 4xx — surface a clean message (strip raw HTML)
            try:
                payload = json.loads(text)
                detail = payload.get("error", text[:300]) if isinstance(payload, dict) else text[:300]
            except json.JSONDecodeError:
                detail = text[:300]
            if "<html" in detail.lower():
                detail = f"HTTP {status} (Cloudflare/proxy error)"
            raise RuntimeError(f"JuiceVault API HTTP {status}: {detail}")

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
        # ── Persist to disk on every successful fetch ──
        if tracks:
            self._jv_write_cache(url, tracks)
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
            if not hasattr(voice, "_jv_connected_at"):
                voice._jv_connected_at = time.time()
            return voice
        voice = await channel.connect(reconnect=True, timeout=30)
        voice._jv_connected_at = time.time()
        return voice

    async def _wait_for_voice_idle(self, voice):
        if not voice:
            return True
        deadline = time.monotonic() + self.VOICE_STOP_TIMEOUT
        while voice.is_playing() or voice.is_paused():
            if time.monotonic() >= deadline:
                return False
            await asyncio.sleep(0.02)
        return True

    def _cleanup_prefetch(self, gid=None):
        if gid is None:
            for path in list(self._prefetched.values()):
                if not any(p == path for p in self.current_files.values()):
                    self._remove_file(path)
            self._prefetched.clear()
            for task in list(self._prefetch_tasks.values()):
                task.cancel()
            self._prefetch_tasks.clear()
            return

        # Scoped cleanup: protect tracks queued or playing in other guilds
        other_needed_urls = set()
        for other_gid, q in self.manual_queues.items():
            if other_gid != gid and q:
                for t in q[:3]:
                    if t.get("url"):
                        other_needed_urls.add(t["url"])
        for other_gid, q in self.queues.items():
            if other_gid != gid and q:
                for t in q[:3]:
                    if t.get("url"):
                        other_needed_urls.add(t["url"])

        guild_next_url = None
        if self.manual_queues.get(gid):
            guild_next_url = self.manual_queues[gid][0].get("url")
        elif self.queues.get(gid):
            guild_next_url = self.queues[gid][0].get("url")

        for url in list(self._prefetch_tasks.keys()):
            if url != guild_next_url and url not in other_needed_urls:
                task = self._prefetch_tasks.pop(url, None)
                if task:
                    task.cancel()

        for url, path in list(self._prefetched.items()):
            if url != guild_next_url and url not in other_needed_urls:
                if not any(p == path for p in self.current_files.values()):
                    self._remove_file(path)
                self._prefetched.pop(url, None)

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
        if not url:
            track_id = track.get("id")
            if track_id and not track.get("_external"):
                url = self._stream_url(track_id)
                track["url"] = url
            else:
                try:
                    catalog = await self.fetch_tracks("all")
                    t_title = str(track.get("title") or track.get("name") or "").strip().lower()
                    for item in catalog:
                        if t_title and t_title in str(item.get("title") or "").strip().lower():
                            if item.get("url"):
                                url = item["url"]
                                track["url"] = url
                                track.setdefault("file_name", item.get("file_name"))
                                break
                except Exception:
                    pass

        if not url:
            raise RuntimeError(f"Track '{track.get('title', 'Unknown')}' has no stream URL available")

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
            async with self.session.get(url, timeout=timeout) as response:
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
            if "juicevault_soundboard" in path or "juicevault_vip" in path or "juicevault_skizzoo" in path:
                return
            try:
                os.remove(path)
            except OSError:
                pass

    def _schedule_file_removal(self, path, delay=25):
        if not path or "juicevault_soundboard" in path or "juicevault_vip" in path or "juicevault_skizzoo" in path:
            return
        async def _remover():
            try:
                await asyncio.sleep(delay)
                other_playing = any(p == path for p in getattr(self, "current_files", {}).values())
                other_prefetched = any(p == path for p in getattr(self, "_prefetched", {}).values())
                if not other_playing and not other_prefetched:
                    self._remove_file(path)
            except Exception:
                pass
        try:
            self.bot.loop.create_task(_remover())
        except Exception:
            self._remove_file(path)

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

    def _clean_track_for_config(self, track: dict) -> dict:
        if not isinstance(track, dict):
            return {}
        clean = {}
        for k, v in track.items():
            if k in ("_cached_file", "_jv_seek_copy", "_retry_count"):
                continue
            if isinstance(v, (str, int, float, bool)) or v is None:
                clean[k] = v
            elif isinstance(v, (list, tuple)):
                clean[k] = [x for x in v if isinstance(x, (str, int, float, bool))]
            elif isinstance(v, dict):
                clean[k] = {str(dk): dv for dk, dv in v.items() if isinstance(dv, (str, int, float, bool))}
        return clean

    def _save_last_track_state(self, guild_id: int, track: dict, position: float = 0.0):
        if not track or not isinstance(track, dict):
            return
        if track.get("_is_vip") or track.get("_is_soundboard"):
            return
        clean_track = self._clean_track_for_config(track)
        if not clean_track:
            return
        pos = max(0.0, float(position or 0.0))
        self._last_played_tracks[guild_id] = clean_track
        self._last_positions[guild_id] = pos
        asyncio.create_task(self._persist_last_track(guild_id, clean_track, pos))

    async def _persist_last_track(self, guild_id: int, clean_track: dict, position: float):
        try:
            guild = self.bot.get_guild(guild_id)
            if guild:
                await self.config.guild(guild).last_track.set(clean_track)
                await self.config.guild(guild).last_position.set(float(position))
        except Exception as e:
            print(f"[JuiceVault] Error persisting last track state for guild {guild_id}: {e}")

    async def _persist_last_position(self, guild_id: int, position: float):
        try:
            guild = self.bot.get_guild(guild_id)
            if guild:
                await self.config.guild(guild).last_position.set(float(position))
        except Exception:
            pass

    async def _get_last_track_to_resume(self, guild):
        gid = guild.id
        track = self._last_played_tracks.get(gid)
        pos = self._last_positions.get(gid)

        if not track:
            try:
                track = await self.config.guild(guild).last_track()
            except Exception:
                track = None

        if pos is None:
            try:
                pos = await self.config.guild(guild).last_position()
            except Exception:
                pos = 0.0

        if not track or not isinstance(track, dict):
            return None

        resume_track = dict(track)
        pos = max(0.0, float(pos or 0.0))
        duration = self._parse_duration(resume_track.get("length") or resume_track.get("duration"))

        # If it was stopped within the last 5 seconds of the song or past duration, start from beginning:
        if duration and (pos >= duration - 5.0):
            resume_track["_resume_position"] = 0.0
        elif pos > 3.0:
            resume_track["_resume_position"] = pos
        else:
            resume_track["_resume_position"] = 0.0

        return resume_track

    def _align_queue_with_last_track(self, gid: int, last_t: dict):
        q = self.queues.get(gid) or []
        if not q or not last_t:
            return
        target_id = str(last_t.get("id") or "")
        idx = -1
        if target_id:
            for i, item in enumerate(q):
                if str(item.get("id")) == target_id:
                    idx = i
                    break
        if idx == -1:
            target_url = last_t.get("url") or last_t.get("webpage_url")
            if target_url:
                for i, item in enumerate(q):
                    if item.get("url") == target_url or item.get("webpage_url") == target_url:
                        idx = i
                        break
        if idx != -1:
            # Reorder queue so the track following last_t plays next:
            self.queues[gid] = q[idx + 1:] + q[:idx]

    async def _disconnect(self, guild):
        if guild:
            gid = guild.id
            cur = self.current.get(gid)
            pos = self.get_position(gid)
            if cur and not cur.get("_is_vip") and not cur.get("_is_soundboard"):
                self._save_last_track_state(gid, cur, pos)
        voice = guild.voice_client
        if voice:
            try:
                if voice.is_playing() or voice.is_paused():
                    voice.stop()
                await self._wait_for_voice_idle(voice)
                await voice.disconnect(force=True)
            except Exception:
                pass

    async def _stop(self, guild_id, disconnect=True):
        cur = self.current.get(guild_id)
        pos = self.get_position(guild_id)
        if cur and not cur.get("_is_vip") and not cur.get("_is_soundboard"):
            self._save_last_track_state(guild_id, cur, pos)
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
        self.history_pos.pop(guild_id, None)
        self.effects.pop(guild_id, None)
        guild = self.bot.get_guild(guild_id)
        if guild:
            if disconnect:
                await self._disconnect(guild)
            elif guild.voice_client:
                voice = guild.voice_client
                if voice.is_playing() or voice.is_paused():
                    voice.stop()

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
        is_first_track = True

        # Always mark guild as enabled and save active voice channel
        try:
            await self.config.guild(guild).enabled.set(True)
            if channel:
                await self.config.guild(guild).channel_id.set(channel.id)
        except Exception:
            pass

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
                if is_first_track:
                    is_first_track = False
                    if not self.manual_queues.get(gid):
                        last_t = await self._get_last_track_to_resume(guild)
                        if last_t:
                            self._align_queue_with_last_track(gid, last_t)
                            self.manual_queues.setdefault(gid, []).insert(0, last_t)
                if self.manual_queues.get(gid):
                    track = self.manual_queues[gid].pop(0)
                    source_type = "external" if track.get("_external") else "manual"
                else:
                    track = self.queues[gid].pop(0)
                    source_type = "normal"
                prev_track = self.current.get(gid)
                if (
                    prev_track
                    and not prev_track.get("_is_vip")
                    and not prev_track.get("_is_soundboard")
                    and not track.get("_from_history")
                    and not track.get("_jv_seek_copy")
                    and not track.get("_is_vip")
                    and not track.get("_is_soundboard")
                ):
                    hist = self.history.setdefault(gid, [])
                    if not hist or str(hist[-1].get("id")) != str(prev_track.get("id")):
                        hist.append(dict(prev_track))
                        del hist[:-50]
                if (
                    not track.get("_from_history")
                    and not track.get("_jv_seek_copy")
                    and not track.get("_is_vip")
                    and not track.get("_is_soundboard")
                ):
                    self.history_pos[gid] = None
                self.current[gid] = track
                if track.get("_resume_position") is not None:
                    start_offset = max(0.0, float(track.pop("_resume_position")))
                    if not track.pop("_resume_was_playing", True):
                        if not hasattr(self, "pause_after_seek"):
                            self.pause_after_seek = {}
                        self.pause_after_seek[gid] = True
                else:
                    start_offset = 0.0
                self.play_positions[gid] = start_offset
                if not track.get("_is_vip") and not track.get("_is_soundboard"):
                    self._save_last_track_state(gid, track, start_offset)
                duration = self._parse_duration(track.get("length"))
                if duration is not None:
                    start_offset = min(start_offset, max(0.0, duration - 0.25))
                started_at = time.monotonic()
                finished = asyncio.Event()
                playback_error = {"value": None}
                local_path = None
                log_file = None
                async def _start_playback_worker():
                    nonlocal local_path, log_file, start_offset
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
                    try:
                        from .voice_recognition import DuckingAudioSource
                        mixer = DuckingAudioSource(source)
                        voice._jv_mixer = mixer
                        play_source = mixer
                    except Exception:
                        play_source = source
                    await self._wait_for_voice_idle(voice)
                    voice.play(play_source, after=after)
                    voice._jv_started_at = time.monotonic()
                    self.play_positions[gid] = start_offset
                    if self.pause_after_seek.pop(gid, False) and voice.is_playing():
                        voice.pause()

                try:
                    # Strict 30-second hard timeout for track download, preparation, and playback startup
                    # "Daca piesa nu continua dupa 30 sec, dai skip si canta alta."
                    await asyncio.wait_for(_start_playback_worker(), timeout=30.0)
                    self._trigger_next_prefetch(gid)
                    if hasattr(self, "web_remote") and self.web_remote:
                        asyncio.create_task(self.web_remote.broadcast_state(gid))
                    ui = self.bot.get_cog("JuiceVaultUI")
                    if ui:
                        asyncio.create_task(ui.update_panel(gid))
                except asyncio.TimeoutError:
                    t_title = self._track_text(track)
                    print(f"[JuiceVault] ⚠️ Track '{t_title}' did not start/continue within 30s. Skipping to next track!")
                    self.last_error[gid] = f"Timeout (>30s): {t_title}"
                    if log_file:
                        try:
                            log_file.close()
                        except OSError:
                            pass
                    self.current_files.pop(gid, None)
                    self._remove_file(local_path)
                    skip_msg = f"⚠️ Piesa **{t_title}** nu a pornit în 30s ➔ Skip automat la următoarea piesă! ⏭️"
                    ui = self.bot.get_cog("JuiceVaultUI")
                    if ui:
                        asyncio.create_task(ui.update_panel(gid))
                    try:
                        cfg_ch = await self.config.guild(guild).channel_id()
                        ch = guild.get_channel(cfg_ch) if cfg_ch else None
                        if ch and hasattr(ch, "send"):
                            asyncio.create_task(ch.send(skip_msg))
                    except Exception:
                        pass
                    continue
                except Exception as exc:
                    self.last_error[gid] = f"Playback: {type(exc).__name__}: {exc}"
                    if log_file:
                        try:
                            log_file.close()
                        except OSError:
                            pass
                    self.current_files.pop(gid, None)
                    self._remove_file(local_path)
                    is_resumed_track = bool(track.get("_resume_position") is not None or track.get("_is_seek_copy"))
                    if is_resumed_track or source_type == "external":
                        t_title = self._track_text(track)
                        print(f"[JuiceVault] Failed starting '{t_title}': {exc}. Skipping to next track!")
                        continue
                    retries = track.get("_retry_count", 0) + 1
                    track["_retry_count"] = retries
                    if retries > 2:
                        print(f"[JuiceVault] dropping failed track {self._track_text(track)} after {retries} attempts: {type(exc).__name__}: {exc}")
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
                completed = bool(not explicit_skip and not explicit_seek and not stop.is_set() and (finish_task in done))
                track_dur = self._parse_duration(track.get("length"))
                started = getattr(voice, "_jv_started_at", None)
                if completed and track_dur and track_dur > 0:
                    elapsed = track_dur
                elif started is not None:
                    eff = str(self.effects.get(gid, "none")).lower()
                    effect_speed = 1.22 if "night" in eff else (0.86 if "slow" in eff else 1.0)
                    elapsed = max(0.0, float(self.play_positions.get(gid, 0.0)) + (time.monotonic() - started) * effect_speed)
                    if track_dur and track_dur > 0:
                        elapsed = min(elapsed, track_dur)
                else:
                    elapsed = self.get_position(gid)
                self.play_positions[gid] = elapsed
                if hasattr(self, "web_remote") and self.web_remote:
                    self.web_remote.record_playback(elapsed_seconds=max(0.0, elapsed), completed=completed, guild_id=gid)
                if explicit_skip or explicit_seek:
                    if voice.is_playing() or voice.is_paused():
                        voice.stop()
                    await self._wait_for_voice_idle(voice)
                else:
                    await self._wait_for_voice_idle(voice)
                if hasattr(voice, "_jv_mixer"):
                    voice._jv_mixer = None
                if log_file:
                    try:
                        log_file.flush()
                        log_file.close()
                    except OSError:
                        pass
                if not explicit_seek:
                    self.current_files.pop(gid, None)
                    if not hasattr(self, "_last_played_files"):
                        self._last_played_files = {}
                    if local_path and os.path.isfile(local_path):
                        self._last_played_files[gid] = local_path
                    if local_path and local_path not in getattr(self, "_preserved_files", set()):
                        other_playing = any(p == local_path for g, p in self.current_files.items() if g != gid)
                        other_prefetched = any(p == local_path for p in self._prefetched.values())
                        if not other_playing and not other_prefetched:
                            self._schedule_file_removal(local_path, 25)
                    elif local_path:
                        self._preserved_files.discard(local_path)
                if stop.is_set() or self.tasks.get(gid) is not task:
                    if explicit_seek:
                        self.current_files.pop(gid, None)
                        if not hasattr(self, "_last_played_files"):
                            self._last_played_files = {}
                        if local_path and os.path.isfile(local_path):
                            self._last_played_files[gid] = local_path
                        other_playing = any(p == local_path for g, p in self.current_files.items() if g != gid)
                        other_prefetched = any(p == local_path for p in self._prefetched.values())
                        if not other_playing and not other_prefetched:
                            self._schedule_file_removal(local_path, 25)
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
                    retries = track.get("_retry_count", 0) + 1
                    track["_retry_count"] = retries
                    if retries >= self.MAX_TRACK_RETRIES:
                        self.last_error[gid] = f"Playback: skipped unplayable track {self._track_text(track)}"
                        self._append_dead_track(track)
                        print(f"[JuiceVault] dropping unplayable track after {retries} retries: {self._track_text(track)}")
                    else:
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
            cur = self.current.get(gid)
            pos = self.get_position(gid)
            if cur and not cur.get("_is_vip") and not cur.get("_is_soundboard"):
                self._save_last_track_state(gid, cur, pos)
            if self.tasks.get(gid) is task:
                await self._disconnect(guild)
                self.current.pop(gid, None)

    def get_position(self, guild_id: int) -> float:
        """Returns the current playback position in seconds, monotonically accurate across pause/resume."""
        base = float(self.play_positions.get(guild_id, 0.0))
        guild = self.bot.get_guild(guild_id)
        voice = guild.voice_client if guild else None
        if not voice:
            return base
        eff = str(self.effects.get(guild_id, "none")).lower()
        effect_speed = 1.22 if "night" in eff else (0.86 if "slow" in eff else 1.0)
        started = getattr(voice, "_jv_started_at", None)
        if started is not None and voice.is_playing() and not voice.is_paused():
            base += max(0.0, (time.monotonic() - started) * effect_speed)
        current = self.current.get(guild_id)
        if current:
            duration = self._parse_duration(current.get("length"))
            if duration is not None and duration > 0:
                base = min(base, duration)
        return max(0.0, base)

    def pause_playback(self, guild_id: int) -> bool:
        """Pause voice playback and freeze elapsed position accurately."""
        guild = self.bot.get_guild(guild_id)
        voice = guild.voice_client if guild else None
        if not voice:
            return False
        if voice.is_playing():
            self.play_positions[guild_id] = self.get_position(guild_id)
            voice.pause()
            return True
        return False

    def resume_playback(self, guild_id: int) -> bool:
        """Resume voice playback without losing position tracking."""
        guild = self.bot.get_guild(guild_id)
        voice = guild.voice_client if guild else None
        if not voice:
            return False
        if voice.is_paused():
            voice._jv_started_at = time.monotonic()
            voice.resume()
            return True
        return False

    async def _request_skip(self, guild_id, count=1):
        guild = self.bot.get_guild(guild_id)
        voice = guild.voice_client if guild else None
        event = self.skip_events.get(guild_id)
        if guild_id not in self.tasks or not event or not voice or not (voice.is_playing() or voice.is_paused()) or event.is_set():
            return False
        self.skip_counts[guild_id] = max(1, min(int(count), 100))
        self.play_positions[guild_id] = 0.0
        if voice:
            voice._jv_started_at = None
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
            base = self.get_position(guild_id)
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

    def _is_skizzoo(self, member) -> bool:
        if not member:
            return False
        names = [
            getattr(member, "name", ""),
            getattr(member, "display_name", ""),
            getattr(member, "global_name", ""),
            getattr(member, "nick", ""),
        ]
        combined = " ".join(str(n or "").lower() for n in names)
        if "skizzoo" in combined:
            return True
        owner_id = getattr(self.bot, "owner_id", None)
        if owner_id and member.id == owner_id:
            return True
        owner_ids = getattr(self.bot, "owner_ids", None) or set()
        if owner_ids and member.id in owner_ids:
            return True
        if member.id in self.VIP_USER_IDS and "ski" in combined:
            return True
        return False

    async def _ensure_skizzoo_audio(self):
        if os.path.isfile(self.SKIZZOO_AUDIO_SLICED) and os.path.getsize(self.SKIZZOO_AUDIO_SLICED) > 1024:
            return self.SKIZZOO_AUDIO_SLICED, True
        if os.path.isfile(self.SKIZZOO_AUDIO_RAW) and os.path.getsize(self.SKIZZOO_AUDIO_RAW) > 1024:
            raw_path = self.SKIZZOO_AUDIO_RAW
            try:
                ffmpeg_bin = self._ffmpeg_executable()
                slice_cmd = [
                    ffmpeg_bin,
                    "-y",
                    "-ss", str(self.SKIZZOO_START_OFFSET),
                    "-t", str(self.SKIZZOO_PLAY_DURATION),
                    "-i", raw_path,
                    "-vn",
                    "-ar", "48000",
                    "-ac", "2",
                    self.SKIZZOO_AUDIO_SLICED,
                ]
                import subprocess
                sub_res = subprocess.run(slice_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
                if sub_res.returncode == 0 and os.path.isfile(self.SKIZZOO_AUDIO_SLICED) and os.path.getsize(self.SKIZZOO_AUDIO_SLICED) > 512:
                    return self.SKIZZOO_AUDIO_SLICED, True
            except Exception:
                pass
            return self.SKIZZOO_AUDIO_RAW, False

        def _do_download():
            try:
                from .external_search_patch import _download_with_ytdlp
                tempdir = tempfile.mkdtemp(prefix="juicevault-skizzoo-")
                try:
                    downloaded = _download_with_ytdlp(self.SKIZZOO_VIDEO_URL, tempdir)
                    if downloaded and os.path.isfile(downloaded) and os.path.getsize(downloaded) > 1024:
                        shutil.copyfile(downloaded, self.SKIZZOO_AUDIO_RAW)
                        ffmpeg_bin = self._ffmpeg_executable()
                        sliced_target = os.path.join(tempdir, "skizzoo_sliced.wav")
                        slice_cmd = [
                            ffmpeg_bin,
                            "-y",
                            "-ss", str(self.SKIZZOO_START_OFFSET),
                            "-t", str(self.SKIZZOO_PLAY_DURATION),
                            "-i", downloaded,
                            "-vn",
                            "-ar", "48000",
                            "-ac", "2",
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
                                shutil.copyfile(sliced_target, self.SKIZZOO_AUDIO_SLICED)
                                return self.SKIZZOO_AUDIO_SLICED, True
                        except Exception as slice_err:
                            print(f"[JuiceVault] Skizzoo entrance slice notice: {slice_err}")

                        return self.SKIZZOO_AUDIO_RAW, False
                finally:
                    shutil.rmtree(tempdir, ignore_errors=True)
            except Exception as exc:
                print(f"[JuiceVault] Skizzoo entrance audio cache error: {exc}")
                return None, False

        return await asyncio.to_thread(_do_download)

    async def _trigger_skizzoo_join(self, guild, member, target_channel_id):
        await asyncio.sleep(self.SKIZZOO_DELAY_SECONDS)

        gid = guild.id
        voice = guild.voice_client
        if not voice or not voice.is_connected() or voice.channel is None:
            return

        current_ch = getattr(getattr(member, "voice", None), "channel", None)
        if not current_ch or current_ch.id != voice.channel.id or current_ch.id != target_channel_id:
            return

        res = await self._ensure_skizzoo_audio()
        audio_path = res[0] if isinstance(res, tuple) else res
        is_pre_sliced = res[1] if isinstance(res, tuple) else False

        if not audio_path or not os.path.isfile(audio_path):
            print(f"[JuiceVault Entrance] Skizzoo entrance audio not available.")
            return

        exe = self._ffmpeg_executable()
        before_opts = "-nostdin"
        extra_opts = "-vn"
        if not is_pre_sliced:
            before_opts = f"-nostdin -ss {self.SKIZZOO_START_OFFSET:.3f}"
            extra_opts = f"-vn -t {self.SKIZZOO_PLAY_DURATION:.3f}"

        from .voice_recognition import DuckingAudioSource
        mixer = getattr(voice, "_jv_mixer", None)
        if mixer is None and hasattr(voice, "source") and isinstance(voice.source, DuckingAudioSource):
            mixer = voice.source
            voice._jv_mixer = mixer
        elif mixer is None and voice.is_playing() and hasattr(voice, "source") and voice.source:
            try:
                mixer = DuckingAudioSource(voice.source)
                voice.source = mixer
                if hasattr(voice, "_player") and voice._player:
                    voice._player.source = mixer
                voice._jv_mixer = mixer
            except Exception:
                mixer = None

        if voice.is_playing() and mixer is not None:
            entrance_source = discord.FFmpegPCMAudio(audio_path, executable=exe, before_options=before_opts, options=extra_opts)
            mixer.set_overlay(entrance_source)
            print(f"[JuiceVault Entrance] 👑 Playing Skizzoo entrance theme (1s-6s) over ducked music (18%) in '{guild.name}'")
        elif not voice.is_playing():
            entrance_source = discord.FFmpegPCMAudio(audio_path, executable=exe, before_options=before_opts, options=extra_opts)
            voice.play(entrance_source)
            print(f"[JuiceVault Entrance] 👑 Playing Skizzoo entrance theme (1s-6s) directly in '{guild.name}'")

    def _is_vip(self, member) -> bool:
        if not member:
            return False
        if member.id in self.VIP_USER_IDS:
            return True
        for r in getattr(member, "roles", []):
            name = getattr(r, "name", "").strip().lower()
            if name in ("vip", "[vip]", "★ vip", "⭐ vip", "v.i.p", "v.i.p.") or name.startswith("vip"):
                return True
        return False

    async def _ensure_vip_audio(self):
        if os.path.isfile(self.VIP_AUDIO_SLICED) and os.path.getsize(self.VIP_AUDIO_SLICED) > 1024:
            return self.VIP_AUDIO_SLICED, True
        if os.path.isfile(self.VIP_AUDIO_RAW) and os.path.getsize(self.VIP_AUDIO_RAW) > 1024:
            raw_path = self.VIP_AUDIO_RAW
            try:
                ffmpeg_bin = self._ffmpeg_executable()
                slice_cmd = [
                    ffmpeg_bin,
                    "-y",
                    "-ss", str(self.VIP_START_OFFSET),
                    "-t", str(self.VIP_PLAY_DURATION),
                    "-i", raw_path,
                    "-vn",
                    "-ar", "48000",
                    "-ac", "2",
                    self.VIP_AUDIO_SLICED,
                ]
                import subprocess
                sub_res = subprocess.run(slice_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
                if sub_res.returncode == 0 and os.path.isfile(self.VIP_AUDIO_SLICED) and os.path.getsize(self.VIP_AUDIO_SLICED) > 512:
                    return self.VIP_AUDIO_SLICED, True
            except Exception:
                pass
            return self.VIP_AUDIO_RAW, False

        def _do_download():
            try:
                from .external_search_patch import _download_with_ytdlp
                tempdir = tempfile.mkdtemp(prefix="juicevault-vip-")
                try:
                    downloaded = _download_with_ytdlp(self.VIP_VIDEO_URL, tempdir)
                    if downloaded and os.path.isfile(downloaded) and os.path.getsize(downloaded) > 1024:
                        shutil.copyfile(downloaded, self.VIP_AUDIO_RAW)
                        ffmpeg_bin = self._ffmpeg_executable()
                        sliced_target = os.path.join(tempdir, "vip_sliced.wav")
                        slice_cmd = [
                            ffmpeg_bin,
                            "-y",
                            "-ss", str(self.VIP_START_OFFSET),
                            "-t", str(self.VIP_PLAY_DURATION),
                            "-i", downloaded,
                            "-vn",
                            "-ar", "48000",
                            "-ac", "2",
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
                            print(f"[JuiceVault Entrance] VIP slice notice: {slice_err}")

                        return self.VIP_AUDIO_RAW, False
                finally:
                    shutil.rmtree(tempdir, ignore_errors=True)
            except Exception as exc:
                print(f"[JuiceVault Entrance] VIP audio cache error: {exc}")
                return None, False

        return await asyncio.to_thread(_do_download)

    async def _trigger_vip_join(self, guild, member, target_channel_id):
        await asyncio.sleep(self.VIP_DELAY_SECONDS)

        gid = guild.id
        voice = guild.voice_client
        if not voice or not voice.is_connected() or voice.channel is None:
            return

        current_ch = getattr(getattr(member, "voice", None), "channel", None)
        if not current_ch or current_ch.id != voice.channel.id or current_ch.id != target_channel_id:
            return

        vip_audio_res = await self._ensure_vip_audio()
        vip_audio = vip_audio_res[0] if isinstance(vip_audio_res, tuple) else vip_audio_res
        is_pre_sliced = vip_audio_res[1] if isinstance(vip_audio_res, tuple) else False

        if not vip_audio or not os.path.isfile(vip_audio):
            print(f"[JuiceVault] VIP audio not available for member {member.id}.")
            return

        exe = self._ffmpeg_executable()
        before_opts = "-nostdin"
        extra_opts = "-vn"
        if not is_pre_sliced:
            before_opts = f"-nostdin -ss {self.VIP_START_OFFSET:.3f}"
            extra_opts = f"-vn -t {self.VIP_PLAY_DURATION:.3f}"

        from .voice_recognition import DuckingAudioSource
        mixer = getattr(voice, "_jv_mixer", None)
        if mixer is None and hasattr(voice, "source") and isinstance(voice.source, DuckingAudioSource):
            mixer = voice.source
            voice._jv_mixer = mixer
        elif mixer is None and voice.is_playing() and hasattr(voice, "source") and voice.source:
            try:
                mixer = DuckingAudioSource(voice.source)
                voice.source = mixer
                if hasattr(voice, "_player") and voice._player:
                    voice._player.source = mixer
                voice._jv_mixer = mixer
            except Exception:
                mixer = None

        if voice.is_playing() and mixer is not None:
            vip_source = discord.FFmpegPCMAudio(vip_audio, executable=exe, before_options=before_opts, options=extra_opts)
            mixer.set_overlay(vip_source)
            print(f"[JuiceVault Entrance] ⭐ Playing VIP greeting (4s-10s) over ducked music (18%) in '{guild.name}'")
        elif not voice.is_playing():
            vip_source = discord.FFmpegPCMAudio(vip_audio, executable=exe, before_options=before_opts, options=extra_opts)
            voice.play(vip_source)
            print(f"[JuiceVault Entrance] ⭐ Playing VIP greeting (4s-10s) directly in '{guild.name}'")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if self.bot.user and member.id == self.bot.user.id:
            if before.channel is not None and after.channel is None:
                gid = member.guild.id
                cur = self.current.get(gid)
                pos = self.get_position(gid)
                if cur and not cur.get("_is_vip") and not cur.get("_is_soundboard"):
                    self._save_last_track_state(gid, cur, pos)
            return

        if getattr(member, "bot", False):
            return

        if before.channel == after.channel or after.channel is None:
            return

        guild = member.guild
        voice = guild.voice_client

        if not voice or not voice.is_connected() or voice.channel != after.channel:
            return

        # Check if user is Skizzoo
        if self._is_skizzoo(member):
            now = time.monotonic()
            if now - self._skizzoo_cooldowns.get(member.id, 0.0) < self.SKIZZOO_COOLDOWN_SECONDS:
                return
            self._skizzoo_cooldowns[member.id] = now
            asyncio.create_task(self._trigger_skizzoo_join(guild, member, after.channel.id))
            return

        # Generic VIP entrance fallback (for any other VIP user / VIP role)
        if self._is_vip(member):
            now = time.monotonic()
            if now - self._vip_cooldowns.get(member.id, 0.0) < self.VIP_COOLDOWN_SECONDS:
                return
            self._vip_cooldowns[member.id] = now
            asyncio.create_task(self._trigger_vip_join(guild, member, after.channel.id))

    @commands.group(name="jv", invoke_without_command=True)
    @commands.guild_only()
    async def jv(self, ctx):
        await ctx.send("`4jv start` `4jv stop` `4jv skip` `4jv skip10` `4jv shuffle` `4jv fav` `4jv favs` `4jv playfav <#>` `4jv vc [on/off]` `4jv categories` `4jv category <name>` `4jv search <name>` `4jv play <name>` `4jv refresh` `4jv status` `4jv remote` `4jv groq [key/clear]`")

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
        try:
            await self.config.guild(ctx.guild).saved_session.set(None)
            getattr(self.bot, "_jv_data", {}).get("saved_sessions", {}).pop(ctx.guild.id, None)
        except Exception:
            pass
        if ctx.guild.id not in self.tasks:
            await ctx.send("JuiceVault is not running.")
            return
        await self._stop(ctx.guild.id, disconnect=True)
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
        self._cleanup_prefetch(ctx.guild.id)
        self._trigger_next_prefetch(ctx.guild.id)
        await ctx.send(f"🔀 Queue shuffled — `{len(queue)}` tracks.")

    @jv.command(name="favorite", aliases=["fav", "like"])
    async def favorite_cmd(self, ctx, *, search_query: str = None):
        """Favorite or unfavorite the currently playing song or search query."""
        gid = ctx.guild.id
        track = None
        if search_query:
            category = await self.config.guild(ctx.guild).category()
            tracks = await self.fetch_tracks(category)
            q = search_query.strip().lower()
            matches = [t for t in tracks if q in str(t.get("title", "")).lower() or q in str(t.get("artist", "")).lower()]
            if not matches:
                await ctx.send(f"❌ No track matching `{search_query}` found.")
                return
            track = matches[0]
        else:
            track = self.current.get(gid)
            if not track:
                await ctx.send("❌ No track is currently playing in this server.")
                return

        username = str(ctx.author.id)
        author_name = ctx.author.display_name

        if not hasattr(self.bot, "_jv_data"):
            self.bot._jv_data = {}
        bot_favs = self.bot._jv_data.setdefault("favorites", {})
        user_list = bot_favs.setdefault(username, [])

        track_id = str(track.get("id") or track.get("songId") or "").strip()
        track_title = str(track.get("title") or track.get("name") or "").strip().lower()

        existing = next((i for i, t in enumerate(user_list) if (track_id and str(t.get("id")) == track_id) or (track_title and str(t.get("title", "")).lower() == track_title)), None)

        t_title = track.get("title") or track.get("name") or "Untitled"
        t_artist = track.get("artist") or "Juice WRLD"

        if existing is not None:
            user_list.pop(existing)
            action_msg = f"💔 Removed **{t_title}** from your favorites."
        else:
            clean_track = {
                "id": track.get("id") or track_id or track_title,
                "title": t_title,
                "artist": t_artist,
                "length": track.get("length") or "—",
                "cover_url": track.get("cover_url") or (f"https://api.juicevault.xyz/cdn/music/covers/{track.get('id')}" if track.get("id") else ""),
                "added_at": int(time.time()),
            }
            user_list.insert(0, clean_track)
            action_msg = f"❤️ Added **{t_title}** by *{t_artist}* to your favorites! ({len(user_list)} saved)"

        # Mirror under display name for easy Web Remote reference
        bot_favs[author_name.lower()] = user_list

        if hasattr(self, "web_remote") and self.web_remote:
            self.web_remote._user_favorites = bot_favs
            try:
                await self.web_remote.config.favorites.set(bot_favs)
            except Exception:
                pass

        await ctx.send(action_msg)

    @jv.command(name="favorites", aliases=["favs", "likes"])
    async def favorites_cmd(self, ctx):
        """List your saved JuiceVault favorites."""
        username = str(ctx.author.id)
        bot_favs = getattr(self.bot, "_jv_data", {}).get("favorites", {})
        user_list = bot_favs.get(username) or bot_favs.get(ctx.author.display_name.lower()) or bot_favs.get("default", [])
        if not user_list:
            await ctx.send("You don't have any saved favorites yet. Use `4jv favorite` while a track is playing!")
            return

        embed = discord.Embed(
            title=f"❤️ {ctx.author.display_name}'s JuiceVault Favorites ({len(user_list)})",
            color=0xF43F5E,
        )
        lines = []
        for i, t in enumerate(user_list[:15], start=1):
            title = t.get("title", "Untitled")
            artist = t.get("artist", "Juice WRLD")
            length = t.get("length", "—")
            lines.append(f"`{i}.` **{title}** — *{artist}* (`{length}`)")

        if len(user_list) > 15:
            lines.append(f"\n*...and {len(user_list) - 15} more on the Web Remote.*")

        embed.description = "\n".join(lines)
        embed.set_footer(text="Use 4jv playfav <number> to queue or play on Web Remote.")
        await ctx.send(embed=embed)

    @jv.command(name="playfav", aliases=["pf"])
    async def playfav_cmd(self, ctx, *, item: str = "1"):
        """Queue or play a song from your favorites."""
        gid = ctx.guild.id
        if gid not in self.tasks:
            await ctx.send("JuiceVault is not running. Use `4jv start` first.")
            return

        username = str(ctx.author.id)
        bot_favs = getattr(self.bot, "_jv_data", {}).get("favorites", {})
        user_list = bot_favs.get(username) or bot_favs.get(ctx.author.display_name.lower()) or bot_favs.get("default", [])
        if not user_list:
            await ctx.send("You don't have any saved favorites yet.")
            return

        selected = None
        if item.isdigit():
            idx = int(item) - 1
            if 0 <= idx < len(user_list):
                selected = user_list[idx]
        elif item.lower() == "all":
            self.manual_queues.setdefault(gid, []).extend(list(user_list))
            await ctx.send(f"➕ Queued all `{len(user_list)}` favorite songs!")
            return
        else:
            q = item.lower()
            for t in user_list:
                if q in str(t.get("title", "")).lower():
                    selected = t
                    break

        if not selected:
            await ctx.send(f"❌ Track `{item}` not found in your favorites.")
            return

        self.manual_queues.setdefault(gid, []).append(dict(selected))
        await ctx.send(f"➕ Added **{selected.get('title', 'Track')}** from favorites to queue (position #{len(self.manual_queues[gid])}).")

    @jv.command(name="voicecommands", aliases=["voicecontrol", "vc"])
    async def voice_commands_cmd(self, ctx, mode: str = None):
        """View status or toggle voice commands recognition in voice channels.
        Modes: 'on', 'off', 'status'"""
        from .voice_recognition import is_voice_recognition_supported, is_voice_commands_enabled_for_guild, set_voice_commands_enabled_for_guild, attach_voice_command_sink, get_voice_client_cls

        supported, reason = is_voice_recognition_supported()

        if mode is not None and mode.lower() in ("on", "enable", "true"):
            if not supported:
                await ctx.send(
                    f"⚠️ **In-Discord voice commands require additional packages on your bot host:**\n"
                    f"`{reason}`\n\n"
                    f"💡 *Tip: Web Remote Voice Control is 100% active and available right now on your phone/browser without extra packages!*"
                )
                return
            await set_voice_commands_enabled_for_guild(self, ctx.guild.id, True)
            if ctx.guild and ctx.guild.voice_client:
                voice = ctx.guild.voice_client
                if not hasattr(voice, "listen"):
                    try:
                        ch = voice.channel
                        await voice.disconnect(force=True)
                        await asyncio.sleep(0.5)
                        voice_cls = get_voice_client_cls()
                        await ch.connect(reconnect=True, timeout=15, cls=voice_cls)
                    except Exception as exc:
                        print(f"[JuiceVault Voice] Reconnect on enable failed: {exc}")
                attach_voice_command_sink(self, ctx.guild)
            await ctx.send("🎤 **Voice Command Recognition: ENABLED in Discord voice channel!**\n🎙️ **Wake Word: \"Garmin\"**\nSay **'Garmin, skip'**, **'Garmin, următoarea'**, **'Garmin, pause'**, **'Garmin, play'**, or **'Garmin, shuffle'**!")
        elif mode is not None and mode.lower() in ("off", "disable", "false"):
            await set_voice_commands_enabled_for_guild(self, ctx.guild.id, False)
            await ctx.send("🔇 **Voice Command Recognition: DISABLED in Discord voice channel.**")
        else:
            is_enabled = await is_voice_commands_enabled_for_guild(self, ctx.guild.id)
            embed = discord.Embed(
                title="🎤 JuiceVault Voice Commands System (Wake Word: 'Garmin')",
                color=0xA855F7 if is_enabled else 0x64748B,
            )
            embed.add_field(
                name="🔊 In-Discord Voice Channel Recognition",
                value=(
                    f"Status: **{'🟢 ACTIVE' if (supported and is_enabled) else ('🟡 READY (Disabled)' if supported else '⚪ Missing Python Packages')}**\n"
                    + (f"Installed & Ready!\nToggle with: `4jv vc on` or `4jv vc off`" if supported else f"Requires: `{reason}`\n💡 **Instalează automat tastând: `4jv installvc`**\n*(sau pe host: `pip install discord-ext-voice-recv SpeechRecognition`)*")
                ),
                inline=False
            )
            embed.add_field(
                name="📱 Web Remote Voice Control",
                value="Status: **🟢 100% READY & ACTIVE!**\nOpen your Web Remote (`4jv remote`) and tap the **🎤 Voice** button or enable Hands-Free Mode on your phone or PC!",
                inline=False
            )
            embed.add_field(
                name="🗣️ Wake Word & Voice Commands (RO / EN)",
                value=(
                    "🎙️ **Wake Word**: Say **`Garmin`** before any command!\n"
                    "• **`Garmin, skip`** / **`Garmin, dă-i skip`** / **`Garmin, următoarea`** ➔ Skip current track\n"
                    "• **`Garmin, bagă piesa robbery`** / **`Garmin, play fire`** ➔ Search & play track\n"
                    "• **`Garmin, skip 10`** / **`Garmin, înainte 10`** ➔ Forward +10s / Skip 10 tracks\n"
                    "• **`Garmin, back 10`** / **`Garmin, înapoi 10`** ➔ Rewind -10s\n"
                    "• **`Garmin, previous`** ➔ Play previous track\n"
                    "• **`Garmin, pause`** / **`Garmin, pauză`** ➔ Pause playback\n"
                    "• **`Garmin, play`** / **`Garmin, continuă`** ➔ Resume playback\n"
                    "• **`Garmin, shuffle`** / **`Garmin, amestecă`** ➔ Shuffle the queue\n"
                    "• **`Garmin, favorite`** / **`Garmin, like`** ➔ Add to favorites"
                ),
                inline=False
            )
            await ctx.send(embed=embed)

    @jv.command(name="installvc", aliases=["installvoice", "installvoicerequirements"])
    @commands.is_owner()
    async def install_vc_cmd(self, ctx):
        """Automatically install voice command dependencies (discord-ext-voice-recv, SpeechRecognition, and davey)
        directly into the bot's Python environment."""
        msg = await ctx.send("⏳ **Instalare în curs...** Se instalează `discord-ext-voice-recv`, `SpeechRecognition` și `davey` (decriptare voce Discord E2EE) în mediul Python al botului...")
        import sys
        import subprocess

        cmd = [sys.executable, "-m", "pip", "install", "discord-ext-voice-recv", "SpeechRecognition", "davey"]
        try:
            proc = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                timeout=180
            )
            if proc.returncode == 0:
                import importlib
                from . import voice_recognition
                importlib.reload(voice_recognition)
                from .voice_recognition import is_voice_recognition_supported, attach_voice_command_sink
                supported, _ = is_voice_recognition_supported()
                if supported and ctx.guild and ctx.guild.voice_client:
                    attach_voice_command_sink(self, ctx.guild)
                await msg.edit(
                    content=(
                        "✅ **Instalare reușită!**\n"
                        "Pachetele `discord-ext-voice-recv`, `SpeechRecognition` și `davey` au fost instalate cu succes în mediul botului!\n"
                        "🎤 **Comenzile vocale Garmin pe voice sunt acum ACTIVE!**\n"
                        "Încearcă acum pe voice: **„Bă Garmin, dă-i skip”** sau **„Bă Garmin, bagă piesa robbery”**!"
                    )
                )
            else:
                err = proc.stderr or proc.stdout
                await msg.edit(content=f"❌ **Eroare la instalare:**\n```{err[:1500]}```")
        except Exception as exc:
            await msg.edit(content=f"❌ **Eroare:** `{exc}`")

    @jv.command(name="vclearn", aliases=["voicelearn", "garminlearn"])
    @commands.guild_only()
    async def vc_learn_cmd(self, ctx, *, word_or_phrase: str):
        """Teach Garmin a new custom wake word or phonetic phrase (e.g. 'carmena', 'băi băiatule')."""
        try:
            from .voice_recognition import add_learned_wake_word, get_learned_wake_words
            await add_learned_wake_word(self, ctx.guild.id, word_or_phrase)
            words = await get_learned_wake_words(self, ctx.guild.id)
            await ctx.send(f"🧠 **[Garmin]** Am învățat noul apelativ: **\"{word_or_phrase}\"**! 🎙️\nCuvinte active învățate: `{', '.join(sorted(words))}`")
        except Exception as exc:
            await ctx.send(f"❌ Eroare: {exc}")

    @jv.command(name="vclearned", aliases=["voicelearned", "garminlearned"])
    @commands.guild_only()
    async def vc_learned_cmd(self, ctx):
        """List all custom wake words and learned song mappings for this server."""
        try:
            from .voice_recognition import get_learned_wake_words, get_learned_song_queries
            words = await get_learned_wake_words(self, ctx.guild.id)
            queries = await get_learned_song_queries(self, ctx.guild.id)
            embed = discord.Embed(title="🧠 Garmin Adaptive Memory", color=0xA855F7)
            embed.add_field(
                name="🎙️ Learned Wake Words",
                value=", ".join(f"`{w}`" for w in sorted(words)) if words else "*Niciun cuvânt personalizat încă. Garmin învață automat variațiile când vorbești!*",
                inline=False
            )
            embed.add_field(
                name="🎵 Learned Song Aliases",
                value="\n".join(f"• **\"{q}\"** ➔ {t.get('title')}" for q, t in list(queries.items())[:15]) if queries else "*Nicio piesă învățată încă. Căutările pe YouTube sunt reținute automat!*",
                inline=False
            )
            await ctx.send(embed=embed)
        except Exception as exc:
            await ctx.send(f"❌ Eroare: {exc}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Handle 'da' / 'yes' / 'nu' / 'no' responses to YouTube voice prompts in text chat."""
        if not message.guild or message.author.bot:
            return
        pending = getattr(self, "_pending_yt_voice", {}).get(message.guild.id)
        if not pending or time.time() >= pending.get("expires", 0.0):
            return

        pending_uid = pending.get("user_id")
        content = message.content.strip().lower()

        # REQUIREMENT: Must come from the SAME person who initiated the command!
        # Do not respond to anyone else ("sa nu raspunda la altcineva")
        if pending_uid and message.author.id != pending_uid:
            return


        is_ro = pending.get("lang") == "ro"
        target_q = None

        from .voice_recognition import _active_sinks
        sink = _active_sinks.get(message.guild.id)

        if pending.get("awaiting_title"):
            if content in ("nu", "no", "n", "cancel", "anuleaza", "stop", "lasa", "nah", "nope"):
                self._pending_yt_voice.pop(message.guild.id, None)
                if sink:
                    sink._unlock_session()
                await message.channel.send("🚫 **[Garmin]** Comandă anulată." if is_ro else "🚫 **[Garmin]** Cancelled.")
                return
            target_q = message.content.strip()
            self._pending_yt_voice.pop(message.guild.id, None)
        elif content in ("da", "yes", "y", "sure", "sigur", "baga", "pune-o", "cauta", "pune", "hai", "da te rog", "te rog", "youtube", "pe youtube", "de pe youtube", "dupa youtube", "play it", "ok", "okay", "yeah", "yep", "yup", "dap", "mda"):
            self._pending_yt_voice.pop(message.guild.id, None)
            target_q = pending.get("query")
        elif content in ("nu", "no", "n", "cancel", "anuleaza", "stop", "lasa", "nah", "nope"):
            self._pending_yt_voice.pop(message.guild.id, None)
            if sink:
                sink._unlock_session()
            await message.channel.send("🚫 **[Garmin]** Comandă anulată." if is_ro else "🚫 **[Garmin]** Cancelled.")
            return
        else:
            return

        if not target_q:
            if sink:
                sink._unlock_session()
            return

        await message.channel.send(f"🔍 **[Garmin]** Caut *\"{target_q}\"* pe YouTube... ⏳" if is_ro else f"🔍 **[Garmin]** Searching YouTube for *\"{target_q}\"*... ⏳")
        try:
            from .voice_recognition import play_chime_and_proceed
            from .external_search_patch import _extract_search
            info = await asyncio.to_thread(_extract_search, target_q)
            yt_track = None
            if info:
                if info.get("_is_playlist") or "entries" in info:
                    entries = info.get("entries") or []
                    yt_track = entries[0] if entries else None
                elif not yt_track and (info.get("url") or info.get("title")):
                    yt_track = info

                if yt_track:
                    gid = message.guild.id
                    try:
                        from .voice_recognition import add_learned_song_query
                        asyncio.create_task(add_learned_song_query(self, gid, target_q, yt_track))
                    except Exception:
                        pass
                    self.manual_queues.setdefault(gid, []).insert(0, yt_track)
                    voice = message.guild.voice_client
                    if gid in self.tasks:
                        if gid in self.skip_events:
                            self.skip_events[gid].set()
                        if voice and (voice.is_playing() or voice.is_paused()):
                            voice.stop()
                    else:
                        if voice and voice.channel:
                            self.stop_events[gid] = asyncio.Event()
                            self.skip_events[gid] = asyncio.Event()
                            self.seek_events[gid] = asyncio.Event()
                            self.skip_counts[gid] = 0
                            self.effects[gid] = "none"
                            self.tasks[gid] = asyncio.create_task(self._player(message.guild, voice.channel))

                    await play_chime_and_proceed(message.guild)
                    title = yt_track.get('title') or target_q
                    await message.channel.send(f"🎥 **[Garmin]** Redare de pe YouTube: **{title}** 🎶" if is_ro else f"🎥 **[Garmin]** Playing from YouTube: **{title}** 🎶")
                    ui = self.bot.get_cog("JuiceVaultUI")
                    if ui:
                        asyncio.create_task(ui.update_panel(gid))
                    if hasattr(self, "web_remote") and self.web_remote:
                        asyncio.create_task(self.web_remote.broadcast_state(gid))
                    if sink:
                        sink._unlock_session()
                    return

            await message.channel.send(f"❌ Nu am găsit pe YouTube: *\"{target_q}\"*" if is_ro else f"❌ Not found on YouTube: *\"{target_q}\"*")
        except Exception as e:
            await message.channel.send(f"❌ YouTube error: `{e}`")
        finally:
            if sink:
                sink._unlock_session()


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

    @jv.command(name="streamtime")
    async def set_stream_time(self, ctx, hours: float = None):
        """View or adjust stream time telemetry hours (e.g. 4jv streamtime or 4jv streamtime 350)."""
        web = getattr(self, "web_remote", None)
        if not web:
            await ctx.send("Web remote is not loaded.")
            return
        if hours is None:
            stats = web.get_telemetry_stats(guild_id=ctx.guild.id)
            today_fmt = stats.get("daily_usage", {}).get("listening_formatted", "0m")
            all_fmt = stats.get("all_time", {}).get("listening_formatted", "0m")
            session_fmt = stats.get("session", {}).get("formatted", "0m") if stats.get("session", {}).get("active") else "Inactive"
            await ctx.send(f"📊 **JuiceVault Stream Time**:\n• Active VC Session: `{session_fmt}`\n• Today: `{today_fmt}`\n• All-Time: `{all_fmt}`\n\n*Tip: To update all-time baseline hours, use `4jv streamtime <hours>`.*")
            return
        if hours < 0:
            await ctx.send("Stream time hours cannot be negative.")
            return
        total_sec = int(hours * 3600)
        web.set_custom_stream_time(total_sec)
        await ctx.send(f"✅ Stream time updated to **{hours:.1f} hours** ({total_sec:,} seconds).")

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
    async def remote_tunnel(self, ctx, action: str = "start", *, token: str = None):
        """Spawn or connect Cloudflare Tunnel for free HTTPS with trusted SSL.
        
        Usage:
        4jv remote tunnel                   -> Start free Cloudflare Quick Tunnel (*.trycloudflare.com)
        4jv remote tunnel token <token>     -> Run persistent Named Tunnel for your domain (e.g. juicevault.space)
        4jv remote tunnel stop              -> Stop Cloudflare Tunnel
        4jv remote tunnel clear             -> Stop tunnel and remove saved tunnel token
        """
        if not getattr(self, "web_remote", None):
            await ctx.send("JuiceVault Web Remote is not loaded.")
            return

        act = action.lower()
        if act in ("stop", "close", "off"):
            await self.web_remote.stop_cloudflare_tunnel()
            await ctx.send("⏹️ Cloudflare Tunnel stopped. Reverted to standard IP access.")
            return
        elif act in ("clear", "reset"):
            await self.web_remote.stop_cloudflare_tunnel(clear_token=True)
            await ctx.send("✅ Cloudflare tunnel token removed and tunnel stopped.")
            return

        # Check if action itself is the token keyword
        named_token = token.strip() if token else None
        if act == "token" and named_token:
            run_token = named_token
        elif act not in ("start", "on", "launch", "token") and not named_token:
            # Maybe the user pasted the token directly: 4jv remote tunnel <token>
            run_token = action.strip()
        else:
            run_token = None

        async with ctx.typing():
            try:
                if run_token:
                    msg = await ctx.send("⏳ Connecting Cloudflare Named Tunnel with token…")
                    tunnel_url = await self.web_remote.start_cloudflare_tunnel(token=run_token)
                else:
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

    @jv.command(name="groq")
    @commands.is_owner()
    async def set_groq_api_key(self, ctx, api_key: str = None):
        """Set or clear the Groq Cloud API key for ultra-fast Whisper Large v3 voice recognition."""
        if not api_key:
            current = await self.config.groq_api_key()
            if not current:
                current = os.environ.get("GROQ_API_KEY")
            if current:
                masked = current[:4] + "..." + current[-4:]
                await ctx.send(f"🔑 Groq Cloud API Key is currently set: `{masked}`.\nTo clear, use `{ctx.clean_prefix}4jv groq clear`.")
            else:
                await ctx.send(f"ℹ️ No Groq Cloud API Key set.\nGet a free key at https://console.groq.com and activate it with:\n`{ctx.clean_prefix}4jv groq <your_api_key>`")
            return

        if api_key.lower() == "clear":
            await self.config.groq_api_key.set(None)
            self._groq_api_key = None
            await ctx.send("✅ Groq Cloud API Key cleared. Voice engine will use Google STT fallback.")
            return

        cleaned_key = api_key.strip()
        await self.config.groq_api_key.set(cleaned_key)
        self._groq_api_key = cleaned_key
        masked = cleaned_key[:4] + "..." + cleaned_key[-4:]
        await ctx.send(
            f"⚡ **Groq Cloud Whisper Large v3 Turbo** activated! (`{masked}`)\n"
            f"Garmin voice recognition is now running with **~60ms ultra-low latency** and superior bilingual Romanian/English understanding."
        )
