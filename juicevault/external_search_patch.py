import asyncio
import os
import shutil
import tempfile

import discord

from .juicevault import JuiceVault
from .juicevault_ui import JuiceVaultPanelView, JuiceVaultUI

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


SOURCE_SEARCHES = (
    ("YouTube", "ytsearch5:{query}"),
    ("SoundCloud", "scsearch5:{query}"),
    ("Bandcamp", "bcsearch5:{query}"),
)


def _source_name(info, fallback="Web"):
    key = str(info.get("extractor_key") or info.get("extractor") or "").casefold()
    if "youtube" in key:
        return "YouTube"
    if "soundcloud" in key:
        return "SoundCloud"
    if "bandcamp" in key:
        return "Bandcamp"
    return str(info.get("extractor") or fallback)


def _format_seconds(seconds):
    if not seconds or not isinstance(seconds, (int, float)):
        return "—"
    s = int(seconds)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _parse_entry(entry, default_source="Web", info_context=None):
    if not isinstance(entry, dict):
        return None
    info_context = info_context or {}
    source = _source_name(entry, default_source)
    entry_id = str(entry.get("id") or "")

    url = (
        entry.get("webpage_url")
        or entry.get("original_url")
        or entry.get("permalink_url")
        or (entry.get("url") if str(entry.get("url", "")).startswith("http") else None)
    )
    if not url and entry_id:
        if "youtube" in source.casefold() or "youtu" in str(info_context.get("webpage_url", "")).casefold():
            url = f"https://www.youtube.com/watch?v={entry_id}"
        elif "soundcloud" in source.casefold():
            url = entry.get("url") or str(entry_id)
        else:
            url = entry.get("url") or f"https://www.youtube.com/watch?v={entry_id}"

    title = str(entry.get("title") or entry.get("fulltitle") or "Unknown Track").strip()
    artist = str(
        entry.get("artist")
        or entry.get("uploader")
        or entry.get("channel")
        or info_context.get("uploader")
        or info_context.get("channel")
        or "Unknown artist"
    ).strip()

    dur = entry.get("duration_string") or _format_seconds(entry.get("duration"))
    thumb = entry.get("thumbnail")
    if not thumb and isinstance(entry.get("thumbnails"), list) and entry["thumbnails"]:
        thumb = entry["thumbnails"][-1].get("url")

    track_id = f"external:{entry_id or abs(hash(url or title))}"
    return {
        "id": track_id,
        "title": title,
        "artist": artist,
        "length": dur or "—",
        "file_name": f"external-{entry_id or 'track'}.webm",
        "url": url,
        "cover_url": thumb,
        "_external": True,
        "_source": source,
        "_webpage_url": url,
        "_query": url or title,
    }


def _extract_search(query, skip_sources=(), max_playlist_items=100):
    if yt_dlp is None:
        raise RuntimeError("yt-dlp is not installed")

    is_url = query.startswith(("http://", "https://"))
    is_playlist_candidate = is_url and any(
        token in query.lower()
        for token in ("list=", "/playlist", "/sets/", "/album/", "/albums/")
    )

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": not is_playlist_candidate,
        "extract_flat": True,
        "default_search": "auto",
        "playlistend": max_playlist_items if is_playlist_candidate else 5,
    }
    skipped = {str(item).casefold() for item in skip_sources}
    targets = (
        [("Web", query)]
        if is_url
        else [
            ("YouTube", "ytsearch5:{query}"),
            ("SoundCloud", "scsearch5:{query}"),
            ("Bandcamp", "bcsearch5:{query}"),
        ]
    )

    for source, target in targets:
        if source.casefold() in skipped:
            continue
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(target.format(query=query), download=False)
            if not info or not isinstance(info, dict):
                continue

            raw_entries = info.get("entries")
            if raw_entries is not None and not isinstance(raw_entries, list):
                try:
                    raw_entries = list(raw_entries)
                except Exception:
                    raw_entries = []

            # Check if this should be treated as an external playlist
            is_playlist = is_url and (
                is_playlist_candidate
                or (info.get("_type") == "playlist" and raw_entries and len(raw_entries) > 1)
            )

            if is_playlist and raw_entries:
                parsed_entries = []
                pl_source = _source_name(info, source)
                for entry in raw_entries:
                    parsed = _parse_entry(entry, default_source=pl_source, info_context=info)
                    if parsed:
                        parsed_entries.append(parsed)
                        if len(parsed_entries) >= max_playlist_items:
                            break

                if parsed_entries:
                    pl_title = str(info.get("title") or "Online Playlist").strip()
                    pl_uploader = str(
                        info.get("uploader")
                        or info.get("channel")
                        or info.get("artist")
                        or pl_source
                    ).strip()
                    return {
                        "_is_playlist": True,
                        "title": pl_title,
                        "artist": pl_uploader,
                        "uploader": pl_uploader,
                        "_source": pl_source,
                        "entries": parsed_entries,
                        "count": len(parsed_entries),
                        "webpage_url": info.get("webpage_url") or query,
                    }

            # Single track from URL or search query with multiple results
            if raw_entries:
                parsed_list = []
                for entry in raw_entries:
                    p = _parse_entry(entry, default_source=source, info_context=info)
                    if p:
                        parsed_list.append(p)
                if parsed_list:
                    first = parsed_list[0]
                    first["_search_results"] = parsed_list
                    return first

            # Direct single info without entries
            single = _parse_entry(info, default_source=source, info_context=info)
            if single:
                single["_search_results"] = [single]
                return single

        except Exception:
            continue

    raise RuntimeError("No result found on YouTube, SoundCloud, Bandcamp, or the supplied URL.")


