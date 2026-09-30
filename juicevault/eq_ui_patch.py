import discord
from urllib.parse import quote_plus

from .juicevault_ui import JuiceVaultPanelView
from .lyrics import (
    build_lyrics_embeds,
    clean_song_title,
    fetch_lyrics,
    get_genius_url,
)


EQ_OPTIONS = [
    ("none", "Flat", "Original unprocessed studio sound"),
    ("bass", "Bass Boost", "Deep punchy bass boost (+11dB)"),
    ("8d", "8D Audio", "360° rotating spatial surround sound"),
    ("nightcore", "Nightcore", "High pitch and accelerated tempo (+22%)"),
    ("slowed", "Slowed & Reverb", "Deep pitched chopped & slowed lo-fi"),
    ("echo", "Echo & Reverb", "Spacious delay and echo ambiance"),
    ("wide", "Stereo Wide", "Immersive 3D stereo stage expansion"),
    ("virtual bass", "Sub-Bass Boost", "Massive low-end rumble (+16dB)"),
]


class JuiceVaultEQSelect(discord.ui.Select):
    def __init__(self, panel, guild_id):
        self.panel = panel
        self.guild_id = guild_id
        options = [
            discord.SelectOption(label=label, value=value, description=description[:100])
            for value, label, description in EQ_OPTIONS
        ]
        super().__init__(
            placeholder="Choose an EQ / audio effect…",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"juicevault:eq_select:{guild_id}",
        )

    async def callback(self, interaction: discord.Interaction):
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.response.send_message("JuiceVault is not loaded.", ephemeral=True)
            return
        effect = self.values[0]
        cog.effects[self.guild_id] = effect
        restarted = False
        if cog.current.get(self.guild_id):
            restarted = await cog._request_seek(self.guild_id, 0.0) is not None
        label = next((label for value, label, _ in EQ_OPTIONS if value == effect), effect)
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🎚️ EQ / Audio Effect",
                description=f"**{label}**\n\n" + (
                    "Applied seamlessly to current playback."
                    if restarted
                    else "Selected — it will apply to the next playback."
                ),
                color=self.panel.PANEL_COLOR,
            ),
            view=None,
        )
        await self.panel.update_panel(self.guild_id)


class JuiceVaultEQView(discord.ui.View):
    def __init__(self, panel, guild_id):
        super().__init__(timeout=60)
        self.add_item(JuiceVaultEQSelect(panel, guild_id))


async def eq_button(self, interaction):
    await interaction.response.send_message(
        embed=discord.Embed(
            title="🎚️ EQ / Audio Effects",
            description="Choose an audio profile for JuiceVault.",
            color=self.panel.PANEL_COLOR,
        ),
        view=JuiceVaultEQView(self.panel, self.guild_id),
        ephemeral=True,
    )


async def send_lyrics_to_channel(interaction: discord.Interaction, panel, guild_id, track, target_channel):
    guild = panel.bot.get_guild(guild_id)
    if isinstance(target_channel, discord.app_commands.AppCommandChannel) or hasattr(target_channel, "id"):
        target = guild.get_channel(target_channel.id) if guild else None
    elif isinstance(target_channel, int):
        target = guild.get_channel(target_channel) if guild else None
    else:
        target = target_channel

    if not target or not isinstance(target, (discord.TextChannel, discord.Thread, discord.VoiceChannel)):
        if not interaction.response.is_done():
            await interaction.response.send_message("Invalid channel selected.", ephemeral=True)
        else:
            await interaction.followup.send("Invalid channel selected.", ephemeral=True)
        return

    # Check bot permissions in target channel
    my_perms = target.permissions_for(guild.me) if guild and guild.me else None
    if my_perms and (not my_perms.send_messages or not my_perms.embed_links):
        msg = f"❌ I don't have permission to send embeds/messages in {target.mention}."
        if not interaction.response.is_done():
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            await interaction.followup.send(msg, ephemeral=True)
        return

    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)

    title = str(track.get("title") or track.get("name") or track.get("file_name") or "Unknown Track").strip()
    artist = str(track.get("artist") or "Juice WRLD").strip()
    cover_url = getattr(panel, "_cover_url", lambda t: None)(track) or f"https://api.juicevault.xyz/cdn/music/covers/{track.get('id')}"

    cog = panel.bot.get_cog("JuiceVault")
    session = getattr(cog, "session", None)

    lyrics_data = await fetch_lyrics(title, artist, session)
    embeds = build_lyrics_embeds(
        title=title,
        artist=artist,
        lyrics=lyrics_data.get("lyrics"),
        genius_url=lyrics_data.get("url"),
        cover_url=cover_url,
        color=panel.PANEL_COLOR,
    )

    try:
        for embed in embeds:
            await target.send(embed=embed)
        await interaction.followup.send(
            f"✅ Lyrics for **{clean_song_title(title)}** sent to {target.mention}!",
            ephemeral=True,
        )
    except Exception as e:
        await interaction.followup.send(
            f"Failed to send lyrics to {target.mention}: `{e}`",
            ephemeral=True,
        )


class JuiceVaultLyricsChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, panel, guild_id, track):
        self.panel = panel
        self.guild_id = guild_id
        self.track = track
        super().__init__(
            channel_types=[discord.ChannelType.text],
            placeholder="Select a channel to send lyrics…",
            min_values=1,
            max_values=1,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction):
        await send_lyrics_to_channel(interaction, self.panel, self.guild_id, self.track, self.values[0])


class JuiceVaultLyricsChannelView(discord.ui.View):
    def __init__(self, panel, guild_id, track, original_channel):
        super().__init__(timeout=120)
        self.panel = panel
        self.guild_id = guild_id
        self.track = track
        self.original_channel = original_channel

        self.add_item(JuiceVaultLyricsChannelSelect(panel, guild_id, track))

        if original_channel and isinstance(original_channel, (discord.TextChannel, discord.Thread)):
            current_btn = discord.ui.Button(
                label=f"Send in #{original_channel.name}"[:80],
                style=discord.ButtonStyle.primary,
                emoji="💬",
                row=1,
            )
            current_btn.callback = self._send_current
            self.add_item(current_btn)

        back_btn = discord.ui.Button(
            label="Back to Options",
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        back_btn.callback = self._back
        self.add_item(back_btn)

    async def _send_current(self, interaction: discord.Interaction):
        await send_lyrics_to_channel(interaction, self.panel, self.guild_id, self.track, self.original_channel)

    async def _back(self, interaction: discord.Interaction):
        view = JuiceVaultLyricsChoiceView(self.panel, self.guild_id, self.track, self.original_channel)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)


