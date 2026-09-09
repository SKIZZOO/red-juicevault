from .juicevault import JuiceVault
from .juicevault_ui import JuiceVaultUI
from .api_sources import patch_juicevault_class
from .ui_patch import patch_ui
from .eq_ui_patch import patch_eq_controls
from .voice_patch import patch_voice_location
from .external_search_patch import patch_external_search


patch_juicevault_class(JuiceVault)
patch_ui(JuiceVaultUI)
patch_eq_controls()
patch_voice_location()
patch_external_search()


async def setup(bot):
    await bot.add_cog(JuiceVault(bot))
    await bot.add_cog(JuiceVaultUI(bot))
