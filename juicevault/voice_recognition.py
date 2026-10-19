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
import time
import unicodedata
import wave

log = logging.getLogger("red.juicevault.voice_recognition")


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


async def play_chime_and_proceed(guild, action_coro=None, interrupt_playback: bool = True):
    """Play the Siri assistant chime in voice channel, then execute the command action."""
    voice = getattr(guild, "voice_client", None)
    chime_path = _get_siri_chime_wav_path()
    if voice and voice.is_connected() and chime_path and os.path.isfile(chime_path):
        try:
            import discord
            if not voice.is_playing() or interrupt_playback:
                if voice.is_playing() or voice.is_paused():
                    voice.stop()
                voice.play(discord.FFmpegPCMAudio(chime_path))
                await asyncio.sleep(0.32)
        except Exception:
            pass
    if action_coro is not None:
        if asyncio.iscoroutine(action_coro):
            await action_coro

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

            # Check if this utterance is answering a pending YouTube question
            pending = getattr(self.cog, "_pending_yt_voice", {}).get(self.guild_id)
            if pending and time.time() < pending.get("expires", 0.0):
                is_affirmative = any(w in clean for w in ("da", "yes", "sure", "sigur", "baga", "pune-o", "canta-o", "play it", "ok", "yep", "bine"))
                is_negative = any(w in clean for w in ("nu", "no", "cancel", "anuleaza", "stop", "lasa", "nevermind"))
                if is_affirmative:
                    self.cog._pending_yt_voice.pop(self.guild_id, None)
                    target_q = pending["query"]
                    is_ro_p = pending.get("lang") == "ro"
                    wait_msg = f"🔍 **[Garmin]** Caut *\"{target_q}\"* pe YouTube... ⏳" if is_ro_p else f"🔍 **[Garmin]** Searching YouTube for *\"{target_q}\"*... ⏳"
                    await self._notify(guild, wait_msg)
                    try:
                        from .external_search_patch import _extract_search
                        results = await asyncio.to_thread(_extract_search, target_q)
                        if results:
                            yt_track = results[0]
                            self.cog.manual_queues.setdefault(self.guild_id, []).insert(0, yt_track)
                            await play_chime_and_proceed(guild, self.cog._request_skip(self.guild_id, 1))
                            res_msg = f"🎥 **[Garmin]** Redare de pe YouTube: **{yt_track.get('title', target_q)}** 🎶" if is_ro_p else f"🎥 **[Garmin]** Playing from YouTube: **{yt_track.get('title', target_q)}** 🎶"
                            await self._notify(guild, res_msg)
                        else:
                            fail_msg = f"❌ **[Garmin]** Nu am găsit rezultate pe YouTube pentru *\"{target_q}\"*." if is_ro_p else f"❌ **[Garmin]** No YouTube results found for *\"{target_q}\"*."
                            await self._notify(guild, fail_msg)
                    except Exception as exc:
                        print(f"[Garmin YouTube Voice] Error: {exc}")
                        await self._notify(guild, f"❌ YouTube search error: `{exc}`")
                    return
                elif is_negative:
                    self.cog._pending_yt_voice.pop(self.guild_id, None)
                    cancel_msg = "🚫 **[Garmin]** Comandă anulată." if pending.get("lang") == "ro" else "🚫 **[Garmin]** Cancelled."
                    await self._notify(guild, cancel_msg)
                    return

            # Check for Garmin Wake Word: "garmin", "ba garmin", "hey garmin", "ok garmin", "carmen", "darmin", etc.
            wake_match = re.search(r'\b(?:hey\s+|ok\s+|hei\s+|ba\s+|bai\s+|alo\s+|yo\s+)?(?:garmin|garmen|garmon|garmyn|carmin|carmen|darmin|german|barmin)\b', clean, re.IGNORECASE)

            if wake_match:
                cmd_part = clean[wake_match.end():].strip().lstrip(",.:;!?- ")
                if not cmd_part:
                    # User only said "Garmin" -> wake up for 8 seconds and ring Siri chime!
                    self._wake_windows[user_id] = now + 8.0
                    print(f"[JuiceVault Voice] Wake word 'Garmin' activated by {user_name}. Waiting for command...")
                    await play_chime_and_proceed(guild)
                    await self._notify(guild, f"🎤 **[Garmin]** Da, {user_name}? Ascult... (Listening...) 🟢")
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

            print(f"[JuiceVault Voice Command] {user_name} -> Garmin command: '{clean_cmd}' (full: '{clean}')")
            is_ro = (detected_lang == "ro-RO") or any(w in clean for w in ("canta", "pune", "baga", "da", "ba", "bai", "piesa", "melodia", "urmatoarea", "sari", "schimba"))

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

            # 2. SEARCH & PLAY SONG (handles "canta robbery", "baga piesa robbery", "da-i play la robbery", "play fire", etc.)
            play_match = re.match(
                r'^(?:canta|pune|baga|play|asculta|da-i play la|dai play la|da play la|da-i drumul la|dai drumul la)\s+(?:piesa|melodia|melodie|track|song)?\s*(?:cu|de\s+la|by)?\s*(.+)$',
                clean_cmd,
                re.IGNORECASE
            )
            if play_match:
                q = play_match.group(1).strip()
                if q:
                    try:
                        tracks = await self.cog.fetch_tracks()
                        candidates = [item for item in tracks if q in _normalize_speech(self.cog._search_text(item))]
                        track = candidates[0] if candidates else None
                        if track:
                            self.cog.manual_queues.setdefault(self.guild_id, []).insert(0, track)
                            await play_chime_and_proceed(guild, self.cog._request_skip(self.guild_id, 1))
                            track_name = self.cog._track_text(track)
                            await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Playing: **{track_name}** 🎶")
                            return
                        else:
                            # Not found in JuiceVault archive -> propose YouTube playback in user's language
                            if not hasattr(self.cog, "_pending_yt_voice"):
                                self.cog._pending_yt_voice = {}
                            self.cog._pending_yt_voice[self.guild_id] = {
                                "user_id": user_id,
                                "query": q,
                                "lang": "ro" if is_ro else "en",
                                "expires": time.time() + 35.0,
                                "user_name": user_name,
                            }
                            if is_ro:
                                ask_msg = f"🎤 **[Garmin]** {user_name}: Piesa *\"{q}\"* nu se află în arhiva JuiceVault. Vrei să o caut și să o redau de pe **YouTube**? *(Zi **„Garmin, da”** sau scrie **da**)*"
                            else:
                                ask_msg = f"🎤 **[Garmin]** {user_name}: Track *\"{q}\"* was not found in the JuiceVault archive. Would you like me to play it from **YouTube**? *(Say **\"Garmin, yes\"** or type **yes**)*"
                            await self._notify(guild, ask_msg)
                            return
                    except Exception as e:
                        log.warning(f"[Garmin Voice Search] Error searching: {e}")

            # 3. SKIP / NEXT (handles "skip", "next", "da-i skip", "dai skip", "urmatoarea", "sari", etc.)
            if any(w in clean_cmd for w in ("skip", "next", "urmatoarea", "sari", "urmatorul", "treci peste", "schimba", "schimb-o", "alta piesa", "alta melodie", "da-i skip", "dai skip", "treci")):
                if any(w in clean_cmd for w in ("10", "ten", "zece")):
                    await play_chime_and_proceed(guild, self.cog._request_skip(self.guild_id, 10))
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Skipped 10 tracks! ⏩")
                else:
                    await play_chime_and_proceed(guild, self.cog._request_skip(self.guild_id, 1))
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Skipped track! ⏭️")
                return

            # 4. PREVIOUS / BACK
            elif any(w in clean_cmd for w in ("previous", "prev", "back", "inapoi", "anterioara", "piesa anterioara", "melodia anterioara")):
                hist = self.cog.history.get(self.guild_id, [])
                if hist:
                    prev_t = hist.pop()
                    self.cog.manual_queues.setdefault(self.guild_id, []).insert(0, prev_t)
                    await play_chime_and_proceed(guild, self.cog._request_skip(self.guild_id, 1))
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Previous track! ⏮️")
                return

            # 5. PAUSE
            elif any(w in clean_cmd for w in ("pause", "pauza", "stop", "opreste", "taci")):
                voice = guild.voice_client if guild else None
                if voice and voice.is_playing():
                    voice.pause()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Paused! ⏸️")
                return

            # 6. RESUME / PLAY
            elif any(w in clean_cmd for w in ("resume", "play", "continua", "porneste", "da drumul", "baga")):
                voice = guild.voice_client if guild else None
                if voice and voice.is_paused():
                    voice.resume()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Resumed playback! ▶️")
                return

            # 7. SHUFFLE
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

            # 8. FAVORITE
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
            """Send a subtle feedback message in the active voice or text channel."""
            if not guild:
                return
            try:
                target_channel = None
                voice = guild.voice_client
                # 1. Prefer voice channel text chat (built-in Discord VC chat)
                if voice and voice.channel and hasattr(voice.channel, "send"):
                    target_channel = voice.channel
                # 2. Configured text channel fallback
                if not target_channel:
                    channel_id = await self.cog.config.guild(guild).channel_id()
                    target_channel = guild.get_channel(channel_id)
                # 3. Default text channel fallback
                if not target_channel and guild.text_channels:
                    target_channel = guild.text_channels[0]
                if target_channel:
                    await target_channel.send(message, delete_after=12)
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
