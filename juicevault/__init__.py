from .juicevault import JuiceVault
from .juicevault_ui import JuiceVaultUI
from .api_sources import patch_juicevault_class
from .ui_patch import patch_ui


patch_juicevault_class(JuiceVault)
patch_ui(JuiceVaultUI)


async def setup(bot):
    await bot.add_cog(JuiceVault(bot))
    await bot.add_cog(JuiceVaultUI(bot))
