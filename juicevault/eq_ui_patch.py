import discord

from .juicevault_ui import JuiceVaultPanelView


EQ_OPTIONS = [
    ("none", "🎵 Flat", "No EQ / original sound"),
    ("bass", "🔊 Bass Boost", "Boost low frequencies"),
    ("8d", "🌀 8D Audio", "Wide rotating stereo effect"),
    ("nightcore", "⚡ Nightcore", "Higher pitch and energy"),
    ("slowed", "🐌 Slowed", "Lower pitch and slower feel"),
    ("echo", "🌌 Echo", "Soft echo / reverb feel"),
    ("wide", "🎧 Wide", "Expanded stereo sound"),
    ("virtual bass", "💥 Virtual Bass", "Extra low-end presence"),
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
            restarted = await cog._request_seek(self.guild_id, -999999) is not None

        label = next((label for value, label, _ in EQ_OPTIONS if value == effect), effect)
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🎚️ EQ / Audio Effect",
                description=f"**{label}**\n\n" + (
                    "Applied and restarted the current song."
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


def patch_eq_controls():
    JuiceVaultPanelView._eq = eq_button
    original_init = JuiceVaultPanelView.__init__

    def smart_eq_init(self, panel, guild_id):
        original_init(self, panel, guild_id)
        guild = panel.bot.get_guild(guild_id)
        cog = panel.bot.get_cog("JuiceVault")
        running = bool(cog and guild_id in cog.tasks)
        voice = guild.voice_client if guild else None
        playing = bool(voice and voice.is_playing())
        paused = bool(voice and voice.is_paused())

        # Replace the playback row so its labels and EQ placement match the reference.
        row_one = [item for item in self.children if getattr(item, "row", None) == 1]
        for item in row_one:
            self.remove_item(item)

        def add(label, style, callback, key, disabled=False):
            button = discord.ui.Button(
                label=label,
                style=style,
                custom_id=f"juicevault:{key}:{guild_id}",
                row=1,
                disabled=disabled,
            )
            button.callback = callback
            self.add_item(button)

        if not running:
            add("▶ Play Music 🧃", discord.ButtonStyle.success, self._start, "start")
        else:
            add("⏹ Stop Music 🧃", discord.ButtonStyle.danger, self._stop, "stop")
            add(
                "▶ Resume Music 🧃" if paused else "⏸ Pause Music🧃",
                discord.ButtonStyle.primary,
                self._pause,
                "pause",
                disabled=not (playing or paused),
            )

        add("🎚 EQ", discord.ButtonStyle.secondary, self._eq, "eq")

        # Navigation labels requested by the new UI wording.
        row_three = [item for item in self.children if getattr(item, "row", None) == 3]
        for item in row_three:
            self.remove_item(item)
        add_nav = lambda label, style, callback, key, disabled=False: self.add_item(
            discord.ui.Button(
                label=label,
                style=style,
                custom_id=f"juicevault:{key}:{guild_id}",
                row=3,
                disabled=disabled,
            )
        )
        nav_buttons = [
            ("⏮ Previous Song", discord.ButtonStyle.secondary, self._previous, "previous", not bool(panel.history.get(guild_id))),
            ("Next Song ⏭", discord.ButtonStyle.primary, self._next, "next", not playing),
        ]
        for label, style, callback, key, disabled in nav_buttons:
            button = discord.ui.Button(label=label, style=style, custom_id=f"juicevault:{key}:{guild_id}", row=3, disabled=disabled)
            button.callback = callback
            self.add_item(button)

    JuiceVaultPanelView.__init__ = smart_eq_init
