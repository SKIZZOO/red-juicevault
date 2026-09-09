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
        self.search_results = {}
        self.failure_counts = {}

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
                self.tasks[guild_id] = asyncio.create_task(
                    self._player(guild, channel)
                )

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

    async def fetch_tracks(self):
        """Load the complete public JuiceVault song index with metadata."""
        async with self.session.get(self.MUSIC_LIST_URL) as response:
            text = await response.text(errors="ignore")
            if response.status != 200:
                try:
                    payload = json.loads(text)
                    detail = (
                        payload.get("error", text[:200])
                        if isinstance(payload, dict)
                        else text[:200]
                    )
                except json.JSONDecodeError:
                    detail = text[:200]
                raise RuntimeError(
                    f"JuiceVault API HTTP {response.status}: {detail}"
                )

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
            if not song_id or not file_name.lower().split("?", 1)[0].endswith(
                self.AUDIO_EXTENSIONS
            ):
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
            try:
                os.remove(log_path)
            except OSError:
                pass

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

                track = self.queues[gid].pop(0)
                self.current[gid] = track
                finished = asyncio.Event()
                playback_error = {"value": None}
                started_at = time.monotonic()
                log_file = tempfile.NamedTemporaryFile(
                    mode="w+b", suffix=".juicevault-ffmpeg.log", delete=False
                )
                log_path = log_file.name

                def after(error):
                    if error:
                        playback_error["value"] = error
                        print(
                            f"[JuiceVault] playback worker error: "
                            f"{type(error).__name__}: {error}"
                        )
                    self.bot.loop.call_soon_threadsafe(finished.set)

                try:
                    self.last_error.pop(gid, None)
                    source = discord.FFmpegPCMAudio(
                        track["url"],
                        executable=self._ffmpeg_executable(),
                        before_options=(
                            '-user_agent "Red-JuiceVault/1.0" '
                            "-reconnect 1 -reconnect_streamed 1 "
                            "-reconnect_at_eof 1 -reconnect_on_network_error 1 "
                            "-reconnect_delay_max 5"
                        ),
                        options="-vn",
                        stderr=log_file,
                    )
                    voice.play(source, after=after)
                except Exception as exc:
                    self.last_error[gid] = (
                        f"Playback: {type(exc).__name__}: {exc}"
                    )
                    print(
                        f"[JuiceVault] could not play {track['url']}: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    try:
                        log_file.close()
                    finally:
                        await self._read_ffmpeg_log(log_path)
                    await asyncio.sleep(self.FAILURE_BACKOFF_SECONDS)
                    self.failure_counts[gid] = self.failure_counts.get(gid, 0) + 1
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

                try:
                    log_file.flush()
                    log_file.close()
                except OSError:
                    pass

                ffmpeg_log = await self._read_ffmpeg_log(log_path)
                elapsed = time.monotonic() - started_at
                was_skipped = skip.is_set()

                if stop.is_set():
                    break

                if was_skipped:
                    skip.clear()
                    self.failure_counts[gid] = 0
                    continue

                if playback_error["value"] or elapsed < self.SHORT_PLAYBACK_SECONDS:
                    self.failure_counts[gid] = self.failure_counts.get(gid, 0) + 1
                    error = playback_error["value"]
                    detail = ffmpeg_log[-1800:] if ffmpeg_log else str(error or "stream ended too quickly")
                    self.last_error[gid] = (
                        f"FFmpeg: piesa s-a oprit după {elapsed:.1f}s. {detail}"
                    )
                    print(
                        f"[JuiceVault] track failed after {elapsed:.1f}s: "
                        f"{self._track_text(track)}"
                    )
                    if self.failure_counts[gid] >= self.MAX_CONSECUTIVE_FAILURES:
                        print(
                            "[JuiceVault] too many consecutive FFmpeg failures; "
                            "waiting before trying another track."
                        )
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
            await self._disconnect(guild)
            self.current.pop(gid, None)

    @commands.group(name="jv", invoke_without_command=True)
    @commands.guild_only()
    async def jv(self, ctx):
        """JuiceVault commands."""
        await ctx.send(
            "`jv start` `jv stop` `jv skip` `jv search <nume>` "
            "`jv play <nume>` `jv refresh` `jv status`"
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
            else:
                self.tasks.pop(gid, None)
                await self.config.guild(ctx.guild).enabled.set(False)
                await ctx.send(
                    "Playerul era blocat fără conexiune voice. "
                    "Am resetat starea; rulează din nou `jv start`."
                )
            return

        try:
            tracks = await self.fetch_tracks()
        except Exception as exc:
            await ctx.send(f"Nu pot accesa JuiceVault API: `{exc}`")
            return

        if not tracks:
            await ctx.send("JuiceVault API nu a returnat piese audio.")
            return

        try:
            voice = await self._connect(ctx.guild, ctx.author.voice.channel)
        except Exception as exc:
            self.last_error[gid] = f"Voice: {type(exc).__name__}: {exc}"
            await ctx.send(
                f"❌ Nu pot intra în voice: `{type(exc).__name__}: {exc}`"
            )
            return

        self.queues[gid] = tracks
        self.stop_events[gid] = asyncio.Event()
        self.skip_events[gid] = asyncio.Event()
        self.failure_counts[gid] = 0
        await self.config.guild(ctx.guild).enabled.set(True)
        await self.config.guild(ctx.guild).channel_id.set(
            ctx.author.voice.channel.id
        )
        self.tasks[gid] = asyncio.create_task(
            self._player(ctx.guild, ctx.author.voice.channel)
        )
        await ctx.send(
            f"▶️ Pornit — {len(tracks)} piese găsite prin JuiceVault API. "
            f"Sunt în `{voice.channel.name}`."
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

    @jv.command(name="skip")
    async def skip(self, ctx):
        """Skip exactly the current track."""
        gid = ctx.guild.id
        voice = ctx.guild.voice_client
        event = self.skip_events.get(gid)
        if gid not in self.tasks or not event or not voice or not voice.is_playing():
            await ctx.send("Nu rulează nicio piesă.")
            return

        event.set()
        voice.stop()
        await ctx.send("⏭️ Am sărit o singură piesă. Urmează următoarea.")

    @jv.command(name="search")
    async def search(self, ctx, *, query: str):
        """Search JuiceVault by title, alternate name, artist, or file name."""
        try:
            tracks = await self.fetch_tracks()
        except Exception as exc:
            await ctx.send(f"Căutarea a eșuat: `{exc}`")
            return

        query_normalized = query.casefold().strip()
        if not query_normalized:
            await ctx.send("Scrie un nume după `jv search`.")
            return

        matches = [
            track for track in tracks
            if query_normalized in self._search_text(track)
        ]

        def score(track):
            title = str(track.get("title") or "").casefold()
            name = str(track.get("name") or "").casefold()
            artist = str(track.get("artist") or "").casefold()
            file_name = str(track.get("file_name") or "").casefold()
            if query_normalized == title or query_normalized == name:
                return 0
            if query_normalized == file_name:
                return 1
            if query_normalized == artist:
                return 2
            if query_normalized in title or query_normalized in name:
                return 3
            if query_normalized in file_name:
                return 4
            return 5

        matches.sort(key=score)
        matches = matches[:10]
        self.search_results[ctx.guild.id] = matches

        if not matches:
            await ctx.send(f"Nu am găsit nicio piesă pentru `{query}`.")
            return

        lines = [f"🔎 Rezultate pentru **{query}**:"]
        for index, track in enumerate(matches, 1):
            title = str(track.get("title") or track.get("name") or "Fără titlu")
            file_name = str(track.get("file_name") or "")
            artist = str(track.get("artist") or "")
            label = f"{artist} - {title}" if artist else title
            if file_name and file_name.casefold() != title.casefold():
                label += f" | `{file_name}`"
            lines.append(f"`{index}.` {label}")

        lines.append(
            "Folosește `jv play <număr>` sau `jv play <nume>` "
            "pentru a o pune următoarea."
        )
        await ctx.send("\n".join(lines)[:1900])

    @jv.command(name="play")
    async def play(self, ctx, *, query: str):
        """Put a named/search-result track next in the queue."""
        gid = ctx.guild.id
        if gid not in self.tasks:
            await ctx.send("Pornește întâi playerul cu `jv start`.")
            return

        selected = None
        if query.strip().isdigit():
            index = int(query.strip()) - 1
            results = self.search_results.get(gid, [])
            if 0 <= index < len(results):
                selected = results[index]
            else:
                await ctx.send(
                    "Număr invalid. Fă mai întâi `jv search <nume>` și alege un rezultat."
                )
                return
        else:
            try:
                tracks = await self.fetch_tracks()
            except Exception as exc:
                await ctx.send(f"Căutarea a eșuat: `{exc}`")
                return

            query_normalized = query.casefold().strip()
            exact = [
                track for track in tracks
                if query_normalized in {
                    str(track.get("title") or "").casefold(),
                    str(track.get("name") or "").casefold(),
                    str(track.get("file_name") or "").casefold(),
                }
            ]
            if exact:
                selected = exact[0]
            else:
                matches = [
                    track for track in tracks
                    if query_normalized in self._search_text(track)
                ]
                if len(matches) == 1:
                    selected = matches[0]
                elif matches:
                    self.search_results[gid] = matches[:10]
                    await ctx.send(
                        "Am găsit mai multe rezultate. Folosește `jv search `"
                        f"{query}` și apoi `jv play <număr>`."
                    )
                    return

        if selected is None:
            await ctx.send(f"Nu am găsit piesa `{query}`.")
            return

        self.queues.setdefault(gid, []).insert(0, selected)
        await ctx.send(
            f"⏭️ Am pus **{self._track_text(selected)}** ca următoarea piesă."
        )

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
        current = self.current.get(gid)
        current_text = self._track_text(current) if current else "nimic"
        await ctx.send(
            f"🟢 Rulează | Voice: `{bool(voice and voice.is_connected())}` | "
            f"Playing: `{bool(voice and voice.is_playing())}` | "
            f"Queue: `{len(self.queues.get(gid, []))}` | "
            f"Current: `{current_text}` | "
            f"Error: `{self.last_error.get(gid, 'none')}`"
        )