def _download_with_ytdlp(url, tempdir):
    outtmpl = os.path.join(tempdir, "%(id)s.%(ext)s")
    base = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "outtmpl": outtmpl,
        "restrictfilenames": True,
        "overwrites": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    attempts = [
        base,
        {**base, "extractor_args": {"youtube": {"player_client": ["android"]}}},
        {**base, "extractor_args": {"youtube": {"player_client": ["web_safari"]}}},
    ]
    last_error = None
    for opts in attempts:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                downloaded = ydl.extract_info(url, download=True)
                prepared = ydl.prepare_filename(downloaded)
            if os.path.isfile(prepared):
                return prepared
            files = [os.path.join(tempdir, name) for name in os.listdir(tempdir)]
            files = [path for path in files if os.path.isfile(path) and not path.endswith(".part")]
            if files:
                return files[0]
            last_error = RuntimeError("yt-dlp finished without producing an audio file")
        except Exception as exc:
            last_error = exc
    raise last_error or RuntimeError("External download failed")


def _download_external(info):
    if yt_dlp is None:
        raise RuntimeError("yt-dlp is not installed")
    url = info.get("webpage_url") or info.get("original_url") or info.get("url")
    if not url:
        raise RuntimeError("The selected source did not provide a playable URL")

    tempdir = tempfile.mkdtemp(prefix="juicevault-external-")
    try:
        try:
            return _download_with_ytdlp(url, tempdir)
        except Exception as first_error:
            query = str(info.get("_query") or info.get("title") or "").strip()
            source = str(info.get("_source") or "").casefold()
            if query and source == "youtube":
                fallback = _extract_search(query, skip_sources=("YouTube",))
                fallback_url = fallback.get("webpage_url") or fallback.get("original_url") or fallback.get("url")
                if fallback_url:
                    path = _download_with_ytdlp(fallback_url, tempdir)
                    info["_source"] = _source_name(fallback, "Web")
                    info["_webpage_url"] = fallback_url
                    info["url"] = fallback_url
                    return path
            raise first_error
    except Exception:
        shutil.rmtree(tempdir, ignore_errors=True)
        raise


async def _open_search(self, interaction):
    await interaction.response.send_message(
        "Choose where you want to search:",
        view=JuiceVaultSearchModeView(self.panel, self.guild_id),
        ephemeral=True,
    )


class JuiceVaultSearchModeView(discord.ui.View):
    def __init__(self, panel, guild_id):
        super().__init__(timeout=120)
        self.panel = panel
        self.guild_id = guild_id

        vault = discord.ui.Button(
            label="JuiceVault Search",
            emoji="🎵",
            style=discord.ButtonStyle.primary,
            custom_id=f"juicevault:search_mode_vault:{guild_id}",
        )
        external = discord.ui.Button(
            label="External Search",
            emoji="🌐",
            style=discord.ButtonStyle.secondary,
            custom_id=f"juicevault:search_mode_external:{guild_id}",
        )
        vault.callback = self._vault
        external.callback = self._external
        self.add_item(vault)
        self.add_item(external)

    async def _vault(self, interaction):
        from .ui_patch import JuiceVaultSearchModal
        await interaction.response.send_modal(JuiceVaultSearchModal(self.panel, self.guild_id))

    async def _external(self, interaction):
        if yt_dlp is None:
            await interaction.response.send_message(
                "External Search is unavailable because **yt-dlp** is not installed.",
                ephemeral=True,
            )
            return
        await interaction.response.send_modal(JuiceVaultOtherSearchModal(self.panel, self.guild_id))