class JuiceVaultLyricsChoiceView(discord.ui.View):
    def __init__(self, panel, guild_id, track, channel):
        super().__init__(timeout=120)
        self.panel = panel
        self.guild_id = guild_id
        self.track = track
        self.channel = channel

        title = str(track.get("title") or track.get("name") or track.get("file_name") or "Unknown Track").strip()
        artist = str(track.get("artist") or "Juice WRLD").strip()
        self.title = clean_song_title(title)
        self.artist = artist

        btn_channel = discord.ui.Button(
            label="Send in a Channel",
            style=discord.ButtonStyle.primary,
            emoji="📢",
            row=0,
        )
        btn_channel.callback = self._on_choose_channel
        self.add_item(btn_channel)

        btn_link = discord.ui.Button(
            label="Give Me Link",
            style=discord.ButtonStyle.secondary,
            emoji="🔗",
            row=0,
        )
        btn_link.callback = self._on_give_link
        self.add_item(btn_link)

    def build_embed(self):
        embed = discord.Embed(
            title=f"🎶 Lyrics: {self.title}",
            description=(
                f"*{self.artist}*\n\n"
                "**Choose an option:**\n"
                "• **Option 1: Send in a channel** — Choose a Discord channel to post the lyrics.\n"
                "• **Option 2: Give me the link** — Get the direct Genius lyrics link."
            ),
            color=self.panel.PANEL_COLOR if self.panel else 0xFF2D55,
        )
        cover_url = getattr(self.panel, "_cover_url", lambda t: None)(self.track) if self.panel else None
        if not cover_url and self.track.get("id"):
            cover_url = f"https://api.juicevault.xyz/cdn/music/covers/{self.track.get('id')}"
        if cover_url:
            embed.set_thumbnail(url=cover_url)
        return embed

    async def _on_choose_channel(self, interaction: discord.Interaction):
        view = JuiceVaultLyricsChannelView(self.panel, self.guild_id, self.track, self.channel)
        embed = discord.Embed(
            title="📢 Choose Channel for Lyrics",
            description=f"Where should the lyrics for **{self.title}** be sent?",
            color=self.panel.PANEL_COLOR if self.panel else 0xFF2D55,
        )
        await interaction.response.edit_message(embed=embed, view=view)

    async def _on_give_link(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        cog = self.panel.bot.get_cog("JuiceVault") if self.panel else None
        session = getattr(cog, "session", None)
        genius_url = await get_genius_url(self.title, self.artist, session)
        embed = discord.Embed(
            title=f"🔗 Lyrics Link: {self.title}",
            description=(
                f"**{self.artist}**\n\n"
                f"**[Click here to view lyrics on Genius]({genius_url})**\n\n"
                f"`{genius_url}`"
            ),
            color=self.panel.PANEL_COLOR if self.panel else 0xFF2D55,
        )
        cover_url = getattr(self.panel, "_cover_url", lambda t: None)(self.track) if self.panel else None
        if not cover_url and self.track.get("id"):
            cover_url = f"https://api.juicevault.xyz/cdn/music/covers/{self.track.get('id')}"
        if cover_url:
            embed.set_thumbnail(url=cover_url)

        view = discord.ui.View(timeout=120)
        view.add_item(discord.ui.Button(label="Open on Genius", url=genius_url, style=discord.ButtonStyle.link))

        back_btn = discord.ui.Button(label="Back to Options", style=discord.ButtonStyle.secondary)

        async def _back_from_link(back_interaction: discord.Interaction):
            orig_view = JuiceVaultLyricsChoiceView(self.panel, self.guild_id, self.track, self.channel)
            await back_interaction.response.edit_message(embed=orig_view.build_embed(), view=orig_view)

        back_btn.callback = _back_from_link
        view.add_item(back_btn)

        await interaction.followup.edit_message(interaction.message.id, embed=embed, view=view)


async def lyrics_button_callback(self, interaction: discord.Interaction):
    cog = self.panel.bot.get_cog("JuiceVault")
    track = cog.current.get(self.guild_id) if cog else None
    if not track:
        await interaction.response.send_message("No track is currently playing.", ephemeral=True)
        return

    view = JuiceVaultLyricsChoiceView(self.panel, self.guild_id, track, interaction.channel)
    await interaction.response.send_message(embed=view.build_embed(), view=view, ephemeral=True)


def patch_eq_controls():
    JuiceVaultPanelView._eq = eq_button
    JuiceVaultPanelView._lyrics = lyrics_button_callback

    # Build the final panel directly. Do not wrap a previously patched
    # __init__, otherwise reloads can leave duplicate custom_ids behind.
    def final_init(self, panel, guild_id):
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

        def add(label, style, callback, key, row, disabled=False):
            button = discord.ui.Button(
                label=label,
                style=style,
                custom_id=f"juicevault:{key}:{guild_id}",
                row=row,
                disabled=disabled,
            )
            button.callback = callback
            self.add_item(button)

        # Row 0: Category, Search, Refresh, Lyrics, EQ.
        add("🎚 Category", discord.ButtonStyle.secondary, self._category, "category", 0)
        add("🔎 Search", discord.ButtonStyle.secondary, self._search, "search", 0)
        add("🔄 Refresh", discord.ButtonStyle.secondary, self._refresh, "refresh", 0, disabled=not running)
        add("🎶 Lyrics", discord.ButtonStyle.secondary, self._lyrics, "lyrics", 0, disabled=not has_track)
        add("🎚 EQ", discord.ButtonStyle.secondary, self._eq, "eq", 0)

        # Row 1: playback controls.
        if not running:
            add("▶ Play Music 🧃", discord.ButtonStyle.success, self._start, "start", 1)
        else:
            add("⏹ Stop Music 🧃", discord.ButtonStyle.danger, self._stop, "stop", 1)
            add(
                "▶ Resume Music 🧃" if paused else "⏸ Pause Music🧃",
                discord.ButtonStyle.primary,
                self._pause,
                "pause",
                1,
                disabled=not has_track,
            )

        # Row 2: Previous / Next ABOVE Repeat / Shuffle.
        add("⏮ Previous Song", discord.ButtonStyle.secondary, self._previous, "previous", 2, disabled=not has_history)
        add("Next Song ⏭", discord.ButtonStyle.primary, self._next, "next", 2, disabled=not playing)

        # Row 3: Repeat / Shuffle.
        add(
            "🔁 Repeat ON" if repeating else "🔁 Repeat",
            discord.ButtonStyle.success if repeating else discord.ButtonStyle.secondary,
            self._repeat,
            "repeat",
            3,
            disabled=not running,
        )
        add("🔀 Shuffle", discord.ButtonStyle.secondary, self._shuffle, "shuffle", 3, disabled=not has_queue)

        # Row 4: seek controls.
        add("⏮ Past 10s", discord.ButtonStyle.secondary, self._seek_back, "seek_back", 4, disabled=not (has_track and (playing or paused)))
        add("Next 10s ⏭", discord.ButtonStyle.secondary, self._seek_forward, "seek_forward", 4, disabled=not (has_track and (playing or paused)))

    JuiceVaultPanelView.__init__ = final_init
