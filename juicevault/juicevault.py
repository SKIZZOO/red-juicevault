import asyncio
import json
import os
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
    """24/7 JuiceVault archive player using the public JuiceVault API."""

    API_BASE = "https://api.juicevault.xyz"
    MUSIC_LIST_URL = f"{API_BASE}/music/list"
    AUDIO_EXTENSIONS = (
        ".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac", ".webm"
    )
    SHORT_PLAYBACK_SECONDS = 4.0
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
        self.stop_events = {}
        self.skip_events = {}
        self.queues = {}
        self.manual_queues = {}
        self.current = {}
        self.last_error = {}
        self.search_results = {}
        self.failure_counts = {}
        self._restore_task = None

    async def cog_load(self):
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": "Red-JuiceVault/1.1"},
            timeout=aiohttp.ClientTimeout(total=30),
        )
        self._restore_task = asyncio.create_task(self._restore_players())

    async def cog_unload(self):
        # The restore task must be cancelled too. Otherwise an old cog instance
        # can wake up after unload, create a player with a closed HTTP session,
        # and fight the newly loaded cog for the same VoiceClient.
        if self._restore_task:
            self._restore_task.cancel()
            try:
                await self._restore_task
            except asyncio.CancelledError:
                pass
            self._restore_task = None

        for guild_id in list(self.tasks):
            await self._stop(guild_id)

        if self.session and not self.session.closed:
            await self.session.close()
        self.session = None

    async def _restore_players(self):
        try:
            await self.bot.wait_until_ready()
            await asyncio.sleep(2)
            if not self.session or self.session.closed:
                return
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
                self.manual_queues[guild_id] = []
                self.queues[guild_id] = []
                self.tasks[guild_id] = asyncio.create_task(self._player(guild, channel))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            print(f"[JuiceVault] restore error: {type(exc).__name__}: {exc}")

    def _ffmpeg_executable(self):
        if imageio_ffmpeg is not None:
            try:
                return imageio_ffmpeg.get_ffmpeg_exe()
            except Exception as exc:
                print(f"[JuiceVault] imageio-ffmpeg unavailable: {exc}")
        return "ffmpeg"

    def _stream_url(self, song_id):
        return f"{self.API_BASE}/music/stream/{quote(str(song_id), safe='')}"

    @staticmethod
    def _track_text(track):
        if not track:
            return "Piesă fără nume"
        artist = str(track.get("artist") or "").strip()
        title = str(track.get("title") or "").strip()
        name = str(track.get("name") or "").strip()
        file_name = str(track.get("file_name") or "").strip()
        if artist and title:
            label = f"{artist} - {title}"
        elif title:
            label = title
        elif name:
            label = name
        elif file_name:
            label = file_name
        else:
            label = "Piesă fără nume"
        if file_name and file_name.casefold() not in label.casefold():
            label += f" [{file_name}]"
        return label

    @staticmethod
    def _search_text(track):
        values = (
            track.get("title"),
            track.get("name"),
            track.get("artist"),
            track.get("file_name"),
        )
        return " ".join(str(value or "") for value in values).casefold()

    @staticmethod
    def _category(track):
        return str(track.get("category") or "uncategorized").strip() or "uncategorized"

    @staticmethod
    def _normalize_category(value):
        return str(value or "all").strip().casefold().replace(" ", "_")

    def _filter_tracks(self, tracks, category):
        wanted = self._normalize_category(category)
        if wanted in ("", "all", "*", "toate"):
            return list(tracks)
        return [track for track in tracks if self._normalize_category(self._category(track)) == wanted]

    def _category_counts(self, tracks):
        counts = {}
        for track in tracks:
            category = self._category(track)
            counts[category] = counts.get(category, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: item[0].casefold()))

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "Red-JuiceVault/1.1"},
                timeout=aiohttp.ClientTimeout(total=30),
            )
        return self.session

    async def fetch_tracks(self):
        """Load the complete public JuiceVault song index with metadata."""
        session = await self._ensure_session()
        async with session.get(self.MUSIC_LIST_URL) as response:
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
        seen_ids = set()
        for song in songs:
            if not isinstance(song, dict):
                continue
            song_id = song.get("id")
            file_name = str(song.get("file_name", ""))
            if not song_id or not file_name.lower().split("?", 1)[0].endswith(self.AUDIO_EXTENSIONS):
                continue
            song_id = str(song_id)
            if song_id in seen_ids:
                continue
            seen_ids.add(song_id)
            track = dict(song)
            track["id"] = song_id
            track["url"] = self._stream_url(song_id)
            tracks.append(track)
        return tracks

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
            await asyncio.sleep(0.10)
        return True

    async def _download_track(self, track):
        """Download the current track before playback to avoid network jitter."""
        session = await self._ensure_session()
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=30, sock_read=30)
        suffix = os.path.splitext(str(track.get("file_name") or ".mp3"))[1] or ".mp3"
        if suffix.lower() not in self.AUDIO_EXTENSIONS:
            suffix = ".mp3"
        handle = tempfile.NamedTemporaryFile(mode="w+b", suffix=f".juicevault{suffix}", delete=False)
        path = handle.name
        try:
            async with session.get(track["url"], timeout=timeout) as response:
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
            except Exception:
                pass
            self._remove_file(path)
            raise

    @staticmethod
    def _remove_file(path):
        if not path:
            return
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
        guild = self.bot.get_guild(guild_id)
        if guild:
            await self._disconnect(guild)

    async def _read_ffmpeg_log(self, log_path):
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as handle:
                return handle.read().strip()
        except OSError:
            return ""
        finally:
            self._remove_file(log_path)

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
                        all_tracks = await self.fetch_tracks()
                        settings = await self.config.guild(guild).all()
                        category = settings.get("category", "all")
                        tracks = self._filter_tracks(all_tracks, category)
                    except Exception as exc:
                        self.last_error[gid] = f"API: {exc}"
                        print(f"[JuiceVault] API error: {exc}")
                        await asyncio.sleep(30)
                        continue
                    if not tracks:
                        self.last_error[gid] = "API nu a returnat piese pentru categoria selectată"
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

                if self.tasks.get(gid) is not task:
                    return

                # Never stop an already-playing source here. Doing that creates
                # artificial skips if two player tasks ever overlap during reload.
                if voice.is_playing() or voice.is_paused():
                    await asyncio.sleep(0.25)
                    continue

                if self.manual_queues.get(gid):
                    track = self.manual_queues[gid].pop(0)
                    source_type = "manual"
                else:
                    track = self.queues[gid].pop(0)
                    source_type = "normal"

                self.current[gid] = track
                finished = asyncio.Event()
                playback_error = {"value": None}
                started_at = time.monotonic()
                local_path = None
                log_file = None
                log_path = None

                try:
                    local_path = await self._download_track(track)
                    log_file = tempfile.NamedTemporaryFile(mode="w+b", suffix=".juicevault-ffmpeg.log", delete=False)
                    log_path = log_file.name

                    def after(error):
                        if error:
                            playback_error["value"] = error
                            print(f"[JuiceVault] playback worker error: {type(error).__name__}: {error}")
                        self.bot.loop.call_soon_threadsafe(finished.set)

                    self.last_error.pop(gid, None)
                    source = discord.FFmpegPCMAudio(
                        local_path,
                        executable=self._ffmpeg_executable(),
                        before_options="-nostdin",
                        options="-vn -af aresample=async=1:first_pts=0",
                        stderr=log_file,
                    )
                    if voice.is_playing() or voice.is_paused():
                        raise RuntimeError("VoiceClient became busy before playback")
                    voice.play(source, after=after)
                except Exception as exc:
                    self.last_error[gid] = f"Playback: {type(exc).__name__}: {exc}"
                    print(f"[JuiceVault] could not play {track['url']}: {type(exc).__name__}: {exc}")
                    if log_file:
                        try:
                            log_file.close()
                        except OSError:
                            pass
                    if log_path:
                        await self._read_ffmpeg_log(log_path)
                    self._remove_file(local_path)
                    if source_type == "manual":
                        self.manual_queues.setdefault(gid, []).insert(0, track)
                    else:
                        self.queues.setdefault(gid, []).insert(0, track)
                    await asyncio.sleep(self.FAILURE_BACKOFF_SECONDS)
                    continue

                stop_task = asyncio.create_task(stop.wait())
                finish_task = asyncio.create_task(finished.wait())
                skip_task = asyncio.create_task(skip.wait())
                done, pending = await asyncio.wait(
                    {stop_task, finish_task, skip_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for pending_task in pending:
                    pending_task.cancel()

                # A skip is valid only when the skip waiter itself completed.
                was_skipped = skip_task in done and skip.is_set()
                if was_skipped and (voice.is_playing() or voice.is_paused()):
                    voice.stop()

                await self._wait_for_voice_idle(voice)
                if log_file:
                    try:
                        log_file.flush()
                        log_file.close()
                    except OSError:
                        pass
                ffmpeg_log = await self._read_ffmpeg_log(log_path) if log_path else ""
                self._remove_file(local_path)
                elapsed = time.monotonic() - started_at

                if stop.is_set() or self.tasks.get(gid) is not task:
                    return

                if was_skipped:
                    skip.clear()
                    self.failure_counts[gid] = 0
                    print(f"[JuiceVault] manual skip: {self._track_text(track)}")
                    continue

                if playback_error["value"] or elapsed < self.SHORT_PLAYBACK_SECONDS:
                    self.failure_counts[gid] = self.failure_counts.get(gid, 0) + 1
                    error = playback_error["value"]
                    detail = ffmpeg_log[-1800:] if ffmpeg_log else str(error or "stream ended too quickly")
                    self.last_error[gid] = f"FFmpeg: piesa s-a oprit după {elapsed:.1f}s. {detail}"
                    print(f"[JuiceVault] track failed after {elapsed:.1f}s: {self._track_text(track)} ({source_type})")
                    if source_type == "manual":
                        self.manual_queues.setdefault(gid, []).insert(0, track)
                    else:
                        self.queues.setdefault(gid, []).insert(0, track)
                    if self.failure_counts[gid] >= self.MAX_CONSECUTIVE_FAILURES:
                        print("[JuiceVault] too many consecutive playback failures; waiting 30s.")
                        await asyncio.sleep(30)
                        self.failure_counts[gid] = 0
                    else:
                        await asyncio.sleep(self.FAILURE_BACKOFF_SECONDS)
                    continue

                self.failure_counts[gid] = 0
                self.last_error.pop(gid, None)

        except asyncio.CancelledError:
            pass
        finally:
            if self.tasks.get(gid) is task:
                await self._disconnect(guild)
                self.current.pop(gid, None)

    @commands.group(name="jv", invoke_without_command=True)
    @commands.guild_only()
    async def jv(self, ctx):
        """JuiceVault commands."""
        await ctx.send(
            "`jv start` `jv stop` `jv skip`/`jv next` `jv search <nume>` "
            "`jv play <nume>` `jv categories` `jv category <nume>` `jv refresh` `jv status`"
        )

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
                return
            await self._stop(gid)
        try:
            all_tracks = await self.fetch_tracks()
            category = (await self.config.guild(ctx.guild).all()).get("category", "all")
            tracks = self._filter_tracks(all_tracks, category)
        except Exception as exc:
            await ctx.send(f"Nu pot accesa JuiceVault API: `{exc}`")
            return
        if not tracks:
            await ctx.send("Nu există piese pentru categoria selectată. Folosește `4jv categories`.")
            return
        try:
            voice = await self._connect(ctx.guild, ctx.author.voice.channel)
        except Exception as exc:
            self.last_error[gid] = f"Voice: {type(exc).__name__}: {exc}"
            await ctx.send(f"❌ Nu pot intra în voice: `{type(exc).__name__}: {exc}`")
            return
        self.queues[gid] = tracks
        self.manual_queues[gid] = []
        self.stop_events[gid] = asyncio.Event()
        self.skip_events[gid] = asyncio.Event()
        self.failure_counts[gid] = 0
        await self.config.guild(ctx.guild).enabled.set(True)
        await self.config.guild(ctx.guild).channel_id.set(ctx.author.voice.channel.id)
        self.tasks[gid] = asyncio.create_task(self._player(ctx.guild, ctx.author.voice.channel))
        await ctx.send(
            f"▶️ Pornit — `{len(tracks)}` piese • categorie `{category}` • `{voice.channel.name}`."
        )

    @jv.command(name="stop")
    async def stop(self, ctx):
        """Stop playback."""
        await self.config.guild(ctx.guild).enabled.set(False)
        if ctx.guild.id not in self.tasks:
            await ctx.send("JuiceVault nu rulează.")
            return
        await self._stop(ctx.guild.id)
        await ctx.send("⏹️ Oprit.")

    @jv.command(name="skip", aliases=["next"])
    async def skip(self, ctx):
        """Skip exactly the current track."""
        gid = ctx.guild.id
        voice = ctx.guild.voice_client
        event = self.skip_events.get(gid)
        if gid not in self.tasks or not event or not voice or not voice.is_playing():
            await ctx.send("Nu rulează nicio piesă.")
            return
        if event.is_set():
            await ctx.send("Un skip este deja în curs.")
            return
        event.set()
        voice.stop()
        await ctx.send("⏭️ Skip.")

    @jv.command(name="categories", aliases=["categorylist", "modes"])
    @commands.guild_only()
    async def categories(self, ctx):
        """List all categories exposed by the JuiceVault API."""
        try:
            tracks = await self.fetch_tracks()
        except Exception as exc:
            await ctx.send(f"Nu pot citi categoriile: `{exc}`")
            return
        counts = self._category_counts(tracks)
        selected = (await self.config.guild(ctx.guild).all()).get("category", "all")
        lines = [f"**all** — {len(tracks)}"]
        lines.extend(f"**{name}** — {count}" for name, count in counts.items())
        await ctx.send("🎚️ Categorii JuiceVault (selectată: `" + str(selected) + "`)\n" + "\n".join(lines))

    @jv.command(name="category", aliases=["mode"])
    @commands.guild_only()
    async def category(self, ctx, *, name: str):
        """Select the API category used by the continuous player."""
        requested = self._normalize_category(name)
        try:
            tracks = await self.fetch_tracks()
        except Exception as exc:
            await ctx.send(f"Nu pot verifica categoria: `{exc}`")
            return
        if requested in ("all", "*", "toate"):
            selected = "all"
            filtered = tracks
        else:
            matching_names = {self._normalize_category(self._category(track)): self._category(track) for track in tracks}
            if requested not in matching_names:
                available = ", ".join(sorted(matching_names.values(), key=str.casefold)) or "niciuna"
                await ctx.send(f"❌ Categoria `{name}` nu există. Disponibile: `{available}`")
                return
            selected = matching_names[requested]
            filtered = self._filter_tracks(tracks, selected)
        await self.config.guild(ctx.guild).category.set(selected)
        if ctx.guild.id in self.tasks:
            self.queues[ctx.guild.id] = filtered
            self.failure_counts[ctx.guild.id] = 0
        await ctx.send(f"🎚️ Categoria setată pe **{selected}** — `{len(filtered)}` piese.")

    @jv.command(name="search")
    @commands.guild_only()
    async def search(self, ctx, *, query: str):
        """Search JuiceVault tracks across all categories."""
        try:
            tracks = await self.fetch_tracks()
        except Exception as exc:
            await ctx.send(f"Căutarea a eșuat: `{exc}`")
            return
        q = query.casefold().strip()
        matches = [track for track in tracks if q in self._search_text(track)][:10]
        if not matches:
            await ctx.send("Nu am găsit nimic.")
            return
        self.search_results[ctx.guild.id] = matches
        lines = [f"**{index}.** {self._track_text(track)} • `{self._category(track)}`" for index, track in enumerate(matches, 1)]
        await ctx.send("🔎 Rezultate JuiceVault:\n" + "\n".join(lines))

    @jv.command(name="play")
    @commands.guild_only()
    async def play(self, ctx, *, query: str):
        """Queue a searched result or search directly and play it next."""
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
            q = query.casefold().strip()
            candidates = [item for item in tracks if q in self._search_text(item)]
            if candidates:
                track = candidates[0]
        if not track:
            await ctx.send("Nu am găsit piesa. Folosește `4jv search <nume>`." )
            return
        if gid not in self.tasks:
            await ctx.send("Playerul nu rulează. Folosește `4jv start` întâi.")
            return
        self.manual_queues.setdefault(gid, []).append(track)
        await ctx.send(f"🎵 Adăugat la Requested: **{self._track_text(track)}** • `{self._category(track)}`")

    @jv.command(name="refresh")
    @commands.guild_only()
    async def refresh(self, ctx):
        """Refresh the normal queue using the selected API category."""
        try:
            tracks = await self.fetch_tracks()
            category = (await self.config.guild(ctx.guild).all()).get("category", "all")
            tracks = self._filter_tracks(tracks, category)
        except Exception as exc:
            self.last_error[ctx.guild.id] = f"API: {exc}"
            await ctx.send(f"Refresh eșuat: `{exc}`")
            return
        self.queues[ctx.guild.id] = tracks
        self.failure_counts[ctx.guild.id] = 0
        self.last_error.pop(ctx.guild.id, None)
        await ctx.send(f"🔄 Queue reîmprospătat: `{len(tracks)}` piese • categoria `{category}`.")

    @jv.command(name="status")
    @commands.guild_only()
    async def status(self, ctx):
        """Show player status."""
        gid = ctx.guild.id
        voice = ctx.guild.voice_client
        current = self.current.get(gid)
        normal = len(self.queues.get(gid, []))
        manual = len(self.manual_queues.get(gid, []))
        error = self.last_error.get(gid)
        settings = await self.config.guild(ctx.guild).all()
        category = settings.get("category", "all")
        playing = bool(voice and voice.is_playing())
        paused = bool(voice and voice.is_paused())
        state = "playing" if playing else "paused" if paused else "idle"
        lines = [
            f"**State:** `{state}`",
            f"**Current:** `{self._track_text(current) if current else 'none'}`",
            f"**Category:** `{category}`",
            f"**Requested:** `{manual}`",
            f"**Queue:** `{normal}`",
            f"**Voice:** `{voice.channel.name if voice and voice.channel else 'none'}`",
        ]
        if error:
            lines.append(f"**Last error:** `{error[:1500]}`")
        await ctx.send("🎧 JuiceVault status\n" + "\n".join(lines))
