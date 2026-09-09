import asyncio

import discord
from discord.ext import commands
from redbot.core import Config


class JuiceVaultPanelView(discord.ui.View):
    """Persistent control buttons for the JuiceVault now-playing panel."""

    def __init__(self, panel, guild_id):
        super().__init__(timeout=None)
        self.panel = panel
        self.guild_id = guild_id

        next_button = discord.ui.Button(
            label="Next",
            emoji="⏭️",
            style=discord.ButtonStyle.primary,
            custom_id=f"juicevault:next:{guild_id}",
        )
        next_button.callback = self._next
        self.add_item(next_button)

        refresh_button = discord.ui.Button(
            label="Refresh",
            emoji="🔄",
            style=discord.ButtonStyle.secondary,
            custom_id=f"juicevault:refresh:{guild_id}",
        )
        refresh_button.callback = self._refresh
        self.add_item(refresh_button)

        stop_button = discord.ui.Button(
            label="Stop",
            emoji="⏹️",
            style=discord.ButtonStyle.danger,
            custom_id=f"juicevault:stop:{guild_id}",
        )
        stop_button.callback = self._stop
        self.add_item(stop_button)

    async def _next(self, interaction: discord.Interaction):
        await interaction.response.defer()
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.followup.send("JuiceVault cog nu este încărcat.", ephemeral=True)
            return

        voice = interaction.guild.voice_client if interaction.guild else None
        event = cog.skip_events.get(self.guild_id)
        if self.guild_id not in cog.tasks or not event or not voice or not voice.is_playing():
            await interaction.followup.send("Nu rulează nicio piesă.", ephemeral=True)
            return

        event.set()
        voice.stop()
        await self.panel.update_panel(self.guild_id)

    async def _refresh(self, interaction: discord.Interaction):
        await interaction.response.defer()
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.followup.send("JuiceVault cog nu este încărcat.", ephemeral=True)
            return

        try:
            tracks = await cog.fetch_tracks()
            if not tracks:
                raise RuntimeError("API nu a returnat piese")
            cog.queues[self.guild_id] = tracks
            cog.last_error.pop(self.guild_id, None)
            await self.panel.update_panel(self.guild_id)
        except Exception as exc:
            await interaction.followup.send(f"Refresh eșuat: `{exc}`", ephemeral=True)

    async def _stop(self, interaction: discord.Interaction):
        await interaction.response.defer()
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.followup.send("JuiceVault cog nu este încărcat.", ephemeral=True)
            return

        await cog.config.guild(interaction.guild).enabled.set(False)
        await cog._stop(self.guild_id)
        await self.panel.update_panel(self.guild_id)


