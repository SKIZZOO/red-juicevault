# -*- coding: utf-8 -*-
"""JuiceVault Mobile Web Remote & REST API server.

Provides a mobile-first Web Remote PWA with real-time WebSocket syncing,
phone lock screen / MediaSession controls, QR code pairing, and REST API
endpoints designed for iOS Shortcuts, Siri, and mobile widgets.
"""

import asyncio
import json
import os
import platform
import re
import secrets
import shutil
import socket
import ssl
import stat
import time
from urllib.parse import quote, unquote

import aiohttp
from aiohttp import web
import discord
from redbot.core import Config, commands
from redbot.core.data_manager import cog_data_path

from .web_assets import HTML_INDEX, MANIFEST_JSON, SERVICE_WORKER_JS
from .juicevault_ui import category_label, JuiceVaultPanelView
from .eq_ui_patch import EQ_OPTIONS


def get_local_ip():
    """Detect the host machine's primary local LAN IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Route lookup without sending actual network packets
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


class JuiceVaultWebRemote:
    """Embedded aiohttp web server handling the Mobile Web Remote and REST API."""

    CONFIG_ID = 918273648

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(None, identifier=self.CONFIG_ID, cog_name="JuiceVaultWebRemote", force_registration=True)
        self.config.register_global(
            enabled=True,
            host="0.0.0.0",
            port=8088,
            token=None,
            custom_url=None,
            ssl_cert=None,
            ssl_key=None,
            require_auth=True,
        )
        self.runner = None
        self.site = None
        self.ws_clients = set()
        self._server_lock = asyncio.Lock()
        self._last_state_cache = {}
        self._tunnel_proc = None
        self._tunnel_url = None

    def _get_main_cog(self):
        return self.bot.get_cog("JuiceVault")

    def _get_ui_cog(self):
        return self.bot.get_cog("JuiceVaultUI")

    async def initialize(self):
        """Ensure persistent auth token is set, then start the web server if enabled."""
        token = await self.config.token()
        if not token:
            token = secrets.token_urlsafe(12)
            await self.config.token.set(token)

        enabled = await self.config.enabled()
        if enabled:
            await self.start_server()

    async def get_public_ip(self):
        """Fetch the public WAN IP of the bot host to allow remote mobile connections."""
        if getattr(self, "_cached_public_ip", None):
            return self._cached_public_ip
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as sess:
                for endpoint in ("https://api.ipify.org", "https://icanhazip.com", "https://ifconfig.me/ip"):
                    try:
                        async with sess.get(endpoint) as r:
                            if r.status == 200:
                                text = (await r.text()).strip()
                                if text and "." in text and not text.startswith(("10.", "192.168.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.3", "127.")):
                                    self._cached_public_ip = text
                                    return text
                    except Exception:
                        continue
        except Exception:
            pass
        return None

    async def get_remote_url(self, with_token=True, prefer_public=True):
        """Return the URL used to access the web remote on mobile."""
        custom = await self.config.custom_url()
        token = await self.config.token() if with_token else ""
        token_param = f"?token={quote(token)}" if token else ""

        if custom:
            base = custom.rstrip("/")
            return f"{base}/{token_param}"

        host = await self.config.host()
        port = await self.config.port()
        cert_path = await self.config.ssl_cert()
        proto = "https" if cert_path else "http"
        local_ip = get_local_ip() if host in ("0.0.0.0", "") else host

        if prefer_public:
            public_ip = await self.get_public_ip()
            if public_ip:
                return f"{proto}://{public_ip}:{port}/{token_param}"

        return f"{proto}://{local_ip}:{port}/{token_param}"

    async def start_server(self):
        """Start or restart the aiohttp web runner and TCP site."""
        async with self._server_lock:
            await self._stop_server_internal()

            app = web.Application()
            # CORS middleware headers
            app.middlewares.append(self._cors_middleware)

            # Web App & PWA routes
            app.router.add_get("/", self._handle_index)
            app.router.add_get("/manifest.json", self._handle_manifest)
            app.router.add_get("/sw.js", self._handle_service_worker)
            app.router.add_get("/ws", self._handle_ws)

            # REST API routes (supports both GET and POST for iOS Shortcuts ease of use)
            app.router.add_get("/api/status", self._api_status)
            app.router.add_get("/api/guilds", self._api_guilds)

            # Playback controls
            for method in ("get", "post"):
                add_route = getattr(app.router, f"add_{method}")
                add_route("/api/playback/play", self._api_play)
                add_route("/api/playback/pause", self._api_pause)
                add_route("/api/playback/toggle", self._api_toggle)
                add_route("/api/playback/skip", self._api_skip)
                add_route("/api/playback/previous", self._api_previous)
                add_route("/api/playback/seek", self._api_seek)
                add_route("/api/playback/stop", self._api_stop)
                add_route("/api/playback/shuffle", self._api_shuffle)
                add_route("/api/playback/repeat", self._api_repeat)
                add_route("/api/playback/eq", self._api_eq)

            app.router.add_post("/api/category", self._api_category)
            app.router.add_get("/api/queue", self._api_queue)
            app.router.add_post("/api/queue/remove", self._api_queue_remove)
            app.router.add_post("/api/queue/play_now", self._api_queue_play_now)
            app.router.add_post("/api/queue/move_next", self._api_queue_move_next)
            app.router.add_get("/api/search", self._api_search)
            app.router.add_post("/api/queue/add", self._api_queue_add)
            app.router.add_get("/api/shortcuts", self._api_shortcuts)
            app.router.add_get("/api/stream", self._api_stream)

            host = await self.config.host()
            port = await self.config.port()
            cert_path = await self.config.ssl_cert()
            key_path = await self.config.ssl_key()

            ssl_ctx = None
            proto = "http"
            if cert_path and key_path:
                if os.path.isfile(cert_path) and os.path.isfile(key_path):
                    try:
                        import ssl
                        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                        ssl_ctx.load_cert_chain(certfile=cert_path, keyfile=key_path)
                        proto = "https"
                        print(f"[JuiceVault Web Remote] Loaded SSL certificate from {cert_path}")
                    except Exception as exc:
                        print(f"[JuiceVault Web Remote] Failed to load SSL context: {exc}")
                else:
                    print(f"[JuiceVault Web Remote] Warning: SSL cert/key file path not found ({cert_path}, {key_path})")

            self.runner = web.AppRunner(app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, host, port, ssl_context=ssl_ctx)
            try:
                await self.site.start()
                print(f"[JuiceVault Web Remote] Server running on {proto}://{host}:{port}")
            except Exception as exc:
                print(f"[JuiceVault Web Remote] Failed to bind to {host}:{port}: {exc}")

    async def _stop_server_internal(self):
        for ws in list(self.ws_clients):
            try:
                await ws.close(code=1000, message=b"Server shutting down")
            except Exception:
                pass
        self.ws_clients.clear()

        if self.site:
            try:
                await self.site.stop()
            except Exception:
                pass
            self.site = None

        if self.runner:
            try:
                await self.runner.cleanup()
            except Exception:
                pass
            self.runner = None

    async def stop_server(self):
        async with self._server_lock:
            await self._stop_server_internal()

    def generate_self_signed_cert(self, cert_path, key_path):
        """Generate a self-signed SSL certificate and private key."""
        os.makedirs(os.path.dirname(os.path.abspath(cert_path)), exist_ok=True)
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import rsa
            from cryptography.hazmat.primitives import serialization
            import datetime, ipaddress

            key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, u"JuiceVault Remote"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"JuiceVault"),
            ])
            cert = (
                x509.CertificateBuilder()
                .subject_name(subject)
                .issuer_name(issuer)
                .public_key(key.public_key())
                .serial_number(x509.random_serial_number())
                .not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1))
                .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
                .add_extension(
                    x509.SubjectAlternativeName([
                        x509.DNSName(u"localhost"),
                        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                    ]),
                    critical=False,
                )
                .sign(key, hashes.SHA256())
            )
            with open(key_path, "wb") as f:
                f.write(
                    key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )
            with open(cert_path, "wb") as f:
                f.write(cert.public_bytes(serialization.Encoding.PEM))
            return True
        except Exception as exc:
            openssl = shutil.which("openssl")
            if openssl:
                import subprocess
                cmd = [
                    openssl, "req", "-x509", "-newkey", "rsa:2048",
                    "-keyout", key_path, "-out", cert_path,
                    "-days", "3650", "-nodes", "-subj", "/CN=JuiceVault Remote"
                ]
                res = subprocess.run(cmd, capture_output=True)
                return res.returncode == 0
            print(f"[JuiceVault Web Remote] Self-signed SSL generation failed: {exc}")
            return False

    async def get_or_download_cloudflared(self):
        """Locate cloudflared executable in PATH or download standalone binary."""
        bin_in_path = shutil.which("cloudflared")
        if bin_in_path:
            return bin_in_path

        data_dir = cog_data_path(raw_name="JuiceVault")
        bin_dir = data_dir / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)

        is_win = platform.system() == "Windows"
        is_arm = "arm" in platform.machine().lower() or "aarch" in platform.machine().lower()

        if is_win:
            exe_name = "cloudflared.exe"
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        elif is_arm:
            exe_name = "cloudflared"
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
        else:
            exe_name = "cloudflared"
            url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"

        target_file = bin_dir / exe_name
        if target_file.exists():
            return str(target_file)

        print(f"[JuiceVault Web Remote] Downloading Cloudflare Quick Tunnel from {url}...")
        try:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        with open(target_file, "wb") as f:
                            f.write(content)
                        if not is_win:
                            os.chmod(target_file, os.stat(target_file).st_mode | stat.S_IEXEC)
                        print("[JuiceVault Web Remote] cloudflared downloaded successfully.")
                        return str(target_file)
        except Exception as exc:
            print(f"[JuiceVault Web Remote] Failed downloading cloudflared: {exc}")
        return None

    async def start_cloudflare_tunnel(self):
        """Launch Cloudflare Quick Tunnel and return the generated https://*.trycloudflare.com URL."""
        if self._tunnel_proc:
            try:
                self._tunnel_proc.terminate()
            except Exception:
                pass
            self._tunnel_proc = None

        bin_path = await self.get_or_download_cloudflared()
        if not bin_path:
            raise RuntimeError("Could not find or download cloudflared executable.")

        port = await self.config.port()
        cmd = [bin_path, "tunnel", "--url", f"http://127.0.0.1:{port}"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._tunnel_proc = proc

        tunnel_url = None
        for _ in range(40):
            await asyncio.sleep(0.4)
            line = await proc.stderr.readline()
            if not line:
                break
            text = line.decode("utf-8", errors="ignore")
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", text)
            if match:
                tunnel_url = match.group(0)
                break

        if tunnel_url:
            self._tunnel_url = tunnel_url
            await self.config.custom_url.set(tunnel_url)
            async def drain_stderr():
                while proc.returncode is None:
                    line = await proc.stderr.readline()
                    if not line:
                        break
            asyncio.create_task(drain_stderr())
            return tunnel_url
        raise RuntimeError("Cloudflare Quick Tunnel timed out generating public URL.")

    async def stop_cloudflare_tunnel(self):
        """Terminate active Cloudflare Quick Tunnel."""
        if self._tunnel_proc:
            try:
                self._tunnel_proc.terminate()
            except Exception:
                pass
            self._tunnel_proc = None
        self._tunnel_url = None
        await self.config.custom_url.set(None)

    @web.middleware
    async def _cors_middleware(self, request, handler):
        if request.method == "OPTIONS":
            response = web.Response(status=204)
        else:
            response = await handler(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-JuiceVault-Token"
        return response

    async def _authenticate(self, request):
        """Check if the request has a valid token."""
        require_auth = await self.config.require_auth()
        if not require_auth:
            return True

        expected_token = await self.config.token()
        if not expected_token:
            return True

        # Check query param
        token = request.query.get("token")
        # Check header
        if not token:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header[7:].strip()
            elif auth_header:
                token = auth_header.strip()
        if not token:
            token = request.headers.get("X-JuiceVault-Token", "").strip()

        if token and secrets.compare_digest(str(token), str(expected_token)):
            return True
        return False

    def _resolve_guild(self, request):
        """Find the target Discord guild for player operations."""
        main = self._get_main_cog()
        if not main:
            return None

        # Check query or body for guild_id
        target_id = request.query.get("guild_id")
        if target_id:
            try:
                guild = self.bot.get_guild(int(target_id))
                if guild:
                    return guild
            except (ValueError, TypeError):
                pass

        # Return first guild currently running playback
        for gid in main.tasks:
            g = self.bot.get_guild(gid)
            if g:
                return g

        # Fallback to any guild the bot is in
        if self.bot.guilds:
            return self.bot.guilds[0]
        return None

    async def _get_player_state(self, guild):
        """Build dictionary with comprehensive live status of the player."""
        main = self._get_main_cog()
        ui = self._get_ui_cog()
        if not main or not guild:
            return {"is_running": False, "is_playing": False, "is_paused": False}

        gid = guild.id
        is_running = gid in main.tasks
        voice = guild.voice_client
        is_playing = bool(voice and voice.is_playing())
        is_paused = bool(voice and voice.is_paused())
        track = main.current.get(gid)
        category = await main.config.guild(guild).category()

        # Parse duration & elapsed position
        duration_sec = 0.0
        position_sec = 0.0
        if track:
            duration_sec = main._parse_duration(track.get("length")) or 0.0
            base = float(main.play_positions.get(gid, 0.0))
            started = getattr(voice, "_jv_started_at", None)
            if started is not None and is_playing and not is_paused:
                base += max(0.0, time.monotonic() - started)
            position_sec = min(base, duration_sec) if duration_sec > 0 else base

        cover_url = None
        if ui and track:
            cover_url = ui._cover_url(track)
        if not cover_url and track and track.get("cover"):
            cover_url = track.get("cover")

        track_dict = None
        if track:
            track_dict = {
                "id": str(track.get("id") or ""),
                "title": str(track.get("title") or track.get("name") or track.get("file_name") or "Untitled Track"),
                "artist": str(track.get("artist") or "Juice WRLD"),
                "category": str(track.get("category") or category),
                "length": str(track.get("length") or "—"),
                "duration_seconds": round(duration_sec, 1),
                "position_seconds": round(position_sec, 1),
                "cover_url": cover_url,
                "is_external": bool(track.get("_external")),
                "source": str(track.get("_source") or "JuiceVault Archive"),
            }

        # Categories list
        categories_dict = {}
        try:
            categories_dict = await main.categories()
        except Exception:
            pass

        return {
            "guild": {"id": str(guild.id), "name": guild.name},
            "voice_channel": voice.channel.name if voice and voice.channel else None,
            "is_running": is_running,
            "is_playing": is_playing,
            "is_paused": is_paused,
            "track": track_dict,
            "category": category,
            "category_label": category_label(category),
            "categories": categories_dict,
            "queue_size": len(main.queues.get(gid, [])),
            "requested_size": len(main.manual_queues.get(gid, [])),
            "effect": main.effects.get(gid, "none"),
            "effects": [
                {"id": val, "label": label, "desc": desc}
                for val, label, desc in EQ_OPTIONS
            ],
            "repeat": bool(ui and ui.repeat_enabled.get(gid, False)),
            "has_history": bool(ui and ui.history.get(gid)),
        }

    async def broadcast_state(self, guild_id=None):
        """Push real-time state to all active WebSocket clients."""
        if not self.ws_clients:
            return

        guild = None
        if guild_id:
            guild = self.bot.get_guild(guild_id)
        if not guild:
            main = self._get_main_cog()
            if main and main.tasks:
                guild = self.bot.get_guild(next(iter(main.tasks)))
        if not guild and self.bot.guilds:
            guild = self.bot.guilds[0]

        if not guild:
            return

        state = await self._get_player_state(guild)
        message = json.dumps({"type": "state_update", "data": state})
        for ws in list(self.ws_clients):
            try:
                await ws.send_str(message)
            except Exception:
                self.ws_clients.discard(ws)

    # Web App Route Handlers
    async def _handle_index(self, request):
        return web.Response(text=HTML_INDEX, content_type="text/html", charset="utf-8")

    async def _handle_manifest(self, request):
        return web.Response(text=MANIFEST_JSON, content_type="application/manifest+json")

    async def _handle_service_worker(self, request):
        return web.Response(text=SERVICE_WORKER_JS, content_type="application/javascript")

    async def _handle_ws(self, request):
        if not await self._authenticate(request):
            return web.Response(status=401, text="Unauthorized")

        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self.ws_clients.add(ws)

        guild = self._resolve_guild(request)
        if guild:
            state = await self._get_player_state(guild)
            await ws.send_str(json.dumps({"type": "state_update", "data": state}))

        try:
            async for msg in ws:
                if msg.type == web.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        action_name = data.get("action")
                        await self._dispatch_ws_action(ws, guild, action_name, data)
                    except Exception as err:
                        await ws.send_str(json.dumps({"type": "toast", "message": f"Error: {err}"}))
                elif msg.type == web.WSMsgType.ERROR:
                    break
        finally:
            self.ws_clients.discard(ws)

        return ws

    async def _dispatch_ws_action(self, ws, guild, action_name, payload):
        main = self._get_main_cog()
        ui = self._get_ui_cog()
        if not main or not guild:
            return

        gid = guild.id
        voice = guild.voice_client

        if action_name == "toggle":
            if voice and voice.is_playing():
                voice.pause()
            elif voice and voice.is_paused():
                voice.resume()
            elif gid not in main.tasks:
                # Start if not running
                channel_id = await main.config.guild(guild).channel_id()
                channel = guild.get_channel(channel_id) if channel_id else None
                if not channel and guild.voice_channels:
                    channel = guild.voice_channels[0]
                if channel:
                    category = await main.config.guild(guild).category()
                    tracks = await main.fetch_tracks(category)
                    main.queues[gid] = tracks
                    main.manual_queues[gid] = []
                    main.stop_events[gid] = asyncio.Event()
                    main.skip_events[gid] = asyncio.Event()
                    main.seek_events[gid] = asyncio.Event()
                    main.skip_counts[gid] = 0
                    main.effects[gid] = "none"
                    await main.config.guild(guild).enabled.set(True)
                    await main.config.guild(guild).channel_id.set(channel.id)
                    main.tasks[gid] = asyncio.create_task(main._player(guild, channel))
        elif action_name == "play":
            if voice and voice.is_paused():
                voice.resume()
        elif action_name == "pause":
            if voice and voice.is_playing():
                voice.pause()
        elif action_name == "skip":
            count = int(payload.get("count", 1))
            await main._request_skip(gid, count)
        elif action_name == "previous":
            if ui:
                history = ui.history.get(gid, [])
                if history:
                    prev = history.pop()
                    main.manual_queues.setdefault(gid, []).insert(0, prev)
                    ui.repeat_queued[gid] = False
                    if voice and (voice.is_playing() or voice.is_paused()):
                        voice.stop()
        elif action_name == "seek":
            delta = float(payload.get("delta", 10))
            await main._request_seek(gid, delta)
        elif action_name == "seek_to":
            pos = float(payload.get("position", 0))
            base = float(main.play_positions.get(gid, 0.0))
            started = getattr(voice, "_jv_started_at", None)
            if started is not None and voice and voice.is_playing() and not voice.is_paused():
                base += max(0.0, time.monotonic() - started)
            delta = pos - base
            await main._request_seek(gid, delta)
        elif action_name == "shuffle":
            queue = main.queues.get(gid)
            if queue:
                import random
                random.shuffle(queue)
                if hasattr(main, "_cleanup_prefetch"):
                    main._cleanup_prefetch()
                if hasattr(main, "_trigger_next_prefetch"):
                    main._trigger_next_prefetch(gid)
        elif action_name == "repeat":
            if ui:
                new_state = not ui.repeat_enabled.get(gid, False)
                ui.repeat_enabled[gid] = new_state
                ui.repeat_queued[gid] = False
                current = main.current.get(gid)
                if new_state and current:
                    main.manual_queues.setdefault(gid, []).insert(0, dict(current, _jv_repeat_copy=True))
                    ui.repeat_queued[gid] = True
                elif not new_state:
                    main.manual_queues[gid] = [t for t in main.manual_queues.get(gid, []) if not t.get("_jv_repeat_copy")]
        elif action_name == "stop":
            await main.config.guild(guild).enabled.set(False)
            await main._stop(gid)
            if ui:
                ui.history[gid] = []
                ui.repeat_enabled[gid] = False
                ui.repeat_queued[gid] = False
        elif action_name == "set_eq":
            effect = payload.get("effect", "none")
            main.effects[gid] = effect
            if main.current.get(gid):
                await main._request_seek(gid, 0.0)
        elif action_name == "set_category":
            cat = main._category_name(payload.get("category", "all"))
            await main.config.guild(guild).category.set(cat)
            tracks = await main.fetch_tracks(cat)
            if cat not in main.CATEGORY_URLS:
                tracks = main._filter_tracks(tracks, cat)
            if gid in main.tasks:
                main.queues[gid] = tracks
                main.failure_counts[gid] = 0

        await self.broadcast_state(gid)
        if ui:
            asyncio.create_task(ui.update_panel(gid))

    # REST API Handlers
    async def _api_status(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        state = await self._get_player_state(guild)
        return web.json_response({"success": True, "state": state})

    async def _api_guilds(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        main = self._get_main_cog()
        guilds = []
        for g in self.bot.guilds:
            guilds.append({
                "id": str(g.id),
                "name": g.name,
                "is_active": bool(main and g.id in main.tasks),
            })
        return web.json_response({"success": True, "guilds": guilds})

    async def _api_play(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        voice = guild.voice_client
        if voice and voice.is_paused():
            voice.resume()
            await self.broadcast_state(guild.id)
            return web.json_response({"success": True, "message": "Playback resumed"})
        return web.json_response({"success": True, "message": "Already playing or player idle"})

    async def _api_pause(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        voice = guild.voice_client
        if voice and voice.is_playing():
            voice.pause()
            await self.broadcast_state(guild.id)
            return web.json_response({"success": True, "message": "Playback paused"})
        return web.json_response({"success": True, "message": "Already paused or not playing"})

    async def _api_toggle(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        await self._dispatch_ws_action(None, guild, "toggle", {})
        return web.json_response({"success": True, "message": "Toggled playback"})

    async def _api_skip(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        count = 1
        if request.query.get("count"):
            try:
                count = int(request.query.get("count"))
            except ValueError:
                pass
        elif request.can_read_body:
            try:
                data = await request.json()
                count = int(data.get("count", 1))
            except Exception:
                pass
        main = self._get_main_cog()
        skipped = await main._request_skip(guild.id, count)
        await self.broadcast_state(guild.id)
        return web.json_response({"success": skipped, "message": f"Skipped {count} track(s)" if skipped else "Unable to skip"})

    async def _api_previous(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        await self._dispatch_ws_action(None, guild, "previous", {})
        return web.json_response({"success": True, "message": "Going back to previous track"})

    async def _api_seek(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        delta = 10.0
        if request.query.get("delta"):
            try:
                delta = float(request.query.get("delta"))
            except ValueError:
                pass
        elif request.can_read_body:
            try:
                data = await request.json()
                delta = float(data.get("delta", 10.0))
            except Exception:
                pass
        main = self._get_main_cog()
        res = await main._request_seek(guild.id, delta)
        await self.broadcast_state(guild.id)
        return web.json_response({"success": res is not None, "target": res})

    async def _api_stop(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        await self._dispatch_ws_action(None, guild, "stop", {})
        return web.json_response({"success": True, "message": "Playback stopped"})

    async def _api_shuffle(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        await self._dispatch_ws_action(None, guild, "shuffle", {})
        return web.json_response({"success": True, "message": "Queue shuffled"})

    async def _api_repeat(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        await self._dispatch_ws_action(None, guild, "repeat", {})
        return web.json_response({"success": True, "message": "Repeat toggled"})

    async def _api_eq(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        effect = request.query.get("effect")
        if not effect and request.can_read_body:
            try:
                data = await request.json()
                effect = data.get("effect")
            except Exception:
                pass
        effect = effect or "none"
        await self._dispatch_ws_action(None, guild, "set_eq", {"effect": effect})
        return web.json_response({"success": True, "effect": effect})

    async def _api_category(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        data = await request.json()
        cat = data.get("category", "all")
        await self._dispatch_ws_action(None, guild, "set_category", {"category": cat})
        return web.json_response({"success": True, "category": cat})

    async def _api_queue(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        main = self._get_main_cog()
        gid = guild.id
        return web.json_response({
            "success": True,
            "current": main.current.get(gid),
            "requested": main.manual_queues.get(gid, []),
            "upcoming": main.queues.get(gid, [])[:30],
        })

    async def _api_queue_remove(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        data = await request.json()
        target_type = str(data.get("type", "requested")).lower()
        idx = int(data.get("index", 0))
        main = self._get_main_cog()
        gid = guild.id

        if target_type == "upcoming":
            q = main.queues.get(gid, [])
            if 0 <= idx < len(q):
                removed = q.pop(idx)
                await self.broadcast_state(gid)
                return web.json_response({"success": True, "removed": removed})
        else:
            manual = main.manual_queues.get(gid, [])
            if 0 <= idx < len(manual):
                removed = manual.pop(idx)
                await self.broadcast_state(gid)
                return web.json_response({"success": True, "removed": removed})
        return web.json_response({"error": "Index out of range"}, status=400)

    async def _api_queue_play_now(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        data = await request.json()
        target_type = str(data.get("type", "upcoming")).lower()
        idx = int(data.get("index", 0))
        main = self._get_main_cog()
        gid = guild.id

        track = None
        if target_type == "requested":
            manual = main.manual_queues.get(gid, [])
            if 0 <= idx < len(manual):
                track = manual.pop(idx)
        else:
            q = main.queues.get(gid, [])
            if 0 <= idx < len(q):
                track = q.pop(idx)

        if not track:
            return web.json_response({"error": "Track not found"}, status=400)

        main.manual_queues.setdefault(gid, []).insert(0, track)
        voice = guild.voice_client
        if voice and (voice.is_playing() or voice.is_paused()):
            voice.stop()

        await self.broadcast_state(gid)
        title = track.get("title") or track.get("name") or "Track"
        return web.json_response({"success": True, "message": f"Playing now: {title}"})

    async def _api_queue_move_next(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        data = await request.json()
        target_type = str(data.get("type", "upcoming")).lower()
        idx = int(data.get("index", 0))
        main = self._get_main_cog()
        gid = guild.id

        track = None
        if target_type == "requested":
            manual = main.manual_queues.get(gid, [])
            if 0 <= idx < len(manual):
                track = manual.pop(idx)
        else:
            q = main.queues.get(gid, [])
            if 0 <= idx < len(q):
                track = q.pop(idx)

        if not track:
            return web.json_response({"error": "Track not found"}, status=400)

        main.manual_queues.setdefault(gid, []).insert(0, track)
        await self.broadcast_state(gid)
        title = track.get("title") or track.get("name") or "Track"
        return web.json_response({"success": True, "message": f"Moved to play next: {title}"})

    async def _api_search(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        query = request.query.get("q", "").strip()
        source = request.query.get("source", "vault").lower()
        if not query:
            return web.json_response({"results": []})

        main = self._get_main_cog()
        results = []

        if source == "vault":
            tracks = await main.fetch_tracks("all")
            matches = [t for t in tracks if query.casefold() in main._search_text(t)][:20]
            for t in matches:
                results.append({
                    "id": str(t.get("id")),
                    "title": str(t.get("title") or t.get("name") or t.get("file_name")),
                    "artist": str(t.get("artist") or "Juice WRLD"),
                    "length": str(t.get("length") or "—"),
                    "category": str(t.get("category") or "archive"),
                    "cover_url": f"https://api.juicevault.xyz/cdn/music/covers/{t.get('id')}",
                    "_external": False,
                })
        else:
            from .external_search_patch import _extract_search, _source_name
            try:
                info = await asyncio.to_thread(_extract_search, query)
                title = str(info.get("title") or info.get("fulltitle") or query).strip()
                artist = str(info.get("artist") or info.get("uploader") or info.get("channel") or "Unknown artist").strip()
                source_name = str(info.get("_source") or _source_name(info)).strip()
                url = info.get("webpage_url") or info.get("original_url") or info.get("url")
                results.append({
                    "id": f"external:{info.get('id') or abs(hash(query))}",
                    "title": title,
                    "artist": artist,
                    "length": str(info.get("duration_string") or info.get("duration") or "—"),
                    "cover_url": info.get("thumbnail"),
                    "url": url,
                    "_external": True,
                    "_source": source_name,
                    "_webpage_url": url,
                    "_query": query,
                })
            except Exception as exc:
                return web.json_response({"results": [], "error": str(exc)})

        return web.json_response({"success": True, "results": results})

    async def _api_queue_add(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        guild = self._resolve_guild(request)
        if not guild:
            return web.json_response({"error": "No guild found"}, status=404)
        data = await request.json()
        track = data.get("track")
        if not track:
            return web.json_response({"error": "Missing track data"}, status=400)

        main = self._get_main_cog()
        gid = guild.id
        if gid not in main.tasks:
            return web.json_response({"error": "Player is offline. Start the player first."}, status=400)

        main.manual_queues.setdefault(gid, []).insert(0, track)
        ui = self._get_ui_cog()
        if ui:
            await ui.update_panel(gid)
        await self.broadcast_state(gid)
        return web.json_response({"success": True, "message": f"Added '{track.get('title')}' to Requested queue!"})

    async def _api_shortcuts(self, request):
        if not await self._authenticate(request):
            return web.json_response({"error": "Unauthorized"}, status=401)
        base = (await self.get_remote_url(with_token=False)).rstrip("/")
        token = await self.config.token()
        t = f"?token={quote(token)}"
        return web.json_response({
            "shortcuts": [
                {"name": "Toggle Play/Pause", "url": f"{base}/api/playback/toggle{t}"},
                {"name": "Next Track", "url": f"{base}/api/playback/skip{t}"},
                {"name": "Previous Track", "url": f"{base}/api/playback/previous{t}"},
                {"name": "Skip 10s Forward", "url": f"{base}/api/playback/seek{t}&delta=10"},
                {"name": "Rewind 10s", "url": f"{base}/api/playback/seek{t}&delta=-10"},
                {"name": "Stop Playback", "url": f"{base}/api/playback/stop{t}"},
                {"name": "Shuffle Queue", "url": f"{base}/api/playback/shuffle{t}"},
            ]
        })

    async def _api_stream(self, request):
        """Stream current playing audio track live to the browser with Range request support."""
        if not await self._authenticate(request):
            return web.Response(status=401, text="Unauthorized")
        guild = self._resolve_guild(request)
        if not guild:
            return web.Response(status=404, text="No active guild")
        main = self._get_main_cog()
        gid = guild.id
        current_file = getattr(main, "current_files", {}).get(gid)
        if not current_file or not os.path.isfile(current_file):
            return web.Response(status=404, text="No track currently playing")

        return web.FileResponse(
            current_file,
            headers={
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache",
                "Content-Type": "audio/mpeg",
            },
        )


    async def send_remote_embed(self, ctx):
        token = await self.config.token()
        port = await self.config.port()
        host = await self.config.host()
        custom = await self.config.custom_url()
        cert_path = await self.config.ssl_cert()
        proto = "https" if cert_path else "http"
        local_ip = get_local_ip() if host in ("0.0.0.0", "") else host
        public_ip = await self.get_public_ip()

        token_param = f"?token={quote(token)}" if token else ""
        local_url = f"{proto}://{local_ip}:{port}/{token_param}"
        public_url = f"{proto}://{public_ip}:{port}/{token_param}" if public_ip else None
        custom_url = f"{custom.rstrip('/')}/{token_param}" if custom else None

        primary_url = custom_url or public_url or local_url
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=260x260&margin=10&format=png&data={quote(primary_url)}"

        vc = ctx.guild.voice_client if ctx.guild else None
        vc_name = vc.channel.name if vc and vc.channel else "Not connected"

        lines = [
            "Control playback, queues, EQ, search, and lock screen media directly from your phone!\n",
            f"🔗 **Primary Phone Link:**\n[**Open JuiceVault Remote**]({primary_url})\n",
        ]
        if public_url and local_url != public_url and not custom_url:
            lines.append(f"🌐 **Public IP:** `http://{public_ip}:{port}/`")
            lines.append(f"🏠 **Local/Subnet IP:** `http://{local_ip}:{port}/`\n")

        lines.append("📷 **Scan the QR Code** with your phone's camera:")

        embed = discord.Embed(
            title="📱 JuiceVault Mobile Web Remote",
            description="\n".join(lines),
            color=discord.Color.from_rgb(155, 89, 182),
        )
        embed.set_image(url=qr_api_url)
        embed.add_field(name="🔑 Auth Token", value=f"`{token}`", inline=True)
        embed.add_field(name="🌐 Port", value=f"`{port}`", inline=True)
        embed.add_field(name="🔊 Voice Channel", value=f"`{vc_name}`", inline=True)
        embed.add_field(
            name="🔒 Free HTTPS Options (No Cert Needed)",
            value=(
                "• **1-Click Cloudflare HTTPS (Recommended):** `4jv remote tunnel` (Instant trusted SSL, 0 config!)\n"
                "• **Direct HTTPS on Open Port:** `4jv remote https on` (Auto-generates self-signed SSL cert)\n"
                "• **Custom Domain:** `4jv remote url <url>` | **Stop Tunnel:** `4jv remote tunnel stop`"
            ),
            inline=False,
        )
        embed.set_footer(text="JuiceVault 24/7 • made by SKIZZOO", icon_url="https://api.juicevault.xyz/favicon.ico")

        await ctx.send(embed=embed)


def patch_web_remote(JuiceVault, JuiceVaultUI):
    """Integrate Web Remote lifecycle, Discord panel button, and state broadcasting."""

    original_init = JuiceVault.__init__
    original_cog_load = JuiceVault.cog_load
    original_cog_unload = JuiceVault.cog_unload

    def jv_init(self, bot):
        original_init(self, bot)
        self.web_remote = JuiceVaultWebRemote(bot)

    async def jv_cog_load(self):
        await original_cog_load(self)
        await self.web_remote.initialize()

    async def jv_cog_unload(self):
        if hasattr(self, "web_remote") and self.web_remote:
            await self.web_remote.stop_server()
        await original_cog_unload(self)

    JuiceVault.__init__ = jv_init
    JuiceVault.cog_load = jv_load = jv_cog_load
    JuiceVault.cog_unload = jv_cog_unload

    # 3. Add ephemeral '📱 Remote' button callback to JuiceVaultPanelView
    async def _remote_button_callback(self, interaction: discord.Interaction):
        cog = self.panel.bot.get_cog("JuiceVault")
        if not cog or not hasattr(cog, "web_remote"):
            await interaction.response.send_message("Web Remote is not available.", ephemeral=True)
            return

        remote = cog.web_remote
        url = await remote.get_remote_url(with_token=True)
        token = await remote.config.token()
        qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=260x260&margin=10&format=png&data={quote(url)}"

        embed = discord.Embed(
            title="📱 JuiceVault Mobile Web Remote",
            description=(
                f"Tap the link below or scan the QR code to open the controller on your phone:\n\n"
                f"🔗 [**Open JuiceVault Phone Controller**]({url})\n\n"
                f"*(This message is private to you)*"
            ),
            color=self.panel.PANEL_COLOR,
        )
        embed.set_image(url=qr_api_url)
        embed.add_field(name="🔑 Auth Token", value=f"`{token}`", inline=True)
        embed.add_field(name="💡 Add to Home Screen", value="Tap 'Add to Home Screen' in Safari or Chrome for a full-screen app!", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    JuiceVaultPanelView._remote = _remote_button_callback

    # Hook button into eq_ui_patch's final_init
    original_panel_init = JuiceVaultPanelView.__init__

    def patched_panel_init(self, panel, guild_id):
        original_panel_init(self, panel, guild_id)
        # Check if remote button already added
        has_remote = any(getattr(item, "custom_id", "") == f"juicevault:remote:{guild_id}" for item in self.children)
        if not has_remote:
            remote_btn = discord.ui.Button(
                label="📱 Remote",
                style=discord.ButtonStyle.secondary,
                custom_id=f"juicevault:remote:{guild_id}",
                row=3,
            )
            remote_btn.callback = self._remote
            self.add_item(remote_btn)

    JuiceVaultPanelView.__init__ = patched_panel_init

    # 4. Broadcast state updates whenever the Discord UI panel updates
    original_update_panel = JuiceVaultUI.update_panel

    async def broadcast_on_panel_update(self, guild_id):
        await original_update_panel(self, guild_id)
        main = self.bot.get_cog("JuiceVault")
        if main and hasattr(main, "web_remote"):
            asyncio.create_task(main.web_remote.broadcast_state(guild_id))

    JuiceVaultUI.update_panel = broadcast_on_panel_update
