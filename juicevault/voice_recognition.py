"""
JuiceVault Voice Recognition Engine
===================================
Provides in-Discord voice channel microphone command detection (Skip, Next, Pause,
Play, Previous, Shuffle, Favorite) with graceful fallback when optional audio
receiving packages are not installed on the host.
"""

import array
import asyncio
import logging
import math
import os
import re
import struct
import tempfile
import threading
import time
import unicodedata
import wave

log = logging.getLogger("red.juicevault.voice_recognition")

# Silence noisy RTCP telemetry spam (SenderReportPacket type=200) from discord-ext-voice-recv
logging.getLogger("discord.ext.voice_recv.reader").setLevel(logging.WARNING)
logging.getLogger("discord.ext.voice_recv").setLevel(logging.WARNING)


def _normalize_speech(text: str) -> str:
    """Normalize text by stripping diacritics and extra punctuation for robust command matching."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return stripped.lower().strip()


_CHIME_FILE_PATH = None


def _get_siri_chime_wav_path() -> str:
    """Generate or retrieve a crisp two-tone assistant chime (D5 -> A5) WAV file."""
    global _CHIME_FILE_PATH
    if _CHIME_FILE_PATH and os.path.isfile(_CHIME_FILE_PATH):
        return _CHIME_FILE_PATH

    path = os.path.join(tempfile.gettempdir(), "juicevault_siri_chime.wav")
    try:
        sample_rate = 48000
        duration1 = 0.09
        duration2 = 0.18
        freq1 = 587.33  # D5
        freq2 = 880.00  # A5

        frames = bytearray()
        total_samples1 = int(sample_rate * duration1)
        total_samples2 = int(sample_rate * duration2)

        for i in range(total_samples1):
            t = i / sample_rate
            env = 1.0 - (i / total_samples1) ** 1.8
            val = int(env * 18000 * math.sin(2 * math.pi * freq1 * t))
            frames.extend(struct.pack('<hh', val, val))

        for i in range(total_samples2):
            t = i / sample_rate
            env = 1.0 - (i / total_samples2) ** 1.3
            val = int(env * 20000 * math.sin(2 * math.pi * freq2 * t))
            frames.extend(struct.pack('<hh', val, val))

        with wave.open(path, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(frames)

        _CHIME_FILE_PATH = path
        return path
    except Exception as exc:
        log.warning(f"[JuiceVault Voice] Failed generating chime: {exc}")
        return ""


def _get_ffmpeg_exe() -> str:
    """Find FFmpeg executable via imageio_ffmpeg, which is standard in Red-DiscordBot envs, or system PATH."""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    import shutil
    return shutil.which("ffmpeg") or "ffmpeg"


def _detect_user_language(text: str, default_lang: str = "ro-RO") -> str:
    """Return 'ro' or 'en' based on vocabulary and detected speech recognition locale."""
    clean = _normalize_speech(text)
    words = set(re.findall(r'[a-z0-9]+', clean))
    ro_markers = {"ba", "bai", "hei", "cauta", "baga", "pune", "canta", "da", "nu", "piesa", "melodia", "urmatoarea", "sari", "schimba", "dupa", "de", "pe", "te", "rog", "sigur", "bine", "hai", "inapoi", "vreau", "ascult"}
    en_markers = {"hey", "hi", "search", "play", "skip", "next", "pause", "resume", "forward", "back", "rewind", "on", "from", "yes", "yeah", "yep", "no", "sure", "please", "track", "song", "what", "shuffle", "like"}

    ro_score = len(words & ro_markers)
    en_score = len(words & en_markers)

    if ro_score > en_score:
        return "ro"
    if en_score > ro_score:
        return "en"
    return "en" if "en" in default_lang.lower() else "ro"


def _mix_pcm(music_pcm: bytes, overlay_pcm: bytes, music_vol: float) -> bytes:
    """Mix 48kHz 16-bit stereo PCM bytes with ducking volume scaling."""
    try:
        import audioop
        m = audioop.mul(music_pcm, 2, max(0.0, min(1.0, music_vol)))
        if overlay_pcm:
            if len(m) > len(overlay_pcm):
                overlay_pcm = overlay_pcm + b'\x00' * (len(m) - len(overlay_pcm))
            elif len(overlay_pcm) > len(m):
                m = m + b'\x00' * (len(overlay_pcm) - len(m))
            return audioop.add(m, overlay_pcm, 2)
        return m
    except Exception:
        pass

    target_len = max(len(music_pcm), len(overlay_pcm))
    if not target_len:
        return b''
    if len(music_pcm) < target_len:
        music_pcm = music_pcm + b'\x00' * (target_len - len(music_pcm))
    if len(overlay_pcm) < target_len:
        overlay_pcm = overlay_pcm + b'\x00' * (target_len - len(overlay_pcm))

    a_music = array.array('h')
    a_music.frombytes(music_pcm)
    if overlay_pcm:
        a_over = array.array('h')
        a_over.frombytes(overlay_pcm)
        for i in range(len(a_music)):
            v = int(a_music[i] * music_vol + a_over[i])
            if v > 32767:
                a_music[i] = 32767
            elif v < -32768:
                a_music[i] = -32768
            else:
                a_music[i] = v
    else:
        for i in range(len(a_music)):
            a_music[i] = int(a_music[i] * music_vol)
    return a_music.tobytes()


class DuckingAudioSource:
    """AudioSource wrapper that ducks the main music volume to 5% (0.05) whenever
    an overlay audio stream (Garmin TTS or Siri chime) is playing."""

    def __init__(self, main_source):
        self.main_source = main_source
        self.overlay_source = None
        self._lock = threading.Lock()
        self.current_volume = 1.0
        self.target_volume = 1.0

    def is_opus(self) -> bool:
        return False

    def set_overlay(self, overlay_source):
        with self._lock:
            if self.overlay_source:
                try:
                    self.overlay_source.cleanup()
                except Exception:
                    pass
            self.overlay_source = overlay_source
            self.target_volume = 0.05  # Duck music down to 5% volume!

    def is_overlay_playing(self) -> bool:
        with self._lock:
            return self.overlay_source is not None

    def read(self) -> bytes:
        music_data = b''
        if self.main_source:
            try:
                music_data = self.main_source.read()
            except Exception:
                music_data = b''

        with self._lock:
            overlay = self.overlay_source

        if not music_data and not overlay:
            return b''

        # Smooth volume ducking / recovery ramp
        if self.current_volume < self.target_volume:
            self.current_volume = min(self.target_volume, self.current_volume + 0.15)
        elif self.current_volume > self.target_volume:
            self.current_volume = max(self.target_volume, self.current_volume - 0.25)

        vol = self.current_volume

        overlay_data = b''
        if overlay:
            try:
                overlay_data = overlay.read()
            except Exception:
                overlay_data = b''

            if not overlay_data:
                # Overlay stream completed
                with self._lock:
                    if self.overlay_source is overlay:
                        try:
                            overlay.cleanup()
                        except Exception:
                            pass
                        self.overlay_source = None
                        self.target_volume = 1.0  # Restore music volume to 100%!

        if not overlay_data and vol >= 0.98:
            return music_data

        if not music_data and overlay_data:
            return overlay_data

        return _mix_pcm(music_data, overlay_data, vol)

    def cleanup(self):
        with self._lock:
            if self.overlay_source:
                try:
                    self.overlay_source.cleanup()
                except Exception:
                    pass
                self.overlay_source = None
        if self.main_source:
            try:
                self.main_source.cleanup()
            except Exception:
                pass


async def play_chime_and_proceed(guild, action_coro=None, interrupt_playback: bool = False):
    """Play the Siri assistant chime in voice channel, then execute the command action.
    If music is actively playing, ducks music to 5% without stopping the track."""
    voice = getattr(guild, "voice_client", None)
    chime_path = _get_siri_chime_wav_path()
    if voice and voice.is_connected() and chime_path and os.path.isfile(chime_path):
        try:
            import discord
            exe = _get_ffmpeg_exe()
            mixer = getattr(voice, "_jv_mixer", None)
            if voice.is_playing() and mixer is not None:
                # Play chime over ducked music (5% volume) without stopping music!
                chime_source = discord.FFmpegPCMAudio(chime_path, executable=exe)
                mixer.set_overlay(chime_source)
                await asyncio.sleep(0.35)
            elif not voice.is_playing() or interrupt_playback:
                if voice.is_playing() or voice.is_paused():
                    voice.stop()
                    for _ in range(20):
                        if not voice.is_playing():
                            break
                        await asyncio.sleep(0.02)
                voice.play(discord.FFmpegPCMAudio(chime_path, executable=exe))
                await asyncio.sleep(0.35)
        except Exception as exc:
            print(f"[JuiceVault Chime] Error: {exc}")
    if action_coro is not None:
        if asyncio.iscoroutine(action_coro):
            await action_coro


async def speak_in_voice(guild, text: str, lang: str = "ro"):
    """Fetch Google Translate TTS and speak out loud directly in the voice channel.
    If music is actively playing, ducks music to 5% volume and speaks over it."""
    voice = getattr(guild, "voice_client", None)
    if not voice or not voice.is_connected():
        return
    import urllib.parse
    import discord

    clean_tts = re.sub(r'[*_~`#<>|]', '', text).strip()
    if not clean_tts:
        return

    clean_tts = clean_tts[:150]
    encoded_q = urllib.parse.quote(clean_tts)
    tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_q}&tl={lang}&client=tw-ob"
    path = os.path.join(tempfile.gettempdir(), f"jv_voice_tts_{guild.id}.mp3")

    downloaded = False
    try:
        import aiohttp
        timeout = aiohttp.ClientTimeout(total=4)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(tts_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    with open(path, "wb") as f:
                        f.write(data)
                    downloaded = True
    except Exception:
        pass

    if not downloaded:
        try:
            import urllib.request
            req = urllib.request.Request(tts_url, headers={"User-Agent": "Mozilla/5.0"})
            def _dl():
                with urllib.request.urlopen(req, timeout=4) as resp:
                    if resp.status == 200:
                        with open(path, "wb") as f:
                            f.write(resp.read())
                        return True
                    return False
            downloaded = await asyncio.to_thread(_dl)
        except Exception as exc:
            print(f"[JuiceVault Voice TTS] Download error: {exc}")
            return

    if not downloaded or not os.path.isfile(path) or os.path.getsize(path) < 100:
        return

    try:
        exe = _get_ffmpeg_exe()
        mixer = getattr(voice, "_jv_mixer", None)
        if voice.is_playing() and mixer is not None:
            # Music is actively playing -> DUCK music to 5% and speak over it!
            print(f"[JuiceVault Voice TTS] 🔊 Speaking over ducked music (5%) in '{guild.name}': \"{clean_tts}\" ({lang})")
            overlay = discord.FFmpegPCMAudio(path, executable=exe)
            mixer.set_overlay(overlay)
            duration = max(1.5, min(8.0, len(clean_tts) * 0.085 + 0.4))
            for _ in range(int(duration / 0.1)):
                if not mixer.is_overlay_playing():
                    break
                await asyncio.sleep(0.1)
        else:
            # No music playing -> play directly on voice client
            if voice.is_playing() or voice.is_paused():
                voice.stop()
                for _ in range(25):
                    if not voice.is_playing():
                        break
                    await asyncio.sleep(0.04)

            print(f"[JuiceVault Voice TTS] 🔊 Speaking in '{guild.name}': \"{clean_tts}\" ({lang})")
            voice.play(discord.FFmpegPCMAudio(path, executable=exe))
            duration = max(1.5, min(7.0, len(clean_tts) * 0.085))
            for _ in range(int(duration / 0.1)):
                if not voice.is_playing():
                    break
                await asyncio.sleep(0.1)
    except Exception as exc:
        print(f"[JuiceVault Voice TTS] Playback error: {exc}")

DAVEY_AVAILABLE = False
try:
    import davey
    DAVEY_AVAILABLE = True
except ImportError:
    davey = None

# 1. Check optional dependencies: discord-ext-voice-recv and SpeechRecognition
VOICE_RECV_AVAILABLE = False
try:
    from discord.ext import voice_recv
    VOICE_RECV_AVAILABLE = True

    # Hotfix for discord-ext-voice-recv:
    # 1. DAVE (Discord Audio/Video E2EE) inbound frame decryption + OpusError corrupted stream resilience.
    try:
        from discord.ext.voice_recv import opus as _vr_opus
        import discord.opus
        if hasattr(_vr_opus, "PacketDecoder"):
            _orig_decode_packet = _vr_opus.PacketDecoder._decode_packet

            def _safe_decode_packet(self, packet):
                try:
                    return _orig_decode_packet(self, packet)
                except discord.opus.OpusError:
                    # Reset decoder and ignore corrupted frame
                    try:
                        self._decoder = discord.opus.Decoder()
                    except Exception:
                        pass
                    return packet, None
                except Exception:
                    return packet, None

            _vr_opus.PacketDecoder._decode_packet = _safe_decode_packet

            def _dave_decrypt(decoder, packet):
                """Decrypt a DAVE (E2EE) frame in place using discord.py's DaveSession."""
                if davey is None or not packet or not getattr(packet, "decrypted_data", None):
                    return

                sink = getattr(decoder, "sink", None)
                vc = getattr(sink, "voice_client", None)
                state = getattr(vc, "_connection", None)
                session = getattr(state, "dave_session", None)
                if (
                    session is None
                    or not getattr(session, "ready", False)
                    or getattr(state, "dave_protocol_version", 0) == 0
                ):
                    return

                user_id = getattr(decoder, "_cached_id", None)
                if user_id is None:
                    return

                try:
                    packet.decrypted_data = session.decrypt(
                        int(user_id), davey.MediaType.audio, bytes(packet.decrypted_data)
                    )
                except Exception:
                    # Silence frames or passthrough frames raise; leave unencrypted
                    pass

            _orig_process_packet = _vr_opus.PacketDecoder._process_packet

            def _safe_process_packet(self, packet):
                member = self._get_cached_member()
                if member is None:
                    try:
                        self._cached_id = self.sink.voice_client._get_id_from_ssrc(self.ssrc)
                    except Exception:
                        pass
                    member = self._get_cached_member()

                # Decrypt DAVE payload if channel uses E2EE
                _dave_decrypt(self, packet)

                pcm = None
                if not self.sink.wants_opus():
                    packet, pcm = self._decode_packet(packet)

                voice_data_cls = getattr(_vr_opus, "VoiceData", getattr(voice_recv, "VoiceData", None))
                if voice_data_cls is not None:
                    data = voice_data_cls(packet, member, pcm=pcm)
                else:
                    data = _orig_process_packet(self, packet)
                self._last_seq = packet.sequence
                self._last_ts = packet.timestamp
                return data

            _vr_opus.PacketDecoder._process_packet = _safe_process_packet
    except Exception as _e:
        log.debug(f"[JuiceVault Voice] PacketDecoder patch note: {_e}")

    # 2. PacketRouter._do_run should catch transient errors and keep running
    try:
        from discord.ext.voice_recv import router as _vr_router
        if hasattr(_vr_router, "PacketRouter"):
            _orig_do_run = _vr_router.PacketRouter._do_run

            def _safe_do_run(self):
                try:
                    _orig_do_run(self)
                except Exception as _rexc:
                    log.debug(f"[JuiceVault Voice] PacketRouter caught: {_rexc}")

            _vr_router.PacketRouter._do_run = _safe_do_run
    except Exception as _e:
        log.debug(f"[JuiceVault Voice] PacketRouter patch note: {_e}")