class JuiceVaultOtherSearchModal(discord.ui.Modal, title="Search Music Online"):
    query = discord.ui.TextInput(
        label="Song name or Playlist URL",
        placeholder="Artist + song title, or YouTube/SoundCloud playlist URL…",
        min_length=1,
        max_length=400,
        required=True,
    )

    def __init__(self, panel, guild_id):
        super().__init__(timeout=120)
        self.panel = panel
        self.guild_id = guild_id

    async def on_submit(self, interaction):
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.response.send_message("JuiceVault is not loaded.", ephemeral=True)
            return
        if self.guild_id not in cog.tasks:
            await interaction.response.send_message("The player is not running. Use `4jv start` first.", ephemeral=True)
            return
        query = str(self.query.value).strip()
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            info = await asyncio.to_thread(_extract_search, query)
            if info.get("_is_playlist"):
                entries = info.get("entries") or []
                if not entries:
                    await interaction.followup.send("❌ No playable tracks found in this playlist.", ephemeral=True)
                    return
                queue = cog.manual_queues.setdefault(self.guild_id, [])
                for i, track in enumerate(entries):
                    queue.insert(i, track)

                pl_title = str(info.get("title") or "Playlist").strip()
                pl_uploader = str(info.get("uploader") or info.get("artist") or "Online").strip()
                source = str(info.get("_source") or "Online").strip()
                count = len(entries)

                embed = discord.Embed(
                    title="🌐 External Playlist • Queued",
                    description=(
                        f"**{pl_title}**\n*{pl_uploader}*\n\n"
                        f"**Source:** `{source}`\n"
                        f"**Tracks Added:** `{count}`\n"
                        "**Position:** `Next in Queue`\n\n"
                        "Each track will be streamed/downloaded when it reaches playback."
                    ),
                    color=self.panel.PANEL_COLOR,
                )
                if entries[0].get("cover_url"):
                    embed.set_thumbnail(url=entries[0]["cover_url"])

                await interaction.followup.send(embed=embed, ephemeral=True)
                await self.panel.update_panel(self.guild_id)
                return

            title = str(info.get("title") or info.get("fulltitle") or query).strip()
            artist = str(info.get("artist") or info.get("uploader") or info.get("channel") or "Unknown artist").strip()
            source = str(info.get("_source") or _source_name(info)).strip()
            url = info.get("webpage_url") or info.get("original_url") or info.get("url")
            dur = info.get("length") or info.get("duration_string") or _format_seconds(info.get("duration")) or "—"
            track = {
                "id": f"external:{info.get('id') or abs(hash(query))}",
                "title": title,
                "artist": artist,
                "length": dur,
                "file_name": f"external-{info.get('id') or 'track'}.webm",
                "url": url,
                "_external": True,
                "_source": source,
                "_webpage_url": url,
                "_query": query,
            }
            if info.get("cover_url"):
                track["cover_url"] = info["cover_url"]
            cog.manual_queues.setdefault(self.guild_id, []).insert(0, track)
            embed = discord.Embed(
                title="🌐 External Search • Queued Next",
                description=(
                    f"**{title}**\n*{artist}*\n\n"
                    f"**Source:** `{source}`\n"
                    "**Position:** `Next`\n\n"
                    "The track will be downloaded when it reaches playback."
                ),
                color=self.panel.PANEL_COLOR,
            )
            if info.get("cover_url"):
                embed.set_thumbnail(url=info["cover_url"])
            await interaction.followup.send(embed=embed, ephemeral=True)
            await self.panel.update_panel(self.guild_id)
        except Exception as exc:
            await interaction.followup.send(
                f"❌ Online search failed: `{type(exc).__name__}: {exc}`",
                ephemeral=True,
            )


def patch_external_search():
    JuiceVaultPanelView._search = _open_search

    original_download = JuiceVault._download_track
    original_remove = JuiceVault._remove_file

    async def download_track(self, track):
        if track.get("_external"):
            return await asyncio.to_thread(_download_external, track)
        return await original_download(self, track)

    @staticmethod
    def remove_file(path):
        if not path:
            return
        if "juicevault_soundboard" in path:
            return
        parent = os.path.dirname(path)
        try:
            original_remove(path)
        finally:
            if os.path.basename(parent).startswith("juicevault-external-"):
                shutil.rmtree(parent, ignore_errors=True)

    JuiceVault._download_track = download_track
    JuiceVault._remove_file = remove_file

    # Keep VOICE directly under the Now Playing / PLAYING section.
    original_make_embed = JuiceVaultUI._make_embed

    async def make_embed_with_voice_under_playing(self, guild_id):
        embed = await original_make_embed(self, guild_id)
        for index, field in enumerate(list(embed.fields)):
            if field.name == "🔊 VOICE":
                name, value, inline = field.name, field.value, field.inline
                embed.remove_field(index)
                embed.insert_field_at(0, name=name, value=value, inline=inline)
                break
        return embed

    JuiceVaultUI._make_embed = make_embed_with_voice_under_playing
