import html
import json
import re
from urllib.parse import quote_plus

import aiohttp
import discord


def clean_song_title(title: str) -> str:
    """Clean audio file extensions, producer tags, BPM markers, and category markers for optimal lyrics lookup."""
    original = str(title or "").strip()
    clean = re.sub(r"\.(wav|mp3|m4a|flac|ogg|aac|opus)$", "", original, flags=re.I)
    clean = re.sub(r"^![^-\n]+-\s*", "", clean)
    clean = re.sub(r"-\s*\d{2,3}\s*BPM.*$", "", clean, flags=re.I)
    clean = re.sub(r"\b\d{2,3}\s*BPM.*$", "", clean, flags=re.I)
    clean = re.sub(r"\((?:stem|stems|session edit|snippet|preview|instrumental|remaster)\)", "", clean, flags=re.I)
    clean = re.sub(r"\[(?:stem|stems|session edit|snippet|preview|instrumental|remaster)\]", "", clean, flags=re.I)
    clean = clean.strip(" -_")
    return clean or original


async def get_genius_url(title: str, artist: str = "Juice WRLD", session: aiohttp.ClientSession = None) -> str:
    """Resolve the direct Genius song page URL or fallback to Genius search URL."""
    cleaned = clean_song_title(title)
    query = f"{artist} {cleaned}".strip()
    fallback_url = f"https://genius.com/search?q={quote_plus(query)}"
    search_url = f"https://genius.com/api/search/multi?q={quote_plus(query)}"

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    should_close = False
    if session is None:
        session = aiohttp.ClientSession()
        should_close = True

    try:
        async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=4)) as resp:
            if resp.status == 200:
                data = await resp.json(content_type=None)
                for section in data.get("response", {}).get("sections", []):
                    if section.get("type") == "song":
                        hits = section.get("hits", [])
                        if hits:
                            return hits[0].get("result", {}).get("url") or fallback_url
    except Exception:
        pass
    finally:
        if should_close:
            await session.close()

    return fallback_url


async def fetch_lyrics(title: str, artist: str = "Juice WRLD", session: aiohttp.ClientSession = None) -> dict:
    """Fetch lyrics from LRCLIB first, with Genius fallback and URL resolution."""
    cleaned = clean_song_title(title)
    query = f"{artist} {cleaned}".strip()
    fallback_genius = f"https://genius.com/search?q={quote_plus(query)}"

    should_close = False
    if session is None:
        session = aiohttp.ClientSession()
        should_close = True

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JuiceVault/2.0"}

    try:
        # 1. Try LRCLIB direct get
        lrclib_url = f"https://lrclib.net/api/get?artist_name={quote_plus(artist)}&track_name={quote_plus(cleaned)}"
        try:
            async with session.get(lrclib_url, headers=headers, timeout=aiohttp.ClientTimeout(total=3.5)) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    lyrics = data.get("plainLyrics")
                    if lyrics and lyrics.strip():
                        # Resolve direct Genius URL for the user link
                        genius_url = await get_genius_url(title, artist, session)
                        return {
                            "title": cleaned,
                            "artist": artist,
                            "lyrics": lyrics.strip(),
                            "source": "LRCLIB",
                            "url": genius_url or fallback_genius,
                            "found": True,
                        }
        except Exception:
            pass

        # 2. Try Genius multi search + page extraction
        genius_url = fallback_genius
        song_url = None
        search_url = f"https://genius.com/api/search/multi?q={quote_plus(query)}"
        try:
            async with session.get(search_url, headers=headers, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                if resp.status == 200:
                    search_data = await resp.json(content_type=None)
                    for section in search_data.get("response", {}).get("sections", []):
                        if section.get("type") == "song":
                            hits = section.get("hits", [])
                            if hits:
                                song_url = hits[0].get("result", {}).get("url")
                                if song_url:
                                    genius_url = song_url
                                break
        except Exception:
            pass

        if song_url:
            try:
                async with session.get(song_url, headers=headers, timeout=aiohttp.ClientTimeout(total=4.5)) as resp:
                    if resp.status == 200:
                        content = await resp.text(errors="ignore")
                        containers = re.findall(r"<div[^>]*data-lyrics-container[^>]*>(.*?)</div>", content, re.DOTALL)
                        if containers:
                            raw = "\n".join(containers)
                            raw = re.sub(r"<br\s*/?>", "\n", raw)
                            text = re.sub(r"<[^>]+>", "", raw)
                            text = html.unescape(text).strip()
                            text = re.sub(r"^\d+\s*Contributors.*?\n", "", text, flags=re.I)
                            if text:
                                return {
                                    "title": cleaned,
                                    "artist": artist,
                                    "lyrics": text.strip(),
                                    "source": "Genius",
                                    "url": song_url,
                                    "found": True,
                                }
            except Exception:
                pass

        return {
            "title": cleaned,
            "artist": artist,
            "lyrics": None,
            "source": "Genius",
            "url": genius_url,
            "found": False,
        }

    finally:
        if should_close:
            await session.close()


def split_lyrics_chunks(lyrics: str, max_chunk_size: int = 3800) -> list:
    """Split lyrics into embed-safe chunks without cutting lines in half."""
    if not lyrics:
        return []
    if len(lyrics) <= max_chunk_size:
        return [lyrics]

    chunks = []
    lines = lyrics.split("\n")
    current_chunk = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1
        if current_len + line_len > max_chunk_size and current_chunk:
            chunks.append("\n".join(current_chunk).strip())
            current_chunk = [line]
            current_len = line_len
        else:
            current_chunk.append(line)
            current_len += line_len

    if current_chunk:
        chunks.append("\n".join(current_chunk).strip())

    return chunks


def build_lyrics_embeds(
    title: str,
    artist: str,
    lyrics: str | None,
    genius_url: str,
    cover_url: str | None = None,
    color: int = 0xFF2D55,
) -> list:
    """Build polished Discord Embeds containing the lyrics."""
    cleaned = clean_song_title(title)
    if not lyrics:
        embed = discord.Embed(
            title=f"🎶 {cleaned}",
            url=genius_url,
            description=(
                f"*{artist}*\n\n"
                f"Full lyrics text could not be extracted automatically.\n"
                f"You can read the complete lyrics directly on Genius:\n"
                f"**[Click here to view on Genius]({genius_url})**"
            ),
            color=color,
        )
        if cover_url:
            embed.set_thumbnail(url=cover_url)
        embed.set_footer(text="JuiceVault Lyrics • Genius")
        return [embed]

    chunks = split_lyrics_chunks(lyrics)
    embeds = []
    total_parts = len(chunks)

    for i, chunk in enumerate(chunks):
        part_str = f" (Part {i + 1}/{total_parts})" if total_parts > 1 else ""
        embed = discord.Embed(
            title=f"🎶 {cleaned}{part_str}",
            url=genius_url,
            description=f"*{artist}*\n\n{chunk}",
            color=color,
        )
        if i == 0 and cover_url:
            embed.set_thumbnail(url=cover_url)
        footer_text = f"Juice WRLD Vault • Page {i + 1}/{total_parts} • Lyrics via Genius" if total_parts > 1 else "Juice WRLD Vault • Lyrics via Genius"
        embed.set_footer(text=footer_text)
        embeds.append(embed)

    return embeds
