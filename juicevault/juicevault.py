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
                headers={"User-Agent": "Red-JuiceVault/1.1"},
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
                self.skip_counts[guild_id] = 0
                self.manual_queues[guild_id] = []
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
            return "Piesă fără nume"
        artist = str(track.get("artist") or "").strip()
        title = str(track.get("title") or track.get("name") or "").strip()
        filename = str(track.get("file_name") or "").strip()
        if artist and title:
            label = f"{artist} — {title}"
        else:
            label = title or filename or "Piesă fără nume"
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
        self.manual_queues.setdefault(gid, [])
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
                            self.last_error[gid] = f"Categoria `{category}` nu are piese."
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
                    for _ in range(min(count, len(self.queues.get(gid, [])))):
                        self.queues[gid].pop(0)
                    print(f"[JuiceVault] skipped {count} queued song(s)")
                    continue
                if self.manual_queues.get(gid):
                    track = self.manual_queues[gid].pop(0)
                    source_type = "manual"
                else:
                    track = self.queues[gid].pop(0)
                    source_type = "normal"
                self.current[gid] = track
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
                    source = discord.FFmpegPCMAudio(local_path, executable=self._ffmpeg_executable(), before_options="-nostdin", options="-vn -af aresample=async=1:first_pts=0", stderr=log_file)
                    voice.play(source, after=after)
                except Exception as exc:
                    self.last_error[gid] = f"Playback: {type(exc).__name__}: {exc}"
                    if log_file:
                        try:
                            log_file.close()
                        except OSError:
                            pass
                    self._remove_file(local_path)
                    target = self.manual_queues if source_type == "manual" else self.queues
                    target.setdefault(gid, []).insert(0, track)
                    print(f"[JuiceVault] could not play {self._track_text(track)}: {type(exc).__name__}: {exc}")
                    await asyncio.sleep(self.FAILURE_BACKOFF_SECONDS)
                    continue
                stop_task = asyncio.create_task(stop.wait())
                finish_task = asyncio.create_task(finished.wait())
                skip_task = asyncio.create_task(skip.wait())
                done, pending = await asyncio.wait({stop_task, finish_task, skip_task}, return_when=asyncio.FIRST_COMPLETED)
                for p in pending:
                    p.cancel()
                explicit_skip = skip_task in done and skip.is_set()
                if explicit_skip:
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
                if explicit_skip:
                    skip.clear()
                    count = max(1, min(int(self.skip_counts.pop(gid, 1)), 100))
                    for _ in range(min(count, len(self.queues.get(gid, [])))):
                        self.queues[gid].pop(0)
                    self.failure_counts[gid] = 0
                    print(f"[JuiceVault] explicit skip request: {count} song(s)")
                    continue
                elapsed = time.monotonic() - started_at
                if playback_error["value"] or elapsed < 4.0:
                    self.failure_counts[gid] = self.failure_counts.get(gid, 0) + 1
                    target = self.manual_queues if source_type == "manual" else self.queues
                    target.setdefault(gid, []).insert(0, track)
                    self.last_error[gid] = f"FFmpeg: piesa s-a oprit după {elapsed:.1f}s."
                    await asyncio.sleep(30 if self.failure_counts[gid] >= self.MAX_CONSECUTIVE_FAILURES else self.FAILURE_BACKOFF_SECONDS)
                    if self.failure_counts[gid] >= self.MAX_CONSECUTIVE_FAILURES:
                        self.failure_counts[gid] = 0
                    continue
                self.failure_counts[gid] = 0
                self.last_error.pop(gid, None)
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

    @commands.group(name="jv", invoke_without_command=True)
    @commands.guild_only()
    async def jv(self, ctx):
        await ctx.send("`4jv start` `4jv stop` `4jv skip` `4jv skip10` `4jv shuffle` `4jv categories` `4jv category <nume>` `4jv search <nume>` `4jv play <nume>` `4jv refresh` `4jv status`")

    @jv.command(name="start")
    async def start(self, ctx):
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("Intră mai întâi într-un voice channel.")
            return
        gid = ctx.guild.id
        if gid in self.tasks:
            voice = ctx.guild.voice_client
            if voice and voice.is_connected():
                await ctx.send("JuiceVault rulează deja.")
                return
            await self._stop(gid)
        category = await self.config.guild(ctx.guild).category()
        try:
            tracks = await self.fetch_tracks(category)
            if category not in self.CATEGORY_URLS:
                tracks = self._filter_tracks(tracks, category)
        except Exception as exc:
            await ctx.send(f"Nu pot accesa JuiceVault API: `{exc}`")
            return
        if not tracks:
            await ctx.send(f"Categoria `{category}` nu conține piese.")
            return
        try:
            voice = await self._connect(ctx.guild, ctx.author.voice.channel)
        except Exception as exc:
            await ctx.send(f"❌ Nu pot intra în voice: `{type(exc).__name__}: {exc}`")
            return
        self.queues[gid] = tracks
        self.manual_queues[gid] = []
        self.stop_events[gid] = asyncio.Event()
        self.skip_events[gid] = asyncio.Event()
        self.skip_counts[gid] = 0
        self.failure_counts[gid] = 0
        await self.config.guild(ctx.guild).enabled.set(True)
        await self.config.guild(ctx.guild).channel_id.set(ctx.author.voice.channel.id)
        self.tasks[gid] = asyncio.create_task(self._player(ctx.guild, ctx.author.voice.channel))
        await ctx.send(f"▶️ Pornit — `{len(tracks)}` piese, categoria `{category}`. Sunt în `{voice.channel.name}`.")

    @jv.command(name="stop")
    async def stop(self, ctx):
        await self.config.guild(ctx.guild).enabled.set(False)
        if ctx.guild.id not in self.tasks:
            await ctx.send("JuiceVault nu rulează.")
            return
        await self._stop(ctx.guild.id)
        await ctx.send("⏹️ Oprit.")

    @jv.command(name="skip", aliases=["next"])
    async def skip(self, ctx):
        if await self._request_skip(ctx.guild.id, 1):
            await ctx.send("⏭️ Skip 1.")
        else:
            await ctx.send("Nu rulează nicio piesă sau un skip este deja în curs.")

    @jv.command(name="skip10")
    async def skip10(self, ctx):
        if await self._request_skip(ctx.guild.id, 10):
            await ctx.send("⏩ Skip 10.")
        else:
            await ctx.send("Nu rulează nicio piesă sau un skip este deja în curs.")

    @jv.command(name="shuffle")
    async def shuffle(self, ctx):
        queue = self.queues.get(ctx.guild.id)
        if not queue:
            await ctx.send("Queue-ul este gol.")
            return
        random.shuffle(queue)
        await ctx.send(f"🔀 Queue amestecat — `{len(queue)}` piese.")

    @jv.command(name="categories")
    async def categories_cmd(self, ctx):
        try:
            counts = await self.get_categories()
        except Exception as exc:
            await ctx.send(f"Nu pot încărca categoriile: `{exc}`")
            return
        lines = [f"**all** — {sum(counts.values())}"]
        lines.extend(f"**{name}** — {count}" for name, count in sorted(counts.items()))
        await ctx.send("🎚️ Categorii JuiceVault:\n" + "\n".join(lines[:50]))

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
            await ctx.send(f"Nu pot accesa API-ul: `{exc}`")
            return
        if category != "all" and not tracks:
            await ctx.send(f"Categoria `{category}` nu există sau nu are piese.")
            return
        await self.config.guild(ctx.guild).category.set(resolved)
        if ctx.guild.id in self.tasks:
            self.queues[ctx.guild.id] = tracks
            self.failure_counts[ctx.guild.id] = 0
        await ctx.send(f"🎚️ Categoria setată pe **{resolved}** — `{len(tracks)}` piese.")

    @jv.command(name="search")
    async def search(self, ctx, *, query: str):
        try:
            tracks = await self.fetch_tracks()
        except Exception as exc:
            await ctx.send(f"Căutarea a eșuat: `{exc}`")
            return
        matches = [track for track in tracks if query.casefold().strip() in self._search_text(track)][:10]
        if not matches:
            await ctx.send("Nu am găsit nimic.")
            return
        self.search_results[ctx.guild.id] = matches
        await ctx.send("🔎 Rezultate JuiceVault:\n" + "\n".join(f"**{i}.** {self._track_text(track)} `[{self._category_name(track.get('category'))}]`" for i, track in enumerate(matches, 1)))

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
                await ctx.send(f"Căutarea a eșuat: `{exc}`")
                return
            candidates = [item for item in tracks if query.casefold().strip() in self._search_text(item)]
            track = candidates[0] if candidates else None
        if not track:
            await ctx.send("Nu am găsit piesa. Folosește `4jv search <nume>`." )
            return
        if gid not in self.tasks:
            await ctx.send("Playerul nu rulează. Folosește `4jv start` întâi.")
            return
        self.manual_queues.setdefault(gid, []).append(track)
        await ctx.send(f"🎵 Adăugat la Requested: **{self._track_text(track)}**")

    @jv.command(name="refresh")
    async def refresh(self, ctx):
        category = await self.config.guild(ctx.guild).category()
        try:
            filtered = await self.fetch_tracks(category)
            if category not in self.CATEGORY_URLS:
                filtered = self._filter_tracks(filtered, category)
        except Exception as exc:
            await ctx.send(f"Refresh eșuat: `{exc}`")
            return
        if not filtered:
            await ctx.send(f"Categoria `{category}` nu conține piese.")
            return
        self.queues[ctx.guild.id] = filtered
        self.failure_counts[ctx.guild.id] = 0
        await ctx.send(f"🔄 Refresh — `{len(filtered)}` piese în `{category}`.")

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
            f"**Voice:** {voice.channel.name if voice and voice.is_connected() else 'nu'}",
            f"**Categorie:** `{category}`",
            f"**Now:** {self._track_text(current) if current else 'nimic'}",
            f"**Queue:** `{queue_size}`",
            f"**Requested:** `{manual_size}`",
        ]
        if error:
            lines.append(f"**Ultima eroare:** `{error}`")
        await ctx.send("\n".join(lines))