except ImportError:
    voice_recv = None

SPEECH_RECOGNITION_AVAILABLE = False
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    sr = None


def is_voice_recognition_supported():
    """Return whether all dependencies for in-Discord voice recognition are installed."""
    missing = []
    if not VOICE_RECV_AVAILABLE:
        missing.append("discord-ext-voice-recv")
    if not SPEECH_RECOGNITION_AVAILABLE:
        missing.append("SpeechRecognition")
    if not DAVEY_AVAILABLE:
        missing.append("davey")

    if missing:
        return False, "pip install " + " ".join(missing)
    return True, "Ready"


def get_voice_client_cls():
    """Return VoiceRecvClient if available, otherwise return standard VoiceClient."""
    if VOICE_RECV_AVAILABLE and hasattr(voice_recv, "VoiceRecvClient"):
        return voice_recv.VoiceRecvClient
    import discord
    return discord.VoiceClient


# Per-guild voice command settings in bot memory
_guild_voice_cmd_enabled = {}
_active_sinks = {}


async def is_voice_commands_enabled_for_guild(cog, guild_id):
    """Check if voice commands are enabled for guild in memory or config."""
    if guild_id in _guild_voice_cmd_enabled:
        return _guild_voice_cmd_enabled[guild_id]
    if hasattr(cog, "config"):
        try:
            val = await cog.config.guild_from_id(guild_id).get_raw("voice_commands_enabled", default=True)
            _guild_voice_cmd_enabled[guild_id] = bool(val)
            return bool(val)
        except Exception:
            pass
    return True


