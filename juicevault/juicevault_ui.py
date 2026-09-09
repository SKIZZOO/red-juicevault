import asyncio

import discord
from redbot.core import Config, commands


class JuiceVaultCategorySelect(discord.ui.Select):
    def __init__(self, panel, guild_id, categories):
        self.panel = panel
        self.guild_id = guild_id
        options = [discord.SelectOption(label="All", value="all", emoji="🎵")]
        for name, count in sorted(categories.items()):
            if name == "all":
                continue
            if len(options) >= 25:
                break
            label = name.replace("_", " ").title()[:100]
            options.append(discord.SelectOption(label=label, value=name[:100], description=f"{count} piese"[:100]))
        super().__init__(placeholder="Alege categoria…", min_values=1, max_values=1, options=options, custom_id=f"juicevault:category_select:{guild_id}")

    async def callback(self, interaction: discord.Interaction):
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.response.send_message("JuiceVault cog nu este încărcat.", ephemeral=True)
            return
        category = cog._category_name(self.values[0])
        try:
            tracks = cog._filter_tracks(await cog.fetch_tracks(), category)
            if category != "all" and not tracks:
                await interaction.response.send_message("Categoria nu mai conține piese.", ephemeral=True)
                return
            await cog.config.guild(interaction.guild).category.set(category)
            if self.guild_id in cog.tasks:
                cog.queues[self.guild_id] = tracks
                cog.failure_counts[self.guild_id] = 0
            await interaction.response.send_message(f"🎚️ Categoria setată pe **{category}** — `{len(tracks)}` piese.", ephemeral=True)
            await self.panel.update_panel(self.guild_id)
        except Exception as exc:
            await interaction.response.send_message(f"Nu pot schimba categoria: `{exc}`", ephemeral=True)


class JuiceVaultCategoryView(discord.ui.View):
    def __init__(self, panel, guild_id, categories):
        super().__init__(timeout=60)
        self.add_item(JuiceVaultCategorySelect(panel, guild_id, categories))


