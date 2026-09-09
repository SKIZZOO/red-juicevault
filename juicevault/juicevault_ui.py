import asyncio
import random

import discord
from redbot.core import Config, commands


CATEGORY_LABELS = {
    "all": "All Music",
    "main": "Main",
    "cut": "Cuts",
    "cuts": "Cuts",
    "cut file": "Cut Files",
    "instrumental": "Instrumentals",
    "instrumentals": "Instrumentals",
    "remaster": "Remasters",
    "remasters": "Remasters",
    "stems": "Stems",
    "released": "Released",
    "session edits": "Session Edits",
    "unreleased": "Unreleased",
}


def category_label(value):
    value = str(value or "all").strip().casefold()
    if value in CATEGORY_LABELS:
        return CATEGORY_LABELS[value]
    return value.replace("_", " ").replace("-", " ").title() or "All Music"


class JuiceVaultCategorySelect(discord.ui.Select):
    def __init__(self, panel, guild_id, categories):
        self.panel = panel
        self.guild_id = guild_id
        options = [
            discord.SelectOption(
                label="All Music",
                value="all",
                emoji="🎵",
                description=f"{sum(categories.values())} tracks",
            )
        ]
        for name, count in sorted(categories.items()):
            if name == "all":
                continue
            if len(options) >= 25:
                break
            options.append(
                discord.SelectOption(
                    label=category_label(name)[:100],
                    value=name[:100],
                    description=f"{count} tracks"[:100],
                )
            )
        super().__init__(
            placeholder="Select a music category…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"juicevault:category_select:{guild_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.response.send_message("JuiceVault is not loaded.", ephemeral=True)
            return

        requested = cog._category_name(self.values[0])
        try:
            tracks = await cog.fetch_tracks(requested)
            if requested not in getattr(cog, "CATEGORY_URLS", {}) and requested != "all":
                resolved = cog._resolve_category(tracks, requested)
                tracks = cog._filter_tracks(tracks, resolved)
            else:
                resolved = requested

            if requested != "all" and not tracks:
                await interaction.response.send_message(
                    f"No tracks are available in **{category_label(requested)}**.",
                    ephemeral=True,
                )
                return

            await cog.config.guild(interaction.guild).category.set(resolved)
            if self.guild_id in cog.tasks:
                cog.queues[self.guild_id] = tracks
                cog.failure_counts[self.guild_id] = 0

            await interaction.response.send_message(
                f"🎚️ Category set to **{category_label(resolved)}** — `{len(tracks)}` tracks.",
                ephemeral=True,
            )
            await self.panel.update_panel(self.guild_id)
        except Exception as exc:
            await interaction.response.send_message(
                f"Unable to change category: `{type(exc).__name__}: {exc}`",
                ephemeral=True,
            )


class JuiceVaultCategoryView(discord.ui.View):
    def __init__(self, panel, guild_id, categories):
        super().__init__(timeout=60)
        self.add_item(JuiceVaultCategorySelect(panel, guild_id, categories))


class JuiceVaultPanelView(discord.ui.View):
    """Persistent JuiceVault control panel."""

    def __init__(self, panel, guild_id):
        super().__init__(timeout=None)
        self.panel = panel
        self.guild_id = guild_id
        guild = panel.bot.get_guild(guild_id)
        voice = guild.voice_client if guild else None
        paused = bool(voice and voice.is_paused())
        repeating = panel.repeat_enabled.get(guild_id, False)

        buttons = [
            ("Start", "▶️", discord.ButtonStyle.success, self._start, "start"),
            (("Resume" if paused else "Pause"), ("▶️" if paused else "⏸️"), discord.ButtonStyle.primary, self._pause, "pause"),
            ("Previous", "⏮️", discord.ButtonStyle.secondary, self._previous, "previous"),
            ("Next", "⏭️", discord.ButtonStyle.primary, self._next, "next"),
            ("Next 10", "⏩", discord.ButtonStyle.primary, self._skip10, "skip10"),
            (("Repeat ON" if repeating else "Repeat"), "🔁", discord.ButtonStyle.success if repeating else discord.ButtonStyle.secondary, self._repeat, "repeat"),
            ("Stop", "⏹️", discord.ButtonStyle.danger, self._stop, "stop"),
            ("Shuffle", "🔀", discord.ButtonStyle.secondary, self._shuffle, "shuffle"),
            ("Category", "🎚️", discord.ButtonStyle.secondary, self._category, "category"),
            ("Refresh", "🔄", discord.ButtonStyle.secondary, self._refresh, "refresh"),
        ]
        for label, emoji, style, callback, key in buttons:
            button = discord.ui.Button(
                label=label,
                emoji=emoji,
                style=style,
                custom_id=f"juicevault:{key}:{guild_id}",
            )
            button.callback = callback
            self.add_item(button)

    def _cog(self):
        return self.panel.bot.get_cog("JuiceVault")

    async def _start(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        if cog is None:
            await interaction.followup.send("JuiceVault is not loaded.", ephemeral=True)
            return
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("Join a voice channel before starting playback.", ephemeral=True)
            return

        gid = self.guild_id
        if gid in cog.tasks:
            voice = interaction.guild.voice_client
            if voice and voice.is_connected():
                await interaction.followup.send("JuiceVault is already running.", ephemeral=True)
                return
            await cog._stop(gid)

        try:
            category = await cog.config.guild(interaction.guild).category()
            all_tracks = await cog.fetch_tracks(category)
            if category not in getattr(cog, "CATEGORY_URLS", {}) and category != "all":
                category = cog._resolve_category(all_tracks, category)
                all_tracks = cog._filter_tracks(all_tracks, category)
            tracks = all_tracks
            if not tracks:
                await interaction.followup.send(
                    f"No tracks are available in **{category_label(category)}**.",
                    ephemeral=True,
                )
                return

            voice = await cog._connect(interaction.guild, interaction.user.voice.channel)
            cog.queues[gid] = tracks
            cog.manual_queues[gid] = []
            cog.stop_events[gid] = asyncio.Event()
            cog.skip_events[gid] = asyncio.Event()
            cog.skip_counts[gid] = 0
            cog.failure_counts[gid] = 0
            self.panel.history[gid] = []
            self.panel.repeat_enabled[gid] = False
            self.panel.repeat_queued[gid] = False
            self.panel.last_seen_current[gid] = None
            self.panel.last_track_snapshot[gid] = None
            self.panel.last_track_object[gid] = None
            await cog.config.guild(interaction.guild).category.set(category)
            await cog.config.guild(interaction.guild).enabled.set(True)
            await cog.config.guild(interaction.guild).channel_id.set(interaction.user.voice.channel.id)
            cog.tasks[gid] = asyncio.create_task(cog._player(interaction.guild, interaction.user.voice.channel))
            await self.panel.update_panel(gid)
            await interaction.followup.send(
                f"▶️ Started in `{voice.channel.name}` — **{category_label(category)}**.",
                ephemeral=True,
            )
        except Exception as exc:
            await interaction.followup.send(
                f"Unable to start playback: `{type(exc).__name__}: {exc}`",
                ephemeral=True,
            )

    async def _pause(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        voice = interaction.guild.voice_client
        if cog is None or self.guild_id not in cog.tasks or voice is None:
            await interaction.followup.send("The player is not running.", ephemeral=True)
            return
        if voice.is_paused():
            voice.resume()
            text = "▶️ Playback resumed."
        elif voice.is_playing():
            voice.pause()
            text = "⏸️ Playback paused."
        else:
            text = "There is no active track."
        await self.panel.update_panel(self.guild_id)
        await interaction.followup.send(text, ephemeral=True)

    async def _previous(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        voice = interaction.guild.voice_client
        history = self.panel.history.get(self.guild_id, [])
        if cog is None or self.guild_id not in cog.tasks or voice is None or not history:
            await interaction.followup.send("There is no previous track.", ephemeral=True)
            return
        previous = history.pop()
        cog.manual_queues.setdefault(self.guild_id, []).insert(0, previous)
        self.panel.repeat_queued[self.guild_id] = False
        if voice.is_playing() or voice.is_paused():
            voice.stop()
        await self.panel.update_panel(self.guild_id)
        await interaction.followup.send(
            f"⏮️ Going back to **{cog._track_text(previous)}**.",
            ephemeral=True,
        )

    async def _repeat(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        if cog is None or self.guild_id not in cog.tasks:
            await interaction.followup.send("The player is not running.", ephemeral=True)
            return
        enabled = not self.panel.repeat_enabled.get(self.guild_id, False)
        self.panel.repeat_enabled[self.guild_id] = enabled
        self.panel.repeat_queued[self.guild_id] = False
        if enabled:
            current = cog.current.get(self.guild_id)
            if current:
                cog.manual_queues.setdefault(self.guild_id, []).insert(0, dict(current, _jv_repeat_copy=True))
                self.panel.repeat_queued[self.guild_id] = True
        else:
            pending = cog.manual_queues.get(self.guild_id, [])
            cog.manual_queues[self.guild_id] = [
                track for track in pending if not track.get("_jv_repeat_copy")
            ]
        await interaction.followup.send(
            "🔁 Repeat enabled — the current track will play again."
            if enabled
            else "🔁 Repeat disabled.",
            ephemeral=True,
        )
        await self.panel.update_panel(self.guild_id)

    async def _stop(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        if cog is None:
            await interaction.followup.send("JuiceVault is not loaded.", ephemeral=True)
            return
        await cog.config.guild(interaction.guild).enabled.set(False)
        await cog._stop(self.guild_id)
        self.panel.history[self.guild_id] = []
        self.panel.repeat_enabled[self.guild_id] = False
        self.panel.repeat_queued[self.guild_id] = False
        self.panel.last_seen_current[self.guild_id] = None
        self.panel.last_track_snapshot[self.guild_id] = None
        self.panel.last_track_object[self.guild_id] = None
        await self.panel.update_panel(self.guild_id)
        await interaction.followup.send("⏹️ Playback stopped.", ephemeral=True)

    async def _next(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        if cog is None:
            await interaction.followup.send("JuiceVault is not loaded.", ephemeral=True)
            return
        if await cog._request_skip(self.guild_id, 1):
            await interaction.followup.send("⏭️ Skipped 1 track.", ephemeral=True)
        else:
            await interaction.followup.send(
                "No track is playing, or a skip is already in progress.",
                ephemeral=True,
            )
        await self.panel.update_panel(self.guild_id)

    async def _skip10(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        if cog is None:
            await interaction.followup.send("JuiceVault is not loaded.", ephemeral=True)
            return
        if await cog._request_skip(self.guild_id, 10):
            await interaction.followup.send("⏩ Skipped 10 tracks.", ephemeral=True)
        else:
            await interaction.followup.send(
                "No track is playing, or a skip is already in progress.",
                ephemeral=True,
            )
        await self.panel.update_panel(self.guild_id)

    async def _shuffle(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        if cog is None:
            await interaction.followup.send("JuiceVault is not loaded.", ephemeral=True)
            return
        queue = cog.queues.get(self.guild_id)
        if not queue:
            await interaction.followup.send("The queue is empty.", ephemeral=True)
            return
        random.shuffle(queue)
        await self.panel.update_panel(self.guild_id)
        await interaction.followup.send(
            f"🔀 Queue shuffled — `{len(queue)}` tracks.",
            ephemeral=True,
        )

    async def _category(self, interaction):
        await interaction.response.defer(ephemeral=True)
        cog = self._cog()
        if cog is None:
            await interaction.followup.send("JuiceVault is not loaded.", ephemeral=True)
            return
        try:
            categories = await cog.categories()
            await interaction.followup.send(
                "🎚️ Select a music category:",
                view=JuiceVaultCategoryView(self.panel, self.guild_id, categories),
                ephemeral=True,
            )
        except Exception as exc:
            await interaction.followup.send(
                f"Unable to load categories: `{type(exc).__name__}: {exc}`",
                ephemeral=True,
            )

    async def _refresh(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        if cog is None:
            await interaction.followup.send("JuiceVault is not loaded.", ephemeral=True)
            return
        try:
            category = await cog.config.guild(interaction.guild).category()
            tracks = await cog.fetch_tracks(category)
            if category not in getattr(cog, "CATEGORY_URLS", {}) and category != "all":
                category = cog._resolve_category(tracks, category)
                tracks = cog._filter_tracks(tracks, category)
            cog.queues[self.guild_id] = tracks
            cog.failure_counts[self.guild_id] = 0
            await self.panel.update_panel(self.guild_id)
            await interaction.followup.send(
                f"🔄 Refreshed — `{len(tracks)}` tracks in **{category_label(category)}**.",
                ephemeral=True,
            )
        except Exception as exc:
            await interaction.followup.send(
                f"Refresh failed: `{type(exc).__name__}: {exc}`",
                ephemeral=True,
            )


class JuiceVaultUI(commands.Cog):
    """Modern English Discord now-playing panel for JuiceVault."""

    PANEL_COLOR = discord.Color.from_rgb(155, 89, 182)
    CONFIG_ID = 918273646

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=self.CONFIG_ID, force_registration=True)
        self.config.register_guild(panel_channel_id=None, panel_message_id=None)
        self._task = None
        self._control_task = None
        self._restore_task = None
        self._registered_views = set()
        self.history = {}
        self.last_seen_current = {}
        self.last_track_snapshot = {}
        self.last_track_object = {}
        self.repeat_enabled = {}
        self.repeat_queued = {}

    async def cog_load(self):
        self._task = asyncio.create_task(self._panel_loop())
        self._control_task = asyncio.create_task(self._control_loop())
        self._restore_task = asyncio.create_task(self._restore_views())

    async def cog_unload(self):
        for task in (self._task, self._control_task, self._restore_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        self._task = None
        self._control_task = None
        self._restore_task = None

    async def _restore_views(self):
        await self.bot.wait_until_ready()
        for guild_id in (await self.config.all_guilds()).keys():
            if self.bot.get_guild(guild_id) is not None:
                self._register_view(guild_id)

    def _register_view(self, guild_id):
        if guild_id in self._registered_views:
            return
        self.bot.add_view(JuiceVaultPanelView(self, guild_id))
        self._registered_views.add(guild_id)

    @staticmethod
    def _track_text(track):
        if not track:
            return "No track"
        artist = str(track.get("artist") or "").strip()
        title = str(track.get("title") or track.get("name") or "").strip()
        return f"{artist} — {title}" if artist and title else title or str(track.get("file_name") or "Untitled track")

    @staticmethod
    def _cover_url(track):
        if not track:
            return None
        song_id = str(track.get("id") or "").strip()
        if song_id:
            return f"https://api.juicevault.xyz/cdn/music/covers/{song_id}"
        cover = str(track.get("cover") or "").strip()
        if cover.startswith("http://") or cover.startswith("https://"):
            return cover
        return f"https://api.juicevault.xyz/{cover.lstrip('/')}" if cover else None

    async def _make_embed(self, guild_id):
        main = self.bot.get_cog("JuiceVault")
        embed = discord.Embed(color=self.PANEL_COLOR)
        embed.set_author(name="JUICEVAULT • LIVE", icon_url="https://api.juicevault.xyz/favicon.ico")

        if main is None or guild_id not in main.tasks:
            embed.title = "Player Offline"
            embed.description = "Press **Start** or use `4jv start` to begin playback."
            embed.set_footer(text="JuiceVault Archive • 24/7 Player")
            return embed

        guild = self.bot.get_guild(guild_id)
        track = main.current.get(guild_id)
        queue_size = len(main.queues.get(guild_id, []))
        requested_size = len(main.manual_queues.get(guild_id, []))
        category = await main.config.guild(guild).category()
        voice = guild.voice_client if guild else None

        if track:
            artist = str(track.get("artist") or "JuiceVault Archive").strip()
            title = str(track.get("title") or track.get("name") or track.get("file_name") or "Untitled track").strip()
            track_category = category_label(track.get("category") or "archive")
            state = "⏸️ PAUSED" if voice and voice.is_paused() else "🔊 PLAYING"

            embed.title = "Now Playing"
            embed.description = f"### {title}\n**{artist}**\n`{state}`  •  JuiceVault Archive"
            embed.add_field(name="CATEGORY", value=track_category[:1024], inline=True)
            embed.add_field(name="LENGTH", value=str(track.get("length") or "—"), inline=True)
            embed.add_field(name="LIBRARY", value=category_label(category), inline=True)
            embed.add_field(name="REQUESTED", value=f"`{requested_size}`", inline=True)
            embed.add_field(name="QUEUE", value=f"`{queue_size}`", inline=True)
            embed.add_field(
                name="REPEAT",
                value="`ON`" if self.repeat_enabled.get(guild_id, False) else "`OFF`",
                inline=True,
            )

            cover_url = self._cover_url(track)
            if cover_url:
                embed.set_thumbnail(url=cover_url)

            play_count = track.get("play_count")
            footer = "JuiceVault Archive • 24/7"
            if play_count is not None:
                try:
                    footer = f"JuiceVault Archive • {int(play_count):,} plays • 24/7"
                except (TypeError, ValueError):
                    pass
            embed.set_footer(text=footer)
        else:
            embed.title = "Loading Next Track…"
            embed.description = "Preparing the next track from the archive."
            embed.add_field(name="LIBRARY", value=category_label(category), inline=True)
            embed.add_field(name="QUEUE", value=f"`{queue_size}`", inline=True)
            embed.set_footer(text="JuiceVault Archive • 24/7 Player")

        if voice and voice.is_connected():
            embed.add_field(name="VOICE", value=f"🔊 {voice.channel.name}", inline=False)
        return embed

    async def _get_panel_message(self, guild_id):
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return None
        settings = await self.config.guild(guild).all()
        channel_id = settings.get("panel_channel_id")
        message_id = settings.get("panel_message_id")
        target = guild.get_channel(channel_id) if channel_id else None
        if not isinstance(target, discord.TextChannel) or not message_id:
            return None
        self._register_view(guild_id)
        try:
            return await target.fetch_message(message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    async def ensure_panel(self, guild_id, channel):
        guild = self.bot.get_guild(guild_id)
        if guild is None or not isinstance(channel, discord.TextChannel):
            return None
        settings = await self.config.guild(guild).all()
        old_channel_id = settings.get("panel_channel_id")
        old_message_id = settings.get("panel_message_id")
        message = await channel.send(
            embed=await self._make_embed(guild_id),
            view=JuiceVaultPanelView(self, guild_id),
        )
        await self.config.guild(guild).panel_channel_id.set(channel.id)
        await self.config.guild(guild).panel_message_id.set(message.id)
        self._register_view(guild_id)
        if old_channel_id and old_message_id:
            old_channel = guild.get_channel(old_channel_id)
            if old_channel:
                try:
                    old_message = await old_channel.fetch_message(old_message_id)
                    if old_message.id != message.id:
                        await old_message.delete()
                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    pass
        return message

    async def update_panel(self, guild_id):
        message = await self._get_panel_message(guild_id)
        if message is None:
            return
        try:
            await message.edit(
                embed=await self._make_embed(guild_id),
                view=JuiceVaultPanelView(self, guild_id),
            )
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

    async def _control_loop(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                main = self.bot.get_cog("JuiceVault")
                if main:
                    for guild_id in list(main.tasks):
                        track = main.current.get(guild_id)
                        track_id = str(track.get("id")) if track else None
                        track_object = id(track) if track else None
                        previous_id = self.last_seen_current.get(guild_id)
                        previous_object = self.last_track_object.get(guild_id)
                        if track_id and (track_id != previous_id or track_object != previous_object):
                            if previous_id:
                                previous_track = self.last_track_snapshot.get(guild_id)
                                if previous_track:
                                    history = self.history.setdefault(guild_id, [])
                                    history.append(previous_track)
                                    del history[:-50]
                            self.last_seen_current[guild_id] = track_id
                            self.last_track_snapshot[guild_id] = dict(track)
                            self.last_track_object[guild_id] = track_object
                            if self.repeat_enabled.get(guild_id):
                                self.repeat_queued[guild_id] = True
                                main.manual_queues.setdefault(guild_id, []).insert(0, dict(track, _jv_repeat_copy=True))

                        guild = self.bot.get_guild(guild_id)
                        voice = guild.voice_client if guild else None
                        if (
                            self.repeat_enabled.get(guild_id)
                            and track
                            and voice
                            and voice.is_connected()
                            and not voice.is_playing()
                            and not voice.is_paused()
                            and not self.repeat_queued.get(guild_id)
                        ):
                            main.manual_queues.setdefault(guild_id, []).insert(0, dict(track, _jv_repeat_copy=True))
                            self.repeat_queued[guild_id] = True
                await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"[JuiceVaultUI] control loop error: {type(exc).__name__}: {exc}")
                await asyncio.sleep(2)

    async def _panel_loop(self):
        await self.bot.wait_until_ready()
        while True:
            try:
                for guild_id in (await self.config.all_guilds()).keys():
                    await self.update_panel(guild_id)
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                print(f"[JuiceVaultUI] panel update error: {type(exc).__name__}: {exc}")
                await asyncio.sleep(10)

    @commands.command(name="jvpanel", aliases=["jvui"])
    @commands.guild_only()
    async def jvpanel(self, ctx):
        if not ctx.author.guild_permissions.manage_guild:
            await ctx.send("You need the Manage Server permission to create the JuiceVault panel.")
            return
        try:
            message = await self.ensure_panel(ctx.guild.id, ctx.channel)
            if message:
                await ctx.send(
                    "✨ JuiceVault panel recreated in this channel and will update automatically.",
                    delete_after=8,
                )
            else:
                await ctx.send("❌ Unable to create the panel in this channel.")
        except (discord.Forbidden, discord.HTTPException) as exc:
            await ctx.send(f"❌ Unable to create the panel: `{type(exc).__name__}: {exc}`")
