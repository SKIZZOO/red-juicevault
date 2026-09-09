from .juicevault import JuiceVault
from .juicevault_ui import JuiceVaultUI
from .api_sources import patch_juicevault_class
from .ui_patch import patch_ui
from .eq_ui_patch import patch_eq_controls
from .voice_patch import patch_voice_location
from .external_search_patch import patch_external_search


patch_juicevault_class(JuiceVault)
patch_ui(JuiceVaultUI)

# JuiceVault website uses /archive/<id> for archive tracks.
# ui_patch builds the display link, so normalize it after the UI patch is installed.
_original_make_embed = JuiceVaultUI._make_embed


async def _archive_make_embed(self, guild_id):
    embed = await _original_make_embed(self, guild_id)
    if embed.url and embed.url.startswith("https://juicevault.xyz/music/"):
        embed.url = embed.url.replace("https://juicevault.xyz/music/", "https://juicevault.xyz/archive/", 1)
    if embed.description:
        embed.description = embed.description.replace(
            "https://juicevault.xyz/music/",
            "https://juicevault.xyz/archive/",
        )
    return embed


JuiceVaultUI._make_embed = _archive_make_embed
patch_eq_controls()
patch_voice_location()
patch_external_search()


async def setup(bot):
    await bot.add_cog(JuiceVault(bot))
    await bot.add_cog(JuiceVaultUI(bot))
