import discord

from . import juicevault_ui as ui
from .juicevault import JuiceVault
from .juicevault_ui import category_label, JuiceVaultPanelView
from .external_search_patch import JuiceVaultOtherSearchModal


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
        state = "⏸️ PAUSED" if voice and voice.is_paused() else "🔊 PLAYING"
        embed.title = "Now Playing"

        if track.get("_external"):
            source = str(track.get("_source") or "External").strip()
            source_url = str(track.get("_webpage_url") or track.get("url") or "").strip()
            embed.description = f"**{title}**\n*{artist}*\n\n`{state}`  •  **{source}**"
            if source_url.startswith(("http://", "https://")):
                embed.url = source_url
            embed.add_field(name="🌐 SOURCE", value=f"**{source}**", inline=True)
        else:
            song_id = str(track.get("id") or "").strip()
            song_url = f"https://juicevault.xyz/music/{song_id}" if song_id else "https://juicevault.xyz/"
            embed.description = f"[{title}]({song_url})\n*{artist}*\n\n`{state}`  •  **JuiceVault Archive**"
            embed.url = song_url

        embed.add_field(name="🎚️ CATEGORY", value=f"**{category_label(track.get('category') or 'archive')}**", inline=True)
        embed.add_field(name="⏱️ LENGTH", value=f"`{track.get('length') or '—'}`", inline=True)
        embed.add_field(name="📚 LIBRARY", value=f"**{category_label(category)}**", inline=True)
        embed.add_field(name="📥 REQUESTED", value=f"`{requested_size}`", inline=True)
        embed.add_field(name="🎶 QUEUE", value=f"`{queue_size}`", inline=True)
        embed.add_field(name="🔁 REPEAT", value="`ON`" if self.repeat_enabled.get(guild_id, False) else "`OFF`", inline=True)

        if not track.get("_external"):
            cover_url = self._cover_url(track)
            if cover_url:
                embed.set_thumbnail(url=cover_url)

        plays = track.get("play_count")
        if track.get("_external"):
            footer_line = f"[JuiceVault Archive](https://juicevault.xyz/) • 24/7 • [made by SKIZZOO](https://guns.lol/skizzoo)"
        else:
            if plays is not None:
                try:
                    plays_text = f"{int(plays):,} plays"
                except (TypeError, ValueError):
                    plays_text = "plays"
            else:
                plays_text = "plays"
            footer_line = f"[JuiceVault Archive](https://juicevault.xyz/) • {plays_text} • 24/7 • [made by SKIZZOO](https://guns.lol/skizzoo)"
        embed.add_field(name="‎", value=footer_line, inline=False)
        embed.set_footer(text="JuiceVault Archive • 24/7 Player")
    else:
        embed.title = "Loading Next Track…"
        embed.description = "Preparing the next track from the archive."
        embed.add_field(name="📚 LIBRARY", value=f"**{category_label(category)}**", inline=True)
        embed.add_field(name="🎶 QUEUE", value=f"`{queue_size}`", inline=True)
        embed.add_field(name="‎", value="[JuiceVault Archive](https://juicevault.xyz/) • 24/7 • [made by SKIZZOO](https://guns.lol/skizzoo)", inline=False)
        embed.set_footer(text="JuiceVault Archive • 24/7 Player")
    if voice and voice.is_connected():
        embed.add_field(name="🔊 VOICE", value=f"`{voice.channel.name}`", inline=False)
    return embed


class JuiceVaultSearchSelect(discord.ui.Select):
    def __init__(self, panel, guild_id, tracks):
        self.panel, self.guild_id, self.tracks = panel, guild_id, tracks
        options = []
        for index, track in enumerate(tracks[:25]):
            title = str(track.get("title") or track.get("name") or track.get("file_name") or "Untitled track").strip()
            artist = str(track.get("artist") or "Unknown artist").strip()
            options.append(discord.SelectOption(label=title[:100], value=str(index), description=f"{artist} • {category_label(track.get('category') or 'archive')}"[:100], emoji="🎵"))
        super().__init__(placeholder="Select a track to add to Requested…", min_values=1, max_values=1, options=options, custom_id=f"juicevault:search_select:{guild_id}")

    async def callback(self, interaction):
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
        embed = discord.Embed(title="✅ Track Selected", description=f"**{title}**\n*{artist}*\n\nAdded directly to **Requested**.", color=self.panel.PANEL_COLOR)
        if not track.get("_external"):
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


