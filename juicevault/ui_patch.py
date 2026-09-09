import discord

from . import juicevault_ui as ui
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


def _styled_panel_init(self, panel, guild_id):
    discord.ui.View.__init__(self, timeout=None)
    self.panel = panel
    self.guild_id = guild_id

    guild = panel.bot.get_guild(guild_id)
    voice = guild.voice_client if guild else None
    paused = bool(voice and voice.is_paused())
    repeating = panel.repeat_enabled.get(guild_id, False)

    # Explicitly use 4 + 4 + 2 buttons. Discord will not auto-pack them.
    buttons = [
        ("▶ Start", discord.ButtonStyle.success, self._start, "start", 0),
        (("▶ Resume" if paused else "⏸ Pause"), discord.ButtonStyle.primary, self._pause, "pause", 0),
        ("⏮ Previous", discord.ButtonStyle.secondary, self._previous, "previous", 0),
        ("Next ⏭", discord.ButtonStyle.primary, self._next, "next", 0),
        ("⏩ Next 10", discord.ButtonStyle.primary, self._skip10, "skip10", 1),
        (("🔁 Repeat ON" if repeating else "🔁 Repeat"), discord.ButtonStyle.success if repeating else discord.ButtonStyle.secondary, self._repeat, "repeat", 1),
        ("⏹ Stop", discord.ButtonStyle.danger, self._stop, "stop", 1),
        ("🔀 Shuffle", discord.ButtonStyle.secondary, self._shuffle, "shuffle", 1),
        ("🎚 Category", discord.ButtonStyle.secondary, self._category, "category", 2),
        ("🔄 Refresh", discord.ButtonStyle.secondary, self._refresh, "refresh", 2),
    ]

    for label, style, callback, key, row in buttons:
        button = discord.ui.Button(
            label=label,
            style=style,
            custom_id=f"juicevault:{key}:{guild_id}",
            row=row,
        )
        button.callback = callback
        self.add_item(button)


def patch_ui(JuiceVaultUI):
    """Install the polished embed and force the panel into three explicit rows."""
    JuiceVaultUI._make_embed = polished_make_embed
    JuiceVaultPanelView.__init__ = _styled_panel_init
    # Replace the module-level class reference used by ensure_panel/update_panel.
    ui.JuiceVaultPanelView = JuiceVaultPanelView
