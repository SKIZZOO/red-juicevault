import asyncio
import os
import shutil
import tempfile

import discord

from .juicevault import JuiceVault

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


SOURCE_SEARCHES = (
    ("YouTube", "ytsearch1:{query}"),
    ("SoundCloud", "scsearch1:{query}"),
    ("Bandcamp", "bcsearch1:{query}"),
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


def _extract_search(query):
    if yt_dlp is None:
        raise RuntimeError("yt-dlp is not installed")
    opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True, "extract_flat": True, "default_search": "auto"}
    targets = [("Web", query)] if query.startswith(("http://", "https://")) else list(SOURCE_SEARCHES)
    for source, target in targets:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(target.format(query=query), download=False)
            entries = info.get("entries") if isinstance(info, dict) else None
            result = next((entry for entry in (entries or []) if entry), info if info else None)
            if result:
                result = dict(result)
                result["_source"] = _source_name(result, source)
                result["webpage_url"] = result.get("webpage_url") or result.get("url")
                return result
        except Exception:
            continue
    raise RuntimeError("No result found on YouTube, SoundCloud, Bandcamp, or the supplied URL.")


def _download_external(info):
    if yt_dlp is None:
        raise RuntimeError("yt-dlp is not installed")
    url = info.get("webpage_url") or info.get("original_url") or info.get("url")
    if not url:
        raise RuntimeError("The selected source did not provide a playable URL")
    tempdir = tempfile.mkdtemp(prefix="juicevault-external-")
    outtmpl = os.path.join(tempdir, "%(id)s.%(ext)s")
    opts = {"quiet": True, "no_warnings": True, "noplaylist": True, "format": "bestaudio/best", "outtmpl": outtmpl, "restrictfilenames": True, "overwrites": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            downloaded = ydl.extract_info(url, download=True)
            prepared = ydl.prepare_filename(downloaded)
        if os.path.isfile(prepared):
            return prepared
        files = [os.path.join(tempdir, name) for name in os.listdir(tempdir)]
        files = [path for path in files if os.path.isfile(path) and not path.endswith(".part")]
        if not files:
            raise RuntimeError("yt-dlp finished without producing an audio file")
        return files[0]
    except Exception:
        shutil.rmtree(tempdir, ignore_errors=True)
        raise


class JuiceVaultOtherSearchModal(discord.ui.Modal, title="Search Music Online"):
    query = discord.ui.TextInput(label="Song name", placeholder="Artist + song title…", min_length=1, max_length=120, required=True)

    def __init__(self, panel, guild_id):
        super().__init__(timeout=120)
        self.panel, self.guild_id = panel, guild_id

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
            title = str(info.get("title") or info.get("fulltitle") or query).strip()
            artist = str(info.get("artist") or info.get("uploader") or info.get("channel") or "Unknown artist").strip()
            source = str(info.get("_source") or _source_name(info)).strip()
            url = info.get("webpage_url") or info.get("original_url") or info.get("url")
            track = {"id": f"external:{info.get('id') or abs(hash(query))}", "title": title, "artist": artist, "length": info.get("duration_string") or info.get("duration") or "—", "file_name": f"external-{info.get('id') or 'track'}.webm", "url": url, "_external": True, "_source": source, "_webpage_url": url}
            cog.manual_queues.setdefault(self.guild_id, []).insert(0, track)
            await interaction.followup.send(embed=discord.Embed(title="🌐 External Search • Queued Next", description=f"**{title}**\n*{artist}*\n\n**Source:** `{source}`\n**Position:** `Next`", color=self.panel.PANEL_COLOR), ephemeral=True)
            await self.panel.update_panel(self.guild_id)
        except Exception as exc:
            await interaction.followup.send(f"❌ Online search failed: `{type(exc).__name__}: {exc}`", ephemeral=True)


def patch_external_search():
    if getattr(JuiceVault, "_jv_external_download_patched", False):
        return
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
        parent = os.path.dirname(path)
        try:
            original_remove(path)
        finally:
            if os.path.basename(parent).startswith("juicevault-external-"):
                shutil.rmtree(parent, ignore_errors=True)

    JuiceVault._download_track = download_track
    JuiceVault._remove_file = remove_file
    JuiceVault._jv_external_download_patched = True