async def set_voice_commands_enabled_for_guild(cog, guild_id, enabled: bool):
    """Enable or disable voice commands for guild."""
    _guild_voice_cmd_enabled[guild_id] = bool(enabled)
    if hasattr(cog, "config"):
        try:
            await cog.config.guild_from_id(guild_id).set_raw("voice_commands_enabled", value=bool(enabled))
        except Exception:
            pass

    # Update active sink if connected
    sink = _active_sinks.get(guild_id)
    if sink:
        sink._active = bool(enabled)


if VOICE_RECV_AVAILABLE and SPEECH_RECOGNITION_AVAILABLE:

    class VoiceCommandAudioSink(voice_recv.AudioSink):
        """Audio sink capturing PCM voice packets from Discord users, buffering utterances,
        and transcribing speech to execute player actions (Skip, Next, Pause, Play, etc.)."""

        def __init__(self, bot, cog, guild_id):
            super().__init__()
            self.bot = bot
            self.cog = cog
            self.guild_id = guild_id
            self._buffers = {}       # user_id -> bytearray
            self._last_speech = {}   # user_id -> timestamp
            self._cooldowns = {}     # user_id -> timestamp
            self._wake_windows = {}  # user_id -> monotonic timestamp deadline
            self._active = True
            self._recognizer = sr.Recognizer()
            self._worker_task = asyncio.create_task(self._process_silence_loop())

        def wants_opus(self) -> bool:
            return False  # Decode Opus packets to 48kHz 16-bit stereo PCM

        def write(self, user, data):
            if not self._active or not user or getattr(user, "bot", False):
                return
            now = time.monotonic()
            uid = user.id

            # Cooldown per user after executing a command (2.5 seconds)
            if now - self._cooldowns.get(uid, 0.0) < 2.5:
                return

            pcm = getattr(data, "pcm", None)
            if not pcm:
                return

            buf = self._buffers.setdefault(uid, bytearray())
            if len(buf) == 0:
                print(f"[JuiceVault Voice] 🎙️ Audio received from {getattr(user, 'display_name', user)} - listening...")
            # Buffer up to 10 seconds of audio (~960,000 bytes)
            if len(buf) < 960_000:
                buf.extend(pcm)
            self._last_speech[uid] = now

        async def _process_silence_loop(self):
            """Monitors when a user finishes speaking (0.6s silence) and dispatches audio to STT."""
            try:
                while self._active:
                    await asyncio.sleep(0.25)
                    now = time.monotonic()
                    uids = list(self._last_speech.keys())
                    for uid in uids:
                        last = self._last_speech.get(uid, 0.0)
                        # Detected end of utterance: 0.6s silence and minimum 0.5s audio
                        if now - last >= 0.6:
                            buf = self._buffers.pop(uid, bytearray())
                            self._last_speech.pop(uid, None)
                            if len(buf) >= 48_000:
                                self._cooldowns[uid] = now
                                asyncio.create_task(self._transcribe_and_dispatch(uid, bytes(buf)))
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                log.debug(f"[JuiceVault Voice] Silence detection loop error: {exc}")

        async def _play_track_now(self, guild, track):
            """Queue a track at index 0 and immediately start playback."""
            gid = self.guild_id
            self.cog.manual_queues.setdefault(gid, []).insert(0, track)
            voice = guild.voice_client
            if gid in self.cog.tasks:
                if gid in self.cog.skip_events:
                    self.cog.skip_events[gid].set()
                if voice and (voice.is_playing() or voice.is_paused()):
                    voice.stop()
            else:
                if voice and voice.channel:
                    self.cog.stop_events[gid] = asyncio.Event()
                    self.cog.skip_events[gid] = asyncio.Event()
                    self.cog.seek_events[gid] = asyncio.Event()
                    self.cog.skip_counts[gid] = 0
                    self.cog.effects[gid] = "none"
                    self.cog.tasks[gid] = asyncio.create_task(self.cog._player(guild, voice.channel))

            ui = self.bot.get_cog("JuiceVaultUI")
            if ui:
                asyncio.create_task(ui.update_panel(gid))
            if hasattr(self.cog, "web_remote") and self.cog.web_remote:
                asyncio.create_task(self.cog.web_remote.broadcast_state(gid))

        async def _search_and_play_youtube(self, guild, query: str, user_name: str, lang: str = "ro"):
            """Search YouTube for query, speak confirmation, and begin immediate playback."""
            if not query:
                return
            clean_q = query.strip()
            wait_speech = f"Caut pe YouTube {clean_q}" if lang == "ro" else f"Searching YouTube for {clean_q}"
            await play_chime_and_proceed(guild)
            await speak_in_voice(guild, wait_speech, lang=lang)
            await self._notify(guild, f"🔍 **[Garmin]** {user_name}: Caut *\"{clean_q}\"* pe YouTube... ⏳" if lang == "ro" else f"🔍 **[Garmin]** {user_name}: Searching YouTube for *\"{clean_q}\"*... ⏳")

            try:
                from .external_search_patch import _extract_search
                info = await asyncio.to_thread(_extract_search, clean_q)
                if info:
                    if info.get("_is_playlist"):
                        entries = info.get("entries") or []
                        yt_track = entries[0] if entries else None
                    else:
                        yt_track = info

                    if yt_track:
                        await self._play_track_now(guild, yt_track)
                        title = yt_track.get("title") or clean_q
                        await self._notify(guild, f"🎥 **[Garmin]** Redare de pe YouTube: **{title}** 🎶" if lang == "ro" else f"🎥 **[Garmin]** Playing from YouTube: **{title}** 🎶")
                        return

                fail_msg = f"Nu am găsit piesa {clean_q} pe YouTube." if lang == "ro" else f"Could not find {clean_q} on YouTube."
                await speak_in_voice(guild, fail_msg, lang=lang)
                await self._notify(guild, f"❌ **[Garmin]** {fail_msg}")
            except Exception as exc:
                print(f"[Garmin YouTube] Error searching '{clean_q}': {exc}")
                fail_msg = f"Nu am găsit rezultate pe YouTube pentru {clean_q}." if lang == "ro" else f"No YouTube results found for {clean_q}."
                await speak_in_voice(guild, fail_msg, lang=lang)
                await self._notify(guild, f"❌ **[Garmin]** {fail_msg}")

        async def _transcribe_and_dispatch(self, user_id, pcm_bytes):
            loop = asyncio.get_running_loop()
            try:
                text, detected_lang = await loop.run_in_executor(None, self._recognize_speech_blocking, pcm_bytes)
            except Exception as exc:
                print(f"[JuiceVault Voice] Transcribe executor error: {exc}")
                return

            if not text:
                return

            clean = _normalize_speech(text)
            guild = self.bot.get_guild(self.guild_id)
            user = guild.get_member(user_id) if guild else None
            user_name = user.display_name if user else f"User {user_id}"
            now = time.monotonic()
            print(f"[JuiceVault Voice] Received speech from {user_name} ({detected_lang}): '{text}' (normalized: '{clean}')")

            user_lang = _detect_user_language(text, default_lang=detected_lang)
            is_ro = (user_lang == "ro")

            # Check if this utterance is answering a pending YouTube question
            pending = getattr(self.cog, "_pending_yt_voice", {}).get(self.guild_id)
            if pending and time.time() < pending.get("expires", 0.0):
                pending_lang = pending.get("lang", user_lang)
                if pending.get("awaiting_title"):
                    clean_title = re.sub(r'^(?:hey\s+|ok\s+|hei\s+|ba\s+|bai\s+|alo\s+|yo\s+)?(?:garmin|garmen|garmon|garmyn|carmin|carmen|darmin|german|barmin)\s*', '', clean, flags=re.I).strip()
                    self.cog._pending_yt_voice.pop(self.guild_id, None)
                    await self._search_and_play_youtube(guild, clean_title or clean, user_name, lang=pending_lang)
                    return

                is_affirmative = any(w in clean for w in ("da", "yes", "sure", "sigur", "baga", "cauta", "pune", "pune-o", "canta-o", "play it", "ok", "yep", "bine", "hai", "da te rog", "te rog", "youtube", "pe youtube", "de pe youtube", "dupa youtube", "play youtube", "pe yt"))
                is_negative = any(w in clean for w in ("nu", "no", "cancel", "anuleaza", "stop", "lasa", "nevermind", "nu mai"))
                if is_affirmative:
                    self.cog._pending_yt_voice.pop(self.guild_id, None)
                    target_q = pending["query"]
                    await self._search_and_play_youtube(guild, target_q, user_name, lang=pending_lang)
                    return
                elif is_negative:
                    self.cog._pending_yt_voice.pop(self.guild_id, None)
                    cancel_msg = "🚫 **[Garmin]** Comandă anulată." if pending_lang == "ro" else "🚫 **[Garmin]** Cancelled."
                    await speak_in_voice(guild, "Comandă anulată." if pending_lang == "ro" else "Cancelled.", lang=pending_lang)
                    await self._notify(guild, cancel_msg)
                    return

            # Check for Garmin Wake Word: "garmin", "ba garmin", "hey garmin", "ok garmin", "carmen", "darmin", etc.
            wake_match = re.search(r'\b(?:hey\s+|ok\s+|hei\s+|ba\s+|bai\s+|alo\s+|yo\s+)?(?:garmin|garmen|garmon|garmyn|carmin|carmen|darmin|german|barmin)\b', clean, re.IGNORECASE)

            if wake_match:
                cmd_part = clean[wake_match.end():].strip().lstrip(",.:;!?- ")
                if not cmd_part:
                    # User only said "Garmin" -> wake up for 10 seconds and greet in user's language!
                    self._wake_windows[user_id] = now + 10.0
                    print(f"[JuiceVault Voice] Wake word 'Garmin' activated by {user_name}. Waiting for command...")
                    await play_chime_and_proceed(guild)
                    greeting = f"Da, {user_name}? Ascult..." if is_ro else f"Yes, {user_name}? I'm listening..."
                    await speak_in_voice(guild, greeting, lang=user_lang)
                    await self._notify(guild, f"🎤 **[Garmin]** {greeting} 🟢")
                    return
                clean_cmd = cmd_part
                self._wake_windows.pop(user_id, None)
            else:
                # Check if within active wake window
                if now < self._wake_windows.get(user_id, 0.0):
                    clean_cmd = clean
                    self._wake_windows.pop(user_id, None)
                else:
                    # Utterance did NOT contain Garmin and not in wake window -> log and ignore
                    print(f"[JuiceVault Voice] Ignored utterance from {user_name} (no 'Garmin' wake word): '{clean}'")
                    return

            print(f"[JuiceVault Voice Command] {user_name} -> Garmin command: '{clean_cmd}' (full: '{clean}') [lang: {user_lang}]")

            # 1. SEEK / DERULARE 10s
            if any(w in clean_cmd for w in ("inainte 10", "forward 10", "skip 10s", "10 secunde inainte")):
                if hasattr(self.cog, "_request_seek"):
                    await play_chime_and_proceed(guild, self.cog._request_seek(self.guild_id, delta=10.0))
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Forward +10s ⏩")
                    return
            elif any(w in clean_cmd for w in ("inapoi 10", "back 10", "rewind 10", "10 secunde inapoi")):
                if hasattr(self.cog, "_request_seek"):
                    await play_chime_and_proceed(guild, self.cog._request_seek(self.guild_id, delta=-10.0))
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Rewind -10s ⏪")
                    return

            # 2. DIRECT YOUTUBE SEARCH & PLAY
            # Handles: "cauta pe youtube yeat", "cauta yeat pe youtube", "baga dupa youtube drake", "play drake on youtube", etc.
            if "youtube" in clean_cmd or " yt" in clean_cmd or clean_cmd.startswith("yt "):
                yt_q = re.sub(r'\b(?:cauta|baga|pune|play|gaseste|search|reda|da-i play la|dai play la)?\s*(?:pe|de\s+pe|dupa|from|on)?\s*(?:youtube|yt)\s*(?:pentru|for|cu|de\s+la|by)?\b', '', clean_cmd, flags=re.I).strip()
                yt_q = re.sub(r'^(?:cauta|baga|pune|play|gaseste|search|reda|da-i play la|dai play la)\s+(?:piesa|melodia|track|song)?\s*(?:cu|de\s+la|by)?\s*', '', yt_q, flags=re.I).strip()
                yt_q = yt_q.strip(" ,.:;!?-")

                if not yt_q:
                    # User only said "Garmin bagă după YouTube" without a song title
                    self._wake_windows[user_id] = now + 15.0
                    if not hasattr(self.cog, "_pending_yt_voice"):
                        self.cog._pending_yt_voice = {}
                    self.cog._pending_yt_voice[self.guild_id] = {
                        "user_id": user_id,
                        "query": "",
                        "lang": user_lang,
                        "expires": time.time() + 20.0,
                        "user_name": user_name,
                        "awaiting_title": True,
                    }
                    prompt_speech = "Ce piesă vrei să caut pe YouTube?" if is_ro else "What track would you like me to search on YouTube?"
                    await play_chime_and_proceed(guild)
                    await speak_in_voice(guild, prompt_speech, lang=user_lang)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: {prompt_speech} ⏳")
                    return

                # User provided song title for YouTube! Search and play immediately!
                print(f"[JuiceVault Voice] Direct YouTube request from {user_name}: '{yt_q}'")
                await self._search_and_play_youtube(guild, yt_q, user_name, lang=user_lang)
                return

            # 3. SEARCH & PLAY SONG (handles "cauta drake", "cauta yeat", "baga 6ix9ine", "canta robbery", "da-i play la robbery", "play fire", etc.)
            play_match = re.match(
                r'^(?:canta|pune|baga|play|asculta|cauta|gaseste|search|reda|da-i play la|dai play la|da play la|da-i drumul la|dai drumul la)\s+(?:piesa|melodia|melodie|track|song)?\s*(?:cu|de\s+la|by)?\s*(.+)$',
                clean_cmd,
                re.IGNORECASE
            )
            if play_match:
                q = play_match.group(1).strip().strip(" ,.:;!?-")
                if q:
                    try:
                        tracks = await self.cog.fetch_tracks()
                        candidates = [item for item in tracks if q in _normalize_speech(self.cog._search_text(item))]
                        track = candidates[0] if candidates else None
                        if track:
                            await play_chime_and_proceed(guild)
                            await self._play_track_now(guild, track)
                            track_name = self.cog._track_text(track)
                            await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Redau: **{track_name}** 🎶" if is_ro else f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Playing: **{track_name}** 🎶")
                            return
                        else:
                            # Not found in JuiceVault archive -> speak question to user in voice channel & text chat!
                            print(f"[JuiceVault Voice] Track '{q}' not found in archive -> Proposing YouTube fallback")
                            if not hasattr(self.cog, "_pending_yt_voice"):
                                self.cog._pending_yt_voice = {}
                            self.cog._pending_yt_voice[self.guild_id] = {
                                "user_id": user_id,
                                "query": q,
                                "lang": user_lang,
                                "expires": time.time() + 45.0,
                                "user_name": user_name,
                            }
                            # Extend wake window so the user can just answer "Da" without repeating "Garmin"
                            self._wake_windows[user_id] = now + 45.0

                            if is_ro:
                                ask_speech = f"Piesa {q} nu se află în JuiceVault. Vrei să o caut pe YouTube?"
                                ask_msg = f"🎤 **[Garmin]** {user_name}: Piesa *\"{q}\"* nu se află în JuiceVault. Vrei să o caut și să o redau de pe **YouTube**? *(Zi **„Garmin, da”** sau scrie **da**)*"
                            else:
                                ask_speech = f"Track {q} was not found in JuiceVault. Would you like me to search on YouTube?"
                                ask_msg = f"🎤 **[Garmin]** {user_name}: Track *\"{q}\"* was not found in the JuiceVault archive. Would you like me to play it from **YouTube**? *(Say **\"Garmin, yes\"** or type **yes**)*"

                            await speak_in_voice(guild, ask_speech, lang=user_lang)
                            await self._notify(guild, ask_msg)
                            return
                    except Exception as e:
                        log.warning(f"[Garmin Voice Search] Error searching: {e}")

            # 4. SKIP / NEXT (handles "skip", "next", "da-i skip", "dai skip", "urmatoarea", "sari", etc.)
            if any(w in clean_cmd for w in ("skip", "next", "urmatoarea", "sari", "urmatorul", "treci peste", "schimba", "schimb-o", "alta piesa", "alta melodie", "da-i skip", "dai skip", "treci")):
                if any(w in clean_cmd for w in ("10", "ten", "zece")):
                    await play_chime_and_proceed(guild, self.cog._request_skip(self.guild_id, 10))
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Skipped 10 tracks! ⏩")
                else:
                    await play_chime_and_proceed(guild, self.cog._request_skip(self.guild_id, 1))
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Skipped track! ⏭️")
                return

            # 5. PREVIOUS / BACK
            elif any(w in clean_cmd for w in ("previous", "prev", "back", "inapoi", "anterioara", "piesa anterioara", "melodia anterioara")):
                hist = self.cog.history.get(self.guild_id, [])
                if hist:
                    prev_t = hist.pop()
                    await play_chime_and_proceed(guild)
                    await self._play_track_now(guild, prev_t)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Previous track! ⏮️")
                return

            # 6. PAUSE
            elif any(w in clean_cmd for w in ("pause", "pauza", "stop", "opreste", "taci")):
                voice = guild.voice_client if guild else None
                if voice and voice.is_playing():
                    await play_chime_and_proceed(guild)
                    if hasattr(self.cog, "pause_playback"):
                        self.cog.pause_playback(self.guild_id)
                    else:
                        voice.pause()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Paused! ⏸️")
                return

            # 7. RESUME / PLAY
            elif any(w in clean_cmd for w in ("resume", "play", "continua", "porneste", "da drumul", "baga")):
                voice = guild.voice_client if guild else None
                if voice and voice.is_paused():
                    await play_chime_and_proceed(guild)
                    if hasattr(self.cog, "resume_playback"):
                        self.cog.resume_playback(self.guild_id)
                    else:
                        voice.resume()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Resumed playback! ▶️")
                elif voice and not voice.is_playing() and (self.guild_id not in self.cog.tasks or self.cog.tasks[self.guild_id].done()):
                    category = await self.cog.config.guild(guild).category()
                    tracks = await self.cog.fetch_tracks(category)
                    if category not in getattr(self.cog, "CATEGORY_URLS", {}) and category != "all":
                        tracks = self.cog._filter_tracks(tracks, category)
                    if tracks:
                        self.cog.queues[self.guild_id] = tracks
                        self.cog.manual_queues[self.guild_id] = []
                        self.cog.stop_events[self.guild_id] = asyncio.Event()
                        self.cog.skip_events[self.guild_id] = asyncio.Event()
                        self.cog.seek_events[self.guild_id] = asyncio.Event()
                        self.cog.skip_counts[self.guild_id] = 0
                        self.cog.effects[self.guild_id] = "none"
                        await play_chime_and_proceed(guild)
                        self.cog.tasks[self.guild_id] = asyncio.create_task(self.cog._player(guild, voice.channel))
                        await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Pornesc redarea! ▶️" if is_ro else f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Started playback! ▶️")
                return

            # 7b. LEAVE / DISCONNECT
            elif any(w in clean_cmd for w in ("leave", "pleaca", "iesi", "deconecteaza", "deconecteaza-te", "disconnect")):
                await play_chime_and_proceed(guild)
                await self.cog.config.guild(guild).enabled.set(False)
                await self.cog._stop(self.guild_id)
                await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Deconectat din voice! 👋" if is_ro else f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Left voice channel! 👋")
                return

            # 8. SHUFFLE
            elif any(w in clean_cmd for w in ("shuffle", "amesteca", "mix")):
                q = self.cog.queues.get(self.guild_id, [])
                if q:
                    import random
                    random.shuffle(q)
                    self.cog._cleanup_prefetch(self.guild_id)
                    self.cog._trigger_next_prefetch(self.guild_id)
                    await play_chime_and_proceed(guild)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Shuffled queue! 🔀")
                return

            # 9. FAVORITE
            elif any(w in clean_cmd for w in ("favorite", "fav", "like", "place", "iubeste", "favorit", "apreciaza")):
                cur = self.cog.current.get(self.guild_id)
                if cur:
                    bot_favs = getattr(self.bot, "_jv_data", {}).setdefault("favorites", {})
                    u_list = bot_favs.setdefault(str(user_id), [])
                    if not any(str(x.get("id")) == str(cur.get("id")) for x in u_list):
                        u_list.insert(0, dict(cur))
                        if hasattr(self.cog, "web_remote") and self.cog.web_remote:
                            try:
                                await self.cog.web_remote.config.favorites.set(bot_favs)
                            except Exception:
                                pass
                        await play_chime_and_proceed(guild)
                        await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Added to favorites! ❤️")
                return

            # Feedback when recognized speech was addressed to Garmin but didn't match known command
            await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Comandă nerecunoscută.")

        def _recognize_speech_blocking(self, pcm_bytes):
            """Convert Discord 48kHz stereo PCM to 16kHz mono PCM, then recognize with Google."""
            try:
                a = array.array('h')
                a.frombytes(pcm_bytes)
                # Discord sends 48kHz 16-bit stereo (2 channels interleaved).
                # To get 16kHz mono (downsampled 3x): taking every 3rd left-channel sample: index [0::6]!
                mono_16k = a[0::6].tobytes()
            except Exception as e:
                print(f"[JuiceVault Voice] Audio conversion error: {e}")
                return None, "ro-RO"

            if not mono_16k or len(mono_16k) < 3200:
                return None, "ro-RO"

            audio_data = sr.AudioData(mono_16k, 16000, 2)
            first_cand = None
            first_lang = "ro-RO"
            for lang in ("ro-RO", "en-US"):
                try:
                    res = self._recognizer.recognize_google(audio_data, language=lang)
                    if res:
                        print(f"[JuiceVault Voice] Google STT recognized ({lang}): '{res}'")
                        lower_res = res.lower()
                        if any(k in lower_res for k in ("garmin", "garmen", "garmon", "carmin", "carmen", "skip", "next", "pause", "play", "canta", "pune", "baga", "urmatoarea", "sari", "da", "nu")):
                            return res, lang
                        if first_cand is None:
                            first_cand = res
                            first_lang = lang
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as exc:
                    print(f"[JuiceVault Voice] Google STT network/API error: {exc}")
                except Exception as exc:
                    print(f"[JuiceVault Voice] Google STT exception: {type(exc).__name__}: {exc}")
            return first_cand, first_lang

        async def _notify(self, guild, message):
            """Send feedback message in the configured text channel and active voice channel."""
            if not guild:
                return
            try:
                target_channels = []
                # 1. Configured music text channel (where panel / commands live)
                if hasattr(self.cog, "config"):
                    try:
                        channel_id = await self.cog.config.guild(guild).channel_id()
                        if channel_id:
                            ch = guild.get_channel(channel_id)
                            if ch and hasattr(ch, "send"):
                                target_channels.append(ch)
                    except Exception:
                        pass

                # Check JuiceVaultUI panel text channel
                ui = self.bot.get_cog("JuiceVaultUI")
                if ui and hasattr(ui, "config"):
                    try:
                        pch_id = await ui.config.guild(guild).panel_channel_id()
                        if pch_id:
                            pch = guild.get_channel(pch_id)
                            if pch and hasattr(pch, "send") and pch not in target_channels:
                                target_channels.append(pch)
                    except Exception:
                        pass

                # 2. Voice channel chat if different
                voice = getattr(guild, "voice_client", None)
                if voice and voice.channel and hasattr(voice.channel, "send") and voice.channel not in target_channels:
                    target_channels.append(voice.channel)

                # 3. Default text channel fallback
                if not target_channels and guild.text_channels:
                    target_channels.append(guild.text_channels[0])

                for ch in target_channels:
                    try:
                        await ch.send(message, delete_after=35)
                    except Exception:
                        pass
                print(f"[JuiceVault Voice Notification] {message}")
            except Exception as exc:
                print(f"[JuiceVault Voice] Failed sending notification: {exc}")

        def cleanup(self):
            self._active = False
            if hasattr(self, "_worker_task") and not self._worker_task.done():
                self._worker_task.cancel()
            _active_sinks.pop(self.guild_id, None)


