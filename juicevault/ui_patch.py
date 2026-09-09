import discord

from . import juicevault_ui as ui
from .juicevault import JuiceVault
from .juicevault_ui import category_label, JuiceVaultPanelView


async def polished_make_embed(self, guild_id):
    main = self.bot.get_cog("JuiceVault")
    embed = discord.Embed(color=self.PANEL_COLOR)
    embed.set_author(name="🎵 JUICEVAULT • LIVE")

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
        embed.description = f"**{title}**\n*{artist}*\n\n`{state}`  •  **JuiceVault Archive**"
        embed.add_field(name="🎚️ CATEGORY", value=f"**{track_category[:1024]}**", inline=True)
        embed.add_field(name="⏱️ LENGTH", value=f"`{track.get('length') or '—'}`", inline=True)
        embed.add_field(name="📚 LIBRARY", value=f"**{category_label(category)}**", inline=True)
        embed.add_field(name="📥 REQUESTED", value=f"`{requested_size}`", inline=True)
        embed.add_field(name="🎶 QUEUE", value=f"`{queue_size}`", inline=True)
        embed.add_field(name="🔁 REPEAT", value="`ON`" if self.repeat_enabled.get(guild_id, False) else "`OFF`", inline=True)
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
        embed.add_field(name="📚 LIBRARY", value=f"**{category_label(category)}**", inline=True)
        embed.add_field(name="🎶 QUEUE", value=f"`{queue_size}`", inline=True)
        embed.set_footer(text="JuiceVault Archive • 24/7 Player")

    if voice and voice.is_connected():
        embed.add_field(name="🔊 VOICE", value=f"`{voice.channel.name}`", inline=False)
    return embed


