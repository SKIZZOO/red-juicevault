import asyncio
import json
import os
import random
import tempfile
import time
from urllib.parse import quote

API_BASE = "https://api.juicevault.xyz"
AUDIO_EXTENSIONS = (".mp3", ".m4a", ".aac", ".ogg", ".opus", ".wav", ".flac", ".webm")

COLLECTION_ENDPOINTS = {
    "all": "/music/list",
    "instrumental": "/music/instrumentals/list",
    "instrumentals": "/music/instrumentals/list",
    "remaster": "/music/remasters/list",
    "remasters": "/music/remasters/list",
    "stems": "/music/stems/list",
    "stem": "/music/stems/list",
    "released": "/music/released/list",
    "cut": "/music/cuts/list",
    "cuts": "/music/cuts/list",
}

ALIASES = {
    "instrumentals": "instrumental",
    "remasters": "remaster",
    "cuts": "cut",
    "cut file": "cut",
    "cut files": "cut",
    "session": "session edits",
    "sessions": "session edits",
    "session edit": "session edits",
    "session edits": "session edits",
    "unreleased": "unreleased",
    "main": "main",
    "stem": "stems",
    "stems": "stems",
}

# ── Disk cache ──────────────────────────────────────────────────────────────
_CACHE_DIR = os.path.join(tempfile.gettempdir(), "juicevault_track_cache")
os.makedirs(_CACHE_DIR, exist_ok=True)


def _cache_path(category: str) -> str:
    safe = category.replace(" ", "_").replace("/", "_")
    return os.path.join(_CACHE_DIR, f"tracks_{safe}.json")


def _write_disk_cache(category: str, tracks: list) -> None:
    try:
        path = _cache_path(category)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"saved_at": time.time(), "tracks": tracks}, f)
        os.replace(tmp, path)
    except Exception as exc:
        print(f"[JuiceVault] cache write failed ({category}): {exc}")


def _read_disk_cache(category: str):
    """Return cached tracks list or None."""
    try:
        path = _cache_path(category)
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tracks = data.get("tracks")
        if isinstance(tracks, list) and tracks:
            age_h = (time.time() - float(data.get("saved_at", 0))) / 3600
            print(f"[JuiceVault] Using offline cache for '{category}' "
                  f"({len(tracks)} tracks, cached {age_h:.1f}h ago).")
            return tracks
    except Exception as exc:
        print(f"[JuiceVault] cache read failed ({category}): {exc}")
    return None


# ── Helpers ─────────────────────────────────────────────────────────────────

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


def _is_api_error_status(status: int) -> bool:
    """Return True for statuses that indicate a server/proxy outage."""
    return status >= 500 or status in (408, 429)


# ── fetch_collection with offline fallback ───────────────────────────────────

async def fetch_collection(session, category):
    category = normalize_category(category)
    endpoint = COLLECTION_ENDPOINTS.get(category, COLLECTION_ENDPOINTS["all"])
    url = f"{API_BASE}{endpoint}"

    # ── Try live API ──
    try:
        async with session.get(url) as response:
            text = await response.text(errors="ignore")
            status = response.status
    except Exception as exc:
        # Network-level failure (timeout, DNS, connection reset, etc.)
        print(f"[JuiceVault] Network error fetching '{category}': {type(exc).__name__}: {exc}")
        cached = _read_disk_cache(category)
        if cached is not None:
            return cached
        raise RuntimeError(
            f"JuiceVault API is unreachable and no offline cache exists for '{category}'. "
            "Please wait for the API server to come back online."
        ) from exc

    if status != 200:
        if _is_api_error_status(status):
            # Server-side / Cloudflare outage — try cache before raising
            print(f"[JuiceVault] API returned HTTP {status} for '{category}', trying offline cache.")
            cached = _read_disk_cache(category)
            if cached is not None:
                return cached
            raise RuntimeError(
                f"JuiceVault API is temporarily down (HTTP {status}). "
                "No offline cache is available yet — please wait for the server to recover."
            )
        # 4xx client errors — surface a clean message (no raw HTML)
        try:
            payload = json.loads(text)
            detail = payload.get("error", text[:300]) if isinstance(payload, dict) else text[:300]
        except json.JSONDecodeError:
            detail = text[:300]
        # Strip HTML tags from Cloudflare error pages
        if "<html" in detail.lower():
            detail = f"HTTP {status} (Cloudflare/proxy error)"
        raise RuntimeError(f"JuiceVault API HTTP {status}: {detail}")

    # ── Parse JSON ──
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise RuntimeError("JuiceVault API returned invalid JSON") from exc

    tracks = normalize_tracks(payload)

    # Category-specific filtering
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

    # ── Persist to disk cache on every successful fetch ──
    if tracks:
        _write_disk_cache(category, tracks)

    return tracks