class JuiceVaultPanelView(discord.ui.View):
    """Persistent JuiceVault controls."""

    def __init__(self, panel, guild_id):
        super().__init__(timeout=None)
        self.panel = panel
        self.guild_id = guild_id

        start = discord.ui.Button(label="Start", emoji="▶️", style=discord.ButtonStyle.success, custom_id=f"juicevault:start:{guild_id}")
        start.callback = self._start
        self.add_item(start)
        stop = discord.ui.Button(label="Stop", emoji="⏹️", style=discord.ButtonStyle.danger, custom_id=f"juicevault:stop:{guild_id}")
        stop.callback = self._stop
        self.add_item(stop)
        next_button = discord.ui.Button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.primary, custom_id=f"juicevault:next:{guild_id}")
        next_button.callback = self._next
        self.add_item(next_button)
        skip10 = discord.ui.Button(label="Skip 10", emoji="⏩", style=discord.ButtonStyle.primary, custom_id=f"juicevault:skip10:{guild_id}")
        skip10.callback = self._skip10
        self.add_item(skip10)
        shuffle = discord.ui.Button(label="Shuffle", emoji="🔀", style=discord.ButtonStyle.secondary, custom_id=f"juicevault:shuffle:{guild_id}")
        shuffle.callback = self._shuffle
        self.add_item(shuffle)
        category = discord.ui.Button(label="Category", emoji="🎚️", style=discord.ButtonStyle.secondary, custom_id=f"juicevault:category:{guild_id}")
        category.callback = self._category
        self.add_item(category)
        refresh = discord.ui.Button(label="Refresh", emoji="🔄", style=discord.ButtonStyle.secondary, custom_id=f"juicevault:refresh:{guild_id}")
        refresh.callback = self._refresh
        self.add_item(refresh)

    async def _start(self, interaction):
        await interaction.response.defer()
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.followup.send("JuiceVault cog nu este încărcat.", ephemeral=True)
            return
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.followup.send("Intră într-un voice channel înainte de Start.", ephemeral=True)
            return
        gid = self.guild_id
        if gid in cog.tasks:
            voice = interaction.guild.voice_client
            if voice and voice.is_connected():
                await interaction.followup.send("JuiceVault rulează deja.", ephemeral=True)
                return
            await cog._stop(gid)
        try:
            all_tracks = await cog.fetch_tracks()
            category = await cog.config.guild(interaction.guild).category()
            tracks = cog._filter_tracks(all_tracks, category)
            if not tracks:
                await interaction.followup.send(f"Categoria `{category}` nu conține piese.", ephemeral=True)
                return
            voice = await cog._connect(interaction.guild, interaction.user.voice.channel)
            cog.queues[gid] = tracks
            cog.manual_queues[gid] = []
            cog.stop_events[gid] = asyncio.Event()
            cog.skip_events[gid] = asyncio.Event()
            cog.skip_counts[gid] = 0
            cog.failure_counts[gid] = 0
            await cog.config.guild(interaction.guild).enabled.set(True)
            await cog.config.guild(interaction.guild).channel_id.set(interaction.user.voice.channel.id)
            cog.tasks[gid] = asyncio.create_task(cog._player(interaction.guild, interaction.user.voice.channel))
            await self.panel.update_panel(gid)
            await interaction.followup.send(f"▶️ Pornit în `{voice.channel.name}` — `{category}`.", ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(f"Nu pot porni playerul: `{type(exc).__name__}: {exc}`", ephemeral=True)

    async def _stop(self, interaction):
        await interaction.response.defer()
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.followup.send("JuiceVault cog nu este încărcat.", ephemeral=True)
            return
        await cog.config.guild(interaction.guild).enabled.set(False)
        await cog._stop(self.guild_id)
        await self.panel.update_panel(self.guild_id)
        await interaction.followup.send("⏹️ Oprit.", ephemeral=True)

    async def _next(self, interaction):
        await interaction.response.defer()
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.followup.send("JuiceVault cog nu este încărcat.", ephemeral=True)
            return
        if await cog._request_skip(self.guild_id, 1):
            await interaction.followup.send("⏭️ Skip 1.", ephemeral=True)
        else:
            await interaction.followup.send("Nu rulează nicio piesă sau un skip este deja în curs.", ephemeral=True)
        await self.panel.update_panel(self.guild_id)

    async def _skip10(self, interaction):
        await interaction.response.defer()
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.followup.send("JuiceVault cog nu este încărcat.", ephemeral=True)
            return
        if await cog._request_skip(self.guild_id, 10):
            await interaction.followup.send("⏩ Skip 10.", ephemeral=True)
        else:
            await interaction.followup.send("Nu rulează nicio piesă sau un skip este deja în curs.", ephemeral=True)
        await self.panel.update_panel(self.guild_id)

    async def _shuffle(self, interaction):
        await interaction.response.defer()
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.followup.send("JuiceVault cog nu este încărcat.", ephemeral=True)
            return
        queue = cog.queues.get(self.guild_id)
        if not queue:
            await interaction.followup.send("Queue-ul este gol.", ephemeral=True)
            return
        import random
        random.shuffle(queue)
        await self.panel.update_panel(self.guild_id)
        await interaction.followup.send(f"🔀 Queue amestecat — `{len(queue)}` piese.", ephemeral=True)

    async def _category(self, interaction):
        await interaction.response.defer(ephemeral=True)
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.followup.send("JuiceVault cog nu este încărcat.", ephemeral=True)
            return
        try:
            categories = await cog.get_categories()
            await interaction.followup.send("🎚️ Alege categoria:", view=JuiceVaultCategoryView(self.panel, self.guild_id, categories), ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(f"Nu pot încărca categoriile: `{exc}`", ephemeral=True)

    async def _refresh(self, interaction):
        await interaction.response.defer()
        cog = self.panel.bot.get_cog("JuiceVault")
        if cog is None:
            await interaction.followup.send("JuiceVault cog nu este încărcat.", ephemeral=True)
            return
        try:
            tracks = await cog.fetch_tracks()
            category = await cog.config.guild(interaction.guild).category()
            cog.queues[self.guild_id] = cog._filter_tracks(tracks, category)
            cog.failure_counts[self.guild_id] = 0
            await self.panel.update_panel(self.guild_id)
            await interaction.followup.send(f"🔄 Refresh — `{len(cog.queues[self.guild_id])}` piese în `{category}`.", ephemeral=True)
        except Exception as exc:
            await interaction.followup.send(f"Refresh eșuat: `{exc}`", ephemeral=True)


class JuiceVaultUI(commands.Cog):
    """Modern Discord now-playing panel for JuiceVault."""

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
        self._task = None
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
            return "Nicio piesă"
        artist = str(track.get("artist") or "").strip()
        title = str(track.get("title") or track.get("name") or "").strip()
        return f"{artist} — {title}" if artist and title else title or str(track.get("file_name") or "Piesă fără nume")

    @staticmethod
    def _cover_url(track):
        cover = str((track or {}).get("cover") or "").strip()
        if not cover:
            return None
        if cover.startswith("http://") or cover.startswith("https://"):
            return cover
        return f"https://api.juicevault.xyz/{cover.lstrip('/')}"

    async def _make_embed(self, guild_id):
        main = self.bot.get_cog("JuiceVault")
        embed = discord.Embed(color=self.PANEL_COLOR)
        embed.set_author(name="JUICEVAULT • LIVE")
        if main is None or guild_id not in main.tasks:
            embed.title = "Player offline"
            embed.description = "Apasă Start sau folosește `4jv start`."
            embed.set_footer(text="JuiceVault • 24/7 Archive Player")
            return embed
        guild = self.bot.get_guild(guild_id)
        track = main.current.get(guild_id)
        queue_size = len(main.queues.get(guild_id, []))
        requested_size = len(main.manual_queues.get(guild_id, []))
        category = await main.config.guild(guild).category()
        voice = guild.voice_client if guild else None
        embed.title = "Now Playing" if track else "Starting…"
        if track:
            category_text = str(track.get("category") or "archive").replace("_", " ").title()
            embed.description = f"## {self._track_text(track)}\n`● LIVE` • JuiceVault Archive"
            embed.add_field(name="Category", value=category_text[:1024], inline=True)
            embed.add_field(name="Length", value=str(track.get("length") or "—"), inline=True)
            embed.add_field(name="Selected", value=str(category), inline=True)
            embed.add_field(name="Requested", value=f"`{requested_size}`", inline=True)
            embed.add_field(name="Queue", value=f"`{queue_size}`", inline=True)
            cover_url = self._cover_url(track)
            if cover_url:
                embed.set_thumbnail(url=cover_url)
            play_count = track.get("play_count")
            embed.set_footer(text=f"JuiceVault • {play_count:,} plays • 24/7" if play_count is not None else "JuiceVault • 24/7")
        else:
            embed.description = "Se încarcă următoarea piesă din arhivă."
            embed.set_footer(text=f"JuiceVault • categoria {category}")
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
        target = channel or (guild.get_channel(channel_id) if channel_id else None)
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
        message = await target.send(embed=await self._make_embed(guild_id), view=JuiceVaultPanelView(self, guild_id))
        await self.config.guild(guild).panel_channel_id.set(target.id)
        await self.config.guild(guild).panel_message_id.set(message.id)
        return message

    async def update_panel(self, guild_id):
        message = await self._get_panel_message(guild_id)
        if message is None:
            return
        try:
            await message.edit(embed=await self._make_embed(guild_id), view=JuiceVaultPanelView(self, guild_id))
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

    @commands.command(name="jvpanel", aliases=["jvui"])
    @commands.guild_only()
    async def jvpanel(self, ctx):
        await self.config.guild(ctx.guild).panel_channel_id.set(ctx.channel.id)
        self._register_view(ctx.guild.id)
        message = await self._get_panel_message(ctx.guild.id, create=True, channel=ctx.channel)
        if message:
            await message.edit(embed=await self._make_embed(ctx.guild.id), view=JuiceVaultPanelView(self, ctx.guild.id))
            await ctx.send("✨ Panoul JuiceVault este aici și se actualizează automat.", delete_after=8)