class JuiceVaultSearchModeView(discord.ui.View):
    def __init__(self, panel, guild_id):
        super().__init__(timeout=60)
        self.panel, self.guild_id = panel, guild_id
        vault = discord.ui.Button(label="🎵 JuiceVault Search", style=discord.ButtonStyle.primary, custom_id=f"juicevault:search_vault:{guild_id}")
        external = discord.ui.Button(label="🌐 External Search", style=discord.ButtonStyle.secondary, custom_id=f"juicevault:search_external:{guild_id}")
        vault.callback = self._vault
        external.callback = self._external
        self.add_item(vault)
        self.add_item(external)

    async def _vault(self, interaction):
        await interaction.response.send_modal(JuiceVaultSearchModal(self.panel, self.guild_id))

    async def _external(self, interaction):
        await interaction.response.send_modal(JuiceVaultOtherSearchModal(self.panel, self.guild_id))


class JuiceVaultSearchModal(discord.ui.Modal, title="Search JuiceVault"):
    query = discord.ui.TextInput(label="Search the archive", placeholder="Track title, artist, filename…", min_length=1, max_length=100, required=True)

    def __init__(self, panel, guild_id):
        super().__init__(timeout=120)
        self.panel, self.guild_id = panel, guild_id

    async def on_submit(self, interaction):
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.response.send_message("JuiceVault is not loaded.", ephemeral=True)
            return
        try:
            tracks = await cog.fetch_tracks()
            query = str(self.query.value).strip()
            matches = [t for t in tracks if query.casefold() in cog._search_text(t)][:25]
        except Exception as exc:
            await interaction.response.send_message(f"Search failed: `{type(exc).__name__}: {exc}`", ephemeral=True)
            return
        if not matches:
            await interaction.response.send_message(f"No tracks found for **{query}**.", ephemeral=True)
            return
        await interaction.response.send_message(embed=discord.Embed(title="🔎 Search Results", description=f"Found **{len(matches)}** matches for **{query}**.\nSelect a track below to add it directly to Requested.", color=self.panel.PANEL_COLOR), view=JuiceVaultSearchView(self.panel, self.guild_id, matches), ephemeral=True)


async def pretty_search_command(self, ctx, *, query):
    try:
        tracks = await self.fetch_tracks()
    except Exception as exc:
        await ctx.send(f"Search failed: `{type(exc).__name__}: {exc}`")
        return
    query = str(query).strip()
    matches = [t for t in tracks if query.casefold() in self._search_text(t)][:25]
    if not matches:
        await ctx.send(f"No tracks found for **{query}**.")
        return
    self.search_results[ctx.guild.id] = matches
    ui_cog = self.bot.get_cog("JuiceVaultUI")
    if ui_cog is None:
        await ctx.send("JuiceVault UI is not loaded.")
        return
    await ctx.send(embed=discord.Embed(title="🔎 JuiceVault Search", description=f"**{query}** — `{len(matches)}` results\n\nSelect a track below to add it directly to **Requested**.", color=ui_cog.PANEL_COLOR), view=JuiceVaultSearchView(ui_cog, ctx.guild.id, matches))


async def search_button(self, interaction):
    await interaction.response.send_message(
        embed=discord.Embed(title="🔎 Search", description="Choose where you want to search for music.", color=self.panel.PANEL_COLOR),
        view=JuiceVaultSearchModeView(self.panel, self.guild_id),
        ephemeral=True,
    )


