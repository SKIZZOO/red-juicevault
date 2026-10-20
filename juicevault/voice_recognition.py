"""
JuiceVault Voice Recognition Engine
===================================
Provides in-Discord voice channel microphone command detection (Skip, Next, Pause,
Play, Previous, Shuffle, Favorite) with graceful fallback when optional audio
receiving packages are not installed on the host.
"""

import array
import asyncio
import concurrent.futures
import logging
import io
import math
import os
import re
import struct
import tempfile
import threading
import time
import unicodedata
import warnings
import wave

# Suppress Python 3.11/3.12/3.13 deprecation warnings from legacy audio libraries like speech_recognition/aifc
warnings.filterwarnings("ignore", category=DeprecationWarning, module=r".*speech_recognition.*")
warnings.filterwarnings("ignore", message=r".*aifc.*", category=DeprecationWarning)

import discord

try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False

try:
    import edge_tts
    HAVE_EDGE_TTS = True
except ImportError:
    edge_tts = None
    HAVE_EDGE_TTS = False

log = logging.getLogger("red.juicevault.voice_recognition")

# High-concurrency thread pool for STT, audio downsampling, and parallel API queries to utilize all available CPU cores
_VOICE_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=min(32, max(8, (os.cpu_count() or 4) * 4)),
    thread_name_prefix="JuiceVault-Voice"
)

# Silence noisy RTCP telemetry and decoder key crypto errors from discord-ext-voice-recv
logging.getLogger("discord.ext.voice_recv.reader").setLevel(logging.CRITICAL)
logging.getLogger("discord.ext.voice_recv").setLevel(logging.CRITICAL)


# Guild voice persona cache: guild_id -> "anime" | "mommy" | "natural"
_guild_persona_cache = {}


async def get_guild_persona(cog, guild_id: int) -> str:
    """Retrieve the voice persona for this guild ('anime', 'mommy', or 'natural')."""
    if guild_id in _guild_persona_cache:
        return _guild_persona_cache[guild_id]
    persona = "anime"
    if hasattr(cog, "config"):
        try:
            val = await cog.config.guild_from_id(guild_id).get_raw("voice_persona", default="anime")
            if val in {"anime", "mommy", "natural"}:
                persona = val
        except Exception:
            pass
    _guild_persona_cache[guild_id] = persona
    return persona


async def set_guild_persona(cog, guild_id: int, persona: str):
    """Set the voice persona for this guild ('anime', 'mommy', or 'natural')."""
    if persona not in {"anime", "mommy", "natural"}:
        persona = "anime"
    _guild_persona_cache[guild_id] = persona
    if hasattr(cog, "config"):
        try:
            await cog.config.guild_from_id(guild_id).set_raw("voice_persona", value=persona)
        except Exception:
            pass


def _resolve_command_phonetics(text: str) -> str:
    """Normalize frequent phonetic misrecognitions for Garmin wake words and control commands."""
    if not text:
        return ""
    t = text

    # Wake word phonetics for "ok garmin" / "okay garmin":
    t = re.sub(r'\b(?:oak|o\s*k|o\.k\.|okay|okey|okei|oh|hope|old|all|ok)\s+(?:garmin|garmen|garmon|garmyn|carmin|carmen|garden|darmin|barmin|garment|armin|darling)\b', 'ok garmin', t, flags=re.I)
    # Wake word phonetics for "hey garmin":
    t = re.sub(r'\b(?:hey|hay|hei|he|ay|hi|hello|yo)\s+(?:garmin|garmen|garmon|garmyn|carmin|carmen|garden|darmin|barmin|garment|armin|darling)\b', 'hey garmin', t, flags=re.I)

    # Wake word misrecognitions from Romanian "bă Garmin" / "Garmin":
    # "beggar man", "bag armin", "bad garmin", "by garmin", "big armin", "back garmin", "barman"
    t = re.sub(r'\b(?:beggar\s+man|bag\s+armin|bad\s+garmin|by\s+garmin|big\s+armin|back\s+garmin|barman)\b', 'ba garmin', t, flags=re.I)
    t = re.sub(r'\b(?:garment|garments|garmon|garmend|garnet)\b', 'garmin', t, flags=re.I)
    t = re.sub(r'\b(?:ba|bai)\s+(?:armin|armen|arman)\b', 'ba garmin', t, flags=re.I)

    # Romanian "dă skip" / "dă-i skip" phonetic English STT mappings:
    # "the escape" -> "da skip"
    # "the scape" -> "da skip"
    # "they skip" -> "dai skip"
    # "the skip" -> "da skip"
    # "day skip" -> "dai skip"
    # "they scape" -> "dai skip"
    # "they skep" -> "dai skip"
    # "the skep" -> "da skip"
    # "the scale" -> "da skip"
    # "the skate" -> "da skip"
    t = re.sub(r'\b(?:the\s+escape|the\s+scape|they\s+scape|they\s+skep|the\s+skep|the\s+skate|they\s+skate)\b', 'da skip', t, flags=re.I)
    t = re.sub(r'\b(?:they\s+skip|day\s+skip)\b', 'dai skip', t, flags=re.I)
    t = re.sub(r'\bthe\s+skip\b', 'da skip', t, flags=re.I)

    return t