# ── Category counts ──────────────────────────────────────────────────────────

async def get_category_counts(session):
    tracks = await fetch_collection(session, "all")
    counts = {}
    counts["all"] = len(tracks)

    session_edits_count = 0
    for track in tracks:
        category = normalize_category(track.get("category"))
        if category != "all":
            counts[category] = counts.get(category, 0) + 1
        if bool(track.get("is_session_edit")):
            session_edits_count += 1

    if session_edits_count:
        counts["session edits"] = session_edits_count

    if "stem" in counts and "stems" not in counts:
        counts["stems"] = counts.pop("stem")

    try:
        cut_tracks = await fetch_collection(session, "cut")
        if cut_tracks:
            counts["cut"] = len(cut_tracks)
    except Exception as exc:
        print(f"[JuiceVault] category endpoint cut failed: {exc}")

    return counts


# ── Class patcher ────────────────────────────────────────────────────────────

def patch_juicevault_class(JuiceVault):
    """Use documented collection endpoints with safe session recovery and offline caching."""
    if getattr(JuiceVault, "_jv_api_sources_patched", False):
        return

    original_init = JuiceVault.__init__
    original_player = JuiceVault._player
    original_download = JuiceVault._download_track

    def init(self, bot):
        original_init(self, bot)
        self._jv_recent_ids = []
        self._jv_task_guilds = {}

    async def collection(self, category):
        """Fetch a collection with session recovery and offline cache fallback."""
        for attempt in range(2):
            session = await self._ensure_session()
            try:
                return await fetch_collection(session, category)
            except RuntimeError as exc:
                if "session is closed" not in str(exc).casefold() or attempt:
                    raise
                # Previous cog instance closed its session during reload.
                self.session = None
                await asyncio.sleep(0.05)
        raise RuntimeError("JuiceVault API session is closed")

    async def fetch_tracks(self, category=None):
        if category is None:
            tracks = await collection(self, "all")
            try:
                cut_tracks = await collection(self, "cut")
                seen = {str(t.get("id")) for t in tracks}
                tracks.extend(t for t in cut_tracks if str(t.get("id")) not in seen)
            except Exception as exc:
                print(f"[JuiceVault] cut collection fetch failed: {exc}")
            category = "all"
        else:
            category = normalize_category(category)
            tracks = await collection(self, category)

        task = asyncio.current_task()
        guild = self._jv_task_guilds.get(task)
        if guild is not None and category == "all":
            player_category = normalize_category(await self.config.guild(guild).category())
            if player_category != "all":
                tracks = await collection(self, player_category)
                category = player_category

        random.shuffle(tracks)
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
        tracks = await collection(self, category)
        random.shuffle(tracks)
        return tracks

    async def get_categories(self):
        for attempt in range(2):
            session = await self._ensure_session()
            try:
                return await get_category_counts(session)
            except RuntimeError as exc:
                if "session is closed" not in str(exc).casefold() or attempt:
                    raise
                self.session = None
                await asyncio.sleep(0.05)
        raise RuntimeError("JuiceVault API session is closed")

    async def categories(self):
        return await self.get_categories()

    async def player_wrapper(self, guild, channel):
        task = asyncio.current_task()
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
