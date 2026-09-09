import discord

from . import juicevault_ui as ui
from .juicevault_ui import category_label, JuiceVaultPanelView


EFFECTS = {
    "none": "Normal",
    "bass": "Bass Boost",
    "8d": "8D / Moving Stereo",
    "nightcore": "Nightcore",
    "slowed": "Slowed",
    "echo": "Echo",
    "wide": "Wide Stereo",
    "virtual bass": "Virtual Bass",
}


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
    effect = EFFECTS.get(main.effects.get(guild_id, "none"), "Normal")
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
        embed.add_field(name="🎛️ EFFECT", value=f"**{effect}**", inline=True)
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
        embed.add_field(name="🎛️ EFFECT", value=f"**{effect}**", inline=True)
        embed.set_footer(text="JuiceVault Archive • 24/7 Player")
    if voice and voice.is_connected():
        embed.add_field(name="🔊 VOICE", value=f"`{voice.channel.name}`", inline=False)
    return embed


class JuiceVaultEffectSelect(discord.ui.Select):
    def __init__(self, panel, guild_id):
        self.panel = panel
        self.guild_id = guild_id
        cog = panel.bot.get_cog("JuiceVault")
        selected = cog.effects.get(guild_id, "none") if cog else "none"
        icons = {"none": "🎵", "bass": "🔊", "8d": "🌀", "nightcore": "⚡", "slowed": "🐢", "echo": "📣", "wide": "↔️", "virtual bass": "💥"}
        options = [discord.SelectOption(label=label, value=value, emoji=icons.get(value), default=value == selected) for value, label in EFFECTS.items()]
        super().__init__(placeholder="Choose an audio effect…", min_values=1, max_values=1, options=options, custom_id=f"juicevault:effect_select:{guild_id}")

    async def callback(self, interaction):
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.response.send_message("JuiceVault is not loaded.", ephemeral=True)
            return
        value = self.values[0]
        cog.effects[self.guild_id] = value
        if self.guild_id in cog.tasks:
            await cog._request_seek(self.guild_id, 0)
        await interaction.response.send_message(f"🎛️ Effect set to **{EFFECTS[value]}**.", ephemeral=True)
        await self.panel.update_panel(self.guild_id)


class JuiceVaultEffectView(discord.ui.View):
    def __init__(self, panel, guild_id):
        super().__init__(timeout=60)
        self.add_item(JuiceVaultEffectSelect(panel, guild_id))


def _styled_panel_init(self, panel, guild_id):
    discord.ui.View.__init__(self, timeout=None)
    self.panel = panel
    self.guild_id = guild_id
    guild = panel.bot.get_guild(guild_id)
    voice = guild.voice_client if guild else None
    paused = bool(voice and voice.is_paused())
    repeating = panel.repeat_enabled.get(guild_id, False)

    async def seek_back(interaction):
        await interaction.response.defer()
        cog = self._cog()
        target = await cog._request_seek(self.guild_id, -10) if cog else None
        if target is None:
            await interaction.followup.send("No active track is available for seeking.", ephemeral=True)
            return
        await self.panel.update_panel(self.guild_id)
        await interaction.followup.send(f"⏪ Rewound 10 seconds — `{int(target)}s`.", ephemeral=True)

    async def seek_forward(interaction):
        await interaction.response.defer()
        cog = self._cog()
        target = await cog._request_seek(self.guild_id, 10) if cog else None
        if target is None:
            await interaction.followup.send("No active track is available for seeking.", ephemeral=True)
            return
        await self.panel.update_panel(self.guild_id)
        await interaction.followup.send(f"⏩ Forward 10 seconds — `{int(target)}s`.", ephemeral=True)

    async def effects_menu(interaction):
        await interaction.response.send_message("🎛️ Choose an audio effect:", view=JuiceVaultEffectView(self.panel, self.guild_id), ephemeral=True)

    self._seek_back = seek_back
    self._seek_forward = seek_forward
    self._effects_menu = effects_menu

    # Exactly 5 + 5 + 3 buttons. Discord's row limit is respected.
    buttons = [
        ("▶ Start", discord.ButtonStyle.success, self._start, "start", 0),
        (("▶ Resume" if paused else "⏸ Pause"), discord.ButtonStyle.primary, self._pause, "pause", 0),
        ("⏮ Previous", discord.ButtonStyle.secondary, self._previous, "previous", 0),
        ("⏪ -10s", discord.ButtonStyle.secondary, self._seek_back, "seek_back", 0),
        ("⏩ +10s", discord.ButtonStyle.secondary, self._seek_forward, "seek_forward", 0),
        ("Next ⏭", discord.ButtonStyle.primary, self._next, "next", 1),
        ("Next 10 ⏩", discord.ButtonStyle.primary, self._skip10, "skip10", 1),
        (("🔁 Repeat ON" if repeating else "🔁 Repeat"), discord.ButtonStyle.success if repeating else discord.ButtonStyle.secondary, self._repeat, "repeat", 1),
        ("⏹ Stop", discord.ButtonStyle.danger, self._stop, "stop", 1),
        ("🔀 Shuffle", discord.ButtonStyle.secondary, self._shuffle, "shuffle", 1),
        ("🎚 Category", discord.ButtonStyle.secondary, self._category, "category", 2),
        ("🎛 Effects", discord.ButtonStyle.secondary, self._effects_menu, "effects", 2),
        ("🔄 Refresh", discord.ButtonStyle.secondary, self._refresh, "refresh", 2),
    ]
    for label, style, callback, key, row in buttons:
        button = discord.ui.Button(label=label, style=style, custom_id=f"juicevault:{key}:{guild_id}", row=row)
        button.callback = callback
        self.add_item(button)


def patch_ui(JuiceVaultUI):
    """Install the polished embed, seeking controls, and audio-effect menu."""
    JuiceVaultUI._make_embed = polished_make_embed
    JuiceVaultPanelView.__init__ = _styled_panel_init
    ui.JuiceVaultPanelView = JuiceVaultPanelView
