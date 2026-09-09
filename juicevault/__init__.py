from .juicevault import JuiceVault
from .juicevault_ui import JuiceVaultUI


async def setup(bot):
    await bot.add_cog(JuiceVault(bot))
    await bot.add_cog(JuiceVaultUI(bot))