class JuiceVaultSearchSelect(discord.ui.Select):
    def __init__(self, panel, guild_id, tracks):
        self.panel = panel
        self.guild_id = guild_id
        self.tracks = tracks
        options = []
        for index, track in enumerate(tracks[:25]):
            title = str(track.get("title") or track.get("name") or track.get("file_name") or "Untitled track").strip()
            artist = str(track.get("artist") or "Unknown artist").strip()
            category = category_label(track.get("category") or "archive")
            options.append(
                discord.SelectOption(
                    label=title[:100],
                    value=str(index),
                    description=f"{artist} • {category}"[:100],
                    emoji="🎵",
                )
            )
        super().__init__(
            placeholder="Select a track to add to Requested…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"juicevault:search_select:{guild_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.response.send_message("JuiceVault is not loaded.", ephemeral=True)
            return
        track = self.tracks[int(self.values[0])]
        if self.guild_id not in cog.tasks:
            await interaction.response.send_message("The player is not running. Use `4jv start` first.", ephemeral=True)
            return

        cog.manual_queues.setdefault(self.guild_id, []).append(track)
        title = str(track.get("title") or track.get("name") or track.get("file_name") or "Untitled track")
        artist = str(track.get("artist") or "Unknown artist")
        embed = discord.Embed(
            title="✅ Track Selected",
            description=f"**{title}**\n*{artist}*\n\nAdded directly to **Requested**.",
            color=self.panel.PANEL_COLOR,
        )
        cover_url = self.panel._cover_url(track)
        if cover_url:
            embed.set_thumbnail(url=cover_url)
        embed.set_footer(text="Search result selected • queued for playback")
        await interaction.response.edit_message(content="", embed=embed, view=None)
        await self.panel.update_panel(self.guild_id)


class JuiceVaultSearchView(discord.ui.View):
    def __init__(self, panel, guild_id, tracks):
        super().__init__(timeout=120)
        self.add_item(JuiceVaultSearchSelect(panel, guild_id, tracks))


class JuiceVaultSearchModal(discord.ui.Modal, title="Search JuiceVault"):
    query = discord.ui.TextInput(
        label="Search the archive",
        placeholder="Track title, artist, filename…",
        min_length=1,
        max_length=100,
        required=True,
    )

    def __init__(self, panel, guild_id):
        super().__init__(timeout=120)
        self.panel = panel
        self.guild_id = guild_id

    async def on_submit(self, interaction: discord.Interaction):
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.response.send_message("JuiceVault is not loaded.", ephemeral=True)
            return
        try:
            tracks = await cog.fetch_tracks()
            query = str(self.query.value).strip().casefold()
            matches = [track for track in tracks if query in cog._search_text(track)][:25]
        except Exception as exc:
            await interaction.response.send_message(f"Search failed: `{type(exc).__name__}: {exc}`", ephemeral=True)
            return
        if not matches:
            await interaction.response.send_message(f"No tracks found for **{self.query.value.strip()}**.", ephemeral=True)
            return
        embed = discord.Embed(
            title="🔎 Search Results",
            description=f"Found **{len(matches)}** matches for **{self.query.value.strip()}**.\nSelect a track below to add it directly to Requested.",
            color=self.panel.PANEL_COLOR,
        )
        await interaction.response.send_message(
            embed=embed,
            view=JuiceVaultSearchView(self.panel, self.guild_id, matches),
            ephemeral=True,
        )


async def pretty_search_command(self, ctx, *, query):
    try:
        tracks = await self.fetch_tracks()
    except Exception as exc:
        await ctx.send(f"Search failed: `{type(exc).__name__}: {exc}`")
        return

    query = str(query).strip()
    matches = [track for track in tracks if query.casefold() in self._search_text(track)][:25]
    if not matches:
        await ctx.send(f"No tracks found for **{query}**.")
        return

    self.search_results[ctx.guild.id] = matches
    ui_cog = self.bot.get_cog("JuiceVaultUI")
    if ui_cog is None:
        await ctx.send("JuiceVault UI is not loaded.")
        return

    embed = discord.Embed(
        title="🔎 JuiceVault Search",
        description=f"**{query}** — `{len(matches)}` results\n\nSelect a track below to add it directly to **Requested**.",
        color=ui_cog.PANEL_COLOR,
    )
    await ctx.send(embed=embed, view=JuiceVaultSearchView(ui_cog, ctx.guild.id, matches))


def _install_smart_controls():
    async def search(self, interaction):
        await interaction.response.send_modal(JuiceVaultSearchModal(self.panel, self.guild_id))

    async def seek_back(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        if cog is None:
            await interaction.followup.send("JuiceVault is not loaded.", ephemeral=True)
            return
        target = await cog._request_seek(self.guild_id, -10)
        if target is None:
            await interaction.followup.send("There is no active track to seek.", ephemeral=True)
        else:
            await interaction.followup.send(f"⏮️ Moved back 10 seconds — `{int(target)}s`.", ephemeral=True)
        await self.panel.update_panel(self.guild_id)

    async def seek_forward(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        if cog is None:
            await interaction.followup.send("JuiceVault is not loaded.", ephemeral=True)
            return
        target = await cog._request_seek(self.guild_id, 10)
        if target is None:
            await interaction.followup.send("There is no active track to seek.", ephemeral=True)
        else:
            await interaction.followup.send(f"⏭️ Moved forward 10 seconds — `{int(target)}s`.", ephemeral=True)
        await self.panel.update_panel(self.guild_id)

    JuiceVaultPanelView._search = search
    JuiceVaultPanelView._seek_back = seek_back
    JuiceVaultPanelView._seek_forward = seek_forward

    def styled_init(self, panel, guild_id):
        discord.ui.View.__init__(self, timeout=None)
        self.panel = panel
        self.guild_id = guild_id

        guild = panel.bot.get_guild(guild_id)
        voice = guild.voice_client if guild else None
        cog = panel.bot.get_cog("JuiceVault")
        running = bool(cog and guild_id in cog.tasks)
        playing = bool(voice and voice.is_playing())
        paused = bool(voice and voice.is_paused())
        has_track = bool(cog and cog.current.get(guild_id))
        has_history = bool(panel.history.get(guild_id))
        has_queue = bool(cog and cog.queues.get(guild_id))
        repeating = panel.repeat_enabled.get(guild_id, False)

        def add(label, style, callback, key, row, *, disabled=False):
            button = discord.ui.Button(
                label=label,
                style=style,
                custom_id=f"juicevault:{key}:{guild_id}",
                row=row,
                disabled=disabled,
            )
            button.callback = callback
            self.add_item(button)

        # Row 0 — only the controls that make sense for the current state.
        if not running:
            add("▶ Start", discord.ButtonStyle.success, self._start, "start", 0)
        else:
            add("▶ Resume" if paused else "⏸ Pause", discord.ButtonStyle.primary, self._pause, "pause", 0, disabled=not has_track)
            add("⏮ Previous", discord.ButtonStyle.secondary, self._previous, "previous", 0, disabled=not has_history)
            add("Next ⏭", discord.ButtonStyle.primary, self._next, "next", 0, disabled=not playing)

        # Row 1 — seeking and queue controls.
        add("⏮ Past 10s", discord.ButtonStyle.secondary, self._seek_back, "seek_back", 1, disabled=not (has_track and (playing or paused)))
        add("Next 10s ⏭", discord.ButtonStyle.secondary, self._seek_forward, "seek_forward", 1, disabled=not (has_track and (playing or paused)))
        add("Next 10 ⏩", discord.ButtonStyle.primary, self._skip10, "skip10", 1, disabled=not playing)
        add("🔁 Repeat ON" if repeating else "🔁 Repeat", discord.ButtonStyle.success if repeating else discord.ButtonStyle.secondary, self._repeat, "repeat", 1, disabled=not running)
        if running:
            add("⏹ Stop", discord.ButtonStyle.danger, self._stop, "stop", 1)
        else:
            # Keep the row balanced without exposing an irrelevant Stop action.
            add("Shuffle", discord.ButtonStyle.secondary, self._shuffle, "shuffle", 1, disabled=True)

        # Row 2 — library and discovery tools.
        add("🎚 Category", discord.ButtonStyle.secondary, self._category, "category", 2)
        add("🔎 Search", discord.ButtonStyle.secondary, self._search, "search", 2)
        add("🔄 Refresh", discord.ButtonStyle.secondary, self._refresh, "refresh", 2, disabled=not running)

        # Row 3 — shuffle stays available while the player is running.
        if running:
            add("🔀 Shuffle", discord.ButtonStyle.secondary, self._shuffle, "shuffle", 3, disabled=not has_queue)

    JuiceVaultPanelView.__init__ = styled_init


def patch_ui(JuiceVaultUI):
    JuiceVaultUI._make_embed = polished_make_embed
    _install_smart_controls()

    search_command = JuiceVault.jv.all_commands.get("search")
    if search_command is not None:
        search_command.callback = pretty_search_command

    ui.JuiceVaultSearchView = JuiceVaultSearchView