def attach_voice_command_sink(cog, guild):
    """Attach VoiceCommandAudioSink to the active voice client if supported and enabled."""
    if not VOICE_RECV_AVAILABLE or not SPEECH_RECOGNITION_AVAILABLE:
        print(f"[JuiceVault Voice] Cannot attach voice sink in {getattr(guild, 'name', 'unknown')}: missing discord-ext-voice-recv or SpeechRecognition")
        return
    if not guild or not guild.voice_client:
        return
    voice = guild.voice_client

    # Check if voice client supports listening
    if not hasattr(voice, "listen") or not hasattr(voice, "is_listening"):
        print(f"[JuiceVault Voice] VoiceClient in {guild.name} does not support listen() (current type: {type(voice).__name__})")
        return

    # Check if already listening
    if voice.is_listening() and guild.id in _active_sinks:
        return

    sink = VoiceCommandAudioSink(cog.bot, cog, guild.id)
    _active_sinks[guild.id] = sink
    try:
        voice.listen(sink)
        print(f"[JuiceVault Voice Recognition] 🟢 ACTIVE: Listening for voice commands in '{guild.name}' (Wake Word: 'Garmin')...")
    except Exception as exc:
        print(f"[JuiceVault Voice Recognition] Failed attaching sink in '{guild.name}': {exc}")
