from .juicevault import JuiceVault
from .ui import JuiceVaultUI


async def setup(bot):
    await bot.add_cog(JuiceVault(bot))
    await bot.add_cog(JuiceVaultUI(bot))