def _install_smart_controls():
    async def seek_back(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        target = await cog._request_seek(self.guild_id, -10) if cog else None
        await interaction.followup.send("There is no active track to seek." if target is None else f"⏮️ Moved back 10 seconds — `{int(target)}s`.", ephemeral=True)
        await self.panel.update_panel(self.guild_id)

    async def seek_forward(self, interaction):
        await interaction.response.defer()
        cog = self._cog()
        target = await cog._request_seek(self.guild_id, 10) if cog else None
        await interaction.followup.send("There is no active track to seek." if target is None else f"⏭️ Moved forward 10 seconds — `{int(target)}s`.", ephemeral=True)
        await self.panel.update_panel(self.guild_id)

    JuiceVaultPanelView._search = search_button
    JuiceVaultPanelView._seek_back = seek_back
    JuiceVaultPanelView._seek_forward = seek_forward

    def styled_init(self, panel, guild_id):
        discord.ui.View.__init__(self, timeout=None)
        self.panel, self.guild_id = panel, guild_id
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

        def add(label, style, callback, key, row, disabled=False):
            b = discord.ui.Button(label=label, style=style, custom_id=f"juicevault:{key}:{guild_id}", row=row, disabled=disabled)
            b.callback = callback
            self.add_item(b)

        add("🎚 Category", discord.ButtonStyle.secondary, self._category, "category", 0)
        add("🔎 Search", discord.ButtonStyle.secondary, self._search, "search", 0)
        add("🔄 Refresh", discord.ButtonStyle.secondary, self._refresh, "refresh", 0, disabled=not running)

        if not running:
            add("▶ Start", discord.ButtonStyle.success, self._start, "start", 1)
        else:
            add("⏹ Stop", discord.ButtonStyle.danger, self._stop, "stop", 1)
            add("▶ Resume" if paused else "⏸ Pause", discord.ButtonStyle.primary, self._pause, "pause", 1, disabled=not has_track)

        add("⏮ Previous", discord.ButtonStyle.secondary, self._previous, "previous", 2, disabled=not has_history)
        add("Next ⏭", discord.ButtonStyle.primary, self._next, "next", 2, disabled=not playing)
        add("🔁 Repeat ON" if repeating else "🔁 Repeat", discord.ButtonStyle.success if repeating else discord.ButtonStyle.secondary, self._repeat, "repeat", 3, disabled=not running)
        add("🔀 Shuffle", discord.ButtonStyle.secondary, self._shuffle, "shuffle", 3, disabled=not has_queue)
        add("⏮ Past 10s", discord.ButtonStyle.secondary, self._seek_back, "seek_back", 4, disabled=not (has_track and (playing or paused)))
        add("Next 10s ⏭", discord.ButtonStyle.secondary, self._seek_forward, "seek_forward", 4, disabled=not (has_track and (playing or paused)))

    JuiceVaultPanelView.__init__ = styled_init


def _panel_signature(panel, guild_id):
    main = panel.bot.get_cog("JuiceVault")
    guild = panel.bot.get_guild(guild_id)
    voice = guild.voice_client if guild else None
    track = main.current.get(guild_id) if main else None
    queue = main.queues.get(guild_id, []) if main else []
    manual = main.manual_queues.get(guild_id, []) if main else []
    category = None
    if main and guild:
        category = str(main.config.guild(guild).category) if False else None
    return (
        bool(main and guild_id in main.tasks),
        str(track.get("id")) if track else None,
        id(track) if track else None,
        bool(voice and voice.is_playing()),
        bool(voice and voice.is_paused()),
        voice.channel.id if voice and voice.is_connected() else None,
        len(queue),
        len(manual),
        panel.repeat_enabled.get(guild_id, False),
        tuple(str(item.get("id")) for item in manual[:10]),
    )


def patch_ui(JuiceVaultUI):
    JuiceVaultUI._make_embed = polished_make_embed
    _install_smart_controls()
    original_update_panel = JuiceVaultUI.update_panel
    original_ensure_panel = JuiceVaultUI.ensure_panel

    async def debounced_update_panel(self, guild_id):
        signature = _panel_signature(self, guild_id)
        if self.__dict__.setdefault("_panel_signatures", {}).get(guild_id) == signature:
            return
        await original_update_panel(self, guild_id)
        self.__dict__["_panel_signatures"][guild_id] = signature

    async def ensure_panel_with_reset(self, guild_id, channel):
        self.__dict__.setdefault("_panel_signatures", {}).pop(guild_id, None)
        return await original_ensure_panel(self, guild_id, channel)

    JuiceVaultUI.update_panel = debounced_update_panel
    JuiceVaultUI.ensure_panel = ensure_panel_with_reset
    search_command = JuiceVault.jv.all_commands.get("search")
    if search_command is not None:
        search_command.callback = pretty_search_command
    ui.JuiceVaultSearchView = JuiceVaultSearchView
    ui.JuiceVaultSearchModeView = JuiceVaultSearchModeView