class JuiceVaultUI(commands.Cog):
    """Modern Discord now-playing panel for the JuiceVault player."""

    PANEL_COLOR = discord.Color.from_rgb(155, 89, 182)
    CONFIG_ID = 918273646

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=self.CONFIG_ID, force_registration=True)
        self.config.register_guild(panel_channel_id=None, panel_message_id=None)
        self._task = None
        self._restore_task = None
        self._registered_views = set()

    async def cog_load(self):
        self._task = asyncio.create_task(self._panel_loop())
        self._restore_task = asyncio.create_task(self._restore_views())

    async def cog_unload(self):
        for task in (self._task, self._restore_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

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
            return "Nicio piesă"
        artist = str(track.get("artist") or "").strip()
        title = str(track.get("title") or track.get("name") or "").strip()
        if artist and title:
            return f"{artist} — {title}"
        return title or str(track.get("file_name") or "Piesă fără nume")

    @staticmethod
    def _cover_url(track):
        cover = str((track or {}).get("cover") or "").strip()
        if not cover:
            return None
        if cover.startswith("http://") or cover.startswith("https://"):
            return cover
        return f"https://api.juicevault.xyz/{cover.lstrip('/')}"

    def _make_embed(self, guild_id):
        main = self.bot.get_cog("JuiceVault")
        embed = discord.Embed(color=self.PANEL_COLOR)
        embed.set_author(name="JUICEVAULT • LIVE")

        if main is None or guild_id not in main.tasks:
            embed.title = "Player offline"
            embed.description = "Pornește playerul cu `4jv start`."
            embed.set_footer(text="JuiceVault • 24/7 Archive Player")
            return embed

        guild = self.bot.get_guild(guild_id)
        track = main.current.get(guild_id)
        queue_size = len(main.queues.get(guild_id, []))
        voice = guild.voice_client if guild else None

        if track:
            embed.title = "Now Playing"
            embed.description = f"## {self._track_text(track)}\n`● LIVE`  •  JuiceVault Archive"
            album = str(track.get("album") or "Unreleased")
            category = str(track.get("category") or "archive").replace("_", " ").title()
            length = str(track.get("length") or "—")
            embed.add_field(name="Album", value=album[:1024], inline=True)
            embed.add_field(name="Length", value=length, inline=True)
            embed.add_field(name="Type", value=category[:1024], inline=True)
            embed.add_field(
                name="Queue",
                value=f"`{queue_size}` piese în așteptare",
                inline=False,
            )
            cover_url = self._cover_url(track)
            if cover_url:
                embed.set_thumbnail(url=cover_url)
            play_count = track.get("play_count")
            if play_count is not None:
                embed.set_footer(text=f"JuiceVault • {play_count:,} plays • 24/7")
            else:
                embed.set_footer(text="JuiceVault • 24/7 Archive Player")
        else:
            embed.title = "Starting…"
            embed.description = "Se încarcă următoarea piesă din arhivă."
            embed.set_footer(text="JuiceVault • 24/7 Archive Player")

        if voice and voice.is_playing():
            embed.add_field(name="Voice", value=f"🔊 {voice.channel.name}", inline=True)
        return embed

    async def _get_panel_message(self, guild_id, create=False, channel=None):
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return None

        settings = await self.config.guild(guild).all()
        channel_id = settings.get("panel_channel_id")
        message_id = settings.get("panel_message_id")
        target = channel
        if target is None and channel_id:
            target = guild.get_channel(channel_id)
        if not isinstance(target, discord.TextChannel):
            return None

        self._register_view(guild_id)
        if message_id:
            try:
                return await target.fetch_message(message_id)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

        if not create:
            return None

        message = await target.send(
            embed=self._make_embed(guild_id),
            view=JuiceVaultPanelView(self, guild_id),
        )
        await self.config.guild(guild).panel_channel_id.set(target.id)
        await self.config.guild(guild).panel_message_id.set(message.id)
        return message

    async def update_panel(self, guild_id):
        message = await self._get_panel_message(guild_id, create=False)
        if message is None:
            return
        try:
            await message.edit(
                embed=self._make_embed(guild_id),
                view=JuiceVaultPanelView(self, guild_id),
            )
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            pass

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

    async def _maybe_create_after_start(self, ctx):
        if not ctx.guild:
            return
        command = getattr(ctx, "command", None)
        if not command or command.qualified_name != "jv start":
            return
        try:
            await self.config.guild(ctx.guild).panel_channel_id.set(ctx.channel.id)
            self._register_view(ctx.guild.id)
            message = await self._get_panel_message(ctx.guild.id, create=True, channel=ctx.channel)
            if message:
                await message.edit(
                    embed=self._make_embed(ctx.guild.id),
                    view=JuiceVaultPanelView(self, ctx.guild.id),
                )
        except (discord.Forbidden, discord.HTTPException) as exc:
            print(f"[JuiceVaultUI] could not create panel: {exc}")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        await self._maybe_create_after_start(ctx)

    @commands.command(name="jvpanel", aliases=["jvui"])
    @commands.guild_only()
    async def jvpanel(self, ctx):
        """Create or move the modern JuiceVault now-playing panel to this channel."""
        await self.config.guild(ctx.guild).panel_channel_id.set(ctx.channel.id)
        self._register_view(ctx.guild.id)
        message = await self._get_panel_message(ctx.guild.id, create=True, channel=ctx.channel)
        if message:
            await message.edit(
                embed=self._make_embed(ctx.guild.id),
                view=JuiceVaultPanelView(self, ctx.guild.id),
            )
            await ctx.send("✨ Panoul JuiceVault este aici și se actualizează automat.", delete_after=8)
