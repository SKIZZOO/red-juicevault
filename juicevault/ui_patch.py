import discord

from .juicevault_ui import category_label


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


def patch_ui(JuiceVaultUI):
    JuiceVaultUI._make_embed = polished_make_embed