def _normalize_speech(text: str) -> str:
    """Normalize text by stripping diacritics and extra punctuation for robust command matching."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFD", text)
    stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    cleaned = stripped.lower().strip()
    return _resolve_command_phonetics(cleaned)


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


_KNOWN_EXTERNAL_ARTISTS_REGEX = re.compile(
    r'\b(?:yeat|carti|playboi\s+carti|travis\s+scott|drake|quavo|ken\s+carson|destroy\s+lonely|'
    r'gunna|young\s+thug|metro\s+boomin|future|trippie\s+redd|don\s+toliver|chief\s+keef|'
    r'21\s+savage|xxxtentacion|ski\s+mask|kodak\s+black|lil\s+yachty|nle\s+choppa|central\s+cee|'
    r'offset|takeoff|roddy\s+ricch|polo\s+g|dababy|nettspend|osamason|tory\s+lanez|lil\s+durk|'
    r'asap\s+rocky|post\s+malone|kendrick\s+lamar|kanye\s+west|lil\s+uzi\s+vert|lil\s+uzi|the\s+weeknd|'
    r'eminem|lil\s+baby|lil\s+wayne|lil\s+peep|mac\s+miller|pop\s+smoke|jack\s+harlow)\b',
    re.I
)


def _resolve_artist_phonetics(text: str) -> str:
    """Normalize common phonetic misrecognitions of artist names and song titles from Romanian and English STT."""
    if not text:
        return ""
    resolved = text

    # 1. Quavo: 'cuavo', 'cu avo', 'cu aveau', 'cu abu', 'cu alb', 'coavo', 'cuevo', 'quave', 'clavo', 'kwavo', 'kwa vo', 'quao', 'cuoavo', 'cu abo'
    resolved = re.sub(r'\b(?:cu\s+avo|cuavo|cu\s+aveau|cu\s+abu|cu\s+alb|coavo|cuevo|quave|clavo|kwavo|kwa\s+vo|quao|cuoavo|cu\s+abo)\b', 'quavo', resolved, flags=re.I)

    # 2. Song & Title phonetic normalization (e.g. 'Money So Big' variations from Romanian STT)
    # 'mani so big', 'mani sau big', 'money so bic', 'money sau big', 'moneys so big', 'money is so big', 'mani so bic'
    resolved = re.sub(r'\b(?:mani|money|manii)\s+(?:so|sau)\s+(?:big|bic|be|b)\b', 'money so big', resolved, flags=re.I)
    resolved = re.sub(r'\b(?:moneys|money\s+is)\s+so\s+big\b', 'money so big', resolved, flags=re.I)

    # 2B. Yeat variations: 'eat', 'it', 'hit', 'yet', 'ieat', 'iet', 'yeet', 'yit', 'iat'
    yeat_song_keywords = (
        r'(?:money\s+so\s+big|flawless|poppin|out\s+the\s+way|idgaf|breathe|get\s+busy|talk|turban|'
        r'sorry\s+bout\s+that|mad\s+bout\s+that|ya\s+ya|heavyweight|nun\s+id\s+change|bettr\s+off|'
        r'rav3\s+p4rty|if\s+we\s+being\s+real|monëy\s+so\s+big|g\s+wagon|2093|up\s+off\s+x|swerved\s+it)'
    )
    # If eat/it/hit/iet/yet/ieat/yeet/yit/iat is followed by a known Yeat song:
    resolved = re.sub(rf'\b(?:eat|it|hit|iet|yet|ieat|yeet|yit|iat)\s+({yeat_song_keywords})\b', r'yeat \1', resolved, flags=re.I)
    # If preceded by request verbs or artist prepositions: 'baga eat', 'pune it', 'de la eat', 'canta hit', 'play eat', 'by it'
    resolved = re.sub(r'\b(baga|pune|canta|cauta|play|de\s+la|by|asculta|reda|de|artistul|piesa\s+lui|ceva\s+de\s+la)\s+(?:eat|it|hit)\b', r'\1 yeat', resolved, flags=re.I)
    # Standalone non-English tokens that unambiguously mean Yeat:
    resolved = re.sub(r'\b(?:yet|ieat|iet|yeet|yit|iat)\b', 'yeat', resolved, flags=re.I)
    # At start of query followed by any title:
    resolved = re.sub(r'^(?:eat|it|hit)\s+(?=[a-z0-9])', 'yeat ', resolved, flags=re.I)
    if resolved.strip().lower() in {"eat", "it", "hit"}:
        resolved = "yeat"

    # 3. Playboi Carti / Carti: 'playboy carti', 'plei boi carti', 'pleiboi carti', 'karti', 'cardi'
    resolved = re.sub(r'\b(?:playboy\s+carti|plei\s*boi\s*carti|pleiboi\s+carti|playboy\s+karti|playboi\s+karti)\b', 'playboi carti', resolved, flags=re.I)
    resolved = re.sub(r'\b(?:karti)\b', 'carti', resolved, flags=re.I)

    # 4. Travis Scott: 'trevis scott', 'travis scot', 'trevis scot', 'trave scott', 'trevis cot', 'travis cot'
    resolved = re.sub(r'\b(?:trevis\s+scott|travis\s+scot|trevis\s+scot|trave\s+scott|trevis\s+cot|travis\s+cot)\b', 'travis scott', resolved, flags=re.I)

    # 5. Lil Uzi Vert / Uzi: 'lil use it', 'lil uzi', 'uzi vert', 'usi vert', 'lil uzzy'
    resolved = re.sub(r'\b(?:lil\s+use\s+it|lil\s+uzi\s+vert|lil\s+usi\s+vert|uzi\s+vert|usi\s+vert|lil\s+uzzy|uzy\s+vert)\b', 'lil uzi vert', resolved, flags=re.I)
    resolved = re.sub(r'\b(?:lil\s+usi|lil\s+use)\b', 'lil uzi', resolved, flags=re.I)

    # 6. Ken Carson: 'ken carsen', 'chian carson', 'chen carson', 'ken karsan', 'ken car son'
    resolved = re.sub(r'\b(?:ken\s+carsen|chian\s+carson|chen\s+carson|ken\s+karsan|ken\s+car\s+son|kian\s+carson)\b', 'ken carson', resolved, flags=re.I)

    # 7. Destroy Lonely: 'destroy loni', 'distroi lonli', 'distroi lonely', 'destroy lonli', 'destroi lonely'
    resolved = re.sub(r'\b(?:destroy\s+loni|distroi\s+lonli|distroi\s+lonely|destroy\s+lonli|destroi\s+lonely)\b', 'destroy lonely', resolved, flags=re.I)

    # 8. Gunna: 'gana', 'guna', 'gona'
    resolved = re.sub(r'\b(?:guna|gana|gona)\b', 'gunna', resolved, flags=re.I)

    # 9. Young Thug: 'iang tag', 'yang tag', 'young tag', 'young tog', 'yang tog', 'ion tag'
    resolved = re.sub(r'\b(?:iang\s+tag|yang\s+tag|young\s+tag|young\s+tog|yang\s+tog|ion\s+tag)\b', 'young thug', resolved, flags=re.I)

    # 10. Metro Boomin: 'metro bumin', 'metrou bumin', 'metro boomy', 'metro bumen'
    resolved = re.sub(r'\b(?:metro\s+bumin|metrou\s+bumin|metro\s+boomy|metro\s+bumen)\b', 'metro boomin', resolved, flags=re.I)

    # 11. Future: 'fiucer', 'fiutur', 'feuture'
    resolved = re.sub(r'\b(?:fiucer|fiutur|feuture)\b', 'future', resolved, flags=re.I)

    # 12. Trippie Redd: 'tripi red', 'trippy red', 'tripe red', 'tripi redd'
    resolved = re.sub(r'\b(?:tripi\s+red|trippy\s+red|tripe\s+red|tripi\s+redd)\b', 'trippie redd', resolved, flags=re.I)

    # 13. Don Toliver: 'dantoliver', 'dan toliver', 'dantolivar', 'don toliver'
    resolved = re.sub(r'\b(?:dantoliver|dan\s+toliver|dantolivar)\b', 'don toliver', resolved, flags=re.I)

    # 14. Chief Keef: 'cif chif', 'chief kif', 'cif kif', 'chef keef', 'chif chif'
    resolved = re.sub(r'\b(?:cif\s+chif|chief\s+kif|cif\s+kif|chef\s+keef|chif\s+chif)\b', 'chief keef', resolved, flags=re.I)

    # 15. 21 Savage: '21 savagi', 'twenty one savage', 'tueni uan sevegi', '21 sevegi', '21 sevidgi'
    resolved = re.sub(r'\b(?:21\s+savagi|twenty\s+one\s+savage|tueni\s+uan\s+sevegi|21\s+sevegi|21\s+sevidgi)\b', '21 savage', resolved, flags=re.I)

    # 16. Juice WRLD: 'gius wrld', 'gius world', 'jus wrld', 'juice world', 'gius uorld', 'gius vorld', 'djius wrld', 'djuice wrld', 'giusuorld', 'giuswrld'
    resolved = re.sub(r'\b(?:gius\s+uorld|gius\s+wrld|gius\s+world|jus\s+wrld|jus\s+world|djius\s+wrld|djius\s+world|djuice\s+wrld|juis\s+uorld|juis\s+wrld|juis\s+world|giusuorld|giuswrld|juice\s+world|gius\s+vorld)\b', 'juice wrld', resolved, flags=re.I)
    resolved = re.sub(r'\b(?:gius|djius|juis)\b', 'juice', resolved, flags=re.I)

    # 17. XXXTentacion: 'x tentacion', 'tentacion', 'tentasion', 'triplu x tentacion', 'xxx tentacion'
    resolved = re.sub(r'\b(?:triplu\s+x\s+tentacion|xxx\s+tentacion|ex\s+tentacion|x\s+tentacion|tentasion)\b', 'xxxtentacion', resolved, flags=re.I)

    # 18. Ski Mask The Slump God: 'schi masc', 'schi mesc', 'ski masc', 'schi mask'
    resolved = re.sub(r'\b(?:schi\s+masc|schi\s+mesc|ski\s+masc|schi\s+mask)\b', 'ski mask', resolved, flags=re.I)

    # 19. Kodak Black: 'codac blec', 'codac black', 'kodak blec'
    resolved = re.sub(r'\b(?:codac\s+blec|codac\s+black|kodak\s+blec)\b', 'kodak black', resolved, flags=re.I)

    # 20. Lil Yachty: 'lil iati', 'lil yachti', 'lil ioti', 'lil iahti'
    resolved = re.sub(r'\b(?:lil\s+iati|lil\s+yachti|lil\s+ioti|lil\s+iahti)\b', 'lil yachty', resolved, flags=re.I)

    # 21. NLE Choppa: 'enele copa', 'nle copa', 'nle ciopa', 'enele ciopa'
    resolved = re.sub(r'\b(?:enele\s+copa|nle\s+copa|nle\s+ciopa|enele\s+ciopa)\b', 'nle choppa', resolved, flags=re.I)

    # 22. Central Cee: 'central si', 'central ci', 'sentral si'
    resolved = re.sub(r'\b(?:central\s+si|central\s+ci|sentral\s+si)\b', 'central cee', resolved, flags=re.I)

    # 23. Offset: 'ofset', 'of set'
    resolved = re.sub(r'\b(?:ofset|of\s+set)\b', 'offset', resolved, flags=re.I)

    # 24. Takeoff: 'teic of', 'teicof', 'take of'
    resolved = re.sub(r'\b(?:teic\s+of|teicof|take\s+of)\b', 'takeoff', resolved, flags=re.I)

    # 25. Roddy Ricch: 'rodi rici', 'rodi rich', 'roddy rici'
    resolved = re.sub(r'\b(?:rodi\s+rici|rodi\s+rich|roddy\s+rici)\b', 'roddy ricch', resolved, flags=re.I)

    # 26. Polo G: 'polo gi', 'polo ji'
    resolved = re.sub(r'\b(?:polo\s+gi|polo\s+ji)\b', 'polo g', resolved, flags=re.I)

    # 27. DaBaby: 'da beibi', 'da baby'
    resolved = re.sub(r'\b(?:da\s+beibi|da\s+baby)\b', 'dababy', resolved, flags=re.I)

    # 28. Nettspend: 'net spend', 'netspend'
    resolved = re.sub(r'\b(?:net\s+spend|netspend)\b', 'nettspend', resolved, flags=re.I)

    # 29. Osamason: 'osama son', 'osama sonn'
    resolved = re.sub(r'\b(?:osama\s+son|osama\s+sonn)\b', 'osamason', resolved, flags=re.I)

    # 30. Tory Lanez: 'tori leinz', 'tori lanez', 'tory leinz'
    resolved = re.sub(r'\b(?:tori\s+leinz|tori\s+lanez|tory\s+leinz)\b', 'tory lanez', resolved, flags=re.I)

    # 31. Lil Durk: 'lil dărc', 'lil darc', 'lil derk', 'lil durck'
    resolved = re.sub(r'\b(?:lil\s+darc|lil\s+derk|lil\s+durck)\b', 'lil durk', resolved, flags=re.I)

    # 32. A$AP Rocky: 'esap rochi', 'asap rochi', 'a sap rocky', 'asap roki'
    resolved = re.sub(r'\b(?:esap\s+rochi|asap\s+rochi|a\s+sap\s+rocky|asap\s+roki)\b', 'asap rocky', resolved, flags=re.I)

    # 33. Drake: 'dreic', 'dreik', 'drek', 'drec'
    resolved = re.sub(r'\b(?:dreic|dreik|drek|drec)\b', 'drake', resolved, flags=re.I)

    # 34. Post Malone: 'post melon', 'post meilon', 'post malon'
    resolved = re.sub(r'\b(?:post\s+melon|post\s+meilon|post\s+malon)\b', 'post malone', resolved, flags=re.I)

    # 35. Kendrick Lamar: 'chendric lamar', 'kendric lamar', 'kendrik lamar'
    resolved = re.sub(r'\b(?:chendric\s+lamar|kendric\s+lamar|kendrik\s+lamar)\b', 'kendrick lamar', resolved, flags=re.I)

    # 36. Kanye West: 'canie vest', 'canie uest', 'kanie vest', 'kanie uest'
    resolved = re.sub(r'\b(?:canie\s+vest|canie\s+uest|kanie\s+vest|kanie\s+uest)\b', 'kanye west', resolved, flags=re.I)

    return resolved.strip()


def _clean_music_query(query: str) -> str:
    """Cleanly extract song or artist search query by stripping YouTube indicators,
    command verbs ('bagă', 'pune', 'play'), filler words ('muzică', 'piesa', 'melodia', 'ceva de la'),
    artist prepositions ('de la Juice WRLD', 'by Juice WRLD'),
    and resolving phonetic artist aliases (e.g. 'cu avo' -> 'quavo', 'yet' -> 'yeat')."""
    if not query:
        return ""
    q = _normalize_speech(query)

    # 1. Resolve artist phonetics FIRST (e.g. 'cu avo' -> 'quavo', 'gius uorld' -> 'juice wrld') BEFORE stripping prepositions!
    q = _resolve_artist_phonetics(q)

    # 2. Remove wake words if present at start
    q = re.sub(r'^(?:hey\s+|ok\s+|okay\s+|hi\s+|hello\s+|hei\s+|ba\s+|bai\s+|alo\s+|yo\s+)?(?:garmin|garmen|garmon|garmyn|carmin|carmen|darmin|german|barmin)\s*', '', q, flags=re.I).strip()

    # 3. Remove YouTube references anywhere in the query
    q = re.sub(r'\b(?:pe|de\s+pe|dupa|din|on|from)\s+(?:youtube|yt)\b', '', q, flags=re.I)
    q = re.sub(r'\b(?:youtube|yt)\b', '', q, flags=re.I)
    q = re.sub(r'\s+', ' ', q).strip()

    # 4. Strip conversational request prefixes iteratively
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

    # 5. Strip trailing fillers like "te rog", "please", "frate", "man", "bro"
    q = re.sub(r'\s+(?:te\s+rog|please|frate|man|bro)$', '', q, flags=re.I).strip()
    q = q.strip(" ,.:;!?-")

    # 6. Re-resolve artist phonetics once more in case stripped prefixes exposed them
    q = _resolve_artist_phonetics(q)

    # 7. Strip trailing & leading Juice WRLD artist specifiers (e.g. "robbery de la juice wrld" -> "robbery")
    # while preserving "juice wrld" if that was the entire query
    is_only_juice = bool(re.match(r'^(?:juice\s+wrld|juice\s+world|juice|gius\s+wrld|gius\s+uorld|jus\s+wrld|juicewrld)$', q.strip(), flags=re.I))
    if not is_only_juice:
        juice_trailing = r'\s+(?:de\s+la|by|de|cu|canta(?:ta)?\s+de)\s+(?:juice\s+wrld|juice\s+world|juice|gius\s+wrld|gius\s+uorld|jus\s+wrld|juicewrld)$'
        sub_q = re.sub(juice_trailing, '', q, flags=re.I).strip()
        if sub_q:
            q = sub_q
        juice_leading = r'^(?:juice\s+wrld|juice\s+world|juice|gius\s+wrld|gius\s+uorld|jus\s+wrld|juicewrld)\s*[-:]?\s+'
        sub_q = re.sub(juice_leading, '', q, flags=re.I).strip()
        if sub_q:
            q = sub_q

    # 8. Convert Romanian 'de la' / 'cantata de' before any other artist into clean spacing
    # e.g. "magnolia de la carti" -> "magnolia carti", "fein de la travis scott" -> "fein travis scott"
    q = re.sub(r'\s+(?:de\s+la|cantata\s+de)\s+', ' ', q, flags=re.I).strip()

    return q.strip()




_MULTI_WORD_WAKE_REGEX = re.compile(
    r'^(?:hey\s+|ok\s+|okay\s+|hei\s+|alo\s+|yo\s+|hi\s+|hello\s+)?(?:god\s+i\'?m\s+in|god\s+im\s+in|egger\s+man|eggar\s+man|eggerman|edgar\s+man|eger\s+man|eger\s+men|egr\s+man|egr\s+men|elgar\s+man|elgar\s+men|got\s+him\s+in|i\s+got\s+him\s+in|a\s+garden|the\s+garden|call\s+man|call\s+men)\b',
    re.IGNORECASE
)

_SINGLE_WORD_WAKE_REGEX = re.compile(
    r'\b(?:(?:hey|ok|okay|hei|ba|bai|alo|yo|bre|ma|fa|auzi|zi|spune|hi|hello|e|a|the|de)\s+){0,3}(?:garmin|garmen|garmon|garmyn|garminn|garmy|garminu|garminul|garmini|carmin|carmen|carmina|carman|carme|carmyn|darmin|damin|darmon|barmin|karmin|karmen|jarmin|parmin|garden|gardon|gardi|gardin|gaming|germain|german|germane|elgar|edgar|eggar|egger|egr|eger|calmin|starmin|sharmin|barman|beggar|garment|garments|armin|darling)\b',
    re.IGNORECASE
)

# In-memory adaptive learning caches
_learned_wake_words_cache = {}    # guild_id -> set of lowercase words
_learned_song_queries_cache = {}  # guild_id -> dict of {query: track_dict}
_user_preferred_languages = {}    # user_id -> "ro" | "en"

AFFIRMATIVE_WORDS = {
    "da", "dap", "mda", "aha", "ihi", "dai", "da-i", "dă",
    "yes", "yeah", "yep", "yup", "sure", "ok", "okay",
    "baga", "pune", "cauta", "canta", "play", "hai",
    "sigur", "categoric", "normal", "clar", "bine", "please",
    "search", "ahead", "bag-o", "bago", "bagao", "pune-o",
    "puneo", "pun-o", "cauta-o", "cautao", "fa-o", "fao",
    "ia-o", "ia", "merge", "exact", "corect",
    # Phonetic STT misrecognitions of short "da" / "yes" from Romanian speakers
    "the", "that", "duh", "dar", "de", "dada", "done", "does", "dust", "go"
}
AFFIRMATIVE_PHRASES = (
    "baga-o", "baga o", "pune-o", "pune o", "cauta-o", "cauta o",
    "da te rog", "te rog", "da frate", "da man", "of course", "play it",
    "go ahead", "da da", "fa-o", "fa o", "da baga", "da pune", "da cauta", "da bag-o", "da pune-o", "da caut-o",
    "da ma", "da ba", "da bro", "da normal", "da-i drumul", "dai drumul", "baga pe youtube", "pune pe youtube",
    "cauta pe youtube", "da pe youtube", "da o vreau", "da vreau", "yes please", "yes play"
)
NEGATIVE_WORDS = {
    "nu", "nop", "nope", "nah", "no", "cancel", "anuleaza", "stop",
    "lasa", "niciun", "niciuna", "dont", "not", "nevermind", "pas",
    "las-o", "laso", "opreste", "nimic", "nici",
    # Phonetic STT misrecognitions of short "nu" / "no"
    "new", "know", "now", "nuu"
}
NEGATIVE_PHRASES = (
    "nu mai", "nu cauta", "las-o", "las o", "nu vreau", "niciun caz", "nici gand",
    "don't", "nu da", "nu baga", "las-o balta", "nu te rog", "nu frate", "nu ma", "nu ba",
    "nu pune", "nu mersi", "mersi nu", "lasa asa"
)


def _find_best_archive_track(tracks, query: str, cog):
    """Intelligently match query against JuiceVault internal track archive.
    Supports exact titles, artist-stripped queries ('robbery de la juice wrld' -> 'robbery'),
    and token-based word matching with intelligent candidate scoring."""
    if not tracks or not query:
        return None
    clean_q = _normalize_speech(query).strip()
    if not clean_q:
        return None

    # Variants of query to try
    queries_to_try = [clean_q]
    q_no_juice = re.sub(r'\b(?:juice\s+wrld|juice\s+world|juice|gius\s+wrld|gius\s+uorld|jus\s+wrld|juicewrld)\b', '', clean_q, flags=re.I).strip()
    q_no_juice = re.sub(r'\s+', ' ', q_no_juice).strip()
    if q_no_juice and q_no_juice != clean_q and len(q_no_juice) >= 2:
        queries_to_try.append(q_no_juice)

    # 1. Substring matching
    matched = []
    for q_try in queries_to_try:
        found = [t for t in tracks if q_try in _normalize_speech(cog._search_text(t))]
        if found:
            matched = found
            break

    # 2. Token / word-level matching
    if not matched:
        for q_try in queries_to_try:
            tokens = [tok for tok in q_try.split() if tok not in {"de", "la", "by", "cu", "si", "and", "the", "a", "o", "un"} and len(tok) >= 2]
            if tokens:
                found = [t for t in tracks if all(tok in _normalize_speech(cog._search_text(t)) for tok in tokens)]
                if found:
                    matched = found
                    break

    if not matched:
        return None

    # 3. Score candidates to pick the best match
    def score_track(t):
        title = _normalize_speech(str(t.get("title") or t.get("name") or "")).strip()
        s = 0
        for target in queries_to_try:
            if title == target:
                s = max(s, 100)
            elif title.startswith(target):
                s = max(s, 60)
            elif target in title:
                s = max(s, 40)
            elif all(tok in title for tok in target.split() if len(tok) >= 2):
                s = max(s, 25)
        # Penalize acoustic/remix/slowed if user did not request it
        if any(w in title for w in ("remix", "acoustic", "slowed", "reverb", "snippet")) and not any(w in clean_q for w in ("remix", "acoustic", "slowed", "reverb", "snippet")):
            s -= 20
        return s

    matched.sort(key=score_track, reverse=True)
    return matched[0]


def _pcm16_to_wav_bytes(pcm_bytes: bytes, sample_rate: int = 16000, channels: int = 1) -> bytes:
    """Pack 16-bit PCM bytes into in-memory standard WAV container for Whisper/Groq API."""
    bio = io.BytesIO()
    with wave.open(bio, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_bytes)
    return bio.getvalue()


async def _get_groq_api_key(cog) -> str:
    """Retrieve Groq API key from environment, Red shared tokens, or cog config."""
    # 1. Environment variable
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key:
        return key

    # 2. In-memory cog attribute
    if hasattr(cog, "_groq_api_key") and cog._groq_api_key:
        return str(cog._groq_api_key).strip()

    # 3. Red shared API tokens: [p]set api groq api_key <key>
    if hasattr(cog, "bot") and hasattr(cog.bot, "get_shared_api_tokens"):
        try:
            tokens = await cog.bot.get_shared_api_tokens("groq")
            if tokens and tokens.get("api_key"):
                return tokens["api_key"].strip()
        except Exception:
            pass

    # 4. Cog global config
    if hasattr(cog, "config") and hasattr(cog.config, "groq_api_key"):
        try:
            cfg_key = await cog.config.groq_api_key()
            if cfg_key:
                return str(cfg_key).strip()
        except Exception:
            pass

    return ""


_LOCAL_WHISPER_MODEL = None
_LOCAL_WHISPER_TRIED = False


_last_groq_passive_time = 0.0


def _can_query_groq_passive() -> bool:
    """Rate-limit passive Groq STT fallback queries to max 1 query per 1.5 seconds to protect API quotas."""
    global _last_groq_passive_time
    now = time.monotonic()
    if now - _last_groq_passive_time >= 1.5:
        _last_groq_passive_time = now
        return True
    return False


def _calculate_rms(pcm_bytes: bytes) -> int:
    """Calculate Root Mean Square (RMS) audio energy level of 16-bit PCM bytes.
    Human speech is typically 600 - 15000+ RMS, while background room noise is < 400 RMS."""
    if not pcm_bytes:
        return 0
    try:
        import audioop
        return audioop.rms(pcm_bytes, 2)
    except Exception:
        pass
    if HAVE_NUMPY:
        try:
            arr = np.frombuffer(pcm_bytes, dtype=np.int16)
            if len(arr) == 0:
                return 0
            return int(np.sqrt(np.mean(arr.astype(np.float64) ** 2)))
        except Exception:
            pass
    try:
        count = len(pcm_bytes) // 2
        if count == 0:
            return 0
        shorts = struct.unpack(f"<{count}h", pcm_bytes[:count * 2])
        sum_sq = sum(s * s for s in shorts)
        return int(math.sqrt(sum_sq / count))
    except Exception:
        return 600


def _get_local_whisper_model():
    """Load local faster-whisper model on CPU using RAM if installed.
    Runs 100% offline with zero network latency and zero API rate limits."""
    global _LOCAL_WHISPER_MODEL, _LOCAL_WHISPER_TRIED
    if _LOCAL_WHISPER_MODEL is not None or _LOCAL_WHISPER_TRIED:
        return _LOCAL_WHISPER_MODEL
    _LOCAL_WHISPER_TRIED = True
    try:
        from faster_whisper import WhisperModel
        print("[JuiceVault Voice] Initializing local faster-whisper model ('tiny.en' on CPU / int8 / RAM)...")
        _LOCAL_WHISPER_MODEL = WhisperModel(
            "tiny.en",
            device="cpu",
            compute_type="int8",
            cpu_threads=min(4, max(1, (os.cpu_count() or 2) // 2)),
        )
        print("[JuiceVault Voice] ✅ Local faster-whisper ready on CPU / RAM!")
    except Exception as exc:
        log.debug(f"[JuiceVault Voice] Local whisper note: {exc}")
        _LOCAL_WHISPER_MODEL = None
    return _LOCAL_WHISPER_MODEL


async def _recognize_speech_groq(mono_16k: bytes, api_key: str, prompt: str = None) -> tuple:
    """Send 16kHz mono PCM directly to Groq Whisper Large v3 Turbo via aiohttp.
    Transcribes in ~50-100ms with superior multilingual accuracy and rapper/music vocabulary priming."""
    try:
        import aiohttp
    except ImportError:
        return None, "ro-RO"

    wav_bytes = _pcm16_to_wav_bytes(mono_16k, sample_rate=16000, channels=1)
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    # Prime vocabulary with artists, tracks, and common commands
    default_prompt = (
        "Garmin, Juice WRLD, Yeat, Money So Big, Quavo, Playboi Carti, Travis Scott, Ken Carson, "
        "Lil Uzi Vert, Drake, Future, Metro Boomin, Trippie Redd, unreleased, robbery, "
        "burn, bandit, lucid dreams, lean wit me, skip, da skip, dai skip, pause, "
        "resume, shuffle, favorite, da, nu, Flawless, Out The Way, Fein, Magnolia, "
        "baga yeat money so big, pune yeat, canta yeat."
    )
    if prompt:
        default_prompt = f"{prompt}, {default_prompt}"

    data = aiohttp.FormData()
    data.add_field("file", wav_bytes, filename="speech.wav", content_type="audio/wav")
    data.add_field("model", "whisper-large-v3-turbo")
    data.add_field("response_format", "verbose_json")
    data.add_field("temperature", "0.0")
    data.add_field("prompt", default_prompt)

    timeout = aiohttp.ClientTimeout(total=4.5)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, data=data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    text = (result.get("text") or "").strip()
                    lang_raw = (result.get("language") or "").lower().strip()
                    if "ro" in lang_raw or "rum" in lang_raw:
                        lang = "ro-RO"
                    elif "en" in lang_raw:
                        lang = "en-US"
                    else:
                        lang = "ro-RO"
                    return text, lang
                else:
                    err_text = await resp.text()
                    print(f"[JuiceVault Voice Groq] API error {resp.status}: {err_text[:160]}")
                    return None, "ro-RO"
    except Exception as exc:
        print(f"[JuiceVault Voice Groq] Network exception: {exc}")
        return None, "ro-RO"


def _match_wake_word(text: str, custom_words: set = None) -> tuple:
    """Permissive wake word detector returning (matched: bool, cmd_part: str, wake_word: str).
    Matches standard 'Garmin', Romanian salutations ('bă Garmin', 'ok Garmin', 'băi Garmin'),
    misrecognized English STT phrases ('hey god i'm in', 'egger man', 'a garden', 'carmen'),
    learned custom words, and Levenshtein edit distance <= 2."""
    clean = _normalize_speech(text)
    if not clean:
        return False, "", ""

    # 1. Multi-word phonetic misrecognitions
    m = _MULTI_WORD_WAKE_REGEX.search(clean)
    if m:
        wake = m.group(0).strip()
        before = clean[:m.start()].strip().rstrip(",.:;!?- ")
        after = clean[m.end():].strip().lstrip(",.:;!?- ")
        cmd = f"{before} {after}".strip()
        return True, cmd, wake

    # 2. Single-word names with optional multi-prefix salutations ('bă Garmin', 'ok Garmin', etc.)
    m = _SINGLE_WORD_WAKE_REGEX.search(clean)
    if m:
        wake = m.group(0).strip()
        before = clean[:m.start()].strip().rstrip(",.:;!?- ")
        after = clean[m.end():].strip().lstrip(",.:;!?- ")
        cmd = f"{before} {after}".strip()
        return True, cmd, wake

    # 3. Custom learned wake words for this guild
    if custom_words:
        for lw in sorted(custom_words, key=len, reverse=True):
            clean_lw = _normalize_speech(lw)
            if not clean_lw:
                continue
            idx = clean.find(clean_lw)
            if idx != -1:
                before = clean[:idx].strip().rstrip(",.:;!?- ")
                after = clean[idx + len(clean_lw):].strip().lstrip(",.:;!?- ")
                cmd = f"{before} {after}".strip()
                return True, cmd, clean_lw

    # 4. Levenshtein fuzzy distance matching on leading words (distance <= 2 to 'garmin')
    tokens = clean.split()
    if tokens:
        prefix_tokens = {"hey", "hei", "ok", "okay", "hi", "hello", "oak", "oh", "alright", "ba", "bai", "alo", "yo", "a", "the", "e", "de", "bre", "ma", "fa", "auzi", "zi"}
        cand_idx = 0
        while cand_idx < len(tokens) and tokens[cand_idx] in prefix_tokens:
            cand_idx += 1
        if cand_idx < len(tokens):
            cand = tokens[cand_idx]
            cand_clean = re.sub(r'[^a-z0-9]', '', cand)
            if 4 <= len(cand_clean) <= 8:
                if _levenshtein(cand_clean, "garmin") <= 2 or _levenshtein(cand_clean, "carmen") <= 1:
                    cmd_tokens = tokens[cand_idx + 1:]
                    return True, " ".join(cmd_tokens).strip(), cand_clean

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
_FFMPEG_EXE_CACHE = None

# In-memory pre-rendered 48kHz 16-bit stereo PCM cache for instant zero-overhead audio playback
_BEEP_PCM_CACHE = {}


class MemoryPCMAudioSource(discord.AudioSource):
    """Zero-overhead in-memory PCM audio source that streams pre-rendered 48kHz 16-bit stereo
    PCM audio frames from RAM without spawning FFmpeg subprocesses or touching the disk."""

    def __init__(self, pcm_bytes: bytes):
        super().__init__()
        self._data = pcm_bytes
        self._offset = 0

    def is_opus(self) -> bool:
        return False

    def read(self) -> bytes:
        if self._offset >= len(self._data):
            return b''
        chunk = self._data[self._offset:self._offset + 3840]
        self._offset += 3840
        if len(chunk) < 3840:
            chunk = chunk + b'\x00' * (3840 - len(chunk))
        return chunk

    def cleanup(self):
        self._offset = len(self._data)


def _synthesize_beep_pcm(notes: list) -> bytes:
    """Synthesize raw 48kHz 16-bit stereo PCM bytes directly in RAM from a list of (freq, duration, volume)."""
    sample_rate = 48000
    frames = bytearray()
    for freq, duration, vol in notes:
        total_samples = int(sample_rate * duration)
        for i in range(total_samples):
            t = i / sample_rate
            env = (1.0 - math.cos(math.pi * min(1.0, i / (sample_rate * 0.010)))) * 0.5
            decay = (1.0 - (i / total_samples)) ** 1.4
            val = int(env * decay * vol * math.sin(2 * math.pi * freq * t))
            val = max(-32767, min(32767, val))
            frames.extend(struct.pack('<hh', val, val))
    return bytes(frames)


def _get_beep_pcm(sound_type: str) -> bytes:
    """Retrieve pre-rendered raw 48kHz PCM audio for acoustic feedback chimes directly from RAM."""
    if sound_type in _BEEP_PCM_CACHE:
        return _BEEP_PCM_CACHE[sound_type]

    if sound_type == "listening":
        # Ascending bright chime (D5 -> A5)
        notes = [(587.33, 0.08, 17000), (880.00, 0.14, 20000)]
    elif sound_type == "error":
        # Descending gentle low tone (A4 -> E4)
        notes = [(440.00, 0.08, 17000), (329.63, 0.15, 19000)]
    else:  # "understood"
        # Bright snappy affirmative double chime (G5 -> C6)
        notes = [(783.99, 0.06, 17000), (1046.50, 0.14, 21000)]

    pcm = _synthesize_beep_pcm(notes)
    _BEEP_PCM_CACHE[sound_type] = pcm
    return pcm


def _generate_beep_wav(path: str, notes: list) -> str:
    """Helper to synthesize short stereo 48kHz WAV beeps from a list of (freq, duration, volume)."""
    try:
        sample_rate = 48000
        pcm = _synthesize_beep_pcm(notes)
        with wave.open(path, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm)
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
    res = _generate_beep_wav(path, [(440.00, 0.08, 17000), (329.63, 0.15, 19000)])
    if res:
        _ERROR_BEEP_PATH = res
    return res


def _get_siri_chime_wav_path() -> str:
    """Alias for listening chime."""
    return _get_listening_beep_wav_path()


def _get_ffmpeg_exe() -> str:
    """Find FFmpeg executable via imageio_ffmpeg, which is standard in Red-DiscordBot envs, or system PATH."""
    global _FFMPEG_EXE_CACHE
    if _FFMPEG_EXE_CACHE:
        return _FFMPEG_EXE_CACHE
    try:
        import imageio_ffmpeg
        _FFMPEG_EXE_CACHE = imageio_ffmpeg.get_ffmpeg_exe()
        return _FFMPEG_EXE_CACHE
    except Exception:
        pass
    import shutil
    res = shutil.which("ffmpeg") or "ffmpeg"
    _FFMPEG_EXE_CACHE = res
    return res


def _detect_user_language(text: str, default_lang: str = "ro-RO") -> str:
    """Return 'ro' or 'en' based on vocabulary. Defaults to 'ro' unless clear English command keywords are used."""
    clean = _normalize_speech(text)
    words = set(re.findall(r'[a-z0-9]+', clean))
    ro_markers = {
        "ba", "bai", "hei", "cauta", "baga", "pune", "canta", "da", "nu", "piesa",
        "melodia", "melodie", "urmatoarea", "sari", "schimba", "dupa", "de", "pe",
        "te", "rog", "sigur", "bine", "hai", "inapoi", "vreau", "ascult", "da-i",
        "dai", "opreste", "taci", "liniste", "amesteca", "lasa"
    }
    en_markers = {
        "search", "skip", "next", "pause", "resume", "forward", "back", "rewind",
        "shuffle", "what", "please", "leave", "disconnect", "cancel"
    }

    ro_score = len(words & ro_markers)
    en_score = len(words & en_markers)

    if ro_score > en_score:
        return "ro"
    if en_score > ro_score and en_score >= 1:
        return "en"
    return "ro"



def _mix_pcm(music_pcm: bytes, overlay_pcm: bytes, music_vol: float) -> bytes:
    """Mix 48kHz 16-bit stereo PCM bytes with ducking volume scaling using SIMD/NumPy when available."""
    if HAVE_NUMPY:
        try:
            target_len = max(len(music_pcm), len(overlay_pcm))
            if not target_len:
                return b''
            if target_len % 4 != 0:
                target_len += 4 - (target_len % 4)

            if len(music_pcm) < target_len:
                music_pcm = music_pcm + b'\x00' * (target_len - len(music_pcm))
            arr_m = np.frombuffer(music_pcm, dtype=np.int16).astype(np.float32) * music_vol

            if overlay_pcm:
                if len(overlay_pcm) < target_len:
                    overlay_pcm = overlay_pcm + b'\x00' * (target_len - len(overlay_pcm))
                arr_o = np.frombuffer(overlay_pcm, dtype=np.int16).astype(np.float32)
                arr_res = np.clip(arr_m + arr_o, -32768, 32767).astype(np.int16)
            else:
                arr_res = arr_m.astype(np.int16)
            return arr_res.tobytes()
        except Exception:
            pass

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
    """AudioSource wrapper that ducks the main music volume to 18% whenever
    an overlay audio stream (Garmin TTS or Siri chime) is playing, and provides master volume control."""

    def __init__(self, main_source):
        super().__init__()
        self.main_source = main_source
        self.overlay_source = None
        self._lock = threading.Lock()
        self.master_volume = 1.0
        self.current_volume = 1.0
        self.target_volume = 1.0

    def is_opus(self) -> bool:
        return False

    def set_volume(self, vol: float):
        """Set master volume between 0.0 (0%) and 1.5 (150%)."""
        with self._lock:
            self.master_volume = max(0.0, min(1.5, float(vol)))
            if self.overlay_source:
                self.target_volume = 0.18 * self.master_volume
            else:
                self.target_volume = self.master_volume

    def get_volume(self) -> float:
        with self._lock:
            return self.master_volume

    def set_overlay(self, overlay_source):
        with self._lock:
            if self.overlay_source:
                try:
                    self.overlay_source.cleanup()
                except Exception:
                    pass
            self.overlay_source = overlay_source
            self.target_volume = 0.18 * self.master_volume  # Duck music down to 18% of master volume

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
                        self.target_volume = self.master_volume  # Restore music volume to user's master volume!

        if not overlay_data and abs(vol - 1.0) < 0.02 and abs(self.master_volume - 1.0) < 0.02:
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


# In-memory RAM caches for TTS audio (MP3 and pre-decoded raw 48kHz stereo PCM)
_TTS_RAM_CACHE = {}  # (clean_tts, persona) -> bytes of MP3
_TTS_PCM_CACHE = {}  # (clean_tts, persona) -> bytes of raw 48kHz 16-bit stereo PCM


def _decode_mp3_to_pcm(mp3_data: bytes) -> bytes:
    """Use FFmpeg in a background thread to decode MP3 audio bytes into raw 48kHz 16-bit stereo PCM.
    Decodes cleanly with ZERO artificial pitch distortion (absolutely NO chipmunk effect)."""
    if not mp3_data:
        return b''
    try:
        import subprocess
        exe = _get_ffmpeg_exe()
        cmd = [exe, "-i", "pipe:0", "-f", "s16le", "-ar", "48000", "-ac", "2", "-loglevel", "quiet", "pipe:1"]
        proc = subprocess.run(cmd, input=mp3_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=4)
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout
    except Exception as exc:
        log.debug(f"[JuiceVault Voice] PCM decode error: {exc}")
    return b''


async def _synthesize_edge_tts(clean_tts: str, persona: str = "anime") -> bytes:
    """Generate crystal-clear Azure Neural TTS using edge-tts.
    - 'anime': Playful, cute anime girl voice (Microsoft Ana)
    - 'mommy': Assertive, sultry, mature dommy mommy voice (Microsoft Sonia)
    - 'natural': Smooth, natural assistant voice (Microsoft Ava)"""
    if not HAVE_EDGE_TTS:
        return b''
    voice_map = {
        "anime": "en-US-AnaNeural",
        "mommy": "en-GB-SoniaNeural",
        "natural": "en-US-AvaNeural"
    }
    voice = voice_map.get(persona, "en-US-AnaNeural")
    pitch = "-2Hz" if persona == "mommy" else "+0Hz"
    rate = "-4%" if persona == "mommy" else "+0%"
    try:
        comm = edge_tts.Communicate(clean_tts, voice, pitch=pitch, rate=rate)
        chunks = []
        async for chunk in comm.stream():
            if chunk.get("type") == "audio" and chunk.get("data"):
                chunks.append(chunk["data"])
        return b''.join(chunks)
    except Exception as exc:
        log.debug(f"[JuiceVault Edge-TTS] Voice synthesis error for '{clean_tts}': {exc}")
        return b''


async def _fetch_tts_bytes(clean_tts: str, persona: str = "anime") -> bytes:
    """Fetch high-fidelity TTS audio with RAM caching and asynchronous PCM pre-decoding."""
    cache_key = (clean_tts, persona)
    if cache_key in _TTS_RAM_CACHE:
        return _TTS_RAM_CACHE[cache_key]

    data = None
    if HAVE_EDGE_TTS:
        data = await _synthesize_edge_tts(clean_tts, persona=persona)

    if not data:
        # Fallback to Google Translate TTS
        import urllib.parse
        encoded_q = urllib.parse.quote(clean_tts)
        tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded_q}&tl=en&client=tw-ob"
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=3.5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(tts_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                    if resp.status == 200:
                        data = await resp.read()
        except Exception:
            pass

        if not data:
            try:
                import urllib.request
                req = urllib.request.Request(tts_url, headers={"User-Agent": "Mozilla/5.0"})
                def _dl():
                    with urllib.request.urlopen(req, timeout=3.5) as resp:
                        if resp.status == 200:
                            return resp.read()
                    return None
                data = await asyncio.to_thread(_dl)
            except Exception as exc:
                print(f"[JuiceVault Voice TTS] Download error for '{clean_tts}': {exc}")

    if data and len(data) >= 100:
        _TTS_RAM_CACHE[cache_key] = data
        try:
            loop = asyncio.get_running_loop()
            pcm = await loop.run_in_executor(_VOICE_EXECUTOR, _decode_mp3_to_pcm, data)
            if pcm:
                _TTS_PCM_CACHE[cache_key] = pcm
        except Exception:
            pass
        return data

    return b''


_COMMON_SYSTEM_PHRASES = [
    # Anime Girl persona phrases (en-US-AnaNeural)
    ("Yes master? I'm listening~", "anime"),
    ("Hai! What would you like to hear?", "anime"),
    ("What track would you like me to search on YouTube?", "anime"),
    ("Search cancelled.", "anime"),
    ("There is no previous track in history.", "anime"),
    ("Playing previous track for you!", "anime"),
    ("Skipping to the next song!", "anime"),
    ("Skipped 10 tracks!", "anime"),
    ("No music is currently playing.", "anime"),
    ("Added to your favorites! You have great taste~", "anime"),
    ("Track is already in your favorites!", "anime"),
    ("Your favorites list is empty.", "anime"),
    ("Shuffling the queue for you!", "anime"),
    ("Playing shuffled queue!", "anime"),
    ("Loop mode enabled! Playing on repeat~", "anime"),
    ("Loop mode disabled!", "anime"),
    ("Restarting from the beginning!", "anime"),
    ("Paused playback!", "anime"),
    ("Resuming music, let's go!", "anime"),
    ("Goodbye master! Have a wonderful day~", "anime"),
    ("Muted playback.", "anime"),
    ("Command not recognized.", "anime"),
    ("Anime girl voice activated! Yes master~", "anime"),
    ("Dommy mommy voice activated. Be good, darling~", "anime"),
    ("Natural assistant voice activated.", "anime"),

    # Dommy Mommy persona phrases (en-GB-SoniaNeural)
    ("Yes darling? I'm listening.", "mommy"),
    ("What song do you want, darling?", "mommy"),
    ("Search cancelled, darling.", "mommy"),
    ("There is no previous track in history.", "mommy"),
    ("Playing previous track. Don't get used to it.", "mommy"),
    ("Skipped that track for you. Be good.", "mommy"),
    ("Skipped 10 tracks for you.", "mommy"),
    ("No music is playing right now.", "mommy"),
    ("Saved to your favorites. Good choice, darling.", "mommy"),
    ("This song is already in your favorites, darling.", "mommy"),
    ("Your favorites list is empty.", "mommy"),
    ("Shuffled your queue, darling~", "mommy"),
    ("Playing shuffled playlist for you.", "mommy"),
    ("Repeating this track for you indefinitely.", "mommy"),
    ("Repeat mode disabled.", "mommy"),
    ("Restarting the song for you.", "mommy"),
    ("Music is paused, darling.", "mommy"),
    ("Resuming your music, darling.", "mommy"),
    ("Leaving now. Behave yourself, darling.", "mommy"),
    ("Muted playback.", "mommy"),
    ("Command not recognized.", "mommy"),
    ("Dommy mommy voice activated. Be good, darling~", "mommy"),
    ("Anime girl voice activated! Yes master~", "mommy"),
    ("Natural assistant voice activated.", "mommy"),

    # Natural assistant phrases (en-US-AvaNeural)
    ("Yes? I'm listening.", "natural"),
    ("Skipped track.", "natural"),
    ("Queue shuffled.", "natural"),
    ("Paused.", "natural"),
    ("Resuming playback.", "natural"),
    ("Restarting song from the beginning.", "natural"),
    ("Added to your favorites.", "natural"),
    ("Goodbye.", "natural"),
]


def prewarm_voice_cache():
    """Background task to pre-generate beep PCM and pre-load/decode common system voice phrases into RAM."""
    def _run():
        # 1. Pre-synthesize all beeps into RAM PCM
        for st in ("listening", "understood", "error"):
            _get_beep_pcm(st)

        # 2. Pre-fetch and decode common phrases for all personas
        loop = asyncio.new_event_loop()
        try:
            for text, persona in _COMMON_SYSTEM_PHRASES:
                try:
                    loop.run_until_complete(_fetch_tts_bytes(text, persona=persona))
                except Exception:
                    pass
        finally:
            loop.close()
        print(f"[JuiceVault Voice] 🚀 Pre-warmed {len(_TTS_PCM_CACHE)} system voice phrases and PCM chimes into RAM.")

    _VOICE_EXECUTOR.submit(_run)


async def play_beep_sound(guild, sound_type: str = "understood", action_coro=None):
    """Play an acoustic feedback tone in the voice channel using pre-rendered RAM PCM buffers:
    - 'listening': ascending tone indicating Garmin is actively listening
    - 'understood': bright positive tone indicating Garmin understood the command
    - 'error': descending gentle tone indicating Garmin didn't understand / error
    Ducks active music to 18% volume without interrupting playback and with zero FFmpeg overhead."""
    voice = getattr(guild, "voice_client", None)
    if not voice or not voice.is_connected():
        if action_coro is not None and asyncio.iscoroutine(action_coro):
            await action_coro
        return

    pcm_data = _get_beep_pcm(sound_type)
    duration = 0.22 if sound_type == "understood" else (0.24 if sound_type == "listening" else 0.26)

    try:
        mixer = getattr(voice, "_jv_mixer", None)
        if mixer is None and hasattr(voice, "source") and isinstance(voice.source, DuckingAudioSource):
            mixer = voice.source
            voice._jv_mixer = mixer
        elif mixer is None and (voice.is_playing() or voice.is_paused()) and hasattr(voice, "source") and voice.source:
            try:
                mixer = DuckingAudioSource(voice.source)
                voice.source = mixer
                if hasattr(voice, "_player") and voice._player:
                    voice._player.source = mixer
                voice._jv_mixer = mixer
            except Exception:
                mixer = None

        if voice.is_paused() and mixer is not None:
            # Temporarily unpause with music muted so beep plays cleanly without ClientException
            try:
                prev_target = mixer.target_volume
                mixer.target_volume = 0.0
                mixer.current_volume = 0.0
                mixer.set_overlay(MemoryPCMAudioSource(pcm_data))
                voice.resume()
                await asyncio.sleep(duration)
                if voice.is_connected() and not voice.is_paused():
                    voice.pause()
                mixer.target_volume = prev_target
            except Exception:
                pass
        elif voice.is_playing() and mixer is not None:
            mixer.set_overlay(MemoryPCMAudioSource(pcm_data))
        elif not voice.is_playing() and not voice.is_paused():
            try:
                voice.play(MemoryPCMAudioSource(pcm_data))
            except Exception:
                pass
    except Exception as exc:
        print(f"[JuiceVault Beep] Error ({sound_type}): {exc}")

    if action_coro is not None:
        await asyncio.sleep(0.04)
        if asyncio.iscoroutine(action_coro):
            await action_coro
    else:
        await asyncio.sleep(duration)


async def play_chime_and_proceed(guild, action_coro=None, interrupt_playback: bool = False, sound_type: str = "understood"):
    """Play assistant feedback chime in voice channel and execute the command action."""
    await play_beep_sound(guild, sound_type=sound_type, action_coro=action_coro)


async def speak_in_voice(guild, text: str, persona: str = None, lang: str = "en"):
    """Fetch Neural TTS and speak out loud directly in the voice channel.
    Utilizes in-memory RAM caches (_TTS_PCM_CACHE and _TTS_RAM_CACHE) for near-instant 0ms response.
    If music is actively playing, ducks music to 18% volume and speaks over it."""
    voice = getattr(guild, "voice_client", None)
    if not voice or not voice.is_connected():
        return

    clean_tts = re.sub(r'[*_~`#<>|]', '', text).strip()
    if not clean_tts:
        return
    clean_tts = clean_tts[:150]

    if not persona:
        persona = _guild_persona_cache.get(guild.id, "anime")

    cache_key = (clean_tts, persona)

    mixer = getattr(voice, "_jv_mixer", None)
    if mixer is None and hasattr(voice, "source") and isinstance(voice.source, DuckingAudioSource):
        mixer = voice.source
        voice._jv_mixer = mixer
    elif mixer is None and (voice.is_playing() or voice.is_paused()) and hasattr(voice, "source") and voice.source:
        try:
            mixer = DuckingAudioSource(voice.source)
            voice.source = mixer
            if hasattr(voice, "_player") and voice._player:
                voice._player.source = mixer
            voice._jv_mixer = mixer
        except Exception:
            mixer = None

    # Helper function to play PCM bytes across playing, paused, and idle voice states
    async def _play_pcm(pcm_bytes: bytes) -> bool:
        duration = len(pcm_bytes) / (48000 * 4) + 0.1
        try:
            if voice.is_paused() and mixer is not None:
                print(f"[JuiceVault Voice TTS] 🔊 Speaking over paused player in '{guild.name}': \"{clean_tts}\" ({persona})")
                prev_target = mixer.target_volume
                mixer.target_volume = 0.0
                mixer.current_volume = 0.0
                mixer.set_overlay(MemoryPCMAudioSource(pcm_bytes))
                voice.resume()
                for _ in range(int(duration / 0.04)):
                    if not mixer.is_overlay_playing():
                        break
                    await asyncio.sleep(0.04)
                if voice.is_connected() and not voice.is_paused():
                    voice.pause()
                mixer.target_volume = prev_target
                return True
            elif voice.is_playing() and mixer is not None:
                print(f"[JuiceVault Voice TTS] 🔊 RAM Instant Speaking over ducked music (18%) in '{guild.name}': \"{clean_tts}\" ({persona})")
                overlay = MemoryPCMAudioSource(pcm_bytes)
                mixer.set_overlay(overlay)
                for _ in range(int(duration / 0.04)):
                    if not mixer.is_overlay_playing():
                        break
                    await asyncio.sleep(0.04)
                return True
            elif not voice.is_playing() and not voice.is_paused():
                print(f"[JuiceVault Voice TTS] 🔊 RAM Instant Speaking in '{guild.name}': \"{clean_tts}\" ({persona})")
                voice.play(MemoryPCMAudioSource(pcm_bytes))
                for _ in range(int(duration / 0.04)):
                    if not voice.is_playing():
                        break
                    await asyncio.sleep(0.04)
                return True
        except Exception as exc:
            print(f"[JuiceVault Voice TTS] Memory PCM playback exception: {exc}")
        return False

    # 1. Fast path: pre-decoded PCM in RAM for 0ms instant playback!
    pcm_data = _TTS_PCM_CACHE.get(cache_key)
    if pcm_data and await _play_pcm(pcm_data):
        return

    # 2. Fetch or retrieve MP3 data
    data = await _fetch_tts_bytes(clean_tts, persona=persona)
    if not data:
        return

    # Check if PCM decode completed during fetch
    pcm_data = _TTS_PCM_CACHE.get(cache_key)
    if pcm_data and await _play_pcm(pcm_data):
        return

    # 3. Fallback: stream MP3 via temp file + FFmpeg
    path = os.path.join(tempfile.gettempdir(), f"jv_voice_tts_{guild.id}.mp3")
    try:
        with open(path, "wb") as f:
            f.write(data)
    except Exception:
        return

    try:
        exe = _get_ffmpeg_exe()
        duration = max(1.2, min(8.0, len(clean_tts) * 0.085 + 0.4))
        if voice.is_paused() and mixer is not None:
            prev_target = mixer.target_volume
            mixer.target_volume = 0.0
            mixer.current_volume = 0.0
            mixer.set_overlay(discord.FFmpegPCMAudio(path, executable=exe))
            voice.resume()
            for _ in range(int(duration / 0.04)):
                if not mixer.is_overlay_playing():
                    break
                await asyncio.sleep(0.04)
            if voice.is_connected() and not voice.is_paused():
                voice.pause()
            mixer.target_volume = prev_target
        elif voice.is_playing() and mixer is not None:
            print(f"[JuiceVault Voice TTS] 🔊 Speaking over ducked music (18%) in '{guild.name}': \"{clean_tts}\" ({lang})")
            overlay = discord.FFmpegPCMAudio(path, executable=exe)
            mixer.set_overlay(overlay)
            for _ in range(int(duration / 0.04)):
                if not mixer.is_overlay_playing():
                    break
                await asyncio.sleep(0.04)
        elif not voice.is_playing() and not voice.is_paused():
            print(f"[JuiceVault Voice TTS] 🔊 Speaking in '{guild.name}': \"{clean_tts}\" ({lang})")
            voice.play(discord.FFmpegPCMAudio(path, executable=exe))
            for _ in range(int(duration / 0.04)):
                if not voice.is_playing():
                    break
                await asyncio.sleep(0.04)
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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
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
            self._lock = threading.Lock()
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
            """Track active session user."""
            now = time.monotonic()
            self._active_session_uid = user_id
            self._active_session_expires = now + duration

        def _unlock_session(self):
            """Release session lock so any user in the voice channel can issue commands to Garmin."""
            self._active_session_uid = None
            self._active_session_expires = 0.0

        def _is_locked_to_other(self, user_id: int) -> bool:
            """Audio packets are never dropped at the sink level, ensuring all users can speak without getting ignored."""
            return False

        def wants_opus(self) -> bool:
            return False  # Decode Opus packets to 48kHz 16-bit stereo PCM

        def write(self, user, data):
            if not self._active or not user or getattr(user, "bot", False):
                return
            pcm = getattr(data, "pcm", None)
            if not pcm:
                return

            now = time.monotonic()
            uid = user.id

            try:
                # Watchdog: revive silence worker task if it ever terminated unexpectedly
                if self._active and (self._worker_task is None or self._worker_task.done()):
                    try:
                        loop = self.bot.loop
                        if loop and loop.is_running():
                            self._worker_task = asyncio.run_coroutine_threadsafe(self._process_silence_loop(), loop)
                    except Exception:
                        pass

                with self._lock:
                    buf = self._buffers.setdefault(uid, bytearray())
                    if len(buf) == 0:
                        print(f"[JuiceVault Voice] 🎙️ Audio received from {getattr(user, 'display_name', user)} - listening...")
                    # Buffer up to 10 seconds of audio (~960,000 bytes)
                    if len(buf) < 960_000:
                        buf.extend(pcm)
                    self._last_speech[uid] = now
            except Exception as exc:
                log.debug(f"[JuiceVault Voice] write() exception: {exc}")

        async def _process_silence_loop(self):
            """Monitors when a user finishes speaking and dispatches audio to STT with minimal latency."""
            while self._active:
                try:
                    # Snappy 30ms polling loop for near-instant responsiveness
                    await asyncio.sleep(0.030)
                    now = time.monotonic()
                    ready_dispatches = []

                    with self._lock:
                        uids = list(self._last_speech.keys())
                        pending = getattr(self.cog, "_pending_yt_voice", {}).get(self.guild_id)
                        for uid in uids:
                            last = self._last_speech.get(uid, 0.0)
                            is_pending = bool(pending and pending.get("user_id") == uid and time.time() < pending.get("expires", 0.0))
                            buf_len = len(self._buffers.get(uid, b""))

                            # Adaptive silence detection:
                            # 0.16s for short "da"/"nu" pending answers
                            # 0.22s for short utterances (<= 1.6s of audio: "Hey Garmin", "Ok Garmin", "skip", "pause", "shuffle")
                            # 0.38s for longer speech (song requests)
                            if is_pending:
                                silence_needed = 0.16
                            elif buf_len <= 320_000:
                                silence_needed = 0.22
                            else:
                                silence_needed = 0.38

                            if now - last >= silence_needed:
                                buf = self._buffers.pop(uid, bytearray())
                                self._last_speech.pop(uid, None)
                                min_bytes = 4_000 if is_pending else 12_000
                                if len(buf) >= min_bytes:
                                    ready_dispatches.append((uid, bytes(buf)))

                    for uid, pcm_bytes in ready_dispatches:
                        asyncio.create_task(self._transcribe_and_dispatch(uid, pcm_bytes))

                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    log.debug(f"[JuiceVault Voice] Silence detection loop error: {exc}")
                    await asyncio.sleep(0.08)

        async def _play_track_now(self, guild, track):
            """Queue a track at index 0 and immediately start playback."""
            try:
                gid = self.guild_id
                self.cog.manual_queues.setdefault(gid, []).insert(0, track)
                voice = guild.voice_client
                if gid in self.cog.tasks and not self.cog.tasks[gid].done():
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
            finally:
                self._unlock_session()

        async def _search_and_play_youtube(self, guild, query: str, user_name: str, persona: str = None):
            """Search YouTube for query, speak confirmation, and begin immediate playback."""
            if not query:
                self._unlock_session()
                return
            clean_q = _clean_music_query(query)
            if not clean_q:
                self._unlock_session()
                return
            if not persona:
                persona = await get_guild_persona(self.cog, self.guild_id)
            wait_speech = f"Searching YouTube for {clean_q}~" if persona == "anime" else (f"Searching YouTube for {clean_q}. One moment." if persona == "mommy" else f"Searching YouTube for {clean_q}.")
            await play_beep_sound(guild, "understood")

            # Launch YouTube extraction concurrently in background while speaking confirmation!
            from .external_search_patch import _extract_search
            search_task = asyncio.create_task(asyncio.to_thread(_extract_search, clean_q))

            await speak_in_voice(guild, wait_speech, persona=persona)
            await self._notify(guild, f"🔍 **[Garmin]** {user_name}: Searching YouTube for *\"{clean_q}\"*... ⏳")

            try:
                info = await search_task
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
                        await self._notify(guild, f"🎥 **[Garmin]** Playing from YouTube: **{title}** 🎶")
                        return

                fail_msg = f"Could not find {clean_q} on YouTube."
                await play_beep_sound(guild, "error")
                await speak_in_voice(guild, fail_msg, persona=persona)
                await self._notify(guild, f"❌ **[Garmin]** {fail_msg}")
            except Exception as exc:
                print(f"[Garmin YouTube] Error searching '{clean_q}': {exc}")
                fail_msg = f"No YouTube results found for {clean_q}."
                await play_beep_sound(guild, "error")
                await speak_in_voice(guild, fail_msg, persona=persona)
                await self._notify(guild, f"❌ **[Garmin]** {fail_msg}")
            finally:
                self._unlock_session()


        async def _transcribe_and_dispatch(self, user_id, pcm_bytes):
            if self._is_locked_to_other(user_id):
                return

            now = time.monotonic()
            guild = self.bot.get_guild(self.guild_id)
            user = guild.get_member(user_id) if guild else None
            user_name = user.display_name if user else f"User {user_id}"

            try:
                mono_16k = self._downsample_to_16k_mono(pcm_bytes)
            except Exception as e:
                print(f"[JuiceVault Voice] Audio conversion error: {e}")
                return

            pending = getattr(self.cog, "_pending_yt_voice", {}).get(self.guild_id)
            is_pending = bool(pending and time.time() < pending.get("expires", 0.0) and pending.get("user_id") == user_id)
            in_wake_window = bool(now < self._wake_windows.get(user_id, 0.0))

            rms = _calculate_rms(mono_16k)
            # Minimum speech energy filter: discard quiet background hum or breathing below 350 RMS
            if not is_pending and not in_wake_window and rms < 350:
                return

            groq_key = await _get_groq_api_key(self.cog)
            text = None
            detected_lang = "en-US"

            # SMART MULTI-TIER PIPELINE:
            # 1. If in active wake window or answering pending prompt: use high-accuracy AI directly
            if is_pending or in_wake_window:
                try:
                    text, detected_lang = await asyncio.wait_for(
                        self._recognize_speech_ai(mono_16k, groq_key=groq_key),
                        timeout=5.0
                    )
                except Exception as exc:
                    print(f"[JuiceVault Voice] Active AI STT error: {exc}")
                    text = None
            else:
                # 2. Passive listening for wake word ("Ok Garmin", "Hey Garmin"):
                # Step A: Local fast-whisper if available (0 tokens, 0 network, runs on CPU/RAM)
                local_model = _get_local_whisper_model()
                if local_model:
                    try:
                        text, detected_lang = await self._recognize_speech_ai(mono_16k, groq_key=None)
                    except Exception:
                        text = None

                # Step B: Free Google STT
                if not text:
                    try:
                        text, detected_lang = await self._recognize_speech_google(mono_16k)
                    except Exception:
                        text = None

                # Step C: If Google STT failed or was rate-limited (HTTP 429/403) and Groq key is configured:
                # Fall back to Groq Cloud so Garmin NEVER ignores wake words!
                if not text and groq_key and _can_query_groq_passive():
                    try:
                        print(f"[JuiceVault Voice] Passive fallback to Groq Whisper Large v3 Turbo (RMS: {rms})...")
                        text, detected_lang = await asyncio.wait_for(
                            self._recognize_speech_groq(mono_16k, groq_key, prompt="Ok Garmin, Hey Garmin, Garmin, skip, pause, play, next"),
                            timeout=4.5
                        )
                    except Exception as g_err:
                        print(f"[JuiceVault Voice] Groq passive fallback error: {g_err}")
                        text = None

            if not text:
                return

            clean = _normalize_speech(text)
            print(f"[JuiceVault Voice] Speech from {user_name}: '{text}' (normalized: '{clean}') [active={is_pending or in_wake_window}]")

            # 1. PENDING TITLE PROMPT (e.g. user said bare "Garmin play" or "Garmin search youtube")
            if is_pending:
                tokens = set(re.findall(r'[a-z0-9]+', clean))
                padded = f" {clean} "
                is_neg = bool(tokens & NEGATIVE_WORDS) or any(f" {p} " in padded for p in NEGATIVE_PHRASES) or "cancel" in clean
                if is_neg:
                    self.cog._pending_yt_voice.pop(self.guild_id, None)
                    with self._lock:
                        self._wake_windows.pop(user_id, None)
                    self._unlock_session()
                    persona = await get_guild_persona(self.cog, self.guild_id)
                    cancel_speech = "Search cancelled." if persona != "mommy" else "Search cancelled, darling."
                    await play_beep_sound(guild, "error")
                    await speak_in_voice(guild, cancel_speech, persona=persona)
                    await self._notify(guild, "🚫 **[Garmin]** Search cancelled.")
                    return

                clean_title = _clean_music_query(clean)
                if clean_title:
                    self.cog._pending_yt_voice.pop(self.guild_id, None)
                    with self._lock:
                        self._wake_windows.pop(user_id, None)
                    self._lock_session(user_id, duration=35.0)
                    persona = await get_guild_persona(self.cog, self.guild_id)
                    await play_beep_sound(guild, "understood")
                    await self._search_and_play_youtube(guild, clean_title, user_name, persona=persona)
                    return
                return

            # 2. WAKE WORD DETECTION (Permissive matcher + custom learned words + fuzzy matching)
            custom_words = await get_learned_wake_words(self.cog, self.guild_id)
            matched_wake, cmd_part, wake_word = _match_wake_word(clean, custom_words)

            if matched_wake:
                self._lock_session(user_id, duration=20.0)
                if wake_word and len(wake_word) >= 3 and wake_word not in custom_words:
                    asyncio.create_task(add_learned_wake_word(self.cog, self.guild_id, wake_word))

                persona = await get_guild_persona(self.cog, self.guild_id)

                if not cmd_part:
                    # User only said "Garmin" / "Hey Garmin" / "Ok Garmin" -> open 12s wake window and greet INSTANTLY!
                    with self._lock:
                        self._wake_windows[user_id] = now + 12.0
                    print(f"[JuiceVault Voice] Wake word '{wake_word}' activated by {user_name} ({persona}). Waiting for command...")
                    if persona == "mommy":
                        greeting = "Yes darling? I'm listening."
                    elif persona == "natural":
                        greeting = "Yes? I'm listening."
                    else:
                        greeting = "Yes master? I'm listening~"

                    # Play instant greeting directly from pre-warmed RAM PCM! (0ms latency!)
                    await speak_in_voice(guild, greeting, persona=persona)
                    await self._notify(guild, f"🎤 **[Garmin]** {greeting} 🟢")
                    return

                # User said "Garmin" + command in one single breath!
                # If it's a song request and Groq / local AI is available, refine transcription with AI for 100% accuracy:
                is_song_request = bool(re.search(r'\b(?:play|search|cauta|baga|pune|canta|listen|put\s+on)\b', cmd_part, re.I) or _KNOWN_EXTERNAL_ARTISTS_REGEX.search(cmd_part))
                if is_song_request and (groq_key or _get_local_whisper_model()):
                    ai_text, _ = await self._recognize_speech_ai(mono_16k, groq_key=groq_key)
                    if ai_text:
                        clean_ai = _normalize_speech(ai_text)
                        m_wake, r_cmd, _ = _match_wake_word(clean_ai, custom_words)
                        if m_wake and r_cmd:
                            cmd_part = r_cmd
                        elif not m_wake and clean_ai:
                            cmd_part = clean_ai

                clean_cmd = cmd_part
                with self._lock:
                    self._wake_windows.pop(user_id, None)
            else:
                # Did this utterance happen within an active wake window?
                if in_wake_window:
                    clean_cmd = clean
                    with self._lock:
                        self._wake_windows.pop(user_id, None)
                else:
                    # Passive chatter between people in call! Discard with ZERO Groq tokens!
                    print(f"[JuiceVault Voice] Passive chatter ignored from {user_name} (no 'Garmin' wake word, 0 Groq calls): '{clean}'")
                    return

            persona = await get_guild_persona(self.cog, self.guild_id)
            print(f"[JuiceVault Voice Command] {user_name} -> Garmin command: '{clean_cmd}' (full: '{clean}') [persona={persona}]")

            # PRECEDENCE 0: SWITCH VOICE PERSONA
            if re.search(r'\b(?:mommy\s+voice|dommy\s+mommy|mommy\s+mode|switch\s+to\s+mommy)\b', clean_cmd, re.I):
                await set_guild_persona(self.cog, self.guild_id, "mommy")
                confirm = "Dommy mommy voice activated. Be good, darling~"
                await speak_in_voice(guild, confirm, persona="mommy")
                self._unlock_session()
                await self._notify(guild, f"💋 **[Garmin]** {user_name}: *\"{text}\"* ➔ **Dommy Mommy** voice activated! 👠")
                return

            if re.search(r'\b(?:anime\s+voice|anime\s+girl|anime\s+mode|switch\s+to\s+anime)\b', clean_cmd, re.I):
                await set_guild_persona(self.cog, self.guild_id, "anime")
                confirm = "Anime girl voice activated! Yes master~"
                await speak_in_voice(guild, confirm, persona="anime")
                self._unlock_session()
                await self._notify(guild, f"✨ **[Garmin]** {user_name}: *\"{text}\"* ➔ **Anime Girl** voice activated! 🎀")
                return

            if re.search(r'\b(?:natural\s+voice|normal\s+voice|default\s+voice|switch\s+to\s+natural)\b', clean_cmd, re.I):
                await set_guild_persona(self.cog, self.guild_id, "natural")
                confirm = "Natural assistant voice activated."
                await speak_in_voice(guild, confirm, persona="natural")
                self._unlock_session()
                await self._notify(guild, f"🎙️ **[Garmin]** {user_name}: *\"{text}\"* ➔ **Natural Assistant** voice activated! 🎧")
                return

            # PRECEDENCE 1: PREVIOUS / BACK
            if re.search(r'\b(?:previous|prev|back|inapoi|dinainte|anterioara|piesa dinainte|melodia dinainte|piesa anterioara|last\s+song|previous\s+song|go\s+back|play\s+previous)\b', clean_cmd, re.I):
                hist = self.cog.history.get(self.guild_id, [])
                if hist:
                    prev_t = hist.pop()
                    await play_chime_and_proceed(guild)
                    await self._play_track_now(guild, prev_t)
                    self._unlock_session()
                    speech = "Playing previous track for you!" if persona == "anime" else ("Playing previous track. Don't get used to it." if persona == "mommy" else "Playing previous track.")
                    await speak_in_voice(guild, speech, persona=persona)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Previous track! ⏮️")
                else:
                    await play_beep_sound(guild, "error")
                    self._unlock_session()
                    await speak_in_voice(guild, "There is no previous track in history.", persona=persona)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: No previous track in history.")
                return

            # PRECEDENCE 2: SKIP / NEXT
            skip_pattern = (
                r'\b(?:skip|next|urmatoarea|sari|treci\s+peste|treci\s+la\s+urmatoarea|schimba|schimb-o|'
                r'alta\s+piesa|alta\s+melodie|da-i\s+skip|dai\s+skip|da\s+skip|dă-i\s+skip|dă\s+skip|dăi\s+skip|'
                r'skip\s+la\s+piesa|skip\s+piesa|skip\s+this|skip\s+song|next\s+song|next\s+track|'
                r'the\s+escape|the\s+scape|they\s+skip|the\s+skip|day\s+skip|they\s+scape|they\s+skep|'
                r'the\s+skep|escape|scape|the\s+scope|they\s+scope|they\s+keep|the\s+keep)\b'
            )
            if re.search(skip_pattern, clean_cmd, re.I) or any(w in clean_cmd for w in ("da-i skip", "dai skip", "da skip", "skip la piesa", "skip piesa", "urmatoarea piesa", "schimba piesa", "the escape", "escape", "they skip", "the scape")):
                if any(w in clean_cmd for w in ("10", "ten", "zece")):
                    await play_chime_and_proceed(guild, self.cog._request_skip(self.guild_id, 10))
                    self._unlock_session()
                    speech = "Skipped 10 tracks!" if persona != "mommy" else "Skipped 10 tracks for you."
                    await speak_in_voice(guild, speech, persona=persona)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Skipped 10 tracks! ⏩")
                else:
                    await play_chime_and_proceed(guild, self.cog._request_skip(self.guild_id, 1))
                    self._unlock_session()
                    speech = "Skipping to the next song!" if persona == "anime" else ("Skipped that track for you. Be good." if persona == "mommy" else "Skipped track.")
                    await speak_in_voice(guild, speech, persona=persona)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Skipped track! ⏭️")
                return

            # PRECEDENCE 3: RESTART / REPLAY
            if re.search(r'\b(?:restart|restart\s+song|replay|start\s+over|play\s+again|from\s+the\s+beginning|beginning)\b', clean_cmd, re.I):
                if hasattr(self.cog, "_request_seek"):
                    await play_chime_and_proceed(guild, self.cog._request_seek(self.guild_id, target_position=0.0))
                    self._unlock_session()
                    speech = "Restarting from the beginning!" if persona == "anime" else ("Restarting the song for you." if persona == "mommy" else "Restarting song from the beginning.")
                    await speak_in_voice(guild, speech, persona=persona)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Restarting from beginning! ⏪")
                    return

            # PRECEDENCE 4: SHUFFLE / RANDOM
            if re.search(r'\b(?:shuffle|amesteca|amesteca\s+piesele|amesteca\s+coada|random|mix|la intamplare|random song|piesa la intamplare|shuffle\s+queue|shuffle\s+playlist)\b', clean_cmd, re.I):
                q = self.cog.queues.get(self.guild_id, [])
                if not q:
                    try:
                        category = await self.cog.config.guild(guild).category()
                        tracks = await self.cog.fetch_tracks(category)
                        if tracks:
                            self.cog.queues[self.guild_id] = list(tracks)
                            q = self.cog.queues[self.guild_id]
                    except Exception:
                        pass
                if q or self.cog.manual_queues.get(self.guild_id):
                    import random
                    if q:
                        random.shuffle(q)
                    mq = self.cog.manual_queues.get(self.guild_id)
                    if mq:
                        random.shuffle(mq)
                    self.cog._cleanup_prefetch(self.guild_id)
                    self.cog._trigger_next_prefetch(self.guild_id)

                    voice = guild.voice_client if guild else None
                    if voice and (voice.is_playing() or voice.is_paused()):
                        await play_chime_and_proceed(guild)
                        speech = "Shuffling the queue for you!" if persona == "anime" else ("Shuffled your queue, darling~" if persona == "mommy" else "Queue shuffled.")
                        await speak_in_voice(guild, speech, persona=persona)
                        await self.cog._request_skip(self.guild_id, 1)
                    else:
                        if voice and voice.channel:
                            self.cog.stop_events[self.guild_id] = asyncio.Event()
                            self.cog.skip_events[self.guild_id] = asyncio.Event()
                            self.cog.seek_events[self.guild_id] = asyncio.Event()
                            self.cog.skip_counts[self.guild_id] = 0
                            self.cog.effects[self.guild_id] = "none"
                            self.cog.tasks[self.guild_id] = asyncio.create_task(self.cog._player(guild, voice.channel))
                        await play_chime_and_proceed(guild)
                        speech = "Playing shuffled queue!" if persona == "anime" else ("Playing shuffled playlist for you." if persona == "mommy" else "Playing shuffled queue!")
                        await speak_in_voice(guild, speech, persona=persona)

                    ui = self.bot.get_cog("JuiceVaultUI")
                    if ui:
                        asyncio.create_task(ui.update_panel(self.guild_id))
                    if hasattr(self.cog, "web_remote") and self.cog.web_remote:
                        asyncio.create_task(self.cog.web_remote.broadcast_state(self.guild_id))
                    self._unlock_session()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Shuffled queue! 🔀")
                else:
                    self._unlock_session()
                return

            # PRECEDENCE 5: LOOP / REPEAT
            if re.search(r'\b(?:loop\s+song|repeat\s+song|loop\s+track|repeat\s+track|loop|repeat)\b', clean_cmd, re.I) and not any(w in clean_cmd for w in ("play", "search", "cauta", "baga")):
                ui = self.bot.get_cog("JuiceVaultUI")
                panel = ui.panel if ui and hasattr(ui, "panel") else None
                cur = self.cog.current.get(self.guild_id)
                if cur and panel:
                    enabled = not panel.repeat_enabled.get(self.guild_id, False)
                    panel.repeat_enabled[self.guild_id] = enabled
                    panel.repeat_queued[self.guild_id] = False
                    manual = self.cog.manual_queues.setdefault(self.guild_id, [])
                    if enabled:
                        if not any(t.get("_jv_repeat_copy") for t in manual):
                            rep = dict(cur)
                            rep.pop("_jv_seek_copy", None)
                            rep.pop("_resume_position", None)
                            rep.pop("_resume_was_playing", None)
                            rep["_jv_repeat_copy"] = True
                            manual.insert(0, rep)
                        panel.repeat_queued[self.guild_id] = True
                        rep_msg = "Loop mode enabled! Playing on repeat~" if persona == "anime" else ("Repeating this track for you indefinitely." if persona == "mommy" else "Repeat mode enabled!")
                    else:
                        self.cog.manual_queues[self.guild_id] = [t for t in manual if not t.get("_jv_repeat_copy")]
                        rep_msg = "Loop mode disabled!" if persona != "mommy" else "Repeat mode disabled."

                    await play_chime_and_proceed(guild)
                    await speak_in_voice(guild, rep_msg, persona=persona)
                    if hasattr(panel, "update_panel"):
                        asyncio.create_task(panel.update_panel(self.guild_id))
                    self._unlock_session()
                    await self._notify(guild, f"🔁 **[Garmin]** {user_name}: *\"{text}\"* ➔ {rep_msg}")
                    return

            # PRECEDENCE 6: VOLUME CONTROLS
            vol_match = re.search(r'\b(?:volume|set\s+volume\s+to|vol)\s+(\d{1,3})\b', clean_cmd, re.I)
            if vol_match or any(w in clean_cmd for w in ("volume up", "louder", "turn it up", "volume down", "quieter", "lower volume", "turn it down", "mute", "unmute")):
                voice = guild.voice_client if guild else None
                mixer = getattr(voice, "_jv_mixer", None) if voice else None
                if mixer and hasattr(mixer, "set_volume"):
                    cur_vol = int(mixer.get_volume() * 100)
                    if vol_match:
                        target_pct = max(0, min(150, int(vol_match.group(1))))
                    elif any(w in clean_cmd for w in ("volume up", "louder", "turn it up")):
                        target_pct = min(150, cur_vol + 15)
                    elif any(w in clean_cmd for w in ("volume down", "quieter", "lower volume", "turn it down")):
                        target_pct = max(0, cur_vol - 15)
                    elif "unmute" in clean_cmd:
                        target_pct = 100
                    else:  # mute
                        target_pct = 0

                    mixer.set_volume(target_pct / 100.0)
                    await play_chime_and_proceed(guild)
                    vol_msg = "Muted playback." if target_pct == 0 else (f"Volume set to {target_pct} percent!" if persona == "anime" else (f"Volume adjusted to {target_pct} percent. Better?" if persona == "mommy" else f"Volume set to {target_pct}%!"))
                    await speak_in_voice(guild, vol_msg, persona=persona)
                    self._unlock_session()
                    await self._notify(guild, f"🔊 **[Garmin]** {user_name}: *\"{text}\"* ➔ {vol_msg}")
                    return
                else:
                    self._unlock_session()
                    await self._notify(guild, "⚠️ **[Garmin]** Volume control is not active.")
                    return

            # PRECEDENCE 7: NOW PLAYING / SONG INFO
            if re.search(r'\b(?:what\s+song\s+is\s+this|what\'?s\s+playing|what\s+is\s+playing|current\s+song|current\s+track|song\s+info|now\s+playing)\b', clean_cmd, re.I):
                cur = self.cog.current.get(self.guild_id)
                if cur:
                    title = cur.get("title") or cur.get("name") or "Untitled Track"
                    artist = cur.get("artist") or "Juice WRLD"
                    np_speech = f"Now playing {title} by {artist}!" if persona == "anime" else (f"Currently playing {title} by {artist}, darling." if persona == "mommy" else f"Currently playing {title} by {artist}.")
                    await play_chime_and_proceed(guild)
                    await speak_in_voice(guild, np_speech, persona=persona)
                    self._unlock_session()
                    await self._notify(guild, f"🎵 **[Garmin]** Currently playing: **{title}** — *{artist}* 🎶")
                else:
                    await play_beep_sound(guild, "error")
                    await speak_in_voice(guild, "No music is currently playing.", persona=persona)
                    self._unlock_session()
                    await self._notify(guild, "ℹ️ **[Garmin]** No track is currently playing.")
                return

            # PRECEDENCE 8: PAUSE / STOP
            if re.search(r'\b(?:pause|pauza|stop|opreste|opreste-te|taci|taci din gura|liniste|shut up|hold|freeze|quiet)\b', clean_cmd, re.I):
                voice = guild.voice_client if guild else None
                if voice and voice.is_playing():
                    await play_chime_and_proceed(guild)
                    if hasattr(self.cog, "pause_playback"):
                        self.cog.pause_playback(self.guild_id)
                    else:
                        voice.pause()
                    self._unlock_session()
                    pause_msg = "Paused playback!" if persona == "anime" else ("Music is paused, darling." if persona == "mommy" else "Paused.")
                    await speak_in_voice(guild, pause_msg, persona=persona)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Paused! ⏸️")
                else:
                    self._unlock_session()
                return

            # PRECEDENCE 9: RESUME / PLAY
            if clean_cmd.strip() in {"play", "resume", "continua", "porneste", "da drumul", "baga", "unpause"} or clean_cmd.strip() == "play":
                voice = guild.voice_client if guild else None
                if voice and voice.is_paused():
                    await play_chime_and_proceed(guild)
                    if hasattr(self.cog, "resume_playback"):
                        self.cog.resume_playback(self.guild_id)
                    else:
                        voice.resume()
                    self._unlock_session()
                    resume_msg = "Resuming music, let's go!" if persona == "anime" else ("Resuming your music, darling." if persona == "mommy" else "Resuming music!")
                    await speak_in_voice(guild, resume_msg, persona=persona)
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
                        start_msg = "Playing shuffled queue!" if persona == "anime" else ("Playing shuffled playlist for you." if persona == "mommy" else "Started playback!")
                        await speak_in_voice(guild, start_msg, persona=persona)
                        await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Started playback! ▶️")
                    else:
                        self._unlock_session()
                    return
                else:
                    # Voice is active and playing: user said bare "Garmin play" -> ask what to play!
                    self._lock_session(user_id, duration=25.0)
                    with self._lock:
                        self._wake_windows[user_id] = now + 15.0
                    if not hasattr(self.cog, "_pending_yt_voice"):
                        self.cog._pending_yt_voice = {}
                    self.cog._pending_yt_voice[self.guild_id] = {
                        "user_id": user_id,
                        "query": "",
                        "lang": "en",
                        "expires": time.time() + 20.0,
                        "user_name": user_name,
                        "awaiting_title": True,
                    }
                    prompt_speech = "Hai! What would you like to hear?" if persona == "anime" else ("What song do you want, darling?" if persona == "mommy" else "What track would you like me to play?")
                    await speak_in_voice(guild, prompt_speech, persona=persona)
                    await play_beep_sound(guild, "listening")
                    self._buffers.pop(user_id, None)
                    self._last_speech.pop(user_id, None)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: {prompt_speech} ⏳")
                    return

            # PRECEDENCE 10: SEEK / FORWARD / REWIND 10s
            if any(w in clean_cmd for w in ("inainte 10", "forward 10", "skip 10s", "10 secunde inainte", "fast forward")):
                if hasattr(self.cog, "_request_seek"):
                    await play_chime_and_proceed(guild, self.cog._request_seek(self.guild_id, delta=10.0))
                    self._unlock_session()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Forward +10s ⏩")
                    return
            elif any(w in clean_cmd for w in ("inapoi 10", "back 10", "rewind 10", "10 secunde inapoi", "rewind")):
                if hasattr(self.cog, "_request_seek"):
                    await play_chime_and_proceed(guild, self.cog._request_seek(self.guild_id, delta=-10.0))
                    self._unlock_session()
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Rewind -10s ⏪")
                    return

            # PRECEDENCE 11A: PLAY FROM FAVORITES
            is_play_fav = bool(re.search(
                r'\b(?:play\s+my\s+favorites|play\s+my\s+favorite\s+song|play\s+my\s+favorite|play\s+a\s+favorite\s+song|play\s+a\s+favorite|play\s+favorite\s+song|play\s+favorite|play\s+favorites|baga\s+o\s+piesa\s+favorita|baga\s+o\s+piesa\s+din\s+favorite|baga\s+din\s+favorite|baga\s+favoritele\s+mele|pune\s+o\s+piesa\s+favorita|pune\s+o\s+piesa\s+din\s+favorite|pune\s+favoritele\s+mele|baga\s+o\s+melodie\s+preferata|pune\s+o\s+melodie\s+preferata|baga\s+melodiile\s+mele\s+preferate|pune\s+preferatele\s+mele|da\s+drumul\s+la\s+favorite|baga\s+piesele\s+mele\s+favorite|baga\s+o\s+piesa\s+de\s+la\s+favorite|pune\s+o\s+piesa\s+din\s+preferatele\s+mele)\b',
                clean_cmd,
                re.I
            )) or (
                any(p in clean_cmd for p in ("play", "baga", "pune", "reda", "da drumul", "canta"))
                and any(f in clean_cmd for f in ("favorite", "favorita", "preferata", "preferate", "favorit", "favorites"))
                and not any(s in clean_cmd for s in ("salveaza", "adauga", "save", "add", "baga la", "pune la"))
            )
            if is_play_fav:
                uid_str = str(user_id)
                bot_favs = getattr(self.bot, "_jv_data", {}).get("favorites", {})
                user_list = bot_favs.get(uid_str) or bot_favs.get(user_name.lower()) or bot_favs.get("default", [])

                if not user_list:
                    no_favs_speech = "Your favorites list is empty."
                    await play_beep_sound(guild, "error")
                    await speak_in_voice(guild, no_favs_speech, persona=persona)
                    await self._notify(guild, f"💔 **[Garmin]** {user_name}: You don't have any favorites. Say *„Garmin, save this song”* while listening to a track!")
                    self._unlock_session()
                    return

                import random
                fav_track = random.choice(user_list)
                track_name = fav_track.get("title") or "Favorite Track"
                artist_name = fav_track.get("artist") or "Juice WRLD"

                play_speech = f"Playing from your favorites: {track_name}."
                await play_beep_sound(guild, "understood")
                await speak_in_voice(guild, play_speech, persona=persona)
                await self._play_track_now(guild, dict(fav_track))
                self._unlock_session()
                await self._notify(guild, f"❤️ **[Garmin]** {user_name}: *\"{text}\"* ➔ Playing favorite: **{track_name}** — *{artist_name}* 🎶")
                return

            # PRECEDENCE 11B: SAVE / FAVORITE CURRENT SONG
            is_save_fav = bool(re.search(
                r'\b(?:save\s+this\s+song|save\s+song|save\s+this|save\s+track|favorite\s+this\s+song|favorite\s+this|favorite\s+song|favorite\s+track|add\s+to\s+favorites|add\s+to\s+favorite|love\s+this\s+song|like\s+this\s+song|salveaza\s+piesa\s+asta|salveaza\s+piesa|salveaza\s+melodia|salveaz-o|adauga\s+la\s+favorite|pune\s+la\s+favorite|baga\s+la\s+favorite|adauga\s+la\s+preferate|pune\s+la\s+preferate|baga\s+la\s+preferate|favoriteaza|imi\s+place\s+piesa|imi\s+place\s+melodia)\b',
                clean_cmd,
                re.I
            )) or (
                any(f in clean_cmd for f in ("favorite", "fav", "favorit", "like", "salveaza", "save"))
                and any(s in clean_cmd for s in ("song", "track", "this", "piesa", "melodia", "asta", "o"))
            )
            if is_save_fav:
                cur = self.cog.current.get(self.guild_id)
                if not cur:
                    no_music_msg = "No music is currently playing." if persona == "anime" else ("No music is playing right now." if persona == "mommy" else "No track is playing right now.")
                    await play_beep_sound(guild, "error")
                    await speak_in_voice(guild, no_music_msg, persona=persona)
                    await self._notify(guild, f"❌ **[Garmin]** {user_name}: {no_music_msg}")
                    self._unlock_session()
                    return

                uid_str = str(user_id)
                if not hasattr(self.bot, "_jv_data"):
                    self.bot._jv_data = {}
                bot_favs = self.bot._jv_data.setdefault("favorites", {})
                user_list = bot_favs.setdefault(uid_str, [])

                track_id = str(cur.get("id") or cur.get("songId") or "").strip()
                track_title = str(cur.get("title") or cur.get("name") or "Untitled").strip()
                track_artist = str(cur.get("artist") or "Juice WRLD").strip()

                existing_idx = next(
                    (i for i, t in enumerate(user_list)
                     if (track_id and str(t.get("id")) == track_id)
                     or (track_title and str(t.get("title", "")).lower() == track_title.lower())),
                    None
                )
                if existing_idx is not None:
                    already_msg = f"{track_title} is already in your favorites!" if persona != "mommy" else f"This song is already in your favorites, darling."
                    await play_beep_sound(guild, "understood")
                    await speak_in_voice(guild, already_msg, persona=persona)
                    await self._notify(guild, f"❤️ **[Garmin]** {user_name}: **{track_title}** is already in your favorites! ({len(user_list)} saved)")
                    self._unlock_session()
                    return

                clean_fav = {
                    "id": cur.get("id") or track_id or track_title,
                    "title": track_title,
                    "artist": track_artist,
                    "length": cur.get("length") or "—",
                    "cover_url": cur.get("cover_url") or (f"https://api.juicevault.xyz/cdn/music/covers/{cur.get('id')}" if cur.get("id") else ""),
                    "url": cur.get("url") or cur.get("webpage_url") or "",
                    "_external": cur.get("_external", False),
                    "_source": cur.get("_source", "JuiceVault"),
                    "added_at": int(time.time()),
                }
                user_list.insert(0, clean_fav)
                bot_favs[user_name.lower()] = user_list
                if hasattr(self.cog, "web_remote") and self.cog.web_remote:
                    self.cog.web_remote._user_favorites = bot_favs
                    try:
                        await self.cog.web_remote.config.favorites.set(bot_favs)
                    except Exception:
                        pass

                count = len(user_list)
                success_speech = "Added to your favorites! You have great taste~" if persona == "anime" else ("Saved to your favorites. Good choice, darling." if persona == "mommy" else "Added to your favorites.")
                await play_beep_sound(guild, "understood")
                await speak_in_voice(guild, success_speech, persona=persona)
                await self._notify(guild, f"❤️ **[Garmin]** {user_name}: *\"{text}\"* ➔ Saved **{track_title}** by {track_artist} to favorites! ({count} saved) ⭐")
                self._unlock_session()
                return

            # PRECEDENCE 12: LEAVE / DISCONNECT
            if re.search(r'\b(?:leave|pleaca|iesi|deconecteaza|deconecteaza-te|disconnect|exit|go away|bye|goodbye)\b', clean_cmd, re.I):
                await play_chime_and_proceed(guild)
                bye_speech = "Goodbye master! Have a wonderful day~" if persona == "anime" else ("Leaving now. Behave yourself, darling." if persona == "mommy" else "Goodbye.")
                await speak_in_voice(guild, bye_speech, persona=persona)
                await self.cog.config.guild(guild).enabled.set(False)
                try:
                    await self.cog.config.guild(guild).saved_session.set(None)
                    getattr(self.bot, "_jv_data", {}).get("saved_sessions", {}).pop(self.guild_id, None)
                except Exception:
                    pass
                await self.cog._stop(self.guild_id, disconnect=True)
                self._unlock_session()
                await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Left voice channel! 👋")
                return

            # PRECEDENCE 13: HELP / COMMANDS
            if clean_cmd.strip() in {"help", "commands", "what can you do", "what can i say", "help me"}:
                help_speech = "You can ask me to play any song or artist, skip, repeat, shuffle, adjust volume, or save favorites!"
                await play_chime_and_proceed(guild)
                await speak_in_voice(guild, help_speech, persona=persona)
                self._unlock_session()
                await self._notify(guild, "💡 **[Garmin]** **Voice Commands:**\n• *„Garmin play <song or artist>”* (Juice WRLD vault or YouTube)\n• *„Garmin skip”* / *„Garmin skip 10”* / *„Garmin previous”*\n• *„Garmin pause”* / *„Garmin resume”*\n• *„Garmin shuffle”* / *„Garmin loop”* / *„Garmin restart”*\n• *„Garmin volume <1-100>”* / *„Garmin louder”* / *„Garmin mute”*\n• *„Garmin what's playing?”* / *„Garmin save this song”*\n• *„Garmin switch to mommy voice”* / *„Garmin anime voice”*")
                return

            # PRECEDENCE 14: DIRECT YOUTUBE SEARCH & PLAY
            if "youtube" in clean_cmd or " yt" in clean_cmd or clean_cmd.startswith("yt "):
                yt_q = _clean_music_query(clean_cmd)
                if not yt_q:
                    self._lock_session(user_id, duration=25.0)
                    with self._lock:
                        self._wake_windows[user_id] = now + 15.0
                    if not hasattr(self.cog, "_pending_yt_voice"):
                        self.cog._pending_yt_voice = {}
                    self.cog._pending_yt_voice[self.guild_id] = {
                        "user_id": user_id,
                        "query": "",
                        "lang": "en",
                        "expires": time.time() + 20.0,
                        "user_name": user_name,
                        "awaiting_title": True,
                    }
                    prompt_speech = "What track would you like me to search on YouTube?"
                    await speak_in_voice(guild, prompt_speech, persona=persona)
                    await play_beep_sound(guild, "listening")
                    self._buffers.pop(user_id, None)
                    self._last_speech.pop(user_id, None)
                    await self._notify(guild, f"🎤 **[Garmin]** {user_name}: {prompt_speech} ⏳")
                    return

                print(f"[JuiceVault Voice] Direct YouTube request from {user_name}: '{yt_q}'")
                self._lock_session(user_id, duration=35.0)
                await self._search_and_play_youtube(guild, yt_q, user_name, persona=persona)
                return

            # PRECEDENCE 15: GENERIC SONG SEARCH & PLAY
            play_match = re.match(
                r'^(?:canta|pune|baga|play|asculta|cauta|gaseste|search|reda|da-i play la|dai play la|da play la|da-i drumul la|dai drumul la|put\s+on|listen\s+to)\s+(?:piesa|melodia|melodie|track|song)?\s*(?:cu|de\s+la|by)?\s*(.+)$',
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
                            await self._notify(guild, f"🧠 **[Garmin]** Playing learned song: **{track_name}** 🎶")
                            return

                        # Check if query matches known external artist directly
                        is_external_artist = bool(_KNOWN_EXTERNAL_ARTISTS_REGEX.search(clean_q))

                        # 2. Search JuiceVault internal archive (skip if known external artist)
                        track = None
                        if not is_external_artist:
                            tracks = await self.cog.fetch_tracks()
                            track = _find_best_archive_track(tracks, clean_q, self.cog)

                        if track:
                            await play_chime_and_proceed(guild)
                            await self._play_track_now(guild, track)
                            self._unlock_session()
                            track_name = self.cog._track_text(track)
                            await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Playing: **{track_name}** 🎶")
                            return
                        else:
                            # 3. Not found in JuiceVault archive -> Direct YouTube playback!
                            print(f"[JuiceVault Voice] Track '{clean_q}' not in archive (external={is_external_artist}) -> Direct YouTube playback")
                            self._lock_session(user_id, duration=35.0)
                            await self._search_and_play_youtube(guild, clean_q, user_name, persona=persona)
                            return
                except Exception as e:
                    log.warning(f"[Garmin Voice Search] Error searching: {e}")

            # Feedback when recognized speech was addressed to Garmin but didn't match known command
            await play_beep_sound(guild, "error")
            self._unlock_session()
            await speak_in_voice(guild, "Command not recognized.", persona=persona)
            await self._notify(guild, f"🎤 **[Garmin]** {user_name}: *\"{text}\"* ➔ Command not recognized.")

        def _downsample_to_16k_mono(self, pcm_bytes: bytes) -> bytes:
            """Downsample Discord 48kHz 16-bit stereo PCM to 16kHz mono PCM using SIMD/NumPy when available."""
            if HAVE_NUMPY:
                try:
                    return np.frombuffer(pcm_bytes, dtype=np.int16)[0::6].tobytes()
                except Exception:
                    pass
            a = array.array('h')
            a.frombytes(pcm_bytes)
            return a[0::6].tobytes()

        async def _recognize_speech_google(self, mono_16k: bytes) -> tuple:
            """Stage 1: Completely FREE, unlimited Google STT for passive background listening.
            Consumes ZERO Groq API quota or tokens and returns with minimal latency!"""
            audio_data = sr.AudioData(mono_16k, 16000, 2)

            def _query():
                try:
                    return self._recognizer.recognize_google(audio_data, language="en-US")
                except sr.UnknownValueError:
                    return None
                except sr.RequestError as exc:
                    print(f"[JuiceVault Voice] Google STT request/quota error: {exc}")
                    return None
                except Exception as exc:
                    print(f"[JuiceVault Voice] Google STT error: {exc}")
                    return None

            loop = asyncio.get_running_loop()
            try:
                res = await asyncio.wait_for(
                    loop.run_in_executor(_VOICE_EXECUTOR, _query),
                    timeout=3.5
                )
                if res:
                    return res, "en-US"
            except Exception:
                pass
            return None, "en-US"

        async def _recognize_speech_ai(self, mono_16k: bytes, groq_key: str = None, prompt: str = None) -> tuple:
            """Stage 2: High-accuracy active STT using local fast-whisper (CPU/RAM) or Groq Whisper Large v3 Turbo.
            Called ONLY when a user actively addresses Garmin or issues a command!"""
            # 1. Local fast-whisper if available (0 API calls, 0 network, runs on CPU/RAM)
            local_model = _get_local_whisper_model()
            if local_model:
                try:
                    import io
                    wav_io = io.BytesIO(_pcm16_to_wav_bytes(mono_16k, sample_rate=16000, channels=1))
                    segments, info = await asyncio.to_thread(local_model.transcribe, wav_io, beam_size=1, language="en")
                    text = " ".join(s.text for s in segments).strip()
                    if text:
                        print(f"[JuiceVault Voice Local Whisper] ⚡ CPU: '{text}'")
                        return text, "en-US"
                except Exception as exc:
                    print(f"[JuiceVault Voice Local Whisper] Error: {exc}")

            # 2. Groq Cloud Whisper Large v3 Turbo (~60ms ultra-low latency)
            if groq_key:
                groq_text, groq_lang = await _recognize_speech_groq(mono_16k, groq_key, prompt=prompt)
                if groq_text:
                    print(f"[JuiceVault Voice Groq] ⚡ Whisper Large v3 Turbo: '{groq_text}'")
                    return groq_text, "en-US"

            # 3. Fallback to Google STT
            return await self._recognize_speech_google(mono_16k)

        async def _recognize_speech_parallel(self, pcm_bytes: bytes, preferred_lang: str = None) -> tuple:
            """Backward compatibility wrapper."""
            mono_16k = self._downsample_to_16k_mono(pcm_bytes)
            groq_key = await _get_groq_api_key(self.cog)
            return await self._recognize_speech_ai(mono_16k, groq_key=groq_key)

        def _recognize_speech_blocking(self, pcm_bytes):
            """Legacy fallback wrapper."""
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    future = asyncio.run_coroutine_threadsafe(self._recognize_speech_parallel(pcm_bytes), loop)
                    return future.result(timeout=6.0)
                return loop.run_until_complete(self._recognize_speech_parallel(pcm_bytes))
            except Exception:
                return None, "ro-RO"

        async def _notify(self, guild, message):
            """Send feedback message strictly to the active voice channel chat where the bot is connected."""
            if not guild:
                return
            try:
                target_channels = []
                voice = getattr(guild, "voice_client", None)
                # Send ONLY to the voice channel's chat where the bot and user are talking
                if voice and voice.channel and hasattr(voice.channel, "send"):
                    target_channels.append(voice.channel)
                else:
                    # Fallback ONLY if the voice channel doesn't support chat
                    if hasattr(self.cog, "config"):
                        try:
                            channel_id = await self.cog.config.guild(guild).channel_id()
                            if channel_id:
                                ch = guild.get_channel(channel_id)
                                if ch and hasattr(ch, "send"):
                                    target_channels.append(ch)
                        except Exception:
                            pass

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
    prewarm_voice_cache()
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

    existing_sink = _active_sinks.get(guild.id)
    # Check if voice is already actively listening and existing sink is alive and healthy:
    if voice.is_listening() and existing_sink is not None and existing_sink._active:
        worker = getattr(existing_sink, "_worker_task", None)
        if worker is not None and not worker.done():
            return

    # If voice was previously listening or had a stale sink, stop and clean it up cleanly:
    if hasattr(voice, "stop_listening"):
        try:
            if voice.is_listening():
                voice.stop_listening()
                time.sleep(0.04)
        except Exception:
            pass

    sink = VoiceCommandAudioSink(cog.bot, cog, guild.id)
    try:
        voice.listen(sink)
        if existing_sink and existing_sink is not sink and hasattr(existing_sink, "cleanup"):
            try:
                existing_sink.cleanup()
            except Exception:
                pass
        _active_sinks[guild.id] = sink
        print(f"[JuiceVault Voice Recognition] 🟢 ACTIVE: Listening for voice commands in '{guild.name}' (Wake Word: 'Garmin')...")
    except Exception as exc:
        print(f"[JuiceVault Voice Recognition] Sink attach note in '{guild.name}': {exc}")
        if voice.is_listening() and existing_sink:
            # Still listening with existing sink - keep it active!
            _active_sinks[guild.id] = existing_sink
            existing_sink._active = True


# Kick off background pre-warming of chimes and voice cache upon module load
try:
    prewarm_voice_cache()
except Exception:
    pass
