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

import discord

log = logging.getLogger("red.juicevault.voice_recognition")

# Silence noisy RTCP telemetry and decoder key crypto errors from discord-ext-voice-recv
logging.getLogger("discord.ext.voice_recv.reader").setLevel(logging.CRITICAL)
logging.getLogger("discord.ext.voice_recv").setLevel(logging.CRITICAL)


def _normalize_speech(text: str) -> str:
    """Normalize text by stripping diacritics and extra punctuation for robust command matching."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return stripped.lower().strip()


def _levenshtein(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return _levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]


def _resolve_artist_phonetics(text: str) -> str:
    """Normalize common phonetic misrecognitions of artist names from Romanian and English STT."""
    if not text:
        return ""
    # 1. Yeat variations: 'yet', 'ieat', 'iet', 'yeet', 'yit', 'iat'
    resolved = re.sub(r'\b(?:yet|ieat|iet|yeet|yit|iat)\b', 'yeat', text, flags=re.I)
    # Standalone 'eat' or 'it' in music query context
    if resolved.strip().lower() in {"eat", "it"}:
        resolved = "yeat"
    # 2. Carti / Playboi Carti variations: 'karti', 'cardi'
    resolved = re.sub(r'\b(?:playboy\s+carti|playboy\s+karti|playboi\s+karti)\b', 'playboi carti', resolved, flags=re.I)
    resolved = re.sub(r'\b(?:karti)\b', 'carti', resolved, flags=re.I)
    # 3. Drake variations
    resolved = re.sub(r'\b(?:dreik|drek|drec)\b', 'drake', resolved, flags=re.I)
    # 4. Travis Scott variations
    resolved = re.sub(r'\b(?:trevis\s+scott|travis\s+scot|trevis\s+scot)\b', 'travis scott', resolved, flags=re.I)
    # 5. Juice WRLD variations
    resolved = re.sub(r'\b(?:gius\s+wrld|gius\s+world|juice\s+world|jus\s+wrld)\b', 'juice wrld', resolved, flags=re.I)
    return resolved.strip()


def _clean_music_query(query: str) -> str:
    """Cleanly extract song or artist search query by stripping YouTube indicators,
    command verbs ('bagă', 'pune', 'play'), filler words ('muzică', 'piesa', 'melodia', 'ceva de la'),
    and resolving phonetic artist aliases (e.g. 'yet' -> 'yeat')."""
    if not query:
        return ""
    q = _normalize_speech(query)

    # 1. Remove wake words if present at start
    q = re.sub(r'^(?:hey\s+|ok\s+|hei\s+|ba\s+|bai\s+|alo\s+|yo\s+)?(?:garmin|garmen|garmon|garmyn|carmin|carmen|darmin|german|barmin)\s*', '', q, flags=re.I).strip()

    # 2. Remove YouTube references anywhere in the query
    q = re.sub(r'\b(?:pe|de\s+pe|dupa|din|on|from)\s+(?:youtube|yt)\b', '', q, flags=re.I)
    q = re.sub(r'\b(?:youtube|yt)\b', '', q, flags=re.I)
    q = re.sub(r'\s+', ' ', q).strip()

    # 3. Strip conversational request prefixes iteratively
    prefix_patterns = [
        r'^(?:te\s+rog|please|hai|ba|bai|alo|yo|si\s+tu|si\s+mie)\s+',
        r'^(?:vreau\s+sa\s+ascult|as\s+vrea\s+sa\s+ascult|da-i\s+drumul\s+la|dai\s+drumul\s+la|da\s+drumul\s+la|da-i\s+play\s+la|dai\s+play\s+la|da\s+play\s+la)\s+',
        r'^(?:cauta-mi|cautami|cauta|baga-mi|bagami|baga|pune-mi|punemi|pune|canta-mi|cantami|canta|gaseste-mi|gaseste|search|play|find|listen\s+to|put\s+on)\s+',
        r'^(?:niste|some|ceva\s+de\s+la|ceva\s+cu|ceva|o\s+piesa\s+cu|o\s+piesa\s+de\s+la|o\s+melodie\s+cu|o\s+melodie\s+de\s+la|a\s+song\s+by|a\s+track\s+by)\s+',
        r'^(?:muzica\s+cu|muzica\s+de\s+la|muzica|piesa\s+cu|piesa\s+de\s+la|piesa|melodia\s+cu|melodia\s+de\s+la|melodia|melodie|track|song|music)\s+',
        r'^(?:cu|de\s+la|de|by|from|la|numit|numita|called)\s+',
    ]
    changed = True
    passes = 0
    while changed and passes < 6:
        changed = False
        passes += 1
        for pat in prefix_patterns:
            new_q = re.sub(pat, '', q, flags=re.I).strip()
            if new_q != q:
                q = new_q
                changed = True

    # 4. Strip trailing fillers like "te rog", "please", "frate", "man", "bro"
    q = re.sub(r'\s+(?:te\s+rog|please|frate|man|bro)$', '', q, flags=re.I).strip()
    q = q.strip(" ,.:;!?-")

    # 5. Resolve artist phonetics
    q = _resolve_artist_phonetics(q)

    return q.strip()




_MULTI_WORD_WAKE_REGEX = re.compile(
    r'^(?:hey\s+|ok\s+|okay\s+|hei\s+|alo\s+|yo\s+)?(?:god\s+i\'?m\s+in|god\s+im\s+in|egger\s+man|eggar\s+man|eggerman|edgar\s+man|eger\s+man|eger\s+men|egr\s+man|egr\s+men|elgar\s+man|elgar\s+men|got\s+him\s+in|i\s+got\s+him\s+in|a\s+garden|the\s+garden|call\s+man|call\s+men)\b',
    re.IGNORECASE
)

_SINGLE_WORD_WAKE_REGEX = re.compile(
    r'\b(?:hey\s+|ok\s+|okay\s+|hei\s+|ba\s+|bai\s+|alo\s+|yo\s+|bre\s+|ma\s+|fa\s+|auzi\s+|zi\s+|spune\s+|hi\s+|hello\s+|e\s+|a\s+|the\s+|de\s+)?(?:garmin|garmen|garmon|garmyn|garminn|garmy|garminu|garminul|garmini|carmin|carmen|carmina|carman|carme|carmyn|darmin|damin|darmon|barmin|karmin|karmen|jarmin|parmin|garden|gardon|gardi|gardin|gaming|germain|german|germane|elgar|edgar|eggar|egger|egr|eger|calmin|starmin|sharmin)\b',
    re.IGNORECASE
)

# In-memory adaptive learning caches
_learned_wake_words_cache = {}    # guild_id -> set of lowercase words
_learned_song_queries_cache = {}  # guild_id -> dict of {query: track_dict}
_user_preferred_languages = {}    # user_id -> "ro" | "en"

AFFIRMATIVE_WORDS = {
    "da", "dap", "mda", "aha", "ihi", "dai", "da-i",
    "yes", "yeah", "yep", "yup", "sure", "ok", "okay",
    "baga", "pune", "cauta", "canta", "play", "hai",
    "sigur", "categoric", "normal", "clar", "bine", "please",
    "search", "ahead"
}
AFFIRMATIVE_PHRASES = (
    "da", "yes", "yep", "yeah", "yup", "sure", "sigur", "baga-o", "baga o", "baga", "pune-o", "pune o", "pune",
    "cauta", "cauta-o", "cauta o", "hai", "da te rog", "te rog", "da frate", "da man", "of course", "play it",
    "go ahead", "da da", "fa-o", "fa o"
)
NEGATIVE_WORDS = {
    "nu", "nop", "nope", "nah", "no", "cancel", "anuleaza", "stop",
    "lasa", "niciun", "niciuna", "dont", "not", "nevermind", "pas"
}
NEGATIVE_PHRASES = (
    "nu", "no", "nope", "nah", "cancel", "anuleaza", "nu mai", "nu cauta", "las-o", "las o",
    "lasa", "nu vreau", "niciun caz", "nici gand", "don't", "stop", "nu da", "nu baga", "las-o balta"
)


def _match_wake_word(text: str, custom_words: set = None) -> tuple:
    """Permissive wake word detector returning (matched: bool, cmd_part: str, wake_word: str).
    Matches standard 'Garmin', Romanian salutations ('bă Garmin', 'hei Garmin'),
    misrecognized English STT phrases ('hey god i'm in', 'egger man', 'a garden', 'carmen'),
    learned custom words, and Levenshtein edit distance <= 2."""
    clean = _normalize_speech(text)
    if not clean:
        return False, "", ""

    # 1. Multi-word phonetic misrecognitions
    m = _MULTI_WORD_WAKE_REGEX.search(clean)
    if m:
        wake = m.group(0).strip()
        cmd = clean[m.end():].strip().lstrip(",.:;!?- ")
        return True, cmd, wake

    # 2. Single-word names with optional prefixes
    m = _SINGLE_WORD_WAKE_REGEX.search(clean)
    if m:
        wake = m.group(0).strip()
        cmd = clean[m.end():].strip().lstrip(",.:;!?- ")
        return True, cmd, wake

    # 3. Custom learned wake words for this guild
    if custom_words:
        for lw in sorted(custom_words, key=len, reverse=True):
            clean_lw = _normalize_speech(lw)
            if not clean_lw:
                continue
            idx = clean.find(clean_lw)
            if idx != -1:
                cmd = clean[idx + len(clean_lw):].strip().lstrip(",.:;!?- ")
                return True, cmd, clean_lw

    # 4. Levenshtein fuzzy distance matching on leading words (distance <= 2 to 'garmin')
    tokens = clean.split()
    if tokens:
        prefix_tokens = {"hey", "hei", "ok", "okay", "ba", "bai", "alo", "yo", "a", "the", "e", "de"}
        cand = tokens[0]
        rest_idx = 1
        if cand in prefix_tokens and len(tokens) > 1:
            cand = tokens[1]
            rest_idx = 2
        cand_clean = re.sub(r'[^a-z0-9]', '', cand)
        if 4 <= len(cand_clean) <= 8:
            if _levenshtein(cand_clean, "garmin") <= 2 or _levenshtein(cand_clean, "carmen") <= 1:
                return True, " ".join(tokens[rest_idx:]).strip(), cand_clean

    return False, "", ""


async def get_learned_wake_words(cog, guild_id: int) -> set:
    if guild_id in _learned_wake_words_cache:
        return _learned_wake_words_cache[guild_id]
    words = set()
    if hasattr(cog, "config"):
        try:
            val = await cog.config.guild_from_id(guild_id).get_raw("learned_wake_words", default=[])
            words = set(str(w).lower() for w in val if w)
        except Exception:
            pass
    _learned_wake_words_cache[guild_id] = words
    return words


async def add_learned_wake_word(cog, guild_id: int, word: str):
    clean_w = _normalize_speech(word)
    if not clean_w or len(clean_w) < 3:
        return
    words = await get_learned_wake_words(cog, guild_id)
    if clean_w not in words:
        words.add(clean_w)
        _learned_wake_words_cache[guild_id] = words
        if hasattr(cog, "config"):
            try:
                await cog.config.guild_from_id(guild_id).set_raw("learned_wake_words", value=list(words))
            except Exception:
                pass


async def get_learned_song_queries(cog, guild_id: int) -> dict:
    if guild_id in _learned_song_queries_cache:
        return _learned_song_queries_cache[guild_id]
    queries = {}
    if hasattr(cog, "config"):
        try:
            val = await cog.config.guild_from_id(guild_id).get_raw("learned_song_queries", default={})
            if isinstance(val, dict):
                queries = val
        except Exception:
            pass
    _learned_song_queries_cache[guild_id] = queries
    return queries


async def add_learned_song_query(cog, guild_id: int, query: str, track: dict):
    clean_q = _normalize_speech(query)
    if not clean_q or not track:
        return
    queries = await get_learned_song_queries(cog, guild_id)
    # Store minimal track metadata so it can be re-played immediately
    save_track = {
        "id": track.get("id"),
        "title": track.get("title") or clean_q,
        "artist": track.get("artist") or "YouTube",
        "url": track.get("url") or track.get("webpage_url"),
        "_webpage_url": track.get("_webpage_url") or track.get("url"),
        "_external": True,
        "_source": track.get("_source", "YouTube"),
        "length": track.get("length", "—"),
    }
    queries[clean_q] = save_track
    _learned_song_queries_cache[guild_id] = queries
    if hasattr(cog, "config"):
        try:
            await cog.config.guild_from_id(guild_id).set_raw("learned_song_queries", value=queries)
        except Exception:
            pass


_LISTENING_BEEP_PATH = None
_UNDERSTOOD_BEEP_PATH = None
_ERROR_BEEP_PATH = None
_CHIME_FILE_PATH = None


def _generate_beep_wav(path: str, notes: list) -> str:
    """Helper to synthesize short stereo 48kHz WAV beeps from a list of (freq, duration, volume)."""
    try:
        sample_rate = 48000
        frames = bytearray()
        for freq, duration, vol in notes:
            total_samples = int(sample_rate * duration)
            for i in range(total_samples):
                t = i / sample_rate
                # Smooth attack (first 10ms) and exponential decay
                env = (1.0 - math.cos(math.pi * min(1.0, i / (sample_rate * 0.010)))) * 0.5
                decay = (1.0 - (i / total_samples)) ** 1.4
                val = int(env * decay * vol * math.sin(2 * math.pi * freq * t))
                val = max(-32767, min(32767, val))
                frames.extend(struct.pack('<hh', val, val))
        with wave.open(path, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(frames)
        return path
    except Exception as exc:
        log.warning(f"[JuiceVault Voice] Failed generating beep '{path}': {exc}")
        return ""


def _get_listening_beep_wav_path() -> str:
    """Ascending bright chime (D5 -> A5) indicating Garmin is actively listening."""
    global _LISTENING_BEEP_PATH
    if _LISTENING_BEEP_PATH and os.path.isfile(_LISTENING_BEEP_PATH):
        return _LISTENING_BEEP_PATH
    path = os.path.join(tempfile.gettempdir(), "juicevault_beep_listening.wav")
    # D5 (587.33Hz) for 0.08s, A5 (880.00Hz) for 0.14s
    res = _generate_beep_wav(path, [(587.33, 0.08, 17000), (880.00, 0.14, 20000)])
    if res:
        _LISTENING_BEEP_PATH = res
    return res


def _get_understood_beep_wav_path() -> str:
    """Bright snappy affirmative double chime (G5 -> C6) indicating Garmin understood."""
    global _UNDERSTOOD_BEEP_PATH
    if _UNDERSTOOD_BEEP_PATH and os.path.isfile(_UNDERSTOOD_BEEP_PATH):
        return _UNDERSTOOD_BEEP_PATH
    path = os.path.join(tempfile.gettempdir(), "juicevault_beep_understood.wav")
    # G5 (783.99Hz) for 0.06s, C6 (1046.50Hz) for 0.14s
    res = _generate_beep_wav(path, [(783.99, 0.06, 17000), (1046.50, 0.14, 21000)])
    if res:
        _UNDERSTOOD_BEEP_PATH = res
    return res


def _get_error_beep_wav_path() -> str:
    """Descending gentle low double tone (A4 -> E4) indicating Garmin didn't understand / error."""
    global _ERROR_BEEP_PATH
    if _ERROR_BEEP_PATH and os.path.isfile(_ERROR_BEEP_PATH):
        return _ERROR_BEEP_PATH
    path = os.path.join(tempfile.gettempdir(), "juicevault_beep_error.wav")
    # A4 (440.00Hz) for 0.08s, E4 (329.63Hz) for 0.15s
    res = _generate_beep_wav(path, [(440.00, 0.08, 17000), (329.63, 0.15, 19000)])
    if res:
        _ERROR_BEEP_PATH = res
    return res


def _get_siri_chime_wav_path() -> str:
    """Alias for listening chime."""
    return _get_listening_beep_wav_path()


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
    if target_len % 4 != 0:
        target_len += 4 - (target_len % 4)
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


class DuckingAudioSource(discord.AudioSource):
    """AudioSource wrapper that ducks the main music volume to 18% (0.18) whenever
    an overlay audio stream (Garmin TTS or Siri chime) is playing."""

    def __init__(self, main_source):
        super().__init__()
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
            self.target_volume = 0.18  # Duck music down to 18% volume ("ducks the sounds a bit")

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
            self.current_volume = min(self.target_volume, self.current_volume + 0.08)
        elif self.current_volume > self.target_volume:
            self.current_volume = max(self.target_volume, self.current_volume - 0.12)

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


async def play_beep_sound(guild, sound_type: str = "understood", action_coro=None):
    """Play an acoustic feedback tone in the voice channel:
    - 'listening': ascending tone indicating Garmin is actively listening
    - 'understood': bright positive tone indicating Garmin understood the command
    - 'error': descending gentle tone indicating Garmin didn't understand / error
    Ducks active music to 18% volume without interrupting playback."""
    voice = getattr(guild, "voice_client", None)
    if not voice or not voice.is_connected():
        if action_coro is not None and asyncio.iscoroutine(action_coro):
            await action_coro
        return

    if sound_type == "listening":
        beep_path = _get_listening_beep_wav_path()
        duration = 0.24
    elif sound_type == "error":
        beep_path = _get_error_beep_wav_path()
        duration = 0.26
    else:  # "understood"
        beep_path = _get_understood_beep_wav_path()
        duration = 0.22

    if beep_path and os.path.isfile(beep_path):
        try:
            import discord
            exe = _get_ffmpeg_exe()
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
                # Play beep over ducked music (18% volume) without stopping music!
                beep_source = discord.FFmpegPCMAudio(beep_path, executable=exe)
                mixer.set_overlay(beep_source)
                await asyncio.sleep(duration)
            elif not voice.is_playing():
                voice.play(discord.FFmpegPCMAudio(beep_path, executable=exe))
                await asyncio.sleep(duration)
        except Exception as exc:
            print(f"[JuiceVault Beep] Error ({sound_type}): {exc}")

    if action_coro is not None:
        if asyncio.iscoroutine(action_coro):
            await action_coro


async def play_chime_and_proceed(guild, action_coro=None, interrupt_playback: bool = False, sound_type: str = "understood"):
    """Play assistant feedback chime in voice channel and execute the command action."""
    await play_beep_sound(guild, sound_type=sound_type, action_coro=action_coro)


async def speak_in_voice(guild, text: str, lang: str = "ro"):
    """Fetch Google Translate TTS and speak out loud directly in the voice channel.
    If music is actively playing, ducks music to 18% volume and speaks over it."""
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
            # Music is actively playing -> DUCK music to 18% and speak over it without stopping the song!
            print(f"[JuiceVault Voice TTS] 🔊 Speaking over ducked music (18%) in '{guild.name}': \"{clean_tts}\" ({lang})")
            overlay = discord.FFmpegPCMAudio(path, executable=exe)
            mixer.set_overlay(overlay)
            duration = max(1.5, min(8.0, len(clean_tts) * 0.085 + 0.4))
            for _ in range(int(duration / 0.1)):
                if not mixer.is_overlay_playing():
                    break
                await asyncio.sleep(0.1)
        elif not voice.is_playing():
            # No music playing -> play directly on voice client
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
            self._active_session_uid = None     # Current user who initiated Garmin interaction
            self._active_session_expires = 0.0  # Monotonic deadline for the active interaction
            self._active = True
            self._recognizer = sr.Recognizer()
            self._worker_task = asyncio.create_task(self._process_silence_loop())

        def _lock_session(self, user_id: int, duration: float = 25.0):
            """Lock Garmin's interaction strictly to user_id. Discards audio from all other speakers."""
            now = time.monotonic()
            self._active_session_uid = user_id
            self._active_session_expires = now + duration
            # Purge any audio buffers from other users captured during the initiation phrase
            for other_uid in list(self._buffers.keys()):
                if other_uid != user_id:
                    self._buffers.pop(other_uid, None)
                    self._last_speech.pop(other_uid, None)

        def _unlock_session(self):
            """Release session lock so any user in the voice channel can issue commands to Garmin."""
            self._active_session_uid = None
            self._active_session_expires = 0.0

        def _is_locked_to_other(self, user_id: int) -> bool:
            """Return True if Garmin is actively engaged in a session with another user."""
            if self._active_session_uid is None:
                return False
            if time.monotonic() >= self._active_session_expires:
                self._active_session_uid = None
                self._active_session_expires = 0.0
                return False
            return self._active_session_uid != user_id

        def wants_opus(self) -> bool:
            return False  # Decode Opus packets to 48kHz 16-bit stereo PCM

        def write(self, user, data):
            if not self._active or not user or getattr(user, "bot", False):
                return
            now = time.monotonic()
            uid = user.id

            # If Garmin is currently locked to another speaker, drop incoming audio completely!
            if self._is_locked_to_other(uid):
                return

            pending = getattr(self.cog, "_pending_yt_voice", {}).get(self.guild_id)
            is_pending_user = bool(pending and pending.get("user_id") == uid and time.time() < pending.get("expires", 0.0))

            # Cooldown per user after executing a command (1.0 second); NEVER drop audio if bot is waiting for an answer!
            if not is_pending_user and (now - self._cooldowns.get(uid, 0.0) < 1.0):
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
            """Monitors when a user finishes speaking and dispatches audio to STT."""
            try:
                while self._active:
                    await asyncio.sleep(0.18)
                    now = time.monotonic()
                    uids = list(self._last_speech.keys())
                    pending = getattr(self.cog, "_pending_yt_voice", {}).get(self.guild_id)
                    for uid in uids:
                        if self._is_locked_to_other(uid):
                            self._buffers.pop(uid, None)
                            self._last_speech.pop(uid, None)
                            continue

                        last = self._last_speech.get(uid, 0.0)
                        is_pending = bool(pending and pending.get("user_id") == uid and time.time() < pending.get("expires", 0.0))
                        # End-of-utterance: 0.38s silence for pending answers ("da"/"nu"), 0.55s for standard commands
                        silence_needed = 0.38 if is_pending else 0.55
                        if now - last >= silence_needed:
                            buf = self._buffers.pop(uid, bytearray())
                            self._last_speech.pop(uid, None)
                            # Capture short single-syllable responses like "da", "nu", "yes", "no"
                            min_bytes = 12_000 if is_pending else 16_000
                            if len(buf) >= min_bytes:
                                if not is_pending:
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
            self._unlock_session()

        async def _search_and_play_youtube(self, guild, query: str, user_name: str, lang: str = "ro"):
            """Search YouTube for query, speak confirmation, and begin immediate playback."""
            if not query:
                self._unlock_session()
                return
            clean_q = _clean_music_query(query)
            if not clean_q:
                self._unlock_session()
                return
            wait_speech = f"Caut pe YouTube {clean_q}" if lang == "ro" else f"Searching YouTube for {clean_q}"
            await play_beep_sound(guild, "understood")
            await speak_in_voice(guild, wait_speech, lang=lang)
            await self._notify(guild, f"🔍 **[Garmin]** {user_name}: Caut *\"{clean_q}\"* pe YouTube... ⏳" if lang == "ro" else f"🔍 **[Garmin]** {user_name}: Searching YouTube for *\"{clean_q}\"*... ⏳")

            try:
                from .external_search_patch import _extract_search
                info = await asyncio.to_thread(_extract_search, clean_q)
                yt_track = None
                if info:
                    if info.get("_is_playlist") or "entries" in info:
                        entries = info.get("entries") or []
                        yt_track = entries[0] if entries else None
                    elif not yt_track and (info.get("url") or info.get("title")):
                        yt_track = info

                    if yt_track:
                        await add_learned_song_query(self.cog, self.guild_id, clean_q, yt_track)
                        await play_beep_sound(guild, "understood")
                        await self._play_track_now(guild, yt_track)
                        title = yt_track.get("title") or clean_q
                        await self._notify(guild, f"🎥 **[Garmin]** Redare de pe YouTube: **{title}** 🎶" if lang == "ro" else f"🎥 **[Garmin]** Playing from YouTube: **{title}** 🎶")
                        return

                fail_msg = f"Nu am găsit piesa {clean_q} pe YouTube." if lang == "ro" else f"Could not find {clean_q} on YouTube."
                await play_beep_sound(guild, "error")
                await speak_in_voice(guild, fail_msg, lang=lang)
                await self._notify(guild, f"❌ **[Garmin]** {fail_msg}")
            except Exception as exc:
                print(f"[Garmin YouTube] Error searching '{clean_q}': {exc}")
                fail_msg = f"Nu am găsit rezultate pe YouTube pentru {clean_q}." if lang == "ro" else f"No YouTube results found for {clean_q}."
                await play_beep_sound(guild, "error")
                await speak_in_voice(guild, fail_msg, lang=lang)
                await self._notify(guild, f"❌ **[Garmin]** {fail_msg}")
            finally:
                self._unlock_session()


        async def _transcribe_and_dispatch(self, user_id, pcm_bytes):
            if self._is_locked_to_other(user_id):
                print(f"[JuiceVault Voice] Ignored utterance from user {user_id} - Garmin is currently focused on {self._active_session_uid}")
                return

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
            _user_preferred_languages[user_id] = user_lang
            is_ro = (user_lang == "ro")

            # Check if this utterance is answering a pending YouTube question
            pending = getattr(self.cog, "_pending_yt_voice", {}).get(self.guild_id)
            if pending and time.time() < pending.get("expires", 0.0):
                pending_uid = pending.get("user_id")
                # REQUIREMENT: Must come from the SAME person who initiated the command!
                if pending_uid and user_id != pending_uid:
                    # Spoken by someone else in the voice channel
                    tokens = set(re.findall(r'[a-z0-9]+', clean))
                    custom_words = await get_learned_wake_words(self.cog, self.guild_id)
                    matched_wake_other, _, _ = _match_wake_word(clean, custom_words)
                    if matched_wake_other and (tokens & (AFFIRMATIVE_WORDS | NEGATIVE_WORDS)):
                        initiator = pending.get("user_name", "persoana care a cerut piesa")
                        lang_p = pending.get("lang", user_lang)
                        await self._notify(
                            guild,
                            f"⚠️ **[Garmin]** {user_name}, aștept răspunsul de la **{initiator}**."
                            if lang_p == "ro" else
                            f"⚠️ **[Garmin]** {user_name}, I am waiting for **{initiator}** to answer."
                        )
                    return
                else:
                    # Utterance is from the SAME user who asked
                    pending_lang = pending.get("lang", user_lang)
                    tokens = set(re.findall(r'[a-z0-9]+', clean))
                    if pending.get("awaiting_title"):
                        is_neg = bool(tokens & NEGATIVE_WORDS) or clean in NEGATIVE_PHRASES
                        if is_neg:
                            self.cog._pending_yt_voice.pop(self.guild_id, None)
                            self._wake_windows.pop(user_id, None)
                            self._unlock_session()
                            await play_beep_sound(guild, "error")
                            cancel_msg = "🚫 **[Garmin]** Căutare anulată." if pending_lang == "ro" else "🚫 **[Garmin]** Search cancelled."
                            await speak_in_voice(guild, "Comandă anulată." if pending_lang == "ro" else "Cancelled.", lang=pending_lang)
                            await self._notify(guild, cancel_msg)
                            return
                        clean_title = _clean_music_query(clean)
                        self.cog._pending_yt_voice.pop(self.guild_id, None)
                        self._wake_windows.pop(user_id, None)
                        self._lock_session(user_id, duration=35.0)
                        await play_beep_sound(guild, "understood")
                        await self._search_and_play_youtube(guild, clean_title or clean, user_name, lang=pending_lang)
                        return

                    # Check NEGATIVE tokens FIRST before affirmative to prevent false positives
                    is_negative = bool(tokens & NEGATIVE_WORDS) or clean in NEGATIVE_PHRASES
                    if is_negative:
                        self.cog._pending_yt_voice.pop(self.guild_id, None)
                        self._wake_windows.pop(user_id, None)
                        self._unlock_session()
                        await play_beep_sound(guild, "error")
                        cancel_msg = "🚫 **[Garmin]** Căutare anulată." if pending_lang == "ro" else "🚫 **[Garmin]** Search cancelled."
                        await speak_in_voice(guild, "Comandă anulată." if pending_lang == "ro" else "Cancelled.", lang=pending_lang)
                        await self._notify(guild, cancel_msg)
                        return

                    is_affirmative = bool(tokens & AFFIRMATIVE_WORDS) or clean in AFFIRMATIVE_PHRASES or "youtube" in clean or "yt" in clean
                    if is_affirmative:
                        self.cog._pending_yt_voice.pop(self.guild_id, None)
                        self._wake_windows.pop(user_id, None)
                        self._lock_session(user_id, duration=35.0)
                        await play_beep_sound(guild, "understood")
                        target_q = pending["query"]
                        await self._search_and_play_youtube(guild, target_q, user_name, lang=pending_lang)
                        return

            # Check for Garmin Wake Word using permissive matcher + custom learned words + fuzzy Levenshtein
            custom_words = await get_learned_wake_words(self.cog, self.guild_id)
            matched_wake, cmd_part, wake_word = _match_wake_word(clean, custom_words)

            if matched_wake:
                self._lock_session(user_id, duration=20.0)
                # If matched a fuzzy variation, automatically learn it for future zero-latency matching!
                if wake_word and len(wake_word) >= 3 and wake_word not in custom_words:
                    asyncio.create_task(add_learned_wake_word(self.cog, self.guild_id, wake_word))

                if not cmd_part:
                    # User only said "Garmin" (or "Hey Garmin", "Bă Garmin", etc.) -> wake window 12s + listening beep + voice response
                    self._wake_windows[user_id] = now + 12.0
                    self._lock_session(user_id, duration=15.0)
                    print(f"[JuiceVault Voice] Wake word '{wake_word}' activated by {user_name}. Waiting for command...")
                    await play_beep_sound(guild, "listening")
                    greeting = f"Da, {user_name}? Ascult..." if is_ro else f"Yes, {user_name}? I'm listening..."
                    await speak_in_voice(guild, greeting, lang=user_lang)
                    await self._notify(guild, f"🎤 **[Garmin]** {greeting} 🟢")
                    return
                clean_cmd = cmd_part
                self._wake_windows.pop(user_id, None)
            else:
                # Check if within active wake window from a previous greeting
                if now < self._wake_windows.get(user_id, 0.0):
                    self._lock_session(user_id, duration=20.0)
                    clean_cmd = clean
                    self._wake_windows.pop(user_id, None)
                else:
                    # Utterance did NOT contain Garmin wake word and not in wake window -> ignore
                    print(f"[JuiceVault Voice] Ignored utterance from {user_name} (no 'Garmin' wake word): '{clean}'")
                    return

            print(f"[JuiceVault Voice Command] {user_name} -> Garmin command: '{clean_cmd}' (full: '{clean}') [lang: {user_lang}]")

            # PRECEDENCE 1: PREVIOUS / BACK (must evaluate before generic search!)
            # Handles: "previous", "previous song", "preview song", "inapoi", "dinainte", "piesa dinainte", "anterioara", etc.
            if re.search(r'\b(?:previous|prev|back|inapoi|dinainte|anterioara|piesa dinainte|melodia dinainte|piesa anterioara|melodia anterioara|preview|preview song|the previous|the last song|piesa trecuta)\b', clean_cmd, re.I):
                hist = self.cog.history.get(self.guild_id, [])
                if hist:
                    prev_t = hist.pop()
                    await play_chime_and_proceed(guild)
                    await self._play_track_now(guild, prev_t)
                    self._unlock_session()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Previous track! ⏮️")
                else:
                    await play_beep_sound(guild, "error")
                    self._unlock_session()
                    no_prev_msg = "Nu există o piesă anterioară în istoric." if is_ro else "There is no previous track in history."
                    await speak_in_voice(guild, no_prev_msg, lang=user_lang)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: {no_prev_msg}")
                return

            # PRECEDENCE 2: SKIP / NEXT
            # Handles: "skip", "skip this song", "next", "urmatoarea", "sari", "schimba", "da-i skip", etc.
            if re.search(r'\b(?:skip|next|urmatoarea|sari|treci peste|schimba|schimb-o|alta piesa|alta melodie|da-i skip|dai skip|skip this|next song)\b', clean_cmd, re.I):
                if any(w in clean_cmd for w in ("10", "ten", "zece")):
                    await play_chime_and_proceed(guild, self.cog._request_skip(self.guild_id, 10))
                    self._unlock_session()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Skipped 10 tracks! ⏩")
                else:
                    await play_chime_and_proceed(guild, self.cog._request_skip(self.guild_id, 1))
                    self._unlock_session()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Skipped track! ⏭️")
                return

            # PRECEDENCE 3: SHUFFLE / RANDOM
            # Handles: "shuffle", "amesteca", "random", "play random song", "la intamplare", etc.
            if re.search(r'\b(?:shuffle|amesteca|random|mix|la intamplare|random song|piesa la intamplare)\b', clean_cmd, re.I):
                q = self.cog.queues.get(self.guild_id, [])
                if q:
                    import random
                    random.shuffle(q)
                    self.cog._cleanup_prefetch(self.guild_id)
                    self.cog._trigger_next_prefetch(self.guild_id)
                    await play_chime_and_proceed(guild)
                    self._unlock_session()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Shuffled queue! 🔀")
                else:
                    self._unlock_session()
                return

            # PRECEDENCE 4: PAUSE / STOP
            # Handles: "pause", "pauza", "stop", "opreste", "taci", "liniste", etc.
            if re.search(r'\b(?:pause|pauza|stop|opreste|opreste-te|taci|taci din gura|liniste|shut up|hold)\b', clean_cmd, re.I):
                voice = guild.voice_client if guild else None
                if voice and voice.is_playing():
                    await play_chime_and_proceed(guild)
                    if hasattr(self.cog, "pause_playback"):
                        self.cog.pause_playback(self.guild_id)
                    else:
                        voice.pause()
                    self._unlock_session()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Paused! ⏸️")
                else:
                    self._unlock_session()
                return

            # PRECEDENCE 5: LEAVE / DISCONNECT
            # Handles: "leave", "pleaca", "iesi", "deconecteaza", "disconnect", "exit", etc.
            if re.search(r'\b(?:leave|pleaca|iesi|deconecteaza|deconecteaza-te|disconnect|exit|go away|bye)\b', clean_cmd, re.I):
                await play_chime_and_proceed(guild)
                await self.cog.config.guild(guild).enabled.set(False)
                await self.cog._stop(self.guild_id)
                self._unlock_session()
                await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Deconectat din voice! 👋" if is_ro else f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Left voice channel! 👋")
                return

            # PRECEDENCE 6: RESUME / PLAY (bare play command)
            # Handles: "play", "resume", "continua", "porneste", "da drumul"
            if clean_cmd.strip() in {"play", "resume", "continua", "porneste", "da drumul", "baga"} or clean_cmd.strip() == "play":
                voice = guild.voice_client if guild else None
                if voice and voice.is_paused():
                    await play_chime_and_proceed(guild)
                    if hasattr(self.cog, "resume_playback"):
                        self.cog.resume_playback(self.guild_id)
                    else:
                        voice.resume()
                    self._unlock_session()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Resumed playback! ▶️")
                    return
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
                        self._unlock_session()
                        await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Pornesc redarea! ▶️" if is_ro else f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Started playback! ▶️")
                    else:
                        self._unlock_session()
                    return

            # PRECEDENCE 7: SEEK / DERULARE 10s
            if any(w in clean_cmd for w in ("inainte 10", "forward 10", "skip 10s", "10 secunde inainte")):
                if hasattr(self.cog, "_request_seek"):
                    await play_chime_and_proceed(guild, self.cog._request_seek(self.guild_id, delta=10.0))
                    self._unlock_session()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Forward +10s ⏩")
                    return
            elif any(w in clean_cmd for w in ("inapoi 10", "back 10", "rewind 10", "10 secunde inapoi")):
                if hasattr(self.cog, "_request_seek"):
                    await play_chime_and_proceed(guild, self.cog._request_seek(self.guild_id, delta=-10.0))
                    self._unlock_session()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Rewind -10s ⏪")
                    return

            # PRECEDENCE 8: FAVORITE
            if any(w in clean_cmd for w in ("favorite", "fav", "like", "place", "iubeste", "favorit", "apreciaza")):
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
                        self._unlock_session()
                        await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Added to favorites! ❤️")
                        return
                self._unlock_session()
                return

            # PRECEDENCE 9: DIRECT YOUTUBE SEARCH & PLAY
            # Handles: "cauta pe youtube yeat", "baga dupa youtube drake", "play drake on youtube", "baga muzica de pe youtube yeat", etc.
            if "youtube" in clean_cmd or " yt" in clean_cmd or clean_cmd.startswith("yt "):
                yt_q = _clean_music_query(clean_cmd)

                if not yt_q:
                    # User only said "Garmin bagă după YouTube" without a song title
                    self._lock_session(user_id, duration=25.0)
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
                    await speak_in_voice(guild, prompt_speech, lang=user_lang)
                    await play_beep_sound(guild, "listening")
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: {prompt_speech} ⏳")
                    return

                print(f"[JuiceVault Voice] Direct YouTube request from {user_name}: '{yt_q}'")
                self._lock_session(user_id, duration=35.0)
                await self._search_and_play_youtube(guild, yt_q, user_name, lang=user_lang)
                return

            # PRECEDENCE 10: GENERIC SONG SEARCH & PLAY
            # Handles: "cauta drake", "cauta yeat", "baga 6ix9ine", "play robbery", or direct artist name "Garmin Yeat"
            play_match = re.match(
                r'^(?:canta|pune|baga|play|asculta|cauta|gaseste|search|reda|da-i play la|dai play la|da play la|da-i drumul la|dai drumul la)\s+(?:piesa|melodia|melodie|track|song)?\s*(?:cu|de\s+la|by)?\s*(.+)$',
                clean_cmd,
                re.IGNORECASE
            )
            q = ""
            if play_match:
                q = play_match.group(1).strip()
            elif len(clean_cmd.split()) <= 6:
                # Direct name utterance, e.g. user says "Garmin Yeat" or "Garmin Drake - Gods Plan"
                q = clean_cmd.strip()

            if q:
                try:
                    clean_q = _clean_music_query(q)
                    if clean_q:
                        # 1. Check learned song query aliases for this guild
                        learned_queries = await get_learned_song_queries(self.cog, self.guild_id)
                        if clean_q in learned_queries:
                            learned_track = learned_queries[clean_q]
                            print(f"[JuiceVault Voice] Playing learned track mapping for '{clean_q}': {learned_track.get('title')}")
                            await play_chime_and_proceed(guild)
                            await self._play_track_now(guild, learned_track)
                            self._unlock_session()
                            track_name = learned_track.get("title") or clean_q
                            await self._notify(guild, f"🧠 **[Garmin]** Am reținut preferința ta: **{track_name}** 🎶" if is_ro else f"🧠 **[Garmin]** Playing learned song: **{track_name}** 🎶")
                            return

                        # 2. Search JuiceVault internal archive
                        tracks = await self.cog.fetch_tracks()
                        candidates = [item for item in tracks if clean_q in _normalize_speech(self.cog._search_text(item))]
                        track = candidates[0] if candidates else None
                        if track:
                            await play_chime_and_proceed(guild)
                            await self._play_track_now(guild, track)
                            self._unlock_session()
                            track_name = self.cog._track_text(track)
                            await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Redau: **{track_name}** 🎶" if is_ro else f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Playing: **{track_name}** 🎶")
                            return
                        else:
                            # 3. Not found in JuiceVault archive -> propose YouTube fallback!
                            # Music is ducked to 18% while Garmin asks; music NEVER stops!
                            print(f"[JuiceVault Voice] Track '{clean_q}' not found in archive -> Proposing YouTube fallback")
                            self._lock_session(user_id, duration=45.0)
                            if not hasattr(self.cog, "_pending_yt_voice"):
                                self.cog._pending_yt_voice = {}
                            self.cog._pending_yt_voice[self.guild_id] = {
                                "user_id": user_id,
                                "query": clean_q,
                                "lang": user_lang,
                                "expires": time.time() + 45.0,
                                "user_name": user_name,
                            }
                            # Extend wake window so the user can just answer "Da" without repeating "Garmin"
                            self._wake_windows[user_id] = now + 45.0

                            if is_ro:
                                ask_speech = f"Piesa {clean_q} nu se află în JuiceVault. Vrei să o caut pe YouTube?"
                                ask_msg = f"🎤 **[Garmin]** {user_name}: Piesa *\"{clean_q}\"* nu se află în JuiceVault. Vrei să o caut și să o redau de pe **YouTube**? *(Zi **„Garmin, da”** sau scrie **da**)*"
                            else:
                                ask_speech = f"Track {clean_q} was not found in JuiceVault. Would you like me to search on YouTube?"
                                ask_msg = f"🎤 **[Garmin]** {user_name}: Track *\"{clean_q}\"* was not found in the JuiceVault archive. Would you like me to play it from **YouTube**? *(Say **\"Garmin, yes\"** or type **yes**)*"

                            await speak_in_voice(guild, ask_speech, lang=user_lang)
                            await play_beep_sound(guild, "listening")
                            await self._notify(guild, ask_msg)
                            return
                except Exception as e:
                    log.warning(f"[Garmin Voice Search] Error searching: {e}")

            # Feedback when recognized speech was addressed to Garmin but didn't match known command
            await play_beep_sound(guild, "error")
            self._unlock_session()
            await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Comandă nerecunoscută.")

        def _recognize_speech_blocking(self, pcm_bytes):
            """Convert Discord 48kHz stereo PCM to 16kHz mono PCM, then recognize with Google.
            Queries both ro-RO and en-US and intelligently selects the best candidate based on
            wake-word match, music intent keywords, and utterance confidence."""
            try:
                a = array.array('h')
                a.frombytes(pcm_bytes)
                # Discord sends 48kHz 16-bit stereo (2 channels interleaved).
                # Downsample 3x to 16kHz mono taking every 3rd sample: index [0::6]!
                mono_16k = a[0::6].tobytes()
            except Exception as e:
                print(f"[JuiceVault Voice] Audio conversion error: {e}")
                return None, "ro-RO"

            if not mono_16k or len(mono_16k) < 2000:
                return None, "ro-RO"

            audio_data = sr.AudioData(mono_16k, 16000, 2)
            candidates = []
            custom_words = _learned_wake_words_cache.get(self.guild_id, set())

            control_words = {
                "skip", "next", "previous", "prev", "back", "pause", "stop", "resume",
                "play", "shuffle", "random", "repeat", "favorite", "like", "youtube", "yt",
                "urmatoarea", "sari", "schimba", "inapoi", "dinainte", "anterioara",
                "pauza", "opreste", "taci", "continua", "porneste", "amesteca", "cauta",
                "baga", "pune", "canta", "da", "nu", "lasa", "anuleaza",
                "yes", "yeah", "yep", "yup", "sure", "ok", "okay", "nah", "nope", "dap", "mda",
                "yeat", "yet", "ieat", "yeet", "drake", "carti", "karti", "travis", "breathe",
                "muzica", "melodia", "melodie", "piesa", "track", "song", "music"
            }

            for lang in ("ro-RO", "en-US"):
                try:
                    res = self._recognizer.recognize_google(audio_data, language=lang)
                    if res:
                        print(f"[JuiceVault Voice] Google STT recognized ({lang}): '{res}'")
                        clean = _normalize_speech(res)
                        score = 0
                        matched_wake, _, _ = _match_wake_word(clean, custom_words)
                        if matched_wake:
                            score += 150
                        tokens = set(re.findall(r'[a-z0-9]+', clean))
                        score += len(tokens & control_words) * 30
                        score += min(len(clean), 25)
                        candidates.append((score, res, lang))
                except sr.UnknownValueError:
                    pass
                except sr.RequestError as exc:
                    print(f"[JuiceVault Voice] Google STT network/API error: {exc}")
                except Exception as exc:
                    print(f"[JuiceVault Voice] Google STT exception: {type(exc).__name__}: {exc}")

            if not candidates:
                return None, "ro-RO"

            # Pick highest scoring candidate
            candidates.sort(key=lambda x: x[0], reverse=True)
            best = candidates[0]
            return best[1], best[2]

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
            self._unlock_session()
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
