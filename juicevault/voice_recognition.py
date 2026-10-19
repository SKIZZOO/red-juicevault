"""
JuiceVault Voice Recognition Engine
===================================
Provides in-Discord voice channel microphone command detection (Skip, Next, Pause,
Play, Previous, Shuffle, Favorite) with graceful fallback when optional audio
receiving packages are not installed on the host.
"""

import asyncio
import logging
import re
import time

log = logging.getLogger("red.juicevault.voice_recognition")

# 1. Check optional dependencies: discord-ext-voice-recv and SpeechRecognition
VOICE_RECV_AVAILABLE = False
try:
    from discord.ext import voice_recv
    VOICE_RECV_AVAILABLE = True
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
            val = await cog.config.guild_from_id(guild_id).get_raw("voice_commands_enabled", default=False)
            _guild_voice_cmd_enabled[guild_id] = bool(val)
            return bool(val)
        except Exception:
            pass
    return False


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
                text = await loop.run_in_executor(None, self._recognize_speech_blocking, pcm_bytes)
            except Exception:
                return

            if not text:
                return

            clean = text.lower().strip()
            guild = self.bot.get_guild(self.guild_id)
            user = guild.get_member(user_id) if guild else None
            user_name = user.display_name if user else f"User {user_id}"
            now = time.monotonic()

            # Check for Garmin Wake Word: "garmin", "hey garmin", "ok garmin", "garmen", etc.
            wake_match = re.search(r'\b(?:hey\s+|ok\s+|hei\s+)?(?:garmin|garmen|garmon|garmyn|carmin)\b', clean, re.IGNORECASE)

            if wake_match:
                cmd_part = clean[wake_match.end():].strip().lstrip(",.:;!?- ")
                if not cmd_part:
                    # User only said "Garmin" -> wake up for 8 seconds
                    self._wake_windows[user_id] = now + 8.0
                    log.info(f"[JuiceVault Voice] Wake word 'Garmin' activated by {user_name}. Waiting for command...")
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
                    # Utterance did NOT contain Garmin and not in wake window -> ignore
                    log.debug(f"[JuiceVault Voice] Ignored utterance from {user_name} (no 'Garmin' wake word): '{clean}'")
                    return

            log.info(f"[JuiceVault Voice Command] {user_name} -> Garmin command: '{clean_cmd}' (full: '{clean}')")

            # 1. SEEK / DERULARE 10s
            if any(w in clean_cmd for w in ("inainte 10", "forward 10", "skip 10s", "10 secunde inainte")):
                if hasattr(self.cog, "_request_seek"):
                    await self.cog._request_seek(self.guild_id, delta=10.0)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Forward +10s ⏩")
                    return
            elif any(w in clean_cmd for w in ("inapoi 10", "back 10", "rewind 10", "10 secunde inapoi")):
                if hasattr(self.cog, "_request_seek"):
                    await self.cog._request_seek(self.guild_id, delta=-10.0)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Rewind -10s ⏪")
                    return

            # 2. SKIP / NEXT
            if any(w in clean_cmd for w in ("skip", "next", "urmatoarea", "sari", "urmatorul", "treci peste", "sară", "schimba", "schimb-o", "alta piesa", "alta melodie")):
                if any(w in clean_cmd for w in ("10", "ten", "zece")):
                    await self.cog._request_skip(self.guild_id, 10)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Skipped 10 tracks! ⏩")
                else:
                    await self.cog._request_skip(self.guild_id, 1)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Skipped track! ⏭️")

            # 3. PREVIOUS / BACK
            elif any(w in clean_cmd for w in ("previous", "prev", "back", "inapoi", "anterioara", "piesa anterioara", "melodia anterioara")):
                hist = self.cog.history.get(self.guild_id, [])
                if hist:
                    prev_t = hist.pop()
                    self.cog.manual_queues.setdefault(self.guild_id, []).insert(0, prev_t)
                    await self.cog._request_skip(self.guild_id, 1)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Previous track! ⏮️")

            # 4. PAUSE
            elif any(w in clean_cmd for w in ("pause", "pauza", "stop", "opreste", "taci")):
                voice = guild.voice_client if guild else None
                if voice and voice.is_playing():
                    voice.pause()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Paused! ⏸️")

            # 5. RESUME / PLAY
            elif any(w in clean_cmd for w in ("resume", "play", "continua", "porneste", "da drumul", "baga")):
                voice = guild.voice_client if guild else None
                if voice and voice.is_paused():
                    voice.resume()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Resumed playback! ▶️")

            # 6. SHUFFLE
            elif any(w in clean_cmd for w in ("shuffle", "amesteca", "mix")):
                q = self.cog.queues.get(self.guild_id, [])
                if q:
                    import random
                    random.shuffle(q)
                    self.cog._cleanup_prefetch(self.guild_id)
                    self.cog._trigger_next_prefetch(self.guild_id)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Shuffled queue! 🔀")

            # 7. FAVORITE
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
                        await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Added to favorites! ❤️")

        def _recognize_speech_blocking(self, pcm_bytes):
            """Synchronously pass PCM audio data to Google Speech Recognition."""
            audio_data = sr.AudioData(pcm_bytes, 48000, 2)
            first_cand = None
            for lang in ("ro-RO", "en-US"):
                try:
                    res = self._recognizer.recognize_google(audio_data, language=lang)
                    if res:
                        lower_res = res.lower()
                        if any(k in lower_res for k in ("garmin", "garmen", "garmon", "skip", "next", "pause", "play", "urmatoarea", "sari")):
                            return res
                        if first_cand is None:
                            first_cand = res
                except Exception:
                    pass
            return first_cand

        async def _notify(self, guild, message):
            """Send a subtle feedback message in the active voice or text channel."""
            if not guild:
                return
            try:
                channel_id = await self.cog.config.guild(guild).channel_id()
                target_channel = guild.get_channel(channel_id)
                if not target_channel and guild.text_channels:
                    target_channel = guild.text_channels[0]
                if target_channel:
                    await target_channel.send(message, delete_after=12)
            except Exception:
                pass

        def cleanup(self):
            self._active = False
            if hasattr(self, "_worker_task") and not self._worker_task.done():
                self._worker_task.cancel()
            _active_sinks.pop(self.guild_id, None)
            super().cleanup()


def attach_voice_command_sink(cog, guild):
    """Attach VoiceCommandAudioSink to the active voice client if supported and enabled."""
    if not VOICE_RECV_AVAILABLE or not SPEECH_RECOGNITION_AVAILABLE:
        return
    if not guild or not guild.voice_client:
        return
    voice = guild.voice_client

    # Check if voice client supports listening
    if not hasattr(voice, "listen") or not hasattr(voice, "is_listening"):
        return

    # Check if already listening
    if voice.is_listening() and guild.id in _active_sinks:
        return

    sink = VoiceCommandAudioSink(cog.bot, cog, guild.id)
    _active_sinks[guild.id] = sink
    try:
        voice.listen(sink)
        log.info(f"[JuiceVault Voice Recognition] Listening for voice commands in {guild.name}...")
    except Exception as exc:
        log.warning(f"[JuiceVault Voice Recognition] Failed attaching sink: {exc}")
