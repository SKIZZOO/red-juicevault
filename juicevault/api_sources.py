import json
import random
from urllib.parse import quote

API_BASE = "https://api.juicevault.xyz"
AUDIO_EXTENSIONS = (".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac", ".webm")

# These are the public music collections documented by JuiceVault.
COLLECTION_ENDPOINTS = {
    "all": "/music/list",
    "instrumental": "/music/instrumentals/list",
    "remaster": "/music/remasters/list",
    "stems": "/music/stems/list",
    "released": "/music/released/list",
    "cut file": "/music/cuts/list",
}

ALIASES = {
    "instrumentals": "instrumental",
    "remasters": "remaster",
    "cuts": "cut file",
    "cut": "cut file",
    "session": "session edits",
    "sessions": "session edits",
    "session edit": "session edits",
    "session edits": "session edits",
    "unreleased": "unreleased",
    "main": "main",
}


def normalize_category(value):
    value = str(value or "all").strip().casefold()
    return ALIASES.get(value, value or "all")


def stream_url(song_id):
    return f"{API_BASE}/music/stream/{quote(str(song_id), safe='')}"


def normalize_tracks(payload):
    songs = payload.get("songs") if isinstance(payload, dict) else None
    if not isinstance(songs, list):
        raise RuntimeError("JuiceVault API response has no songs list")
    tracks = []
    seen = set()
    for song in songs:
        if not isinstance(song, dict):
            continue
        song_id = song.get("id")
        filename = str(song.get("file_name") or "")
        if not song_id or not filename.lower().split("?", 1)[0].endswith(AUDIO_EXTENSIONS):
            continue
        song_id = str(song_id)
        if song_id in seen:
            continue
        seen.add(song_id)
        track = dict(song)
        track["id"] = song_id
        track["url"] = stream_url(song_id)
        tracks.append(track)
    return tracks


async def fetch_collection(session, category):
    category = normalize_category(category)
    endpoint = COLLECTION_ENDPOINTS.get(category, COLLECTION_ENDPOINTS["all"])
    async with session.get(f"{API_BASE}{endpoint}") as response:
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

    tracks = normalize_tracks(payload)
    # The documentation exposes unreleased/main/session edits through song metadata,
    # not separate public collection endpoints. The search example also shows an
    # Unreleased album with category=main.
    if category == "unreleased":
        tracks = [
            t for t in tracks
            if "unreleased" in str(t.get("album") or "").casefold()
            or "unreleased" in str(t.get("category") or "").casefold()
        ]
    elif category == "main":
        tracks = [t for t in tracks if normalize_category(t.get("category")) == "main"]
    elif category == "session edits":
        tracks = [t for t in tracks if bool(t.get("is_session_edit"))]
    return tracks


async def get_category_counts(session):
    tracks = await fetch_collection(session, "all")
    counts = {}
    for track in tracks:
        category = normalize_category(track.get("category"))
        counts[category] = counts.get(category, 0) + 1
    return counts


def patch_juicevault_class(JuiceVault):
    """Use the documented collection endpoints and randomized, low-repeat refills."""
    if getattr(JuiceVault, "_jv_api_sources_patched", False):
        return

    original_init = JuiceVault.__init__
    original_player = JuiceVault._player
    original_download = JuiceVault._download_track

    def init(self, bot):
        original_init(self, bot)
        self._jv_recent_ids = []
        self._jv_task_guilds = {}

    async def fetch_tracks(self):
        await self._ensure_session()
        category = "all"
        task = __import__("asyncio").current_task()
        guild = self._jv_task_guilds.get(task)
        if guild is not None:
            category = await self.config.guild(guild).category()
        category = normalize_category(category)
        tracks = await fetch_collection(self.session, category)
        random.shuffle(tracks)

        # Prefer tracks that have not played recently. We still keep the recent
        # tracks at the back so tiny collections never become empty.
        if len(tracks) > 1 and self._jv_recent_ids:
            recent = set(self._jv_recent_ids[-75:])
            fresh = [t for t in tracks if t.get("id") not in recent]
            old = [t for t in tracks if t.get("id") in recent]
            if fresh:
                random.shuffle(fresh)
                random.shuffle(old)
                tracks = fresh + old
        return tracks

    async def fetch_category_tracks(self, category):
        await self._ensure_session()
        tracks = await fetch_collection(self.session, category)
        random.shuffle(tracks)
        return tracks

    async def get_categories(self):
        await self._ensure_session()
        return await get_category_counts(self.session)

    async def categories(self):
        return await self.get_categories()

    async def player_wrapper(self, guild, channel):
        task = __import__("asyncio").current_task()
        self._jv_task_guilds[task] = guild
        try:
            return await original_player(self, guild, channel)
        finally:
            self._jv_task_guilds.pop(task, None)

    async def download_wrapper(self, track):
        song_id = str(track.get("id") or "")
        if song_id:
            self._jv_recent_ids.append(song_id)
            if len(self._jv_recent_ids) > 250:
                del self._jv_recent_ids[:-150]
        return await original_download(self, track)

    JuiceVault.__init__ = init
    JuiceVault.fetch_tracks = fetch_tracks
    JuiceVault.fetch_category_tracks = fetch_category_tracks
    JuiceVault.get_categories = get_categories
    JuiceVault.categories = categories
    JuiceVault._player = player_wrapper
    JuiceVault._download_track = download_wrapper
    JuiceVault._jv_api_sources_patched = True
